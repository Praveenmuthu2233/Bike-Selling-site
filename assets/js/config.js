/**
 * SMR Motors - Global Client Configuration
 */
window.APP_CONFIG = {
  API_BASE: window.location.origin,
  GOOGLE_CLIENT_ID: window.ENV_GOOGLE_CLIENT_ID || '',
  ENDPOINTS: {
    CONFIG: '/api/config',
    AUTH_GOOGLE: '/api/auth/google',
    AUTH_DEMO: '/api/auth/demo-google',
    AUTH_ME: '/api/auth/me',
    AUTH_LOGOUT: '/api/auth/logout',
    BIKES: '/api/bikes',
    CATEGORIES: '/api/categories',
    ENQUIRIES: '/api/enquiries',
    CONTACT: '/api/contact',
    USER_PROFILE: '/api/users/profile',
    USER_DASHBOARD: '/api/users/dashboard',
    USER_LISTINGS: '/api/users/listings',
    USER_FAVORITES: '/api/users/favorites',
    USER_ENQUIRIES: '/api/users/enquiries',
    ADMIN_LOGIN: '/api/admin/login',
    ADMIN_DASHBOARD: '/api/admin/dashboard',
    ADMIN_BIKES: '/api/admin/bikes',
    ADMIN_USERS: '/api/admin/users',
    ADMIN_MESSAGES: '/api/admin/messages',
    ADMIN_AUDIT_LOGS: '/api/admin/audit-logs'
  }
};
