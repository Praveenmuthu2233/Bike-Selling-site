import glob
import re

for f in sorted(glob.glob("my-node-app/templates/*.html") + glob.glob("my-node-app/static/*.js")):
    if "admin.html" in f or "adminModern.css" in f:
        continue
    with open(f, "r", encoding="utf-8") as file:
        for idx, line in enumerate(file):
            if re.search(r"approve|reject|administrative|admin", line, re.I):
                print(f"{f}:{idx+1}: {line.strip()[:110]}")
