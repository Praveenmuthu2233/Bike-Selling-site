/**
 * Modern Admin Console Script - SMR Motors
 * Full administration: Metrics, Bike approvals, Users, Enquiries, Contact, Audit Logs, Settings.
 */

let allAdminBikes = [];
let allAdminUsers = [];

document.addEventListener("DOMContentLoaded", function () {
  checkAdminSession();
});

/**
 * Check if admin is currently logged in
 */
async function checkAdminSession() {
  const token = sessionStorage.getItem("adminToken");
  const loginSection = document.getElementById("adminLoginSection");
  const appSection = document.getElementById("adminAppSection");

  if (!token) {
    loginSection.classList.remove("d-none");
    appSection.classList.add("d-none");
    return;
  }

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/dashboard`, {
      headers: { Authorization: "Bearer " + token }
    });

    if (res.ok) {
      const data = await res.json();
      loginSection.classList.add("d-none");
      appSection.classList.remove("d-none");

      const adminUser = sessionStorage.getItem("adminUsername") || "Administrator";
      document.getElementById("currentAdminName").textContent = adminUser.toUpperCase();

      renderDashboardMetrics(data);
      loadAdminBikes();
    } else {
      sessionStorage.removeItem("adminToken");
      loginSection.classList.remove("d-none");
      appSection.classList.add("d-none");
    }
  } catch (err) {
    console.error("Admin session check error:", err);
  }
}

/**
 * Handle Admin Login Submit
 */
async function handleAdminLoginSubmit(event) {
  event.preventDefault();
  const username = document.getElementById("adminUsername").value.trim();
  const password = document.getElementById("adminPassword").value.trim();
  const loginBtn = document.getElementById("adminLoginBtn");

  loginBtn.disabled = true;
  loginBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Authenticating...`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (data.success && data.token) {
      sessionStorage.setItem("adminToken", data.token);
      sessionStorage.setItem("adminUsername", data.admin?.username || username);

      Swal.fire({
        icon: "success",
        title: "Access Granted",
        text: `Welcome to SMR Motors Management Console, ${data.admin?.username || username}!`,
        confirmButtonColor: "#10b981",
        timer: 1500,
        showConfirmButton: false
      }).then(() => {
        checkAdminSession();
      });
    } else {
      throw new Error(data.message || "Invalid credentials.");
    }
  } catch (err) {
    Swal.fire({
      icon: "error",
      title: "Login Failed",
      text: err.message,
      confirmButtonColor: "#ef4444"
    });
  } finally {
    loginBtn.disabled = false;
    loginBtn.innerHTML = `<i class="fa-solid fa-right-to-bracket me-1"></i> Sign In to Admin Console`;
  }
}

/**
 * Switch tabs in the admin console
 */
function switchAdminTab(tabName) {
  document.querySelectorAll(".admin-tab").forEach(tab => tab.classList.remove("active"));
  document.querySelectorAll(".admin-nav-pills .nav-link").forEach(btn => btn.classList.remove("active"));

  const targetTab = document.getElementById(`adm-${tabName}`);
  const targetBtn = document.getElementById(`adm-${tabName}-btn`);

  if (targetTab) targetTab.classList.add("active");
  if (targetBtn) targetBtn.classList.add("active");

  if (tabName === "overview") loadAdminDashboardData();
  if (tabName === "bikes") loadAdminBikes();
  if (tabName === "users") loadAdminUsers();
  if (tabName === "enquiries") loadAdminEnquiries();
  if (tabName === "messages") loadAdminMessages();
  if (tabName === "categories") loadAdminCategories();
  if (tabName === "audit") loadAdminAuditLogs();
}

/**
 * Load complete admin dashboard statistics
 */
async function loadAdminDashboardData() {
  const token = sessionStorage.getItem("adminToken");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/dashboard`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    if (data.success) {
      renderDashboardMetrics(data);
    }
  } catch (e) {
    console.error("Dashboard error:", e);
  }
}

function renderDashboardMetrics(data) {
  const stats = data.stats || {};
  document.getElementById("mTotalUsers").textContent = stats.totalUsers || 0;
  document.getElementById("mActiveListings").textContent = stats.activeListings || 0;
  document.getElementById("mPendingApprovals").textContent = stats.pendingApprovals || 0;
  document.getElementById("mTotalEnquiries").textContent = stats.totalEnquiries || 0;

  // Header badges
  const pendingCount = stats.pendingApprovals || 0;
  document.getElementById("pendingAlertBadge").textContent = `${pendingCount} Pending Approvals`;
  document.getElementById("sidePendingCount").textContent = pendingCount;
  document.getElementById("sideMsgCount").textContent = stats.newContactMessages || 0;

  // Render recent registrations
  const regContainer = document.getElementById("overviewRegistrationsContainer");
  const users = data.recentRegistrations || [];
  if (users.length === 0) {
    regContainer.innerHTML = `<p class="text-muted text-center py-3">No recent user registrations.</p>`;
  } else {
    let html = `<ul class="list-group list-group-flush">`;
    users.forEach(u => {
      const avatar = u.profile_image || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=80";
      html += `
        <li class="list-group-item d-flex align-items-center justify-content-between px-0 py-2 border-0">
          <div class="d-flex align-items-center gap-2">
            <img src="${avatar}" class="rounded-circle" width="36" height="36" style="object-fit:cover;">
            <div>
              <div class="fw-semibold small">${u.name}</div>
              <small class="text-muted">${u.email}</small>
            </div>
          </div>
          <small class="text-muted">${new Date(u.created_at).toLocaleDateString()}</small>
        </li>`;
    });
    html += `</ul>`;
    regContainer.innerHTML = html;
  }
}

/**
 * Load all bikes for admin
 */
async function loadAdminBikes() {
  const token = sessionStorage.getItem("adminToken");
  const tbody = document.getElementById("adminBikesTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted"><div class="spinner-border spinner-border-sm text-dark me-2"></div>Loading bikes...</td></tr>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/bikes?status=all`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    allAdminBikes = data.bikes || [];
    filterAdminBikes();
    renderOverviewPendingQueue(allAdminBikes.filter(b => b.status === "pending"));
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Error loading bikes: ${err.message}</td></tr>`;
  }
}

function renderOverviewPendingQueue(pendingBikes) {
  const container = document.getElementById("overviewPendingContainer");
  if (!pendingBikes || pendingBikes.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted"><i class="fa-solid fa-circle-check fa-2x text-success mb-2"></i><p>All listings reviewed! No pending submissions.</p></div>`;
    return;
  }

  let html = `<table class="table table-sm align-middle"><thead><tr><th>Bike</th><th>Seller</th><th>Expected Price</th><th>Actions</th></tr></thead><tbody>`;
  pendingBikes.slice(0, 5).forEach(b => {
    html += `
      <tr>
        <td>
          <div class="fw-bold small">${b.title}</div>
          <small class="text-muted">${b.brand} • ${b.vehicle_number || "No Reg"}</small>
        </td>
        <td>
          <div class="small">${b.seller_name || "User"}</div>
          <small class="text-muted">${b.seller_phone || ""}</small>
        </td>
        <td class="text-success fw-bold">₹${Number(b.price).toLocaleString()}</td>
        <td>
          <button class="btn btn-sm btn-success py-0 px-2" onclick="approveBike(${b.id})">Approve</button>
          <button class="btn btn-sm btn-outline-danger py-0 px-2" onclick="openRejectModal(${b.id})">Reject</button>
        </td>
      </tr>`;
  });
  html += `</tbody></table>`;
  container.innerHTML = html;
}

function filterAdminBikes() {
  const search = document.getElementById("adminBikeSearch").value.toLowerCase();
  const statusFilter = document.getElementById("adminBikeStatusFilter").value;
  const brandFilter = document.getElementById("adminBikeBrandFilter").value;

  let filtered = allAdminBikes.filter(b => {
    const matchesSearch = (b.title || "").toLowerCase().includes(search) || (b.vehicle_number || "").toLowerCase().includes(search) || (b.seller_name || "").toLowerCase().includes(search);
    const matchesStatus = statusFilter === "all" || b.status === statusFilter;
    const matchesBrand = brandFilter === "all" || b.brand === brandFilter;
    return matchesSearch && matchesStatus && matchesBrand;
  });

  renderAdminBikesTable(filtered);
}

function filterAdminBikesByStatus(status) {
  document.getElementById("adminBikeStatusFilter").value = status;
  filterAdminBikes();
}

function renderAdminBikesTable(bikes) {
  const tbody = document.getElementById("adminBikesTableBody");
  if (!bikes || bikes.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-5 text-muted"><p class="mb-0">No bikes match the selected criteria.</p></td></tr>`;
    return;
  }

  let html = "";
  bikes.forEach(b => {
    const imgUrl = b.images?.[0] || b.image || "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=200";
    let statusBadge = "";
    if (b.status === "approved") statusBadge = `<span class="badge bg-success">Approved</span>`;
    else if (b.status === "rejected") statusBadge = `<span class="badge bg-danger">Rejected</span>`;
    else if (b.status === "soldout") statusBadge = `<span class="badge bg-secondary">Sold Out</span>`;
    else statusBadge = `<span class="badge bg-warning text-dark">Pending</span>`;

    html += `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-3">
            <img src="${imgUrl}" class="rounded-3" width="60" height="45" style="object-fit:cover;">
            <div>
              <div class="fw-bold">${b.title}</div>
              <small class="text-muted">${b.brand} ${b.model} • Reg: ${b.vehicle_number || "N/A"}</small>
            </div>
          </div>
        </td>
        <td>
          <div class="fw-semibold small">${b.seller_name || "Individual"}</div>
          <small class="text-muted"><i class="fa-solid fa-phone me-1"></i>${b.seller_phone || "N/A"}</small>
        </td>
        <td>
          <div class="text-muted small">Buy: ₹${Number(b.price).toLocaleString()}</div>
          <div class="text-success fw-bold">Fixing: ₹${Number(b.selling_price || b.price).toLocaleString()}</div>
        </td>
        <td>${statusBadge}</td>
        <td><small class="text-muted">${new Date(b.created_at).toLocaleDateString()}</small></td>
        <td class="text-end">
          <div class="btn-group btn-group-sm">
            ${b.status === 'pending' ? `
              <button class="btn btn-success" onclick="approveBike(${b.id})" title="Approve"><i class="fa-solid fa-check"></i></button>
              <button class="btn btn-danger" onclick="openRejectModal(${b.id})" title="Reject"><i class="fa-solid fa-xmark"></i></button>
            ` : ''}
            <button class="btn btn-outline-secondary" onclick="openPriceModal(${b.id}, ${b.selling_price || b.price})" title="Update Price"><i class="fa-solid fa-tag"></i></button>
            <button class="btn btn-outline-dark" onclick="markBikeSoldOut(${b.id})" title="Mark Sold Out"><i class="fa-solid fa-ban"></i></button>
            <button class="btn btn-outline-danger" onclick="deleteBikeAdmin(${b.id})" title="Delete"><i class="fa-solid fa-trash"></i></button>
          </div>
        </td>
      </tr>`;
  });

  tbody.innerHTML = html;
}

/**
 * Approve Bike
 */
async function approveBike(bikeId) {
  const token = sessionStorage.getItem("adminToken");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/bikes/${bikeId}/approve`, {
      method: "PUT",
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    if (data.success) {
      Swal.fire({ icon: "success", title: "Approved", text: "Bike published to marketplace.", timer: 1200, showConfirmButton: false });
      loadAdminBikes();
      loadAdminDashboardData();
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Reject Bike
 */
function openRejectModal(bikeId) {
  document.getElementById("rejectBikeId").value = bikeId;
  document.getElementById("rejectionReasonInput").value = "";
  new bootstrap.Modal(document.getElementById("rejectBikeModal")).show();
}

async function confirmRejectBike() {
  const bikeId = document.getElementById("rejectBikeId").value;
  const reason = document.getElementById("rejectionReasonInput").value.trim();
  const token = sessionStorage.getItem("adminToken");

  if (!reason) {
    Swal.fire({ icon: "warning", title: "Required", text: "Please enter a rejection reason." });
    return;
  }

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/bikes/${bikeId}/reject`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById("rejectBikeModal")).hide();
      Swal.fire({ icon: "info", title: "Rejected", text: "Listing marked as rejected.", timer: 1200, showConfirmButton: false });
      loadAdminBikes();
      loadAdminDashboardData();
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Update Price
 */
function openPriceModal(bikeId, currentPrice) {
  document.getElementById("priceBikeId").value = bikeId;
  document.getElementById("newSellingPriceInput").value = currentPrice;
  new bootstrap.Modal(document.getElementById("priceBikeModal")).show();
}

async function confirmUpdatePrice() {
  const bikeId = document.getElementById("priceBikeId").value;
  const newPrice = document.getElementById("newSellingPriceInput").value;
  const token = sessionStorage.getItem("adminToken");

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/bikes/${bikeId}/price`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ newPrice })
    });
    const data = await res.json();
    if (data.success) {
      bootstrap.Modal.getInstance(document.getElementById("priceBikeModal")).hide();
      Swal.fire({ icon: "success", title: "Price Updated", timer: 1200, showConfirmButton: false });
      loadAdminBikes();
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Mark Sold Out
 */
async function markBikeSoldOut(bikeId) {
  const token = sessionStorage.getItem("adminToken");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/bikes/${bikeId}/soldout`, {
      method: "PUT",
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    if (data.success) {
      Swal.fire({ icon: "success", title: "Marked Sold Out", timer: 1200, showConfirmButton: false });
      loadAdminBikes();
      loadAdminDashboardData();
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Delete Bike Admin
 */
async function deleteBikeAdmin(bikeId) {
  const confirm = await Swal.fire({
    title: "Delete Listing?",
    text: "Are you sure you want to delete this bike permanently?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#ef4444",
    confirmButtonText: "Delete"
  });
  if (!confirm.isConfirmed) return;

  const token = sessionStorage.getItem("adminToken");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/bikes/${bikeId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    if (data.success) {
      Swal.fire({ icon: "success", title: "Deleted", timer: 1200, showConfirmButton: false });
      loadAdminBikes();
      loadAdminDashboardData();
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Load Users
 */
async function loadAdminUsers() {
  const token = sessionStorage.getItem("adminToken");
  const tbody = document.getElementById("adminUsersTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Loading users...</td></tr>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/users`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    allAdminUsers = data.users || [];
    filterAdminUsers();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Error: ${err.message}</td></tr>`;
  }
}

function filterAdminUsers() {
  const q = document.getElementById("adminUserSearch").value.toLowerCase();
  const filtered = allAdminUsers.filter(u =>
    (u.name || "").toLowerCase().includes(q) ||
    (u.email || "").toLowerCase().includes(q) ||
    (u.phone || "").toLowerCase().includes(q)
  );

  const tbody = document.getElementById("adminUsersTableBody");
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No users found.</td></tr>`;
    return;
  }

  let html = "";
  filtered.forEach(u => {
    const avatar = u.profile_image || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=80";
    html += `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-2">
            <img src="${avatar}" class="rounded-circle" width="34" height="34" style="object-fit:cover;">
            <span class="fw-semibold">${u.name}</span>
          </div>
        </td>
        <td>${u.email}</td>
        <td>${u.phone || '<span class="text-muted">Not provided</span>'}</td>
        <td><span class="badge bg-primary-subtle text-primary">${u.role || "user"}</span></td>
        <td><small class="text-muted">${new Date(u.created_at).toLocaleDateString()}</small></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-danger" onclick="deleteUserAdmin(${u.id})"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`;
  });
  tbody.innerHTML = html;
}

async function deleteUserAdmin(userId) {
  const confirm = await Swal.fire({
    title: "Delete User?",
    text: "Delete this user account?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#ef4444"
  });
  if (!confirm.isConfirmed) return;

  const token = sessionStorage.getItem("adminToken");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/users/${userId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    if (data.success) {
      loadAdminUsers();
      loadAdminDashboardData();
    }
  } catch (e) {
    Swal.fire({ icon: "error", title: "Error", text: e.message });
  }
}

/**
 * Load Enquiries
 */
async function loadAdminEnquiries() {
  const token = sessionStorage.getItem("adminToken");
  const statusFilter = document.getElementById("adminEnquiryStatusFilter").value;
  const tbody = document.getElementById("adminEnquiriesTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Loading enquiries...</td></tr>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/enquiries?status=${statusFilter}`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    const list = data.enquiries || [];

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No enquiries found.</td></tr>`;
      return;
    }

    let html = "";
    list.forEach(e => {
      let badge = "";
      if (e.status === "completed") badge = `<span class="badge bg-success">Completed</span>`;
      else if (e.status === "in_progress") badge = `<span class="badge bg-primary">In Progress</span>`;
      else badge = `<span class="badge bg-warning text-dark">Pending</span>`;

      html += `
        <tr>
          <td>
            <div class="fw-semibold">${e.customerName || e.name}</div>
            <small class="text-muted"><i class="fa-solid fa-phone me-1"></i>${e.mobile || e.phone}</small>
          </td>
          <td>
            <div class="fw-bold small">${e.listingTitle || "Bike #" + e.bike_id}</div>
          </td>
          <td><small>${e.message || "No message"}</small></td>
          <td>${badge}</td>
          <td><small class="text-muted">${new Date(e.created_at).toLocaleDateString()}</small></td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-primary me-1" onclick="openReplyEnquiryModal(${e.id}, '${e.status}')">Status/Reply</button>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteEnquiryAdmin(${e.id})"><i class="fa-solid fa-trash"></i></button>
          </td>
        </tr>`;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Error: ${err.message}</td></tr>`;
  }
}

function openReplyEnquiryModal(enquiryId, currentStatus) {
  document.getElementById("replyEnquiryId").value = enquiryId;
  document.getElementById("replyStatusSelect").value = currentStatus || "pending";
  document.getElementById("replyMessageText").value = "";
  new bootstrap.Modal(document.getElementById("replyEnquiryModal")).show();
}

async function confirmSaveEnquiryReply() {
  const enquiryId = document.getElementById("replyEnquiryId").value;
  const status = document.getElementById("replyStatusSelect").value;
  const message = document.getElementById("replyMessageText").value.trim();
  const token = sessionStorage.getItem("adminToken");

  try {
    await fetch(`${window.API.BASE_URL}/api/enquiries/${enquiryId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ status })
    });

    if (message) {
      await fetch(`${window.API.BASE_URL}/api/enquiries/${enquiryId}/message`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify({ admin_reply: message })
      });
    }

    bootstrap.Modal.getInstance(document.getElementById("replyEnquiryModal")).hide();
    Swal.fire({ icon: "success", title: "Updated", timer: 1200, showConfirmButton: false });
    loadAdminEnquiries();
  } catch (e) {
    Swal.fire({ icon: "error", title: "Error", text: e.message });
  }
}

async function deleteEnquiryAdmin(enquiryId) {
  const confirm = await Swal.fire({ title: "Delete Enquiry?", icon: "warning", showCancelButton: true });
  if (!confirm.isConfirmed) return;

  const token = sessionStorage.getItem("adminToken");
  try {
    await fetch(`${window.API.BASE_URL}/api/enquiries/${enquiryId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token }
    });
    loadAdminEnquiries();
    loadAdminDashboardData();
  } catch (e) {}
}

/**
 * Load Contact Messages
 */
async function loadAdminMessages() {
  const token = sessionStorage.getItem("adminToken");
  const tbody = document.getElementById("adminMessagesTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Loading messages...</td></tr>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/messages`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    const messages = data.messages || [];

    if (messages.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No messages received yet.</td></tr>`;
      return;
    }

    let html = "";
    messages.forEach(m => {
      const isUnread = m.status === "unread";
      html += `
        <tr class="${isUnread ? 'table-warning' : ''}">
          <td class="fw-semibold">${m.name}</td>
          <td>
            <div>${m.email}</div>
            <small class="text-muted">${m.phone || ""}</small>
          </td>
          <td><small>${m.message}</small></td>
          <td><span class="badge ${isUnread ? 'bg-danger' : 'bg-light text-muted'}">${m.status}</span></td>
          <td><small class="text-muted">${new Date(m.created_at).toLocaleDateString()}</small></td>
          <td class="text-end">
            ${isUnread ? `<button class="btn btn-sm btn-outline-success me-1" onclick="markMessageRead(${m.id})">Mark Read</button>` : ''}
            <button class="btn btn-sm btn-outline-danger" onclick="deleteMessageAdmin(${m.id})"><i class="fa-solid fa-trash"></i></button>
          </td>
        </tr>`;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Error: ${err.message}</td></tr>`;
  }
}

async function markMessageRead(msgId) {
  const token = sessionStorage.getItem("adminToken");
  try {
    await fetch(`${window.API.BASE_URL}/api/admin/messages/${msgId}/read`, {
      method: "PUT",
      headers: { Authorization: "Bearer " + token }
    });
    loadAdminMessages();
    loadAdminDashboardData();
  } catch (e) {}
}

async function deleteMessageAdmin(msgId) {
  const token = sessionStorage.getItem("adminToken");
  try {
    await fetch(`${window.API.BASE_URL}/api/admin/messages/${msgId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token }
    });
    loadAdminMessages();
    loadAdminDashboardData();
  } catch (e) {}
}

/**
 * Load Categories
 */
async function loadAdminCategories() {
  const tbody = document.getElementById("adminCategoriesTableBody");
  tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Loading categories...</td></tr>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/categories`);
    const data = await res.json();
    const categories = data.categories || [];

    let html = "";
    categories.forEach(c => {
      html += `
        <tr>
          <td class="fw-bold">${c.category_name}</td>
          <td>${c.description || "-"}</td>
          <td><span class="badge bg-success">${c.status || 'active'}</span></td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-danger" onclick="deleteCategoryAdmin(${c.id})"><i class="fa-solid fa-trash"></i></button>
          </td>
        </tr>`;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-4">Error: ${err.message}</td></tr>`;
  }
}

async function openAddCategoryModal() {
  const { value: formValues } = await Swal.fire({
    title: 'Add New Category',
    html:
      '<input id="swal-input1" class="swal2-input" placeholder="Category Name">' +
      '<input id="swal-input2" class="swal2-input" placeholder="Description">',
    focusConfirm: false,
    showCancelButton: true,
    preConfirm: () => {
      return [
        document.getElementById('swal-input1').value,
        document.getElementById('swal-input2').value
      ];
    }
  });

  if (formValues && formValues[0]) {
    const token = sessionStorage.getItem("adminToken");
    await fetch(`${window.API.BASE_URL}/api/categories`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ category_name: formValues[0], description: formValues[1] })
    });
    loadAdminCategories();
  }
}

async function deleteCategoryAdmin(id) {
  const token = sessionStorage.getItem("adminToken");
  await fetch(`${window.API.BASE_URL}/api/categories/${id}`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token }
  });
  loadAdminCategories();
}

/**
 * Load Audit Logs
 */
async function loadAdminAuditLogs() {
  const token = sessionStorage.getItem("adminToken");
  const tbody = document.getElementById("adminAuditTableBody");
  tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Loading logs...</td></tr>`;

  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/audit-logs`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    const logs = data.logs || [];

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No audit logs recorded yet.</td></tr>`;
      return;
    }

    let html = "";
    logs.forEach(l => {
      html += `
        <tr>
          <td><small class="text-muted">${new Date(l.created_at).toLocaleString()}</small></td>
          <td class="fw-semibold">${l.username || "admin"}</td>
          <td><span class="badge bg-dark">${l.action}</span></td>
          <td><small class="text-muted font-monospace">${l.details || ""}</small></td>
          <td><small>${l.ip_address || "127.0.0.1"}</small></td>
        </tr>`;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">Error: ${err.message}</td></tr>`;
  }
}

/**
 * Change Admin Password
 */
async function handleAdminChangePassword(event) {
  event.preventDefault();
  const currentPassword = document.getElementById("adminCurrentPass").value;
  const newPassword = document.getElementById("adminNewPass").value;
  const confirmPassword = document.getElementById("adminConfirmPass").value;

  if (newPassword !== confirmPassword) {
    Swal.fire({ icon: "error", title: "Mismatch", text: "New password and confirmation do not match." });
    return;
  }

  const token = sessionStorage.getItem("adminToken");
  try {
    const res = await fetch(`${window.API.BASE_URL}/api/admin/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ currentPassword, newPassword })
    });
    const data = await res.json();
    if (data.success) {
      Swal.fire({ icon: "success", title: "Updated", text: "Admin password updated successfully." });
      document.getElementById("adminPasswordForm").reset();
    } else {
      throw new Error(data.message);
    }
  } catch (err) {
    Swal.fire({ icon: "error", title: "Error", text: err.message });
  }
}

/**
 * Toggle Password Visibility
 */
function toggleAdminPasswordVisibility() {
  const input = document.getElementById("adminPassword");
  const icon = document.getElementById("togglePasswordIcon");
  if (input.type === "password") {
    input.type = "text";
    icon.classList.remove("fa-eye");
    icon.classList.add("fa-eye-slash");
  } else {
    input.type = "password";
    icon.classList.remove("fa-eye-slash");
    icon.classList.add("fa-eye");
  }
}

/**
 * Admin Logout
 */
function handleAdminLogout() {
  Swal.fire({
    title: "Sign Out",
    text: "Sign out from Administrator Console?",
    icon: "question",
    showCancelButton: true,
    confirmButtonColor: "#ef4444",
    confirmButtonText: "Logout"
  }).then(result => {
    if (result.isConfirmed) {
      sessionStorage.removeItem("adminToken");
      sessionStorage.removeItem("adminUsername");
      window.location.reload();
    }
  });
}
