-- ==============================================================================
-- SMR Motors - TiDB Cloud MySQL 8.0 Compatible Schema (Complete 24 Tables)
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `smr_motors` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `smr_motors`;

-- 1. Users Table (Google OAuth 2.0 & Session Profile)
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `google_id` VARCHAR(191) NULL UNIQUE,
  `name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(191) NOT NULL UNIQUE,
  `profile_image` VARCHAR(500) NULL,
  `phone` VARCHAR(25) NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_users_email` (`email`),
  INDEX `idx_users_google_id` (`google_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Admins Table (Secure Isolated Admin Auth)
CREATE TABLE IF NOT EXISTS `admins` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(60) NOT NULL UNIQUE,
  `email` VARCHAR(191) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'admin',
  `last_login` TIMESTAMP NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_admins_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Categories Table
CREATE TABLE IF NOT EXISTS `categories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `category_name` VARCHAR(80) NOT NULL UNIQUE,
  `description` TEXT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bikes Table (Motorcycle Inventory & Negotiation Lifecycle)
CREATE TABLE IF NOT EXISTS `bikes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(160) NOT NULL,
  `brand` VARCHAR(60) NOT NULL,
  `model` VARCHAR(80) NOT NULL,
  `year` INT NOT NULL,
  `price` DECIMAL(12,2) NOT NULL,
  `requested_price` DECIMAL(12,2) NULL,
  `proposed_seller_payout` DECIMAL(12,2) NULL,
  `accepted_seller_payout` DECIMAL(12,2) NULL,
  `public_selling_price` DECIMAL(12,2) NULL,
  `listing_status` VARCHAR(40) NOT NULL DEFAULT 'pending',
  `negotiation_status` VARCHAR(40) NOT NULL DEFAULT 'pending',
  `kilometers_driven` INT NOT NULL DEFAULT 0,
  `fuel_type` VARCHAR(30) NOT NULL DEFAULT 'Petrol',
  `transmission` VARCHAR(30) NOT NULL DEFAULT 'Manual',
  `description` TEXT NULL,
  `images` JSON NULL,
  `seller_id` INT NULL,
  `seller_name` VARCHAR(100) NULL,
  `seller_phone` VARCHAR(30) NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `rejection_reason` TEXT NULL,
  `featured` TINYINT(1) NOT NULL DEFAULT 0,
  `registration_number` VARCHAR(50) NULL,
  `location` VARCHAR(120) NULL,
  `approved_by` VARCHAR(60) NULL,
  `approved_at` TIMESTAMP NULL,
  `rejected_by` VARCHAR(60) NULL,
  `rejected_at` TIMESTAMP NULL,
  `buying_price` DECIMAL(12,2) NULL,
  `expenses` DECIMAL(12,2) DEFAULT 0,
  `profit` DECIMAL(12,2) DEFAULT 0,
  `isSoldout` TINYINT(1) DEFAULT 0,
  `sold_by` VARCHAR(60) NULL,
  `sold_at` TIMESTAMP NULL,
  `sold_snapshot` JSON NULL,
  `seller_agreement_at` TIMESTAMP NULL,
  `published_at` TIMESTAMP NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_bikes_brand` (`brand`),
  INDEX `idx_bikes_status` (`status`),
  INDEX `idx_bikes_listing_status` (`listing_status`),
  INDEX `idx_bikes_price` (`price`),
  INDEX `idx_bikes_seller` (`seller_id`),
  FOREIGN KEY (`seller_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4a. Listing Status History Table
CREATE TABLE IF NOT EXISTS `listing_status_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `old_status` VARCHAR(40) NULL,
  `new_status` VARCHAR(40) NOT NULL,
  `changed_by` VARCHAR(60) NOT NULL DEFAULT 'system',
  `reason` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_lsh_bike` (`bike_id`),
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4b. Price Negotiations Table (Counteroffers & Margin Transparency)
CREATE TABLE IF NOT EXISTS `price_negotiations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `seller_id` INT NULL,
  `admin_id` INT NULL,
  `requested_price` DECIMAL(12,2) NULL,
  `proposed_payout` DECIMAL(12,2) NOT NULL,
  `counteroffer_number` INT NOT NULL DEFAULT 1,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `message` TEXT NULL,
  `seller_response_note` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `responded_at` TIMESTAMP NULL,
  INDEX `idx_pneg_bike` (`bike_id`),
  INDEX `idx_pneg_seller` (`seller_id`),
  INDEX `idx_pneg_status` (`status`),
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4c. Bike Transactions Table (Sold Out Financial Records)
CREATE TABLE IF NOT EXISTS `bike_transactions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `seller_id` INT NULL,
  `admin_id` INT NULL,
  `seller_payout` DECIMAL(12,2) NOT NULL,
  `actual_sale_price` DECIMAL(12,2) NOT NULL,
  `service_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `repair_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `transport_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `other_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `total_expenses` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `realized_profit` DECIMAL(12,2) NOT NULL,
  `buyer_name` VARCHAR(100) NULL,
  `buyer_phone` VARCHAR(30) NULL,
  `sold_by` VARCHAR(60) NULL,
  `sold_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `notes` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_tx_bike` (`bike_id`),
  INDEX `idx_tx_seller` (`seller_id`),
  INDEX `idx_tx_sold_at` (`sold_at`),
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4c-1. Sold Bikes Table (Sold Out Management permanent archive)
CREATE TABLE IF NOT EXISTS `sold_bikes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL UNIQUE,
  `title` VARCHAR(160) NOT NULL,
  `brand` VARCHAR(60) NOT NULL,
  `model` VARCHAR(80) NOT NULL,
  `year` INT NOT NULL,
  `price` DECIMAL(12,2) NOT NULL,
  `kilometers_driven` INT NOT NULL DEFAULT 0,
  `fuel_type` VARCHAR(30) NOT NULL DEFAULT 'Petrol',
  `transmission` VARCHAR(30) NOT NULL DEFAULT 'Manual',
  `seller_id` INT NULL,
  `seller_name` VARCHAR(100) NULL,
  `seller_phone` VARCHAR(30) NULL,
  `seller_payout` DECIMAL(12,2) NULL,
  `actual_sale_price` DECIMAL(12,2) NOT NULL,
  `total_expenses` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `realized_profit` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `buyer_name` VARCHAR(100) NULL,
  `buyer_phone` VARCHAR(30) NULL,
  `sold_by` VARCHAR(60) NULL,
  `sold_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_sold_bikes_bike_id` (`bike_id`),
  INDEX `idx_sold_bikes_brand` (`brand`),
  INDEX `idx_sold_bikes_sold_at` (`sold_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4c-2. Financial Records Table
CREATE TABLE IF NOT EXISTS `financial_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `transaction_type` VARCHAR(50) NOT NULL DEFAULT 'sale',
  `requested_price` DECIMAL(12,2) NULL,
  `buying_price` DECIMAL(12,2) NULL,
  `seller_payout` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `selling_price` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `service_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `repair_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `transport_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `other_expense` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `total_expenses` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `estimated_profit` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `actual_profit` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `recorded_by` VARCHAR(60) NULL,
  `notes` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_fin_bike` (`bike_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 4c-3. Buyer Details Table (Customer Sale Information)
CREATE TABLE IF NOT EXISTS `buyer_details` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `full_name` VARCHAR(120) NOT NULL,
  `phone` VARCHAR(30) NOT NULL,
  `alt_phone` VARCHAR(30) NULL,
  `email` VARCHAR(191) NULL,
  `location` VARCHAR(120) NOT NULL,
  `city` VARCHAR(80) NOT NULL,
  `state` VARCHAR(80) NOT NULL DEFAULT 'Tamil Nadu',
  `address` TEXT NULL,
  `pincode` VARCHAR(20) NULL,
  `consent_obtained` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_bd_bike` (`bike_id`),
  INDEX `idx_bd_phone` (`phone`),
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4c-4. Sale Documents Table (Identity Proof & Secure Sale Attachments)
CREATE TABLE IF NOT EXISTS `sale_documents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `buyer_id` INT NULL,
  `document_type` VARCHAR(60) NOT NULL,
  `document_ref_masked` VARCHAR(80) NULL,
  `file_name` VARCHAR(255) NULL,
  `mime_type` VARCHAR(100) NULL,
  `file_size` INT NULL DEFAULT 0,
  `file_data` LONGBLOB NULL,
  `uploaded_by` VARCHAR(60) NOT NULL DEFAULT 'admin',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_sd_bike` (`bike_id`),
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4d. Bike Images Table (6-Image Gallery)
CREATE TABLE IF NOT EXISTS `bike_images` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bike_id` INT NOT NULL,
  `image_url` VARCHAR(500) NOT NULL,
  `image_order` INT NOT NULL DEFAULT 1,
  `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_bi_bike` (`bike_id`),
  INDEX `idx_bi_order` (`bike_id`, `image_order`),
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4e. Bikes For Sale Table (Legacy Compatibility)
CREATE TABLE IF NOT EXISTS `bikesforsale` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `listingTitle` VARCHAR(255),
  `vehicleNumber` VARCHAR(255),
  `sellerName` VARCHAR(255),
  `mobileNum` VARCHAR(20),
  `bikeCondition` VARCHAR(50),
  `bikeType` VARCHAR(50),
  `makedFrom` VARCHAR(50),
  `bikeModel` VARCHAR(100),
  `bikeKms` VARCHAR(50),
  `bikePrice` VARCHAR(50),
  `sellingPrice` VARCHAR(50),
  `bikeOwner` VARCHAR(50),
  `bikeBuyingYear` VARCHAR(10),
  `bikeColor` VARCHAR(50),
  `bikeEngineCC` VARCHAR(50),
  `driveType` VARCHAR(50),
  `insurance` VARCHAR(50),
  `horsepower` VARCHAR(50),
  `bikeLocation` VARCHAR(255),
  `description` TEXT,
  `isAccepted` BOOLEAN DEFAULT TRUE,
  `isSoldout` BOOLEAN DEFAULT FALSE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Notifications Table (User & Admin Alerts)
CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `target_role` VARCHAR(20) NOT NULL DEFAULT 'user',
  `title` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `type` VARCHAR(50) NOT NULL DEFAULT 'info',
  `link` VARCHAR(255) NULL,
  `is_read` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_notif_user` (`user_id`),
  INDEX `idx_notif_role` (`target_role`),
  INDEX `idx_notif_read` (`is_read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Enquiries Table (Customer Leads)
CREATE TABLE IF NOT EXISTS `enquiries` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `bike_id` INT NULL,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(191) NOT NULL,
  `phone` VARCHAR(30) NOT NULL,
  `message` TEXT NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `admin_notes` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_enquiries_user` (`user_id`),
  INDEX `idx_enquiries_bike` (`bike_id`),
  INDEX `idx_enquiries_status` (`status`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6b. Enquiry Replies Table
CREATE TABLE IF NOT EXISTS `enquiry_replies` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `enquiry_id` INT NOT NULL,
  `admin_id` INT NULL,
  `admin_username` VARCHAR(60) NULL,
  `reply_message` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_er_enquiry` (`enquiry_id`),
  FOREIGN KEY (`enquiry_id`) REFERENCES `enquiries`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Favorites Table (Saved Vehicles)
CREATE TABLE IF NOT EXISTS `favorites` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `bike_id` INT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uniq_user_bike_fav` (`user_id`, `bike_id`),
  INDEX `idx_fav_user` (`user_id`),
  INDEX `idx_fav_bike` (`bike_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`bike_id`) REFERENCES `bikes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Contact Messages Table
CREATE TABLE IF NOT EXISTS `contact_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(191) NOT NULL,
  `phone` VARCHAR(30) NULL,
  `subject` VARCHAR(255) NOT NULL DEFAULT 'General Inquiry',
  `message` TEXT NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'unread',
  `email_delivery_status` VARCHAR(50) NOT NULL DEFAULT 'pending',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_contact_email` (`email`),
  INDEX `idx_contact_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8b. Contact Replies Table
CREATE TABLE IF NOT EXISTS `contact_replies` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `contact_message_id` INT NOT NULL,
  `admin_id` INT NULL,
  `admin_username` VARCHAR(60) NULL,
  `reply_message` TEXT NOT NULL,
  `sent_status` VARCHAR(50) NOT NULL DEFAULT 'sent',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_cr_msg` (`contact_message_id`),
  INDEX `idx_cr_admin` (`admin_id`),
  FOREIGN KEY (`contact_message_id`) REFERENCES `contact_messages`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Admin Audit Logs Table
CREATE TABLE IF NOT EXISTS `admin_audit_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_id` INT NULL,
  `admin_username` VARCHAR(60) NOT NULL,
  `action` VARCHAR(60) NOT NULL,
  `target_type` VARCHAR(40) NOT NULL,
  `target_id` VARCHAR(60) NULL,
  `details` TEXT NULL,
  `ip_address` VARCHAR(45) NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_audit_admin` (`admin_id`),
  INDEX `idx_audit_action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9b. Admin Activity Logs Table
CREATE TABLE IF NOT EXISTS `admin_activity_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_id` INT NULL,
  `admin_username` VARCHAR(60) NOT NULL,
  `action` VARCHAR(60) NOT NULL,
  `details` TEXT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_aal_admin` (`admin_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Customer Support Chat Conversations Table
CREATE TABLE IF NOT EXISTS `chat_conversations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `subject` VARCHAR(255) NOT NULL DEFAULT 'General Support Inquiry',
  `bike_id` INT NULL,
  `status` VARCHAR(50) NOT NULL DEFAULT 'open',
  `assigned_admin_id` INT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_conv_user` (`user_id`),
  INDEX `idx_conv_bike` (`bike_id`),
  INDEX `idx_conv_status` (`status`),
  INDEX `idx_conv_assigned` (`assigned_admin_id`),
  INDEX `idx_conv_updated` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Customer Support Chat Messages Table
CREATE TABLE IF NOT EXISTS `chat_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `conversation_id` INT NOT NULL,
  `sender_id` INT NOT NULL,
  `sender_role` VARCHAR(20) NOT NULL,
  `message` TEXT NOT NULL,
  `is_read` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_msg_conv` (`conversation_id`),
  INDEX `idx_msg_sender` (`sender_id`),
  INDEX `idx_msg_read` (`is_read`),
  INDEX `idx_msg_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Customer Support Chat Read Receipts Table
CREATE TABLE IF NOT EXISTS `chat_read_status` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `conversation_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `last_read_message_id` INT NOT NULL DEFAULT 0,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_conv_user` (`conversation_id`, `user_id`),
  INDEX `idx_crs_conv` (`conversation_id`),
  INDEX `idx_crs_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. User Sessions Table
CREATE TABLE IF NOT EXISTS `user_sessions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_token` VARCHAR(128) NOT NULL UNIQUE,
  `user_id` INT NOT NULL,
  `ip_address` VARCHAR(45) NULL,
  `user_agent` TEXT NULL,
  `expires_at` TIMESTAMP NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_us_token` (`session_token`),
  INDEX `idx_us_user` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. Durable Persistent Images Table (Longblob binary store)
CREATE TABLE IF NOT EXISTS `durable_images` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `filename` VARCHAR(255) NOT NULL UNIQUE,
  `mime_type` VARCHAR(100) NOT NULL DEFAULT 'image/jpeg',
  `file_size` INT NOT NULL DEFAULT 0,
  `image_data` LONGBLOB NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_di_filename` (`filename`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
