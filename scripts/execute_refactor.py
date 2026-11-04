import os
import py_compile
import sys

app_path = "my-node-app/app.py"

with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

print("Original app.py length:", len(code))

# Backup original
with open("my-node-app/app.py.bak", "w", encoding="utf-8") as f:
    f.write(code)
print("Backup created at my-node-app/app.py.bak")

# 1. Replace IN_MEMORY_STORE with empty dict
old_store_start = '# Seed In-Memory Store (Active fallback when MySQL is unreachable)\nIN_MEMORY_STORE = {'
old_store_end = '    ]\n}\n\ndef create_notification('

if old_store_start in code and old_store_end in code:
    idx1 = code.find(old_store_start)
    idx2 = code.find(old_store_end) + len('    ]\n}\n')
    new_store = '''# In-Memory Store (Empty placeholder structure; no fake demo records)
IN_MEMORY_STORE = {
    "bikes": [],
    "categories": [],
    "enquiries": [],
    "users": [],
    "favorites": [],
    "contact_messages": [],
    "contact_replies": [],
    "audit_logs": [],
    "price_negotiations": [],
    "bike_transactions": [],
    "notifications": []
}
'''
    code = code[:idx1] + new_store + code[idx2:]
    print("Step 1: Replaced IN_MEMORY_STORE with clean empty dictionary.")
else:
    print("Step 1 WARNING: Could not find exact IN_MEMORY_STORE markers!")

# 2. Remove automatic seeding of categories and bikes in initialize_database()
old_seed = '''        # Seed categories if empty
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            for cat in IN_MEMORY_STORE["categories"]:
                cursor.execute(
                    "INSERT INTO categories (category_name, image_url) VALUES (%s, %s)",
                    (cat["category_name"], cat["image_url"])
                )
            conn.commit()

        # Seed bikes if empty
        cursor.execute("SELECT COUNT(*) FROM bikes")
        if cursor.fetchone()[0] == 0:
            for b in IN_MEMORY_STORE["bikes"]:
                cursor.execute(
                    """INSERT INTO bikes (title, brand, model, year, price, kilometers_driven, fuel_type, transmission, description, images, seller_name, seller_phone, status, featured)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (b["title"], b["brand"], b["model"], b["year"], b["price"], b["kilometers_driven"], b["fuel_type"], b["transmission"], b["description"], json.dumps(b["images"]), b["seller_name"], b["seller_phone"], b["status"], b.get("featured", 0))
                )
                cursor.execute(
                    """INSERT INTO bikesforsale (listingTitle, makedFrom, bikeModel, bikeBuyingYear, bikePrice, sellingPrice, bikeKms, sellerName, mobileNum, description, isAccepted, isSoldout)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (b["listingTitle"], b["makedFrom"], b["bikeModel"], b["bikeBuyingYear"], b["bikePrice"], b["sellingPrice"], b["bikeKms"], b["sellerName"], b["mobileNum"], b["description"], b["isAccepted"], b["isSoldout"])
                )
            conn.commit()'''

if old_seed in code:
    code = code.replace(old_seed, '        # Categories and bikes are loaded exclusively from TiDB Cloud smr_motors database (No auto-seeding of fake demo data)')
    print("Step 2: Removed automatic categories and bikes seed logic from initialize_database().")
else:
    print("Step 2 WARNING: old_seed not found.")

# 3. get_bikes_api - Remove fallback to IN_MEMORY_STORE and return 503 if DB unavailable
old_bikes_api_block = '''    all_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            all_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_bikes:
        all_bikes = list(IN_MEMORY_STORE["bikes"])'''

new_bikes_api_block = '''    all_bikes = []
    conn = get_db()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Database connection unavailable. Please check TiDB Cloud connectivity."
        }), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
        all_bikes = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({
            "success": False,
            "message": f"Database query error: {str(e)}"
        }), 500'''

if old_bikes_api_block in code:
    code = code.replace(old_bikes_api_block, new_bikes_api_block)
    print("Step 3a: Updated get_bikes_api with pure TiDB queries & 503 error handling.")
else:
    print("Step 3a WARNING: old_bikes_api_block not found.")

# 3b. get_sold_bikes_api - Remove fallback
old_sold_api_block = '''    if not all_bikes:
        all_bikes = [b for b in IN_MEMORY_STORE["bikes"] if b.get("status") == "soldout" or b.get("isSoldout") == 1 or b.get("listing_status") == "soldout"]'''

new_sold_api_block = '''    if not conn and not all_bikes:
        return jsonify({
            "success": False,
            "message": "Database connection unavailable. Please check TiDB Cloud connectivity."
        }), 503'''

if old_sold_api_block in code:
    code = code.replace(old_sold_api_block, new_sold_api_block)
    print("Step 3b: Updated get_sold_bikes_api.")
else:
    print("Step 3b WARNING: old_sold_api_block not found.")

# 3c. get_single_bike_api
old_single_bike_block = '''    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            return jsonify({"success": True, "data": b, **b})
    return jsonify({"success": False, "message": "Bike not found"}), 404'''

new_single_bike_block = '''    return jsonify({"success": False, "message": "Motorcycle not found in database"}), 404'''

if old_single_bike_block in code:
    code = code.replace(old_single_bike_block, new_single_bike_block)
    print("Step 3c: Updated get_single_bike_api.")
else:
    print("Step 3c WARNING: old_single_bike_block not found.")

# 3d. get_categories
old_categories_block = '''def get_categories():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM categories ORDER BY id ASC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return jsonify({"success": True, "categories": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "categories": IN_MEMORY_STORE["categories"]})'''

new_categories_block = '''def get_categories():
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories ORDER BY id ASC")
        rows = cursor.fetchall() or []
        cursor.close()
        conn.close()
        return jsonify({"success": True, "categories": rows})
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_categories_block in code:
    code = code.replace(old_categories_block, new_categories_block)
    print("Step 3d: Updated get_categories.")
else:
    print("Step 3d WARNING: old_categories_block not found.")

# 4a. enquiries_api
old_enquiries_get = '''    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return jsonify({"success": True, "data": rows, "enquiries": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({"success": True, "data": IN_MEMORY_STORE["enquiries"], "enquiries": IN_MEMORY_STORE["enquiries"]})'''

new_enquiries_get = '''    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
        rows = cursor.fetchall() or []
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": rows, "enquiries": rows})
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_enquiries_get in code:
    code = code.replace(old_enquiries_get, new_enquiries_get)
    print("Step 4a: Updated enquiries_api GET.")
else:
    print("Step 4a WARNING: old_enquiries_get not found.")

# 4b. admin_enquiries_api
old_admin_enquiries = '''    all_enquiries = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                all_enquiries = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_enquiries:
        all_enquiries = IN_MEMORY_STORE["enquiries"]'''

new_admin_enquiries = '''    all_enquiries = []
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
        all_enquiries = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database query error: {str(e)}"}), 500'''

if old_admin_enquiries in code:
    code = code.replace(old_admin_enquiries, new_admin_enquiries)
    print("Step 4b: Updated admin_enquiries_api.")
else:
    print("Step 4b WARNING: old_admin_enquiries not found.")

# 5. admin_dashboard_api - remove in-memory fake override
old_dash_override = '''    # In-memory fallback if DB unreachable or empty
    if counts["total_bikes"] == 0 and IN_MEMORY_STORE.get("bikes"):
        mem_bikes = [b for b in IN_MEMORY_STORE["bikes"] if b.get("status") != "archived"]
        counts["total_bikes"] = len(mem_bikes)
        counts["pending_bikes"] = len([b for b in mem_bikes if (b.get("listing_status") == "pending" or b.get("status") == "pending") and not b.get("isSoldout") and b.get("status") not in ("sold", "soldout", "rejected")])
        counts["approved_bikes"] = len([b for b in mem_bikes if (b.get("listing_status") == "published" or b.get("status") == "approved") and not b.get("isSoldout") and b.get("status") not in ("sold", "soldout", "rejected")])
        counts["rejected_bikes"] = len([b for b in mem_bikes if b.get("status") == "rejected" or b.get("listing_status") == "rejected"])
        counts["sold_bikes"] = len([b for b in mem_bikes if b.get("status") in ("sold", "soldout") or b.get("isSoldout") == 1])
        counts["total_users"] = len(IN_MEMORY_STORE.get("users", []))
        counts["total_enquiries"] = len(IN_MEMORY_STORE.get("enquiries", []))
        if not recent_bikes_list:
            recent_bikes_list = mem_bikes[:10]
        if not recent_users_list:
            recent_users_list = IN_MEMORY_STORE.get("users", [])[:10]
        if not txs:
            txs = IN_MEMORY_STORE.get("bike_transactions", [])'''

new_dash_override = '''    # All dashboard statistics and financial metrics are calculated 100% from live TiDB Cloud tables'''

if old_dash_override in code:
    code = code.replace(old_dash_override, new_dash_override)
    print("Step 5: Removed admin_dashboard_api in-memory fake override.")
else:
    print("Step 5 WARNING: old_dash_override not found.")

# Also ensure admin_dashboard_api returns 503 if DB is not connected
old_dash_db = '''    conn = get_db()
    if conn:
        try:'''

new_dash_db = '''    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    if conn:
        try:'''

# Replace only inside admin_dashboard_api
dash_idx = code.find('def admin_dashboard_api():')
if dash_idx != -1:
    after_dash = code[dash_idx:]
    sub_old = '    conn = get_db()\n    if conn:\n        try:'
    sub_new = '    conn = get_db()\n    if not conn:\n        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503\n    if conn:\n        try:'
    if sub_old in after_dash:
        after_dash = after_dash.replace(sub_old, sub_new, 1)
        code = code[:dash_idx] + after_dash
        print("Step 5b: Added 503 check to admin_dashboard_api.")

# 6. admin_listings_paginated & admin_bikes_api
old_admin_listings = '''    bikes = IN_MEMORY_STORE["bikes"]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            db_bikes = cursor.fetchall()
            if db_bikes: bikes = db_bikes
            cursor.close()
            conn.close()
        except Exception:
            pass'''

new_admin_listings = '''    bikes = []
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
        bikes = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_admin_listings in code:
    code = code.replace(old_admin_listings, new_admin_listings)
    print("Step 6a: Updated admin_listings_paginated.")
else:
    print("Step 6a WARNING: old_admin_listings not found.")

old_admin_bikes = '''    all_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            all_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_bikes:
        all_bikes = IN_MEMORY_STORE["bikes"]'''

new_admin_bikes = '''    all_bikes = []
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
        all_bikes = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_admin_bikes in code:
    code = code.replace(old_admin_bikes, new_admin_bikes)
    print("Step 6b: Updated admin_bikes_api.")
else:
    print("Step 6b WARNING: old_admin_bikes not found.")

# 7. admin_sold_bikes_api
old_admin_sold = '''    if not sold_records:
        # Fallback to in-memory store
        for b in IN_MEMORY_STORE["bikes"]:
            b_st = str(b.get("status") or "").lower()
            b_lst = str(b.get("listing_status") or "").lower()
            if b.get("isSoldout") == 1 or b_st in ("sold", "soldout") or b_lst in ("sold", "soldout"):
                sold_records.append(b)'''

new_admin_sold = '''    if not conn and not sold_records:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503'''

if old_admin_sold in code:
    code = code.replace(old_admin_sold, new_admin_sold)
    print("Step 7: Updated admin_sold_bikes_api.")
else:
    print("Step 7 WARNING: old_admin_sold not found.")

# 8. admin_users_api
old_admin_users = '''    all_users = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, google_id, name, email, profile_image, phone, role, is_active, last_login, created_at FROM users ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                all_users = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_users and not get_db():
        all_users = IN_MEMORY_STORE["users"]'''

new_admin_users = '''    all_users = []
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, google_id, name, email, profile_image, phone, role, is_active, last_login, created_at FROM users ORDER BY id DESC")
        all_users = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_admin_users in code:
    code = code.replace(old_admin_users, new_admin_users)
    print("Step 8: Updated admin_users_api.")
else:
    print("Step 8 WARNING: old_admin_users not found.")

# 9. admin_messages_api
old_admin_msgs = '''    messages = IN_MEMORY_STORE.get("contact_messages", [])
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC")
            db_msgs = cursor.fetchall()
            if db_msgs:
                messages = db_msgs
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass'''

new_admin_msgs = '''    messages = []
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC")
        messages = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_admin_msgs in code:
    code = code.replace(old_admin_msgs, new_admin_msgs)
    print("Step 9: Updated admin_messages_api.")
else:
    print("Step 9 WARNING: old_admin_msgs not found.")

# 10. Staff list API
old_staff_list = '''    if not staff_list:
        for u, acc in adminAccounts.items():
            staff_list.append({
                "id": len(staff_list) + 1,
                "username": u,
                "full_name": acc.get("name", u.capitalize()),
                "email": f"{u}@smrmotors.com",
                "phone": "+91 98765 43210",
                "role": normalize_admin_role(acc.get("role")),
                "is_active": 1,
                "last_login": None,
                "created_at": datetime.datetime.utcnow().isoformat()
            })'''

new_staff_list = '''    if not conn and not staff_list:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503'''

if old_staff_list in code:
    code = code.replace(old_staff_list, new_staff_list)
    print("Step 10: Updated staff_list API.")
else:
    print("Step 10 WARNING: old_staff_list not found.")

# 11. Notifications API
old_notifs = '''    notifs = IN_MEMORY_STORE["notifications"]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if target_role == "admin":
                cursor.execute("SELECT * FROM notifications WHERE target_role = 'admin' ORDER BY id DESC LIMIT 50")
            elif user_id:
                cursor.execute("SELECT * FROM notifications WHERE user_id = %s OR target_role = 'all' ORDER BY id DESC LIMIT 50", (user_id,))
            else:
                cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                notifs = rows
        except Exception:
            pass'''

new_notifs = '''    notifs = []
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        if target_role == "admin":
            cursor.execute("SELECT * FROM notifications WHERE target_role = 'admin' ORDER BY id DESC LIMIT 50")
        elif user_id:
            cursor.execute("SELECT * FROM notifications WHERE user_id = %s OR target_role = 'all' ORDER BY id DESC LIMIT 50", (user_id,))
        else:
            cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 50")
        notifs = cursor.fetchall() or []
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500'''

if old_notifs in code:
    code = code.replace(old_notifs, new_notifs)
    print("Step 11: Updated get_notifications_api.")
else:
    print("Step 11 WARNING: old_notifs not found.")

# 12. Staff activity & audit logs
old_staff_act = '''    if not logs:
        logs = IN_MEMORY_STORE.get("audit_logs", [])'''

new_staff_act = '''    if not conn and not logs:
        return jsonify({"success": False, "message": "Database connection unavailable."}), 503'''

if old_staff_act in code:
    code = code.replace(old_staff_act, new_staff_act)
    print("Step 12a: Updated staff activity API.")
else:
    print("Step 12a WARNING: old_staff_act not found.")

old_audit_logs = '''    if not get_db():
        rows = IN_MEMORY_STORE.get("audit_logs", [])
    return jsonify({"success": True, "data": rows})'''

new_audit_logs = '''    return jsonify({"success": True, "data": rows})'''

if old_audit_logs in code:
    code = code.replace(old_audit_logs, new_audit_logs)
    print("Step 12b: Updated audit logs API.")
else:
    print("Step 12b WARNING: old_audit_logs not found.")

# 13. Disable auth_demo_google_api
old_demo_auth = '''@app.route("/api/auth/demo-google", methods=["POST"])
@app.route("/auth/demo-google", methods=["POST"])
def auth_demo_google_api():
    """
    Instant demo sign-in for testing without a live Google Cloud Console OAuth Client.
    Supports 7-day remembered session.
    """'''

new_demo_auth = '''@app.route("/api/auth/demo-google", methods=["POST"])
@app.route("/auth/demo-google", methods=["POST"])
def auth_demo_google_api():
    return jsonify({"success": False, "message": "Demo sign-in disabled. Please sign in with Google."}), 403
def _unused_auth_demo_google_api():'''

if old_demo_auth in code:
    code = code.replace(old_demo_auth, new_demo_auth)
    print("Step 13: Disabled demo-google auth.")
else:
    print("Step 13 WARNING: old_demo_auth not found.")

# Save modified code
with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("\nVerifying syntax with py_compile...")
try:
    py_compile.compile(app_path, doraise=True)
    print("SUCCESS: my-node-app/app.py compiles cleanly!")
except Exception as e:
    print(f"COMPILE ERROR: {e}")
    # restore backup
    with open("my-node-app/app.py.bak", "r", encoding="utf-8") as f:
        bak = f.read()
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(bak)
    print("Restored from backup.")
    sys.exit(1)
