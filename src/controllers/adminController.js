/**
 * Admin Panel Controller
 * Handles secure administrator authentication, dashboard statistics,
 * user management, bike approval workflow, enquiry management, contact messages, and audit logging.
 */

const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../config/db');
const { JWT_SECRET } = require('../middleware/auth');
const { logAdminAction } = require('../middleware/adminAuth');
const { formatBike } = require('./bikeController');

/**
 * POST /api/admin/login
 */
async function adminLogin(req, res) {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({ success: false, message: 'Username and password are required.' });
    }

    const trimmedUser = username.trim().toLowerCase();
    let adminRecord = null;

    // Check environment admin config first
    const envAdminUser = (process.env.ADMIN_USERNAME || 'admin').toLowerCase();
    const envAdminEmail = (process.env.ADMIN_EMAIL || 'admin@smrmotors.com').toLowerCase();
    const envAdminHash = process.env.ADMIN_PASSWORD_HASH;

    if (trimmedUser === envAdminUser || trimmedUser === envAdminEmail) {
      if (envAdminHash) {
        const isMatch = await bcrypt.compare(password, envAdminHash);
        if (isMatch) {
          adminRecord = {
            id: 1,
            username: envAdminUser,
            email: envAdminEmail,
            role: 'superadmin'
          };
        }
      }
    }

    // Check database if not matched yet
    if (!adminRecord && db.getIsConnected()) {
      const rows = await db.query(
        'SELECT id, username, email, password_hash, role FROM admins WHERE LOWER(username) = ? OR LOWER(email) = ?',
        [trimmedUser, trimmedUser]
      );
      if (rows && rows.length > 0) {
        const isMatch = await bcrypt.compare(password, rows[0].password_hash);
        if (isMatch) {
          adminRecord = {
            id: rows[0].id,
            username: rows[0].username,
            email: rows[0].email,
            role: rows[0].role || 'admin'
          };
        }
      }
    } else if (!adminRecord) {
      // Check in fallback store
      const found = db.fallbackStore.admins.find(
        a => a.username.toLowerCase() === trimmedUser || a.email.toLowerCase() === trimmedUser
      );
      if (found) {
        const isMatch = await bcrypt.compare(password, found.password_hash);
        if (isMatch) {
          adminRecord = {
            id: found.id,
            username: found.username,
            email: found.email,
            role: found.role
          };
        }
      }
    }

    // Legacy fallback check for hardcoded accounts during initial setup/migration
    if (!adminRecord) {
      const legacyAccounts = {
        admin: { pass: 'Admin@123', name: 'Administrator', role: 'superadmin' },
        murugan: { pass: 'murugan@22', name: 'Murugan', role: 'superadmin' },
        raja: { pass: 'raja@22', name: 'Raja', role: 'admin' },
        mani: { pass: 'mani@22', name: 'Mani', role: 'limited' }
      };

      if (legacyAccounts[trimmedUser] && legacyAccounts[trimmedUser].pass === password) {
        adminRecord = {
          id: 99,
          username: trimmedUser,
          email: `${trimmedUser}@smrmotors.com`,
          role: legacyAccounts[trimmedUser].role
        };
      }
    }

    if (!adminRecord) {
      return res.status(401).json({ success: false, message: 'Invalid administrator credentials.' });
    }

    // Generate Admin JWT token
    const token = jwt.sign(
      {
        id: adminRecord.id,
        username: adminRecord.username,
        email: adminRecord.email,
        role: adminRecord.role,
        isAdmin: true
      },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    await logAdminAction(adminRecord.id, adminRecord.username, 'ADMIN_LOGIN', { status: 'success' }, req.ip);

    return res.json({
      success: true,
      message: 'Admin login successful.',
      token,
      admin: {
        id: adminRecord.id,
        username: adminRecord.username,
        name: adminRecord.username.toUpperCase(),
        email: adminRecord.email,
        role: adminRecord.role
      }
    });
  } catch (err) {
    console.error('[AdminLogin Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Internal server error during admin login.' });
  }
}

/**
 * GET /api/admin/dashboard
 */
async function getAdminDashboard(req, res) {
  try {
    let totalUsers = 0;
    let totalBikes = 0;
    let activeListings = 0;
    let pendingApprovals = 0;
    let rejectedListings = 0;
    let soldoutListings = 0;
    let totalEnquiries = 0;
    let newContactMessages = 0;
    let recentRegistrations = [];
    let recentActivities = [];

    if (db.getIsConnected()) {
      const [uCnt] = await db.query('SELECT COUNT(*) as count FROM users');
      totalUsers = uCnt[0]?.count || 0;

      const [bCnt] = await db.query('SELECT COUNT(*) as count FROM bikes');
      totalBikes = bCnt[0]?.count || 0;

      const [actCnt] = await db.query('SELECT COUNT(*) as count FROM bikes WHERE status = "approved"');
      activeListings = actCnt[0]?.count || 0;

      const [pndCnt] = await db.query('SELECT COUNT(*) as count FROM bikes WHERE status = "pending"');
      pendingApprovals = pndCnt[0]?.count || 0;

      const [rejCnt] = await db.query('SELECT COUNT(*) as count FROM bikes WHERE status = "rejected"');
      rejectedListings = rejCnt[0]?.count || 0;

      const [soldCnt] = await db.query('SELECT COUNT(*) as count FROM bikes WHERE status = "soldout"');
      soldoutListings = soldCnt[0]?.count || 0;

      const [enqCnt] = await db.query('SELECT COUNT(*) as count FROM enquiries');
      totalEnquiries = enqCnt[0]?.count || 0;

      const [msgCnt] = await db.query('SELECT COUNT(*) as count FROM contact_messages WHERE status = "unread"');
      newContactMessages = msgCnt[0]?.count || 0;

      recentRegistrations = await db.query(
        'SELECT id, name, email, profile_image, phone, created_at FROM users ORDER BY created_at DESC LIMIT 5'
      );

      recentActivities = await db.query(
        'SELECT * FROM admin_audit_logs ORDER BY created_at DESC LIMIT 10'
      );
    } else {
      totalUsers = db.fallbackStore.users.length;
      totalBikes = db.fallbackStore.bikes.length;
      activeListings = db.fallbackStore.bikes.filter(b => b.status === 'approved').length;
      pendingApprovals = db.fallbackStore.bikes.filter(b => b.status === 'pending').length;
      rejectedListings = db.fallbackStore.bikes.filter(b => b.status === 'rejected').length;
      soldoutListings = db.fallbackStore.bikes.filter(b => b.status === 'soldout').length;
      totalEnquiries = db.fallbackStore.enquiries.length;
      newContactMessages = db.fallbackStore.contact_messages.filter(m => m.status === 'unread').length;
      recentRegistrations = db.fallbackStore.users.slice(-5).reverse();
      recentActivities = db.fallbackStore.audit_logs.slice(-10).reverse();
    }

    return res.json({
      success: true,
      stats: {
        totalUsers,
        totalBikes,
        activeListings,
        pendingApprovals,
        rejectedListings,
        soldoutListings,
        totalEnquiries,
        newContactMessages
      },
      recentRegistrations,
      recentActivities
    });
  } catch (err) {
    console.error('[AdminDashboard Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to load admin dashboard statistics.' });
  }
}

/**
 * GET /api/admin/users
 */
async function getAdminUsers(req, res) {
  try {
    const { search, role } = req.query;
    let users = [];

    if (db.getIsConnected()) {
      let conditions = [];
      let params = [];

      if (search) {
        conditions.push('(name LIKE ? OR email LIKE ? OR phone LIKE ?)');
        const q = `%${search}%`;
        params.push(q, q, q);
      }
      if (role && role !== 'all') {
        conditions.push('role = ?');
        params.push(role);
      }

      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
      users = await db.query(
        `SELECT id, google_id, name, email, profile_image, phone, role, created_at, updated_at
         FROM users ${whereClause} ORDER BY created_at DESC`,
        params
      );
    } else {
      let list = db.fallbackStore.users;
      if (search) {
        const q = search.toLowerCase();
        list = list.filter(u => (u.name || '').toLowerCase().includes(q) || (u.email || '').toLowerCase().includes(q));
      }
      users = list;
    }

    return res.json({
      success: true,
      count: users.length,
      users
    });
  } catch (err) {
    console.error('[AdminUsers Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve users.' });
  }
}

/**
 * DELETE /api/admin/users/:id
 */
async function deleteAdminUser(req, res) {
  try {
    const userId = parseInt(req.params.id, 10);
    if (db.getIsConnected()) {
      await db.query('DELETE FROM users WHERE id = ?', [userId]);
    } else {
      db.fallbackStore.users = db.fallbackStore.users.filter(u => u.id !== userId);
    }

    await logAdminAction(req.admin.id, req.admin.username, 'DELETE_USER', { userId }, req.ip);

    return res.json({ success: true, message: 'User account deleted successfully.' });
  } catch (err) {
    console.error('[DeleteUser Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to delete user.' });
  }
}

/**
 * GET /api/admin/bikes
 */
async function getAdminBikes(req, res) {
  try {
    const { status, search, brand } = req.query;
    let bikes = [];

    if (db.getIsConnected()) {
      let conditions = [];
      let params = [];

      if (status && status !== 'all') {
        conditions.push('status = ?');
        params.push(status);
      }
      if (brand && brand !== 'all') {
        conditions.push('brand = ?');
        params.push(brand);
      }
      if (search) {
        conditions.push('(title LIKE ? OR brand LIKE ? OR model LIKE ? OR vehicle_number LIKE ?)');
        const q = `%${search}%`;
        params.push(q, q, q, q);
      }

      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
      bikes = await db.query(`SELECT * FROM bikes ${whereClause} ORDER BY created_at DESC`, params);
    } else {
      let list = db.fallbackStore.bikes;
      if (status && status !== 'all') list = list.filter(b => b.status === status);
      if (brand && brand !== 'all') list = list.filter(b => b.brand === brand);
      if (search) {
        const q = search.toLowerCase();
        list = list.filter(b => (b.title || '').toLowerCase().includes(q) || (b.brand || '').toLowerCase().includes(q));
      }
      bikes = list;
    }

    const formatted = bikes.map(formatBike);
    return res.json({
      success: true,
      count: formatted.length,
      bikes: formatted
    });
  } catch (err) {
    console.error('[AdminBikes Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve bikes.' });
  }
}

/**
 * PUT /api/admin/bikes/:id/approve
 */
async function approveBike(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);
    if (db.getIsConnected()) {
      await db.query('UPDATE bikes SET status = "approved", rejection_reason = NULL, updated_at = NOW() WHERE id = ?', [bikeId]);
    } else {
      const b = db.fallbackStore.bikes.find(item => item.id === bikeId);
      if (b) {
        b.status = 'approved';
        b.rejection_reason = null;
        b.updated_at = new Date();
      }
    }

    await logAdminAction(req.admin.id, req.admin.username, 'APPROVE_BIKE', { bikeId }, req.ip);

    return res.json({ success: true, message: 'Bike listing approved and published.' });
  } catch (err) {
    console.error('[ApproveBike Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to approve bike.' });
  }
}

/**
 * PUT /api/admin/bikes/:id/reject
 */
async function rejectBike(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);
    const { reason } = req.body;
    const rejectionReason = reason || 'Does not meet marketplace guidelines.';

    if (db.getIsConnected()) {
      await db.query(
        'UPDATE bikes SET status = "rejected", rejection_reason = ?, updated_at = NOW() WHERE id = ?',
        [rejectionReason, bikeId]
      );
    } else {
      const b = db.fallbackStore.bikes.find(item => item.id === bikeId);
      if (b) {
        b.status = 'rejected';
        b.rejection_reason = rejectionReason;
        b.updated_at = new Date();
      }
    }

    await logAdminAction(req.admin.id, req.admin.username, 'REJECT_BIKE', { bikeId, reason: rejectionReason }, req.ip);

    return res.json({ success: true, message: 'Bike listing rejected.' });
  } catch (err) {
    console.error('[RejectBike Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to reject bike.' });
  }
}

/**
 * PUT /api/admin/bikes/:id/price
 */
async function updateBikePrice(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);
    const { newPrice, sellingPrice } = req.body;
    const finalPrice = parseFloat(newPrice || sellingPrice);

    if (isNaN(finalPrice)) {
      return res.status(400).json({ success: false, message: 'Valid price value is required.' });
    }

    if (db.getIsConnected()) {
      await db.query('UPDATE bikes SET selling_price = ?, updated_at = NOW() WHERE id = ?', [finalPrice, bikeId]);
    } else {
      const b = db.fallbackStore.bikes.find(item => item.id === bikeId);
      if (b) {
        b.selling_price = finalPrice;
        b.updated_at = new Date();
      }
    }

    await logAdminAction(req.admin.id, req.admin.username, 'UPDATE_PRICE', { bikeId, newPrice: finalPrice }, req.ip);

    return res.json({ success: true, message: 'Selling price updated successfully.' });
  } catch (err) {
    console.error('[UpdateBikePrice Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update price.' });
  }
}

/**
 * PUT /api/admin/bikes/:id/soldout
 */
async function markBikeSoldOut(req, res) {
  try {
    const bikeId = parseInt(req.params.id, 10);

    if (db.getIsConnected()) {
      await db.query('UPDATE bikes SET status = "soldout", updated_at = NOW() WHERE id = ?', [bikeId]);
    } else {
      const b = db.fallbackStore.bikes.find(item => item.id === bikeId);
      if (b) {
        b.status = 'soldout';
        b.updated_at = new Date();
      }
    }

    await logAdminAction(req.admin.id, req.admin.username, 'MARK_SOLDOUT', { bikeId }, req.ip);

    return res.json({ success: true, message: 'Bike marked as Sold Out.' });
  } catch (err) {
    console.error('[MarkBikeSoldOut Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update soldout status.' });
  }
}

/**
 * GET /api/admin/messages
 */
async function getAdminMessages(req, res) {
  try {
    let messages = [];
    if (db.getIsConnected()) {
      messages = await db.query('SELECT * FROM contact_messages ORDER BY created_at DESC');
    } else {
      messages = db.fallbackStore.contact_messages;
    }

    return res.json({
      success: true,
      count: messages.length,
      messages
    });
  } catch (err) {
    console.error('[GetAdminMessages Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve messages.' });
  }
}

/**
 * PUT /api/admin/messages/:id/read
 */
async function markMessageRead(req, res) {
  try {
    const msgId = parseInt(req.params.id, 10);
    if (db.getIsConnected()) {
      await db.query('UPDATE contact_messages SET status = "read" WHERE id = ?', [msgId]);
    } else {
      const m = db.fallbackStore.contact_messages.find(item => item.id === msgId);
      if (m) m.status = 'read';
    }

    return res.json({ success: true, message: 'Message marked as read.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

/**
 * DELETE /api/admin/messages/:id
 */
async function deleteMessage(req, res) {
  try {
    const msgId = parseInt(req.params.id, 10);
    if (db.getIsConnected()) {
      await db.query('DELETE FROM contact_messages WHERE id = ?', [msgId]);
    } else {
      db.fallbackStore.contact_messages = db.fallbackStore.contact_messages.filter(m => m.id !== msgId);
    }

    return res.json({ success: true, message: 'Message deleted.' });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

/**
 * POST /api/admin/change-password
 */
async function changeAdminPassword(req, res) {
  try {
    const { currentPassword, newPassword } = req.body;
    if (!currentPassword || !newPassword) {
      return res.status(400).json({ success: false, message: 'Both current and new passwords are required.' });
    }

    if (newPassword.length < 6) {
      return res.status(400).json({ success: false, message: 'New password must be at least 6 characters.' });
    }

    const adminId = req.admin.id;
    let adminRecord;

    if (db.getIsConnected()) {
      const rows = await db.query('SELECT * FROM admins WHERE id = ?', [adminId]);
      adminRecord = rows[0];
    } else {
      adminRecord = db.fallbackStore.admins.find(a => a.id === adminId);
    }

    if (!adminRecord) {
      return res.status(404).json({ success: false, message: 'Admin account not found.' });
    }

    const isMatch = await bcrypt.compare(currentPassword, adminRecord.password_hash);
    if (!isMatch) {
      return res.status(401).json({ success: false, message: 'Incorrect current password.' });
    }

    const newHash = await bcrypt.hash(newPassword, 10);
    if (db.getIsConnected()) {
      await db.query('UPDATE admins SET password_hash = ? WHERE id = ?', [newHash, adminId]);
    } else {
      adminRecord.password_hash = newHash;
    }

    await logAdminAction(adminId, req.admin.username, 'PASSWORD_CHANGE', {}, req.ip);

    return res.json({ success: true, message: 'Admin password changed successfully.' });
  } catch (err) {
    console.error('[ChangeAdminPassword Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update password.' });
  }
}

/**
 * GET /api/admin/audit-logs
 */
async function getAuditLogs(req, res) {
  try {
    let logs = [];
    if (db.getIsConnected()) {
      logs = await db.query('SELECT * FROM admin_audit_logs ORDER BY created_at DESC LIMIT 50');
    } else {
      logs = db.fallbackStore.audit_logs.slice(-50).reverse();
    }
    return res.json({ success: true, count: logs.length, logs });
  } catch (err) {
    return res.status(500).json({ success: false, message: err.message });
  }
}

module.exports = {
  adminLogin,
  getAdminDashboard,
  getAdminUsers,
  deleteAdminUser,
  getAdminBikes,
  approveBike,
  rejectBike,
  updateBikePrice,
  markBikeSoldOut,
  getAdminMessages,
  markMessageRead,
  deleteMessage,
  changeAdminPassword,
  getAuditLogs
};
