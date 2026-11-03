import os
import shutil

APP_PY = os.path.join("my-node-app", "app.py")
BACKUP_PY = os.path.join("my-node-app", "app.py.bak_persistence")

shutil.copyfile(APP_PY, BACKUP_PY)
print("Backup created at:", BACKUP_PY)

with open(APP_PY, "r", encoding="utf-8") as f:
    content = f.read()

# -----------------------------------------------------------------------------
# 1. Add save_durable_image and update serve_uploads
# -----------------------------------------------------------------------------
target_uploads = '''@app.route("/uploads/<path:filename>")
@app.route("/public/uploads/<path:filename>")
@app.route("/my-node-app/public/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)'''

repl_uploads = '''def save_durable_image(filename, filepath_or_stream, mime_type=None):
    """
    Persists uploaded bike image directly into TiDB Cloud `durable_images` table.
    Ensures images survive Render container restarts/redeployments permanently.
    """
    try:
        if isinstance(filepath_or_stream, (bytes, bytearray)):
            image_data = bytes(filepath_or_stream)
        elif hasattr(filepath_or_stream, "read"):
            pos = filepath_or_stream.tell() if hasattr(filepath_or_stream, "tell") else 0
            image_data = filepath_or_stream.read()
            if hasattr(filepath_or_stream, "seek"):
                filepath_or_stream.seek(pos)
        elif isinstance(filepath_or_stream, str) and os.path.exists(filepath_or_stream):
            with open(filepath_or_stream, "rb") as f:
                image_data = f.read()
        else:
            return False

        if not mime_type:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or "image/jpeg"

        file_size = len(image_data)
        if file_size == 0:
            return False

        conn = get_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO durable_images (filename, mime_type, file_size, image_data)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        mime_type = VALUES(mime_type),
                        file_size = VALUES(file_size),
                        image_data = VALUES(image_data)
                """, (filename, mime_type, file_size, image_data))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                print(f"[Durable Image] Notice: Could not sync {filename} to TiDB Cloud:", e)
                if conn:
                    try: conn.close()
                    except Exception: pass
    except Exception as err:
        print(f"[Durable Image] Error saving {filename}:", err)
    return False

@app.route("/uploads/<path:filename>")
@app.route("/public/uploads/<path:filename>")
@app.route("/my-node-app/public/uploads/<path:filename>")
def serve_uploads(filename):
    clean_filename = os.path.basename(filename)
    disk_path = os.path.join(UPLOAD_DIR, clean_filename)

    # 1. If file exists on local filesystem, serve it directly
    if os.path.isfile(disk_path):
        return send_from_directory(UPLOAD_DIR, clean_filename)

    # 2. Resilient TiDB Cloud retrieval: If disk was wiped by Render restart/redeploy,
    # pull image data from `durable_images` table, re-cache on disk, and stream.
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT mime_type, image_data FROM durable_images WHERE filename = %s LIMIT 1",
                (clean_filename,)
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row and row.get("image_data"):
                img_bytes = row["image_data"]
                mime_type = row.get("mime_type") or "image/jpeg"

                # Re-cache to local disk for fast subsequent reads
                try:
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    with open(disk_path, "wb") as f:
                        f.write(img_bytes)
                except Exception:
                    pass

                import io
                from flask import send_file
                return send_file(io.BytesIO(img_bytes), mimetype=mime_type)
        except Exception as e:
            print(f"[Durable Image] Database retrieval failed for {clean_filename}:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    # 3. Fallback: Check if file exists in static/images
    alt_static = os.path.join(app.root_path, "static", "images", clean_filename)
    if os.path.isfile(alt_static):
        return send_from_directory(os.path.join(app.root_path, "static", "images"), clean_filename)

    return jsonify({"error": f"Image {clean_filename} not found"}), 404'''

assert target_uploads in content, "target_uploads not found"
content = content.replace(target_uploads, repl_uploads, 1)
print("1. Added save_durable_image and updated serve_uploads.")

# -----------------------------------------------------------------------------
# 2. Add get_current_user_profile right after user_required
# -----------------------------------------------------------------------------
target_user_req = '''def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"success": False, "message": "Authentication required. Please sign in."}), 401
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"success": False, "message": "Invalid auth header format. Expected Bearer <token>"}), 401
        try:
            import jwt
            decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
            g.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Session has expired. Please sign in again."}), 401
        except Exception:
            return jsonify({"success": False, "message": "Invalid or expired session. Please sign in again."}), 401
        return f(*args, **kwargs)
    return wrapper'''

repl_user_req = target_user_req + '''

def get_current_user_profile():
    """
    Extracts current authenticated user record from JWT Authorization header,
    session, or smr_remember_token / smr_remember_me cookie.
    Queries TiDB Cloud MySQL `users` table for live data.
    Returns: (user_id, user_dict) or (None, None)
    """
    u_id = None
    if hasattr(g, "user") and g.user and g.user.get("id"):
        u_id = g.user.get("id")
    elif session.get("user_id"):
        u_id = session.get("user_id")
    else:
        auth = request.headers.get("Authorization", "")
        if auth and "bearer" in auth.lower():
            try:
                parts = auth.split()
                if len(parts) == 2:
                    import jwt
                    decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
                    u_id = decoded.get("id") or decoded.get("user_id")
            except Exception:
                pass
        if not u_id:
            token = request.cookies.get("smr_remember_token") or request.cookies.get("smr_remember_me")
            if token:
                try:
                    user_val = validate_remembered_session(token)
                    if user_val:
                        u_id = user_val.get("id")
                except Exception:
                    pass

    if not u_id:
        return None, None

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, google_id, name, email, profile_image, phone, role, is_active, created_at FROM users WHERE id = %s LIMIT 1",
                (u_id,)
            )
            user_row = cursor.fetchone()
            cursor.close()
            conn.close()
            if user_row:
                return user_row["id"], user_row
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return u_id, {"id": u_id, "name": "User", "role": "user"}'''

assert target_user_req in content, "target_user_req not found"
content = content.replace(target_user_req, repl_user_req, 1)
print("2. Added get_current_user_profile.")

# -----------------------------------------------------------------------------
# 3. Update user_profile template API response
# -----------------------------------------------------------------------------
target_profile_tmpl = '''def user_profile():
    if request.headers.get("Authorization"):
        # API request
        return jsonify({"success": True, "user": IN_MEMORY_STORE["users"][0]})
    return render_template("profile.html")'''

repl_profile_tmpl = '''def user_profile():
    if request.headers.get("Authorization"):
        # API request
        u_id, u_data = get_current_user_profile()
        if u_data:
            return jsonify({"success": True, "user": u_data})
        return jsonify({"success": False, "message": "Authentication required"}), 401
    return render_template("profile.html")'''

assert target_profile_tmpl in content, "target_profile_tmpl not found"
content = content.replace(target_profile_tmpl, repl_profile_tmpl, 1)
print("3. Updated user_profile template endpoint.")

# -----------------------------------------------------------------------------
# 4. Update add_bike_api: durable image saving + seller_id extraction
# -----------------------------------------------------------------------------
target_add_bike_img = '''                ext = f.filename.rsplit(".", 1)[1].lower()
                sname = f"bike_{int(datetime.datetime.utcnow().timestamp())}_{idx+1}_{uuid.uuid4().hex[:6]}.{ext}"
                f.save(os.path.join(UPLOAD_DIR, sname))
                uploaded_urls.append(f"/uploads/{sname}")'''

repl_add_bike_img = '''                ext = f.filename.rsplit(".", 1)[1].lower()
                sname = f"bike_{int(datetime.datetime.utcnow().timestamp())}_{idx+1}_{uuid.uuid4().hex[:6]}.{ext}"
                dest_fpath = os.path.join(UPLOAD_DIR, sname)
                f.save(dest_fpath)
                save_durable_image(sname, dest_fpath, f.mimetype)
                uploaded_urls.append(f"/uploads/{sname}")'''

assert target_add_bike_img in content, "target_add_bike_img not found"
content = content.replace(target_add_bike_img, repl_add_bike_img, 1)

target_seller_id = '''    sphone = data.get("seller_phone") or data.get("mobileNum") or ""
    seller_id = data.get("seller_id") or session.get("user_id") or None
    # Check caller authentication to set status and listing_status correctly'''

repl_seller_id = '''    sphone = data.get("seller_phone") or data.get("mobileNum") or ""
    seller_id = data.get("seller_id") or session.get("user_id") or None
    if not seller_id:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr and "Bearer" in auth_hdr:
            try:
                dec_tok = jwt.decode(auth_hdr.split()[1], JWT_SECRET, algorithms=["HS256"])
                seller_id = dec_tok.get("id") or dec_tok.get("user_id")
            except Exception:
                pass
    # Check caller authentication to set status and listing_status correctly'''

assert target_seller_id in content, "target_seller_id not found"
content = content.replace(target_seller_id, repl_seller_id, 1)
print("4. Updated add_bike_api for durable images and seller_id.")

# -----------------------------------------------------------------------------
# 5. Update auth_demo_google_api to ensure demo user exists in TiDB
# -----------------------------------------------------------------------------
target_demo_auth = '''    import jwt
    user = IN_MEMORY_STORE["users"][0]
    payload = {'''

repl_demo_auth = '''    import jwt
    user = find_or_create_google_user({
        "google_id": "demo-google-user-001",
        "name": "Praveen Demo Rider",
        "email": "rider@smrmotors.com",
        "profile_image": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80"
    })
    payload = {'''

assert target_demo_auth in content, "target_demo_auth not found"
content = content.replace(target_demo_auth, repl_demo_auth, 1)
print("5. Updated auth_demo_google_api to persist demo user in TiDB.")

# -----------------------------------------------------------------------------
# 6. Update upload_images_api and upload_files_legacy to call save_durable_image
# -----------------------------------------------------------------------------
target_upload_images = '''        unique_name = f"bike_{int(datetime.datetime.utcnow().timestamp())}_{idx+1}_{uuid.uuid4().hex[:6]}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, unique_name))
        saved_images.append({'''

repl_upload_images = '''        unique_name = f"bike_{int(datetime.datetime.utcnow().timestamp())}_{idx+1}_{uuid.uuid4().hex[:6]}.{ext}"
        dest_p = os.path.join(UPLOAD_DIR, unique_name)
        f.save(dest_p)
        save_durable_image(unique_name, dest_p, f.mimetype)
        saved_images.append({'''

assert target_upload_images in content, "target_upload_images not found"
content = content.replace(target_upload_images, repl_upload_images, 1)

target_upload_legacy = '''            fn = f"{int(datetime.datetime.utcnow().timestamp())}-{secure_filename(f.filename)}"
            f.save(os.path.join(UPLOAD_DIR, fn))
            saved.append([fn, f"/uploads/{fn}"])'''

repl_upload_legacy = '''            fn = f"{int(datetime.datetime.utcnow().timestamp())}-{secure_filename(f.filename)}"
            dest_leg = os.path.join(UPLOAD_DIR, fn)
            f.save(dest_leg)
            save_durable_image(fn, dest_leg, f.mimetype)
            saved.append([fn, f"/uploads/{fn}"])'''

assert target_upload_legacy in content, "target_upload_legacy not found"
content = content.replace(target_upload_legacy, repl_upload_legacy, 1)
print("6. Updated upload_images_api and upload_files_legacy.")

# -----------------------------------------------------------------------------
# 7. Update User Endpoints (lines 6140-6417)
# -----------------------------------------------------------------------------
target_user_endpoints = '''@app.route("/api/users/dashboard", methods=["GET"])
def user_dashboard_metrics():
    """
    Returns real-time counts from TiDB Cloud:
    Total, Pending, Approved, Rejected, Sold Out Listings & Pending Enquiries.
    """
    stats = {
        "total_listings": 0,
        "pending_listings": 0,
        "approved_listings": 0,
        "rejected_listings": 0,
        "sold_listings": 0,
        "pending_enquiries": 0
    }
    recent_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                  COUNT(*) as total_listings,
                  COUNT(CASE WHEN status = 'pending' AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as pending_listings,
                  COUNT(CASE WHEN status IN ('approved', 'published') AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as approved_listings,
                  COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_listings,
                  COUNT(CASE WHEN status = 'soldout' OR isSoldout = 1 THEN 1 END) as sold_listings
                FROM bikes
            """)
            row = cursor.fetchone()
            if row:
                for k, v in row.items():
                    stats[k] = int(v or 0)

            cursor.execute("SELECT COUNT(*) as pending_enquiries FROM enquiries WHERE status = 'pending'")
            enq_row = cursor.fetchone()
            if enq_row:
                stats["pending_enquiries"] = int(enq_row.get("pending_enquiries") or 0)

            cursor.execute("SELECT * FROM bikes ORDER BY id DESC LIMIT 5")
            recent_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not recent_bikes:
        bikes = IN_MEMORY_STORE["bikes"]
        stats = {
            "total_listings": len(bikes),
            "pending_listings": len([b for b in bikes if b.get("status") == "pending"]),
            "approved_listings": len([b for b in bikes if b.get("status") in ("approved", "published")]),
            "rejected_listings": len([b for b in bikes if b.get("status") == "rejected"]),
            "sold_listings": len([b for b in bikes if b.get("status") == "soldout" or b.get("isSoldout") == 1]),
            "pending_enquiries": len(IN_MEMORY_STORE["enquiries"])
        }
        recent_bikes = bikes[:5]

    return jsonify({
        "success": True,
        "data": {
            "stats": stats,
            "my_listings": [_normalize_bike(b, is_admin=False) for b in recent_bikes]
        }
    })

@app.route("/api/users/listings", methods=["GET"])
def user_my_listings():
    status_filter = (request.args.get("status") or "").strip().lower()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 6)))
    except (ValueError, TypeError):
        limit = 6

    bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            rows = cursor.fetchall()
            if rows: bikes = rows
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not bikes:
        bikes = IN_MEMORY_STORE["bikes"]

    normalized = [_normalize_bike(b, is_admin=False) for b in bikes]

    if status_filter:
        if status_filter == "pending":
            normalized = [b for b in normalized if b.get("status") == "pending" and b.get("isSoldout") != 1]
        elif status_filter in ("approved", "published"):
            normalized = [b for b in normalized if b.get("status") in ("approved", "published") and b.get("isSoldout") != 1]
        elif status_filter == "rejected":
            normalized = [b for b in normalized if b.get("status") == "rejected"]
        elif status_filter in ("soldout", "sold"):
            normalized = [b for b in normalized if b.get("status") == "soldout" or b.get("isSoldout") == 1]

    total = len(normalized)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = normalized[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "bikes": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/users/negotiations", methods=["GET"])
def user_my_negotiations():
    bikes = [_normalize_bike(b, is_admin=False) for b in IN_MEMORY_STORE["bikes"]]
    negs = [b for b in bikes if b.get("listing_status") in ("price_offered", "seller_accepted", "seller_rejected")]
    return jsonify({"success": True, "data": negs})

@app.route("/api/users/enquiries", methods=["GET"])
def user_my_enquiries():
    enqs = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC LIMIT 50")
            enqs = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not enqs:
        enqs = IN_MEMORY_STORE["enquiries"]
    return jsonify({"success": True, "data": enqs, "enquiries": enqs})

@app.route("/api/users/favorites", methods=["GET", "POST"])
def user_favorites_api():
    user_id = session.get("user_id") or 1
    if request.method == "POST":
        data = request.get_json() or {}
        bike_id = data.get("bike_id")
        if not bike_id:
            return jsonify({"success": False, "message": "bike_id required"}), 400
        conn = get_db()
        is_fav = True
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM favorites WHERE user_id = %s AND bike_id = %s", (user_id, bike_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("DELETE FROM favorites WHERE user_id = %s AND bike_id = %s", (user_id, bike_id))
                    is_fav = False
                else:
                    cursor.execute("INSERT INTO favorites (user_id, bike_id) VALUES (%s, %s)", (user_id, bike_id))
                    is_fav = True
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                if conn:
                    try: conn.close()
                    except Exception: pass
        return jsonify({"success": True, "favorited": is_fav, "message": "Favorites updated"})

    # GET favorites
    fav_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.* FROM favorites f
                JOIN bikes b ON f.bike_id = b.id
                WHERE f.user_id = %s
                ORDER BY f.id DESC
            """, (user_id,))
            fav_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not fav_bikes:
        fav_bikes = [b for b in IN_MEMORY_STORE["bikes"] if b.get("featured") == 1]
    return jsonify({"success": True, "data": [_normalize_bike(b, is_admin=False) for b in fav_bikes]})

@app.route("/api/users/notifications", methods=["GET"])
def user_notifications_api():
    conn = get_db()
    notifs = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM notifications WHERE target_role = 'user' ORDER BY id DESC LIMIT 30")
            notifs = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not notifs:
        notifs = [n for n in IN_MEMORY_STORE.get("notifications", []) if n.get("target_role") == "user"]
    return jsonify({"success": True, "data": notifs, "notifications": notifs})

@app.route("/api/users/notifications/<int:notif_id>/read", methods=["PUT", "POST"])
def user_mark_notification_read(notif_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (notif_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for n in IN_MEMORY_STORE.get("notifications", []):
        if n.get("id") == notif_id:
            n["is_read"] = 1
    return jsonify({"success": True, "message": "Notification marked as read"})

@app.route("/api/users/notifications/read-all", methods=["PUT", "POST"])
def user_mark_all_notifications_read():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE target_role = 'user'")
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for n in IN_MEMORY_STORE.get("notifications", []):
        if n.get("target_role") == "user":
            n["is_read"] = 1
    return jsonify({"success": True, "message": "All notifications marked as read"})

@app.route("/api/users/profile", methods=["GET", "PUT"])
def user_profile_api():
    if request.method == "PUT":
        data = request.get_json() or {}
        user = IN_MEMORY_STORE["users"][0]
        if "name" in data: user["name"] = data["name"]
        if "phone" in data: user["phone"] = data["phone"]
        return jsonify({"success": True, "message": "Profile updated successfully", "user": user})
    return jsonify({"success": True, "user": IN_MEMORY_STORE["users"][0]})'''

repl_user_endpoints = '''@app.route("/api/users/dashboard", methods=["GET"])
def user_dashboard_metrics():
    """
    Returns real-time dashboard counts and recent listings for the current user from TiDB Cloud.
    Guaranteed permanent database persistence. Never falls back to mock in-memory data.
    """
    stats = {
        "total_listings": 0,
        "pending_listings": 0,
        "approved_listings": 0,
        "rejected_listings": 0,
        "sold_listings": 0,
        "pending_enquiries": 0
    }
    recent_bikes = []
    u_id, u_data = get_current_user_profile()
    u_phone = (u_data.get("phone") or "").strip() if u_data else ""
    u_name = (u_data.get("name") or "").strip() if u_data else ""
    u_email = (u_data.get("email") or "").strip() if u_data else ""

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if u_id:
                # Metrics for this user's listings
                cursor.execute("""
                    SELECT
                      COUNT(*) as total_listings,
                      COUNT(CASE WHEN status = 'pending' AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as pending_listings,
                      COUNT(CASE WHEN status IN ('approved', 'published') AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as approved_listings,
                      COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_listings,
                      COUNT(CASE WHEN status = 'soldout' OR isSoldout = 1 THEN 1 END) as sold_listings
                    FROM bikes
                    WHERE seller_id = %s OR (seller_phone = %s AND %s != '') OR (seller_name = %s AND %s != '')
                """, (u_id, u_phone, u_phone, u_name, u_name))
                row = cursor.fetchone()
                if row:
                    for k, v in row.items():
                        stats[k] = int(v or 0)

                cursor.execute("""
                    SELECT COUNT(*) as pending_enquiries FROM enquiries
                    WHERE status = 'pending' AND (email = %s OR mobile = %s)
                """, (u_email, u_phone))
                enq_row = cursor.fetchone()
                if enq_row:
                    stats["pending_enquiries"] = int(enq_row.get("pending_enquiries") or 0)

                cursor.execute("""
                    SELECT * FROM bikes
                    WHERE seller_id = %s OR (seller_phone = %s AND %s != '') OR (seller_name = %s AND %s != '')
                    ORDER BY id DESC LIMIT 5
                """, (u_id, u_phone, u_phone, u_name, u_name))
                recent_bikes = cursor.fetchall() or []
            else:
                # Unauthenticated overview
                cursor.execute("""
                    SELECT
                      COUNT(*) as total_listings,
                      COUNT(CASE WHEN status = 'pending' AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as pending_listings,
                      COUNT(CASE WHEN status IN ('approved', 'published') AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as approved_listings,
                      COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_listings,
                      COUNT(CASE WHEN status = 'soldout' OR isSoldout = 1 THEN 1 END) as sold_listings
                    FROM bikes
                """)
                row = cursor.fetchone()
                if row:
                    for k, v in row.items():
                        stats[k] = int(v or 0)
                recent_bikes = []

            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] user_dashboard_metrics error:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({
        "success": True,
        "data": {
            "stats": stats,
            "my_listings": [_normalize_bike(b, is_admin=False) for b in recent_bikes]
        }
    })

@app.route("/api/users/listings", methods=["GET"])
def user_my_listings():
    """
    Returns paginated motorcycle listings belonging strictly to the current user.
    """
    status_filter = (request.args.get("status") or "").strip().lower()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 6)))
    except (ValueError, TypeError):
        limit = 6

    u_id, u_data = get_current_user_profile()
    if not u_id:
        return jsonify({
            "success": True,
            "data": [],
            "bikes": [],
            "pagination": {"total": 0, "page": page, "limit": limit, "totalPages": 1, "hasNext": False, "hasPrev": False, "start": 0, "end": 0}
        })

    u_phone = (u_data.get("phone") or "").strip() if u_data else ""
    u_name = (u_data.get("name") or "").strip() if u_data else ""

    bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM bikes
                WHERE seller_id = %s OR (seller_phone = %s AND %s != '') OR (seller_name = %s AND %s != '')
                ORDER BY id DESC
            """, (u_id, u_phone, u_phone, u_name, u_name))
            bikes = cursor.fetchall() or []
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] user_my_listings error:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    normalized = [_normalize_bike(b, is_admin=False) for b in bikes]

    if status_filter:
        if status_filter == "pending":
            normalized = [b for b in normalized if b.get("status") == "pending" and b.get("isSoldout") != 1]
        elif status_filter in ("approved", "published"):
            normalized = [b for b in normalized if b.get("status") in ("approved", "published") and b.get("isSoldout") != 1]
        elif status_filter == "rejected":
            normalized = [b for b in normalized if b.get("status") == "rejected"]
        elif status_filter in ("soldout", "sold"):
            normalized = [b for b in normalized if b.get("status") == "soldout" or b.get("isSoldout") == 1]

    total = len(normalized)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = normalized[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "bikes": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/users/negotiations", methods=["GET"])
def user_my_negotiations():
    """Returns price negotiations for the current user's listings."""
    u_id, u_data = get_current_user_profile()
    if not u_id:
        return jsonify({"success": True, "data": []})

    u_phone = (u_data.get("phone") or "").strip() if u_data else ""
    u_name = (u_data.get("name") or "").strip() if u_data else ""

    negs = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM bikes
                WHERE (seller_id = %s OR (seller_phone = %s AND %s != '') OR (seller_name = %s AND %s != ''))
                  AND listing_status IN ('price_offered', 'seller_accepted', 'seller_rejected')
                ORDER BY id DESC
            """, (u_id, u_phone, u_phone, u_name, u_name))
            rows = cursor.fetchall() or []
            negs = [_normalize_bike(b, is_admin=False) for b in rows]
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({"success": True, "data": negs})

@app.route("/api/users/enquiries", methods=["GET"])
def user_my_enquiries():
    """Returns enquiries submitted by or relating to the current user."""
    u_id, u_data = get_current_user_profile()
    enqs = []
    if u_data:
        u_email = (u_data.get("email") or "").strip()
        u_phone = (u_data.get("phone") or "").strip()
        conn = get_db()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM enquiries
                    WHERE email = %s OR (mobile = %s AND %s != '') OR customer_id = %s
                    ORDER BY id DESC LIMIT 50
                """, (u_email, u_phone, u_phone, u_id))
                enqs = cursor.fetchall() or []
                cursor.close()
                conn.close()
            except Exception:
                if conn:
                    try: conn.close()
                    except Exception: pass

    return jsonify({"success": True, "data": enqs, "enquiries": enqs})

@app.route("/api/users/favorites", methods=["GET", "POST"])
def user_favorites_api():
    """
    Manages favorite bikes permanently in TiDB Cloud favorites table.
    Never falls back to mock demo bikes when empty.
    """
    u_id, _ = get_current_user_profile()
    if not u_id:
        u_id = session.get("user_id") or 1

    if request.method == "POST":
        data = request.get_json() or {}
        bike_id = data.get("bike_id")
        if not bike_id:
            return jsonify({"success": False, "message": "bike_id required"}), 400
        conn = get_db()
        is_fav = True
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM favorites WHERE user_id = %s AND bike_id = %s", (u_id, bike_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("DELETE FROM favorites WHERE user_id = %s AND bike_id = %s", (u_id, bike_id))
                    is_fav = False
                else:
                    cursor.execute("INSERT INTO favorites (user_id, bike_id) VALUES (%s, %s)", (u_id, bike_id))
                    is_fav = True
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                if conn:
                    try: conn.close()
                    except Exception: pass
        return jsonify({"success": True, "favorited": is_fav, "message": "Favorites updated"})

    # GET favorites
    fav_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.* FROM favorites f
                JOIN bikes b ON f.bike_id = b.id
                WHERE f.user_id = %s
                ORDER BY f.id DESC
            """, (u_id,))
            fav_bikes = cursor.fetchall() or []
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({"success": True, "data": [_normalize_bike(b, is_admin=False) for b in fav_bikes]})

@app.route("/api/users/notifications", methods=["GET"])
def user_notifications_api():
    """Returns persistent notifications for the current user from TiDB Cloud."""
    u_id, _ = get_current_user_profile()
    conn = get_db()
    notifs = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if u_id:
                cursor.execute("""
                    SELECT * FROM notifications
                    WHERE target_role = 'user' AND (user_id IS NULL OR user_id = %s)
                    ORDER BY id DESC LIMIT 30
                """, (u_id,))
            else:
                cursor.execute("SELECT * FROM notifications WHERE target_role = 'user' ORDER BY id DESC LIMIT 30")
            notifs = cursor.fetchall() or []
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({"success": True, "data": notifs, "notifications": notifs})

@app.route("/api/users/notifications/<int:notif_id>/read", methods=["PUT", "POST"])
def user_mark_notification_read(notif_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (notif_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "message": "Notification marked as read"})

@app.route("/api/users/notifications/read-all", methods=["PUT", "POST"])
def user_mark_all_notifications_read():
    u_id, _ = get_current_user_profile()
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            if u_id:
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE target_role = 'user' AND (user_id IS NULL OR user_id = %s)", (u_id,))
            else:
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE target_role = 'user'")
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "message": "All notifications marked as read"})

@app.route("/api/users/profile", methods=["GET", "PUT"])
def user_profile_api():
    """
    Manages user profile permanently in TiDB Cloud MySQL users table.
    Updates name and phone, commits to database, and returns fresh record.
    """
    u_id, u_data = get_current_user_profile()
    if not u_id or not u_data:
        return jsonify({"success": False, "message": "Authentication required. Please sign in."}), 401

    if request.method == "PUT":
        data = request.get_json() or {}
        new_name = (data.get("name") or "").strip()
        new_phone = (data.get("phone") or "").strip()

        conn = get_db()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    UPDATE users
                    SET name = CASE WHEN %s != '' THEN %s ELSE name END,
                        phone = CASE WHEN %s != '' THEN %s ELSE phone END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (new_name, new_name, new_phone, new_phone, u_id))
                conn.commit()

                cursor.execute("SELECT id, google_id, name, email, profile_image, phone, role, is_active, created_at FROM users WHERE id = %s LIMIT 1", (u_id,))
                fresh_user = cursor.fetchone()
                cursor.close()
                conn.close()
                if fresh_user:
                    u_data = fresh_user
            except Exception as e:
                print("[Database] Profile update error:", e)
                if conn:
                    try: conn.close()
                    except Exception: pass
                return jsonify({"success": False, "message": f"Database update error: {str(e)}"}), 500

        return jsonify({"success": True, "message": "Profile updated successfully", "user": u_data})

    return jsonify({"success": True, "user": u_data})'''

assert target_user_endpoints in content, "target_user_endpoints not found"
content = content.replace(target_user_endpoints, repl_user_endpoints, 1)
print("7. Updated all User Endpoints for permanent TiDB persistence.")

# -----------------------------------------------------------------------------
# 8. Fix Admin Users API: No mock fallback when empty
# -----------------------------------------------------------------------------
target_admin_users = '''    if not all_users:
        all_users = IN_MEMORY_STORE["users"]'''

repl_admin_users = '''    if not all_users and not get_db():
        all_users = IN_MEMORY_STORE["users"]'''

assert target_admin_users in content, "target_admin_users not found"
content = content.replace(target_admin_users, repl_admin_users, 1)

target_admin_single_user = '''    if not user:
        for u in IN_MEMORY_STORE["users"]:
            if u.get("id") == user_id:
                user = u
                break
        listings = [b for b in IN_MEMORY_STORE["bikes"] if b.get("seller_id") == user_id]
        enquiries = [e for e in IN_MEMORY_STORE["enquiries"] if e.get("email") == user.get("email")]'''

repl_admin_single_user = '''    if not user and not get_db():
        for u in IN_MEMORY_STORE["users"]:
            if u.get("id") == user_id:
                user = u
                break
        listings = [b for b in IN_MEMORY_STORE["bikes"] if b.get("seller_id") == user_id]
        enquiries = [e for e in IN_MEMORY_STORE["enquiries"] if e.get("email") == user.get("email")]'''

assert target_admin_single_user in content, "target_admin_single_user not found"
content = content.replace(target_admin_single_user, repl_admin_single_user, 1)
print("8. Updated Admin Users API.")

# -----------------------------------------------------------------------------
# 9. Fix Admin Audit Logs API & Reports fallback
# -----------------------------------------------------------------------------
target_audit_api = '''@app.route("/api/admin/audit-logs", methods=["GET"])
def admin_audit_logs_api():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admin_audit_logs ORDER BY id DESC LIMIT 100")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return jsonify({"success": True, "data": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "data": IN_MEMORY_STORE["audit_logs"]})'''

repl_audit_api = '''@app.route("/api/admin/audit-logs", methods=["GET"])
def admin_audit_logs_api():
    rows = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admin_audit_logs ORDER BY id DESC LIMIT 100")
            rows = cursor.fetchall() or []
            cursor.close()
            conn.close()
            return jsonify({"success": True, "data": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not get_db():
        rows = IN_MEMORY_STORE.get("audit_logs", [])
    return jsonify({"success": True, "data": rows})'''

assert target_audit_api in content, "target_audit_api not found"
content = content.replace(target_audit_api, repl_audit_api, 1)
print("9. Updated Admin Audit Logs API.")

with open(APP_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: my-node-app/app.py patched with complete permanent persistence!")
