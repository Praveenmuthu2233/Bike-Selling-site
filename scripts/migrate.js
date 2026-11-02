#!/usr/bin/env node
/**
 * Standalone TiDB Cloud Database Migration Runner
 * Usage: npm run migrate
 */

const { initializeDatabase } = require('../src/config/initDb');

async function run() {
  console.log('--- Running TiDB Cloud Migrations ---');
  try {
    await initializeDatabase();
    console.log('--- Migration completed successfully ---');
    process.exit(0);
  } catch (err) {
    console.error('Migration failed:', err);
    process.exit(1);
  }
}

run();
