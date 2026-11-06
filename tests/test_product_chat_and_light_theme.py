import os
import sys
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("SMR MOTORS - PRODUCT CHAT & LIGHT THEME VERIFICATION SUITE")
print("=" * 70)

# TEST 1: Check style.css :root variables for Light Theme
print("\n[TEST 1] Verifying style.css Light Theme Palette...")
style_path = 'my-node-app/static/style.css'
with open(style_path, 'r', encoding='utf-8') as f:
    style_content = f.read()

required_vars = [
    ('--bg-primary', '#F8FAFC'),
    ('--bg-surface', '#FFFFFF'),
    ('--accent-primary', '#2563EB'),
    ('--accent-hover', '#1D4ED8'),
    ('--text-primary', '#172033'),
    ('--heading-color', '#0F172A'),
    ('--border-subtle', '#E2E8F0'),
    ('--color-success', '#16A34A'),
    ('--color-danger', '#DC2626'),
    ('--footer-bg', '#F1F5F9')
]

for var_name, expected_val in required_vars:
    pattern = rf'{re.escape(var_name)}:\s*{re.escape(expected_val)}'
    assert re.search(pattern, style_content), f"Missing or incorrect variable: {var_name}"
    print(f"  ✓ {var_name}: {expected_val} verified")

# TEST 2: Check secondary CSS files for Light Mode
print("\n[TEST 2] Verifying secondary stylesheets (components.css, user.css, auth.css, adminModern.css)...")
with open('my-node-app/static/components.css', 'r', encoding='utf-8') as f:
    comp_content = f.read()
assert '#2563EB' in comp_content, "components.css should have #2563EB blue accent"
assert '.bike-card {' in comp_content
assert 'background: #FFFFFF;' in comp_content
print("  ✓ components.css contains light bike card & blue accents")

with open('my-node-app/static/user.css', 'r', encoding='utf-8') as f:
    user_content = f.read()
assert 'background: #FFFFFF;' in user_content
assert 'color: #2563EB;' in user_content
print("  ✓ user.css contains light sidebar & blue active tabs")

with open('my-node-app/static/auth.css', 'r', encoding='utf-8') as f:
    auth_content = f.read()
assert 'background: #FFFFFF;' in auth_content
assert 'color: #0F172A;' in auth_content
print("  ✓ auth.css contains light auth card & dark heading")

with open('my-node-app/static/adminModern.css', 'r', encoding='utf-8') as f:
    admin_css_content = f.read()
assert '--admin-primary: #2563EB;' in admin_css_content
assert '--admin-sidebar-accent: #2563EB;' in admin_css_content
print("  ✓ adminModern.css contains #2563EB admin primary & sidebar accent")

# TEST 3: User Product Chat in profile.html & user/profile.html
print("\n[TEST 3] Verifying User Product Chat logic in profile.html...")
for pfile in ['my-node-app/templates/profile.html', 'user/profile.html']:
    with open(pfile, 'r', encoding='utf-8') as f:
        p_content = f.read()

    assert 'c.bike_title' in p_content, f"bike_title missing in {pfile}"
    assert 'c.bike_price' in p_content, f"bike_price missing in {pfile}"
    assert 'chatHeaderTitle' in p_content, f"Dynamic header title missing in {pfile}"
    assert 'userChatActiveRequestToken' in p_content, f"Active request token missing in {pfile}"
    assert 'AbortController' in p_content, f"AbortController missing in {pfile}"
    assert 'existingConv' in p_content, f"Duplicate conversation prevention missing in {pfile}"
    assert 'background: #FFFFFF;' in p_content, f"Light chat styling missing in {pfile}"
    assert 'background: #EFF6FF;' in p_content, f"Light blue active / outgoing bubble missing in {pfile}"
    print(f"  ✓ {pfile} product chat switching & light theme verified")

# TEST 4: Admin Chat integrity in admin.html
print("\n[TEST 4] Verifying Admin Customer Chat in admin.html...")
with open('my-node-app/templates/admin.html', 'r', encoding='utf-8') as f:
    admin_content = f.read()
assert 'openAdminConversation' in admin_content
assert 'loadAdminChat' in admin_content
assert 'sendAdminChatMessage' in admin_content
assert '#2563EB' in admin_content, "admin.html chat should use blue accents"
print("  ✓ admin.html chat functions intact & styled with blue theme")

# TEST 5: JavaScript syntax extraction and validation
print("\n[TEST 5] Checking JavaScript syntax in updated templates...")
import subprocess
js_check_script = """
const fs = require('fs');
const files = [
  'my-node-app/templates/profile.html',
  'my-node-app/templates/admin.html',
  'my-node-app/templates/enquiry-bike-details.html',
  'my-node-app/templates/SoldOutPage.html'
];

let hasError = false;
for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  const scripts = content.match(/<script(?![^>]*src=)[^>]*>([\\s\\S]*?)<\\/script>/gi) || [];
  let scriptIndex = 0;
  for (const s of scripts) {
    scriptIndex++;
    let code = s.replace(/<script[^>]*>/i, '').replace(/<\\/script>/i, '');
    // Clean Jinja template placeholders
    code = code.replace(/\\{\\{[^}]*\\}\\}/g, 'placeholder_val');
    code = code.replace(/\\{%[^%]*%\\}/g, '');
    try {
      new Function(code);
    } catch (e) {
      console.error(`JS Syntax Error in ${file} (Script #${scriptIndex}):`, e.message);
      hasError = true;
    }
  }
  console.log(`  ✓ Checked ${scripts.length} script tags in ${file}`);
}
if (hasError) process.exit(1);
"""

with open('scripts/test_js_syntax.js', 'w', encoding='utf-8') as f:
    f.write(js_check_script)

res = subprocess.run(['node', 'scripts/test_js_syntax.js'], capture_output=True, text=True)
print(res.stdout)
if res.returncode != 0:
    print(res.stderr)
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL TESTS PASSED SUCCESSFULLY! (5/5)")
print("=" * 70)
