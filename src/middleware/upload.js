/**
 * Secure Multer File Upload Middleware
 * Implements type whitelisting, size restrictions, and unique filename generation.
 */

const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Ensure upload directory exists in both public/uploads and my-node-app/public/uploads
const uploadDir = path.join(__dirname, '../../public/uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const myNodeUploadDir = path.join(__dirname, '../../my-node-app/public/uploads');
if (!fs.existsSync(myNodeUploadDir)) {
  fs.mkdirSync(myNodeUploadDir, { recursive: true });
}

// Allowed MIME types whitelist
const ALLOWED_MIME_TYPES = [
  'image/jpeg',
  'image/jpg',
  'image/png',
  'image/webp',
  'image/avif'
];

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    // Generate secure sanitized unique filename: timestamp-random-cleaned.ext
    const cleanName = file.originalname.replace(/[^a-zA-Z0-9.-]/g, '_');
    const ext = path.extname(cleanName).toLowerCase();
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    const finalFilename = `bike-${uniqueSuffix}${ext}`;
    
    // Also copy to myNodeUploadDir on file write if needed
    cb(null, finalFilename);
  }
});

function fileFilter(req, file, cb) {
  if (ALLOWED_MIME_TYPES.includes(file.mimetype.toLowerCase())) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type: ${file.mimetype}. Allowed types: JPEG, PNG, WebP, AVIF.`), false);
  }
}

// Multer instance with 5MB limit and max 6 files
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB max per image
    files: 6 // Maximum 6 images per bike listing
  },
  fileFilter: fileFilter
});

module.exports = {
  upload,
  uploadDir
};
