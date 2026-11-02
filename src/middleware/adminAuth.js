/**
 * Administrator Authentication Middleware
 * Validates admin JWT token and logs audit activity.
 */

const jwt = require('jsonwebtoken');
const db = require('../config/db');
const { JWT_SECRET } = require('./auth');

async function adminAuth(req, res, next) {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      return res.status(401).json({ success: false, message: 'Admin authentication required.' });
    }

    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      return res.status(401).json({ success: false, message: 'Invalid token format.' });
    }

    const token = parts[1];
    let decoded;
    try {
      decoded = jwt.verify(token, JWT_SECRET);
    } catch (err) {
      if (err.name === 'TokenExpiredError') {
        return res.status(401).json({ success: false, message: 'Admin session expired. Please log in again.' });
      }
      return res.status(401).json({ success: false, message: 'Invalid admin token.' });
    }

    if (!decoded.isAdmin || (decoded.role !== 'admin' && decoded.role !== 'superadmin')) {
      return res.status(403).json({ success: false, message: 'Access denied. Insufficient administrative privileges.' });
    }

    req.admin = decoded;
    next();
  } catch (err) {
    console.error('[AdminAuth Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Internal server error during admin validation.' });
  }
}

/**
 * Audit log helper
 */
async function logAdminAction(adminId, username, action, details, ip) {
  try {
    if (db.getIsConnected()) {
      await db.query(
        'INSERT INTO admin_audit_logs (admin_id, username, action, details, ip_address) VALUES (?, ?, ?, ?, ?)',
        [adminId || null, username || 'unknown', action, JSON.stringify(details || {}), ip || '']
      );
    } else {
      db.fallbackStore.audit_logs.push({
        id: db.fallbackStore.nextId.audit_logs++,
        admin_id: adminId || null,
        username: username || 'unknown',
        action,
        details: JSON.stringify(details || {}),
        ip_address: ip || '',
        created_at: new Date()
      });
    }
  } catch (err) {
    console.error('[Audit Log Error]:', err.message);
  }
}

module.exports = {
  adminAuth,
  logAdminAction
};
