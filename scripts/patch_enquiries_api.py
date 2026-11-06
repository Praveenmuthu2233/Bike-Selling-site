import re

backend_file = 'my-node-app/app.py'
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's inspect the start and end of enquiries_api
start_marker = "def enquiries_api():"
idx_start = content.find(start_marker)
assert idx_start != -1

# Find the next route
next_route_idx = content.find("@app.route", idx_start)
assert next_route_idx != -1

old_func = content[idx_start:next_route_idx]

new_func = """def enquiries_api():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        new_id = None
        bike_id = data.get("bike_id")
        bike_title = data.get("bike_title", "Motorcycle Inquiry")
        name = (data.get("name") or data.get("customerName") or "").strip()
        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or data.get("mobile") or "").strip()
        msg = (data.get("message") or "Interested in this motorcycle. Please arrange test ride and contact me.").strip()
        status = "pending"
        user_id = data.get("user_id")

        # Automatically resolve authenticated user if token present or user_id provided
        auth_header = request.headers.get("Authorization", "")
        if auth_header and "Bearer" in auth_header:
            try:
                import jwt
                tok = auth_header.split()[1]
                dec = jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
                user_id = user_id or dec.get("id") or dec.get("user_id")
                if not name:
                    name = dec.get("name") or ""
                if not email:
                    email = dec.get("email") or ""
            except Exception:
                pass

        # If user_id is known, query users table to auto-fill any missing profile attributes
        if user_id:
            try:
                u_conn = get_db()
                if u_conn:
                    u_cur = u_conn.cursor(dictionary=True)
                    u_cur.execute("SELECT id, name, email, phone FROM users WHERE id = %s", (user_id,))
                    u_row = u_cur.fetchone()
                    u_cur.close()
                    u_conn.close()
                    if u_row:
                        name = name or u_row.get("name") or "Valued Customer"
                        email = email or u_row.get("email") or ""
                        phone = phone or u_row.get("phone") or ""
            except Exception:
                pass

        if not name:
            name = "Customer"

        # Reject enquiries on sold out bikes (Requirement 4)
        if bike_id:
            try:
                b_id_int = int(bike_id)
                check_sold = False
                c_conn = get_db()
                if c_conn:
                    try:
                        c_cur = c_conn.cursor(dictionary=True)
                        c_cur.execute("SELECT isSoldout, status, listing_status, title FROM bikes WHERE id = %s", (b_id_int,))
                        b_chk = c_cur.fetchone()
                        c_cur.close()
                        c_conn.close()
                        if b_chk:
                            b_st = str(b_chk.get("status") or "").lower()
                            b_lst = str(b_chk.get("listing_status") or "").lower()
                            if b_chk.get("isSoldout") == 1 or b_st in ("sold", "soldout") or b_lst in ("sold", "soldout"):
                                check_sold = True
                            if b_chk.get("title") and bike_title == "Motorcycle Inquiry":
                                bike_title = b_chk.get("title")
                    except Exception:
                        if c_conn:
                            try: c_conn.close()
                            except Exception: pass

                if check_sold:
                    return jsonify({"success": False, "message": "Enquiries are closed for this motorcycle as it has already been marked Sold Out."}), 400
            except (ValueError, TypeError):
                pass

        # Prevent duplicate submissions caused by repeated clicks (Scenario A / B debouncing)
        conn = get_db()
        if conn and bike_id:
            try:
                dup_cur = conn.cursor(dictionary=True)
                dup_cur.execute(\"\"\"
                    SELECT id FROM enquiries
                    WHERE (user_id = %s OR (email = %s AND email != ''))
                      AND (bike_id = %s OR listingId = %s)
                      AND created_at >= NOW() - INTERVAL 90 SECOND
                    LIMIT 1
                \"\"\", (user_id or -1, email or "__none__", bike_id, bike_id))
                dup_row = dup_cur.fetchone()
                dup_cur.close()
                if dup_row:
                    conn.close()
                    return jsonify({
                        "success": True,
                        "id": dup_row["id"],
                        "message": "Enquiry submitted successfully! SMR Motors team will contact you shortly."
                    }), 200
            except Exception:
                pass

        if conn:
            try:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        \"\"\"INSERT INTO enquiries (user_id, bike_id, name, email, phone, message, status, listingId, listingTitle, customerName, mobile)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\"\"\",
                        (user_id, bike_id, name, email, phone, msg, status, bike_id, bike_title, name, phone)
                    )
                except Exception:
                    cursor.execute(
                        \"\"\"INSERT INTO enquiries (bike_id, name, email, phone, message, status, listingId, listingTitle, customerName, mobile)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\"\"\",
                        (bike_id, name, email, phone, msg, status, bike_id, bike_title, name, phone)
                    )
                conn.commit()
                new_id = cursor.lastrowid
                cursor.close()
                conn.close()
            except Exception as e:
                if conn:
                    try: conn.close()
                    except Exception: pass
                return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

        # Create user dashboard notification if user is authenticated
        if user_id:
            try:
                create_notification(
                    title="Enquiry Submitted Successfully",
                    message=f"Your enquiry for {bike_title} was received. SMR Motors sales team will contact you shortly.",
                    user_id=user_id,
                    target_role="user",
                    notif_type="success",
                    link=f"/profile.html?tab=enquiries"
                )
            except Exception:
                pass

        # Send enquiry email notification to showroom owner / admin
        try:
            enq_email_subject = f"SMR Motors - New Enquiry for {bike_title}"
            enq_email_body = f\"\"\"SMR MOTORS - NEW MOTORCYCLE ENQUIRY
===========================================
A customer has submitted a new enquiry for an active motorcycle listing:

Listing:       {bike_title} (ID #{bike_id})
Customer Name: {name}
Email Address: {email}
Mobile Number: {phone}
Enquiry ID:    #{new_id}

Message:
-------------------------------------------
{msg}
-------------------------------------------

Timestamp: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Manage enquiries in the Admin Portal: https://bike-selling-site-lco8.onrender.com/admin.html?tab=enquiries
\"\"\"
            send_email_notification(
                to_email=CONTACT_RECEIVER_EMAIL,
                subject=enq_email_subject,
                body_text=enq_email_body
            )
        except Exception as em_err:
            print("[Enquiry Email Notice]:", em_err)

        return jsonify({
            "success": True,
            "message": "Enquiry submitted successfully! SMR Motors team will contact you shortly.",
            "id": new_id
        }), 201

    conn = get_db()
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
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
\n"""

content = content[:idx_start] + new_func + content[next_route_idx:]
with open(backend_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated enquiries_api in app.py successfully!")
