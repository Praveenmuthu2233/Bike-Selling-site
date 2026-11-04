import re

files_to_check = [
    r"g:\SMRbikeSite-final\index.html",
    r"g:\SMRbikeSite-final\login.html",
    r"g:\SMRbikeSite-final\assets\js\auth.js",
    r"g:\SMRbikeSite-final\my-node-app\static\auth.js",
    r"g:\SMRbikeSite-final\my-node-app\static\js\auth.js",
    r"g:\SMRbikeSite-final\my-node-app\templates\admin.html",
    r"g:\SMRbikeSite-final\my-node-app\templates\adminAddListing.html",
    r"g:\SMRbikeSite-final\my-node-app\templates\contact.html",
    r"g:\SMRbikeSite-final\my-node-app\templates\index.html",
    r"g:\SMRbikeSite-final\my-node-app\templates\profile.html",
    r"g:\SMRbikeSite-final\my-node-app\templates\userLogin.html",
    r"g:\SMRbikeSite-final\user\profile.html"
]

for fp in files_to_check:
    print(f"\n=== {fp} ===")
    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            if any(k in line for k in ["Hunter 350", "Demo Rider", "demo.rider@gmail.com"]):
                print(f"L{idx}: {line.strip()[:100]}")
