import re

routes = []
with open('my-node-app/app.py', encoding='utf-8') as f:
    lines = f.readlines()

current_routes = []
for idx, line in enumerate(lines, 1):
    if line.strip().startswith('@app.route'):
        current_routes.append(line.strip())
    elif current_routes and line.strip().startswith('def '):
        fn_name = line.strip().split('(')[0].replace('def ', '')
        # scan next 40 lines of this function to see if it supports pagination
        fn_body = "".join(lines[idx:idx+45])
        has_page = 'page' in fn_body or 'limit' in fn_body or 'offset' in fn_body
        routes.append((current_routes, fn_name, idx, has_page))
        current_routes = []

print(f"Found {len(routes)} routes in app.py")
for r in routes:
    routes_str = " | ".join(r[0])
    if any(k in routes_str.lower() for k in ['admin', 'user', 'bike', 'enquir', 'chat', 'contact', 'staff', 'audit', 'notif', 'fav']):
        print(f"Line {r[2]}: {r[1]} -> {routes_str} (pagination: {r[3]})")
