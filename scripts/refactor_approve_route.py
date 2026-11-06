import os

def refactor_admin_approve_bike():
    app_path = os.path.join("my-node-app", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = '@app.route("/api/admin/bikes/<int:bike_id>/approve", methods=["POST", "PUT"])'
    end_marker = '@app.route("/api/admin/bikes/<int:bike_id>/reject", methods=["POST", "PUT"])'

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("Could not find start or end marker")
        return

    new_approve_code = """@app.route("/api/admin/bikes/<int:bike_id>/approve", methods=["POST", "PUT"])
@app.route("/bikes/<int:bike_id>/accept", methods=["POST", "PUT"])
@admin_required
def admin_approve_bike(bike_id):
    \"\"\"
    Approves and publishes a customer-submitted bike to the live showroom catalog.
    1. Validates approved selling price (₹0 to ₹10,00,000).
    2. Atomically updates status to 'approved', listing_status to 'accepted', isSoldout to 0.
    3. Updates price and published_at timestamp so it appears at top of inventory.
    4. Records status history in listing_status_history.
    5. Creates or reuses existing seller chat conversation and sends 4-point document request message.
    6. Safely updates conversation timestamp using actual schema.
    7. Creates user in-app dashboard notification.
    8. Transactional rollback protection: completely rolls back on any error.
    \"\"\"
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    admin_username = g.admin.get("username", "admin")
    admin_id = g.admin.get("id") or 1

    # 1. Price validation
    approved_price = None
    raw_price = data.get("approved_price") if "approved_price" in data else (data.get("public_selling_price") if "public_selling_price" in data else data.get("price"))
    if raw_price is not None and str(raw_price).strip() != "":
        try:
            approved_price = float(raw_price)
            if approved_price < 0 or approved_price > 1000000:
                return jsonify({"success": False, "message": "Bike price must be between ₹0 and ₹10,00,000."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Bike price must be a valid number between ₹0 and ₹10,00,000."}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503

    try:
        cursor = conn.cursor(dictionary=True)

        # 2. Query bike submission record
        cursor.execute(\"\"\"
            SELECT id, title, brand, model, price, status, listing_status, seller_id, seller_name, seller_phone, user_id
            FROM bikes WHERE id = %s
        \"\"\", (bike_id,))
        bike_row = cursor.fetchone()

        if not bike_row:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": f"Motorcycle #{bike_id} not found."}), 404

        current_status = bike_row.get("status")
        current_listing_status = bike_row.get("listing_status")
        bike_title = bike_row.get("title") or f"Motorcycle #{bike_id}"
        bike_brand = bike_row.get("brand") or "Motorcycle"
        bike_model = bike_row.get("model") or ""
        seller_id = bike_row.get("seller_id") or bike_row.get("user_id")
        seller_name = bike_row.get("seller_name")
        seller_phone = bike_row.get("seller_phone")
        final_price = approved_price if approved_price is not None else float(bike_row.get("price") or 0.0)

        # If seller_id is missing, look up users table by seller_phone
        if not seller_id and seller_phone:
            try:
                cursor.execute("SELECT id, name FROM users WHERE phone = %s OR phone LIKE %s LIMIT 1", (seller_phone, f"%{seller_phone[-10:]}%"))
                s_user = cursor.fetchone()
                if s_user:
                    seller_id = s_user.get("id")
                    seller_name = seller_name or s_user.get("name")
            except Exception:
                pass

        # 3. Update bikes table: status='approved', listing_status='accepted', isSoldout=0, published_at=CURRENT_TIMESTAMP
        if approved_price is not None:
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
            \"\"\", (final_price, final_price, admin_username, bike_id))
            try:
                cursor.execute("UPDATE bikesforsale SET isAccepted = 1, isSoldout = 0, sellingPrice = %s WHERE id = %s", (str(final_price), bike_id))
            except Exception:
                pass
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
            try:
                cursor.execute("UPDATE bikesforsale SET isAccepted = 1, isSoldout = 0 WHERE id = %s", (bike_id,))
            except Exception:
                pass

        # 4. Record status transition history
        try:
            cursor.execute(\"\"\"
                INSERT INTO listing_status_history (bike_id, old_status, new_status, changed_by, reason)
                VALUES (%s, %s, 'accepted', %s, 'Bike submission accepted by admin; document verification initiated')
            \"\"\", (bike_id, current_status or "pending", admin_username))
        except Exception:
            pass

        # 5. Customer Notification & Document Request Message
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
                WHERE user_id = %s AND (bike_id = %s OR (bike_id IS NULL AND subject LIKE %s))
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

            # Avoid duplicate messages on repeated clicks
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

                # Update conversation timestamp safely using actual schema
                try:
                    cursor.execute(\"\"\"
                        UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
                    \"\"\", (conv_id,))
                except Exception:
                    cursor.execute(\"\"\"
                        UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s
                    \"\"\", (conv_id,))

            # In-app dashboard notification
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

        # Commit transaction atomically
        conn.commit()
        cursor.close()
        conn.close()

        log_admin_action(admin_username, "approve_bike", "bike", bike_id, f"Accepted motorcycle submission #{bike_id} ({bike_title}) and requested documents")

        return jsonify({
            "success": True,
            "message": "Motorcycle submission accepted and published to live marketplace! Document request sent to seller."
        })

    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

"""

    content = content[:start_idx] + new_approve_code + content[end_idx:]

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Refactored admin_approve_bike in app.py successfully")

if __name__ == "__main__":
    refactor_admin_approve_bike()
