backend_file = 'my-node-app/app.py'
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "def get_single_bike_api(bike_id):"
idx_start = content.find(start_marker)
assert idx_start != -1

next_func_idx = content.find("\n@app.route", idx_start)

new_single_api = """def get_single_bike_api(bike_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(\"\"\"
                SELECT b.*, s.actual_sale_price, s.sold_at as sold_record_date, s.sold_by
                FROM bikes b
                LEFT JOIN sold_bikes s ON b.id = s.bike_id
                WHERE b.id = %s
            \"\"\", (bike_id,))
            b = cursor.fetchone()
            cursor.close()
            conn.close()
            if b:
                if isinstance(b.get("images"), str):
                    try: b["images"] = json.loads(b["images"])
                    except Exception: b["images"] = [b["images"]]
                if not b.get("images"):
                    b["images"] = ["/static/images/IMG-20251204-WA0053.jpg"]
                b["listingTitle"] = b.get("title")
                b["makedFrom"] = b.get("brand")
                b["bikeModel"] = b.get("model")
                b["bikeBuyingYear"] = str(b.get("year", 2022))
                b["sellingPrice"] = str(b.get("actual_sale_price") or b.get("price", 100000))
                b["bikePrice"] = str(b.get("actual_sale_price") or b.get("price", 100000))
                b["bikeKms"] = str(b.get("kilometers_driven", 0))
                b["isAccepted"] = 1 if b.get("status") == "approved" else 0
                b["isSoldout"] = 1 if (b.get("status") in ("sold", "soldout") or b.get("isSoldout") == 1) else 0

                # Check if caller has admin token
                is_admin = False
                auth_header = request.headers.get("Authorization", "")
                if auth_header and "Bearer" in auth_header:
                    try:
                        import jwt
                        tok = auth_header.split()[1]
                        dec = jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
                        if dec.get("role") in ("admin", "superadmin") or "username" in dec:
                            is_admin = True
                    except Exception:
                        pass

                # Mask private details for public visitors
                raw_reg = b.get("registration_number") or ""
                if is_admin:
                    b["sellerName"] = b.get("seller_name")
                    b["mobileNum"] = b.get("seller_phone")
                    b["registration_number_masked"] = raw_reg or "TN-XX-XXXX"
                else:
                    b["sellerName"] = "SMR Motors Verified Seller"
                    b["mobileNum"] = "+91 98765 43210"
                    b["seller_phone"] = None
                    if raw_reg and len(raw_reg) >= 6:
                        b["registration_number_masked"] = raw_reg[:4] + "-**-****"
                    else:
                        b["registration_number_masked"] = "TN-**-****"

                return jsonify({"success": True, "data": b, **b})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # In-memory fallback
    memory_store = get_memory_store()
    for b in memory_store.get("bikes", []):
        if b.get("id") == bike_id:
            b_copy = dict(b)
            raw_reg = b_copy.get("registration_number") or ""
            b_copy["registration_number_masked"] = (raw_reg[:4] + "-**-****") if len(raw_reg) >= 6 else "TN-**-****"
            return jsonify({"success": True, "data": b_copy, **b_copy})

    return jsonify({"success": False, "message": "Motorcycle not found"}), 404
"""

content = content[:idx_start] + new_single_api + content[next_func_idx:]
with open(backend_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated get_single_bike_api in app.py successfully!")
