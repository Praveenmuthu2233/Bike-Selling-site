/**
 * TiDB Cloud Database Migration & Initialization Script
 * Creates tables, relationships, indexes, and default seeds.
 */

const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const db = require('./db');

const TABLE_SCHEMAS = [
  // 1. users
  `CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    profile_image VARCHAR(500),
    phone VARCHAR(30),
    role VARCHAR(50) DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_google_id (google_id),
    INDEX idx_user_email (email)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 2. admins
  `CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_username (username),
    INDEX idx_admin_email (email)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 3. categories
  `CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cat_status (status)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 4. bikes
  `CREATE TABLE IF NOT EXISTS bikes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year VARCHAR(10),
    price DECIMAL(12,2) NOT NULL,
    selling_price DECIMAL(12,2),
    kilometers_driven VARCHAR(50),
    fuel_type VARCHAR(50) DEFAULT 'Petrol',
    transmission VARCHAR(50) DEFAULT 'Manual',
    description TEXT,
    images JSON,
    seller_id INT,
    seller_name VARCHAR(255),
    seller_phone VARCHAR(50),
    vehicle_number VARCHAR(100),
    bike_condition VARCHAR(50),
    bike_color VARCHAR(50),
    engine_cc VARCHAR(50),
    insurance VARCHAR(50),
    horsepower VARCHAR(50),
    location VARCHAR(255),
    category_id INT,
    status ENUM('pending', 'approved', 'rejected', 'soldout') DEFAULT 'pending',
    rejection_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_bike_status (status),
    INDEX idx_bike_brand (brand),
    INDEX idx_bike_price (price),
    INDEX idx_bike_seller (seller_id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 5. enquiries
  `CREATE TABLE IF NOT EXISTS enquiries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    bike_id INT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50) NOT NULL,
    message TEXT,
    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
    admin_reply TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_enquiry_user (user_id),
    INDEX idx_enquiry_bike (bike_id),
    INDEX idx_enquiry_status (status)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 6. favorites
  `CREATE TABLE IF NOT EXISTS favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bike_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY user_bike_fav (user_id, bike_id),
    INDEX idx_fav_user (user_id),
    INDEX idx_fav_bike (bike_id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 7. contact_messages
  `CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    message TEXT NOT NULL,
    status ENUM('unread', 'read', 'archived') DEFAULT 'unread',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_msg_status (status)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,

  // 8. admin_audit_logs
  `CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    username VARCHAR(100),
    action VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_created (created_at)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`
];

async function initializeDatabase() {
  console.log('[Migration] Checking TiDB Cloud database schema...');
  const connected = await db.testConnection();

  if (!connected) {
    console.log('[Migration] Offline fallback initialized with in-memory stores & seed data.');
    return;
  }

  const pool = db.getPool();
  const conn = await pool.getConnection();

  try {
    for (const sql of TABLE_SCHEMAS) {
      await conn.query(sql);
    }
    console.log('[Migration] All 8 TiDB tables verified/created successfully.');

    // Seed Categories if empty
    const [catRows] = await conn.query('SELECT COUNT(*) AS cnt FROM categories');
    if (catRows[0].cnt === 0) {
      const catPath = path.join(__dirname, '../../category.json');
      if (fs.existsSync(catPath)) {
        const catData = JSON.parse(fs.readFileSync(catPath, 'utf8'));
        for (const c of catData) {
          await conn.query(
            'INSERT INTO categories (category_name, description, image_url, status) VALUES (?, ?, ?, ?)',
            [c.bikeName || 'Standard', `${c.bikeName} collection`, c.imageUrl, 'active']
          );
        }
        console.log(`[Migration] Seeded ${catData.length} categories.`);
      }
    }

    // Seed Initial Admin if no admins exist
    const [adminRows] = await conn.query('SELECT COUNT(*) AS cnt FROM admins');
    if (adminRows[0].cnt === 0) {
      const adminUsername = process.env.ADMIN_USERNAME || 'admin';
      const adminEmail = process.env.ADMIN_EMAIL || 'admin@smrmotors.com';
      let passwordHash = process.env.ADMIN_PASSWORD_HASH;

      if (!passwordHash) {
        // Default secure bcrypt hash for placeholder initial setup
        passwordHash = await bcrypt.hash('Admin@123', 10);
      }

      await conn.query(
        'INSERT INTO admins (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
        [adminUsername, adminEmail, passwordHash, 'superadmin']
      );
      console.log(`[Migration] Created initial admin account (${adminUsername}).`);
    }

    // Seed Bikes from data.json if empty
    const [bikeRows] = await conn.query('SELECT COUNT(*) AS cnt FROM bikes');
    if (bikeRows[0].cnt === 0) {
      const dataPath = path.join(__dirname, '../../data.json');
      if (fs.existsSync(dataPath)) {
        const bikeData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
        const brands = ['KTM', 'Royal Enfield', 'Hero', 'Yamaha', 'Honda', 'Bajaj', 'TVS'];
        for (let idx = 0; idx < bikeData.length; idx++) {
          const b = bikeData[idx];
          const matchedBrand = brands.find(br => b.name.toLowerCase().includes(br.toLowerCase())) || 'Other';
          const price = 45000 + (idx * 8500);
          await conn.query(
            `INSERT INTO bikes (
              title, brand, model, year, price, selling_price, kilometers_driven,
              fuel_type, transmission, description, images, seller_id, seller_name,
              seller_phone, vehicle_number, bike_condition, bike_color, engine_cc,
              insurance, horsepower, location, category_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [
              b.name,
              matchedBrand,
              b.name,
              '2022',
              price,
              price + 4000,
              '15000',
              'Petrol',
              'Manual',
              `Well maintained ${b.name} in pristine condition. Single owner, all service records available.`,
              JSON.stringify([b.image]),
              1,
              'SMR Motors',
              '+91 7845215164',
              `TN 07 AB 100${idx}`,
              'Good',
              'Black',
              '150cc',
              'Yes',
              'Yes',
              'Kelambakkam, Chennai',
              1,
              'approved'
            ]
          );
        }
        console.log(`[Migration] Seeded ${bikeData.length} sample bikes from data.json.`);
      }
    }
  } catch (err) {
    console.error('[Migration Error]:', err.message);
  } finally {
    conn.release();
  }
}

module.exports = {
  initializeDatabase,
  TABLE_SCHEMAS
};
