/**
 * User Panel Controller
 * Handles user profile, listings, enquiries, favorites, and user dashboard statistics.
 */

const db = require('../config/db');

/**
 * GET /api/users/profile
 */
async function getProfile(req, res) {
  try {
    const userId = req.user.id;
    let user;

    if (db.getIsConnected()) {
      const [rows] = await db.query(
        'SELECT id, google_id, name, email, profile_image, phone, role, created_at FROM users WHERE id = ?',
        [userId]
      );
      user = rows;
    } else {
      user = db.fallbackStore.users.find(u => u.id === userId);
    }

    if (!user) {
      return res.status(404).json({ success: false, message: 'User profile not found.' });
    }

    return res.json({
      success: true,
      user
    });
  } catch (err) {
    console.error('[GetProfile Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve profile.' });
  }
}

/**
 * PUT /api/users/profile
 * Updates user profile. Rejects any attempt to modify role or privilege escalation.
 */
async function updateProfile(req, res) {
  try {
    const userId = req.user.id;
    const { name, phone } = req.body;

    // Security guard: never allow role modification from user endpoint
    if (req.body.role || req.body.isAdmin) {
      return res.status(403).json({
        success: false,
        message: 'Security Violation: Modifying user role or permissions is strictly forbidden.'
      });
    }

    const updatedName = (name || req.user.name || '').trim();
    const updatedPhone = (phone || req.user.phone || '').trim();

    if (db.getIsConnected()) {
      await db.query(
        'UPDATE users SET name = ?, phone = ?, updated_at = NOW() WHERE id = ?',
        [updatedName, updatedPhone, userId]
      );
    } else {
      const u = db.fallbackStore.users.find(item => item.id === userId);
      if (u) {
        u.name = updatedName;
        u.phone = updatedPhone;
        u.updated_at = new Date();
      }
    }

    return res.json({
      success: true,
      message: 'Profile updated successfully.',
      user: {
        id: userId,
        name: updatedName,
        phone: updatedPhone,
        email: req.user.email,
        profile_image: req.user.profile_image,
        role: 'user'
      }
    });
  } catch (err) {
    console.error('[UpdateProfile Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update profile.' });
  }
}

/**
 * GET /api/users/dashboard
 * User Dashboard summary
 */
async function getUserDashboard(req, res) {
  try {
    const userId = req.user.id;
    let listings = [];
    let enquiries = [];
    let favorites = [];
    let recentBikes = [];

    if (db.getIsConnected()) {
      listings = await db.query('SELECT * FROM bikes WHERE seller_id = ? ORDER BY created_at DESC', [userId]);
      enquiries = await db.query(
        `SELECT e.*, b.title as bike_title, b.images as bike_images, b.price as bike_price, b.brand as bike_brand
         FROM enquiries e
         LEFT JOIN bikes b ON e.bike_id = b.id
         WHERE e.user_id = ? OR e.email = ?
         ORDER BY e.created_at DESC`,
        [userId, req.user.email]
      );
      favorites = await db.query(
        `SELECT f.id as fav_id, b.* FROM favorites f
         JOIN bikes b ON f.bike_id = b.id
         WHERE f.user_id = ?
         ORDER BY f.created_at DESC`,
        [userId]
      );
      recentBikes = await db.query(
        'SELECT * FROM bikes WHERE status = "approved" ORDER BY created_at DESC LIMIT 4'
      );
    } else {
      listings = db.fallbackStore.bikes.filter(b => b.seller_id === userId);
      enquiries = db.fallbackStore.enquiries.filter(e => e.user_id === userId || e.email === req.user.email);
      const favIds = db.fallbackStore.favorites.filter(f => f.user_id === userId).map(f => f.bike_id);
      favorites = db.fallbackStore.bikes.filter(b => favIds.includes(b.id));
      recentBikes = db.fallbackStore.bikes.filter(b => b.status === 'approved').slice(0, 4);
    }

    const approvedListings = listings.filter(b => b.status === 'approved').length;
    const pendingListings = listings.filter(b => b.status === 'pending').length;
    const rejectedListings = listings.filter(b => b.status === 'rejected').length;

    return res.json({
      success: true,
      stats: {
        totalListings: listings.length,
        approvedListings,
        pendingListings,
        rejectedListings,
        totalEnquiries: enquiries.length,
        totalFavorites: favorites.length
      },
      listings,
      enquiries,
      favorites,
      recentBikes
    });
  } catch (err) {
    console.error('[UserDashboard Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to load user dashboard.' });
  }
}

/**
 * GET /api/users/listings
 * Bikes listed by current user
 */
async function getUserListings(req, res) {
  try {
    const userId = req.user.id;
    let listings = [];

    if (db.getIsConnected()) {
      listings = await db.query('SELECT * FROM bikes WHERE seller_id = ? ORDER BY created_at DESC', [userId]);
    } else {
      listings = db.fallbackStore.bikes.filter(b => b.seller_id === userId);
    }

    return res.json({
      success: true,
      listings
    });
  } catch (err) {
    console.error('[GetUserListings Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve listings.' });
  }
}

/**
 * GET /api/users/enquiries
 * Enquiries made by current user
 */
async function getUserEnquiries(req, res) {
  try {
    const userId = req.user.id;
    let enquiries = [];

    if (db.getIsConnected()) {
      enquiries = await db.query(
        `SELECT e.*, b.title as bike_title, b.brand as bike_brand, b.model as bike_model,
                b.price as bike_price, b.images as bike_images, b.vehicle_number
         FROM enquiries e
         LEFT JOIN bikes b ON e.bike_id = b.id
         WHERE e.user_id = ? OR e.email = ?
         ORDER BY e.created_at DESC`,
        [userId, req.user.email]
      );
    } else {
      enquiries = db.fallbackStore.enquiries
        .filter(e => e.user_id === userId || e.email === req.user.email)
        .map(e => {
          const b = db.fallbackStore.bikes.find(bike => bike.id === e.bike_id);
          return {
            ...e,
            bike_title: b ? b.title : 'Bike Listing',
            bike_brand: b ? b.brand : '',
            bike_price: b ? b.price : '',
            bike_images: b ? b.images : []
          };
        });
    }

    return res.json({
      success: true,
      enquiries
    });
  } catch (err) {
    console.error('[GetUserEnquiries Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve enquiries.' });
  }
}

/**
 * GET /api/users/favorites
 */
async function getUserFavorites(req, res) {
  try {
    const userId = req.user.id;
    let favorites = [];

    if (db.getIsConnected()) {
      favorites = await db.query(
        `SELECT f.id as fav_id, f.created_at as favorited_at, b.*
         FROM favorites f
         JOIN bikes b ON f.bike_id = b.id
         WHERE f.user_id = ?
         ORDER BY f.created_at DESC`,
        [userId]
      );
    } else {
      const favList = db.fallbackStore.favorites.filter(f => f.user_id === userId);
      favorites = favList.map(f => {
        const bike = db.fallbackStore.bikes.find(b => b.id === f.bike_id);
        return {
          fav_id: f.id,
          favorited_at: f.created_at,
          ...bike
        };
      }).filter(item => item && item.id);
    }

    return res.json({
      success: true,
      favorites
    });
  } catch (err) {
    console.error('[GetUserFavorites Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve favorites.' });
  }
}

/**
 * POST /api/users/favorites/:bikeId
 */
async function addFavorite(req, res) {
  try {
    const userId = req.user.id;
    const bikeId = parseInt(req.params.bikeId, 10);

    if (isNaN(bikeId)) {
      return res.status(400).json({ success: false, message: 'Invalid bike ID.' });
    }

    if (db.getIsConnected()) {
      await db.query(
        'INSERT IGNORE INTO favorites (user_id, bike_id) VALUES (?, ?)',
        [userId, bikeId]
      );
    } else {
      const exists = db.fallbackStore.favorites.some(f => f.user_id === userId && f.bike_id === bikeId);
      if (!exists) {
        db.fallbackStore.favorites.push({
          id: db.fallbackStore.nextId.favorites++,
          user_id: userId,
          bike_id: bikeId,
          created_at: new Date()
        });
      }
    }

    return res.json({ success: true, message: 'Added to favorites.' });
  } catch (err) {
    console.error('[AddFavorite Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to add favorite.' });
  }
}

/**
 * DELETE /api/users/favorites/:bikeId
 */
async function removeFavorite(req, res) {
  try {
    const userId = req.user.id;
    const bikeId = parseInt(req.params.bikeId, 10);

    if (db.getIsConnected()) {
      await db.query('DELETE FROM favorites WHERE user_id = ? AND bike_id = ?', [userId, bikeId]);
    } else {
      db.fallbackStore.favorites = db.fallbackStore.favorites.filter(
        f => !(f.user_id === userId && f.bike_id === bikeId)
      );
    }

    return res.json({ success: true, message: 'Removed from favorites.' });
  } catch (err) {
    console.error('[RemoveFavorite Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to remove favorite.' });
  }
}

module.exports = {
  getProfile,
  updateProfile,
  getUserDashboard,
  getUserListings,
  getUserEnquiries,
  getUserFavorites,
  addFavorite,
  removeFavorite
};
