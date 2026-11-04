endpoints_to_check = {
    "Homepage / Inventory": ["/api/bikes", "GET"],
    "Bike Details": ["/api/bikes/<int:bike_id>", "GET"],
    "Sell Your Bike": ["/api/bikes", "POST"],
    "Sold Gallery": ["/api/bikes/sold", "GET"],
    "User Dashboard / Profile": ["/api/auth/me", "GET"],
    "My Bike Listings": ["/api/users/bikes", "GET"],
    "My Enquiries": ["/api/users/enquiries", "GET"],
    "Favorites": ["/api/users/favorites", "GET"],
    "Admin Dashboard": ["/api/admin/dashboard", "GET"],
    "Bike Management": ["/api/admin/bikes", "GET"],
    "Pending Bikes": ["/api/admin/bikes?tab=pending", "GET"],
    "Approved Bikes": ["/api/admin/bikes?tab=approved", "GET"],
    "Rejected Bikes": ["/api/admin/bikes?tab=rejected", "GET"],
    "Sold Out Admin": ["/api/admin/sold-bikes", "GET"],
    "User Management": ["/api/admin/users", "GET"],
    "Staff Management": ["/api/admin/staff", "GET"],
    "Customer Enquiries": ["/api/admin/enquiries", "GET"],
    "Customer Chat": ["/api/chat/conversations", "GET"],
    "Contact Messages": ["/api/admin/messages", "GET"],
    "Notifications": ["/api/notifications", "GET"],
    "Reports": ["/api/admin/reports/bikes", "GET"],
    "Superadmin Dashboard": ["/api/admin/dashboard", "GET"]
}

with open("my-node-app/app.py", "r", encoding="utf-8") as f:
    code = f.read()

print("Verifying route mappings in my-node-app/app.py:\n")
for name, (route, method) in endpoints_to_check.items():
    clean_route = route.split("?")[0].replace("<int:bike_id>", "")
    found = clean_route in code
    print(f"[{'FOUND' if found else 'MISSING'}] {name:25} -> {route} ({method})")
