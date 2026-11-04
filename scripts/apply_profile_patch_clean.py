# -*- coding: utf-8 -*-
"""
Apply clean, precise updates to my-node-app/templates/profile.html.
"""
PROFILE_HTML = 'my-node-app/templates/profile.html'

with open(PROFILE_HTML, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Navbar to add Hamburger button
old_nav = '''  <!-- Top Navigation -->
  <header class="navbar">
    <div class="container">
      <a href="{{ url_for('index') }}" class="nav-brand">'''

new_nav = '''  <!-- Top Navigation -->
  <header class="navbar">
    <div class="container" style="display:flex; align-items:center; justify-content:space-between;">
      <div style="display:flex; align-items:center; gap:0.75rem;">
        <button class="user-sidebar-toggle-btn" id="userSidebarToggle" onclick="toggleUserSidebar()" aria-label="Toggle Navigation Menu">
          <i class="fas fa-bars"></i>
        </button>
        <a href="{{ url_for('index') }}" class="nav-brand">'''

content = content.replace(old_nav, new_nav, 1)

# 2. Add id and close button to user-sidebar
old_sidebar = '''  <div class="user-layout">
    <!-- Sidebar Navigation -->
    <aside class="user-sidebar">'''

new_sidebar = '''  <div class="user-layout">
    <!-- Sidebar Navigation Drawer -->
    <aside class="user-sidebar" id="userSidebar">
      <button class="user-sidebar-close-btn" onclick="toggleUserSidebar(false)" aria-label="Close Sidebar">
        <i class="fas fa-times"></i>
      </button>'''

content = content.replace(old_sidebar, new_sidebar, 1)

# 3. Add backdrop after </aside>
old_aside_close = '''      </div>
    </aside>

    <!-- Main Content Area -->'''

new_aside_close = '''      </div>
    </aside>
    <!-- Mobile Sidebar Backdrop -->
    <div class="user-sidebar-backdrop" id="userSidebarBackdrop" onclick="toggleUserSidebar(false)"></div>

    <!-- Main Content Area -->'''

content = content.replace(old_aside_close, new_aside_close, 1)

# 4. Enquiries table: responsive class and pagination
old_enq_block = '''        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Vehicle Enquired</th>
                  <th>Price</th>
                  <th>Message</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody id="my-enquiries-table-body">
                <tr><td colspan="5" style="text-align: center; padding: 3rem;"><i class="fas fa-spinner fa-spin"></i> Loading enquiries...</td></tr>
              </tbody>
            </table>
          </div>
        </div>'''

new_enq_block = '''        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table responsive-table-mobile">
              <thead>
                <tr>
                  <th>Vehicle Enquired</th>
                  <th>Price</th>
                  <th>Message</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody id="my-enquiries-table-body">
                <tr><td colspan="5" style="text-align: center; padding: 3rem;"><i class="fas fa-spinner fa-spin"></i> Loading enquiries...</td></tr>
              </tbody>
            </table>
          </div>
          <div id="my-enquiries-pagination" style="padding: 1rem 1.5rem;"></div>
        </div>'''

content = content.replace(old_enq_block, new_enq_block, 1)

# 5. Favorites pagination
old_fav_block = '''        <div id="favorites-grid" class="bike-grid">
          <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary);"></i>
          </div>
        </div>'''

new_fav_block = '''        <div id="favorites-grid" class="bike-grid">
          <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary);"></i>
          </div>
        </div>
        <div id="favorites-pagination" style="margin-top: 1.5rem;"></div>'''

content = content.replace(old_fav_block, new_fav_block, 1)

# 6. Negotiations pagination
old_neg_block = '''        <div id="user-negotiations-container" style="display: flex; flex-direction: column; gap: 1.5rem;">
          <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading offers...</div>
        </div>'''

new_neg_block = '''        <div id="user-negotiations-container" style="display: flex; flex-direction: column; gap: 1.5rem;">
          <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading offers...</div>
        </div>
        <div id="user-negotiations-pagination" style="margin-top: 1.5rem;"></div>'''

content = content.replace(old_neg_block, new_neg_block, 1)

# 7. Notifications pagination
old_notif_block = '''        <div class="table-card">
          <div id="user-notifications-list" style="display: flex; flex-direction: column;">
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>
          </div>
        </div>'''

new_notif_block = '''        <div class="table-card">
          <div id="user-notifications-list" style="display: flex; flex-direction: column;">
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>
          </div>
          <div id="user-notifications-pagination" style="padding: 1rem 1.5rem;"></div>
        </div>'''

content = content.replace(old_notif_block, new_notif_block, 1)

# 8. switchUserTab and pagination helpers
old_switch_tab = '''    function switchUserTab(tabId, el) {
      document.querySelectorAll('.user-tab-pane').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.user-nav-link').forEach(i => i.classList.remove('active'));
      const target = document.getElementById(tabId);
      if (target) target.classList.add('active');
      if (el) el.classList.add('active');

      if (tabId === 'user-tab-listings') loadUserListings();
      if (tabId === 'user-tab-add-bike') renderUserBikeImagePreviews();
      if (tabId === 'user-tab-negotiations') loadUserNegotiations();
      if (tabId === 'user-tab-enquiries') loadUserEnquiries();
      if (tabId === 'user-tab-favorites') loadFavorites();
      if (tabId === 'user-tab-notifications') loadUserNotifications();
      if (tabId === 'user-tab-messages') loadUserChat();
      else if (typeof pauseUserChatPolling === 'function') pauseUserChatPolling();
    }'''

new_switch_tab = '''    // Mobile Sidebar Drawer Toggle
    function toggleUserSidebar(forceState) {
      const sidebar = document.getElementById('userSidebar');
      const backdrop = document.getElementById('userSidebarBackdrop');
      if (!sidebar) return;
      const isOpen = (typeof forceState === 'boolean') ? forceState : !sidebar.classList.contains('open');
      if (isOpen) {
        sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('active');
        document.body.style.overflow = 'hidden';
      } else {
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
        document.body.style.overflow = '';
      }
    }

    // User Panel Pagination State
    const userPages = {
      listings: { page: 1, limit: 10 },
      enquiries: { page: 1, limit: 10 },
      negotiations: { page: 1, limit: 10 },
      favorites: { page: 1, limit: 10 },
      notifications: { page: 1, limit: 10 }
    };

    function changeUserPage(section, newPage) {
      if (!userPages[section]) userPages[section] = { page: 1, limit: 10 };
      userPages[section].page = Math.max(1, newPage);
      if (section === 'listings') loadUserListings(userPages.listings.page, currentUserListingFilter, userPages.listings.limit);
      else if (section === 'enquiries') loadUserEnquiries(userPages.enquiries.page, userPages.enquiries.limit);
      else if (section === 'negotiations') loadUserNegotiations(userPages.negotiations.page, userPages.negotiations.limit);
      else if (section === 'favorites') loadFavorites(userPages.favorites.page, userPages.favorites.limit);
      else if (section === 'notifications') loadUserNotifications(userPages.notifications.page, userPages.notifications.limit);
    }

    function changeUserLimit(section, newLimit) {
      newLimit = parseInt(newLimit, 10) || 10;
      if (!userPages[section]) userPages[section] = { page: 1, limit: 10 };
      userPages[section].limit = newLimit;
      userPages[section].page = 1;
      changeUserPage(section, 1);
    }

    function renderUserPagination(containerId, section, p) {
      const c = document.getElementById(containerId);
      if (!c) return;
      if (!p || p.total === 0) {
        c.innerHTML = '';
        return;
      }

      const curr = p.page || 1;
      const limit = p.limit || userPages[section]?.limit || 10;
      const total = p.total || 0;
      const totalPages = p.totalPages || p.total_pages || Math.ceil(total / limit) || 1;
      const start = (p.start !== undefined && p.start !== null) ? p.start : ((curr - 1) * limit + 1);
      const end = (p.end !== undefined && p.end !== null) ? p.end : Math.min(curr * limit, total);

      let pageButtons = [];
      const maxButtons = 5;
      let startPage = Math.max(1, curr - 2);
      let endPage = Math.min(totalPages, startPage + maxButtons - 1);
      if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
      }

      if (startPage > 1) {
        pageButtons.push(`<button type="button" class="user-btn-page" onclick="changeUserPage('${section}', 1)">1</button>`);
        if (startPage > 2) pageButtons.push(`<span class="user-page-ellipsis">&hellip;</span>`);
      }

      for (let i = startPage; i <= endPage; i++) {
        pageButtons.push(`
          <button type="button" class="user-btn-page ${i === curr ? 'active' : ''}" onclick="changeUserPage('${section}', ${i})" ${i === curr ? 'aria-current="page"' : ''}>
            ${i}
          </button>
        `);
      }

      if (endPage < totalPages) {
        if (endPage < totalPages - 1) pageButtons.push(`<span class="user-page-ellipsis">&hellip;</span>`);
        pageButtons.push(`<button type="button" class="user-btn-page" onclick="changeUserPage('${section}', ${totalPages})">${totalPages}</button>`);
      }

      c.innerHTML = `
        <div class="user-pagination-container">
          <div class="user-pagination-info">
            Showing <strong>${start}&ndash;${end}</strong> of <strong>${total}</strong> records
          </div>
          <div class="user-pagination-controls">
            <label class="user-pagination-limit-label" style="display:inline-flex; align-items:center; gap:6px; font-size:0.84rem; color:var(--text-secondary); margin-right:6px;">
              Rows:
              <select class="user-pagination-limit-select" onchange="changeUserLimit('${section}', this.value)">
                <option value="10" ${limit === 10 ? 'selected' : ''}>10</option>
                <option value="25" ${limit === 25 ? 'selected' : ''}>25</option>
                <option value="50" ${limit === 50 ? 'selected' : ''}>50</option>
              </select>
            </label>
            <button type="button" class="user-btn-page" ${curr <= 1 ? 'disabled' : ''} onclick="changeUserPage('${section}', ${curr - 1})" title="Previous Page">
              <i class="fas fa-chevron-left"></i>
            </button>
            <div class="user-pagination-pages" style="display:inline-flex; gap:4px;">
              ${pageButtons.join('')}
            </div>
            <button type="button" class="user-btn-page" ${curr >= totalPages ? 'disabled' : ''} onclick="changeUserPage('${section}', ${curr + 1})" title="Next Page">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
      `;
    }

    function switchUserTab(tabId, el) {
      document.querySelectorAll('.user-tab-pane').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.user-nav-link').forEach(i => i.classList.remove('active'));
      const target = document.getElementById(tabId);
      if (target) target.classList.add('active');
      if (el) el.classList.add('active');

      if (window.innerWidth <= 992) {
        toggleUserSidebar(false);
      }

      if (tabId === 'user-tab-listings') loadUserListings(userPages.listings.page, currentUserListingFilter, userPages.listings.limit);
      if (tabId === 'user-tab-add-bike') renderUserBikeImagePreviews();
      if (tabId === 'user-tab-negotiations') loadUserNegotiations(userPages.negotiations.page, userPages.negotiations.limit);
      if (tabId === 'user-tab-enquiries') loadUserEnquiries(userPages.enquiries.page, userPages.enquiries.limit);
      if (tabId === 'user-tab-favorites') loadFavorites(userPages.favorites.page, userPages.favorites.limit);
      if (tabId === 'user-tab-notifications') loadUserNotifications(userPages.notifications.page, userPages.notifications.limit);
      if (tabId === 'user-tab-messages') loadUserChat();
      else if (typeof pauseUserChatPolling === 'function') pauseUserChatPolling();
    }'''

content = content.replace(old_switch_tab, new_switch_tab, 1)

# 9. Update loadUserListings
old_listings_start = '''    async function loadUserListings(page = 1, status = currentUserListingFilter) {
      const tbody = document.getElementById('my-listings-table-body');
      try {
        const queryStatus = (status && status !== 'all') ? `&status=${encodeURIComponent(status)}` : '';
        const res = await apiRequest(`/api/users/listings?page=${page}&limit=6${queryStatus}`);'''

new_listings_start = '''    async function loadUserListings(page = 1, status = currentUserListingFilter, limit = null) {
      limit = limit || userPages.listings.limit || 10;
      const tbody = document.getElementById('my-listings-table-body');
      try {
        const queryStatus = (status && status !== 'all') ? `&status=${encodeURIComponent(status)}` : '';
        const res = await apiRequest(`/api/users/listings?page=${page}&limit=${limit}${queryStatus}`);'''

content = content.replace(old_listings_start, new_listings_start, 1)

old_listings_pagin = '''        // Render pagination
        const paginEl = document.getElementById('my-listings-pagination');
        if (paginEl && p.totalPages > 1) {
          paginEl.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
              <span style="font-size:0.85rem; color:var(--text-muted);">Page ${p.page} of ${p.totalPages} (${p.total} total)</span>
              <div style="display:flex; gap:0.35rem;">
                <button class="btn btn-sm btn-outline" onclick="loadUserListings(${p.page - 1}, currentUserListingFilter)" ${p.page <= 1 ? 'disabled' : ''}><i class="fas fa-chevron-left"></i> Prev</button>
                <button class="btn btn-sm btn-outline" onclick="loadUserListings(${p.page + 1}, currentUserListingFilter)" ${p.page >= p.totalPages ? 'disabled' : ''}>Next <i class="fas fa-chevron-right"></i></button>
              </div>
            </div>
          `;
        } else if (paginEl) {
          paginEl.innerHTML = '';
        }'''

new_listings_pagin = '''        // Render pagination
        renderUserPagination('my-listings-pagination', 'listings', res.pagination || p);'''

content = content.replace(old_listings_pagin, new_listings_pagin, 1)

# 10. filterUserListings resets page
content = content.replace("function filterUserListings(status, btn) {", "function filterUserListings(status, btn) {\n      userPages.listings.page = 1;")

# 11. loadUserNegotiations update
old_neg_call = '''    async function loadUserNegotiations() {
      const container = document.getElementById('user-negotiations-container');
      try {
        const res = await apiRequest('/api/users/negotiations');
        const negs = res.data || [];
        const badge = document.getElementById('user-badge-negotiations');
        const pendingCount = negs.filter(b => b.listing_status === 'price_offered').length;'''

new_neg_call = '''    async function loadUserNegotiations(page = 1, limit = null) {
      limit = limit || userPages.negotiations.limit || 10;
      const container = document.getElementById('user-negotiations-container');
      try {
        const res = await apiRequest(`/api/users/negotiations?page=${page}&limit=${limit}`);
        const negs = res.data || [];
        const badge = document.getElementById('user-badge-negotiations');
        const pendingCount = (res.pending_count !== undefined) ? res.pending_count : negs.filter(b => b.listing_status === 'price_offered').length;'''

content = content.replace(old_neg_call, new_neg_call, 1)

old_neg_empty = '''        if (negs.length === 0) {
          container.innerHTML = `
            <div class="empty-state">
              <i class="fas fa-handshake empty-state-icon"></i>
              <h3>No Active Price Negotiations</h3>
              <p>When SMR Motors reviews your listed bikes and proposes a payout offer, you will be able to review and accept it here.</p>
            </div>
          `;
          return;
        }'''

new_neg_empty = '''        if (negs.length === 0) {
          container.innerHTML = `
            <div class="empty-state">
              <i class="fas fa-handshake empty-state-icon"></i>
              <h3>No Active Price Negotiations</h3>
              <p>When SMR Motors reviews your listed bikes and proposes a payout offer, you will be able to review and accept it here.</p>
            </div>
          `;
          renderUserPagination('user-negotiations-pagination', 'negotiations', res.pagination);
          return;
        }'''

content = content.replace(old_neg_empty, new_neg_empty, 1)

old_neg_end = '''              ${actionContent}
            </div>
          `;
        }).join('');
      } catch (err) {'''

new_neg_end = '''              ${actionContent}
            </div>
          `;
        }).join('');

        renderUserPagination('user-negotiations-pagination', 'negotiations', res.pagination);
      } catch (err) {'''

content = content.replace(old_neg_end, new_neg_end, 1)

# 12. loadUserEnquiries update
old_enq_func = '''    async function loadUserEnquiries() {
      const tbody = document.getElementById('my-enquiries-table-body');
      try {
        const res = await apiRequest('/api/users/enquiries');
        const enquiries = res.data || [];
        if (enquiries.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem;">No enquiries yet.</td></tr>`;
          return;
        }
        tbody.innerHTML = enquiries.map(e => `
          <tr>
            <td style="font-weight:700;">${e.bike_title || 'General Motorcycle Inquiry'}</td>
            <td>${e.bike_price ? '₹'+Number(e.bike_price).toLocaleString('en-IN') : '-'}</td>
            <td>${e.message}</td>
            <td><span class="badge badge-${e.status==='completed'?'approved':'pending'}">${e.status}</span></td>
            <td>${new Date(e.created_at).toLocaleDateString()}</td>
          </tr>
        `).join('');
      } catch (err) {'''

new_enq_func = '''    async function loadUserEnquiries(page = 1, limit = null) {
      limit = limit || userPages.enquiries.limit || 10;
      const tbody = document.getElementById('my-enquiries-table-body');
      try {
        const res = await apiRequest(`/api/users/enquiries?page=${page}&limit=${limit}`);
        const enquiries = res.data || [];
        if (enquiries.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem;">No enquiries yet.</td></tr>`;
          renderUserPagination('my-enquiries-pagination', 'enquiries', res.pagination);
          return;
        }
        tbody.innerHTML = enquiries.map(e => `
          <tr>
            <td data-label="Vehicle Enquired" style="font-weight:700;">${e.bike_title || 'General Motorcycle Inquiry'}</td>
            <td data-label="Price">${e.bike_price ? '₹'+Number(e.bike_price).toLocaleString('en-IN') : '-'}</td>
            <td data-label="Message">${e.message || '-'}</td>
            <td data-label="Status"><span class="badge badge-${e.status==='completed'?'approved':'pending'}">${e.status}</span></td>
            <td data-label="Date">${new Date(e.created_at).toLocaleDateString()}</td>
          </tr>
        `).join('');

        renderUserPagination('my-enquiries-pagination', 'enquiries', res.pagination);
      } catch (err) {'''

content = content.replace(old_enq_func, new_enq_func, 1)

# 13. loadFavorites update
old_fav_func = '''    async function loadFavorites() {
      const grid = document.getElementById('favorites-grid');
      try {
        const res = await apiRequest('/api/users/favorites');
        const favs = res.data || [];
        if (favs.length === 0) {
          grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><h3>No saved favorites yet</h3></div>`;
          return;
        }
        grid.innerHTML = favs.map(bike => {
          let imgs = [];
          try { imgs = typeof bike.images === 'string' ? JSON.parse(bike.images) : (bike.images || []); } catch(e){}
          const cover = imgs[0] || '/static/images/IMG-20251204-WA0053.jpg';
          return `
            <div class="bike-card">
              <div class="bike-card-img-wrapper">
                <img src="${cover}" class="bike-card-img" />
              </div>
              <div class="bike-card-body">
                <div class="bike-card-brand">${bike.brand}</div>
                <h3 class="bike-card-title">${bike.title}</h3>
                <div class="bike-card-footer">
                  <span class="bike-price-value">₹${Number(bike.price).toLocaleString('en-IN')}</span>
                  <a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-primary">View</a>
                </div>
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {'''

new_fav_func = '''    async function loadFavorites(page = 1, limit = null) {
      limit = limit || userPages.favorites.limit || 10;
      const grid = document.getElementById('favorites-grid');
      try {
        const res = await apiRequest(`/api/users/favorites?page=${page}&limit=${limit}`);
        const favs = res.data || [];
        if (favs.length === 0) {
          grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><h3>No saved favorites yet</h3></div>`;
          renderUserPagination('favorites-pagination', 'favorites', res.pagination);
          return;
        }
        grid.innerHTML = favs.map(bike => {
          let imgs = [];
          try { imgs = typeof bike.images === 'string' ? JSON.parse(bike.images) : (bike.images || []); } catch(e){}
          const cover = imgs[0] || '/static/images/IMG-20251204-WA0053.jpg';
          return `
            <div class="bike-card">
              <div class="bike-card-img-wrapper">
                <img src="${cover}" class="bike-card-img" />
              </div>
              <div class="bike-card-body">
                <div class="bike-card-brand">${bike.brand}</div>
                <h3 class="bike-card-title">${bike.title}</h3>
                <div class="bike-card-footer">
                  <span class="bike-price-value">₹${Number(bike.price).toLocaleString('en-IN')}</span>
                  <a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-primary">View</a>
                </div>
              </div>
            </div>
          `;
        }).join('');

        renderUserPagination('favorites-pagination', 'favorites', res.pagination);
      } catch (err) {'''

content = content.replace(old_fav_func, new_fav_func, 1)

# 14. loadUserNotifications update
old_notif_func = '''    async function loadUserNotifications() {
      const container = document.getElementById('user-notifications-list');
      try {
        const res = await apiRequest('/api/notifications');
        const notifs = res.notifications || [];
        if (notifs.length === 0) {
          container.innerHTML = `<div style="text-align:center; padding: 3rem; color:var(--text-muted);">No notifications yet.</div>`;
          return;
        }
        container.innerHTML = notifs.map(n => `
          <div style="padding:1rem 1.5rem; border-bottom:1px solid var(--border-subtle); display:flex; gap:1rem; align-items:flex-start; background:${n.is_read?'transparent':'rgba(255,107,0,0.04)'};">
            <i class="fas fa-bell" style="color:var(--accent-primary); margin-top:0.25rem;"></i>
            <div style="flex:1;">
              <div style="font-weight:700; color:#FFF; font-size:0.95rem;">${n.title}</div>
              <div style="font-size:0.88rem; color:var(--text-secondary); margin-top:0.2rem;">${n.message}</div>
              <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.35rem;">${new Date(n.created_at).toLocaleString()}</div>
            </div>
          </div>
        `).join('');
      } catch (e) {'''

new_notif_func = '''    async function loadUserNotifications(page = 1, limit = null) {
      limit = limit || userPages.notifications.limit || 10;
      const container = document.getElementById('user-notifications-list');
      try {
        const res = await apiRequest(`/api/notifications?page=${page}&limit=${limit}`);
        const notifs = res.notifications || res.data || [];
        if (notifs.length === 0) {
          container.innerHTML = `<div style="text-align:center; padding: 3rem; color:var(--text-muted);">No notifications yet.</div>`;
          renderUserPagination('user-notifications-pagination', 'notifications', res.pagination);
          return;
        }
        container.innerHTML = notifs.map(n => `
          <div style="padding:1rem 1.5rem; border-bottom:1px solid var(--border-subtle); display:flex; gap:1rem; align-items:flex-start; background:${n.is_read?'transparent':'rgba(255,107,0,0.04)'};">
            <i class="fas fa-bell" style="color:var(--accent-primary); margin-top:0.25rem;"></i>
            <div style="flex:1;">
              <div style="font-weight:700; color:#FFF; font-size:0.95rem;">${n.title}</div>
              <div style="font-size:0.88rem; color:var(--text-secondary); margin-top:0.2rem;">${n.message}</div>
              <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.35rem;">${new Date(n.created_at).toLocaleString()}</div>
            </div>
          </div>
        `).join('');

        renderUserPagination('user-notifications-pagination', 'notifications', res.pagination);
      } catch (e) {'''

content = content.replace(old_notif_func, new_notif_func, 1)

with open(PROFILE_HTML, 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved profile.html successfully!")
