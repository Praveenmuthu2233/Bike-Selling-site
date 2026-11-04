with open('my-node-app/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_str = '''@app.route("/api/admin/chat/conversations", methods=["GET"])
@admin_required
def admin_get_chat_conversations():
    f_status = (request.args.get("filter") or "all").lower().strip()
    search = (request.args.get("search") or "").lower().strip()

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable."}), 500'''

new_str = '''@app.route("/api/admin/chat/conversations", methods=["GET"])
@admin_required
def admin_get_chat_conversations():
    f_status = (request.args.get("filter") or "all").lower().strip()
    search = (request.args.get("search") or "").lower().strip()

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection unavailable."}), 503'''

if old_str in text:
    text = text.replace(old_str, new_str, 1)
    with open('my-node-app/app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated admin_get_chat_conversations 503 status.")
else:
    print("Could not match old_str in app.py")
