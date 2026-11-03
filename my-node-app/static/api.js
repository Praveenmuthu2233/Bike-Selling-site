/**
 * SMR Motors - Unified API & Notification Client
 */

// Toast notification manager
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'info-circle';
  if (type === 'success') icon = 'check-circle';
  if (type === 'error') icon = 'exclamation-circle';

  toast.innerHTML = `
    <i class="fas fa-${icon}"></i>
    <div style="flex:1; font-size: 0.92rem;">${message}</div>
    <button style="background:none;border:none;color:inherit;cursor:pointer;opacity:0.7;" onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal helper
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('open');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('open');
}

// Global API Request Helper
async function apiRequest(endpoint, options = {}) {
  const config = window.APP_CONFIG || {};
  const baseUrl = config.API_BASE || window.location.origin;
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;

  const headers = { ...options.headers };

  // Attach token if present
  const isAdminRequest = (endpoint.includes('/admin') && !endpoint.includes('/admin/login')) ||
    (window.location.pathname.includes('admin') && !!(localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken')));
  const token = isAdminRequest 
    ? (localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken'))
    : (localStorage.getItem('token') || sessionStorage.getItem('token'));

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Handle JSON body if not FormData
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
    if (typeof options.body !== 'string') {
      options.body = JSON.stringify(options.body);
    }
  }

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      if (response.status === 401 && !options.skipAuthRedirect) {
        if (isAdminRequest) {
          localStorage.removeItem('adminToken');
          sessionStorage.removeItem('adminToken');
          if (!window.location.pathname.includes('login')) {
            window.location.href = '/admin/login.html';
          }
        }
      }
      throw new Error(data.message || `Request failed with status ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error.message);
    throw error;
  }
}
