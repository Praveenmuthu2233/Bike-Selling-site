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

// 1. Static Assets & Uploads
const uploadDir = path.join(__dirname, 'public/uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
app.use('/uploads', express.static(uploadDir));
app.use('/public/uploads', express.static(uploadDir));
app.use('/my-node-app/public/uploads', express.static(uploadDir));

// Clean Structured Assets (/assets)
app.use('/assets', express.static(path.join(__dirname, 'assets')));

// Admin & User directories static resources (css, js)
app.use('/admin', express.static(path.join(__dirname, 'admin')));
app.use('/user', express.static(path.join(__dirname, 'user')));

// Legacy static and public directories fallback
const staticDir = path.join(__dirname, 'my-node-app/static');
app.use('/my-node-app/static', express.static(staticDir));
app.use('/static', express.static(staticDir));

const publicDir = path.join(__dirname, 'my-node-app/public');
app.use('/my-node-app/public', express.static(publicDir));
app.use('/public', express.static(publicDir));

// Serve root directory
app.use(express.static(__dirname));

// 2. HTML Page Routes (Clean URLs & Modern File Mapping)

// Homepage
app.get(['/', '/index.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// About & Contact
app.get(['/about', '/about.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'about.html'));
});

app.get(['/contact', '/contact.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'contact.html'));
});

// Auth: Login & Register
app.get(['/login', '/login.html', '/userLogin.html', '/my-node-app/templates/userLogin.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'login.html'));
});

app.get(['/register', '/register.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'register.html'));
});

// Vehicle Details
app.get(['/bike-details', '/bike-details.html', '/enquiry-bike-details.html', '/my-node-app/templates/enquiry-bike-details.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'bike-details.html'));
});

// Sell Bike
app.get(['/sell', '/sell-bike.html', '/bikeSelling.html', '/my-node-app/templates/bikeSelling.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'sell-bike.html'));
});

// Sold Inventory Gallery
app.get(['/sold', '/sold-bikes.html', '/SoldOutPage.html', '/soldout', '/my-node-app/templates/SoldOutPage.html'], (req, res, next) => {
  if (req.headers.authorization || req.xhr || req.headers.accept?.includes('application/json')) {
    req.query.status = 'soldout';
    return adminController.getAdminBikes(req, res).then ? adminController.getAdminBikes(req, res) : null;
  }
  res.sendFile(path.join(__dirname, 'sold-bikes.html'));
});

// User Dashboard & Sub-pages
app.get(['/user/dashboard', '/user/dashboard.html', '/profile', '/profile.html', '/my-node-app/templates/profile.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'user/dashboard.html'));
});

app.get(['/user/profile', '/user/profile.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'user/profile.html'));
});

app.get(['/user/my-listings', '/user/my-listings.html', '/listingUserBike.html', '/admin-listings', '/my-node-app/templates/listingUserBike.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'user/my-listings.html'));
});

app.get(['/user/enquiries', '/user/enquiries.html', '/enquiryBike.html', '/admin-enquiries', '/my-node-app/templates/enquiryBike.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'user/enquiries.html'));
});

app.get(['/user/favorites', '/user/favorites.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'user/favorites.html'));
});

// Admin Console & Sub-pages
app.get(['/admin/login', '/admin/login.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'admin/login.html'));
});

app.get(['/admin', '/admin/', '/admin/dashboard', '/admin/dashboard.html', '/admin.html', '/my-node-app/templates/admin.html', '/my-node-app/public/admin.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'admin/dashboard.html'));
});

app.get(['/admin/users', '/admin/users.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'admin/users.html'));
});

app.get(['/adminAddListing.html', '/admin-add', '/my-node-app/templates/adminAddListing.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'sell-bike.html'));
});

// Mount Modern REST APIs
app.use('/api', apiRouter);

/* ===================================================
   LEGACY ENDPOINT COMPATIBILITY
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

app.get('/profile-data', userAuth, userController.getProfile);
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
    console.log(`  Marketplace: http://localhost:${PORT}/`);
    console.log(`  User Dashboard: http://localhost:${PORT}/user/dashboard.html`);
    console.log(`  Admin Portal: http://localhost:${PORT}/admin/dashboard.html`);
    console.log(`  Google Sign-In: http://localhost:${PORT}/login.html`);
    console.log(`===================================================`);
  });
}

startServer();

module.exports = app;
