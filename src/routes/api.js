/**
 * REST API Router
 * SMR Motors Modernization
 */

const express = require('express');
const router = express.Router();

const authController = require('../controllers/authController');
const userController = require('../controllers/userController');
const bikeController = require('../controllers/bikeController');
const enquiryController = require('../controllers/enquiryController');
const adminController = require('../controllers/adminController');
const categoryController = require('../controllers/categoryController');
const contactController = require('../controllers/contactController');

const { userAuth, optionalUserAuth } = require('../middleware/auth');
const { adminAuth } = require('../middleware/adminAuth');
const { upload } = require('../middleware/upload');

/* ==========================================
   AUTHENTICATION ROUTES
   ========================================== */
router.post('/auth/google', authController.googleAuth);
router.post('/auth/demo-google', authController.demoGoogleAuth);
router.post('/auth/logout', authController.logout);
router.get('/auth/me', userAuth, authController.getMe);

/* ==========================================
   USER PANEL ROUTES (Protected by userAuth)
   ========================================== */
router.get('/users/profile', userAuth, userController.getProfile);
router.put('/users/profile', userAuth, userController.updateProfile);
router.get('/users/dashboard', userAuth, userController.getUserDashboard);
router.get('/users/listings', userAuth, userController.getUserListings);
router.get('/users/enquiries', userAuth, userController.getUserEnquiries);
router.get('/users/favorites', userAuth, userController.getUserFavorites);
router.post('/users/favorites/:bikeId', userAuth, userController.addFavorite);
router.delete('/users/favorites/:bikeId', userAuth, userController.removeFavorite);

/* ==========================================
   BIKE MANAGEMENT ROUTES
   ========================================== */
router.get('/bikes', bikeController.getBikes);
router.get('/bikes/:id', bikeController.getBikeById);
router.post('/bikes', optionalUserAuth, upload.array('images', 6), bikeController.createBike);
router.put('/bikes/:id', optionalUserAuth, bikeController.updateBike);
router.delete('/bikes/:id', optionalUserAuth, bikeController.deleteBike);

/* ==========================================
   ENQUIRY ROUTES
   ========================================== */
router.post('/enquiries', optionalUserAuth, enquiryController.createEnquiry);
router.get('/enquiries', enquiryController.getEnquiries);
router.put('/enquiries/:id/status', adminAuth, enquiryController.updateEnquiryStatus);
router.put('/enquiries/:id/message', adminAuth, enquiryController.updateEnquiryMessage);
router.delete('/enquiries/:id', adminAuth, enquiryController.deleteEnquiry);

/* ==========================================
   CATEGORY ROUTES
   ========================================== */
router.get('/categories', categoryController.getCategories);
router.post('/categories', adminAuth, categoryController.createCategory);
router.put('/categories/:id', adminAuth, categoryController.updateCategory);
router.delete('/categories/:id', adminAuth, categoryController.deleteCategory);

/* ==========================================
   CONTACT ROUTES
   ========================================== */
router.post('/contact', contactController.submitContactMessage);

/* ==========================================
   IMAGE UPLOAD ROUTE
   ========================================== */
router.post('/upload/images', upload.array('attachments', 6), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ success: false, message: 'No images uploaded.' });
  }
  const files = req.files.map(f => `/uploads/${f.filename}`);
  return res.json({
    success: true,
    message: 'Images uploaded successfully.',
    files,
    urls: files
  });
});

/* ==========================================
   ADMIN PANEL ROUTES (Protected by adminAuth)
   ========================================== */
router.post('/admin/login', adminController.adminLogin);
router.get('/admin/dashboard', adminAuth, adminController.getAdminDashboard);
router.get('/admin/users', adminAuth, adminController.getAdminUsers);
router.delete('/admin/users/:id', adminAuth, adminController.deleteAdminUser);
router.get('/admin/bikes', adminAuth, adminController.getAdminBikes);
router.put('/admin/bikes/:id/approve', adminAuth, adminController.approveBike);
router.put('/admin/bikes/:id/reject', adminAuth, adminController.rejectBike);
router.put('/admin/bikes/:id/price', adminAuth, adminController.updateBikePrice);
router.put('/admin/bikes/:id/soldout', adminAuth, adminController.markBikeSoldOut);
router.get('/admin/enquiries', adminAuth, enquiryController.getEnquiries);
router.get('/admin/messages', adminAuth, adminController.getAdminMessages);
router.put('/admin/messages/:id/read', adminAuth, adminController.markMessageRead);
router.delete('/admin/messages/:id', adminAuth, adminController.deleteMessage);
router.post('/admin/change-password', adminAuth, adminController.changeAdminPassword);
router.get('/admin/audit-logs', adminAuth, adminController.getAuditLogs);

module.exports = router;
