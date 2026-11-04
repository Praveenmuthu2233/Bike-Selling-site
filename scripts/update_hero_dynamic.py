paths = [
    'my-node-app/static/marketplace.js',
    'my-node-app/static/js/marketplace.js',
    'assets/js/marketplace.js'
]

target = '''    renderBikes(allBikes);
    renderPaginationControls(currentPagination);'''

replacement = '''    renderBikes(allBikes);
    renderPaginationControls(currentPagination);

    // Bind hero vehicle card dynamically to live TiDB motorcycle
    if (allBikes.length > 0) {
      const topBike = allBikes[0];
      const heroImg = document.getElementById('hero-bike-img');
      const heroTitle = document.getElementById('hero-bike-title');
      const heroSpecs = document.getElementById('hero-bike-specs');
      const heroPrice = document.getElementById('hero-bike-price');
      if (heroTitle && topBike) {
        heroTitle.textContent = topBike.title || `${topBike.brand || ''} ${topBike.model || ''}`;
        if (heroSpecs) {
          const yr = topBike.year || '';
          const km = topBike.kilometers_driven ? `${Number(topBike.kilometers_driven).toLocaleString('en-IN')} KM` : '';
          const fl = topBike.fuel_type || 'Petrol';
          heroSpecs.textContent = [yr, km, fl].filter(Boolean).join(' • ') || 'Inspected • RC Transfer Guarantee';
        }
        if (heroPrice && topBike.price !== undefined && topBike.price !== null) {
          heroPrice.textContent = `₹${Number(topBike.price).toLocaleString('en-IN')}`;
        }
        if (heroImg && topBike.images && topBike.images.length > 0) {
          heroImg.src = topBike.images[0];
        }
      }
    }'''

for p in paths:
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    if target in content:
        content = content.replace(target, replacement)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {p}")
    else:
        print(f"Target not found in {p}")
