import py_compile
import sys

app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # 1. admin_propose_price loop
    if 'for b in IN_MEMORY_STORE["bikes"]:' in line and i < 3650:
        new_lines.append('    create_notification(\n')
        new_lines.append('        "Payout Proposal Submitted",\n')
        new_lines.append('        f"SMR Motors has proposed a seller payout of ₹{proposed_payout:,.0f} for your listing #{bike_id}.",\n')
        new_lines.append('        target_role="user",\n')
        new_lines.append('        link="/profile.html?tab=negotiations"\n')
        new_lines.append('    )\n')
        new_lines.append('    return jsonify({\n')
        new_lines.append('        "success": True,\n')
        new_lines.append('        "message": f"Counteroffer of ₹{proposed_payout:,.0f} proposed to seller",\n')
        new_lines.append('        "proposed_seller_payout": proposed_payout,\n')
        new_lines.append('        "listing_status": "price_offered"\n')
        new_lines.append('    })\n')
        # Skip until def or return
        i += 1
        while i < len(lines) and not lines[i].startswith('@app.route("/api/users/bikes/<int:bike_id>/negotiate'):
            i += 1
        continue

    # 2. user_respond_negotiation loop
    if 'for b in IN_MEMORY_STORE["bikes"]:' in line and 3650 <= i < 3730:
        new_lines.append('    res_status = "seller_accepted" if action == "accept" else "seller_rejected"\n')
        new_lines.append('    create_notification(\n')
        new_lines.append('        f"Seller {action.capitalize()}ed Offer #{bike_id}",\n')
        new_lines.append('        f"Seller {action}ed payout proposal for motorcycle #{bike_id}.",\n')
        new_lines.append('        target_role="admin",\n')
        new_lines.append('        link="/admin.html?tab=negotiations"\n')
        new_lines.append('    )\n')
        new_lines.append('    return jsonify({\n')
        new_lines.append('        "success": True,\n')
        new_lines.append('        "message": f"Proposal successfully {action}ed",\n')
        new_lines.append('        "action": action,\n')
        new_lines.append('        "listing_status": res_status\n')
        new_lines.append('    })\n')
        i += 1
        while i < len(lines) and not lines[i].startswith('@app.route("/api/admin/bikes/<int:bike_id>/publish'):
            i += 1
        continue

    # 3. admin_publish_bike loop
    if 'for b in IN_MEMORY_STORE["bikes"]:' in line and 3730 <= i < 3820:
        new_lines.append('    create_notification(\n')
        new_lines.append('        f"Bike #{bike_id} is Now Live!",\n')
        new_lines.append('        f"Motorcycle #{bike_id} has been published to live marketplace at ₹{public_price:,.0f}.",\n')
        new_lines.append('        target_role="user",\n')
        new_lines.append('        link=f"/enquiry-bike-details.html?id={bike_id}"\n')
        new_lines.append('    )\n')
        new_lines.append('    return jsonify({\n')
        new_lines.append('        "success": True,\n')
        new_lines.append('        "message": "Bike successfully published to live marketplace",\n')
        new_lines.append('        "public_selling_price": public_price,\n')
        new_lines.append('        "listing_status": "published"\n')
        new_lines.append('    })\n')
        i += 1
        while i < len(lines) and not lines[i].startswith('@app.route("/api/admin/bikes/<int:bike_id>/sold'):
            i += 1
        continue

    # 4. admin_update_bike loop
    if 'for b in IN_MEMORY_STORE["bikes"]:' in line and i > 4500:
        # Skip until log_admin_action
        i += 1
        while i < len(lines) and 'log_admin_action(' not in lines[i]:
            i += 1
        new_lines.append(lines[i])
        i += 1
        continue

    new_lines.append(line)
    i += 1

with open(app_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Saved app.py. Now compiling...")
try:
    py_compile.compile(app_path, doraise=True)
    print("SUCCESS: app.py compiled successfully!")
except Exception as e:
    print(f"COMPILE ERROR: {e}")
    sys.exit(1)
