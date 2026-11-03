with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. seller_id validation in add_bike_api
old_seller_chk = '''    if not seller_id:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr and "Bearer" in auth_hdr:
            try:
                dec_tok = jwt.decode(auth_hdr.split()[1], JWT_SECRET, algorithms=["HS256"])
                seller_id = dec_tok.get("id") or dec_tok.get("user_id")
            except Exception:
                pass
    # Check caller authentication to set status and listing_status correctly'''

new_seller_chk = '''    if not seller_id:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr and "Bearer" in auth_hdr:
            try:
                dec_tok = jwt.decode(auth_hdr.split()[1], JWT_SECRET, algorithms=["HS256"])
                seller_id = dec_tok.get("id") or dec_tok.get("user_id")
            except Exception:
                pass

    # Ensure seller_id exists in users table to satisfy foreign key constraint
    if seller_id:
        conn_chk = get_db()
        if conn_chk:
            try:
                cur_chk = conn_chk.cursor()
                cur_chk.execute("SELECT id FROM users WHERE id = %s LIMIT 1", (seller_id,))
                if not cur_chk.fetchone():
                    seller_id = None
                cur_chk.close()
                conn_chk.close()
            except Exception:
                if conn_chk:
                    try: conn_chk.close()
                    except Exception: pass
    # Check caller authentication to set status and listing_status correctly'''

assert old_seller_chk in content, "old_seller_chk not found"
content = content.replace(old_seller_chk, new_seller_chk, 1)

# 2. Return conversation object in create_chat_conversation
old_chat_ret1 = '''                return jsonify({
                    "success": True,
                    "conversation_id": conv_id,
                    "message_id": new_msg_id,
                    "reused_existing": True,
                    "message": "Message sent successfully"
                }), 201'''

new_chat_ret1 = '''                return jsonify({
                    "success": True,
                    "conversation_id": conv_id,
                    "conversation": {"id": conv_id, "subject": subject},
                    "message_id": new_msg_id,
                    "reused_existing": True,
                    "message": "Message sent successfully"
                }), 201'''

assert old_chat_ret1 in content, "old_chat_ret1 not found"
content = content.replace(old_chat_ret1, new_chat_ret1, 1)

old_chat_ret2 = '''        return jsonify({
            "success": True,
            "conversation_id": conv_id,
            "message_id": new_msg_id,
            "message": "Conversation started successfully"
        }), 201'''

new_chat_ret2 = '''        return jsonify({
            "success": True,
            "conversation_id": conv_id,
            "conversation": {"id": conv_id, "subject": subject},
            "message_id": new_msg_id,
            "message": "Conversation started successfully"
        }), 201'''

assert old_chat_ret2 in content, "old_chat_ret2 not found"
content = content.replace(old_chat_ret2, new_chat_ret2, 1)

with open('my-node-app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py with seller_id validation and chat conversation response.")
