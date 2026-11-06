import os
import sys

backend_file = 'my-node-app/app.py'
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace admin_approve_bike
start_marker = "def admin_approve_bike(bike_id):"
idx_start = content.find(start_marker)
assert idx_start != -1

next_route_idx = content.find("@app.route(\"/api/admin/bikes/<int:bike_id>/reject\"", idx_start)
assert next_route_idx != -1

new_approve_code = """def admin_approve_bike(bike_id):
    data = request.get_json(silent=True) or {}
    admin_username = g.admin.get("username", "admin")
    admin_id = g.admin.get("id") or 1

    conn = get_db()
    current_status = None
    current_listing_status = None
    bike_title = f"Motorcycle #{bike_id}"
    seller_id = None
    seller_name = None
    seller_phone = None
    bike_brand = "Motorcycle"
    bike_model = ""

    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT status, listing_status, title, brand, model, seller_id, seller_name, seller_phone FROM bikes WHERE id = %s", (bike_id,))
            row = cursor.fetchone()
            if row:
                current_status = row.get("status")
                current_listing_status = row.get("listing_status")
                bike_title = row.get("title") or bike_title
                bike_brand = row.get("brand") or "Motorcycle"
                bike_model = row.get("model") or ""
                seller_id = row.get("seller_id")
                seller_name = row.get("seller_name")
                seller_phone = row.get("seller_phone")
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # If seller_id is missing, try looking up users by phone
    if not seller_id and seller_phone:
        try:
            s_conn = get_db()
            if s_conn:
                s_cur = s_conn.cursor(dictionary=True)
                s_cur.execute("SELECT id, name FROM users WHERE phone = %s OR phone LIKE %s LIMIT 1", (seller_phone, f"%{seller_phone[-10:]}%"))
                s_user = s_cur.fetchone()
                if s_user:
                    seller_id = s_user.get("id")
                    seller_name = seller_name or s_user.get("name")
                s_cur.close()
                s_conn.close()
        except Exception:
            pass

    approved_price = None
    if g.admin.get("role") == "superadmin":
        raw_app_price = data.get("approved_price") if "approved_price" in data else (data.get("public_selling_price") if "public_selling_price" in data else data.get("price"))
        if raw_app_price is not None and str(raw_app_price).strip() != "":
            try:
                approved_price = float(raw_app_price)
                if approved_price < 0 or approved_price > 1000000:
                    return jsonify({"success": False, "message": "Bike price must be between ₹0 and ₹10,00,000."}), 400
            except (ValueError, TypeError):
                return jsonify({"success": False, "message": "Bike price must be between ₹0 and ₹10,00,000."}), 400

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Update status to approved & accepted, update timestamp so it moves to top of listing
            if approved_price:
                cursor.execute(\"\"\"
                    UPDATE bikes SET
                      status = 'approved',
                      listing_status = 'accepted',
                      isSoldout = 0,
                      price = %s,
                      public_selling_price = %s,
                      approved_by = %s,
                      approved_at = CURRENT_TIMESTAMP,
                      updated_at = CURRENT_TIMESTAMP,
                      published_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                \"\"\", (approved_price, approved_price, admin_username, bike_id))
                cursor.execute("UPDATE bikesforsale SET isAccepted = 1, isSoldout = 0, sellingPrice = %s WHERE id = %s", (str(approved_price), bike_id))
            else:
                cursor.execute(\"\"\"
                    UPDATE bikes SET
                      status = 'approved',
                      listing_status = 'accepted',
                      isSoldout = 0,
                      approved_by = %s,
                      approved_at = CURRENT_TIMESTAMP,
                      updated_at = CURRENT_TIMESTAMP,
                      published_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                \"\"\", (admin_username, bike_id))
                cursor.execute("UPDATE bikesforsale SET isAccepted = 1, isSoldout = 0 WHERE id = %s", (bike_id,))

            # Record status transition in listing_status_history
            cursor.execute(\"\"\"
                INSERT INTO listing_status_history (bike_id, old_status, new_status, changed_by, reason)
                VALUES (%s, %s, 'accepted', %s, 'Bike submission accepted by admin; document verification initiated')
            \"\"\", (bike_id, current_status or "pending", admin_username))

            # Send automatic customer message through existing customer-admin chat system
            cust_name = seller_name or "Rider"
            acceptance_msg = f\"\"\"Hello {cust_name},

Good news! Your bike submission for {bike_brand} {bike_model} has been accepted by SMR Motors.

To continue the selling process, please submit the required bike ownership documents.

Required documents:
1. RC Book (Registration Certificate)
2. Valid insurance document
3. Owner identity proof
4. Other relevant vehicle documents, if applicable.

Please upload clear copies through your SMR Motors account or contact our team for assistance.

Thank you,
SMR Motors Team\"\"\"

            if seller_id:
                # Check for existing conversation for this customer and bike
                cursor.execute(\"\"\"
                    SELECT id FROM chat_conversations
                    WHERE user_id = %s AND (bike_id = %s OR subject LIKE %s)
                    ORDER BY id DESC LIMIT 1
                \"\"\", (seller_id, bike_id, f"%{bike_brand}%"))
                conv_row = cursor.fetchone()
                if conv_row:
                    conv_id = conv_row["id"]
                    cursor.execute("UPDATE chat_conversations SET bike_id = %s, status = 'open', updated_at = CURRENT_TIMESTAMP WHERE id = %s", (bike_id, conv_id))
                else:
                    cursor.execute(\"\"\"
                        INSERT INTO chat_conversations (user_id, bike_id, subject, status)
                        VALUES (%s, %s, %s, 'open')
                    \"\"\", (seller_id, bike_id, f"Inquiry about {bike_brand} {bike_model}"))
                    conv_id = cursor.lastrowid

                # Do not send repeated acceptance messages when the admin clicks multiple times
                cursor.execute(\"\"\"
                    SELECT id FROM chat_messages
                    WHERE conversation_id = %s AND message LIKE %s
                    LIMIT 1
                \"\"\", (conv_id, "%has been accepted by SMR Motors%"))
                already_sent = cursor.fetchone()

                if not already_sent and conv_id:
                    cursor.execute(\"\"\"
                        INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message, is_read)
                        VALUES (%s, %s, 'admin', %s, 0)
                    \"\"\", (conv_id, admin_id, acceptance_msg))
                    cursor.execute(\"\"\"
                        UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
                    \"\"\", (conv_id,))

                # Create in-app dashboard notification
                try:
                    create_notification(
                        title="Bike Submission Accepted! Documents Required",
                        message=f"Good news! Your {bike_brand} {bike_model} submission has been accepted. Please upload ownership documents to proceed.",
                        user_id=seller_id,
                        target_role="user",
                        notif_type="success",
                        link=f"/profile.html?tab=listings&bike_id={bike_id}&action=upload_docs"
                    )
                except Exception:
                    pass

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    log_admin_action(admin_username, "approve_bike", "bike", bike_id, f"Accepted motorcycle submission #{bike_id} ({bike_title}) and requested documents")

    return jsonify({
        "success": True,
        "message": "Motorcycle submission accepted! Automatic document request message sent to customer."
    })
\n"""

content = content[:idx_start] + new_approve_code + content[next_route_idx:]

# 2. Add Document endpoints (upload, list, verify, download)
doc_endpoints = """
# ==============================================================================
# SECURE CUSTOMER MOTORCYCLE OWNERSHIP DOCUMENTS WORKFLOW
# RC Book, Insurance, Identity Proof, Vehicle Documents
# ==============================================================================

DOCUMENTS_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "secure_documents")
os.makedirs(DOCUMENTS_UPLOAD_FOLDER, exist_ok=True)
ALLOWED_DOC_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp"}
MAX_DOC_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def is_allowed_doc_filename(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

@app.route("/api/users/bikes/<int:bike_id>/documents", methods=["GET", "POST"])
def user_bike_documents_api(bike_id):
    \"\"\"
    Customer endpoint to submit and view ownership documents for an accepted bike submission.
    \"\"\"
    # Authenticate user from JWT or session
    user_id = None
    user_name = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header and "Bearer" in auth_header:
        try:
            import jwt
            tok = auth_header.split()[1]
            dec = jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
            user_id = dec.get("id") or dec.get("user_id")
            user_name = dec.get("name")
        except Exception:
            pass

    if not user_id:
        return jsonify({"success": False, "message": "Authentication required. Please sign in."}), 401

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, brand, model, seller_id, seller_name, status, listing_status FROM bikes WHERE id = %s", (bike_id,))
        bike = cursor.fetchone()
        if not bike:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Motorcycle listing not found."}), 404

        # Verify caller owns this listing
        if bike.get("seller_id") and int(bike.get("seller_id")) != int(user_id):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Unauthorized. You can only manage documents for your own motorcycle listings."}), 403

        if request.method == "POST":
            doc_type = request.form.get("document_type") or "rc_book"
            remarks = (request.form.get("notes") or "").strip()

            if "file" not in request.files and "document" not in request.files:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "No document file provided for upload."}), 400

            file_obj = request.files.get("file") or request.files.get("document")
            if not file_obj or file_obj.filename == "":
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "No document file selected."}), 400

            orig_filename = os.path.basename(file_obj.filename)
            if not is_allowed_doc_filename(orig_filename):
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "Invalid file type. Allowed: PDF, JPG, PNG, WEBP."}), 400

            # Generate secure server-side filename
            ext = orig_filename.rsplit(".", 1)[1].lower()
            import uuid, time
            secure_name = f"doc_{bike_id}_{doc_type}_{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
            file_disk_path = os.path.join(DOCUMENTS_UPLOAD_FOLDER, secure_name)
            file_obj.save(file_disk_path)
            file_size = os.path.getsize(file_disk_path)

            if file_size > MAX_DOC_SIZE_BYTES:
                try: os.remove(file_disk_path)
                except Exception: pass
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "File exceeds maximum 10MB limit."}), 400

            mime_type = file_obj.content_type or ("application/pdf" if ext == "pdf" else f"image/{ext}")

            # Insert into bike_documents
            cursor.execute(\"\"\"
                INSERT INTO bike_documents
                (bike_id, user_id, document_type, file_name, file_path, mime_type, file_size, status, admin_remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            \"\"\", (bike_id, user_id, doc_type, orig_filename, secure_name, mime_type, file_size, remarks or None))
            doc_id = cursor.lastrowid
            conn.commit()

            # Create notification for admin
            try:
                create_notification(
                    title="New Customer Document Uploaded",
                    message=f"Customer {user_name or 'Seller'} uploaded {doc_type.replace('_',' ').title()} for {bike.get('brand')} {bike.get('model')}.",
                    target_role="admin",
                    notif_type="info",
                    link=f"/admin.html#tab-approved-bikes"
                )
            except Exception:
                pass

            cursor.close()
            conn.close()
            return jsonify({
                "success": True,
                "message": f"{doc_type.replace('_',' ').title()} uploaded successfully! SMR Motors team will verify.",
                "document_id": doc_id
            }), 201

        # GET request: fetch documents for this bike
        cursor.execute(\"\"\"
            SELECT id, bike_id, user_id, document_type, file_name, mime_type, file_size, status, admin_remarks, verified_by, verified_at, created_at
            FROM bike_documents
            WHERE bike_id = %s
            ORDER BY id DESC
        \"\"\", (bike_id,))
        docs = cursor.fetchall() or []
        cursor.close()
        conn.close()

        for d in docs:
            d["download_url"] = f"/api/documents/{d['id']}/download"
            d["view_url"] = f"/api/documents/{d['id']}/view"

        return jsonify({"success": True, "data": docs, "documents": docs})
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/admin/bikes/<int:bike_id>/documents", methods=["GET"])
@admin_required
def admin_get_bike_documents(bike_id):
    \"\"\"
    Admin endpoint to view all ownership documents submitted by customer for a motorcycle.
    \"\"\"
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(\"\"\"
            SELECT d.id, d.bike_id, d.user_id, d.document_type, d.file_name, d.mime_type, d.file_size,
                   d.status, d.admin_remarks, d.verified_by, d.verified_at, d.created_at,
                   u.name AS user_name, u.email AS user_email, u.phone AS user_phone
            FROM bike_documents d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.bike_id = %s
            ORDER BY d.id DESC
        \"\"\", (bike_id,))
        docs = cursor.fetchall() or []
        cursor.close()
        conn.close()

        for d in docs:
            d["download_url"] = f"/api/documents/{d['id']}/download"
            d["view_url"] = f"/api/documents/{d['id']}/view"

        return jsonify({"success": True, "data": docs, "documents": docs})
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/admin/bikes/<int:bike_id>/documents/<int:doc_id>/verify", methods=["POST"])
@admin_required
def admin_verify_bike_document(bike_id, doc_id):
    \"\"\"
    Admin document verification: approve or reject with reason, and notify customer through chat.
    \"\"\"
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "approved").lower().strip()
    if new_status not in ("approved", "rejected", "pending"):
        return jsonify({"success": False, "message": "Status must be 'approved' or 'rejected'."}), 400

    remarks = (data.get("remarks") or data.get("reason") or "").strip()
    if new_status == "rejected" and not remarks:
        return jsonify({"success": False, "message": "A rejection reason / remark is required when rejecting documents."}), 400

    admin_username = g.admin.get("username", "admin")

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(\"\"\"
            SELECT d.id, d.bike_id, d.user_id, d.document_type, d.file_name,
                   b.title AS bike_title, b.brand AS bike_brand, b.model AS bike_model,
                   u.name AS customer_name
            FROM bike_documents d
            LEFT JOIN bikes b ON d.bike_id = b.id
            LEFT JOIN users u ON d.user_id = u.id
            WHERE d.id = %s AND d.bike_id = %s
        \"\"\", (doc_id, bike_id))
        doc_record = cursor.fetchone()
        if not doc_record:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Document record not found."}), 404

        cursor.execute(\"\"\"
            UPDATE bike_documents SET
              status = %s,
              admin_remarks = %s,
              verified_by = %s,
              verified_at = CURRENT_TIMESTAMP
            WHERE id = %s
        \"\"\", (new_status, remarks or None, admin_username, doc_id))

        user_id = doc_record.get("user_id")
        doc_type_label = doc_record.get("document_type", "document").replace("_", " ").title()
        bike_brand = doc_record.get("bike_brand") or "Motorcycle"
        bike_model = doc_record.get("bike_model") or ""
        cust_name = doc_record.get("customer_name") or "Valued Customer"

        # Notify customer through chat system
        if user_id:
            chat_status_text = "APPROVED" if new_status == "approved" else "REJECTED"
            chat_msg = f\"\"\"Hello {cust_name},

Update regarding your bike submission for {bike_brand} {bike_model}:

Your uploaded document ({doc_type_label}) has been {chat_status_text} by SMR Motors verification team.
\"\"\"
            if remarks:
                chat_msg += f\"\\nRemarks: {remarks}\\n\"

            if new_status == "rejected":
                chat_msg += \"\\nPlease upload a clear, updated copy through your SMR Motors account to proceed with the listing.\"
            else:
                chat_msg += \"\\nThank you for providing verified ownership documents.\"

            chat_msg += \"\\n\\nSMR Motors Operations Team\"

            cursor.execute(\"\"\"
                SELECT id FROM chat_conversations
                WHERE user_id = %s AND (bike_id = %s OR subject LIKE %s)
                ORDER BY id DESC LIMIT 1
            \"\"\", (user_id, bike_id, f"%{bike_brand}%"))
            conv_row = cursor.fetchone()
            if conv_row:
                conv_id = conv_row["id"]
            else:
                cursor.execute(\"\"\"
                    INSERT INTO chat_conversations (user_id, bike_id, subject, status)
                    VALUES (%s, %s, %s, 'open')
                \"\"\", (user_id, bike_id, f"Inquiry about {bike_brand} {bike_model}"))
                conv_id = cursor.lastrowid

            cursor.execute(\"\"\"
                INSERT INTO chat_messages (conversation_id, sender_id, sender_role, message, is_read)
                VALUES (%s, %s, 'admin', %s, 0)
            \"\"\", (conv_id, g.admin.get("id") or 1, chat_msg))
            cursor.execute(\"\"\"
                UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
            \"\"\", (conv_id,))

            # In-app notification
            create_notification(
                title=f"Document {chat_status_text}: {doc_type_label}",
                message=f"Your {doc_type_label} for {bike_brand} {bike_model} has been {new_status}. {remarks or ''}".strip(),
                user_id=user_id,
                target_role="user",
                notif_type="success" if new_status == "approved" else "warning",
                link=f"/profile.html?tab=listings&bike_id={bike_id}&action=upload_docs"
            )

        conn.commit()
        cursor.close()
        conn.close()

        log_admin_action(admin_username, "verify_document", "document", doc_id, f"Document #{doc_id} ({doc_type_label}) set to {new_status} for bike #{bike_id}")

        return jsonify({
            "success": True,
            "message": f"Document marked as {new_status}. Customer notified.",
            "status": new_status
        })
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/documents/<int:doc_id>/download", methods=["GET"])
@app.route("/api/documents/<int:doc_id>/view", methods=["GET"])
def download_secure_document(doc_id):
    \"\"\"
    Secure document delivery: viewable/downloadable only by authorized Admin/Superadmin or document owner.
    \"\"\"
    # Check admin auth
    is_admin = False
    admin_auth = request.headers.get("Authorization", "") or request.cookies.get("admin_token", "")
    admin_token = None
    if admin_auth and "Bearer" in admin_auth:
        admin_token = admin_auth.split()[1]
    elif admin_auth:
        admin_token = admin_auth

    if admin_token:
        try:
            import jwt
            dec = jwt.decode(admin_token, JWT_SECRET, algorithms=["HS256"])
            if dec.get("role") in ("admin", "superadmin") or "username" in dec:
                is_admin = True
        except Exception:
            pass

    # Check user auth
    caller_user_id = None
    user_token = request.args.get("token") or request.cookies.get("user_token")
    if not user_token and request.headers.get("Authorization"):
        hdr = request.headers.get("Authorization")
        if "Bearer" in hdr:
            user_token = hdr.split()[1]
    if user_token:
        try:
            import jwt
            dec = jwt.decode(user_token, JWT_SECRET, algorithms=["HS256"])
            caller_user_id = dec.get("id") or dec.get("user_id")
        except Exception:
            pass

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    doc = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bike_documents WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            try: conn.close()
            except Exception: pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    if not doc:
        return jsonify({"success": False, "message": "Document not found."}), 404

    # Authorization Check: only admin/superadmin OR the document owner can access
    if not is_admin:
        if not caller_user_id or int(caller_user_id) != int(doc.get("user_id", -1)):
            return jsonify({"success": False, "message": "Unauthorized. You do not have permission to view or download this document."}), 403

    filename_on_disk = doc.get("file_path")
    full_path = os.path.join(DOCUMENTS_UPLOAD_FOLDER, filename_on_disk)
    if not os.path.exists(full_path):
        return jsonify({"success": False, "message": "Document file not found on disk."}), 404

    from flask import send_from_directory
    as_attachment = (request.path.endswith("/download") or request.args.get("download") == "1")
    return send_from_directory(
        DOCUMENTS_UPLOAD_FOLDER,
        filename_on_disk,
        mimetype=doc.get("mime_type", "application/octet-stream"),
        as_attachment=as_attachment,
        download_name=doc.get("file_name", filename_on_disk)
    )
"""

if "/api/users/bikes/<int:bike_id>/documents" not in content:
    content += "\n" + doc_endpoints
    print("Added secure document endpoints to app.py")

with open(backend_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py with approval workflow and document endpoints successfully!")
