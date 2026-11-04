with open("my-node-app/templates/profile.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("profile.html catch blocks:")
for idx, line in enumerate(lines, 1):
    if "} catch (" in line or "} catch(" in line:
        print(f"L{idx}: {line.strip()}")
        for j in range(idx, min(len(lines), idx + 5)):
            print(f"   {lines[j].strip()}")
