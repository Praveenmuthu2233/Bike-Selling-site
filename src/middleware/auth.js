/**
 * User Authentication Middleware (JWT)
 * Verifies JWT tokens issued after Google OAuth sign-in.
 */

const jwt = require('jsonwebtoken');
const db = require('../config/db');

const JWT_SECRET = process.env.JWT_SECRET || 'smr-motors-jwt-secret-key-2025';

async function userAuth(req, res, next) {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      return res.status(401).json({ success: false, message: 'Authentication required. Missing Authorization header.' });
    }

    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      return res.status(401).json({ success: false, message: 'Invalid Authorization header format. Expected Bearer <token>.' });
    }

    const token = parts[1];
    let decoded;
    try {
      decoded = jwt.verify(token, JWT_SECRET);
    } catch (err) {
      if (err.name === 'TokenExpiredError') {
        return res.status(401).json({ success: false, message: 'Session expired. Please sign in again.' });
      }
      return res.status(401).json({ success: false, message: 'Invalid authentication token.' });
    }

    // Verify user exists in database
    let user = null;
    if (db.getIsConnected()) {
      const rows = await db.query('SELECT id, google_id, name, email, profile_image, phone, role FROM users WHERE id = ?', [decoded.id]);
      if (rows && rows.length > 0) {
        user = rows[0];
      }
    } else {
      user = db.fallbackStore.users.find(u => u.id === decoded.id);
    }

    if (!user) {
      // Fallback: trust token payload if user was recently created in fallback
      user = {
        id: decoded.id,
        google_id: decoded.google_id,
        name: decoded.name,
        email: decoded.email,
        profile_image: decoded.profile_image,
        phone: decoded.phone || '',
        role: decoded.role || 'user'
      };
    }

    req.user = user;
    next();
  } catch (err) {
    console.error('[UserAuth Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Internal server error during authentication.' });
  }
}

/**
 * Optional user authentication - sets req.user if valid token present, but doesn't block request if missing
 */
function optionalUserAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader) return next();

  const parts = authHeader.split(' ');
  if (parts.length === 2 && parts[0] === 'Bearer') {
    try {
      const decoded = jwt.verify(parts[1], JWT_SECRET);
      req.user = decoded;
    } catch (e) {}
  }
  next();
}

module.exports = {
  userAuth,
  optionalUserAuth,
  JWT_SECRET
};
