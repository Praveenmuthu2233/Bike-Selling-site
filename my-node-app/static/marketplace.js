/**
 * SMR Motors - Marketplace Vehicle Inventory Loader & Filters
 */

let allBikes = [];
let currentBikeForEnquiry = null;

async function loadMarketplaceBikes() {
  const container = document.getElementById('marketplace-bikes-grid');
  if (!container) return;

  container.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 3rem 0;">
      <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary);"></i>
      <p style="margin-top: 1rem; color: var(--text-secondary);">Loading verified motorcycle inventory...</p>
    </div>
  `;

  try {
    const res = await apiRequest('/api/bikes');
    allBikes = res.data || [];
    renderBikes(allBikes);
    populateBrandFilter(allBikes);
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <i class="fas fa-exclamation-triangle empty-state-icon"></i>
        <h3>Unable to load motorcycles</h3>
        <p>${err.message}</p>
        <button onclick="loadMarketplaceBikes()" class="btn btn-primary" style="margin-top: 1rem;">Try Again</button>
      </div>
    `;
  }
}

function renderBikes(bikes) {
  const container = document.getElementById('marketplace-bikes-grid');
  if (!container) return;

  if (!bikes || bikes.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <i class="fas fa-motorcycle empty-state-icon"></i>
        <h3>No motorcycles found</h3>
        <p>Try adjusting your search criteria or price filters.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = bikes.map(bike => {
    let images = [];
    try {
      images = typeof bike.images === 'string' ? JSON.parse(bike.images) : (bike.images || []);
    } catch (e) {
      images = [];
    }
    const coverImage = (images && images.length > 0) 
      ? images[0] 
      : 'https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=600&q=80';

    const formattedPrice = Number(bike.price).toLocaleString('en-IN');
    const isSold = (bike.status === 'soldout' || bike.status === 'sold');

    return `
      <div class="bike-card">
        <div class="bike-card-img-wrapper">
          <img src="${coverImage}" alt="${bike.title}" class="bike-card-img" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=600&q=80';" />
          <div class="bike-card-badge">
            ${isSold 
              ? '<span class="badge badge-soldout">Sold Out</span>'
              : (bike.featured ? '<span class="badge badge-featured"><i class="fas fa-star"></i> Featured</span>' : '<span class="badge badge-approved">Verified</span>')
            }
          </div>
          <button class="bike-fav-btn" onclick="toggleFavorite(${bike.id}, this)" title="Save to Favorites">
            <i class="far fa-heart"></i>
          </button>
        </div>
        <div class="bike-card-body">
          <div class="bike-card-brand">${bike.brand || 'Motorcycle'}</div>
          <h3 class="bike-card-title">${bike.title}</h3>
          <div class="bike-specs-row">
            <div class="bike-spec-item"><i class="fas fa-calendar-alt"></i> ${bike.year}</div>
            <div class="bike-spec-item"><i class="fas fa-tachometer-alt"></i> ${(bike.kilometers_driven || 0).toLocaleString()} km</div>
            <div class="bike-spec-item"><i class="fas fa-gas-pump"></i> ${bike.fuel_type || 'Petrol'}</div>
            <div class="bike-spec-item"><i class="fas fa-cogs"></i> ${bike.transmission || 'Manual'}</div>
          </div>
          <div class="bike-card-footer">
            <div class="bike-price-wrap">
              <span class="bike-price-label">Price</span>
              <span class="bike-price-value">₹${formattedPrice}</span>
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <a href="/bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline">Details</a>
              ${!isSold ? `<button onclick="openEnquiryModal(${bike.id})" class="btn btn-sm btn-primary">Enquire</button>` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function populateBrandFilter(bikes) {
  const brandSelect = document.getElementById('filter-brand');
  if (!brandSelect) return;
  const brands = [...new Set(bikes.map(b => b.brand).filter(Boolean))].sort();
  brandSelect.innerHTML = `<option value="">All Brands</option>` + brands.map(b => `<option value="${b}">${b}</option>`).join('');
}

function applyFilters() {
  const searchTerm = (document.getElementById('search-input')?.value || '').toLowerCase();
  const selectedBrand = document.getElementById('filter-brand')?.value || '';
  const maxPrice = parseFloat(document.getElementById('filter-price')?.value) || Infinity;
  const sortOrder = document.getElementById('filter-sort')?.value || 'newest';

  let filtered = allBikes.filter(bike => {
    const matchesSearch = !searchTerm || 
      bike.title.toLowerCase().includes(searchTerm) || 
      bike.brand.toLowerCase().includes(searchTerm) || 
      (bike.model && bike.model.toLowerCase().includes(searchTerm));

    const matchesBrand = !selectedBrand || bike.brand.toLowerCase() === selectedBrand.toLowerCase();
    const matchesPrice = !maxPrice || Number(bike.price) <= maxPrice;

    return matchesSearch && matchesBrand && matchesPrice;
  });

  if (sortOrder === 'price-low') {
    filtered.sort((a, b) => Number(a.price) - Number(b.price));
  } else if (sortOrder === 'price-high') {
    filtered.sort((a, b) => Number(b.price) - Number(a.price));
  } else if (sortOrder === 'year-new') {
    filtered.sort((a, b) => Number(b.year) - Number(a.year));
  }

  renderBikes(filtered);
}

async function toggleFavorite(bikeId, btn) {
  const user = AuthService.getUser();
  if (!user) {
    showToast('Please sign in with Google to save favorites', 'info');
    setTimeout(() => { window.location.href = '/login.html'; }, 1000);
    return;
  }

  try {
    const res = await apiRequest('/api/users/favorites', {
      method: 'POST',
      body: { bike_id: bikeId }
    });
    btn.classList.toggle('active');
    const icon = btn.querySelector('i');
    if (icon) {
      icon.className = btn.classList.contains('active') ? 'fas fa-heart' : 'far fa-heart';
    }
    showToast(res.message || 'Favorites updated', 'success');
  } catch (err) {
    showToast(err.message || 'Failed to update favorites', 'error');
  }
}

function openEnquiryModal(bikeId) {
  const bike = allBikes.find(b => b.id === bikeId);
  if (!bike) return;
  currentBikeForEnquiry = bike;

  const modalTitle = document.getElementById('enquiry-modal-bike-title');
  if (modalTitle) modalTitle.innerText = `${bike.year} ${bike.title} (₹${Number(bike.price).toLocaleString('en-IN')})`;

  const user = AuthService.getUser();
  if (user) {
    const nameInput = document.getElementById('enquiry-name');
    const emailInput = document.getElementById('enquiry-email');
    const phoneInput = document.getElementById('enquiry-phone');
    if (nameInput) nameInput.value = user.name || '';
    if (emailInput) emailInput.value = user.email || '';
    if (phoneInput && user.phone) phoneInput.value = user.phone;
  }

  openModal('enquiry-modal');
}

async function submitEnquiry(event) {
  event.preventDefault();
  if (!currentBikeForEnquiry) return;

  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

  const formData = new FormData(form);
  const payload = {
    bike_id: currentBikeForEnquiry.id,
    name: formData.get('name'),
    email: formData.get('email'),
    phone: formData.get('phone'),
    message: formData.get('message')
  };

  try {
    const res = await apiRequest('/api/enquiries', {
      method: 'POST',
      body: payload
    });
    showToast(res.message || 'Enquiry submitted successfully! Our team will contact you.', 'success');
    closeModal('enquiry-modal');
    form.reset();
  } catch (err) {
    showToast(err.message || 'Failed to submit enquiry', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('marketplace-bikes-grid')) {
    loadMarketplaceBikes();

    const searchInput = document.getElementById('search-input');
    const brandSelect = document.getElementById('filter-brand');
    const priceSlider = document.getElementById('filter-price');
    const sortSelect = document.getElementById('filter-sort');

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (brandSelect) brandSelect.addEventListener('change', applyFilters);
    if (priceSlider) {
      priceSlider.addEventListener('input', (e) => {
        const valDisplay = document.getElementById('price-val-display');
        if (valDisplay) valDisplay.innerText = `Up to ₹${Number(e.target.value).toLocaleString('en-IN')}`;
        applyFilters();
      });
    }
    if (sortSelect) sortSelect.addEventListener('change', applyFilters);
  }
});
