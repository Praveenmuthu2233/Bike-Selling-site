import os
import sys
from dotenv import load_dotenv

# Load env from my-node-app/.env
env_path = os.path.join(os.path.dirname(__file__), '..', 'my-node-app', '.env')
load_dotenv(dotenv_path=env_path)

import mysql.connector

def run_migration():
    host = os.getenv("DB_HOST", "gateway01.ap-southeast-1.prod.aws.tidbcloud.com")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "smr_motors")
    port = int(os.getenv("DB_PORT", 4000))

    print(f"Connecting to TiDB Cloud {host}:{port} db={database} user={user}...")
    
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )
    cursor = conn.cursor()

    # Create user_sessions table
    print("Creating user_sessions table if not exists...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_sessions` (
      `id` INT AUTO_INCREMENT PRIMARY KEY,
      `user_id` INT NOT NULL,
      `token_hash` VARCHAR(64) NOT NULL,
      `ip_address` VARCHAR(45) NULL,
      `user_agent` VARCHAR(255) NULL,
      `expires_at` TIMESTAMP NOT NULL,
      `is_revoked` TINYINT(1) NOT NULL DEFAULT 0,
      `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX `idx_us_token_hash` (`token_hash`),
      INDEX `idx_us_user_id` (`user_id`),
      INDEX `idx_us_expires` (`expires_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # Verify existing tables
    cursor.execute("SHOW TABLES")
    tables = [r[0] for r in cursor.fetchall()]
    print("Tables in TiDB Cloud database:", tables)

    # Test accurate count queries
    cursor.execute("""
        SELECT
            COUNT(*) as total_bikes,
            SUM(CASE WHEN (status = 'pending' OR listing_status = 'pending') 
                          AND (isSoldout IS NULL OR isSoldout = 0) 
                          AND COALESCE(status, '') NOT IN ('sold', 'soldout', 'rejected', 'archived') 
                          AND COALESCE(listing_status, '') NOT IN ('sold', 'soldout', 'rejected', 'archived') 
                THEN 1 ELSE 0 END) as pending_bikes,
            SUM(CASE WHEN (status IN ('approved', 'published') OR listing_status IN ('approved', 'published')) 
                          AND (isSoldout IS NULL OR isSoldout = 0) 
                          AND COALESCE(status, '') NOT IN ('sold', 'soldout', 'rejected', 'archived') 
                          AND COALESCE(listing_status, '') NOT IN ('sold', 'soldout', 'rejected', 'archived') 
                THEN 1 ELSE 0 END) as approved_bikes,
            SUM(CASE WHEN status = 'rejected' OR listing_status = 'rejected' 
                THEN 1 ELSE 0 END) as rejected_bikes,
            SUM(CASE WHEN isSoldout = 1 OR status IN ('sold', 'soldout') OR listing_status IN ('sold', 'soldout') 
                THEN 1 ELSE 0 END) as sold_bikes
        FROM bikes
        WHERE COALESCE(status, '') != 'archived' AND COALESCE(listing_status, '') != 'archived';
    """)
    bike_counts = cursor.fetchone()
    print("Accurate TiDB bike counts query result:", bike_counts)

    cursor.close()
    conn.close()
    print("Migration and query test completed successfully.")

if __name__ == "__main__":
    run_migration()
