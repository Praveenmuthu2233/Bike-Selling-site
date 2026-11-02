/**
 * Enquiry Management Controller
 * Handles customer bike enquiries, status tracking, and responses.
 */

const db = require('../config/db');

/**
 * POST /api/enquiries
 */
async function createEnquiry(req, res) {
  try {
    const data = req.body;
    const bikeId = parseInt(data.bike_id || data.listingId, 10);
    const userId = req.user ? req.user.id : (data.user_id || null);
    const name = data.name || data.customerName || 'Customer';
    const email = data.email || (req.user ? req.user.email : '');
    const phone = data.phone || data.mobile || '';
    const message = data.message || '';
    const status = data.status || 'pending';

    if (!phone) {
      return res.status(400).json({ success: false, message: 'Contact phone number is required.' });
    }

    let insertId;
    if (db.getIsConnected()) {
      const sql = `
        INSERT INTO enquiries (user_id, bike_id, name, email, phone, message, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `;
      const result = await db.query(sql, [userId, bikeId || null, name, email, phone, message, status]);
      insertId = result.insertId;
    } else {
      insertId = db.fallbackStore.nextId.enquiries++;
      db.fallbackStore.enquiries.unshift({
        id: insertId,
        user_id: userId,
        bike_id: bikeId || null,
        name,
        email,
        phone,
        message,
        status,
        created_at: new Date()
      });
    }

    return res.status(201).json({
      success: true,
      message: 'Enquiry submitted successfully. Our team will contact you shortly.',
      id: insertId
    });
  } catch (err) {
    console.error('[CreateEnquiry Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to submit enquiry.' });
  }
}

/**
 * GET /api/enquiries
 */
async function getEnquiries(req, res) {
  try {
    const { status, mobile, phone, bikeId } = req.query;

    let enquiries = [];
    if (db.getIsConnected()) {
      let conditions = [];
      let params = [];

      if (status && status !== 'all') {
        conditions.push('e.status = ?');
        params.push(status);
      }

      if (mobile || phone) {
        conditions.push('(e.phone = ? OR e.phone LIKE ?)');
        const p = mobile || phone;
        params.push(p, `%${p}%`);
      }

      if (bikeId) {
        conditions.push('e.bike_id = ?');
        params.push(parseInt(bikeId, 10));
      }

      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
      const sql = `
        SELECT e.*, b.title as listingTitle, b.price as bikePrice, b.vehicle_number as vehicleNumber,
               b.brand as makedFrom, b.model as bikeModel
        FROM enquiries e
        LEFT JOIN bikes b ON e.bike_id = b.id
        ${whereClause}
        ORDER BY e.created_at DESC
      `;
      enquiries = await db.query(sql, params);
    } else {
      enquiries = db.fallbackStore.enquiries.map(e => {
        const bike = db.fallbackStore.bikes.find(b => b.id === e.bike_id);
        return {
          ...e,
          listingTitle: bike ? bike.title : 'Bike Listing',
          bikePrice: bike ? bike.price : '',
          vehicleNumber: bike ? bike.vehicle_number : '',
          makedFrom: bike ? bike.brand : '',
          bikeModel: bike ? bike.model : ''
        };
      });

      if (status && status !== 'all') {
        enquiries = enquiries.filter(e => e.status === status);
      }
      if (mobile || phone) {
        const p = mobile || phone;
        enquiries = enquiries.filter(e => e.phone.includes(p));
      }
      if (bikeId) {
        enquiries = enquiries.filter(e => e.bike_id === parseInt(bikeId, 10));
      }
    }

    // Map legacy fields for backwards compatibility with enquiryBikeScript.js
    const formatted = enquiries.map(e => ({
      ...e,
      listingId: e.bike_id,
      customerName: e.name,
      mobile: e.phone,
      timestamp: e.created_at ? new Date(e.created_at).toLocaleString() : ''
    }));

    if (req.originalUrl === '/enquiries') {
      return res.json(formatted);
    }

    return res.json({
      success: true,
      count: formatted.length,
      enquiries: formatted
    });
  } catch (err) {
    console.error('[GetEnquiries Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to retrieve enquiries.' });
  }
}

/**
 * PUT /api/enquiries/:id/status
 */
async function updateEnquiryStatus(req, res) {
  try {
    const enquiryId = parseInt(req.params.id, 10);
    const { status } = req.body;

    if (!status) {
      return res.status(400).json({ success: false, message: 'Status is required.' });
    }

    if (db.getIsConnected()) {
      await db.query('UPDATE enquiries SET status = ? WHERE id = ?', [status, enquiryId]);
    } else {
      const e = db.fallbackStore.enquiries.find(item => item.id === enquiryId);
      if (e) e.status = status;
    }

    return res.json({ success: true, message: 'Enquiry status updated successfully.' });
  } catch (err) {
    console.error('[UpdateEnquiryStatus Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update enquiry status.' });
  }
}

/**
 * PUT /api/enquiries/:id/message
 */
async function updateEnquiryMessage(req, res) {
  try {
    const enquiryId = parseInt(req.params.id, 10);
    const { message, admin_reply } = req.body;
    const replyText = admin_reply || message || '';

    if (db.getIsConnected()) {
      await db.query('UPDATE enquiries SET admin_reply = ? WHERE id = ?', [replyText, enquiryId]);
    } else {
      const e = db.fallbackStore.enquiries.find(item => item.id === enquiryId);
      if (e) e.admin_reply = replyText;
    }

    return res.json({ success: true, message: 'Enquiry reply updated successfully.' });
  } catch (err) {
    console.error('[UpdateEnquiryMessage Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to update enquiry message.' });
  }
}

/**
 * DELETE /api/enquiries/:id
 */
async function deleteEnquiry(req, res) {
  try {
    const enquiryId = parseInt(req.params.id, 10);

    if (db.getIsConnected()) {
      await db.query('DELETE FROM enquiries WHERE id = ?', [enquiryId]);
    } else {
      db.fallbackStore.enquiries = db.fallbackStore.enquiries.filter(e => e.id !== enquiryId);
    }

    return res.json({ success: true, message: 'Enquiry deleted successfully.' });
  } catch (err) {
    console.error('[DeleteEnquiry Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to delete enquiry.' });
  }
}

module.exports = {
  createEnquiry,
  getEnquiries,
  updateEnquiryStatus,
  updateEnquiryMessage,
  deleteEnquiry
};
