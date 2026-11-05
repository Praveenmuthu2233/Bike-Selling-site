-- ==============================================================================
-- SMR MOTORS - 24 TABLES RECORD COUNT VERIFICATION QUERY
-- ==============================================================================
USE `smr_motors`;

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
