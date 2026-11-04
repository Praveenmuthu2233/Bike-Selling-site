/**
 * SMR Motors - Homepage Script
 * Dynamic product loading, real images, filtering, search, categories, favorites, enquiries, and contact submission.
 */

let allProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 8;
let currentUser = null;

document.addEventListener("DOMContentLoaded", function () {
  checkNavbarAuth();
  loadCategories();
  loadProducts();
  loadGallery();
  setupFilterHandlers();
});

/**
 * Check logged in user status and update top navigation
 */
async function checkNavbarAuth() {
  const token = sessionStorage.getItem("token");
  const loggedOutBox = document.getElementById("navAuthLoggedOut");
  const loggedInBox = document.getElementById("navAuthLoggedIn");

  if (!token) {
    if (loggedOutBox) loggedOutBox.classList.remove("d-none");
    if (loggedInBox) loggedInBox.classList.add("d-none");
    return;
  }

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/auth/me`, {
      headers: { Authorization: "Bearer " + token }
    });

    if (res.ok) {
      const data = await res.json();
      if (data.success && data.user) {
        currentUser = data.user;
        if (loggedOutBox) loggedOutBox.classList.add("d-none");
        if (loggedInBox) {
          loggedInBox.classList.remove("d-none");
          const photo = document.getElementById("navUserPhoto");
          const name = document.getElementById("navUserNameText");
          if (photo && currentUser.profile_image) photo.src = currentUser.profile_image;
          if (name) name.textContent = (currentUser.name || "My Account").split(" ")[0];
        }
      }
    } else {
      sessionStorage.removeItem("token");
      if (loggedOutBox) loggedOutBox.classList.remove("d-none");
      if (loggedInBox) loggedInBox.classList.add("d-none");
    }
  } catch (e) {
    if (loggedOutBox) loggedOutBox.classList.remove("d-none");
  }
}

/**
 * Load categories dynamically
 */
async function loadCategories() {
  const container = document.getElementById("categoryBikeImg");
  if (!container) return;

  try {
    let categories = [];
    const res = await fetch(`${window.API.BASE_URL}/api/categories`);
    if (res.ok) {
      const data = await res.json();
      categories = data.categories || [];
    }

    if (categories.length === 0) {
      container.innerHTML = '<div class="col-12 text-center text-muted py-3">No categories currently configured.</div>';
      return;
    }

    let html = "";
    categories.slice(0, 8).forEach(cat => {
      html += `
        <div class="col-6 col-md-4 col-lg-3 text-center">
          <div class="category-card p-3 rounded-4 shadow-sm bg-white h-100 border">
            <img src="${cat.image_url}" alt="${cat.category_name}" class="img-fluid rounded-3 mb-2" style="height: 140px; object-fit: cover; width: 100%;">
            <h5 class="fw-bold fs-6 mb-0">${cat.category_name}</h5>
          </div>
        </div>`;
    });
    container.innerHTML = html;
  } catch (err) {
    console.error("Categories load error:", err);
  }
}

/**
 * Load bikes from API
 */
async function loadProducts() {
  const container = document.getElementById("productList");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/bikes`);
    const data = await res.json();

    allProducts = (data.bikes || data || []).filter(b => b.status === "approved" || b.isAccepted == 1);
    filteredProducts = [...allProducts];

    displayProducts(1);
    setupPagination();
  } catch (err) {
    console.error("Error fetching bikes:", err);
    if (container) {
      container.innerHTML = `<div class="col-12 alert alert-warning text-center">Unable to load bikes at this time. Please try refreshing.</div>`;
    }
  }
}

/**
 * Display bikes for a given page
 */
function displayProducts(page) {
  currentPage = page;
  const container = document.getElementById("productList");
  if (!container) return;

  const start = (page - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const paginated = filteredProducts.slice(start, end);

  if (paginated.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center py-5">
        <i class="fa-solid fa-motorcycle fa-3x text-muted mb-3"></i>
        <h5 class="text-muted">No bikes match your search or price criteria.</h5>
        <button class="btn btn-outline-success btn-sm mt-2" onclick="resetFilters()">Reset Filters</button>
      </div>`;
    return;
  }

  let html = "";
  paginated.forEach(bike => {
    let images = [];
    if (Array.isArray(bike.images)) images = bike.images;
    else if (typeof bike.images === "string") {
      try { images = JSON.parse(bike.images); } catch(e) { images = [bike.images]; }
    }
    const bikeImage = images[0] || bike.image || "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=500";
    const priceDisplay = Number(bike.selling_price || bike.sellingPrice || bike.price || 0).toLocaleString();

    html += `
      <div class="col-12 col-md-6 col-lg-3">
        <div class="product-bike-card card h-100 border-0 shadow-sm rounded-4 overflow-hidden position-relative">
          <!-- Favorite Icon Button -->
          <button class="btn btn-sm btn-light rounded-circle position-absolute top-0 end-0 m-2 shadow-sm fav-toggle-btn" 
                  onclick="toggleFavorite(${bike.id}, this)" title="Save to Favorites">
            <i class="fa-regular fa-heart text-danger"></i>
          </button>

          <!-- Bike Thumbnail -->
          <div class="bike-img-wrapper" style="height: 180px; overflow: hidden; background: #f1f5f9;">
            <img src="${bikeImage}" alt="${bike.title}" class="card-img-top w-100 h-100" style="object-fit: cover;">
          </div>

          <div class="card-body p-3 d-flex flex-column">
            <span class="badge bg-light text-dark align-self-start mb-1 small">${bike.brand}</span>
            <h5 class="card-title fw-bold fs-6 mb-1 text-truncate" title="${bike.title}">${bike.title}</h5>
            <div class="text-success fw-bold fs-5 mb-2">₹${priceDisplay}</div>

            <div class="small text-muted mb-3">
              <div><i class="fa-solid fa-gauge me-1"></i> ${bike.kilometers_driven || bike.bikeKms || "0"} kms</div>
              <div><i class="fa-solid fa-location-dot me-1"></i> ${bike.location || bike.bikeLocation || "Kelambakkam"}</div>
            </div>

            <div class="mt-auto d-flex gap-2">
              <button type="button" class="btn btn-outline-secondary btn-sm flex-fill fw-semibold" 
                      data-bs-toggle="modal" data-bs-target="#viewModal${bike.id}">
                Details
              </button>
              <button type="button" class="btn btn-success btn-sm flex-fill fw-semibold" 
                      onclick="openEnquiryModal(${bike.id}, '${bike.title.replace(/'/g, "\\'")}')">
                Enquire
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Detail Modal -->
      <div class="modal fade" id="viewModal${bike.id}" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content rounded-4 border-0">
            <div class="modal-header border-0 pb-0">
              <h5 class="modal-title fw-bold">${bike.title}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-4">
              <img src="${bikeImage}" class="img-fluid rounded-3 mb-3 w-100" style="height: 220px; object-fit: cover;">
              <h4 class="text-success fw-bold mb-3">₹${priceDisplay}</h4>
              <div class="row g-2 small">
                <div class="col-6"><strong>Make / Brand:</strong> ${bike.brand}</div>
                <div class="col-6"><strong>Model:</strong> ${bike.model}</div>
                <div class="col-6"><strong>Reg Number:</strong> ${bike.vehicle_number || "TN Registered"}</div>
                <div class="col-6"><strong>Condition:</strong> ${bike.bike_condition || "Good"}</div>
                <div class="col-6"><strong>Year:</strong> ${bike.year || "2022"}</div>
                <div class="col-6"><strong>Kms:</strong> ${bike.kilometers_driven || "0"} kms</div>
                <div class="col-6"><strong>Color:</strong> ${bike.bike_color || "Standard"}</div>
                <div class="col-6"><strong>Engine CC:</strong> ${bike.engine_cc || "150cc"}</div>
                <div class="col-6"><strong>Insurance:</strong> ${bike.insurance || "Yes"}</div>
                <div class="col-6"><strong>Location:</strong> ${bike.location || "Kelambakkam"}</div>
              </div>
              <p class="text-muted mt-3 mb-0 small">${bike.description || "Well maintained pre-owned motorcycle with complete checkup."}</p>
            </div>
            <div class="modal-footer border-0 pt-0">
              <button type="button" class="btn btn-light" data-bs-dismiss="modal">Close</button>
              <button type="button" class="btn btn-success fw-semibold" data-bs-dismiss="modal" 
                      onclick="openEnquiryModal(${bike.id}, '${bike.title.replace(/'/g, "\\'")}')">
                Send Enquiry
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

/**
 * Setup Single, Non-Duplicate Pagination
 */
function setupPagination() {
  const container = document.getElementById("pagination");
  if (!container) return;

  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  if (totalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = `<ul class="pagination pagination-sm gap-1 mb-0">`;

  // Prev
  html += `
    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
      <button class="page-link rounded-2" onclick="displayProducts(${currentPage - 1}); setupPagination();">&laquo;</button>
    </li>`;

  for (let i = 1; i <= totalPages; i++) {
    html += `
      <li class="page-item ${currentPage === i ? 'active' : ''}">
        <button class="page-link rounded-2 ${currentPage === i ? 'bg-success border-success text-white' : ''}" onclick="displayProducts(${i}); setupPagination();">${i}</button>
      </li>`;
  }

  // Next
  html += `
    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
      <button class="page-link rounded-2" onclick="displayProducts(${currentPage + 1}); setupPagination();">&raquo;</button>
    </li>`;

  html += `</ul>`;
  container.innerHTML = html;
}

/**
 * Setup Search & Filter Handlers
 */
function setupFilterHandlers() {
  const applyBtn = document.getElementById("applyFilter");
  const searchInput = document.getElementById("searchInput");

  if (applyBtn) {
    applyBtn.addEventListener("click", applyFilter);
  }
  if (searchInput) {
    searchInput.addEventListener("keyup", function (e) {
      if (e.key === "Enter") applyFilter();
    });
  }
}

function applyFilter() {
  const min = parseFloat(document.getElementById("minPrice").value) || 0;
  const max = parseFloat(document.getElementById("maxPrice").value) || Infinity;
  const search = (document.getElementById("searchInput")?.value || "").toLowerCase().trim();

  filteredProducts = allProducts.filter(bike => {
    const price = parseFloat(bike.selling_price || bike.sellingPrice || bike.price || 0);
    const matchesPrice = price >= min && price <= max;

    const title = (bike.title || "").toLowerCase();
    const brand = (bike.brand || "").toLowerCase();
    const model = (bike.model || "").toLowerCase();
    const matchesSearch = !search || title.includes(search) || brand.includes(search) || model.includes(search);

    return matchesPrice && matchesSearch;
  });

  displayProducts(1);
  setupPagination();
}

function resetFilters() {
  document.getElementById("minPrice").value = 0;
  document.getElementById("maxPrice").value = 250000;
  if (document.getElementById("searchInput")) document.getElementById("searchInput").value = "";
  filteredProducts = [...allProducts];
  displayProducts(1);
  setupPagination();
}

/**
 * Open Enquiry Modal with auto-filled info
 */
function openEnquiryModal(bikeId, bikeTitle) {
  document.getElementById("enquiryBikeId").value = bikeId;
  document.getElementById("enquiryModalBikeTitle").textContent = `Enquiry: ${bikeTitle}`;

  if (currentUser) {
    document.getElementById("enquiryCustomerName").value = currentUser.name || "";
    document.getElementById("enquiryCustomerEmail").value = currentUser.email || "";
    document.getElementById("enquiryCustomerMobile").value = currentUser.phone || "";
  }

  new bootstrap.Modal(document.getElementById("customerEnquiryModal")).show();
}

/**
 * Submit Enquiry
 */
async function submitBikeEnquiry(event) {
  event.preventDefault();
  const bikeId = document.getElementById("enquiryBikeId").value;
  const name = document.getElementById("enquiryCustomerName").value.trim();
  const phone = document.getElementById("enquiryCustomerMobile").value.trim();
  const email = document.getElementById("enquiryCustomerEmail").value.trim();
  const message = document.getElementById("enquiryCustomerMessage").value.trim();

  const token = sessionStorage.getItem("token");

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/enquiries`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {})
      },
      body: JSON.stringify({
        bike_id: bikeId,
        name,
        phone,
        email,
        message
      })
    });

    const data = await res.json();
    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById("customerEnquiryModal")).hide();
      Swal.fire({
        icon: "success",
        title: "Enquiry Sent!",
        text: "Thank you! Our SMR Motors sales team will contact you shortly.",
        confirmButtonColor: "#10b981"
      });
      document.getElementById("enquirySubmitForm").reset();
    } else {
      throw new Error(data.message || "Failed to submit enquiry.");
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Submission Error", text: err.message });
  }
}

/**
 * Toggle Favorite
 */
async function toggleFavorite(bikeId, btnElement) {
  const token = sessionStorage.getItem("token");
  if (!token) {
    Swal.fire({
      icon: "info",
      title: "Sign In with Google",
      text: "Please sign in with your Google account to save bikes to your favorites.",
      showCancelButton: true,
      confirmButtonColor: "#10b981",
      confirmButtonText: "Sign In Now"
    }).then(res => {
      if (res.isConfirmed) window.location.href = "/userLogin.html";
    });
    return;
  }

  const icon = btnElement.querySelector("i");
  const isSolid = icon.classList.contains("fa-solid");

  try {
    const method = isSolid ? "DELETE" : "POST";
    const res = await fetch(`${window.API.BASE_URL}/api/users/favorites/${bikeId}`, {
      method,
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    if (data.success) {
      if (isSolid) {
        icon.classList.remove("fa-solid");
        icon.classList.add("fa-regular");
      } else {
        icon.classList.remove("fa-regular");
        icon.classList.add("fa-solid");
      }
    }
  } catch (e) {
    console.error("Favorite toggle error:", e);
  }
}

/**
 * Contact Form Submit
 */
async function handleContactSubmit(event) {
  event.preventDefault();
  const submitBtn = document.getElementById("contactSubmitBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Sending...";

  const name = document.getElementById("contactName").value.trim();
  const email = document.getElementById("contactEmail").value.trim();
  const phone = document.getElementById("contactPhone").value.trim();
  const message = document.getElementById("contactMessage").value.trim();

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/contact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, phone, message })
    });

    const data = await res.json();
    if (data.success) {
      Swal.fire({
        icon: "success",
        title: "Message Sent!",
        text: "Thank you for reaching out. We will get back to you shortly.",
        confirmButtonColor: "#10b981"
      });
      document.getElementById("contactForm").reset();
    } else {
      throw new Error(data.message || "Failed to send message.");
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i class="fa-regular fa-paper-plane me-1"></i> Submit Message`;
  }
}

/**
 * Gallery loader
 */
function loadGallery() {
  const gallery = document.getElementById("galleryImages");
  if (!gallery || !window.gallery_image) return;

  let html = "";
  window.gallery_image.forEach((img, index) => {
    html += `
      <div class="carousel-item ${index === 0 ? 'active' : ''}">
        <img src="${img.url}" class="d-block w-100" alt="${img.alt}" style="max-height: 480px; object-fit: cover;">
      </div>`;
  });
  gallery.innerHTML = html;
}
