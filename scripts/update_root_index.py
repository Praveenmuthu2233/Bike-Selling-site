with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_s = '''          <!-- Hero Vehicle Card Showcase -->
          <div class="hero-visual" style="position: relative;">
            <div style="position: relative; border-radius: var(--radius-xl); overflow: hidden; border: 1px solid var(--border-medium); box-shadow: var(--shadow-lg), var(--shadow-glow);">
              <img src="assets/images/IMG-20251204-WA0053.jpg" alt="Featured Motorcycle" style="width: 100%; height: 380px; object-fit: cover;" onerror="this.src='https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=800&q=80';" />
              <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(11,15,23,0.95), transparent); padding: 2rem 1.5rem 1.25rem;">
                <span class="badge badge-featured"><i class="fas fa-award"></i> Featured Arrival</span>
                <h3 style="font-size: 1.35rem; margin: 0.5rem 0 0.25rem;">Royal Enfield Hunter 350</h3>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 0.9rem; color: var(--text-secondary);">2023 • 8,400 KM • Petrol</span>
                  <span style="font-family: var(--font-display); font-size: 1.3rem; font-weight: 800; color: #FFF;">₹1,45,000</span>
                </div>
              </div>
            </div>
          </div>'''

new_s = '''          <!-- Hero Showcase Presentation -->
          <div class="hero-visual" style="position: relative;">
            <div id="hero-featured-card" style="position: relative; border-radius: var(--radius-xl); overflow: hidden; border: 1px solid var(--border-medium); box-shadow: var(--shadow-lg), var(--shadow-glow);">
              <img id="hero-bike-img" src="assets/images/IMG-20251204-WA0053.jpg" alt="SMR Motors Certified Motorcycle" style="width: 100%; height: 380px; object-fit: cover;" onerror="this.src='https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=800&q=80';" />
              <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(11,15,23,0.95), transparent); padding: 2rem 1.5rem 1.25rem;">
                <span class="badge badge-featured"><i class="fas fa-certificate"></i> Certified Pre-Owned</span>
                <h3 id="hero-bike-title" style="font-size: 1.35rem; margin: 0.5rem 0 0.25rem;">SMR Motors Certified Selection</h3>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span id="hero-bike-specs" style="font-size: 0.9rem; color: var(--text-secondary);">Verified Inspection • Clean RC Transfer</span>
                  <span id="hero-bike-price" style="font-family: var(--font-display); font-size: 1.3rem; font-weight: 800; color: #FFF;">Explore Below &darr;</span>
                </div>
              </div>
            </div>
          </div>'''

if old_s in c:
    c = c.replace(old_s, new_s)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Updated root index.html")
else:
    print("Could not find old_s in root index.html")
