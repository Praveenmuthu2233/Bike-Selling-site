import os
import re

html_files = []
for root, dirs, files in os.walk('.'):
    # Skip node_modules, .git, .vscode, certs
    if any(skip in root for skip in ['node_modules', '.git', '.vscode', 'certs', '__pycache__']):
        continue
    for f in files:
        if f.endswith('.html'):
            html_files.append(os.path.join(root, f))

print(f"Total HTML files found: {len(html_files)}")

results = []
all_ok = True

for path in sorted(html_files):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    has_anti_fouc = "localStorage.getItem('smr_theme')" in content or 'localStorage.getItem("smr_theme")' in content
    has_theme_css = "theme.css" in content
    has_theme_js = "theme.js" in content
    has_toggle = "theme-toggle-btn" in content

    status = {
        'path': path,
        'fouc': has_anti_fouc,
        'css': has_theme_css,
        'js': has_theme_js,
        'toggle': has_toggle
    }
    results.append(status)

    # Let's check missing elements
    issues = []
    if not has_anti_fouc:
        issues.append("MISSING ANTI-FOUC")
    if not has_theme_css:
        issues.append("MISSING THEME.CSS")
    if not has_theme_js:
        issues.append("MISSING THEME.JS")

    if issues:
        print(f"[FAIL] {path}: {', '.join(issues)}")
        all_ok = False
    else:
        toggle_str = "with toggle" if has_toggle else "no toggle (modal/subpage/standalone)"
        print(f"[OK] {path} ({toggle_str})")

print("\n--- Summary ---")
print(f"All files checked: {len(html_files)}")
print(f"Overall status: {'ALL PASSED' if all_ok else 'SOME FAILED'}")
