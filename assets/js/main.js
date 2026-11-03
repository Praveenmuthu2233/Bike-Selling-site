/**
 * SMR Motors - Main Application Interactions, Global Navigation & Profile State
 */

// Global Profile Navigation Handler
window.handleProfileNavigation = function(event) {
  if (event) event.preventDefault();
  const user = typeof AuthService !== 'undefined' ? AuthService.getUser() : null;
  const adminToken = localStorage.getItem('admin_token') || localStorage.getItem('adminToken');

  if (user) {
    window.location.href = '/profile.html';
  } else if (adminToken) {
    window.location.href = '/admin.html';
  } else {
    window.location.href = '/login.html';
  }
};

// Global User Profile Dropdown Toggle
window.toggleUserProfileDropdown = function(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  const wrapper = document.getElementById('userProfileDropdownWrap');
  const menu = document.getElementById('userProfileDropdownMenu');
  if (wrapper && menu) {
    const isShowing = menu.classList.contains('show');
    if (isShowing) {
      menu.classList.remove('show');
      wrapper.classList.remove('open');
    } else {
      menu.classList.add('show');
      wrapper.classList.add('open');
    }
  }
};

// Global click outside listener to close dropdowns
document.addEventListener('click', (e) => {
  const wrapper = document.getElementById('userProfileDropdownWrap');
  const menu = document.getElementById('userProfileDropdownMenu');
  if (wrapper && menu && !wrapper.contains(e.target)) {
    menu.classList.remove('show');
    wrapper.classList.remove('open');
  }
});

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Header scroll effect
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 20) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // 2. Mobile drawer setup
  const mobileBtn = document.querySelector('.mobile-menu-btn');
  const drawer = document.querySelector('.mobile-nav-drawer');
  const backdrop = document.querySelector('.mobile-nav-backdrop');

  if (mobileBtn && drawer && backdrop) {
    mobileBtn.addEventListener('click', () => {
      drawer.classList.add('open');
      backdrop.classList.add('open');
    });

    const closeBtn = drawer.querySelector('.drawer-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        drawer.classList.remove('open');
        backdrop.classList.remove('open');
      });
    }

    backdrop.addEventListener('click', () => {
      drawer.classList.remove('open');
      backdrop.classList.remove('open');
    });
  }

  // 3. User session header state & Redesigned User Profile Dropdown (Requirement 1 & 2)
  let user = null;
  if (typeof AuthService !== 'undefined') {
    user = await AuthService.verifySession();
  }

  const adminToken = localStorage.getItem('admin_token') || localStorage.getItem('adminToken');
  let adminUser = null;
  try {
    const adminStr = localStorage.getItem('admin_user') || localStorage.getItem('adminUser');
    if (adminStr) adminUser = JSON.parse(adminStr);
  } catch (e) {}

  const authNavSlots = document.querySelectorAll('.nav-auth-slot');
  authNavSlots.forEach(slot => {
    const isMobileSlot = slot.closest('.mobile-nav-drawer') || slot.classList.contains('mobile-nav-footer');

    if (user) {
      const userImg = user.profile_image || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80';
      const userName = user.name || 'Rider';
      const firstName = userName.split(' ')[0];
      const userEmail = user.email || '';

      if (isMobileSlot) {
        // Mobile Drawer Layout
        slot.innerHTML = `
          <div style="display:flex; flex-direction:column; gap:0.75rem; width:100%;">
            <a href="/profile.html" style="display:flex; align-items:center; gap:0.75rem; padding:0.65rem 0.85rem; background:rgba(255,255,255,0.05); border-radius:12px; border:1px solid rgba(255,255,255,0.1); text-decoration:none;">
              <img src="${userImg}" style="width:38px; height:38px; border-radius:50%; object-fit:cover; border:1.5px solid var(--accent-primary);" alt="${userName}">
              <div style="display:flex; flex-direction:column; overflow:hidden;">
                <span style="font-weight:700; color:#fff; font-size:0.9rem;">${userName}</span>
                <span style="font-size:0.75rem; color:var(--text-muted);">${userEmail}</span>
              </div>
            </a>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">
              <a href="/profile.html" class="btn btn-sm btn-secondary" style="justify-content:center; text-decoration:none;"><i class="fas fa-gauge-high"></i> Dashboard</a>
              <a href="/bikeSelling.html" class="btn btn-sm btn-primary" style="justify-content:center; text-decoration:none;"><i class="fas fa-plus"></i> Sell Bike</a>
            </div>
            <button onclick="AuthService.logout()" class="btn btn-sm btn-outline" style="width:100%; justify-content:center; color:#F87171; border-color:rgba(239,68,68,0.3);"><i class="fas fa-arrow-right-from-bracket"></i> Logout</button>
          </div>
        `;
      } else {
        // Desktop Top Navbar Dropdown
        slot.innerHTML = `
          <div style="display:flex; align-items:center; gap:0.75rem;">
            <div class="user-profile-dropdown-wrapper" id="userProfileDropdownWrap">
              <button type="button" class="user-profile-trigger" onclick="toggleUserProfileDropdown(event)" aria-label="User Profile Menu">
                <img src="${userImg}" class="trigger-avatar" alt="${userName}">
                <span class="trigger-name">${firstName}</span>
                <i class="fas fa-chevron-down trigger-chevron"></i>
              </button>

              <div class="user-profile-dropdown-menu" id="userProfileDropdownMenu">
                <div class="dropdown-user-header">
                  <img src="${userImg}" class="dropdown-user-avatar" alt="${userName}">
                  <div class="dropdown-user-details">
                    <span class="dropdown-user-name">${userName}</span>
                    <span class="dropdown-user-email">${userEmail}</span>
                  </div>
                </div>

                <div class="dropdown-menu-list">
                  <a href="/profile.html" class="dropdown-item-link">
                    <i class="fas fa-gauge-high"></i>
                    <span>My Dashboard</span>
                  </a>
                  <a href="/profile.html?tab=listings" class="dropdown-item-link">
                    <i class="fas fa-motorcycle"></i>
                    <span>My Bike Listings</span>
                  </a>
                  <a href="/profile.html?tab=enquiries" class="dropdown-item-link">
                    <i class="fas fa-envelope-open-text"></i>
                    <span>My Enquiries</span>
                  </a>
                  <a href="/profile.html?tab=favorites" class="dropdown-item-link">
                    <i class="fas fa-heart"></i>
                    <span>My Favorites</span>
                  </a>
                  <a href="/profile.html?tab=profile" class="dropdown-item-link">
                    <i class="fas fa-user-pen"></i>
                    <span>Edit Profile</span>
                  </a>

                  ${adminToken ? `
                    <div class="dropdown-divider"></div>
                    <a href="/admin.html" class="dropdown-item-link" style="color:var(--accent-primary);">
                      <i class="fas fa-shield-alt"></i>
                      <span>Admin Console (${adminUser ? adminUser.role : 'Manager'})</span>
                    </a>
                  ` : ''}

                  <div class="dropdown-divider"></div>
                  <button type="button" onclick="AuthService.logout()" class="dropdown-item-link logout-item">
                    <i class="fas fa-arrow-right-from-bracket"></i>
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            </div>

            <a href="/bikeSelling.html" class="btn btn-sm btn-primary">
              <i class="fas fa-plus"></i> Sell Bike
            </a>
          </div>
        `;
      }
    } else if (adminToken && !isMobileSlot) {
      // If admin only is logged in
      const admName = adminUser ? (adminUser.full_name || adminUser.username) : 'Admin';
      slot.innerHTML = `
        <div style="display:flex; align-items:center; gap:0.75rem;">
          <a href="/admin.html" class="btn btn-sm btn-outline" style="border-color:var(--accent-primary); color:var(--accent-primary);">
            <i class="fas fa-shield-alt"></i> ${admName} Console
          </a>
          <a href="/login.html" class="btn btn-sm btn-secondary">User Sign In</a>
          <a href="/bikeSelling.html" class="btn btn-sm btn-primary"><i class="fas fa-plus"></i> Sell Bike</a>
        </div>
      `;
    } else {
      // Logged Out State
      slot.innerHTML = `
        <a href="/login.html" class="btn btn-sm btn-outline"><i class="fas fa-user"></i> Sign In</a>
        <a href="/bikeSelling.html" class="btn btn-sm btn-primary"><i class="fas fa-plus"></i> Sell Bike</a>
      `;
    }
  });

  // Also bind all profile/dashboard links in navbar & footer to use handleProfileNavigation if logged out
  document.querySelectorAll('a[href*="profile.html"], a[href*="user_profile"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const activeUser = typeof AuthService !== 'undefined' ? AuthService.getUser() : null;
      if (!activeUser && !localStorage.getItem('token') && !sessionStorage.getItem('token')) {
        e.preventDefault();
        window.location.href = '/login.html';
      }
    });
  });

  // 4. Dynamic Business Hours & Showroom Status (Asia/Kolkata Timezone)
  function updateBusinessHoursStatus() {
    const now = new Date();
    // Convert to IST (UTC + 5.5 hours)
    const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
    const istDate = new Date(utcMs + (5.5 * 3600000));
    const currentMins = istDate.getHours() * 60 + istDate.getMinutes();
    const openMins = 9 * 60 + 30;   // 9:30 AM
    const closeMins = 20 * 60 + 30; // 8:30 PM

    const isOpen = currentMins >= openMins && currentMins < closeMins;
    const timeStr = istDate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });

    document.querySelectorAll('.live-business-hours-badge, .business-status-badge').forEach(el => {
      if (isOpen) {
        el.innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,0.15);color:#10B981;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:700;"><span style="width:7px;height:7px;border-radius:50%;background:#10B981;display:inline-block;box-shadow:0 0 8px #10B981;"></span> Showroom Open • Closes 8:30 PM IST (${timeStr})</span>`;
      } else {
        el.innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(239,68,68,0.15);color:#EF4444;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:700;"><span style="width:7px;height:7px;border-radius:50%;background:#EF4444;display:inline-block;"></span> Showroom Closed • Opens 9:30 AM IST (${timeStr})</span>`;
      }
    });
  }
  updateBusinessHoursStatus();
  setInterval(updateBusinessHoursStatus, 60000);

  // 5. Contact form submission handler if on contact page
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

      const formData = new FormData(contactForm);
      const payload = {
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        message: formData.get('message')
      };

      try {
        const res = await apiRequest('/api/contact', {
          method: 'POST',
          body: payload
        });
        showToast(res.message || 'Your message was sent successfully!', 'success');
        contactForm.reset();
      } catch (err) {
        showToast(err.message || 'Failed to send message', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }
});
