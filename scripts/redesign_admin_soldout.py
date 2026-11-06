import os

def update_admin_soldout_section():
    fpath = os.path.join("my-node-app", "templates", "admin.html")
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update tab-soldout-bikes HTML
    old_section_header = """            <!-- Filter Controls -->
            <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
              <div class="toolbar-search-input" style="flex:1; min-width:220px;">
                <i class="fas fa-search"></i>
                <input type="text" id="soldBikeFilterSearch" placeholder="Search by title, brand, reg number, seller..." oninput="debounceSoldBikeSearch()">
              </div>
              <select id="soldBikeFilterPaymentStatus" class="form-input-modern" style="width:160px; padding:0.45rem 0.75rem;" onchange="loadSoldOutBikesView(1)">
                <option value="all">All Payment Status</option>
                <option value="Full Payment">Full Payment</option>
                <option value="Partial">Partial / Advance</option>
                <option value="Pending">Payment Pending</option>
              </select>
              <select id="soldBikeFilterBrand" class="form-input-modern" style="width:170px; padding:0.45rem 0.75rem;" onchange="loadSoldOutBikesView(1)">
                <option value="all">All Brands</option>
                <option value="Royal Enfield">Royal Enfield</option>
                <option value="Yamaha">Yamaha</option>
                <option value="KTM">KTM</option>
                <option value="Bajaj">Bajaj</option>
                <option value="Honda">Honda</option>
                <option value="TVS">TVS</option>
                <option value="Hero">Hero</option>
                <option value="Suzuki">Suzuki</option>
              </select>
              <div style="display:flex; align-items:center; gap:6px;">
                <span style="font-size:0.8rem; color:var(--admin-text-secondary);">From:</span>
                <input type="date" id="soldBikeStartDate" class="form-input-modern" style="width:140px; padding:0.4rem 0.6rem;" onchange="loadSoldOutBikesView(1)">
              </div>
              <div style="display:flex; align-items:center; gap:6px;">
                <span style="font-size:0.8rem; color:var(--admin-text-secondary);">To:</span>
                <input type="date" id="soldBikeEndDate" class="form-input-modern" style="width:140px; padding:0.4rem 0.6rem;" onchange="loadSoldOutBikesView(1)">
              </div>
              <button class="btn-table-action" onclick="resetSoldBikeFilters()" title="Reset Filters"><i class="fas fa-rotate-left"></i></button>
            </div>
          </div>

          <div class="table-responsive-wrapper">
            <table class="admin-data-table responsive-table-mobile">
              <thead>
                <tr>
                  <th>Motorcycle Details</th>
                  <th>Brand & Model</th>
                  <th>Registration No.</th>
                  <th>Specs (Year/KM/Fuel)</th>
                  <th>Seller Info</th>
                  <th>Sold Date & Time</th>
                  <th>Sold By</th>
                  <th>Final Price</th>
                  <th class="fin-col-superadmin">Net Profit</th>
                  <th>Status</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="soldout-bikes-tbody">
                <tr><td colspan="11" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading sales ledger...</td></tr>
              </tbody>
            </table>
          </div>
          <div class="pagination-container-modern" id="soldout-bikes-pagination" style="margin-top:1.25rem;"></div>"""

    new_section_header = """            <!-- Filter Controls -->
            <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
              <div class="toolbar-search-input" style="flex:1; min-width:220px;">
                <i class="fas fa-search"></i>
                <input type="text" id="soldBikeFilterSearch" placeholder="Search by title, brand, reg number, seller..." oninput="debounceSoldBikeSearch()">
              </div>
              <select id="soldBikeFilterPaymentStatus" class="form-input-modern" style="width:160px; padding:0.45rem 0.75rem;" onchange="loadSoldOutBikesView(1)">
                <option value="all">All Payment Status</option>
                <option value="Full Payment">Full Payment</option>
                <option value="Partial">Partial / Advance</option>
                <option value="Pending">Payment Pending</option>
              </select>
              <select id="soldBikeFilterBrand" class="form-input-modern" style="width:170px; padding:0.45rem 0.75rem;" onchange="loadSoldOutBikesView(1)">
                <option value="all">All Brands</option>
                <option value="Royal Enfield">Royal Enfield</option>
                <option value="Yamaha">Yamaha</option>
                <option value="KTM">KTM</option>
                <option value="Bajaj">Bajaj</option>
                <option value="Honda">Honda</option>
                <option value="TVS">TVS</option>
                <option value="Hero">Hero</option>
                <option value="Suzuki">Suzuki</option>
              </select>
              <div style="display:flex; align-items:center; gap:6px;">
                <span style="font-size:0.8rem; color:var(--admin-text-secondary);">From:</span>
                <input type="date" id="soldBikeStartDate" class="form-input-modern" style="width:140px; padding:0.4rem 0.6rem;" onchange="loadSoldOutBikesView(1)">
              </div>
              <div style="display:flex; align-items:center; gap:6px;">
                <span style="font-size:0.8rem; color:var(--admin-text-secondary);">To:</span>
                <input type="date" id="soldBikeEndDate" class="form-input-modern" style="width:140px; padding:0.4rem 0.6rem;" onchange="loadSoldOutBikesView(1)">
              </div>
              <button class="btn-table-action" onclick="resetSoldBikeFilters()" title="Reset Filters"><i class="fas fa-rotate-left"></i></button>
            </div>

            <!-- Scope Bar & View Mode Toggle (Light Theme) -->
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding:0.85rem 1rem; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:var(--radius-md); margin-top:0.25rem;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="badge-status badge-approved" id="soldout-scope-badge" style="font-size:0.75rem; padding:3px 10px; font-weight:800;">
                  <i class="fas fa-clock-rotate-left"></i> Latest 6 Units
                </span>
                <span style="font-size:0.82rem; color:var(--admin-text-secondary);" id="soldout-scope-desc">
                  Showing latest 6 sold motorcycles, sorted newest first. Older sales preserved in full history.
                </span>
              </div>
              <div style="display:flex; gap:8px; align-items:center;">
                <button type="button" id="btn-toggle-sold-view" onclick="toggleSoldViewScope()" class="btn-table-action" style="background:#FFFFFF; color:#2563EB; border:1px solid #2563EB; font-weight:700;">
                  <i class="fas fa-list-check"></i> View All Archive
                </button>
                <div style="display:inline-flex; border:1px solid #CBD5E1; border-radius:6px; overflow:hidden;">
                  <button type="button" id="btn-sold-display-cards" onclick="setSoldDisplayFormat('cards')" class="btn-table-action" style="border:none; border-radius:0; padding:6px 12px; background:#2563EB; color:#fff;" title="Cards View"><i class="fas fa-th-large"></i> Cards</button>
                  <button type="button" id="btn-sold-display-table" onclick="setSoldDisplayFormat('table')" class="btn-table-action" style="border:none; border-radius:0; padding:6px 12px; background:#fff; color:#475569;" title="Table View"><i class="fas fa-table"></i> Table</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Responsive Mobile/Desktop Cards Grid -->
          <div id="soldout-cards-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:1.25rem; margin-top:1.25rem;">
            <div style="grid-column:1/-1; text-align:center; padding:3rem;"><i class="fas fa-spinner fa-spin" style="font-size:2rem; color:var(--admin-info);"></i></div>
          </div>

          <!-- Responsive Tabular View Wrapper (Desktop Switch) -->
          <div id="soldout-table-wrapper" class="table-responsive-wrapper" style="display:none; margin-top:1.25rem;">
            <table class="admin-data-table responsive-table-mobile">
              <thead>
                <tr>
                  <th>Motorcycle Details</th>
                  <th>Brand & Model</th>
                  <th>Registration No.</th>
                  <th>Specs (Year/KM/Fuel)</th>
                  <th>Seller Info</th>
                  <th>Sold Date & Time</th>
                  <th>Sold By</th>
                  <th>Final Price</th>
                  <th class="fin-col-superadmin">Net Profit</th>
                  <th>Status</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody id="soldout-bikes-tbody">
                <tr><td colspan="11" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading sales ledger...</td></tr>
              </tbody>
            </table>
          </div>
          <div class="pagination-container-modern" id="soldout-bikes-pagination" style="margin-top:1.25rem;"></div>"""

    if old_section_header in content:
        content = content.replace(old_section_header, new_section_header, 1)
        print("Updated tab-soldout-bikes layout with Scope Bar and Dual View")
    else:
        print("old_section_header not found in admin.html")

    # 2. Update adminPages.soldout default limit to 6
    content = content.replace("soldout: { page: 1, limit: 10 }", "soldout: { page: 1, limit: 6 }")

    # 3. Update loadSoldOutBikesView in JavaScript
    old_load_fn = """    async function loadSoldOutBikesView(page = 1, limit = null) {
      limit = limit || adminPages.soldout.limit || 10;
      const tbody = document.getElementById('soldout-bikes-tbody');
      if (!tbody) return;
      tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading sales archive...</td></tr>';"""

    new_load_fn = """    let soldDisplayFormat = 'cards';
    let soldViewScopeAll = false;

    function setSoldDisplayFormat(fmt) {
      soldDisplayFormat = fmt;
      const cardsGrid = document.getElementById('soldout-cards-grid');
      const tableWrap = document.getElementById('soldout-table-wrapper');
      const btnCards = document.getElementById('btn-sold-display-cards');
      const btnTable = document.getElementById('btn-sold-display-table');

      if (fmt === 'table') {
        if (cardsGrid) cardsGrid.style.display = 'none';
        if (tableWrap) tableWrap.style.display = 'block';
        if (btnCards) { btnCards.style.background = '#fff'; btnCards.style.color = '#475569'; }
        if (btnTable) { btnTable.style.background = '#2563EB'; btnTable.style.color = '#fff'; }
      } else {
        if (cardsGrid) cardsGrid.style.display = 'grid';
        if (tableWrap) tableWrap.style.display = 'none';
        if (btnCards) { btnCards.style.background = '#2563EB'; btnCards.style.color = '#fff'; }
        if (btnTable) { btnTable.style.background = '#fff'; btnTable.style.color = '#475569'; }
      }
    }

    function toggleSoldViewScope() {
      soldViewScopeAll = !soldViewScopeAll;
      const scopeBadge = document.getElementById('soldout-scope-badge');
      const scopeDesc = document.getElementById('soldout-scope-desc');
      const toggleBtn = document.getElementById('btn-toggle-sold-view');

      if (soldViewScopeAll) {
        adminPages.soldout.limit = 24;
        if (scopeBadge) {
          scopeBadge.className = 'badge-status badge-pending';
          scopeBadge.innerHTML = '<i class="fas fa-database"></i> Full Sales Archive';
        }
        if (scopeDesc) scopeDesc.textContent = 'Viewing complete historical sales archive with 24 units per page.';
        if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-clock-rotate-left"></i> Latest 6 Units View';
      } else {
        adminPages.soldout.limit = 6;
        if (scopeBadge) {
          scopeBadge.className = 'badge-status badge-approved';
          scopeBadge.innerHTML = '<i class="fas fa-clock-rotate-left"></i> Latest 6 Units';
        }
        if (scopeDesc) scopeDesc.textContent = 'Showing latest 6 sold motorcycles, sorted newest first. Older sales preserved in full history.';
        if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-list-check"></i> View All Archive';
      }
      loadSoldOutBikesView(1, adminPages.soldout.limit);
    }

    async function loadSoldOutBikesView(page = 1, limit = null) {
      limit = limit || adminPages.soldout.limit || 6;
      adminPages.soldout.page = page;
      adminPages.soldout.limit = limit;

      const cardsGrid = document.getElementById('soldout-cards-grid');
      const tbody = document.getElementById('soldout-bikes-tbody');
      if (cardsGrid) cardsGrid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:3rem;"><i class="fas fa-spinner fa-spin" style="font-size:2rem; color:var(--admin-info);"></i></div>';
      if (tbody) tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; padding:2rem;"><i class="fas fa-spinner fa-spin"></i> Loading sales archive...</td></tr>';"""

    if old_load_fn in content:
        content = content.replace(old_load_fn, new_load_fn, 1)
        print("Updated loadSoldOutBikesView start")
    else:
        print("old_load_fn not found")

    # 4. Update the render loop in loadSoldOutBikesView to populate cardsGrid as well
    old_render_end = """        tbody.innerHTML = list.map(b => {
          const img = b.primary_image || (b.images && b.images[0]) || '/static/images/IMG-20251204-WA0053.jpg';
          const finalPrice = parseFloat(b.final_selling_price || 0).toLocaleString('en-IN');
          const profit = parseFloat(b.realized_profit || 0).toLocaleString('en-IN');
          const soldDate = (b.sold_date || '').substring(0, 16).replace('T', ' ');

          return `
            <tr>
              <td data-label="Motorcycle Details">
                <div class="table-bike-item">
                  <img src="${img}" class="table-bike-thumb" alt="${b.title}">
                  <div class="table-bike-info">
                    <span class="table-bike-title">#${b.bike_id} - ${b.title}</span>
                    <span class="table-bike-meta">Listed: ${(b.original_listing_date || '').substring(0, 10)}</span>
                  </div>
                </div>
              </td>
              <td data-label="Brand & Model"><strong>${b.brand}</strong> <span style="color:var(--admin-text-secondary);">${b.model}</span></td>
              <td data-label="Registration No."><span style="font-family:monospace; font-weight:700; background:#F1F5F9; padding:2px 6px; border-radius:4px;">${b.registration_number || 'TN-XX-XXXX'}</span></td>
              <td data-label="Specs">${b.year} &bull; ${(b.kilometers_driven || 0).toLocaleString()} km &bull; ${b.fuel_type || 'Petrol'}</td>
              <td data-label="Seller Info">
                <div>${b.seller_name || 'SMR Motors'}</div>
                <div style="font-size:0.75rem; color:var(--admin-text-secondary);">${b.seller_phone || ''}</div>
              </td>
              <td data-label="Sold Date & Time"><span style="font-size:0.82rem; color:var(--admin-text-secondary);">${soldDate}</span></td>
              <td data-label="Sold By"><strong>${b.sold_by || 'admin'}</strong></td>
              <td data-label="Final Price"><strong>₹${finalPrice}</strong></td>
              ${isSuper ? `
                <td data-label="Net Profit" class="fin-col-superadmin"><strong style="color:var(--admin-success);">₹${profit}</strong></td>
              ` : `
                <td class="fin-col-superadmin" style="display:none;">-</td>
              `}
              <td data-label="Status"><span class="badge-status badge-sold">SOLD OUT</span></td>
              <td data-label="Actions" style="text-align:right;">
                <div class="table-action-group">
                  <a href="/admin/sold-bike-details.html?id=${b.bike_id}" class="btn-table-action" style="text-decoration:none; display:inline-flex; align-items:center; gap:4px;" title="View Complete Historical Snapshot">
                    <i class="fas fa-eye"></i> View Details
                  </a>
                </div>
              </td>
            </tr>
          `;
        }).join('');

        renderPagination('soldout-bikes-pagination', 'soldout', res.pagination);"""

    new_render_end = """        // Render Responsive Cards Grid
        if (cardsGrid) {
          cardsGrid.innerHTML = list.map(b => {
            const img = b.primary_image || (b.images && b.images[0]) || '/static/images/IMG-20251204-WA0053.jpg';
            const finalPrice = parseFloat(b.final_selling_price || 0).toLocaleString('en-IN');
            const profit = parseFloat(b.realized_profit || 0).toLocaleString('en-IN');
            const soldDate = (b.sold_date || '').substring(0, 10);

            return `
              <div class="admin-soldout-card" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:1.15rem; box-shadow:0 1px 3px rgba(0,0,0,0.05); display:flex; flex-direction:column; justify-content:space-between; transition:all 0.2s;">
                <div>
                  <div style="position:relative; width:100%; height:180px; border-radius:8px; overflow:hidden; margin-bottom:0.85rem; background:#0F172A;">
                    <img src="${img}" alt="${b.title}" style="width:100%; height:100%; object-fit:cover;" onerror="this.src='/static/images/IMG-20251204-WA0053.jpg';">
                    <span style="position:absolute; top:8px; right:8px; background:#DC2626; color:#fff; font-size:0.72rem; font-weight:800; padding:3px 8px; border-radius:4px; letter-spacing:0.5px;">
                      <i class="fas fa-check-circle"></i> SOLD OUT
                    </span>
                  </div>

                  <div style="font-size:0.8rem; color:#64748B; font-weight:700; text-transform:uppercase;">${b.brand} &bull; ${b.model}</div>
                  <h4 style="font-size:1.05rem; font-weight:800; color:#0F172A; margin:3px 0 6px;">#${b.bike_id} - ${b.title}</h4>

                  <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:0.75rem;">
                    <span style="font-family:monospace; font-weight:700; font-size:0.75rem; background:#F1F5F9; color:#0F172A; padding:2px 6px; border-radius:4px;">${b.registration_number || 'TN-XX-XXXX'}</span>
                    <span style="font-size:0.75rem; color:#64748B; background:#F8FAFC; padding:2px 6px; border-radius:4px;"><i class="fas fa-calendar"></i> ${b.year}</span>
                    <span style="font-size:0.75rem; color:#64748B; background:#F8FAFC; padding:2px 6px; border-radius:4px;"><i class="fas fa-tachometer-alt"></i> ${(b.kilometers_driven||0).toLocaleString()} km</span>
                  </div>

                  <div style="font-size:0.8rem; color:#64748B; margin-bottom:0.5rem;">
                    <div><i class="fas fa-user-tag" style="color:#2563EB;"></i> Seller: <strong>${b.seller_name || 'Showroom'}</strong></div>
                    <div><i class="fas fa-calendar-check" style="color:#16A34A;"></i> Sold: <strong>${soldDate}</strong> by ${b.sold_by || 'admin'}</div>
                  </div>
                </div>

                <div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center; gap:8px;">
                  <div>
                    <div style="font-size:0.7rem; color:#64748B; text-transform:uppercase; font-weight:800;">Final Price</div>
                    <div style="font-size:1.2rem; font-weight:900; color:#0F172A;">₹${finalPrice}</div>
                    ${isSuper ? `<div style="font-size:0.75rem; color:#16A34A; font-weight:700;">Net Profit: ₹${profit}</div>` : ''}
                  </div>
                  <a href="/admin-sold-bike-details.html?id=${b.bike_id}" class="btn-table-action" style="background:#2563EB; color:#FFFFFF; font-weight:700; border-radius:6px; padding:7px 14px; text-decoration:none; display:inline-flex; align-items:center; gap:6px; box-shadow:0 2px 4px rgba(37,99,235,0.2);">
                    <i class="fas fa-eye"></i> View Details
                  </a>
                </div>
              </div>
            `;
          }).join('');
        }

        // Render Desktop Tabular View
        tbody.innerHTML = list.map(b => {
          const img = b.primary_image || (b.images && b.images[0]) || '/static/images/IMG-20251204-WA0053.jpg';
          const finalPrice = parseFloat(b.final_selling_price || 0).toLocaleString('en-IN');
          const profit = parseFloat(b.realized_profit || 0).toLocaleString('en-IN');
          const soldDate = (b.sold_date || '').substring(0, 16).replace('T', ' ');

          return `
            <tr>
              <td data-label="Motorcycle Details">
                <div class="table-bike-item">
                  <img src="${img}" class="table-bike-thumb" alt="${b.title}">
                  <div class="table-bike-info">
                    <span class="table-bike-title">#${b.bike_id} - ${b.title}</span>
                    <span class="table-bike-meta">Listed: ${(b.original_listing_date || '').substring(0, 10)}</span>
                  </div>
                </div>
              </td>
              <td data-label="Brand & Model"><strong>${b.brand}</strong> <span style="color:var(--admin-text-secondary);">${b.model}</span></td>
              <td data-label="Registration No."><span style="font-family:monospace; font-weight:700; background:#F1F5F9; padding:2px 6px; border-radius:4px;">${b.registration_number || 'TN-XX-XXXX'}</span></td>
              <td data-label="Specs">${b.year} &bull; ${(b.kilometers_driven || 0).toLocaleString()} km &bull; ${b.fuel_type || 'Petrol'}</td>
              <td data-label="Seller Info">
                <div>${b.seller_name || 'SMR Motors'}</div>
                <div style="font-size:0.75rem; color:var(--admin-text-secondary);">${b.seller_phone || ''}</div>
              </td>
              <td data-label="Sold Date & Time"><span style="font-size:0.82rem; color:var(--admin-text-secondary);">${soldDate}</span></td>
              <td data-label="Sold By"><strong>${b.sold_by || 'admin'}</strong></td>
              <td data-label="Final Price"><strong>₹${finalPrice}</strong></td>
              ${isSuper ? `
                <td data-label="Net Profit" class="fin-col-superadmin"><strong style="color:var(--admin-success);">₹${profit}</strong></td>
              ` : `
                <td class="fin-col-superadmin" style="display:none;">-</td>
              `}
              <td data-label="Status"><span class="badge-status badge-sold">SOLD OUT</span></td>
              <td data-label="Actions" style="text-align:right;">
                <div class="table-action-group">
                  <a href="/admin-sold-bike-details.html?id=${b.bike_id}" class="btn-table-action" style="background:#2563EB; color:#fff; text-decoration:none; display:inline-flex; align-items:center; gap:4px; font-weight:700; border-radius:6px; padding:6px 12px;" title="View Complete Historical Snapshot">
                    <i class="fas fa-eye"></i> View Details
                  </a>
                </div>
              </td>
            </tr>
          `;
        }).join('');

        renderPagination('soldout-bikes-pagination', 'soldout', res.pagination);"""

    if old_render_end in content:
        content = content.replace(old_render_end, new_render_end, 1)
        print("Updated loadSoldOutBikesView render loop with Cards and Table")
    else:
        print("old_render_end not found")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print("admin.html updated successfully with redesigned Admin Sold-Out page")

if __name__ == "__main__":
    update_admin_soldout_section()
