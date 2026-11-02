/**
 * SMR Motors - Google OAuth 2.0 & Session Management
 */

const AuthService = {
  getToken() {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
  },

  setSession(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  clearSession() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
  },

  getUser() {
    try {
      const u = localStorage.getItem('user') || sessionStorage.getItem('user');
      return u ? JSON.parse(u) : null;
    } catch (e) {
      return null;
    }
  },

  async verifySession() {
    const token = this.getToken();
    if (!token) return null;
    try {
      const res = await apiRequest('/api/auth/me', { skipAuthRedirect: true });
      if (res.success && res.user) {
        localStorage.setItem('user', JSON.stringify(res.user));
        return res.user;
      }
    } catch (e) {
      this.clearSession();
    }
    return null;
  },

  async handleGoogleCredential(credential) {
    try {
      const res = await apiRequest('/api/auth/google', {
        method: 'POST',
        body: { credential }
      });

      if (res.success) {
        this.setSession(res.token, res.user);
        showToast('Signed in successfully!', 'success');
        setTimeout(() => {
          window.location.href = '/user/dashboard.html';
        }, 800);
      } else {
        showToast(res.message || 'Google sign-in failed', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Authentication error', 'error');
    }
  },

  async demoLogin() {
    try {
      const res = await apiRequest('/api/auth/demo-google', { method: 'POST' });
      if (res.success) {
        this.setSession(res.token, res.user);
        showToast('Demo account activated!', 'success');
        setTimeout(() => {
          window.location.href = '/user/dashboard.html';
        }, 800);
      } else {
        showToast(res.message || 'Demo login failed', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Failed to authenticate demo account', 'error');
    }
  },

  logout() {
    this.clearSession();
    showToast('Signed out safely', 'info');
    setTimeout(() => {
      window.location.href = '/login.html';
    }, 600);
  }
};

// Initialize Google GIS if container present
function initGoogleAuth(buttonContainerId = 'google-signin-btn') {
  const cfg = window.APP_CONFIG || {};
  const clientId = cfg.GOOGLE_CLIENT_ID;

  if (window.google && window.google.accounts && clientId) {
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (response && response.credential) {
          AuthService.handleGoogleCredential(response.credential);
        }
      }
    });

    const btnContainer = document.getElementById(buttonContainerId);
    if (btnContainer) {
      window.google.accounts.id.renderButton(btnContainer, {
        theme: 'filled_blue',
        size: 'large',
        text: 'continue_with',
        shape: 'rectangular',
        width: 320
      });
    }
  }
}
