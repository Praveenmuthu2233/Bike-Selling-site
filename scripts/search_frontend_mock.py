import os
import re

search_patterns = [
    "Hunter 350",
    "Pulsar NS200",
    "Duke 250",
    "MT-15",
    "Demo Rider",
    "mock",
    "dummy",
    "sample",
    "placeholder",
    "IN_MEMORY_STORE",
    "demo"
]

results = []

for root, dirs, files in os.walk("g:/SMRbikeSite-final"):
    # skip .git, venv, .gemini
    if any(x in root for x in [".git", "venv", ".gemini", "__pycache__", "node_modules"]):
        continue
    for file in files:
        if file.endswith((".html", ".js")):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pat in ["Hunter 350", "Pulsar NS200", "Demo Rider", "demo.rider@gmail.com"]:
                        if pat.lower() in content.lower():
                            results.append(f"{filepath}: matches '{pat}'")
            except Exception as e:
                pass

for r in results:
    print(r)
if not results:
    print("No occurrences of fake demo data found in HTML/JS!")
