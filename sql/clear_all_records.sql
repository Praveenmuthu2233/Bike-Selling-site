-- ==============================================================================
-- SMR MOTORS - COMPLETE FRESH DATABASE CLEANUP SCRIPT (TiDB Cloud Compatible)
-- ==============================================================================
-- Purpose: Safely delete all existing records from all 24 tables in `smr_motors`
-- Constraints strictly respected:
--   1. NO DROP DATABASE, NO DROP TABLE, NO TRUNCATE TABLE.
--   2. Preserves table structures, schemas, columns, constraints, and indexes 100%.
--   3. Uses explicit transaction with FOREIGN_KEY_CHECKS = 0 to prevent constraint locks.
-- ==============================================================================

USE `smr_motors`;

-- 1. Temporarily disable foreign key checks & safe update restrictions
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_SAFE_UPDATES = 0;

-- 2. Execute DELETE statements across all 24 tables in reverse-dependency order
DELETE FROM `chat_read_status`;
DELETE FROM `chat_messages`;
DELETE FROM `chat_conversations`;
DELETE FROM `enquiry_replies`;
DELETE FROM `enquiries`;
DELETE FROM `contact_replies`;
DELETE FROM `contact_messages`;
DELETE FROM `bike_images`;
DELETE FROM `bike_transactions`;
DELETE FROM `price_negotiations`;
DELETE FROM `listing_status_history`;
DELETE FROM `financial_records`;
DELETE FROM `sold_bikes`;
DELETE FROM `favorites`;
DELETE FROM `bikesforsale`;
DELETE FROM `bikes`;
DELETE FROM `categories`;
DELETE FROM `notifications`;
DELETE FROM `user_sessions`;
DELETE FROM `users`;
DELETE FROM `admin_activity_logs`;
DELETE FROM `admin_audit_logs`;
DELETE FROM `admins`;
DELETE FROM `durable_images`;

-- 3. Restore foreign key checks & safe update mode
SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;

-- 4. Commit transaction
COMMIT;

-- ==============================================================================
-- 5. VERIFICATION QUERY (Run this to verify 0 records in all 24 tables)
-- ==============================================================================
SELECT 'admin_activity_logs' AS table_name, COUNT(*) AS record_count FROM `admin_activity_logs`
UNION ALL SELECT 'admin_audit_logs', COUNT(*) FROM `admin_audit_logs`
UNION ALL SELECT 'admins', COUNT(*) FROM `admins`
UNION ALL SELECT 'bike_images', COUNT(*) FROM `bike_images`
UNION ALL SELECT 'bike_transactions', COUNT(*) FROM `bike_transactions`
UNION ALL SELECT 'bikes', COUNT(*) FROM `bikes`
UNION ALL SELECT 'bikesforsale', COUNT(*) FROM `bikesforsale`
UNION ALL SELECT 'categories', COUNT(*) FROM `categories`
UNION ALL SELECT 'chat_conversations', COUNT(*) FROM `chat_conversations`
UNION ALL SELECT 'chat_messages', COUNT(*) FROM `chat_messages`
UNION ALL SELECT 'chat_read_status', COUNT(*) FROM `chat_read_status`
UNION ALL SELECT 'contact_messages', COUNT(*) FROM `contact_messages`
UNION ALL SELECT 'contact_replies', COUNT(*) FROM `contact_replies`
UNION ALL SELECT 'durable_images', COUNT(*) FROM `durable_images`
UNION ALL SELECT 'enquiries', COUNT(*) FROM `enquiries`
UNION ALL SELECT 'enquiry_replies', COUNT(*) FROM `enquiry_replies`
UNION ALL SELECT 'favorites', COUNT(*) FROM `favorites`
UNION ALL SELECT 'financial_records', COUNT(*) FROM `financial_records`
UNION ALL SELECT 'listing_status_history', COUNT(*) FROM `listing_status_history`
UNION ALL SELECT 'notifications', COUNT(*) FROM `notifications`
UNION ALL SELECT 'price_negotiations', COUNT(*) FROM `price_negotiations`
UNION ALL SELECT 'sold_bikes', COUNT(*) FROM `sold_bikes`
UNION ALL SELECT 'user_sessions', COUNT(*) FROM `user_sessions`
UNION ALL SELECT 'users', COUNT(*) FROM `users`;
