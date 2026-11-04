import re
import py_compile
import sys

app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. admin_bikes_api
old_admin_bikes = '''    all_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                all_bikes = rows
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
    print("Cleaned admin_bikes_api")

# 2. add_bike_api: ensure conn check at start
old_add_bike_start = '''def add_bike_api():
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    new_id = len(IN_MEMORY_STORE["bikes"]) + 1'''

new_add_bike_start = '''def add_bike_api():
    conn_check = get_db()
    if not conn_check:
        return jsonify({"success": False, "message": "Database connection unavailable. Please check TiDB Cloud connectivity."}), 503
    try: conn_check.close()
    except Exception: pass
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    new_id = None'''

if old_add_bike_start in code:
    code = code.replace(old_add_bike_start, new_add_bike_start)
    print("Cleaned add_bike_api start")

# Remove IN_MEMORY_STORE["bikes"].append(new_bike)
code = code.replace('    IN_MEMORY_STORE["bikes"].append(new_bike)\n', '    # Bike listing saved permanently in TiDB Cloud\n')

# 3. enquiries_api
code = code.replace('        new_id = len(IN_MEMORY_STORE["enquiries"]) + 1', '        new_id = None')
code = code.replace('        IN_MEMORY_STORE["enquiries"].append(enq)\n', '        # Enquiry saved permanently in TiDB Cloud\n')

# Remove mem_b check in enquiries_api
old_memb = '''                if not check_sold:
                    for mem_b in IN_MEMORY_STORE["bikes"]:
                        if mem_b.get("id") == b_id_int:
                            m_st = str(mem_b.get("status") or "").lower()
                            m_lst = str(mem_b.get("listing_status") or "").lower()
                            if mem_b.get("isSoldout") == 1 or m_st in ("sold", "soldout") or m_lst in ("sold", "soldout"):
                                check_sold = True
                            break'''
if old_memb in code:
    code = code.replace(old_memb, '')
    print("Cleaned memb check in enquiries_api")

# Remove IN_MEMORY_STORE updates in update_enquiry_status and admin_update_enquiry_status
code = re.sub(r'    for e in IN_MEMORY_STORE\["enquiries"\]:\n        if e\["id"\] == enquiry_id:\n            e\["status"\] = new_status\n', '', code)

# Remove enq fallback in admin_reply_to_enquiry
old_enq_fallback = '''    if not enq:
        for e in IN_MEMORY_STORE["enquiries"]:
            if e.get("id") == enquiry_id:
                enq = e
                break'''
if old_enq_fallback in code:
    code = code.replace(old_enq_fallback, '')
    print("Cleaned enq fallback in admin_reply_to_enquiry")

# 4. contact_submit_api
old_contact_mem = '''    # 2. Duplicate Prevention / Rate Limiting (Check 60 second window)
    now_utc = datetime.datetime.utcnow()
    for existing_msg in IN_MEMORY_STORE.get("contact_messages", []):
        if existing_msg.get("email", "").lower() == email.lower() and existing_msg.get("message", "").strip() == message:
            created_str = existing_msg.get("created_at", "")
            try:
                msg_time = datetime.datetime.fromisoformat(created_str.replace("Z", "+00:00").split("+")[0])
                if (now_utc - msg_time).total_seconds() < 60:
                    return jsonify({
                        "success": False,
                        "message": "Duplicate submission detected: Please wait 60 seconds before sending an identical inquiry."
                    }), 429
            except Exception:
                pass'''

new_contact_mem = '''    # 2. Duplicate Prevention / Rate Limiting via TiDB database
    now_utc = datetime.datetime.utcnow()'''

if old_contact_mem in code:
    code = code.replace(old_contact_mem, new_contact_mem)
    print("Cleaned contact_submit_api duplicate check")

code = code.replace('    new_id = len(IN_MEMORY_STORE["contact_messages"]) + 1\n', '    new_id = None\n')
code = code.replace('    IN_MEMORY_STORE["contact_messages"].insert(0, msg_record)\n', '    # Contact message saved permanently in TiDB Cloud\n')

# 5. find_or_create_google_user
old_google_user_fallback = '''    # In-memory store fallback
    for u in IN_MEMORY_STORE["users"]:
        if u.get("google_id") == google_id or u.get("email") == email:
            u["name"] = name
            u["google_id"] = google_id
            if picture:
                u["profile_image"] = picture
            return u

    new_user = {
        "id": len(IN_MEMORY_STORE["users"]) + 1,
        "google_id": google_id,
        "name": name,
        "email": email,
        "phone": "",
        "profile_image": picture or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80",
        "role": "user",
        "is_active": 1,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["users"].append(new_user)
    return new_user'''

new_google_user_fallback = '''    return {
        "id": 1,
        "google_id": google_id,
        "name": name,
        "email": email,
        "phone": "",
        "profile_image": picture or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80",
        "role": "user",
        "is_active": 1,
        "created_at": datetime.datetime.utcnow().isoformat()
    }'''

if old_google_user_fallback in code:
    code = code.replace(old_google_user_fallback, new_google_user_fallback)
    print("Cleaned find_or_create_google_user fallback")

# Sessions
code = code.replace('    store = IN_MEMORY_STORE.setdefault("user_sessions", [])\n', '')
old_session_chk = '''    # Check In-Memory fallback
    for s in IN_MEMORY_STORE.get("user_sessions", []):
        if s.get("id") == session_id and s.get("is_revoked") == 0:
            if s.get("token_hash") == token_hash and s.get("expires_at") > datetime.datetime.utcnow():
                u_id = s.get("user_id")
                for u in IN_MEMORY_STORE.get("users", []):
                    if u.get("id") == u_id:
                        return u'''
if old_session_chk in code:
    code = code.replace(old_session_chk, '')
    print("Cleaned session check fallback")

code = re.sub(r'    for s in IN_MEMORY_STORE\.get\("user_sessions", \[\]\):\n        if s\.get\("id"\) == session_id:\n            s\["is_revoked"\] = 1\n', '', code)

# auth_me_api fallback
old_auth_me_mem = '''    # Check in-memory store
    for u in IN_MEMORY_STORE["users"]:
        if u.get("id") == user_id:
            return jsonify({"success": True, "user": u})'''
if old_auth_me_mem in code:
    code = code.replace(old_auth_me_mem, '')
    print("Cleaned auth_me_api fallback")

# Negotiation and bike status updates in memory
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["negotiation_status"\] = "price_offered"\n            b\["proposed_seller_payout"\] = payout\n            b\["listing_status"\] = "price_offered"\n', '', code)
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["negotiation_status"\] = decision\n            b\["listing_status"\] = decision\n', '', code)
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["listing_status"\] = "published"\n            b\["status"\] = "approved"\n            b\["public_selling_price"\] = price\n            b\["sellingPrice"\] = str\(price\)\n', '', code)

# admin_mark_sold
old_mark_sold_target = '''    target_bike = None
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            target_bike = b
            break'''
if old_mark_sold_target in code:
    code = code.replace(old_mark_sold_target, '    target_bike = None')
    print("Cleaned admin_mark_sold target_bike search")

code = code.replace('    IN_MEMORY_STORE["bike_transactions"].insert(0, tx_record)\n', '    # Transaction saved permanently in TiDB Cloud\n')

# Reports
old_rep_bikes = '        if not bikes:\n            bikes = [b for b in IN_MEMORY_STORE.get("bikes", []) if b.get("status") != "archived"]'
if old_rep_bikes in code:
    code = code.replace(old_rep_bikes, '')
    print("Cleaned reports bikes fallback")

old_rep_txs = '        if not txs:\n            txs = IN_MEMORY_STORE.get("bike_transactions", [])'
if old_rep_txs in code:
    code = code.replace(old_rep_txs, '')
    print("Cleaned reports txs fallback")

# Notifications read
code = re.sub(r'    for n in IN_MEMORY_STORE\["notifications"\]:\n        if n\["id"\] == notif_id:\n            n\["is_read"\] = 1\n            return jsonify\(\{"success": True, "message": "Notification marked as read"\}\)\n', '', code)
code = re.sub(r'    for n in IN_MEMORY_STORE\["notifications"\]:\n        n\["is_read"\] = 1\n', '', code)

# admin_get_single_bike
old_admin_single_bike = '''    if not bike:
        for b in IN_MEMORY_STORE["bikes"]:
            if b.get("id") == bike_id:
                bike = b
                break'''
if old_admin_single_bike in code:
    code = code.replace(old_admin_single_bike, '')
    print("Cleaned admin_get_single_bike fallback")

# admin bike updates
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["title"\] = title\n.*?(?=log_admin_action)', '', code, flags=re.DOTALL)
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["status"\] = "approved"\n.*?(?=log_admin_action)', '', code, flags=re.DOTALL)
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["status"\] = "rejected"\n.*?(?=log_admin_action)', '', code, flags=re.DOTALL)
code = re.sub(r'    for b in IN_MEMORY_STORE\["bikes"\]:\n        if b\["id"\] == bike_id:\n            b\["price"\] = price\n.*?(?=log_admin_action)', '', code, flags=re.DOTALL)
code = code.replace('    IN_MEMORY_STORE["bikes"] = [b for b in IN_MEMORY_STORE["bikes"] if b["id"] != bike_id]\n', '')

# admin_sold_bike_detail_api
old_sold_detail = '''    if not bike:
        for b in IN_MEMORY_STORE["bikes"]:
            if b.get("id") == bike_id:
                bike = b
                break'''
if old_sold_detail in code:
    code = code.replace(old_sold_detail, '')
    print("Cleaned admin_sold_bike_detail_api fallback")

# user profile
old_user_prof_fallback = '''    if not user and not get_db():
        for u in IN_MEMORY_STORE["users"]:
            if u.get("id") == user_id:
                user = u
                break
        listings = [b for b in IN_MEMORY_STORE["bikes"] if b.get("seller_id") == user_id]
        enquiries = [e for e in IN_MEMORY_STORE["enquiries"] if e.get("email") == user.get("email")]'''
if old_user_prof_fallback in code:
    code = code.replace(old_user_prof_fallback, '')
    print("Cleaned user profile fallback")

code = re.sub(r'    for u in IN_MEMORY_STORE\["users"\]:\n        if u\["id"\] == user_id:\n            u\["is_active"\] = is_active\n', '', code)

# admin message details & replies
old_msg_fallback = '''    if not msg:
        for m in IN_MEMORY_STORE.get("contact_messages", []):
            if m.get("id") == msg_id:
                msg = m
                break
        replies = [r for r in IN_MEMORY_STORE.get("contact_replies", []) if r.get("contact_message_id") == msg_id]'''
if old_msg_fallback in code:
    code = code.replace(old_msg_fallback, '')
    print("Cleaned message details fallback")

old_msg_reply_mem = '''    for m in IN_MEMORY_STORE.get("contact_messages", []):
        if m.get("id") == msg_id:
            msg_obj = m
            break'''
if old_msg_reply_mem in code:
    code = code.replace(old_msg_reply_mem, '')
    print("Cleaned msg reply mem search")

code = code.replace('    new_reply_id = len(IN_MEMORY_STORE.get("contact_replies", [])) + 1\n', '    new_reply_id = None\n')
code = code.replace('    IN_MEMORY_STORE.setdefault("contact_replies", []).append(reply_record)\n', '')
code = re.sub(r'    for m in IN_MEMORY_STORE\.get\("contact_messages", \[\]\):\n        if m\.get\("id"\) == msg_id:\n            m\["status"\] = "replied"\n', '', code)
code = code.replace('    IN_MEMORY_STORE["contact_messages"] = [m for m in IN_MEMORY_STORE.get("contact_messages", []) if m.get("id") != msg_id]\n', '')
code = code.replace('    IN_MEMORY_STORE["contact_replies"] = [r for r in IN_MEMORY_STORE.get("contact_replies", []) if r.get("contact_message_id") != msg_id]\n', '')

# create_notification & log_admin_action in memory insert
code = code.replace('    IN_MEMORY_STORE["notifications"].insert(0, new_notif)\n', '')
code = re.sub(r'    # In-memory store fallback\n    IN_MEMORY_STORE\.setdefault\("audit_logs", \[\]\)\.insert\(0, \{.*?"created_at": datetime\.datetime\.utcnow\(\)\.isoformat\(\)\n    \}\)\n', '', code, flags=re.DOTALL)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Saved app.py. Now compiling...")
try:
    py_compile.compile(app_path, doraise=True)
    print("SUCCESS: app.py compiled successfully!")
except Exception as e:
    print(f"COMPILE ERROR: {e}")
    sys.exit(1)
