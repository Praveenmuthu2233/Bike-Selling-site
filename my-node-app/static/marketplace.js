/**
 * SMR Motors - Marketplace Vehicle Inventory Loader, Server-Side Pagination & Filters
 */

let allBikes = [];
let currentBikeForEnquiry = null;
let currentPage = 1;
let currentLimit = window.innerWidth <= 768 ? 6 : 9;
let currentPagination = null;
let brandsLoaded = false;

// Adjust limit on resize
window.addEventListener('resize', () => {
  const newLimit = window.innerWidth <= 768 ? 6 : 9;
  if (newLimit !== currentLimit) {
    currentLimit = newLimit;
    loadMarketplaceBikes(1);
  }
});

async function loadMarketplaceBikes(page = 1) {
  const container = document.getElementById('marketplace-bikes-grid');
  if (!container) return;

  currentPage = page;

  container.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 3rem 0;">
      <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-primary);"></i>
      <p style="margin-top: 1rem; color: var(--text-secondary);">Loading verified motorcycle inventory...</p>
    </div>
  `;

  // Build query string based on active filters
  const searchTerm = (document.getElementById('search-input')?.value || '').trim();
  const selectedBrand = document.getElementById('filter-brand')?.value || '';
  const maxPrice = document.getElementById('filter-price')?.value;
  const sortOrder = document.getElementById('filter-sort')?.value || 'newest';

  let sortParam = 'newest';
  if (sortOrder === 'price-low') sortParam = 'price_asc';
  else if (sortOrder === 'price-high') sortParam = 'price_desc';
  else if (sortOrder === 'year-new') sortParam = 'year_desc';

  const params = new URLSearchParams({
    page: currentPage,
    limit: currentLimit,
    sort: sortParam
  });

  if (searchTerm) params.set('search', searchTerm);
  if (selectedBrand) params.set('brand', selectedBrand);
  if (maxPrice && Number(maxPrice) < 600000) params.set('max_price', maxPrice);

  try {
    const res = await apiRequest(`/api/bikes?${params.toString()}`);
    allBikes = res.data || res.bikes || [];
    currentPagination = res.pagination || {
      total: allBikes.length,
      page: currentPage,
      limit: currentLimit,
      totalPages: Math.ceil(allBikes.length / currentLimit) || 1,
      hasNext: false,
      hasPrev: false,
      start: 1,
      end: allBikes.length
    };

    renderBikes(allBikes);
    renderPaginationControls(currentPagination);

    if (!brandsLoaded) {
      loadBrandFilterOptions();
      brandsLoaded = true;
    }
  } catch (err) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <i class="fas fa-exclamation-triangle empty-state-icon"></i>
        <h3>Unable to load motorcycles</h3>
        <p>${err.message}</p>
        <button onclick="loadMarketplaceBikes(1)" class="btn btn-primary" style="margin-top: 1rem;">Try Again</button>
      </div>
    `;
    const paginContainer = document.getElementById('marketplace-pagination');
    if (paginContainer) paginContainer.innerHTML = '';
  }
}

async function loadBrandFilterOptions() {
  const brandSelect = document.getElementById('filter-brand');
  if (!brandSelect) return;
  try {
    const res = await apiRequest('/api/bikes?status=all&limit=100');
    const bikes = res.data || res.bikes || [];
    const brands = [...new Set(bikes.map(b => b.brand).filter(Boolean))].sort();
    if (brands.length > 0) {
      brandSelect.innerHTML = `<option value="">All Brands</option>` + brands.map(b => `<option value="${b}">${b}</option>`).join('');
    }
  } catch (e) {
    // Fallback standard brands
    brandSelect.innerHTML = `
      <option value="">All Brands</option>
      <option value="Royal Enfield">Royal Enfield</option>
      <option value="Yamaha">Yamaha</option>
      <option value="KTM">KTM</option>
      <option value="Bajaj">Bajaj</option>
      <option value="Honda">Honda</option>
      <option value="TVS">TVS</option>
    `;
  }
}

// Global state for individual motorcycle card image sliders
window.cardSliderState = window.cardSliderState || {};

function buildBikeCardHtml(bike, isShowcase = false) {
  let images = [];
  try {
    images = typeof bike.images === 'string' ? JSON.parse(bike.images) : (bike.images || []);
  } catch (e) {
    images = [];
  }
  if (!images || images.length === 0) {
    images = ['/static/images/IMG-20251204-WA0053.jpg'];
  }
  // Up to 6 images per bike as specified in requirements
  images = images.slice(0, 6);

  const formattedPrice = Number(bike.price || bike.sellingPrice || 100000).toLocaleString('en-IN');
  const isSold = (bike.status === 'soldout' || bike.listing_status === 'soldout' || bike.isSoldout === 1);
  const locationText = (bike.location || 'Salem, Tamil Nadu').split(',')[0].trim();
  const kmsText = (bike.kilometers_driven || 0).toLocaleString();
  const fuelText = bike.fuel_type || 'Petrol';
  const transText = bike.transmission || 'Manual';

  const prefix = isShowcase ? 'showcase-' : '';
  const sliderId = `cslider-${prefix}${bike.id}`;
  const trackId = `ctrack-${prefix}${bike.id}`;
  const counterId = `ccnt-${prefix}${bike.id}`;
  const dotsId = `cdots-${prefix}${bike.id}`;

  const sliderHtml = `
    <div class="bike-card-img-wrapper">
      <div class="card-slider" id="${sliderId}" data-slider-id="${sliderId}" data-total="${images.length}">
        <div class="card-slider-track" id="${trackId}">
          ${images.map((src, i) => `
            <div class="card-slider-slide">
              <img src="${src}" alt="${bike.title} - Photo ${i+1}" class="bike-card-img" loading="lazy" onerror="this.src='/static/images/IMG-20251204-WA0053.jpg';" />
            </div>
          `).join('')}
        </div>
        ${images.length > 1 ? `
          <button type="button" class="card-slider-arrow prev" onclick="event.stopPropagation(); navigateCardSlider('${sliderId}', -1, true)" title="Previous image" aria-label="Previous image">
            <i class="fas fa-chevron-left"></i>
          </button>
          <button type="button" class="card-slider-arrow next" onclick="event.stopPropagation(); navigateCardSlider('${sliderId}', 1, true)" title="Next image" aria-label="Next image">
            <i class="fas fa-chevron-right"></i>
          </button>
          <div class="card-slider-dots" id="${dotsId}">
            ${images.map((_, i) => `
              <button type="button" class="card-slider-dot ${i === 0 ? 'active' : ''}" onclick="event.stopPropagation(); gotoCardSlide('${sliderId}', ${i}, true)" title="Image ${i+1}" aria-label="Go to image ${i+1}"></button>
            `).join('')}
          </div>
          <div class="card-img-counter" id="${counterId}">
            <span class="current-idx">1</span> / <span>${images.length}</span>
          </div>
        ` : ''}
        <div class="bike-card-badge">
          ${isSold 
            ? '<span class="badge badge-soldout">Sold Out</span>'
            : (bike.featured ? '<span class="badge badge-featured"><i class="fas fa-star"></i> Featured</span>' : '<span class="badge badge-approved"><i class="fas fa-check-circle"></i> Certified</span>')
          }
        </div>
        <button type="button" class="bike-fav-btn" onclick="toggleFavorite(${bike.id}, this)" title="Save to Favorites" aria-label="Add to Favorites">
          <i class="far fa-heart"></i>
        </button>
      </div>
    </div>
  `;

  return `
    <div class="bike-card" style="${isShowcase ? 'box-shadow: 0 8px 24px rgba(0,0,0,0.35);' : ''}">
      ${sliderHtml}
      <div class="bike-card-body" style="${isShowcase ? 'padding: 1.25rem;' : ''}">
        <div class="bike-card-brand">${bike.brand || 'Motorcycle'} ${bike.model ? '• ' + bike.model : ''}</div>
        <h3 class="bike-card-title" style="${isShowcase ? 'font-size: 1.15rem; margin-bottom: 0.5rem;' : ''}">${bike.title}</h3>
        <div class="bike-specs-row" style="${isShowcase ? 'margin-bottom: 0.85rem;' : ''}">
          <div class="bike-spec-item" title="Model Year"><i class="fas fa-calendar-alt"></i> ${bike.year}</div>
          <div class="bike-spec-item" title="Kilometers Driven"><i class="fas fa-tachometer-alt"></i> ${kmsText} km</div>
          <div class="bike-spec-item" title="Fuel Type"><i class="fas fa-gas-pump"></i> ${fuelText}</div>
          <div class="bike-spec-item" title="Transmission"><i class="fas fa-cogs"></i> ${transText}</div>
          <div class="bike-spec-item" title="Location"><i class="fas fa-map-marker-alt"></i> ${locationText}</div>
        </div>
        <div class="bike-card-footer" style="${isShowcase ? 'padding-top: 0.85rem; border-top: 1px solid var(--border-subtle);' : ''}">
          <div class="bike-price-wrap">
            <span class="bike-price-label">Price</span>
            <span class="bike-price-value" style="${isShowcase ? 'font-size: 1.25rem;' : ''}">₹${formattedPrice}</span>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <a href="/enquiry-bike-details.html?id=${bike.id}" class="btn btn-sm btn-outline">Details</a>
            ${!isSold ? `<button type="button" onclick="openEnquiryModal(${bike.id})" class="btn btn-sm btn-primary">Enquire</button>` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

function initAllCardSliders() {
  const sliders = document.querySelectorAll('.card-slider');
  sliders.forEach(sliderEl => {
    const sliderId = sliderEl.dataset.sliderId || sliderEl.id;
    const total = parseInt(sliderEl.dataset.total) || 1;
    if (!sliderId || total <= 1) return;

    // Reset previous timer if any
    if (window.cardSliderState[sliderId] && window.cardSliderState[sliderId].timer) {
      clearInterval(window.cardSliderState[sliderId].timer);
    }

    const state = {
      sliderId: sliderId,
      currentIndex: 0,
      total: total,
      timer: null,
      paused: false,
      manuallyStopped: false
    };
    window.cardSliderState[sliderId] = state;

    // Auto-play every 3.5 seconds (3 to 4 seconds requirement)
    state.timer = setInterval(() => {
      if (!state.paused && !state.manuallyStopped) {
        navigateCardSlider(sliderId, 1, false);
      }
    }, 3500);

    // Pause on mouse hover, resume on mouse leave
    sliderEl.onmouseenter = () => { state.paused = true; };
    sliderEl.onmouseleave = () => { state.paused = false; };

    // Mobile touch swipe support
    let touchStartX = 0;
    sliderEl.ontouchstart = (e) => {
      touchStartX = e.touches[0].clientX;
    };
    sliderEl.ontouchend = (e) => {
      const touchEndX = e.changedTouches[0].clientX;
      const diff = touchStartX - touchEndX;
      if (Math.abs(diff) > 35) {
        if (diff > 0) {
          navigateCardSlider(sliderId, 1, true); // swipe left -> slide next
        } else {
          navigateCardSlider(sliderId, -1, true); // swipe right -> slide prev
        }
      }
    };
  });
}

function navigateCardSlider(sliderId, dir, isManual = false) {
  const state = window.cardSliderState[sliderId];
  if (!state) return;
  const nextIdx = (state.currentIndex + dir + state.total) % state.total;
  gotoCardSlide(sliderId, nextIdx, isManual);
}

function gotoCardSlide(sliderId, targetIdx, isManual = false) {
  const state = window.cardSliderState[sliderId];
  const sliderEl = document.getElementById(sliderId);
  if (!sliderEl) return;

  const total = state ? state.total : (parseInt(sliderEl.dataset.total) || 1);
  const safeIdx = (targetIdx + total) % total;

  if (state) {
    state.currentIndex = safeIdx;
    if (isManual) {
      // Stop auto-play when manually controlled (Requirement 1)
      state.manuallyStopped = true;
      if (state.timer) {
        clearInterval(state.timer);
        state.timer = null;
      }
    }
  }

  // Horizontal slide right to left
  const track = sliderEl.querySelector('.card-slider-track');
  if (track) {
    track.style.transform = `translateX(-${safeIdx * 100}%)`;
  }

  // Update dot indicators
  const dots = sliderEl.querySelectorAll('.card-slider-dot');
  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === safeIdx);
  });

  // Update dynamic image counter badge
  const counterSpan = sliderEl.querySelector('.card-img-counter .current-idx');
  if (counterSpan) {
    counterSpan.textContent = safeIdx + 1;
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
        <button onclick="resetMarketplaceFilters()" class="btn btn-outline" style="margin-top: 1rem;">Reset Filters</button>
      </div>
    `;
    return;
  }

  container.innerHTML = bikes.map(bike => buildBikeCardHtml(bike, false)).join('');
  initAllCardSliders();
}

function renderPaginationControls(p) {
  let paginContainer = document.getElementById('marketplace-pagination');
  if (!paginContainer) {
    const grid = document.getElementById('marketplace-bikes-grid');
    if (!grid) return;
    paginContainer = document.createElement('div');
    paginContainer.id = 'marketplace-pagination';
    paginContainer.className = 'pagination-wrapper';
    paginContainer.style.marginTop = '2.5rem';
    grid.parentNode.insertBefore(paginContainer, grid.nextSibling);
  }

  if (!p || p.totalPages <= 1) {
    paginContainer.innerHTML = p && p.total > 0 
      ? `<div style="text-align:center; color:var(--text-muted); font-size:0.88rem;">Showing all ${p.total} verified motorcycles</div>` 
      : '';
    return;
  }

  let pagesHtml = '';
  const totalPages = p.totalPages;
  const curPage = p.page;

  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= curPage - 1 && i <= curPage + 1)) {
      pagesHtml += `<button class="pagination-btn ${i === curPage ? 'active' : ''}" onclick="loadMarketplaceBikes(${i})">${i}</button>`;
    } else if (i === curPage - 2 || i === curPage + 2) {
      pagesHtml += `<span style="color:var(--text-muted); padding:0 0.25rem;">...</span>`;
    }
  }

  paginContainer.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; width: 100%;">
      <div style="color: var(--text-muted); font-size: 0.88rem;">
        Showing <strong style="color: var(--text-primary);">${p.start}–${p.end}</strong> of <strong style="color: var(--text-primary);">${p.total}</strong> motorcycles
      </div>
      <div style="display: flex; gap: 0.4rem; align-items: center;">
        <button class="pagination-btn" ${!p.hasPrev ? 'disabled style="opacity:0.4; cursor:not-allowed;"' : `onclick="loadMarketplaceBikes(${curPage - 1})"`}>
          <i class="fas fa-chevron-left"></i> Prev
        </button>
        ${pagesHtml}
        <button class="pagination-btn" ${!p.hasNext ? 'disabled style="opacity:0.4; cursor:not-allowed;"' : `onclick="loadMarketplaceBikes(${curPage + 1})"`}>
          Next <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  `;
}

function applyFilters() {
  loadMarketplaceBikes(1);
}

function resetMarketplaceFilters() {
  const searchInput = document.getElementById('search-input');
  const brandSelect = document.getElementById('filter-brand');
  const priceSlider = document.getElementById('filter-price');
  const valDisplay = document.getElementById('price-val-display');

  if (searchInput) searchInput.value = '';
  if (brandSelect) brandSelect.value = '';
  if (priceSlider) priceSlider.value = 600000;
  if (valDisplay) valDisplay.innerText = 'Up to ₹6,00,000';

  loadMarketplaceBikes(1);
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

// ==============================================================================
// SHOWCASE CAROUSEL (Requirement 9: One bike at a time on mobile, autoplay, swipe)
// ==============================================================================
let carouselBikes = [];
let carouselCurrentIndex = 0;
let carouselAutoplayTimer = null;
let touchStartX = 0;
let touchEndX = 0;

async function initShowcaseCarousel() {
  const track = document.getElementById('carousel-track');
  const dotsContainer = document.getElementById('carousel-dots');
  const wrap = document.getElementById('showcase-carousel-wrap');
  if (!track) return;

  try {
    const res = await apiRequest('/api/bikes?status=approved&limit=12');
    const bikes = (res.data || res.bikes || []).filter(b => {
      const st = (b.status || b.listing_status || '').toLowerCase();
      return (st === 'approved' || st === 'published') && b.isSoldout != 1;
    });

    if (bikes.length === 0) {
      if (wrap) wrap.style.display = 'none';
      return;
    }

    carouselBikes = bikes;
    if (wrap) wrap.style.display = 'block';

    track.innerHTML = carouselBikes.map((bike, idx) => {
      return `
        <div class="carousel-slide" data-slide-index="${idx}">
          ${buildBikeCardHtml(bike, true)}
        </div>
      `;
    }).join('');

    initAllCardSliders();
    renderCarouselDots();
    updateCarouselPosition();
    startCarouselAutoplay();

    // Hover pause listeners
    wrap.addEventListener('mouseenter', stopCarouselAutoplay);
    wrap.addEventListener('mouseleave', startCarouselAutoplay);

    // Touch swipe listeners for mobile (Requirement 9)
    const viewport = document.getElementById('carousel-viewport');
    if (viewport) {
      viewport.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
        stopCarouselAutoplay();
      }, { passive: true });

      viewport.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleCarouselSwipe();
        startCarouselAutoplay();
      }, { passive: true });
    }

  } catch (err) {
    console.warn('Carousel showcase notice:', err);
    if (wrap) wrap.style.display = 'none';
  }
}

function handleCarouselSwipe() {
  const threshold = 40;
  if (touchEndX < touchStartX - threshold) {
    carouselNext();
  } else if (touchEndX > touchStartX + threshold) {
    carouselPrev();
  }
}

function getMaxCarouselIndex() {
  const isMobile = window.innerWidth <= 768;
  const visibleCards = isMobile ? 1 : 3;
  return Math.max(0, carouselBikes.length - visibleCards);
}

function renderCarouselDots() {
  const dotsContainer = document.getElementById('carousel-dots');
  if (!dotsContainer) return;
  const isMobile = window.innerWidth <= 768;
  const visibleCards = isMobile ? 1 : 3;
  const totalSteps = Math.max(1, carouselBikes.length - visibleCards + 1);

  if (totalSteps <= 1) {
    dotsContainer.innerHTML = '';
    return;
  }

  dotsContainer.innerHTML = Array.from({ length: totalSteps }).map((_, i) => `
    <button class="carousel-dot ${i === carouselCurrentIndex ? 'active' : ''}" onclick="goToCarouselSlide(${i})" aria-label="Slide ${i+1}"></button>
  `).join('');
}

function updateCarouselPosition() {
  const track = document.getElementById('carousel-track');
  if (!track || carouselBikes.length === 0) return;

  const isMobile = window.innerWidth <= 768;
  const stepPercent = isMobile ? 100 : (100 / 3);
  track.style.transform = `translateX(-${carouselCurrentIndex * stepPercent}%)`;

  const dots = document.querySelectorAll('.carousel-dot');
  dots.forEach((dot, idx) => {
    dot.classList.toggle('active', idx === carouselCurrentIndex);
  });
}

function carouselNext() {
  const maxIdx = getMaxCarouselIndex();
  carouselCurrentIndex = (carouselCurrentIndex >= maxIdx) ? 0 : carouselCurrentIndex + 1;
  updateCarouselPosition();
}

function carouselPrev() {
  const maxIdx = getMaxCarouselIndex();
  carouselCurrentIndex = (carouselCurrentIndex <= 0) ? maxIdx : carouselCurrentIndex - 1;
  updateCarouselPosition();
}

function goToCarouselSlide(idx) {
  carouselCurrentIndex = Math.min(Math.max(0, idx), getMaxCarouselIndex());
  updateCarouselPosition();
}

function startCarouselAutoplay() {
  stopCarouselAutoplay();
  carouselAutoplayTimer = setInterval(carouselNext, 4500);
}

function stopCarouselAutoplay() {
  if (carouselAutoplayTimer) {
    clearInterval(carouselAutoplayTimer);
    carouselAutoplayTimer = null;
  }
}

window.addEventListener('resize', () => {
  if (carouselBikes.length > 0) {
    const maxIdx = getMaxCarouselIndex();
    if (carouselCurrentIndex > maxIdx) carouselCurrentIndex = maxIdx;
    renderCarouselDots();
    updateCarouselPosition();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('marketplace-bikes-grid')) {
    loadMarketplaceBikes();
    initShowcaseCarousel();

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
