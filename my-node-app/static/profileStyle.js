/**
 * User Dashboard Controller Script - SMR Motors
 * Handles Profile, Bike CRUD with Images, Enquiries, Favorites, and Session Management.
 */

let currentUser = null;
let currentDashboardData = null;
let selectedBikeImages = [];

document.addEventListener("DOMContentLoaded", function () {
  checkUserSession();
});

/**
 * Check active session; redirect to login if not authenticated
 */
async function checkUserSession() {
  const token = sessionStorage.getItem("token");
  if (!token) {
    window.location.href = "/userLogin.html";
    return;
  }

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/profile`, {
      headers: { Authorization: "Bearer " + token }
    });

    if (!res.ok) {
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
      window.location.href = "/userLogin.html";
      return;
    }

    const data = await res.json();
    if (data.success && data.user) {
      currentUser = data.user;
      renderUserData(currentUser);
      loadDashboardData();
    }
  } catch (err) {
    console.error("Session verification error:", err);
  }
}

/**
 * Render user profile elements across the UI
 */
function renderUserData(user) {
  const defaultAvatar = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120";
  const avatarUrl = user.profile_image || defaultAvatar;

  // Nav
  document.getElementById("navAvatar").src = avatarUrl;
  document.getElementById("navUserName").textContent = user.name || "User";

  // Sidebar
  document.getElementById("sideAvatar").src = avatarUrl;
  document.getElementById("sideName").textContent = user.name || "User";
  document.getElementById("sideEmail").textContent = user.email || "";

  // Overview Banner
  document.getElementById("welcomeAvatar").src = avatarUrl;
  document.getElementById("welcomeName").textContent = (user.name || "User").split(" ")[0];

  // Profile Tab
  document.getElementById("profileAvatarBig").src = avatarUrl;
  document.getElementById("profileFullName").textContent = user.name || "";
  document.getElementById("profileEmailAddress").textContent = user.email || "";
  document.getElementById("inputProfileName").value = user.name || "";
  document.getElementById("inputProfileEmail").value = user.email || "";
  document.getElementById("inputProfilePhone").value = user.phone || "";
}

/**
 * Switch Dashboard Tabs
 */
function switchTab(tabName) {
  document.querySelectorAll(".dashboard-tab").forEach(tab => tab.classList.remove("active"));
  document.querySelectorAll(".sidebar-nav .nav-link").forEach(btn => btn.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabName}`);
  const targetBtn = document.getElementById(`tab-${tabName}-btn`);

  if (targetTab) targetTab.classList.add("active");
  if (targetBtn) targetBtn.classList.add("active");

  // Close mobile offcanvas if open
  const offcanvasEl = document.getElementById("sidebarMenu");
  if (offcanvasEl) {
    const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
    if (offcanvas) offcanvas.hide();
  }

  // Reload tab specific data
  if (tabName === "listings") loadUserListings();
  if (tabName === "enquiries") loadUserEnquiries();
  if (tabName === "favorites") loadUserFavorites();
}

/**
 * Load complete aggregated dashboard data
 */
async function loadDashboardData() {
  const token = sessionStorage.getItem("token");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/dashboard`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    if (data.success) {
      currentDashboardData = data;
      const stats = data.stats;

      document.getElementById("statTotalListings").textContent = stats.totalListings || 0;
      document.getElementById("statApprovedListings").textContent = stats.approvedListings || 0;
      document.getElementById("statPendingListings").textContent = stats.pendingListings || 0;
      document.getElementById("statTotalEnquiries").textContent = stats.totalEnquiries || 0;

      // Render recent listings in overview
      renderOverviewListings(data.listings);
      renderOverviewRecentMarketplace(data.recentBikes);
    }
  } catch (err) {
    console.error("Dashboard data load error:", err);
  }
}

function renderOverviewListings(listings) {
  const container = document.getElementById("overviewListingsContainer");
  if (!listings || listings.length === 0) {
    container.innerHTML = `
      <div class="text-center py-4 text-muted">
        <i class="fa-solid fa-motorcycle fa-2x mb-2 text-muted-subtle"></i>
        <p class="mb-2">You haven't listed any bikes yet.</p>
        <button class="btn btn-sm btn-outline-success" onclick="openAddBikeModal()">Add Your First Bike</button>
      </div>`;
    return;
  }

  let html = `<div class="list-group list-group-flush">`;
  listings.slice(0, 3).forEach(b => {
    let images = [];
    try { images = typeof b.images === 'string' ? JSON.parse(b.images) : (b.images || []); } catch(e) {}
    const imgUrl = images[0] || b.image || "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=200";

    const badgeClass = b.status === "approved" ? "bg-success" : (b.status === "rejected" ? "bg-danger" : "bg-warning text-dark");
    html += `
      <div class="list-group-item d-flex align-items-center justify-content-between px-0 py-3">
        <div class="d-flex align-items-center gap-3">
          <img src="${imgUrl}" class="rounded-3" width="55" height="42" style="object-fit:cover;">
          <div>
            <h6 class="mb-0 fw-bold">${b.title}</h6>
            <small class="text-muted">₹${Number(b.price).toLocaleString()} • ${b.brand} ${b.model}</small>
          </div>
        </div>
        <span class="badge ${badgeClass} text-uppercase px-2 py-1">${b.status}</span>
      </div>`;
  });
  html += `</div>`;
  container.innerHTML = html;
}

function renderOverviewRecentMarketplace(recentBikes) {
  const container = document.getElementById("overviewRecentBikesContainer");
  if (!recentBikes || recentBikes.length === 0) {
    container.innerHTML = `<p class="text-muted text-center py-3">No bikes available currently.</p>`;
    return;
  }

  let html = `<div class="list-group list-group-flush">`;
  recentBikes.forEach(b => {
    let images = [];
    try { images = typeof b.images === 'string' ? JSON.parse(b.images) : (b.images || []); } catch(e) {}
    const imgUrl = images[0] || b.image || "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=200";

    html += `
      <a href="/enquiry-bike-details.html?id=${b.id}" class="list-group-item list-group-item-action d-flex align-items-center justify-content-between px-0 py-2 border-0">
        <div class="d-flex align-items-center gap-3">
          <img src="${imgUrl}" class="rounded-3" width="50" height="38" style="object-fit:cover;">
          <div>
            <h6 class="mb-0 small fw-bold text-dark">${b.title}</h6>
            <small class="text-success fw-bold">₹${Number(b.selling_price || b.price).toLocaleString()}</small>
          </div>
        </div>
        <span class="btn btn-sm btn-light py-0 px-2 text-muted"><i class="fa-solid fa-chevron-right small"></i></span>
      </a>`;
  });
  html += `</div>`;
  container.innerHTML = html;
}

/**
 * Save user profile updates
 */
async function handleSaveProfile(event) {
  event.preventDefault();
  const token = sessionStorage.getItem("token");
  const name = document.getElementById("inputProfileName").value.trim();
  const phone = document.getElementById("inputProfilePhone").value.trim();

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token
      },
      body: JSON.stringify({ name, phone })
    });

    const data = await res.json();
    if (data.success) {
      currentUser.name = name;
      currentUser.phone = phone;
      renderUserData(currentUser);

      Swal.fire({
        icon: "success",
        title: "Profile Updated",
        text: "Your profile information was updated successfully.",
        confirmButtonColor: "#10b981"
      });
    } else {
      throw new Error(data.message || "Failed to update profile.");
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Load user's own bike listings
 */
async function loadUserListings() {
  const token = sessionStorage.getItem("token");
  const container = document.getElementById("userListingsContainer");
  container.innerHTML = `<div class="text-center py-4 text-muted col-12"><div class="spinner-border spinner-border-sm text-success me-2"></div>Loading listings...</div>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/listings`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    if (!data.success || !data.listings || data.listings.length === 0) {
      container.innerHTML = `
        <div class="text-center py-5 text-muted col-12">
          <i class="fa-solid fa-motorcycle fa-3x mb-3 text-muted-subtle"></i>
          <h5>No bikes listed yet</h5>
          <p class="text-muted">Start selling today! Listings are reviewed and published by SMR Motors.</p>
          <button class="btn btn-success fw-semibold" onclick="openAddBikeModal()"><i class="fa-solid fa-plus me-1"></i> Add Your First Bike</button>
        </div>`;
      return;
    }

    let html = "";
    data.listings.forEach(b => {
      let images = [];
      try { images = typeof b.images === 'string' ? JSON.parse(b.images) : (b.images || []); } catch(e) {}
      const imgUrl = images[0] || b.image || "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=300";

      let statusBadge = "";
      if (b.status === "approved") {
        statusBadge = `<span class="badge bg-success"><i class="fa-solid fa-check-circle me-1"></i> Approved & Active</span>`;
      } else if (b.status === "rejected") {
        statusBadge = `<span class="badge bg-danger"><i class="fa-solid fa-circle-xmark me-1"></i> Rejected</span>`;
      } else if (b.status === "soldout") {
        statusBadge = `<span class="badge bg-secondary"><i class="fa-solid fa-tag me-1"></i> Sold Out</span>`;
      } else {
        statusBadge = `<span class="badge bg-warning text-dark"><i class="fa-solid fa-clock me-1"></i> Pending Approval</span>`;
      }

      html += `
        <div class="col-md-6 col-xl-4">
          <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden">
            <div class="position-relative">
              <img src="${imgUrl}" class="card-img-top" style="height: 190px; object-fit: cover;">
              <div class="position-absolute top-0 start-0 m-2">${statusBadge}</div>
            </div>
            <div class="card-body p-3">
              <h5 class="fw-bold mb-1">${b.title}</h5>
              <p class="text-success fw-bold fs-5 mb-2">₹${Number(b.price).toLocaleString()}</p>
              
              <div class="small text-muted mb-2">
                <div><i class="fa-solid fa-calendar me-1"></i> Year: ${b.year || "N/A"} • <i class="fa-solid fa-gauge me-1"></i> ${b.kilometers_driven || 0} kms</div>
                <div><i class="fa-solid fa-hashtag me-1"></i> Reg: ${b.vehicle_number || "N/A"}</div>
              </div>

              ${b.status === 'rejected' && b.rejection_reason ? `
                <div class="alert alert-danger py-2 px-3 small mb-2">
                  <strong>Rejection Reason:</strong> ${b.rejection_reason}
                </div>` : ''}

              <div class="d-flex gap-2 mt-3 pt-2 border-top">
                <button class="btn btn-sm btn-outline-primary flex-fill" onclick="openEditBikeModal(${b.id})">
                  <i class="fa-solid fa-pen-to-square me-1"></i> Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteUserBike(${b.id})">
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>`;
    });

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="col-12 alert alert-danger">Error loading listings: ${err.message}</div>`;
  }
}

/**
 * Handle image selection & thumbnail preview
 */
function handleImageSelection(event) {
  const files = Array.from(event.target.files);
  selectedBikeImages = files.slice(0, 6);
  renderImagePreviews();
}

function renderImagePreviews() {
  const previewRow = document.getElementById("imagePreviewRow");
  previewRow.innerHTML = "";

  selectedBikeImages.forEach((file, index) => {
    const reader = new FileReader();
    reader.onload = function (e) {
      const col = document.createElement("div");
      col.className = "col-4 col-sm-2";
      col.innerHTML = `
        <div class="preview-thumbnail">
          <img src="${e.target.result}" alt="Preview">
          <button type="button" class="preview-remove-btn" onclick="removeSelectedImage(${index})">&times;</button>
        </div>`;
      previewRow.appendChild(col);
    };
    reader.readAsDataURL(file);
  });
}

function removeSelectedImage(index) {
  selectedBikeImages.splice(index, 1);
  renderImagePreviews();
}

function openAddBikeModal() {
  document.getElementById("addBikeModalTitle").textContent = "List a Bike for Sale";
  document.getElementById("addBikeForm").reset();
  document.getElementById("editBikeId").value = "";
  document.getElementById("imagePreviewRow").innerHTML = "";
  selectedBikeImages = [];
  const modal = new bootstrap.Modal(document.getElementById("addBikeModal"));
  modal.show();
}

async function openEditBikeModal(bikeId) {
  const token = sessionStorage.getItem("token");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/bikes/${bikeId}`);
    const data = await res.json();
    const bike = data.bike || data;

    document.getElementById("addBikeModalTitle").textContent = "Edit Bike Listing";
    document.getElementById("editBikeId").value = bike.id;
    document.getElementById("bikeTitle").value = bike.title || bike.listingTitle || "";
    document.getElementById("bikeBrand").value = bike.brand || bike.makedFrom || "Other";
    document.getElementById("bikeModel").value = bike.model || bike.bikeModel || "";
    document.getElementById("bikeYear").value = bike.year || bike.bikeBuyingYear || 2022;
    document.getElementById("bikePrice").value = bike.price || bike.bikePrice || "";
    document.getElementById("bikeKms").value = bike.kilometers_driven || bike.bikeKms || "";
    document.getElementById("bikeVehicleNum").value = bike.vehicle_number || bike.vehicleNumber || "";
    document.getElementById("bikeCondition").value = bike.bike_condition || bike.bikeCondition || "Good";
    document.getElementById("bikeColor").value = bike.bike_color || bike.bikeColor || "";
    document.getElementById("bikeEngineCC").value = bike.engine_cc || bike.bikeEngineCC || "";
    document.getElementById("bikeInsurance").value = bike.insurance || "No";
    document.getElementById("bikeLocation").value = bike.location || bike.bikeLocation || "";
    document.getElementById("bikeDescription").value = bike.description || "";

    const modal = new bootstrap.Modal(document.getElementById("addBikeModal"));
    modal.show();
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: "Failed to load bike details." });
  }
}

/**
 * Submit Bike (Add or Edit) with Multipart Form Data
 */
async function handleBikeSubmit(event) {
  event.preventDefault();
  const token = sessionStorage.getItem("token");
  const editId = document.getElementById("editBikeId").value;
  const submitBtn = document.getElementById("submitBikeBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Submitting...";

  const formData = new FormData();
  formData.append("title", document.getElementById("bikeTitle").value);
  formData.append("brand", document.getElementById("bikeBrand").value);
  formData.append("model", document.getElementById("bikeModel").value);
  formData.append("year", document.getElementById("bikeYear").value);
  formData.append("price", document.getElementById("bikePrice").value);
  formData.append("kilometers_driven", document.getElementById("bikeKms").value);
  formData.append("vehicle_number", document.getElementById("bikeVehicleNum").value);
  formData.append("bike_condition", document.getElementById("bikeCondition").value);
  formData.append("bike_color", document.getElementById("bikeColor").value);
  formData.append("engine_cc", document.getElementById("bikeEngineCC").value);
  formData.append("insurance", document.getElementById("bikeInsurance").value);
  formData.append("location", document.getElementById("bikeLocation").value);
  formData.append("description", document.getElementById("bikeDescription").value);

  // Append images
  selectedBikeImages.forEach(file => {
    formData.append("images", file);
  });

  const url = editId ? `${window.API.BASE_URL}/api/bikes/${editId}` : `${window.API.BASE_URL}/api/bikes`;
  const method = editId ? "PUT" : "POST";

  try {
    let res;
    if (editId) {
      // Put sends JSON
      const jsonBody = {
        title: document.getElementById("bikeTitle").value,
        price: document.getElementById("bikePrice").value,
        kilometers_driven: document.getElementById("bikeKms").value,
        description: document.getElementById("bikeDescription").value
      };
      res = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify(jsonBody)
      });
    } else {
      res = await fetch(url, {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
        body: formData
      });
    }

    const result = await res.json();
    if (result.success) {
      bootstrap.Modal.getInstance(document.getElementById("addBikeModal")).hide();
      Swal.fire({
        icon: "success",
        title: editId ? "Bike Updated" : "Listing Submitted!",
        text: editId ? "Listing details updated." : "Your bike listing was submitted and will be published after administrator approval.",
        confirmButtonColor: "#10b981"
      });
      loadUserListings();
      loadDashboardData();
    } else {
      throw new Error(result.message || "Failed to save bike.");
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Submission Failed", text: err.message });
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Listing";
  }
}

/**
 * Delete User Bike
 */
async function deleteUserBike(bikeId) {
  const confirm = await Swal.fire({
    title: "Delete Listing?",
    text: "Are you sure you want to remove this bike listing? This action cannot be undone.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#ef4444",
    cancelButtonColor: "#64748b",
    confirmButtonText: "Yes, delete it"
  });

  if (!confirm.isConfirmed) return;

  const token = sessionStorage.getItem("token");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/bikes/${bikeId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token }
    });
    const result = await res.json();

    if (result.success) {
      Swal.fire({ icon: "success", title: "Deleted", text: "Listing removed successfully.", timer: 1500, showConfirmButton: false });
      loadUserListings();
      loadDashboardData();
    } else {
      throw new Error(result.message);
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Load user's enquiries
 */
async function loadUserEnquiries() {
  const token = sessionStorage.getItem("token");
  const container = document.getElementById("userEnquiriesContainer");
  container.innerHTML = `<div class="text-center py-4 text-muted col-12"><div class="spinner-border spinner-border-sm text-info me-2"></div>Loading enquiries...</div>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/enquiries`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    if (!data.success || !data.enquiries || data.enquiries.length === 0) {
      container.innerHTML = `
        <div class="text-center py-5 text-muted col-12">
          <i class="fa-regular fa-comments fa-3x mb-3 text-muted-subtle"></i>
          <h5>No enquiries found</h5>
          <p class="text-muted">You haven't submitted any enquiries yet. Browse bikes and submit an enquiry!</p>
          <a href="/#Products" class="btn btn-outline-primary">Browse Marketplace</a>
        </div>`;
      return;
    }

    let html = "";
    data.enquiries.forEach(e => {
      const statusBadge = e.status === "completed"
        ? `<span class="badge bg-success">Completed</span>`
        : (e.status === "in_progress"
            ? `<span class="badge bg-primary">In Progress</span>`
            : `<span class="badge bg-warning text-dark">Pending Review</span>`);

      html += `
        <div class="col-md-6 col-xl-4">
          <div class="card h-100 border-0 shadow-sm rounded-4 p-3">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="small text-muted">${new Date(e.created_at).toLocaleDateString()}</span>
              ${statusBadge}
            </div>
            <h6 class="fw-bold mb-1">${e.bike_title || "Bike Enquiry"}</h6>
            <p class="small text-muted mb-2">Ref ID: #${e.id} • ${e.bike_brand || ""} ${e.bike_model || ""}</p>
            <div class="p-2 bg-light rounded-3 small mb-3">
              <strong>Your Note:</strong> "${e.message || "Enquired about price & test drive availability."}"
            </div>
            ${e.admin_reply ? `
              <div class="p-2 bg-success-subtle text-success rounded-3 small mb-2">
                <strong>SMR Motors Reply:</strong> "${e.admin_reply}"
              </div>` : ''}
            <div class="mt-auto pt-2 border-top d-flex justify-content-between align-items-center">
              <a href="/enquiry-bike-details.html?id=${e.bike_id}" class="btn btn-sm btn-outline-secondary">View Bike</a>
              <small class="text-muted">Contact: ${e.phone}</small>
            </div>
          </div>
        </div>`;
    });

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="col-12 alert alert-danger">Error: ${err.message}</div>`;
  }
}

/**
 * Load user's saved favorites
 */
async function loadUserFavorites() {
  const token = sessionStorage.getItem("token");
  const container = document.getElementById("userFavoritesContainer");
  container.innerHTML = `<div class="text-center py-4 text-muted col-12"><div class="spinner-border spinner-border-sm text-danger me-2"></div>Loading favorites...</div>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/favorites`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    if (!data.success || !data.favorites || data.favorites.length === 0) {
      container.innerHTML = `
        <div class="text-center py-5 text-muted col-12">
          <i class="fa-regular fa-heart fa-3x mb-3 text-muted-subtle"></i>
          <h5>Your wishlist is empty</h5>
          <p class="text-muted">Save your favorite motorcycles while browsing the marketplace!</p>
          <a href="/#Products" class="btn btn-outline-success">Browse Bikes</a>
        </div>`;
      return;
    }

    let html = "";
    data.favorites.forEach(b => {
      let images = [];
      try { images = typeof b.images === 'string' ? JSON.parse(b.images) : (b.images || []); } catch(e) {}
      const imgUrl = images[0] || b.image || "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=300";

      html += `
        <div class="col-md-6 col-xl-4">
          <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden">
            <img src="${imgUrl}" class="card-img-top" style="height: 180px; object-fit: cover;">
            <div class="card-body p-3">
              <h5 class="fw-bold mb-1">${b.title}</h5>
              <p class="text-success fw-bold fs-5 mb-2">₹${Number(b.selling_price || b.price).toLocaleString()}</p>
              <p class="small text-muted mb-3">${b.brand} • ${b.kilometers_driven || 0} kms • ${b.location || "Kelambakkam"}</p>
              <div class="d-flex gap-2">
                <a href="/enquiry-bike-details.html?id=${b.id}" class="btn btn-sm btn-success flex-fill">View Details</a>
                <button class="btn btn-sm btn-outline-danger" onclick="removeFavorite(${b.id})" title="Remove"><i class="fa-solid fa-trash"></i></button>
              </div>
            </div>
          </div>
        </div>`;
    });

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="col-12 alert alert-danger">Error: ${err.message}</div>`;
  }
}

async function removeFavorite(bikeId) {
  const token = sessionStorage.getItem("token");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/users/favorites/${bikeId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    if (data.success) {
      loadUserFavorites();
      loadDashboardData();
    }
  } catch (err) {
    console.error("Remove favorite error:", err);
  }
}

/**
 * Handle Logout
 */
function handleLogout() {
  Swal.fire({
    title: "Sign Out",
    text: "Are you sure you want to log out of SMR Motors?",
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#ef4444",
    confirmButtonText: "Yes, Sign Out"
  }).then(result => {
    if (result.isConfirmed) {
      sessionStorage.removeItem("token");
      sessionStorage.removeItem("user");
      window.location.href = "/";
    }
  });
}
