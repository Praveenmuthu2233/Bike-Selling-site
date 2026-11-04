def replace_in_file(filepath, old_text, new_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_text in content:
        content = content.replace(old_text, new_text)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully replaced in {filepath}")
    else:
        # Try normalizing newlines
        content_norm = content.replace('\r\n', '\n')
        old_norm = old_text.replace('\r\n', '\n')
        new_norm = new_text.replace('\r\n', '\n')
        if old_norm in content_norm:
            content_norm = content_norm.replace(old_norm, new_norm)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_norm)
            print(f"Successfully replaced (normalized newlines) in {filepath}")
        else:
            print(f"Target not found in {filepath}")

old_box = '''          <!-- Hero Vehicle Card Showcase -->
          <div class="hero-visual" style="position: relative;">
            <div style="position: relative; border-radius: var(--radius-xl); overflow: hidden; border: 1px solid var(--border-medium); box-shadow: var(--shadow-lg), var(--shadow-glow);">
              <img src="{{ url_for('static', filename='images/IMG-20251204-WA0053.jpg') }}" alt="Featured Motorcycle" style="width: 100%; height: 380px; object-fit: cover;" onerror="this.src='/static/IMG-20251204-WA0053.jpg';" />
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

new_box = '''          <!-- Hero Showcase Presentation -->
          <div class="hero-visual" style="position: relative;">
            <div id="hero-featured-card" style="position: relative; border-radius: var(--radius-xl); overflow: hidden; border: 1px solid var(--border-medium); box-shadow: var(--shadow-lg), var(--shadow-glow);">
              <img id="hero-bike-img" src="{{ url_for('static', filename='images/IMG-20251204-WA0053.jpg') }}" alt="SMR Motors Certified Motorcycle" style="width: 100%; height: 380px; object-fit: cover;" onerror="this.src='/static/IMG-20251204-WA0053.jpg';" />
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

replace_in_file('my-node-app/templates/index.html', old_box, new_box)
replace_in_file('index.html', old_box.replace("{{ url_for('static', filename='images/IMG-20251204-WA0053.jpg') }}", "/static/images/IMG-20251204-WA0053.jpg"), new_box.replace("{{ url_for('static', filename='images/IMG-20251204-WA0053.jpg') }}", "/static/images/IMG-20251204-WA0053.jpg"))
