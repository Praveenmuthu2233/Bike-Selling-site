#!/usr/bin/env node
/**
 * Script to create or update an administrator account
 * Usage: node scripts/seed-admin.js <username> <email> <password> [role]
 */

const bcrypt = require('bcryptjs');
const db = require('../src/config/db');

async function seedAdmin() {
  const args = process.argv.slice(2);
  const username = args[0] || process.env.ADMIN_USERNAME || 'admin';
  const email = args[1] || process.env.ADMIN_EMAIL || 'admin@smrmotors.com';
  const password = args[2] || 'Admin@123';
  const role = args[3] || 'superadmin';

  console.log(`Generating password hash for admin "${username}" (${email})...`);
  const passwordHash = await bcrypt.hash(password, 10);
  console.log(`Password Hash: ${passwordHash}`);

  const connected = await db.testConnection();
  if (connected) {
    try {
      const existing = await db.query('SELECT * FROM admins WHERE username = ? OR email = ?', [username, email]);
      if (existing.length > 0) {
        await db.query(
          'UPDATE admins SET password_hash = ?, role = ? WHERE id = ?',
          [passwordHash, role, existing[0].id]
        );
        console.log(`Successfully updated existing admin account (ID: ${existing[0].id}).`);
      } else {
        const res = await db.query(
          'INSERT INTO admins (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
          [username, email, passwordHash, role]
        );
        console.log(`Successfully created new admin account with ID: ${res.insertId}`);
      }
    } catch (err) {
      console.error('Database error:', err.message);
    }
  } else {
    console.log('TiDB Cloud not connected. Added admin to in-memory fallback store.');
    db.fallbackStore.admins.push({
      id: db.fallbackStore.nextId.admins++,
      username,
      email,
      password_hash: passwordHash,
      role,
      created_at: new Date()
    });
  }

  console.log('\nYou can put this in your .env:');
  console.log(`ADMIN_USERNAME=${username}`);
  console.log(`ADMIN_EMAIL=${email}`);
  console.log(`ADMIN_PASSWORD_HASH=${passwordHash}\n`);
  process.exit(0);
}

seedAdmin();
