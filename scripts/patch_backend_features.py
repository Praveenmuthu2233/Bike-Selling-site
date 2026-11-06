import os
import sys

backend_file = 'my-node-app/app.py'
with open(backend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add bike_documents and sale_documents to initialize_database()
target_init_str = "CREATE TABLE IF NOT EXISTS `durable_images`"
idx_init = content.find(target_init_str)
assert idx_init != -1, "durable_images not found in app.py"

end_durable_idx = content.find("conn.commit()", idx_init)
assert end_durable_idx != -1, "conn.commit() after durable_images not found"

doc_tables_sql = """
        # 12. bike_documents table (Secure Customer Ownership Documents: RC, Insurance, Owner ID, etc.)
        cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS `bike_documents` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `bike_id` INT NOT NULL,
          `user_id` INT NOT NULL,
          `document_type` VARCHAR(50) NOT NULL,
          `file_name` VARCHAR(255) NOT NULL,
          `file_path` VARCHAR(500) NOT NULL,
          `mime_type` VARCHAR(100) NOT NULL,
          `file_size` INT NOT NULL,
          `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
          `admin_remarks` TEXT NULL,
          `verified_by` VARCHAR(60) NULL,
          `verified_at` TIMESTAMP NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX `idx_bikedoc_bike` (`bike_id`),
          INDEX `idx_bikedoc_user` (`user_id`),
          INDEX `idx_bikedoc_status` (`status`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        \"\"\")

        # 13. sale_documents table (Secure Handover Proof)
        cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS `sale_documents` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `bike_id` INT NOT NULL,
          `buyer_id` INT NULL,
          `document_type` VARCHAR(50) NOT NULL DEFAULT 'identity_proof',
          `document_ref_masked` VARCHAR(100) NULL,
          `file_name` VARCHAR(255) NOT NULL,
          `mime_type` VARCHAR(100) NOT NULL DEFAULT 'application/octet-stream',
          `file_size` INT NOT NULL DEFAULT 0,
          `file_data` LONGBLOB NULL,
          `file_path` VARCHAR(500) NULL,
          `uploaded_by` VARCHAR(60) NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_saledoc_bike` (`bike_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        \"\"\")

        # Incremental schema migrations
        try:
            cursor.execute("ALTER TABLE `enquiries` ADD COLUMN `user_id` INT NULL")
            conn.commit()
        except Exception:
            pass
"""

# Insert before conn.commit()
if "CREATE TABLE IF NOT EXISTS `bike_documents`" not in content:
    content = content[:end_durable_idx] + doc_tables_sql + "\n        " + content[end_durable_idx:]
    print("Added bike_documents and sale_documents tables to initialize_database()")
else:
    print("bike_documents table already present in initialize_database()")

with open(backend_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py database init section.")
