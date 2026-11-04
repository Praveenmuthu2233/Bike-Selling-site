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
          window.location.href = '/profile.html';
        }, 600);
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
          window.location.href = '/profile.html';
        }, 600);
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
      window.location.href = '/index.html';
    }, 400);
  },

  handleOriginMismatchError(err) {
    console.warn('[Google Auth Diagnostic]', err);
    const banner = document.getElementById('oauth-diagnostic-banner');
    if (banner) {
      const currentOrigin = window.location.origin;
      banner.style.display = 'block';
      banner.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; padding: 14px 16px; margin-bottom: 1.25rem; font-size: 0.86rem; color: #FCA5A5; line-height: 1.5;">
          <div style="font-weight: 700; color: #FFF; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            <i class="fas fa-exclamation-triangle" style="color: #EF4444;"></i> Google OAuth: Error 400 (origin_mismatch)
          </div>
          <div>Your current website origin is: <code style="background: rgba(0,0,0,0.4); padding: 2px 6px; border-radius: 4px; color: #38BDF8;">${currentOrigin}</code></div>
          <div style="margin-top: 8px;">
            To resolve this in Google Cloud Console:
            <ol style="margin-left: 1.2rem; margin-top: 4px;">
              <li>Open <strong>Google Cloud Console &rarr; Credentials &rarr; OAuth 2.0 Client IDs</strong></li>
              <li>Under <strong>Authorized JavaScript origins</strong>, add: <code style="color:#FFF;">${currentOrigin}</code></li>
              <li>Under <strong>Authorized redirect URIs</strong>, add: <code style="color:#FFF;">${currentOrigin}/api/auth/google/callback</code></li>
            </ol>
          </div>
          <div style="margin-top: 8px; color: #FDE047;">
            <i class="fas fa-info-circle"></i> Please ensure authorized JavaScript origins match in Google Cloud Console.
          </div>
        </div>
      `;
    }
  }
};

// Initialize Google GIS if container present
async function initGoogleAuth(buttonContainerId = 'google-signin-btn') {
  let clientId = window.ENV_GOOGLE_CLIENT_ID || window.APP_CONFIG?.GOOGLE_CLIENT_ID;

  // If client ID is not preloaded in window, fetch from backend /api/config
  if (!clientId || clientId.startsWith('your_')) {
    try {
      const res = await fetch('/api/config');
      if (res.ok) {
        const conf = await res.json();
        if (conf.googleClientId && !conf.googleClientId.startsWith('your_')) {
          clientId = conf.googleClientId;
          if (window.APP_CONFIG) {
            window.APP_CONFIG.GOOGLE_CLIENT_ID = clientId;
          }
          window.ENV_GOOGLE_CLIENT_ID = clientId;
        }
      }
    } catch (e) {
      console.warn('[Google Auth] Could not query /api/config for Client ID');
    }
  }

  const btnContainer = document.getElementById(buttonContainerId);

  if (!clientId || clientId.startsWith('your_')) {
    console.info('[Google Auth] GOOGLE_CLIENT_ID not configured in .env. Interactive Google button hidden.');
    if (btnContainer) {
      btnContainer.innerHTML = '<div style="font-size: 0.85rem; padding: 10px 14px; background: rgba(255, 165, 0, 0.12); border: 1px solid rgba(255, 165, 0, 0.3); border-radius: 8px; color: #ffb74d; text-align: center;"><i class="fas fa-info-circle"></i> Google OAuth setup required in environment configuration.</div>';
    }
    return;
  }

  if (window.google && window.google.accounts) {
    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response && response.credential) {
            AuthService.handleGoogleCredential(response.credential);
          }
        },
        error_callback: (err) => {
          AuthService.handleOriginMismatchError(err);
        }
      });

      if (btnContainer) {
        btnContainer.innerHTML = '';
        window.google.accounts.id.renderButton(btnContainer, {
          theme: 'filled_blue',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          width: 320
        });
      }
    } catch (err) {
      console.error('[Google Auth Initialization Error]:', err);
      AuthService.handleOriginMismatchError(err);
    }
  }
}
