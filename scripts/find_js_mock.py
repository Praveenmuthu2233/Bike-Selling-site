import os
import re

for root, dirs, files in os.walk("g:/SMRbikeSite-final"):
    if any(x in root for x in [".git", "venv", ".gemini", "__pycache__", "node_modules"]):
        continue
    for file in files:
        if file.endswith(".js"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = re.findall(r"(mock|dummy|fake|fallback|sample|hardcoded)", content, re.IGNORECASE)
                if matches and ("test" not in file.lower()):
                    lines = content.splitlines()
                    for idx, line in enumerate(lines, 1):
                        if any(w in line.lower() for w in ["mock", "dummy", "fake", "sample"]) and not line.strip().startswith("//"):
                            print(f"{filepath}:{idx} -> {line.strip()[:100]}")
