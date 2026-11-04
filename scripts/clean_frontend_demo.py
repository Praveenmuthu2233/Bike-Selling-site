import os

# 1. Clean my-node-app/static/marketplace.js
market_js_paths = [
    'my-node-app/static/marketplace.js',
    'my-node-app/static/js/marketplace.js',
    'assets/js/marketplace.js'
]

for p in market_js_paths:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            code = f.read()

        # Remove fallbackBrands
        old_fallback = """  } catch (e) {
    const currentSelected = activeFilterState.brand || brandSelect.value || '';
    const fallbackBrands = ['Royal Enfield', 'Yamaha', 'KTM', 'Bajaj', 'Honda', 'TVS', 'BMW'];
    brandSelect.innerHTML = `<option value="">All Brands</option>` + fallbackBrands.map(b => `<option value="${b}" ${b.toLowerCase() === currentSelected.toLowerCase() ? 'selected' : ''}>${b}</option>`).join('');
  }"""
        new_fallback = """  } catch (e) {
    brandSelect.innerHTML = `<option value="">All Brands</option>`;
  }"""
        if old_fallback in code:
            code = code.replace(old_fallback, new_fallback)

        # Enhance empty state in renderBikes
        old_empty = """  if (!bikes || bikes.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <i class="fas fa-motorcycle empty-state-icon"></i>
        <h3>No motorcycles found</h3>
        <p>Try adjusting your search criteria or price filters.</p>
        <button onclick="resetMarketplaceFilters()" class="btn btn-outline" style="margin-top: 1rem;">Reset Filters</button>
      </div>
    `;
    return;
  }"""
        new_empty = """  if (!bikes || bikes.length === 0) {
    const hasFilter = isAnyFilterActive();
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 4rem 1.5rem;">
        <i class="fas fa-motorcycle empty-state-icon" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
        <h3 style="font-size: 1.3rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.5rem;">
          ${hasFilter ? 'No matching motorcycles found' : 'No motorcycles currently listed in inventory'}
        </h3>
        <p style="color: var(--text-muted); max-width: 480px; margin: 0 auto 1.5rem auto;">
          ${hasFilter ? 'Try adjusting your search keyword, category, or price range filters.' : 'Our verified showroom inventory is being updated. Please check back soon or submit your motorcycle for evaluation.'}
        </p>
        ${hasFilter 
          ? '<button onclick="resetMarketplaceFilters()" class="btn btn-outline"><i class="fas fa-undo"></i> Reset Filters</button>' 
          : '<a href="/sell-bike.html" class="btn btn-primary" style="display:inline-flex; align-items:center; gap:0.5rem;"><i class="fas fa-plus"></i> Sell Your Motorcycle</a>'}
      </div>
    `;
    return;
  }"""
        if old_empty in code:
            code = code.replace(old_empty, new_empty)

        with open(p, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Cleaned {p}")

# 2. Clean login templates (remove demoLogin triggers)
for p in ['my-node-app/templates/userLogin.html', 'login.html']:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            code = f.read()
        old_demo = "AuthService.demoLogin(rememberMe);"
        new_demo = "alert('Google Identity service is initializing. Please ensure popups/cookies are allowed and try again.');"
        if old_demo in code:
            code = code.replace(old_demo, new_demo)
        old_demo2 = "AuthService.demoLogin();"
        if old_demo2 in code:
            code = code.replace(old_demo2, "alert('Google Identity service is initializing. Please ensure popups/cookies are allowed and try again.');")
        with open(p, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Cleaned login demo in {p}")

# 3. Clean static demo titles in templates
p_sold = 'my-node-app/templates/sold-bike-details.html'
if os.path.exists(p_sold):
    with open(p_sold, 'r', encoding='utf-8') as f:
        code = f.read()
    code = code.replace('<h1 class="sold-banner-title" id="banner-title">Royal Enfield Classic 350</h1>', '<h1 class="sold-banner-title" id="banner-title">Loading Motorcycle...</h1>')
    with open(p_sold, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Cleaned banner title in {p_sold}")

p_admin = 'my-node-app/templates/admin.html'
if os.path.exists(p_admin):
    with open(p_admin, 'r', encoding='utf-8') as f:
        code = f.read()
    code = code.replace('<span id="sold-bike-brand-model-display">Royal Enfield • Classic 350</span>', '<span id="sold-bike-brand-model-display">Motorcycle Details</span>')
    with open(p_admin, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Cleaned modal text in {p_admin}")

# 4. Clean data.json, category.json, galary.json (set to empty arrays)
for p in ['data.json', 'category.json', 'my-node-app/public/galary.json']:
    if os.path.exists(p):
        with open(p, 'w', encoding='utf-8') as f:
            f.write('[]\n')
        print(f"Emptyed {p} to []")

# 5. Clean _unused_auth_demo_google_api from my-node-app/app.py
p_app = 'my-node-app/app.py'
if os.path.exists(p_app):
    with open(p_app, 'r', encoding='utf-8') as f:
        code = f.read()
    old_demo_block = """@app.route("/api/auth/demo-google", methods=["POST"])
@app.route("/auth/demo-google", methods=["POST"])
def auth_demo_google_api():
    return jsonify({"success": False, "message": "Demo sign-in disabled. Please sign in with Google."}), 403
def _unused_auth_demo_google_api():"""
    new_demo_block = """@app.route("/api/auth/demo-google", methods=["POST"])
@app.route("/auth/demo-google", methods=["POST"])
def auth_demo_google_api():
    return jsonify({"success": False, "message": "Demo sign-in permanently disabled in production. Please sign in with Google."}), 403
def _unused_auth_demo_google_api():
    return jsonify({"success": False, "message": "Disabled"}), 403
def _disabled_auth_demo_legacy():"""
    if old_demo_block in code:
        code = code.replace(old_demo_block, new_demo_block)
        with open(p_app, 'w', encoding='utf-8') as f:
            f.write(code)
        print("Cleaned demo auth endpoint in app.py")

print("Frontend and codebase demo data cleanup completed.")
