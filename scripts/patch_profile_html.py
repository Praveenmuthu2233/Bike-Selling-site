# -*- coding: utf-8 -*-
"""
Patch User Panel (profile.html) with responsive navigation drawer and server-side pagination.
"""
import os
import re

PROFILE_HTML = 'my-node-app/templates/profile.html'

def patch_profile():
    print(f"Reading {PROFILE_HTML}...")
    with open(PROFILE_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add toggle button in Navbar
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

    if old_nav in content:
        content = content.replace(old_nav, new_nav, 1)
        print("Updated navbar in profile.html.")
    else:
        old_nav_crlf = old_nav.replace('\n', '\r\n')
        new_nav_crlf = new_nav.replace('\n', '\r\n')
        if old_nav_crlf in content:
            content = content.replace(old_nav_crlf, new_nav_crlf, 1)
            print("Updated navbar in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_nav")

    # 2. Add id and close button to user-sidebar + backdrop
    old_sidebar = '''  <div class="user-layout">
    <!-- Sidebar Navigation -->
    <aside class="user-sidebar">'''

    new_sidebar = '''  <div class="user-layout">
    <!-- Sidebar Navigation Drawer -->
    <aside class="user-sidebar" id="userSidebar">
      <button class="user-sidebar-close-btn" onclick="toggleUserSidebar(false)" aria-label="Close Sidebar">
        <i class="fas fa-times"></i>
      </button>'''

    if old_sidebar in content:
        content = content.replace(old_sidebar, new_sidebar, 1)
        print("Updated sidebar start in profile.html.")
    else:
        old_sidebar_crlf = old_sidebar.replace('\n', '\r\n')
        new_sidebar_crlf = new_sidebar.replace('\n', '\r\n')
        if old_sidebar_crlf in content:
            content = content.replace(old_sidebar_crlf, new_sidebar_crlf, 1)
            print("Updated sidebar start in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_sidebar")

    # 3. Add backdrop after </aside>
    old_aside_close = '''      </div>
    </aside>

    <!-- Main Content Area -->'''

    new_aside_close = '''      </div>
    </aside>
    <!-- Mobile Sidebar Backdrop -->
    <div class="user-sidebar-backdrop" id="userSidebarBackdrop" onclick="toggleUserSidebar(false)"></div>

    <!-- Main Content Area -->'''

    if old_aside_close in content:
        content = content.replace(old_aside_close, new_aside_close, 1)
        print("Added user-sidebar-backdrop in profile.html.")
    else:
        old_aside_close_crlf = old_aside_close.replace('\n', '\r\n')
        new_aside_close_crlf = new_aside_close.replace('\n', '\r\n')
        if old_aside_close_crlf in content:
            content = content.replace(old_aside_close_crlf, new_aside_close_crlf, 1)
            print("Added user-sidebar-backdrop in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_aside_close")

    # 4. Enquiries pagination & responsive table
    old_enq_table = '''        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table">'''

    new_enq_table = '''        <div class="table-card">
          <div class="table-responsive">
            <table class="data-table responsive-table-mobile">'''

    if old_enq_table in content:
        content = content.replace(old_enq_table, new_enq_table, 1)
        print("Updated enquiries table class in profile.html.")
    else:
        old_enq_table_crlf = old_enq_table.replace('\n', '\r\n')
        new_enq_table_crlf = new_enq_table.replace('\n', '\r\n')
        if old_enq_table_crlf in content:
            content = content.replace(old_enq_table_crlf, new_enq_table_crlf, 1)
            print("Updated enquiries table class in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_enq_table")

    old_enq_close = '''              <tbody id="my-enquiries-table-body">
                <tr><td colspan="5" style="text-align: center; padding: 3rem;"><i class="fas fa-spinner fa-spin"></i> Loading enquiries...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>'''

    new_enq_close = '''              <tbody id="my-enquiries-table-body">
                <tr><td colspan="5" style="text-align: center; padding: 3rem;"><i class="fas fa-spinner fa-spin"></i> Loading enquiries...</td></tr>
              </tbody>
            </table>
          </div>
          <div id="my-enquiries-pagination" style="padding: 1rem 1.5rem;"></div>
        </div>
      </div>'''

    if old_enq_close in content:
        content = content.replace(old_enq_close, new_enq_close, 1)
        print("Added #my-enquiries-pagination in profile.html.")
    else:
        old_enq_close_crlf = old_enq_close.replace('\n', '\r\n')
        new_enq_close_crlf = new_enq_close.replace('\n', '\r\n')
        if old_enq_close_crlf in content:
            content = content.replace(old_enq_close_crlf, new_enq_close_crlf, 1)
            print("Added #my-enquiries-pagination in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_enq_close")

    # 5. Favorites pagination
    old_fav_close = '''        <div id="favorites-grid" class="bike-grid">
          <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary);"></i>
          </div>
        </div>
      </div>'''

    new_fav_close = '''        <div id="favorites-grid" class="bike-grid">
          <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary);"></i>
          </div>
        </div>
        <div id="favorites-pagination" style="margin-top: 1.5rem;"></div>
      </div>'''

    if old_fav_close in content:
        content = content.replace(old_fav_close, new_fav_close, 1)
        print("Added #favorites-pagination in profile.html.")
    else:
        old_fav_close_crlf = old_fav_close.replace('\n', '\r\n')
        new_fav_close_crlf = new_fav_close.replace('\n', '\r\n')
        if old_fav_close_crlf in content:
            content = content.replace(old_fav_close_crlf, new_fav_close_crlf, 1)
            print("Added #favorites-pagination in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_fav_close")

    # 6. Negotiations pagination
    old_neg_close = '''        <div id="user-negotiations-container" style="display: flex; flex-direction: column; gap: 1.5rem;">
          <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading offers...</div>
        </div>
      </div>'''

    new_neg_close = '''        <div id="user-negotiations-container" style="display: flex; flex-direction: column; gap: 1.5rem;">
          <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading offers...</div>
        </div>
        <div id="user-negotiations-pagination" style="margin-top: 1.5rem;"></div>
      </div>'''

    if old_neg_close in content:
        content = content.replace(old_neg_close, new_neg_close, 1)
        print("Added #user-negotiations-pagination in profile.html.")
    else:
        old_neg_close_crlf = old_neg_close.replace('\n', '\r\n')
        new_neg_close_crlf = new_neg_close.replace('\n', '\r\n')
        if old_neg_close_crlf in content:
            content = content.replace(old_neg_close_crlf, new_neg_close_crlf, 1)
            print("Added #user-negotiations-pagination in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_neg_close")

    # 7. Notifications pagination
    old_notif_close = '''        <div class="table-card">
          <div id="user-notifications-list" style="display: flex; flex-direction: column;">
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>
          </div>
        </div>'''

    new_notif_close = '''        <div class="table-card">
          <div id="user-notifications-list" style="display: flex; flex-direction: column;">
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>
          </div>
          <div id="user-notifications-pagination" style="padding: 1rem 1.5rem;"></div>
        </div>'''

    if old_notif_close in content:
        content = content.replace(old_notif_close, new_notif_close, 1)
        print("Added #user-notifications-pagination in profile.html.")
    else:
        old_notif_close_crlf = old_notif_close.replace('\n', '\r\n')
        new_notif_close_crlf = new_notif_close.replace('\n', '\r\n')
        if old_notif_close_crlf in content:
            content = content.replace(old_notif_close_crlf, new_notif_close_crlf, 1)
            print("Added #user-notifications-pagination in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_notif_close")

    # 8. Add JavaScript helpers: toggleUserSidebar, userPages, changeUserPage, changeUserLimit, renderUserPagination
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

    if old_switch_tab in content:
        content = content.replace(old_switch_tab, new_switch_tab, 1)
        print("Updated switchUserTab and pagination helpers in profile.html.")
    else:
        old_switch_tab_crlf = old_switch_tab.replace('\n', '\r\n')
        new_switch_tab_crlf = new_switch_tab.replace('\n', '\r\n')
        if old_switch_tab_crlf in content:
            content = content.replace(old_switch_tab_crlf, new_switch_tab_crlf, 1)
            print("Updated switchUserTab and pagination helpers in profile.html (CRLF).")
        else:
            print("WARNING: Could not match old_switch_tab")

    # 9. Update loadUserListings
    old_listings_pattern = r'async function loadUserListings\(page = 1, status = currentUserListingFilter\)\s*\{[\s\S]*?// Render pagination[\s\S]*?else if \(paginEl\) \{\s*paginEl\.innerHTML = \'\';\s*\}\s*\}\s*catch\s*\(err\)\s*\{'
    new_listings_snippet = '''async function loadUserListings(page = 1, status = currentUserListingFilter, limit = null) {
      limit = limit || userPages.listings.limit || 10;
      const tbody = document.getElementById('my-listings-table-body');
      try {
        const queryStatus = (status && status !== 'all') ? `&status=${encodeURIComponent(status)}` : '';
        const res = await apiRequest(`/api/users/listings?page=${page}&limit=${limit}${queryStatus}`);
        const listings = res.data || [];
        const p = res.pagination || { total: listings.length, page: page, limit: limit, totalPages: 1 };
        if (listings.length === 0) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2.5rem; color:var(--text-muted);">You have not listed any motorcycles yet. <button onclick="switchUserTab('user-tab-add-bike', document.querySelectorAll('.user-nav-link')[2])" class="btn btn-sm btn-primary" style="margin-left:0.5rem;">List a Bike Now</button></td></tr>`;
          renderUserPagination('my-listings-pagination', 'listings', p);
          return;
        }
        tbody.innerHTML = listings.map(bike => {
          const st = (bike.listing_status || bike.status || 'pending').toLowerCase();
          let badgeClass = 'badge-pending';
          let statusText = 'Pending Approval';
          if (st === 'approved' || st === 'published') {
            badgeClass = 'badge-approved';
            statusText = 'Approved & Live';
          } else if (st === 'price_offered') {
            badgeClass = 'badge-featured';
            statusText = 'Offer Received';
          } else if (st === 'seller_accepted') {
            badgeClass = 'badge-approved';
            statusText = 'Offer Accepted';
          } else if (st === 'rejected' || st === 'seller_rejected') {
            badgeClass = 'badge-rejected';
            statusText = 'Listing Rejected';
          } else if (st === 'soldout') {
            badgeClass = 'badge-soldout';
            statusText = 'Sold Out';
          }

          let coverThumb = '/static/images/IMG-20251204-WA0053.jpg';
          if (Array.isArray(bike.images) && bike.images.length > 0) {
            coverThumb = bike.images[0];
          }

          let rejectionBanner = '';
          if (st === 'rejected' && bike.rejection_reason) {
            rejectionBanner = `
              <div style="margin-top:0.45rem; padding:0.5rem 0.75rem; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:6px; font-size:0.8rem; color:#FCA5A5;">
                <i class="fas fa-exclamation-triangle" style="color:#EF4444; margin-right:4px;"></i>
                <strong>Admin Rejection Reason:</strong> ${bike.rejection_reason}
              </div>
            `;
          }

          return `
            <tr>
              <td data-label="Vehicle">
                <div style="display:flex; align-items:center; gap:0.75rem;">
                  <img src="${coverThumb}" style="width:48px; height:48px; border-radius:6px; object-fit:cover; border:1px solid var(--border-subtle); flex-shrink:0;" onerror="this.src='/static/images/IMG-20251204-WA0053.jpg';" />
                  <div>
                    <div style="font-weight:700; color:#FFF;">${bike.year} ${bike.title}</div>
                    <div style="font-size:0.78rem; color:var(--text-muted);"><i class="fas fa-map-marker-alt"></i> ${bike.location || 'Salem, TN'}</div>
                    ${rejectionBanner}
                  </div>
                </div>
              </td>
              <td data-label="Brand & Model">${bike.brand} • ${bike.model}</td>
              <td data-label="Expected Price" style="color:var(--accent-primary); font-weight:800;">₹${Number(bike.price).toLocaleString('en-IN')}</td>
              <td data-label="Kilometers">${(bike.kilometers_driven||0).toLocaleString()} km</td>
              <td data-label="Review Status"><span class="badge ${badgeClass}">${statusText}</span></td>
              <td data-label="Action">
                <div style="display:flex; gap:0.4rem; justify-content:flex-end;">
                  ${st === 'approved' || st === 'published' ? `
                    <a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline" target="_blank" title="View Showroom Listing"><i class="fas fa-eye"></i></a>
                  ` : ''}
                  <button onclick="deleteMyBike(${bike.id})" class="btn btn-sm btn-danger" title="Delete Listing"><i class="fas fa-trash"></i></button>
                </div>
              </td>
            </tr>
          `;
        }).join('');

        renderUserPagination('my-listings-pagination', 'listings', res.pagination);
      } catch (err) {'''
    match = re.search(old_listings_pattern, content)
    if match:
        content = content[:match.start()] + new_listings_snippet + content[match.end():]
        print("Updated loadUserListings in profile.html.")
    else:
        print("WARNING: Could not match old_listings_pattern")

    # 10. Update filterUserListings to reset page to 1
    content = content.replace("function filterUserListings(status, btn) {", "function filterUserListings(status, btn) {\n      userPages.listings.page = 1;")

    # 11. Update loadUserNegotiations to support page, limit, and pagination
    old_neg_func_pattern = r'async function loadUserNegotiations\(\)\s*\{[\s\S]*?const res = await apiRequest\(\'/api/users/negotiations\'\);[\s\S]*?container\.innerHTML = negs\.map\([\s\S]*?\)\.join\(\'\'\);\s*\}\s*catch\s*\(e\)\s*\{'
    new_neg_func_snippet = '''async function loadUserNegotiations(page = 1, limit = null) {
      limit = limit || userPages.negotiations.limit || 10;
      const container = document.getElementById('user-negotiations-container');
      try {
        const res = await apiRequest(`/api/users/negotiations?page=${page}&limit=${limit}`);
        const negs = res.data || [];
        const badge = document.getElementById('user-badge-negotiations');
        const pendingCount = (res.pending_count !== undefined) ? res.pending_count : negs.filter(b => b.listing_status === 'price_offered').length;
        if (badge) {
          badge.innerText = pendingCount;
          badge.style.display = pendingCount > 0 ? 'inline-block' : 'none';
        }

        if (negs.length === 0) {
          container.innerHTML = `
            <div class="empty-state">
              <i class="fas fa-handshake empty-state-icon"></i>
              <h3>No Active Price Negotiations</h3>
              <p>When SMR Motors reviews your listed bikes and proposes a payout offer, you will be able to review and accept it here.</p>
            </div>
          `;
          renderUserPagination('user-negotiations-pagination', 'negotiations', res.pagination);
          return;
        }

        container.innerHTML = negs.map(b => {
          const st = b.listing_status;
          const reqPrice = Number(b.requested_price || b.price);
          const proposed = Number(b.proposed_seller_payout || b.price);
          let actionContent = '';

          if (st === 'price_offered') {
            actionContent = `
              <div style="background:rgba(255,107,0,0.06); border:1px solid rgba(255,107,0,0.25); border-radius:8px; padding:1.25rem; margin-top:1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
                  <div>
                    <div style="font-size:0.85rem; color:var(--text-muted);">SMR Valuation Counteroffer:</div>
                    <div style="font-size:1.75rem; font-weight:800; color:var(--accent-primary);">₹${proposed.toLocaleString('en-IN')}</div>
                    ${b.admin_negotiation_notes ? `<div style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.35rem;"><i class="fas fa-comment-dots"></i> "${b.admin_negotiation_notes}"</div>` : ''}
                  </div>
                  <div style="display:flex; gap:0.75rem;">
                    <button class="btn btn-sm btn-primary" onclick="respondNegotiation(${b.id}, 'accept')"><i class="fas fa-check"></i> Accept Deal</button>
                    <button class="btn btn-sm btn-outline" onclick="respondNegotiation(${b.id}, 'reject')"><i class="fas fa-times"></i> Decline</button>
                  </div>
                </div>
              </div>
            `;
          } else if (st === 'seller_accepted') {
            actionContent = `
              <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:1rem; margin-top:1rem; display:flex; align-items:center; gap:0.75rem; color:#6EE7B7;">
                <i class="fas fa-check-circle" style="font-size:1.35rem; color:#10B981;"></i>
                <div>
                  <strong>Deal Finalized!</strong> You accepted ₹${proposed.toLocaleString('en-IN')}. SMR Motors inventory team is preparing showroom display and payout paperwork.
                </div>
              </div>
            `;
          } else if (st === 'seller_rejected') {
            actionContent = `
              <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:1rem; margin-top:1rem; display:flex; align-items:center; gap:0.75rem; color:#FCA5A5;">
                <i class="fas fa-ban" style="font-size:1.35rem; color:#EF4444;"></i>
                <div>
                  <strong>Offer Declined:</strong> You chose not to proceed with the payout counteroffer of ₹${proposed.toLocaleString('en-IN')}.
                </div>
              </div>
            `;
          }

          let thumb = '/static/images/IMG-20251204-WA0053.jpg';
          if (Array.isArray(b.images) && b.images.length > 0) thumb = b.images[0];

          return `
            <div class="card" style="padding:1.5rem; border:1px solid var(--border-subtle); background:var(--bg-surface); border-radius:12px;">
              <div style="display:flex; gap:1.25rem; align-items:flex-start; flex-wrap:wrap;">
                <img src="${thumb}" style="width:96px; height:72px; object-fit:cover; border-radius:8px; border:1px solid var(--border-subtle);" onerror="this.src='/static/images/IMG-20251204-WA0053.jpg';" />
                <div style="flex:1; min-width:220px;">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                      <h3 style="margin:0 0 0.25rem; font-size:1.15rem; color:#FFF;">${b.year} ${b.title}</h3>
                      <div style="font-size:0.84rem; color:var(--text-muted);">${b.brand} • ${b.model} • ${(b.kilometers_driven||0).toLocaleString()} km</div>
                    </div>
                    <div style="text-align:right;">
                      <div style="font-size:0.75rem; color:var(--text-muted);">Your Asking Price</div>
                      <div style="font-size:1.1rem; font-weight:700; color:#FFF;">₹${reqPrice.toLocaleString('en-IN')}</div>
                    </div>
                  </div>
                  ${actionContent}
                </div>
              </div>
            </div>
          `;
        }).join('');

        renderUserPagination('user-negotiations-pagination', 'negotiations', res.pagination);
      } catch (e) {'''

    match = re.search(old_neg_func_pattern, content)
    if match:
        content = content[:match.start()] + new_neg_func_snippet + content[match.end():]
        print("Updated loadUserNegotiations in profile.html.")
    else:
        print("WARNING: Could not match old_neg_func_pattern")

    # 12. Update loadUserEnquiries to support page, limit, pagination, and data-labels
    old_enq_func_pattern = r'async function loadUserEnquiries\(\)\s*\{[\s\S]*?const res = await apiRequest\(\'/api/users/enquiries\'\);[\s\S]*?tbody\.innerHTML = enquiries\.map\([\s\S]*?\)\.join\(\'\'\);\s*\}\s*catch\s*\(err\)\s*\{'
    new_enq_func_snippet = '''async function loadUserEnquiries(page = 1, limit = null) {
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

    match = re.search(old_enq_func_pattern, content)
    if match:
        content = content[:match.start()] + new_enq_func_snippet + content[match.end():]
        print("Updated loadUserEnquiries in profile.html.")
    else:
        print("WARNING: Could not match old_enq_func_pattern")

    # 13. Update loadFavorites to support page, limit, and pagination
    old_fav_func_pattern = r'async function loadFavorites\(\)\s*\{[\s\S]*?const res = await apiRequest\(\'/api/users/favorites\'\);[\s\S]*?grid\.innerHTML = favs\.map\([\s\S]*?\)\.join\(\'\'\);\s*\}\s*catch\s*\(err\)\s*\{'
    new_fav_func_snippet = '''async function loadFavorites(page = 1, limit = null) {
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

    match = re.search(old_fav_func_pattern, content)
    if match:
        content = content[:match.start()] + new_fav_func_snippet + content[match.end():]
        print("Updated loadFavorites in profile.html.")
    else:
        print("WARNING: Could not match old_fav_func_pattern")

    # 14. Update loadUserNotifications to support page, limit, and pagination
    old_notif_func_pattern = r'async function loadUserNotifications\(\)\s*\{[\s\S]*?const res = await apiRequest\(\'/api/notifications\'\);[\s\S]*?container\.innerHTML = notifs\.map\([\s\S]*?\)\.join\(\'\'\);\s*\}\s*catch\s*\(e\)\s*\{'
    new_notif_func_snippet = '''async function loadUserNotifications(page = 1, limit = null) {
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

    match = re.search(old_notif_func_pattern, content)
    if match:
        content = content[:match.start()] + new_notif_func_snippet + content[match.end():]
        print("Updated loadUserNotifications in profile.html.")
    else:
        print("WARNING: Could not match old_notif_func_pattern")

    with open(PROFILE_HTML, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Saved profile.html.")

patch_profile()
