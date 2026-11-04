# -*- coding: utf-8 -*-
"""
Patch all admin login pages and backend to completely remove prepopulated
admin credentials, hardcoded fallbacks, and URL spoofing.
"""

# 1. Update my-node-app/templates/adminLogin.html
admin_login_path = 'my-node-app/templates/adminLogin.html'
with open(admin_login_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace username input
old_u = 'placeholder="admin" value="admin"'
new_u = 'placeholder="Enter admin username" autocomplete="username" value=""'
if old_u in text:
    text = text.replace(old_u, new_u, 1)
    print("Replaced username input in adminLogin.html")

# Replace password input
old_p = 'placeholder="••••••••••••" value="admin123"'
new_p = 'placeholder="Enter admin password" autocomplete="current-password" value=""'
if old_p in text:
    text = text.replace(old_p, new_p, 1)
    print("Replaced password input in adminLogin.html")

# Clean DOMContentLoaded handler to guarantee fields are empty and no auto-redirect loops
old_dom = """    // Prevent redirect loops: only redirect if a valid session already exists
    document.addEventListener('DOMContentLoaded', () => {
      const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
      if (token) {
        // Quick verify session without loop
        fetch('/api/admin/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
          if (res.ok) {
            window.location.href = "{{ url_for('admin_page') }}";
          } else {
            // Expired token: clear and stay on login page
            localStorage.removeItem('adminToken');
            sessionStorage.removeItem('adminToken');
          }
        }).catch(() => {
          // If offline/error, stay on login page
        });
      }
    });"""

new_dom = """    // Guarantee credentials fields are always empty on page load
    document.addEventListener('DOMContentLoaded', () => {
      const uInput = document.getElementById('admin-username');
      const pInput = document.getElementById('admin-password');
      if (uInput) uInput.value = '';
      if (pInput) pInput.value = '';

      // Purge session tokens if explicit logout requested
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('logout') === 'true') {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('adminToken');
        localStorage.removeItem('admin_user');
        localStorage.removeItem('adminUser');
        sessionStorage.removeItem('admin_token');
        sessionStorage.removeItem('adminToken');
        sessionStorage.removeItem('admin_user');
        sessionStorage.removeItem('adminUser');
      }
    });"""

if old_dom in text:
    text = text.replace(old_dom, new_dom, 1)
    print("Replaced DOMContentLoaded handler in adminLogin.html")
else:
    # Try with CRLF
    old_dom_crlf = old_dom.replace('\n', '\r\n')
    new_dom_crlf = new_dom.replace('\n', '\r\n')
    if old_dom_crlf in text:
        text = text.replace(old_dom_crlf, new_dom_crlf, 1)
        print("Replaced DOMContentLoaded handler in adminLogin.html (CRLF)")

with open(admin_login_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved my-node-app/templates/adminLogin.html")


# 2. Update admin/login.html
admin_static_login = 'admin/login.html'
with open(admin_static_login, 'r', encoding='utf-8') as f:
    text_static = f.read()

if old_u in text_static:
    text_static = text_static.replace(old_u, new_u, 1)
    print("Replaced username input in admin/login.html")

if old_p in text_static:
    text_static = text_static.replace(old_p, new_p, 1)
    print("Replaced password input in admin/login.html")

old_dom_static = """    // Check if session already valid; redirect once to dashboard
    document.addEventListener('DOMContentLoaded', () => {
      const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
      if (token) {
        fetch('/api/admin/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
          if (res.ok) {
            window.location.href = 'dashboard.html';
          } else {
            localStorage.removeItem('adminToken');
            sessionStorage.removeItem('adminToken');
          }
        }).catch(() => {});
      }
    });"""

new_dom_static = """    // Guarantee credentials fields are always empty on page load
    document.addEventListener('DOMContentLoaded', () => {
      const uInput = document.getElementById('admin-username');
      const pInput = document.getElementById('admin-password');
      if (uInput) uInput.value = '';
      if (pInput) pInput.value = '';

      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('logout') === 'true') {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('adminToken');
        localStorage.removeItem('admin_user');
        localStorage.removeItem('adminUser');
        sessionStorage.removeItem('admin_token');
        sessionStorage.removeItem('adminToken');
        sessionStorage.removeItem('admin_user');
        sessionStorage.removeItem('adminUser');
      }
    });"""

if old_dom_static in text_static:
    text_static = text_static.replace(old_dom_static, new_dom_static, 1)
    print("Replaced DOMContentLoaded handler in admin/login.html")
else:
    old_dom_static_crlf = old_dom_static.replace('\n', '\r\n')
    new_dom_static_crlf = new_dom_static.replace('\n', '\r\n')
    if old_dom_static_crlf in text_static:
        text_static = text_static.replace(old_dom_static_crlf, new_dom_static_crlf, 1)
        print("Replaced DOMContentLoaded handler in admin/login.html (CRLF)")

with open(admin_static_login, 'w', encoding='utf-8') as f:
    f.write(text_static)
print("Saved admin/login.html")


# 3. Update my-node-app/templates/admin.html (Remove ?token= impersonation)
admin_html_path = 'my-node-app/templates/admin.html'
with open(admin_html_path, 'r', encoding='utf-8') as f:
    text_admin = f.read()

old_auth_bypass = """    // Authentication Guard
    function checkAdminAuth() {
      // Support URL token parameter for development & verification sessions
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('token')) {
        localStorage.setItem('admin_token', urlParams.get('token'));
        localStorage.setItem('admin_user', JSON.stringify({
          id: 1,
          username: urlParams.get('username') || 'admin',
          full_name: 'SMR Administrator',
          role: urlParams.get('role') || 'superadmin'
        }));
      }

      const token = localStorage.getItem('admin_token') || localStorage.getItem('adminToken') || sessionStorage.getItem('admin_token') || sessionStorage.getItem('adminToken');"""

new_auth_guard = """    // Authentication Guard
    function checkAdminAuth() {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('adminToken') || sessionStorage.getItem('admin_token') || sessionStorage.getItem('adminToken');"""

if old_auth_bypass in text_admin:
    text_admin = text_admin.replace(old_auth_bypass, new_auth_guard, 1)
    print("Removed URL token impersonation bypass from admin.html")
else:
    old_auth_bypass_crlf = old_auth_bypass.replace('\n', '\r\n')
    new_auth_guard_crlf = new_auth_guard.replace('\n', '\r\n')
    if old_auth_bypass_crlf in text_admin:
        text_admin = text_admin.replace(old_auth_bypass_crlf, new_auth_guard_crlf, 1)
        print("Removed URL token impersonation bypass from admin.html (CRLF)")

# Also update adminLogout to purge all token variants
old_logout = """    function adminLogout() {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('adminToken');
      localStorage.removeItem('admin_user');
      localStorage.removeItem('adminUser');
      sessionStorage.removeItem('admin_token');
      sessionStorage.removeItem('adminToken');
      window.location.href = '/admin/login.html';
    }"""

new_logout = """    function adminLogout() {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('adminToken');
      localStorage.removeItem('admin_user');
      localStorage.removeItem('adminUser');
      sessionStorage.removeItem('admin_token');
      sessionStorage.removeItem('adminToken');
      sessionStorage.removeItem('admin_user');
      sessionStorage.removeItem('adminUser');
      window.location.href = '/admin/login.html?logout=true';
    }"""

if old_logout in text_admin:
    text_admin = text_admin.replace(old_logout, new_logout, 1)
    print("Updated adminLogout in admin.html")
else:
    old_logout_crlf = old_logout.replace('\n', '\r\n')
    new_logout_crlf = new_logout.replace('\n', '\r\n')
    if old_logout_crlf in text_admin:
        text_admin = text_admin.replace(old_logout_crlf, new_logout_crlf, 1)
        print("Updated adminLogout in admin.html (CRLF)")

with open(admin_html_path, 'w', encoding='utf-8') as f:
    f.write(text_admin)
print("Saved my-node-app/templates/admin.html")


# 4. Update my-node-app/app.py (Remove hardcoded adminAccounts dictionary passwords and fallback)
app_py_path = 'my-node-app/app.py'
with open(app_py_path, 'r', encoding='utf-8') as f:
    text_app = f.read()

old_accounts = """adminAccounts = {
    "admin":   {"password": "admin123",  "name": "Administrator", "role": "superadmin"},
    "mani":    {"password": "mani@22",    "name": "Mani (Staff)",   "role": "admin"},
    "murugan": {"password": "murugan@22", "name": "Murugan (Owner)", "role": "superadmin"},
    "raja":    {"password": "raja@22",    "name": "Raja (Owner)",    "role": "superadmin"},
}"""

new_accounts = """# In-memory dictionary no longer holds static plaintext passwords.
# Authentication is strictly database-driven via TiDB Cloud admins table.
adminAccounts = {}"""

if old_accounts in text_app:
    text_app = text_app.replace(old_accounts, new_accounts, 1)
    print("Replaced adminAccounts dictionary in app.py")
else:
    old_accounts_crlf = old_accounts.replace('\n', '\r\n')
    new_accounts_crlf = new_accounts.replace('\n', '\r\n')
    if old_accounts_crlf in text_app:
        text_app = text_app.replace(old_accounts_crlf, new_accounts_crlf, 1)
        print("Replaced adminAccounts dictionary in app.py (CRLF)")

# Remove the fallback to adminAccounts in admin_login_api
old_login_fallback = """    # 2. Fall back to configured adminAccounts
    if not admin_data:
        acc = adminAccounts.get(username)
        if acc and acc["password"] == password:
            norm_role = normalize_admin_role(acc.get("role"))
            admin_data = {
                "id": 1,
                "username": username,
                "name": acc["name"],
                "role": norm_role
            }

    if not admin_data:
        return jsonify({"success": False, "message": "Invalid Administrator Credentials"}), 401"""

new_login_fallback = """    # 2. Strict Database Authentication: Reject if no database record found
    if not admin_data:
        return jsonify({"success": False, "message": "Invalid Administrator Credentials"}), 401"""

if old_login_fallback in text_app:
    text_app = text_app.replace(old_login_fallback, new_login_fallback, 1)
    print("Removed hardcoded login fallback in admin_login_api")
else:
    old_login_fallback_crlf = old_login_fallback.replace('\n', '\r\n')
    new_login_fallback_crlf = new_login_fallback.replace('\n', '\r\n')
    if old_login_fallback_crlf in text_app:
        text_app = text_app.replace(old_login_fallback_crlf, new_login_fallback_crlf, 1)
        print("Removed hardcoded login fallback in admin_login_api (CRLF)")

with open(app_py_path, 'w', encoding='utf-8') as f:
    f.write(text_app)
print("Saved my-node-app/app.py")
