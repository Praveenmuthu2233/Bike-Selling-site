import re

app_path = "my-node-app/app.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Patch admin_get_staff_list
old_staff = """    for s in staff_list:
        r = normalize_admin_role(s.get("role"))
        if role_filter != "all" and r != role_filter:
            continue
        if search:
            combined = f"{s.get('id')} {s.get('username','')} {s.get('full_name','')} {s.get('email','')} {s.get('phone','')}".lower()
            if search not in combined:
                continue
        s_copy = dict(s)
        s_copy["name"] = s_copy.get("full_name") or s_copy.get("username", "").capitalize()
        s_copy["role"] = r
        s_copy["is_active"] = int(s_copy.get("is_active") if s_copy.get("is_active") is not None else 1)
        filtered.append(s_copy)

    return jsonify({"success": True, "staff": filtered, "data": filtered})"""

new_staff = """    for s in staff_list:
        r = normalize_admin_role(s.get("role"))
        if role_filter != "all" and r != role_filter:
            continue
        if search:
            combined = f"{s.get('id')} {s.get('username','')} {s.get('full_name','')} {s.get('email','')} {s.get('phone','')}".lower()
            if search not in combined:
                continue
        s_copy = dict(s)
        s_copy["name"] = s_copy.get("full_name") or s_copy.get("username", "").capitalize()
        s_copy["role"] = r
        s_copy["is_active"] = int(s_copy.get("is_active") if s_copy.get("is_active") is not None else 1)
        filtered.append(s_copy)

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "staff": page_data,
        "data": page_data,
        "all_staff": filtered,
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
    })"""

if old_staff in content:
    content = content.replace(old_staff, new_staff, 1)
    print("1. admin_get_staff_list patched")
else:
    print("1. admin_get_staff_list NOT found")

# 2. Patch admin_audit_logs_api
old_audit = """@app.route("/api/admin/audit-logs", methods=["GET"])
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
    return jsonify({"success": True, "data": rows})"""

new_audit = """@app.route("/api/admin/audit-logs", methods=["GET"])
def admin_audit_logs_api():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    offset = (page - 1) * limit
    rows = []
    total = 0
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as cnt FROM admin_audit_logs")
            cnt_row = cursor.fetchone()
            total = cnt_row.get("cnt", 0) if cnt_row else 0

            cursor.execute("SELECT * FROM admin_audit_logs ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset))
            rows = cursor.fetchall() or []
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    total_pages = math.ceil(total / limit) if total > 0 else 1
    end_idx = min(offset + limit, total)
    return jsonify({
        "success": True,
        "data": rows,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": offset + 1 if total > 0 else 0,
            "end": end_idx
        }
    })"""

if old_audit in content:
    content = content.replace(old_audit, new_audit, 1)
    print("2. admin_audit_logs_api patched")
else:
    print("2. admin_audit_logs_api NOT found")

# 3. Patch user_my_negotiations
old_neg = """    return jsonify({"success": True, "data": negs})"""

new_neg = """    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    total = len(negs)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = negs[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
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
    })"""

# Match specific user_my_negotiations return statement
target_neg_block = """    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(\"\"\"
                SELECT * FROM bikes
                WHERE (seller_id = %s OR (seller_phone = %s AND %s != '') OR (seller_name = %s AND %s != ''))
                  AND listing_status IN ('price_offered', 'seller_accepted', 'seller_rejected')
                ORDER BY id DESC
            \"\"\", (u_id, u_phone, u_phone, u_name, u_name))
            rows = cursor.fetchall() or []
            negs = [_normalize_bike(b, is_admin=False) for b in rows]
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({"success": True, "data": negs})"""

replace_neg_block = """    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(\"\"\"
                SELECT * FROM bikes
                WHERE (seller_id = %s OR (seller_phone = %s AND %s != '') OR (seller_name = %s AND %s != ''))
                  AND listing_status IN ('price_offered', 'seller_accepted', 'seller_rejected')
                ORDER BY id DESC
            \"\"\", (u_id, u_phone, u_phone, u_name, u_name))
            rows = cursor.fetchall() or []
            negs = [_normalize_bike(b, is_admin=False) for b in rows]
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    total = len(negs)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = negs[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
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
    })"""

if target_neg_block in content:
    content = content.replace(target_neg_block, replace_neg_block, 1)
    print("3. user_my_negotiations patched")
else:
    print("3. user_my_negotiations NOT found")

# 4. Patch user_my_enquiries
target_enq_block = """    return jsonify({"success": True, "data": enqs, "enquiries": enqs})"""

replace_enq_block = """    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    total = len(enqs)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = enqs[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "enquiries": page_data,
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
    })"""

if target_enq_block in content:
    content = content.replace(target_enq_block, replace_enq_block, 1)
    print("4. user_my_enquiries patched")
else:
    print("4. user_my_enquiries NOT found")

# 5. Patch user_favorites_api GET
target_fav_block = """    return jsonify({"success": True, "data": [_normalize_bike(b, is_admin=False) for b in fav_bikes]})"""

replace_fav_block = """    normalized_favs = [_normalize_bike(b, is_admin=False) for b in fav_bikes]
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    total = len(normalized_favs)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = normalized_favs[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
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
    })"""

if target_fav_block in content:
    content = content.replace(target_fav_block, replace_fav_block, 1)
    print("5. user_favorites_api GET patched")
else:
    print("5. user_favorites_api GET NOT found")

# 6. Patch user_notifications_api
target_notif_block = """    return jsonify({"success": True, "data": notifs, "notifications": notifs})"""

replace_notif_block = """    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    total = len(notifs)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = notifs[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "notifications": page_data,
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
    })"""

if target_notif_block in content:
    content = content.replace(target_notif_block, replace_notif_block, 1)
    print("6. user_notifications_api patched")
else:
    print("6. user_notifications_api NOT found")

# 7. Patch admin_get_chat_conversations
old_admin_chat_end = """    return jsonify({"success": True, "conversations": conversations, "data": conversations})"""
new_admin_chat_end = """    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 15))))
    except (ValueError, TypeError):
        limit = 15

    total = len(conversations)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = conversations[start_idx:end_idx]

    return jsonify({
        "success": True,
        "conversations": page_data,
        "data": page_data,
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
    })"""

if old_admin_chat_end in content:
    content = content.replace(old_admin_chat_end, new_admin_chat_end, 1)
    print("7. admin_get_chat_conversations patched")
else:
    print("7. admin_get_chat_conversations NOT found")

# 8. Patch get_user_chat_conversations
old_user_chat_end = """    return jsonify({"success": True, "conversations": conversations})"""
new_user_chat_end = """    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.args.get("limit", 15))))
    except (ValueError, TypeError):
        limit = 15

    total = len(conversations)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = conversations[start_idx:end_idx]

    return jsonify({
        "success": True,
        "conversations": page_data,
        "data": page_data,
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
    })"""

if old_user_chat_end in content:
    content = content.replace(old_user_chat_end, new_user_chat_end, 1)
    print("8. get_user_chat_conversations patched")
else:
    print("8. get_user_chat_conversations NOT found")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Backend pagination patch complete.")
