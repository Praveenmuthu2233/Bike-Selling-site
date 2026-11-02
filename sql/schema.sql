-- ==============================================================================
-- SMR Motors - TiDB Cloud MySQL 8.0 Compatible Schema
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

-- 4. Bikes Table (Motorcycle Inventory)
CREATE TABLE IF NOT EXISTS `bikes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(160) NOT NULL,
  `brand` VARCHAR(60) NOT NULL,
  `model` VARCHAR(80) NOT NULL,
  `year` INT NOT NULL,
  `price` DECIMAL(12,2) NOT NULL,
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
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_bikes_brand` (`brand`),
  INDEX `idx_bikes_status` (`status`),
  INDEX `idx_bikes_price` (`price`),
  INDEX `idx_bikes_seller` (`seller_id`),
  FOREIGN KEY (`seller_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Enquiries Table (Customer Leads)
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

-- 6. Favorites Table (Saved Vehicles)
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

-- 7. Contact Messages Table (General Inquiries)
CREATE TABLE IF NOT EXISTS `contact_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(191) NOT NULL,
  `phone` VARCHAR(30) NULL,
  `message` TEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'unread',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Admin Audit Logs Table (Accountability & Security)
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
