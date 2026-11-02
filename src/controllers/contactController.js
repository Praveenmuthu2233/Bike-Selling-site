/**
 * Contact Message Controller
 */

const db = require('../config/db');

async function submitContactMessage(req, res) {
  try {
    const { name, email, phone, message } = req.body;
    if (!name || !email || !message) {
      return res.status(400).json({ success: false, message: 'Name, email and message are required fields.' });
    }

    let insertId;
    if (db.getIsConnected()) {
      const result = await db.query(
        'INSERT INTO contact_messages (name, email, phone, message, status) VALUES (?, ?, ?, ?, "unread")',
        [name, email, phone || '', message]
      );
      insertId = result.insertId;
    } else {
      insertId = db.fallbackStore.nextId.contact_messages++;
      db.fallbackStore.contact_messages.unshift({
        id: insertId,
        name,
        email,
        phone: phone || '',
        message,
        status: 'unread',
        created_at: new Date()
      });
    }

    return res.status(201).json({
      success: true,
      message: 'Thank you for reaching out! Your message has been sent to SMR Motors.',
      id: insertId
    });
  } catch (err) {
    console.error('[ContactMessage Error]:', err.message);
    return res.status(500).json({ success: false, message: 'Failed to submit contact message.' });
  }
}

module.exports = {
  submitContactMessage
};
