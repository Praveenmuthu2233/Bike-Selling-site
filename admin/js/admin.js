/**
 * SMR Motors - Admin Portal Controller
 */

let targetBikeIdForAction = null;

function checkAdminAuth() {
  const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
  if (!token) {
    window.location.href = 'login.html';
    return null;
  }
  try {
    const admin = JSON.parse(localStorage.getItem('adminUser') || sessionStorage.getItem('adminUser') || '{}');
    const nameEl = document.getElementById('topbar-admin-name');
    if (nameEl && admin.username) nameEl.innerText = admin.username;
    return admin;
  } catch (e) {
    return {};
  }
}

function adminLogout() {
  localStorage.removeItem('adminToken');
  localStorage.removeItem('adminUser');
  sessionStorage.removeItem('adminToken');
  sessionStorage.removeItem('adminUser');
  showToast('Logged out of Admin Portal', 'info');
  setTimeout(() => {
    window.location.href = 'login.html';
  }, 600);
}

function switchAdminTab(tabId, el) {
  document.querySelectorAll('.admin-tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.admin-nav-item').forEach(i => i.classList.remove('active'));

  const targetPane = document.getElementById(tabId);
  if (targetPane) targetPane.classList.add('active');
  if (el) el.classList.add('active');

  const titleEl = document.getElementById('admin-breadcrumb-title');
  if (titleEl && el) {
    titleEl.innerText = el.innerText.trim();
  }

  // Load appropriate data
  if (tabId === 'tab-overview') loadAdminOverview();
  if (tabId === 'tab-bikes') loadAdminBikes();
  if (tabId === 'tab-enquiries') loadAdminEnquiries();
  if (tabId === 'tab-messages') loadAdminMessages();
  if (tabId === 'tab-audit') loadAdminAuditLogs();
}

async function loadAdminOverview() {
  try {
    const res = await apiRequest('/api/admin/dashboard');
    if (res.success && res.data) {
      const { counts, recentUsers, pendingApprovals } = res.data;
      document.getElementById('adm-stat-bikes').innerText = counts.total_bikes || 0;
      document.getElementById('adm-stat-pending').innerText = counts.pending_bikes || 0;
      document.getElementById('adm-stat-users').innerText = counts.total_users || 0;
      document.getElementById('adm-stat-enquiries').innerText = counts.total_enquiries || 0;

      // Pending alert
      const alertBox = document.getElementById('pending-approvals-alert');
      if (counts.pending_bikes > 0) {
        alertBox.style.display = 'flex';
        document.getElementById('pending-alert-text').innerText = `You have ${counts.pending_bikes} vehicle listing(s) pending approval.`;
      } else {
        alertBox.style.display = 'none';
      }

      // Recent users
      const tbody = document.getElementById('overview-recent-users-tbody');
      if (recentUsers && recentUsers.length > 0) {
        tbody.innerHTML = recentUsers.map(u => `
          <tr>
            <td>
              <div style="font-weight: 600;">${u.name}</div>
            </td>
            <td style="color: var(--text-secondary);">${u.email}</td>
            <td><span class="badge badge-featured"><i class="fab fa-google"></i> Google</span></td>
            <td style="color: var(--text-muted); font-size: 0.85rem;">${new Date(u.created_at).toLocaleDateString()}</td>
          </tr>
        `).join('');
      } else {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 2rem; color:var(--text-muted);">No registered users found.</td></tr>`;
      }
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminBikes() {
  const tbody = document.getElementById('admin-bikes-table-body');
  const statusFilter = document.getElementById('adm-bikes-filter-status')?.value || '';
  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 3rem;"><i class="fas fa-spinner fa-spin"></i> Loading inventory...</td></tr>`;

  try {
    const endpoint = statusFilter ? `/api/admin/bikes?status=${statusFilter}` : '/api/admin/bikes';
    const res = await apiRequest(endpoint);
    const bikes = res.data || [];

    if (bikes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 3rem; color:var(--text-muted);">No motorcycles match the selected status filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = bikes.map(bike => {
      let badgeClass = 'badge-pending';
      if (bike.status === 'approved') badgeClass = 'badge-approved';
      if (bike.status === 'rejected') badgeClass = 'badge-rejected';
      if (bike.status === 'soldout') badgeClass = 'badge-soldout';

      return `
        <tr>
          <td>
            <div style="font-weight: 700; color: #FFF;">${bike.year} ${bike.title}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">${bike.model || ''}</div>
          </td>
          <td>${bike.brand}</td>
          <td>
            <span style="color: var(--accent-primary); font-weight: 800; font-family: var(--font-display); font-size: 1.05rem;">
              ₹${Number(bike.price).toLocaleString('en-IN')}
            </span>
          </td>
          <td>${(bike.kilometers_driven || 0).toLocaleString()} km</td>
          <td>
            <div>${bike.seller_name || 'Showroom Owned'}</div>
            <div style="font-size: 0.78rem; color: var(--text-muted);">${bike.seller_phone || ''}</div>
          </td>
          <td>
            <span class="badge ${badgeClass}">${bike.status}</span>
            ${bike.rejection_reason ? `<div style="font-size:0.75rem; color:var(--color-danger);">${bike.rejection_reason}</div>` : ''}
          </td>
          <td>
            <div style="display:flex; gap:0.4rem; flex-wrap:wrap;">
              ${bike.status !== 'approved' ? `
                <button onclick="approveBikeAction(${bike.id})" class="btn btn-sm btn-success" title="Approve Listing">
                  <i class="fas fa-check"></i>
                </button>
              ` : ''}
              ${bike.status !== 'rejected' ? `
                <button onclick="promptRejectBike(${bike.id})" class="btn btn-sm btn-danger" title="Reject Listing">
                  <i class="fas fa-times"></i>
                </button>
              ` : ''}
              <button onclick="promptPriceUpdate(${bike.id}, ${bike.price})" class="btn btn-sm btn-secondary" title="Edit Price">
                <i class="fas fa-tag"></i>
              </button>
              <button onclick="deleteBikeAdmin(${bike.id})" class="btn btn-sm btn-outline" title="Delete">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

async function approveBikeAction(id) {
  try {
    const res = await apiRequest(`/api/admin/bikes/${id}/approve`, { method: 'PUT' });
    showToast(res.message || 'Motorcycle listing approved!', 'success');
    loadAdminBikes();
    loadAdminOverview();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function promptRejectBike(id) {
  targetBikeIdForAction = id;
  document.getElementById('reject-reason-input').value = '';
  openModal('reject-modal');
}

async function confirmRejectBike() {
  if (!targetBikeIdForAction) return;
  const reason = document.getElementById('reject-reason-input').value.trim();
  try {
    const res = await apiRequest(`/api/admin/bikes/${targetBikeIdForAction}/reject`, {
      method: 'PUT',
      body: { reason: reason || 'Listing details did not meet marketplace quality standards.' }
    });
    showToast(res.message || 'Listing rejected', 'info');
    closeModal('reject-modal');
    loadAdminBikes();
    loadAdminOverview();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function promptPriceUpdate(id, currentPrice) {
  targetBikeIdForAction = id;
  document.getElementById('update-price-input').value = currentPrice;
  openModal('price-modal');
}

async function confirmPriceUpdate() {
  if (!targetBikeIdForAction) return;
  const price = document.getElementById('update-price-input').value;
  try {
    const res = await apiRequest(`/api/admin/bikes/${targetBikeIdForAction}/price`, {
      method: 'PUT',
      body: { price: Number(price) }
    });
    showToast(res.message || 'Price updated successfully', 'success');
    closeModal('price-modal');
    loadAdminBikes();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteBikeAdmin(id) {
  if (!confirm('Are you sure you want to permanently delete this vehicle from inventory?')) return;
  try {
    const res = await apiRequest(`/api/admin/bikes/${id}`, { method: 'DELETE' });
    showToast(res.message || 'Vehicle deleted from database', 'success');
    loadAdminBikes();
    loadAdminOverview();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminEnquiries() {
  const tbody = document.getElementById('admin-enquiries-table-body');
  try {
    const res = await apiRequest('/api/enquiries');
    const enquiries = res.data || [];

    if (enquiries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 3rem; color:var(--text-muted);">No customer enquiries found.</td></tr>`;
      return;
    }

    tbody.innerHTML = enquiries.map(e => `
      <tr>
        <td>
          <div style="font-weight: 700;">${e.name}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">${new Date(e.created_at).toLocaleDateString()}</div>
        </td>
        <td>
          <div><a href="tel:${e.phone}" style="color:var(--accent-primary); font-weight:600;"><i class="fas fa-phone"></i> ${e.phone}</a></div>
          <div style="font-size: 0.82rem; color: var(--text-secondary);">${e.email}</div>
        </td>
        <td>
          <strong>${e.bike_title || 'General'}</strong>
        </td>
        <td style="max-width: 250px; font-size: 0.88rem; color: var(--text-secondary);">${e.message}</td>
        <td>
          <span class="badge badge-${e.status === 'completed' ? 'approved' : (e.status === 'contacted' ? 'featured' : 'pending')}">
            ${e.status}
          </span>
        </td>
        <td>
          <div style="display:flex; gap:0.4rem;">
            ${e.status !== 'contacted' ? `
              <button onclick="updateEnquiryStatusAction(${e.id}, 'contacted')" class="btn btn-sm btn-outline" title="Mark Contacted">
                <i class="fas fa-phone"></i>
              </button>
            ` : ''}
            ${e.status !== 'completed' ? `
              <button onclick="updateEnquiryStatusAction(${e.id}, 'completed')" class="btn btn-sm btn-success" title="Mark Completed">
                <i class="fas fa-check"></i>
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

async function updateEnquiryStatusAction(id, status) {
  try {
    const res = await apiRequest(`/api/enquiries/${id}/status`, {
      method: 'PUT',
      body: { status }
    });
    showToast(res.message || `Enquiry updated to ${status}`, 'success');
    loadAdminEnquiries();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminMessages() {
  const tbody = document.getElementById('admin-messages-table-body');
  try {
    const res = await apiRequest('/api/admin/messages');
    const msgs = res.data || [];

    if (msgs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 3rem; color:var(--text-muted);">No showroom contact submissions.</td></tr>`;
      return;
    }

    tbody.innerHTML = msgs.map(m => `
      <tr>
        <td style="font-weight: 600;">${m.name}</td>
        <td>
          <div>${m.email}</div>
          <div style="font-size: 0.82rem; color: var(--text-muted);">${m.phone || '-'}</div>
        </td>
        <td style="max-width: 320px; font-size: 0.88rem; color: var(--text-secondary);">${m.message}</td>
        <td style="color: var(--text-muted); font-size: 0.85rem;">${new Date(m.created_at).toLocaleString()}</td>
        <td>
          <button onclick="deleteContactMsg(${m.id})" class="btn btn-sm btn-danger"><i class="fas fa-trash"></i></button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 2rem; color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

async function deleteContactMsg(id) {
  try {
    await apiRequest(`/api/admin/messages/${id}`, { method: 'DELETE' });
    showToast('Message deleted', 'info');
    loadAdminMessages();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadAdminAuditLogs() {
  const tbody = document.getElementById('admin-audit-table-body');
  try {
    const res = await apiRequest('/api/admin/audit-logs');
    const logs = res.data || [];

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 3rem; color:var(--text-muted);">No audit events recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr>
        <td style="font-size: 0.82rem; color: var(--text-muted);">${new Date(l.created_at).toLocaleString()}</td>
        <td style="font-weight: 600; color: var(--accent-primary);">${l.admin_username}</td>
        <td><span class="badge badge-featured">${l.action}</span></td>
        <td>${l.target_type}</td>
        <td>#${l.target_id || '-'}</td>
        <td style="max-width: 250px; font-size: 0.82rem; color: var(--text-secondary);">${l.details || '-'}</td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const admin = checkAdminAuth();
  if (admin) {
    loadAdminOverview();
  }
});
