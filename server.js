/**
 * SMR Motors - Main Application Server
 * Modernized Node.js / Express Server with TiDB Cloud, Google OAuth & REST APIs
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const { initializeDatabase } = require('./src/config/initDb');
const apiRouter = require('./src/routes/api');

// Legacy controller imports for seamless backwards compatibility
const bikeController = require('./src/controllers/bikeController');
const enquiryController = require('./src/controllers/enquiryController');
const adminController = require('./src/controllers/adminController');
const userController = require('./src/controllers/userController');
const { optionalUserAuth, userAuth } = require('./src/middleware/auth');
const { adminAuth } = require('./src/middleware/adminAuth');
const { upload } = require('./src/middleware/upload');

const app = express();
const PORT = process.env.PORT || 5000;

// Security & Parsing Middlewares
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static Directories
const uploadDir = path.join(__dirname, 'public/uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
app.use('/uploads', express.static(uploadDir));
app.use('/public/uploads', express.static(uploadDir));
app.use('/my-node-app/public/uploads', express.static(uploadDir));

// Serve static assets from both my-node-app/static and /static
const staticDir = path.join(__dirname, 'my-node-app/static');
app.use('/my-node-app/static', express.static(staticDir));
app.use('/static', express.static(staticDir));

// Serve public files from both my-node-app/public and /public
const publicDir = path.join(__dirname, 'my-node-app/public');
app.use('/my-node-app/public', express.static(publicDir));
app.use('/public', express.static(publicDir));

// Serve root directory for static images like logo, banner photos
app.use(express.static(__dirname));

// HTML Templates Directory
const templatesDir = path.join(__dirname, 'my-node-app/templates');

// HTML Page Routes - Handles both clean URLs and .html paths
app.get(['/', '/index.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'index.html'));
});

app.get(['/login', '/userLogin.html', '/my-node-app/templates/userLogin.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'userLogin.html'));
});

app.get(['/profile', '/profile.html', '/my-node-app/templates/profile.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'profile.html'));
});

app.get(['/admin', '/admin.html', '/my-node-app/templates/admin.html', '/my-node-app/public/admin.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'admin.html'));
});

app.get(['/sell', '/bikeSelling.html', '/my-node-app/templates/bikeSelling.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'bikeSelling.html'));
});

app.get(['/enquiryBike.html', '/admin-enquiries', '/my-node-app/templates/enquiryBike.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'enquiryBike.html'));
});

app.get(['/listingUserBike.html', '/admin-listings', '/my-node-app/templates/listingUserBike.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'listingUserBike.html'));
});

app.get(['/adminAddListing.html', '/admin-add', '/my-node-app/templates/adminAddListing.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'adminAddListing.html'));
});

app.get(['/SoldOutPage.html', '/soldout', '/my-node-app/templates/SoldOutPage.html'], (req, res, next) => {
  // If API request with authorization header or JSON accept, return JSON data
  if (req.headers.authorization || req.xhr || req.headers.accept?.includes('application/json')) {
    req.query.status = 'soldout';
    return adminController.getAdminBikes(req, res).then ? adminController.getAdminBikes(req, res) : null;
  }
  res.sendFile(path.join(templatesDir, 'SoldOutPage.html'));
});

app.get(['/enquiry-bike-details.html', '/bike-details', '/my-node-app/templates/enquiry-bike-details.html'], (req, res) => {
  res.sendFile(path.join(templatesDir, 'enquiry-bike-details.html'));
});

// Mount Modern REST APIs
app.use('/api', apiRouter);

/* ===================================================
   LEGACY ENDPOINT COMPATIBILITY
   Ensures old frontend scripts continue working seamlessly
   =================================================== */
app.get('/bikes', bikeController.getBikes);
app.get('/bikes/:id', bikeController.getBikeById);
app.post(['/addBike', '/userAddBike'], optionalUserAuth, upload.array('attachments', 6), bikeController.createBike);
app.put('/bikes/:id/accept', adminAuth, adminController.approveBike);
app.put('/bikes/:id/reject', adminAuth, adminController.rejectBike);
app.put('/bikes/:id/price', adminAuth, adminController.updateBikePrice);
app.put('/bikes/:id/soldout', adminAuth, adminController.markBikeSoldOut);

app.get('/enquiries', enquiryController.getEnquiries);
app.post('/enquiries', optionalUserAuth, enquiryController.createEnquiry);
app.delete('/deleteEnquiry/:id', adminAuth, enquiryController.deleteEnquiry);
app.get('/enquiries/:mobile', (req, res, next) => {
  req.query.mobile = req.params.mobile;
  return enquiryController.getEnquiries(req, res, next);
});

app.post('/adminLogin', adminController.adminLogin);
app.get('/adminProfile', adminAuth, (req, res) => {
  res.json({ success: true, admin: req.admin });
});

app.get('/profile', userAuth, userController.getProfile);
app.post(['/upload/gallery', '/upload/attachments'], upload.array('attachments', 6), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ message: 'No files uploaded' });
  }
  const files = req.files.map(f => [f.filename, `/uploads/${f.filename}`]);
  return res.json({ message: 'Files uploaded successfully', files });
});

// Global 404 handler for API routes
app.use('/api/*', (req, res) => {
  res.status(404).json({ success: false, message: `Endpoint ${req.originalUrl} not found.` });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('[Unhandled Server Error]:', err.stack || err.message);
  if (err.name === 'MulterError') {
    return res.status(400).json({ success: false, message: `Upload error: ${err.message}` });
  }
  res.status(500).json({ success: false, message: err.message || 'Internal Server Error' });
});

// Initialize database and start listening
async function startServer() {
  try {
    await initializeDatabase();
  } catch (e) {
    console.warn('[Startup] Database initialization warning:', e.message);
  }

  app.listen(PORT, () => {
    console.log(`===================================================`);
    console.log(`  SMR MOTORS SERVER RUNNING ON PORT ${PORT}`);
    console.log(`  Local URL: http://localhost:${PORT}`);
    console.log(`  User Dashboard: http://localhost:${PORT}/profile.html`);
    console.log(`  Admin Dashboard: http://localhost:${PORT}/admin.html`);
    console.log(`  Google Sign-In: http://localhost:${PORT}/userLogin.html`);
    console.log(`===================================================`);
  });
}

startServer();

module.exports = app;
