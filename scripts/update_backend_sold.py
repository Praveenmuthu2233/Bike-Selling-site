import os

def update_backend_sold_apis():
    app_path = os.path.join("my-node-app", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update routes for admin-sold-bike-details
    old_routes = """@app.route("/admin/sold-bike-details.html")
@app.route("/sold-bike-details.html")
@app.route("/admin/sold-bike-details")
@app.route("/admin/bike-details.html")
@app.route("/admin/bike-details")
@app.route("/bike-details-admin")
def sold_bike_details_page():
    return render_template("sold-bike-details.html")"""

    new_routes = """@app.route("/admin-sold-bike-details.html")
@app.route("/admin-sold-bike-details")
@app.route("/admin/sold-bike-details.html")
@app.route("/admin/sold-bike-details")
@app.route("/admin/bike-details.html")
@app.route("/admin/bike-details")
@app.route("/bike-details-admin")
def sold_bike_details_page():
    return render_template("admin-sold-bike-details.html")

@app.route("/sold-bike-details.html")
def public_sold_details_redirect():
    # Public sold details page is removed; redirect to public Sold-Out gallery
    return redirect("/SoldOutPage.html")"""

    if old_routes in content:
        content = content.replace(old_routes, new_routes, 1)
        print("Updated sold details routes")
    else:
        print("old_routes not found, checking variations")

    # 2. In admin_sold_bikes_api, set default limit to 6 (latest 6 sold bikes)
    old_admin_limit = """    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10"""

    new_admin_limit = """    try:
        limit = max(1, int(request.args.get("limit", 6)))
    except (ValueError, TypeError):
        limit = 6"""

    if old_admin_limit in content:
        content = content.replace(old_admin_limit, new_admin_limit, 1)
        print("Updated admin_sold_bikes_api default limit to 6")

    # 3. In get_sold_bikes_api (public), ensure default limit is 8
    old_pub_limit = """    try:
        limit = max(1, int(request.args.get("limit", 9)))
    except (ValueError, TypeError):
        limit = 9"""

    new_pub_limit = """    try:
        limit = max(1, int(request.args.get("limit", 8)))
    except (ValueError, TypeError):
        limit = 8"""

    if old_pub_limit in content:
        content = content.replace(old_pub_limit, new_pub_limit, 1)
        print("Updated get_sold_bikes_api public default limit to 8")

    # 4. In admin_sold_bike_detail_api, enrich financial metrics and seller info
    old_fin_setup = """    fin_data = calculate_bike_financials(bp, sp, rep, oth)
    fin_data["purchase_date"] = str(bike.get("purchase_date") or "")
    fin_data["sale_date"] = str(bike.get("sold_at") or (sold_record.get("sold_at") if sold_record else "") or "")
    fin_data["payment_status"] = (sold_record.get("payment_status") if sold_record else None) or bike.get("payment_status") or "Full Payment" """

    new_fin_setup = """    fin_data = calculate_bike_financials(bp, sp, rep, oth)
    fin_data["customer_expected_price"] = float(bike.get("price") or 0.0)
    fin_data["admin_suggested_price"] = float(bike.get("suggested_price") or bike.get("public_selling_price") or bike.get("price") or 0.0)
    fin_data["formatted_customer_expected_price"] = f"₹{float(bike.get('price') or 0.0):,.0f}"
    fin_data["formatted_admin_suggested_price"] = f"₹{float(bike.get('suggested_price') or bike.get('public_selling_price') or bike.get('price') or 0.0):,.0f}"
    fin_data["purchase_date"] = str(bike.get("purchase_date") or "")
    fin_data["sale_date"] = str(bike.get("sold_at") or (sold_record.get("sold_at") if sold_record else "") or "")
    fin_data["payment_status"] = (sold_record.get("payment_status") if sold_record else None) or bike.get("payment_status") or "Full Payment" """

    # Handle whitespace if needed
    if "fin_data = calculate_bike_financials(bp, sp, rep, oth)" in content:
        # replace the lines
        idx = content.find("fin_data = calculate_bike_financials(bp, sp, rep, oth)")
        end_idx = content.find('fin_data["payment_status"]', idx)
        line_end = content.find('\n', end_idx)
        old_block = content[idx:line_end]
        content = content.replace(old_block, new_fin_setup.strip())
        print("Updated fin_data with customer_expected_price and admin_suggested_price")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("app.py updated successfully")

if __name__ == "__main__":
    update_backend_sold_apis()
