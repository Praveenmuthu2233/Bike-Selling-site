import re
import py_compile
import sys

app_path = "my-node-app/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. create_notification
code = code.replace(
    '"id": len(IN_MEMORY_STORE["notifications"]) + 1,',
    '"id": int(datetime.datetime.utcnow().timestamp()),'
)

# 2. admin_reply_to_enquiry
old_enq_mem = '''    for e in IN_MEMORY_STORE["enquiries"]:
        if e.get("id") == enquiry_id:
            e["admin_reply"] = reply_text
            e["replied_at"] = datetime.datetime.utcnow().isoformat()
            e["replied_by"] = admin_username'''
if old_enq_mem in code:
    code = code.replace(old_enq_mem, '    # Reply stored permanently in TiDB Cloud enquiry_replies table')
    print("Fixed admin_reply_to_enquiry")

# 3. find_or_create_google_user docstring
code = code.replace(
    'Finds or creates user in TiDB Cloud MySQL, falling back to IN_MEMORY_STORE.',
    'Finds or creates user permanently in TiDB Cloud MySQL.'
)

# 4. admin_propose_price
old_prop_mem = '''    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["proposed_seller_payout"] = proposed_payout
            b["listing_status"] = "price_offered"
            b["negotiation_status"] = "awaiting_seller_response"
            create_notification(
                "Price Proposal Submitted",
                f"SMR Motors evaluated vehicle #{bike_id} and submitted payout valuation: ₹{proposed_payout:,.0f}.",
                user_id=b.get("seller_id"),
                target_role="user",
                link="/profile.html"
            )'''
if old_prop_mem in code:
    code = code.replace(old_prop_mem, '    # Proposal saved permanently in TiDB Cloud')
    print("Fixed admin_propose_price")

# 5. user_respond_negotiation
old_resp_mem = '''    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            payout = b.get("proposed_seller_payout") or b.get("price", 0)
            if action == "accept":
                b["accepted_seller_payout"] = payout
                b["listing_status"] = "seller_accepted"
                b["negotiation_status"] = "accepted"
            else:
                b["listing_status"] = "seller_rejected"
                b["negotiation_status"] = "rejected"'''
if old_resp_mem in code:
    code = code.replace(old_resp_mem, '    # Negotiation response saved permanently in TiDB Cloud')
    print("Fixed user_respond_negotiation")

# 6. admin_publish_bike
old_pub_mem = '''    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            seller_payout = float(b.get("accepted_seller_payout") or b.get("proposed_seller_payout") or b.get("requested_price") or public_price)
            margin = public_price - seller_payout
            b["public_selling_price"] = public_price
            b["price"] = public_price
            b["status"] = "approved"
            b["listing_status"] = "published"
            b["isAccepted"] = 1
            b["published_at"] = datetime.datetime.utcnow().isoformat()'''
if old_pub_mem in code:
    code = code.replace(old_pub_mem, '    # Publication state saved permanently in TiDB Cloud')
    print("Fixed admin_publish_bike")

# 7. admin_mark_sold
code = code.replace(
    '"id": len(IN_MEMORY_STORE["bike_transactions"]) + 1,',
    '"id": int(datetime.datetime.utcnow().timestamp()),'
)

# 8. admin_update_bike
old_upd_mem = '''    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            if title: b["title"] = title
            if brand: b["brand"] = brand
            if model: b["model"] = model
            if year: b["year"] = int(year)
            if kms is not None: b["kilometers_driven"] = int(kms)
            if fuel: b["fuel_type"] = fuel
            if trans: b["transmission"] = trans
            if desc: b["description"] = desc
            if sname: b["seller_name"] = sname
            if sphone: b["seller_phone"] = sphone
            if public_price is not None:
                b["price"] = public_price
                b["public_selling_price"] = public_price'''
if old_upd_mem in code:
    code = code.replace(old_upd_mem, '    # Bike updates persisted permanently in TiDB Cloud')
    print("Fixed admin_update_bike")

# 9. admin_price_bike
old_price_mem = '''    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["price"] = float(new_price)
            b["public_selling_price"] = float(new_price)
            b["sellingPrice"] = str(new_price)'''
if old_price_mem in code:
    code = code.replace(old_price_mem, '    # Price updated permanently in TiDB Cloud')
    print("Fixed admin_price_bike")

# 10. admin_reply_to_message
old_msg_fallback = '''    if not target_msg:
        for m in IN_MEMORY_STORE.get("contact_messages", []):
            if m.get("id") == msg_id:
                target_msg = m
                break'''
if old_msg_fallback in code:
    code = code.replace(old_msg_fallback, '')
    print("Fixed admin_reply_to_message")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Saved app.py. Now compiling...")
try:
    py_compile.compile(app_path, doraise=True)
    print("SUCCESS: app.py compiled successfully!")
except Exception as e:
    print(f"COMPILE ERROR: {e}")
    sys.exit(1)
