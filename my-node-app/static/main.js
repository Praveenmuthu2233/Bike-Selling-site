/**
 * SMR Motors - Main Application Interactions & UI Utilities
 */

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

  // 3. User session header state
  const user = await AuthService.verifySession();
  const authNavSlots = document.querySelectorAll('.nav-auth-slot');
  authNavSlots.forEach(slot => {
    if (user) {
      slot.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.75rem;">
          <a href="/user/dashboard.html" class="btn btn-sm btn-secondary" style="border-radius: var(--radius-full); padding: 0.35rem 0.85rem; display:flex; align-items:center; gap:0.5rem;">
            <img src="${user.profile_image || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=80&q=80'}" style="width:24px;height:24px;border-radius:50%;object-fit:cover;" />
            <span>${user.name.split(' ')[0]}</span>
          </a>
          <button onclick="AuthService.logout()" class="btn btn-sm btn-outline" title="Sign out" style="padding:0.35rem 0.65rem;">
            <i class="fas fa-sign-out-alt"></i>
          </button>
        </div>
      `;
    } else {
      slot.innerHTML = `
        <a href="/login.html" class="btn btn-sm btn-outline"><i class="fas fa-user"></i> Sign In</a>
        <a href="/sell-bike.html" class="btn btn-sm btn-primary"><i class="fas fa-plus"></i> Sell Bike</a>
      `;
    }
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
