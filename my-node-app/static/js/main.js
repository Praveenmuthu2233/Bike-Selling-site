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

  // 4. Contact form submission handler if on contact page
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
