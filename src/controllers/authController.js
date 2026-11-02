/**
 * Authentication Controller
 * Handles Google OAuth 2.0 Sign-In, Token Verification, Session Management, and User Profile.
 */

const axios = require('axios');
const jwt = require('jsonwebtoken');
const db = require('../config/db');
const { JWT_SECRET } = require('../middleware/auth');

/**
 * Verify Google ID Token via Google's tokeninfo endpoint or client library
 */
async function verifyGoogleIdToken(idToken) {
  try {
    const res = await axios.get(`https://oauth2.googleapis.com/tokeninfo?id_token=${idToken}`, {
      timeout: 8000
    });
    const payload = res.data;

    // Check Google Client ID if configured
    const expectedClientId = process.env.GOOGLE_CLIENT_ID;
    if (expectedClientId && payload.aud !== expectedClientId) {
      console.warn(`[Google Auth] Token audience mismatch: ${payload.aud} vs ${expectedClientId}`);
    }

    if (!payload.email_verified && payload.email_verified !== 'true') {
      throw new Error('Google email address is not verified.');
    }

    return {
      googleId: payload.sub,
      email: payload.email.toLowerCase(),
      name: payload.name || payload.email.split('@')[0],
      picture: payload.picture || null
    };
  } catch (err) {
    console.error('[Google Verification Error]:', err.response?.data || err.message);
    throw new Error('Failed to verify Google ID token with Google authentication servers.');
  }
}

/**
 * Find or create user in TiDB Cloud
 */
async function findOrCreateUser({ googleId, email, name, picture }) {
  if (db.getIsConnected()) {
    // Check by google_id or email
    const [existing] = await db.query(
      'SELECT id, google_id, name, email, profile_image, phone, role FROM users WHERE google_id = ? OR email = ?',
      [googleId, email]
    );

    if (existing) {
      // Update details
      await db.query(
        'UPDATE users SET name = ?, profile_image = ?, google_id = ? WHERE id = ?',
        [name, picture || existing.profile_image, googleId, existing.id]
      );
      return {
        id: existing.id,
        google_id: googleId,
        name,
        email: existing.email,
        profile_image: picture || existing.profile_image,
        phone: existing.phone || '',
        role: existing.role || 'user'
      };
    }

    // Insert new user
    const res = await db.query(
      'INSERT INTO users (google_id, name, email, profile_image, role) VALUES (?, ?, ?, ?, ?)',
      [googleId, name, email, picture, 'user']
    );

    return {
      id: res.insertId,
      google_id: googleId,
      name,
      email,
      profile_image: picture,
      phone: '',
      role: 'user'
    };
  } else {
    // In-memory fallback
    let user = db.fallbackStore.users.find(u => u.google_id === googleId || u.email === email);
    if (user) {
      user.name = name;
      if (picture) user.profile_image = picture;
      user.google_id = googleId;
      return user;
    }

    const newUser = {
      id: db.fallbackStore.nextId.users++,
      google_id: googleId,
      name,
      email,
      profile_image: picture,
      phone: '',
      role: 'user',
      created_at: new Date()
    };
    db.fallbackStore.users.push(newUser);
    return newUser;
  }
}

/**
 * POST /api/auth/google
 * Receives Google Credential / ID Token
 */
async function googleAuth(req, res) {
  try {
    const { credential, idToken } = req.body;
    const tokenToVerify = credential || idToken;

    if (!tokenToVerify) {
      return res.status(400).json({
        success: false,
        message: 'Missing Google authentication credential token.'
      });
    }

    // Verify token with Google
    const googleUser = await verifyGoogleIdToken(tokenToVerify);

    // Save user details in TiDB Cloud
    const user = await findOrCreateUser(googleUser);

    // Issue JWT session token
    const token = jwt.sign(
      {
        id: user.id,
        google_id: user.google_id,
        email: user.email,
        name: user.name,
        role: user.role || 'user'
      },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    return res.status(200).json({
      success: true,
      message: 'Successfully authenticated with Google.',
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        profile_image: user.profile_image,
        phone: user.phone,
        role: user.role
      }
    });
  } catch (err) {
    console.error('[GoogleAuth Endpoint Error]:', err.message);
    return res.status(401).json({
      success: false,
      message: err.message || 'Google authentication failed.'
    });
  }
}

/**
 * POST /api/auth/demo-google
 * Helper endpoint for local development testing when Google OAuth Client ID is not configured
 */
async function demoGoogleAuth(req, res) {
  try {
    const { email, name, picture } = req.body;
    const testEmail = (email || 'demo.user@gmail.com').toLowerCase();
    const testName = name || 'Demo Google User';
    const testPicture = picture || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&h=200&q=80';
    const googleId = 'google_demo_' + Buffer.from(testEmail).toString('hex').slice(0, 16);

    const user = await findOrCreateUser({
      googleId,
      email: testEmail,
      name: testName,
      picture: testPicture
    });

    const token = jwt.sign(
      {
        id: user.id,
        google_id: user.google_id,
        email: user.email,
        name: user.name,
        role: user.role || 'user'
      },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    return res.status(200).json({
      success: true,
      message: 'Signed in with Demo Google Account (Development Mode).',
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        profile_image: user.profile_image,
        phone: user.phone,
        role: user.role
      }
    });
  } catch (err) {
    console.error('[DemoGoogleAuth Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Demo Google sign-in failed.' });
  }
}

/**
 * GET /api/auth/me
 * Returns current authenticated user
 */
async function getMe(req, res) {
  try {
    if (!req.user) {
      return res.status(401).json({ success: false, message: 'Not authenticated.' });
    }
    return res.json({
      success: true,
      user: req.user
    });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

/**
 * POST /api/auth/logout
 */
function logout(req, res) {
  return res.json({
    success: true,
    message: 'Logged out successfully.'
  });
}

module.exports = {
  googleAuth,
  demoGoogleAuth,
  getMe,
  logout
};
