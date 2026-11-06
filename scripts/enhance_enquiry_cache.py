import os

def enhance_enquiry_cache():
    fpath = os.path.join("my-node-app", "app.py")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    old_target = """# Enquiries API
@app.route("/api/enquiries", methods=["GET", "POST"])
@app.route("/enquiries", methods=["GET", "POST"])
def enquiries_api():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}"""

    new_replacement = """# In-memory deduplication cache for enquiries: (key) -> timestamp
_recent_enquiry_timestamps = {}

# Enquiries API
@app.route("/api/enquiries", methods=["GET", "POST"])
@app.route("/enquiries", methods=["GET", "POST"])
def enquiries_api():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        bike_id = data.get("bike_id")
        user_id = data.get("user_id")
        email = (data.get("email") or "").strip().lower()

        # In-memory rapid deduplication check (prevents double-clicks within 90s)
        dedup_key = f"{bike_id}_{user_id or email}"
        now_ts = time.time()
        if dedup_key in _recent_enquiry_timestamps:
            if now_ts - _recent_enquiry_timestamps[dedup_key] < 90:
                return jsonify({
                    "success": True,
                    "message": "Enquiry submitted successfully! SMR Motors team will contact you shortly."
                }), 200
        _recent_enquiry_timestamps[dedup_key] = now_ts"""

    if old_target in content:
        content = content.replace(old_target, new_replacement, 1)
        print("Added in-memory deduplication cache check")
    else:
        print("Target not found for enquiry cache")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    enhance_enquiry_cache()
