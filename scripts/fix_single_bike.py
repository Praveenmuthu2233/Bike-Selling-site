import os

def fix_get_single_bike():
    fpath = os.path.join("my-node-app", "app.py")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    old_target = """    # In-memory fallback
    memory_store = get_memory_store()
    for b in memory_store.get("bikes", []):
        if b.get("id") == bike_id:
            b_copy = dict(b)
            raw_reg = b_copy.get("registration_number") or ""
            b_copy["registration_number_masked"] = (raw_reg[:4] + "-**-****") if len(raw_reg) >= 6 else "TN-**-****"
            return jsonify({"success": True, "data": b_copy, **b_copy})

    return jsonify({"success": False, "message": "Motorcycle not found"}), 404"""

    new_replacement = """    return jsonify({"success": False, "message": "Motorcycle not found"}), 404"""

    if old_target in content:
        content = content.replace(old_target, new_replacement, 1)
        print("Replaced undefined get_memory_store fallback")
    else:
        print("Target not found")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fix_get_single_bike()
