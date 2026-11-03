import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'my-node-app'))
from app import get_db, initialize_database

print("Executing initialize_database() to create tables in TiDB Cloud...")
conn = get_db()
if not conn:
    print("Failed to get DB connection")
    sys.exit(1)

cursor = conn.cursor()

# 1. sold_bikes table
print("Creating sold_bikes table...")
cursor.execute("""
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
""")

# 2. financial_records table
print("Creating financial_records table...")
cursor.execute("""
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
  INDEX `idx_fin_bike` (`bike_id`),
  INDEX `idx_fin_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
""")

# 3. admin_activity_logs table
print("Creating admin_activity_logs table...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS `admin_activity_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_id` INT NULL,
  `admin_username` VARCHAR(60) NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'admin',
  `action` VARCHAR(60) NOT NULL,
  `target_type` VARCHAR(40) NOT NULL,
  `target_id` VARCHAR(60) NULL,
  `details` TEXT NULL,
  `ip_address` VARCHAR(45) NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_act_admin` (`admin_id`),
  INDEX `idx_act_action` (`action`),
  INDEX `idx_act_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
""")

# Also ensure sold_by column in bike_transactions
try:
    cursor.execute("ALTER TABLE `bike_transactions` ADD COLUMN `sold_by` VARCHAR(60) NULL")
except Exception:
    pass

conn.commit()

# Verify all tables now
cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]
print("Updated TiDB tables list:", sorted(tables))

required = ['bike_images', 'sold_bikes', 'admin_activity_logs', 'financial_records', 'bike_transactions', 'bikes']
for req in required:
    if req in tables:
        print(f"  [OK] Table '{req}' is confirmed present in TiDB Cloud.")
    else:
        print(f"  [FAIL] Table '{req}' missing!")

cursor.close()
conn.close()
print("Migration completed successfully.")
