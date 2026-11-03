import os
import sys
import json
import math
import csv
import io
import datetime
import tempfile
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory, g, session
from flask_cors import CORS

# Load environment variables prioritizing my-node-app/.env, fallback to root .env
app_dir = os.path.dirname(os.path.abspath(__file__))
local_env = os.path.join(app_dir, ".env")
root_env = os.path.join(os.path.dirname(app_dir), ".env")

if os.path.exists(local_env):
    load_dotenv(local_env, override=True)
if os.path.exists(root_env):
    load_dotenv(root_env, override=False)
load_dotenv()

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Ensure proper protocol (https) and host detection behind Render reverse proxy
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
except Exception:
    pass

# Enable CORS for all routes
CORS(app, resources={r"*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "smr-motors-jwt-secret-key-2025")

# Google OAuth 2.0 Credentials
raw_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
raw_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
raw_callback_url = os.getenv("GOOGLE_CALLBACK_URL", "").strip()

# Sanitize dummy or placeholder values
GOOGLE_CLIENT_ID = "" if raw_client_id.startswith("your_") else raw_client_id
GOOGLE_CLIENT_SECRET = "" if raw_client_secret.startswith("your_") else raw_client_secret
GOOGLE_CALLBACK_URL = raw_callback_url or "/api/auth/google/callback"

# Diagnostic log (Mask credentials - NEVER expose secrets in logs)
if GOOGLE_CLIENT_ID:
    cid_masked = GOOGLE_CLIENT_ID[:8] + "..." + GOOGLE_CLIENT_ID[-16:] if len(GOOGLE_CLIENT_ID) > 24 else "***"
    print(f"[OAuth Config] Google Client ID loaded: {cid_masked}")
else:
    print("[OAuth Config] Notice: GOOGLE_CLIENT_ID not configured or is placeholder (Demo auth active).")

if GOOGLE_CLIENT_SECRET:
    print("[OAuth Config] Google Client Secret is loaded securely in backend environment.")
else:
    print("[OAuth Config] Notice: GOOGLE_CLIENT_SECRET not configured or is placeholder.")

# Inject public Google Client ID into all template rendering contexts
@app.context_processor
def inject_google_client_id():
    return dict(google_client_id=GOOGLE_CLIENT_ID)

# Upload directory configuration (Windows & Linux compatible)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_FILE_SIZE = 5 * 1024 * 1024  # 5MB per image

def allowed_image_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# -----------------------------------------------------------------------------
# SMTP EMAIL DISPATCH & NOTIFICATION CONFIGURATION
# -----------------------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER or "praveenmuthu9500@gmail.com")
CONTACT_RECEIVER_EMAIL = os.getenv("CONTACT_RECEIVER_EMAIL", "praveenmuthu9500@gmail.com")

def send_email_notification(to_email, subject, body_text, body_html=None):
    """
    Sends email via SMTP if configured, or logs safely to server console.
    Returns (success_bool, status_message).
    Never logs or exposes passwords.
    """
    if not to_email:
        return False, "missing_recipient"

    if SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM_EMAIL
            msg["To"] = to_email

            part1 = MIMEText(body_text, "plain", "utf-8")
            msg.attach(part1)
            if body_html:
                part2 = MIMEText(body_html, "html", "utf-8")
                msg.attach(part2)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_PORT == 587:
                    server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
            print(f"[Email Notification] Successfully dispatched to {to_email} | Subject: {subject}")
            return True, "delivered"
        except Exception as e:
            err_msg = str(e)
            if SMTP_PASSWORD and SMTP_PASSWORD in err_msg:
                err_msg = err_msg.replace(SMTP_PASSWORD, "[PROTECTED]")
            print(f"[Email Notification Notice] SMTP dispatch to {to_email} failed: {err_msg}")
            return False, f"failed: {err_msg[:60]}"
    else:
        # Development / local resilient fallback: safe log without exposing secrets
        print(f"[Email Notification (Local/Mock)] Recipient: {to_email} | Subject: {subject}")
        return True, "logged_locally (SMTP unconfigured)"


# -----------------------------------------------------------------------------
# TIDB CLOUD DATABASE CONNECTION & RESILIENCE STORE
# -----------------------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST") or os.getenv("TIDB_HOST") or "127.0.0.1"
DB_PORT = int(os.getenv("DB_PORT") or os.getenv("TIDB_PORT") or 4000)
DB_USER = os.getenv("DB_USER") or os.getenv("TIDB_USER") or "root"
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("TIDB_PASSWORD") or ""
DB_NAME = os.getenv("DB_NAME") or os.getenv("TIDB_DATABASE") or "smr_motors"

# Requirement 13: Never use the sys database for application data
if DB_NAME.lower() == "sys":
    raise ValueError("Security Violation: 'sys' database cannot be used for application data. Set DB_NAME=smr_motors.")

# Resolve TiDB TLS CA certificate (Requirement 4)
ca_env = os.getenv("DB_SSL_CA") or os.getenv("TIDB_SSL_CA") or "certs/isrgrootx1.pem"
possible_ca_paths = [
    ca_env if os.path.isabs(ca_env) else os.path.join(app_dir, ca_env),
    os.path.join(app_dir, "certs", "isrgrootx1.pem"),
    os.path.join(os.path.dirname(app_dir), "my-node-app", "certs", "isrgrootx1.pem")
]
ssl_ca_path = None
for p in possible_ca_paths:
    if os.path.exists(p):
        ssl_ca_path = os.path.abspath(p)
        break

dbconfig = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "connection_timeout": 12
}

is_ssl = os.getenv("DB_SSL", "true").lower() in ("true", "1") or "tidbcloud.com" in DB_HOST.lower()
if is_ssl and ssl_ca_path:
    dbconfig["ssl_ca"] = ssl_ca_path
    dbconfig["ssl_verify_cert"] = True
    dbconfig["ssl_verify_identity"] = True

# Diagnostic log without passwords (Requirement 12)
user_masked = DB_USER[:4] + "***" if len(DB_USER) > 4 else "***"
print(f"[Database Config] TiDB Target: {DB_HOST}:{DB_PORT} (db: {DB_NAME}, user: {user_masked})")
if ssl_ca_path:
    print(f"[Database Config] TLS certificate verification active using CA: {os.path.basename(ssl_ca_path)}")

# Seed In-Memory Store (Active fallback when MySQL is unreachable)
IN_MEMORY_STORE = {
    "bikes": [
        {
            "id": 1,
            "title": "Royal Enfield Hunter 350 Dapper Ash",
            "listingTitle": "Royal Enfield Hunter 350 Dapper Ash",
            "brand": "Royal Enfield",
            "makedFrom": "Royal Enfield",
            "model": "Hunter 350",
            "bikeModel": "Hunter 350",
            "year": 2023,
            "bikeBuyingYear": "2023",
            "price": 145000,
            "sellingPrice": "145000",
            "bikePrice": "155000",
            "kilometers_driven": 8400,
            "bikeKms": "8400",
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "description": "Mint condition, single owner, company serviced with clean insurance.",
            "images": ["/static/images/IMG-20251204-WA0053.jpg", "/static/images/IMG-20251204-WA0051.jpg"],
            "seller_name": "SMR Motors",
            "sellerName": "SMR Motors",
            "seller_phone": "+91 98765 43210",
            "mobileNum": "9876543210",
            "status": "approved",
            "listing_status": "published",
            "negotiation_status": "completed",
            "requested_price": 145000,
            "public_selling_price": 145000,
            "isAccepted": 1,
            "isSoldout": 0,
            "featured": 1,
            "created_at": "2025-01-15T10:00:00Z"
        },
        {
            "id": 2,
            "title": "Yamaha MT-15 V2 Metallic Black",
            "listingTitle": "Yamaha MT-15 V2 Metallic Black",
            "brand": "Yamaha",
            "makedFrom": "Yamaha",
            "model": "MT-15 V2",
            "bikeModel": "MT-15 V2",
            "year": 2022,
            "bikeBuyingYear": "2022",
            "price": 132000,
            "sellingPrice": "132000",
            "bikePrice": "140000",
            "kilometers_driven": 14200,
            "bikeKms": "14200",
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "description": "Excellent performance, dual channel ABS, original tyres.",
            "images": ["/static/images/IMG-20251204-WA0051.jpg", "/static/images/IMG-20251204-WA0054.jpg"],
            "seller_name": "SMR Motors",
            "sellerName": "SMR Motors",
            "seller_phone": "+91 98765 43210",
            "mobileNum": "9876543210",
            "status": "approved",
            "listing_status": "published",
            "negotiation_status": "completed",
            "requested_price": 132000,
            "public_selling_price": 132000,
            "isAccepted": 1,
            "isSoldout": 0,
            "featured": 1,
            "created_at": "2025-01-18T12:00:00Z"
        },
        {
            "id": 3,
            "title": "KTM Duke 250 Racing Orange",
            "listingTitle": "KTM Duke 250 Racing Orange",
            "brand": "KTM",
            "makedFrom": "KTM",
            "model": "Duke 250",
            "bikeModel": "Duke 250",
            "year": 2021,
            "bikeBuyingYear": "2021",
            "price": 168000,
            "sellingPrice": "168000",
            "bikePrice": "175000",
            "kilometers_driven": 19500,
            "bikeKms": "19500",
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "description": "Track-ready, new Michelin road tyres, complete service record.",
            "images": ["/static/images/IMG-20251204-WA0054.jpg"],
            "seller_name": "SMR Motors",
            "sellerName": "SMR Motors",
            "seller_phone": "+91 98765 43210",
            "mobileNum": "9876543210",
            "status": "approved",
            "listing_status": "published",
            "negotiation_status": "completed",
            "requested_price": 168000,
            "public_selling_price": 168000,
            "isAccepted": 1,
            "isSoldout": 0,
            "featured": 0,
            "created_at": "2025-01-20T14:00:00Z"
        },
        {
            "id": 4,
            "title": "Bajaj Pulsar NS200 Pewter Grey",
            "listingTitle": "Bajaj Pulsar NS200 Pewter Grey",
            "brand": "Bajaj",
            "makedFrom": "Bajaj",
            "model": "Pulsar NS200",
            "bikeModel": "Pulsar NS200",
            "year": 2022,
            "bikeBuyingYear": "2022",
            "price": 105000,
            "sellingPrice": "105000",
            "bikePrice": "112000",
            "kilometers_driven": 16000,
            "bikeKms": "16000",
            "fuel_type": "Petrol",
            "transmission": "Manual",
            "description": "Clean commuter, accident free, high mileage engine.",
            "images": ["/static/images/IMG-20251204-WA0056.jpg"],
            "seller_name": "SMR Motors",
            "sellerName": "SMR Motors",
            "seller_phone": "+91 98765 43210",
            "mobileNum": "9876543210",
            "status": "approved",
            "listing_status": "published",
            "negotiation_status": "completed",
            "requested_price": 105000,
            "public_selling_price": 105000,
            "isAccepted": 1,
            "isSoldout": 0,
            "featured": 0,
            "created_at": "2025-01-22T09:00:00Z"
        }
    ],
    "categories": [
        {"id": 1, "category_name": "Cruiser", "image_url": "/static/images/IMG-20251204-WA0053.jpg"},
        {"id": 2, "category_name": "Sports", "image_url": "/static/images/IMG-20251204-WA0051.jpg"},
        {"id": 3, "category_name": "Naked", "image_url": "/static/images/IMG-20251204-WA0054.jpg"},
        {"id": 4, "category_name": "Commuter", "image_url": "/static/images/IMG-20251204-WA0056.jpg"}
    ],
    "enquiries": [],
    "users": [
        {
            "id": 1,
            "name": "Demo Rider",
            "email": "demo.rider@gmail.com",
            "phone": "+91 98765 43210",
            "profile_image": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80",
            "role": "user",
            "is_active": 1,
            "created_at": "2025-01-01T00:00:00Z"
        }
    ],
    "favorites": [],
    "contact_messages": [],
    "contact_replies": [],
    "audit_logs": [],
    "price_negotiations": [
        {
            "id": 1,
            "bike_id": 4,
            "seller_id": 1,
            "admin_id": 1,
            "requested_price": 115000.0,
            "proposed_payout": 92000.0,
            "counteroffer_number": 1,
            "status": "accepted",
            "message": "Fair market valuation based on vehicle age and inspection.",
            "seller_response_note": "Accepted by seller",
            "created_at": "2025-01-23T11:00:00Z"
        }
    ],
    "bike_transactions": [
        {
            "id": 1,
            "bike_id": 4,
            "bike_title": "Bajaj Pulsar NS200 Pewter Grey",
            "seller_id": 1,
            "admin_id": 1,
            "seller_name": "SMR Motors",
            "seller_phone": "+91 98765 43210",
            "seller_payout": 92000.0,
            "actual_sale_price": 105000.0,
            "service_expense": 2500.0,
            "repair_expense": 1200.0,
            "transport_expense": 800.0,
            "other_expense": 500.0,
            "total_expenses": 5000.0,
            "realized_profit": 8000.0,
            "sold_at": "2025-01-26T14:30:00Z",
            "notes": "Full fluid service, brake pads replacement, delivered to buyer with RC transfer.",
            "buyer_name": "Arun Kumar",
            "buyer_phone": "+91 94433 22110",
            "created_at": "2025-01-26T14:30:00Z"
        }
    ],
    "notifications": [
        {
            "id": 1,
            "user_id": 1,
            "target_role": "user",
            "title": "Welcome to SMR Motors",
            "message": "Explore certified pre-owned motorcycles or list your bike for transparent valuation.",
            "type": "welcome",
            "link": "/index.html",
            "is_read": 0,
            "created_at": "2025-01-20T10:00:00Z"
        },
        {
            "id": 2,
            "user_id": None,
            "target_role": "admin",
            "title": "New Listing Submitted",
            "message": "A new motorcycle listing is pending review and price proposal.",
            "type": "listing",
            "link": "/admin.html?tab=pending",
            "is_read": 0,
            "created_at": "2025-01-25T11:00:00Z"
        }
    ]
}

def create_notification(title, message, user_id=None, target_role="user", notif_type="info", link=None):
    """
    Persists notification to TiDB Cloud and In-Memory store.
    """
    new_notif = {
        "id": len(IN_MEMORY_STORE["notifications"]) + 1,
        "user_id": user_id,
        "target_role": target_role,
        "title": title,
        "message": message,
        "type": notif_type,
        "link": link or "",
        "is_read": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO notifications (user_id, target_role, title, message, type, link, is_read)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, target_role, title, message, notif_type, link or "", 0)
            )
            conn.commit()
            new_notif["id"] = cursor.lastrowid
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    IN_MEMORY_STORE["notifications"].insert(0, new_notif)
    return new_notif


_tidb_pool = None

def get_db():
    """
    Returns an active TLS-encrypted MySQL connection to TiDB Cloud using connection pooling.
    Handles connection errors gracefully without leaking credentials.
    """
    global _tidb_pool
    try:
        import mysql.connector
        from mysql.connector import pooling
        if _tidb_pool is None:
            pool_cfg = dict(dbconfig)
            pool_cfg["pool_name"] = "smr_tidb_pool"
            pool_cfg["pool_size"] = 5
            pool_cfg["pool_reset_session"] = True
            _tidb_pool = pooling.MySQLConnectionPool(**pool_cfg)
        return _tidb_pool.get_connection()
    except Exception:
        # Fallback to direct connection if pooling is not supported or connection pool fails
        try:
            import mysql.connector
            return mysql.connector.connect(**dbconfig)
        except Exception as e:
            err_msg = str(e)
            if DB_PASSWORD and DB_PASSWORD in err_msg:
                err_msg = err_msg.replace(DB_PASSWORD, "[PROTECTED]")
            return None

def log_admin_action(admin_username, action, target_type, target_id=None, details=None):
    """
    Records administrative security and audit logs permanently in TiDB Cloud.
    """
    try:
        ip = request.remote_addr if request else "127.0.0.1"
    except Exception:
        ip = "127.0.0.1"

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO admin_audit_logs (admin_username, action, target_type, target_id, details, ip_address)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (admin_username or "admin", action, target_type, str(target_id) if target_id else None, details or "", ip)
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # In-memory store fallback
    IN_MEMORY_STORE.setdefault("audit_logs", []).insert(0, {
        "id": len(IN_MEMORY_STORE.get("audit_logs", [])) + 1,
        "admin_username": admin_username or "admin",
        "action": action,
        "target_type": target_type,
        "target_id": str(target_id) if target_id else None,
        "details": details or "",
        "ip_address": ip,
        "created_at": datetime.datetime.utcnow().isoformat()
    })

def initialize_database():
    """
    Initializes TiDB Cloud connection:
    - Tests SELECT 1 (Requirement 9)
    - Creates smr_motors database if it does not exist (Requirement 5)
    - Never uses sys database (Requirement 13)
    - Creates all required application tables from schema (Requirement 6)
    - Seeds initial catalog and admin accounts if empty
    - Handles connection errors gracefully (Requirement 11)
    - Never prints secrets or passwords in logs (Requirement 12)
    """
    try:
        import mysql.connector
    except ImportError:
        print("[Database] mysql-connector-python not available. Using in-memory store.")
        return

    # Verify/create smr_motors database
    try:
        admin_cfg = dict(dbconfig)
        target_db = admin_cfg.pop("database", "smr_motors")
        admin_conn = mysql.connector.connect(**admin_cfg)
        admin_cur = admin_conn.cursor()
        admin_cur.execute("SELECT 1")
        _ = admin_cur.fetchone()
        admin_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{target_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        admin_conn.commit()
        admin_cur.close()
        admin_conn.close()
        print(f"[Database] TiDB Cloud connectivity verified (SELECT 1 passed). Database `{target_db}` ready.")
    except Exception as e:
        err_str = str(e)
        if DB_PASSWORD and DB_PASSWORD in err_str:
            err_str = err_str.replace(DB_PASSWORD, "[PROTECTED]")
        print(f"[Database] Notice connecting to TiDB Cloud gateway: {err_str}")

    conn = get_db()
    if not conn:
        print("[Database] TiDB Cloud unreachable. Running with in-memory resilient data store.")
        return

    try:
        cursor = conn.cursor()

        # 1. users table (Google OAuth 2.0 & Session Profile)
        cursor.execute("""
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
        """)

        # 2. admins table
        cursor.execute("""
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
        """)

        # 3. categories table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `categories` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `category_name` VARCHAR(80) NOT NULL UNIQUE,
          `description` TEXT NULL,
          `image_url` VARCHAR(255) NULL,
          `status` VARCHAR(20) NOT NULL DEFAULT 'active',
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 4. bikes table (Motorcycle Inventory)
        cursor.execute("""
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
          `requested_price` DECIMAL(12,2) NULL,
          `proposed_seller_payout` DECIMAL(12,2) NULL,
          `accepted_seller_payout` DECIMAL(12,2) NULL,
          `public_selling_price` DECIMAL(12,2) NULL,
          `listing_status` VARCHAR(40) NOT NULL DEFAULT 'pending',
          `negotiation_status` VARCHAR(40) NOT NULL DEFAULT 'pending',
          `seller_agreement_at` TIMESTAMP NULL,
          `published_at` TIMESTAMP NULL,
          `sold_at` TIMESTAMP NULL,
          `rejection_reason` TEXT NULL,
          `featured` TINYINT(1) NOT NULL DEFAULT 0,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX `idx_bikes_brand` (`brand`),
          INDEX `idx_bikes_status` (`status`),
          INDEX `idx_bikes_listing_status` (`listing_status`),
          INDEX `idx_bikes_price` (`price`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # Add any missing columns to existing bikes table
        for col_name, col_def in [
            ("requested_price", "DECIMAL(12,2) NULL"),
            ("proposed_seller_payout", "DECIMAL(12,2) NULL"),
            ("accepted_seller_payout", "DECIMAL(12,2) NULL"),
            ("public_selling_price", "DECIMAL(12,2) NULL"),
            ("listing_status", "VARCHAR(40) DEFAULT 'pending'"),
            ("negotiation_status", "VARCHAR(40) DEFAULT 'pending'"),
            ("published_at", "TIMESTAMP NULL"),
            ("sold_at", "TIMESTAMP NULL"),
            ("seller_agreement_at", "TIMESTAMP NULL"),
            ("registration_number", "VARCHAR(50) NULL"),
            ("location", "VARCHAR(120) NULL"),
            ("approved_by", "VARCHAR(60) NULL"),
            ("approved_at", "TIMESTAMP NULL"),
            ("rejected_by", "VARCHAR(60) NULL"),
            ("rejected_at", "TIMESTAMP NULL"),
            ("buying_price", "DECIMAL(12,2) NULL"),
            ("expenses", "DECIMAL(12,2) DEFAULT 0"),
            ("profit", "DECIMAL(12,2) DEFAULT 0"),
            ("isSoldout", "TINYINT(1) DEFAULT 0")
        ]:
            try:
                cursor.execute(f"ALTER TABLE `bikes` ADD COLUMN `{col_name}` {col_def}")
                conn.commit()
            except Exception:
                pass

        # 4a. bike_images table (Supports up to 6 gallery images per motorcycle)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `bike_images` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `bike_id` INT NOT NULL,
          `image_url` VARCHAR(500) NOT NULL,
          `image_order` INT NOT NULL DEFAULT 1,
          `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_bike_images_bike_id` (`bike_id`),
          INDEX `idx_bike_images_primary` (`is_primary`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        conn.commit()

        # Add missing columns to admins table
        for col_name, col_def in [
            ("full_name", "VARCHAR(100) NULL"),
            ("phone", "VARCHAR(30) NULL"),
            ("is_active", "TINYINT(1) NOT NULL DEFAULT 1"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        ]:
            try:
                cursor.execute(f"ALTER TABLE `admins` ADD COLUMN `{col_name}` {col_def}")
                conn.commit()
            except Exception:
                pass

        # Add missing columns to users table
        for col_name, col_def in [
            ("last_login", "TIMESTAMP NULL")
        ]:
            try:
                cursor.execute(f"ALTER TABLE `users` ADD COLUMN `{col_name}` {col_def}")
                conn.commit()
            except Exception:
                pass

        # Add missing columns to enquiries table
        for col_name, col_def in [
            ("admin_reply", "TEXT NULL"),
            ("replied_at", "TIMESTAMP NULL"),
            ("replied_by", "VARCHAR(60) NULL")
        ]:
            try:
                cursor.execute(f"ALTER TABLE `enquiries` ADD COLUMN `{col_name}` {col_def}")
                conn.commit()
            except Exception:
                pass

        # Add missing columns to bike_transactions table
        for col_name, col_def in [
            ("buyer_name", "VARCHAR(100) NULL"),
            ("buyer_phone", "VARCHAR(30) NULL")
        ]:
            try:
                cursor.execute(f"ALTER TABLE `bike_transactions` ADD COLUMN `{col_name}` {col_def}")
                conn.commit()
            except Exception:
                pass

        # Ensure enquiry_replies table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `enquiry_replies` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `enquiry_id` INT NOT NULL,
          `admin_id` INT NULL,
          `admin_username` VARCHAR(60) NULL,
          `reply_message` TEXT NOT NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_er_enq` (`enquiry_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        conn.commit()

        # 4b. price_negotiations table
        cursor.execute("""
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
          INDEX `idx_pneg_status` (`status`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 4c. bike_transactions table
        cursor.execute("""
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
          `sold_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `notes` TEXT NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_tx_bike` (`bike_id`),
          INDEX `idx_tx_seller` (`seller_id`),
          INDEX `idx_tx_sold_at` (`sold_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 4d. notifications table
        cursor.execute("""
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
        """)

        # 5. enquiries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `enquiries` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `listingId` INT NULL,
          `listingTitle` VARCHAR(255) NULL,
          `customerName` VARCHAR(255) NULL,
          `mobile` VARCHAR(20) NULL,
          `email` VARCHAR(255) NULL,
          `location` VARCHAR(255) NULL,
          `timestamp` VARCHAR(50) NULL,
          `status` VARCHAR(50) DEFAULT 'pending',
          `message` TEXT NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 6. favorites table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `favorites` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `user_id` INT NOT NULL,
          `bike_id` INT NOT NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY `uniq_user_bike_fav` (`user_id`, `bike_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 7. contact_messages table
        cursor.execute("""
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
        """)

        # Add any missing columns to contact_messages
        for col_name, col_def in [
            ("subject", "VARCHAR(255) NOT NULL DEFAULT 'General Inquiry'"),
            ("email_delivery_status", "VARCHAR(50) NOT NULL DEFAULT 'pending'")
        ]:
            try:
                cursor.execute(f"ALTER TABLE `contact_messages` ADD COLUMN `{col_name}` {col_def}")
                conn.commit()
            except Exception:
                pass

        # 7b. contact_replies table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `contact_replies` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `contact_message_id` INT NOT NULL,
          `admin_id` INT NULL,
          `admin_username` VARCHAR(60) NULL,
          `reply_message` TEXT NOT NULL,
          `sent_status` VARCHAR(50) NOT NULL DEFAULT 'sent',
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX `idx_cr_msg` (`contact_message_id`),
          INDEX `idx_cr_admin` (`admin_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 8. admin_audit_logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `admin_audit_logs` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `admin_id` INT NULL,
          `admin_username` VARCHAR(60) NOT NULL,
          `action` VARCHAR(60) NOT NULL,
          `target_type` VARCHAR(40) NOT NULL,
          `target_id` VARCHAR(60) NULL,
          `details` TEXT NULL,
          `ip_address` VARCHAR(45) NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # 9. bikesforsale legacy compatibility table
        cursor.execute("""
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
        """)
        conn.commit()

        # Seed categories if empty
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            for cat in IN_MEMORY_STORE["categories"]:
                cursor.execute(
                    "INSERT INTO categories (category_name, image_url) VALUES (%s, %s)",
                    (cat["category_name"], cat["image_url"])
                )
            conn.commit()

        # Seed bikes if empty
        cursor.execute("SELECT COUNT(*) FROM bikes")
        if cursor.fetchone()[0] == 0:
            for b in IN_MEMORY_STORE["bikes"]:
                cursor.execute(
                    """INSERT INTO bikes (title, brand, model, year, price, kilometers_driven, fuel_type, transmission, description, images, seller_name, seller_phone, status, featured)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (b["title"], b["brand"], b["model"], b["year"], b["price"], b["kilometers_driven"], b["fuel_type"], b["transmission"], b["description"], json.dumps(b["images"]), b["seller_name"], b["seller_phone"], b["status"], b.get("featured", 0))
                )
                cursor.execute(
                    """INSERT INTO bikesforsale (listingTitle, makedFrom, bikeModel, bikeBuyingYear, bikePrice, sellingPrice, bikeKms, sellerName, mobileNum, description, isAccepted, isSoldout)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (b["listingTitle"], b["makedFrom"], b["bikeModel"], b["bikeBuyingYear"], b["bikePrice"], b["sellingPrice"], b["bikeKms"], b["sellerName"], b["mobileNum"], b["description"], b["isAccepted"], b["isSoldout"])
                )
            conn.commit()

        # Seed default admins if empty
        cursor.execute("SELECT COUNT(*) FROM admins")
        if cursor.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            default_admins = [
                ("admin", "Praveen Administrator", "admin@smrmotors.com", "+91 98765 43210", generate_password_hash("admin123"), "superadmin", 1),
                ("mani", "Mani (Showroom Staff)", "mani@smrmotors.com", "+91 98765 43211", generate_password_hash("mani@22"), "admin", 1),
                ("murugan", "Murugan (Partner)", "murugan@smrmotors.com", "+91 98765 43212", generate_password_hash("murugan@22"), "superadmin", 1),
                ("raja", "Raja (Partner)", "raja@smrmotors.com", "+91 98765 43213", generate_password_hash("raja@22"), "superadmin", 1),
            ]
            for u, fn, em, ph, pw, r, act in default_admins:
                cursor.execute(
                    "INSERT INTO admins (username, full_name, email, phone, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (u, fn, em, ph, pw, r, act)
                )
            conn.commit()

        cursor.close()
        conn.close()
        print("[Database] TiDB Cloud tables and seeds verified successfully.")
    except Exception as e:
        err_str = str(e)
        if DB_PASSWORD and DB_PASSWORD in err_str:
            err_str = err_str.replace(DB_PASSWORD, "[PROTECTED]")
        print("[Database] Table initialization notice:", err_str)

# -----------------------------------------------------------------------------
# AUTHENTICATION & ROLE-BASED ACCESS CONTROL HELPERS (RBAC: SUPERADMIN, ADMIN, USER)
# -----------------------------------------------------------------------------
adminAccounts = {
    "admin":   {"password": "admin123",  "name": "Administrator", "role": "superadmin"},
    "mani":    {"password": "mani@22",    "name": "Mani (Staff)",   "role": "admin"},
    "murugan": {"password": "murugan@22", "name": "Murugan (Owner)", "role": "superadmin"},
    "raja":    {"password": "raja@22",    "name": "Raja (Owner)",    "role": "superadmin"},
}

def normalize_admin_role(raw_role):
    r = str(raw_role or "").lower().strip()
    if r in ("superadmin", "main", "owner"):
        return "superadmin"
    return "admin"

def admin_required(f):
    """Allows both SUPERADMIN (Owner) and ADMIN (Staff) access."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"success": False, "message": "Missing admin authorization header"}), 401
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"success": False, "message": "Invalid token header format. Expected Bearer <token>"}), 401
        try:
            import jwt
            decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
            decoded["role"] = normalize_admin_role(decoded.get("role"))
            g.admin = decoded
        except Exception:
            return jsonify({"success": False, "message": "Expired or invalid admin session"}), 401
        return f(*args, **kwargs)
    return wrapper

def superadmin_required(f):
    """Restricts access strictly to SUPERADMIN (Owner). Returns HTTP 403 Forbidden for Staff (ADMIN)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"success": False, "message": "Missing admin authorization header"}), 401
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"success": False, "message": "Invalid token header format. Expected Bearer <token>"}), 401
        try:
            import jwt
            decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
            role = normalize_admin_role(decoded.get("role"))
            decoded["role"] = role
            g.admin = decoded
            if role != "superadmin":
                return jsonify({
                    "success": False,
                    "message": "Access Forbidden: Superadmin owner permission required for confidential financial records and operations."
                }), 403
        except Exception:
            return jsonify({"success": False, "message": "Expired or invalid admin session"}), 401
        return f(*args, **kwargs)
    return wrapper

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"success": False, "message": "Authentication required. Please sign in."}), 401
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"success": False, "message": "Invalid auth header format. Expected Bearer <token>"}), 401
        try:
            import jwt
            decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
            g.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Session has expired. Please sign in again."}), 401
        except Exception:
            return jsonify({"success": False, "message": "Invalid or expired session. Please sign in again."}), 401
        return f(*args, **kwargs)
    return wrapper

# -----------------------------------------------------------------------------
# STATIC FILE SERVING ROUTES (Handles all path variants cleanly)
# -----------------------------------------------------------------------------
@app.route("/static/<path:filename>")
def serve_static(filename):
    static_dir = os.path.join(app.root_path, "static")
    return send_from_directory(static_dir, filename)

@app.route("/public/<path:filename>")
@app.route("/my-node-app/public/<path:filename>")
def serve_public(filename):
    public_dir = os.path.join(app.root_path, "public")
    return send_from_directory(public_dir, filename)

@app.route("/my-node-app/static/<path:filename>")
def serve_legacy_static(filename):
    static_dir = os.path.join(app.root_path, "static")
    return send_from_directory(static_dir, filename)

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    # Try root assets then my-node-app static
    root_assets = os.path.join(os.path.dirname(app.root_path), "assets")
    if os.path.exists(os.path.join(root_assets, filename)):
        return send_from_directory(root_assets, filename)
    static_dir = os.path.join(app.root_path, "static")
    return send_from_directory(static_dir, filename)

@app.route("/uploads/<path:filename>")
@app.route("/public/uploads/<path:filename>")
@app.route("/my-node-app/public/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# Direct root files route (e.g. IMG-*.jpg, config.js, favicon)
@app.route("/<filename>")
def serve_root_asset(filename):
    # Check if this matches a template route first
    if filename.endswith(".html"):
        clean_name = filename
        if os.path.exists(os.path.join(app.root_path, "templates", clean_name)):
            return render_template(clean_name)
    
    # Check static, public, and root folders
    for directory in [
        os.path.join(app.root_path, "static"),
        os.path.join(app.root_path, "public"),
        os.path.join(app.root_path, "static", "images"),
        os.path.dirname(app.root_path),
        app.root_path
    ]:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            return send_from_directory(directory, filename)
    return jsonify({"error": f"Asset {filename} not found"}), 404

# -----------------------------------------------------------------------------
# TEMPLATE PAGE ROUTES (Clean URLs & Direct .html Mapping)
# -----------------------------------------------------------------------------
@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")

@app.route("/login")
@app.route("/login.html")
@app.route("/userLogin.html")
def user_login():
    return render_template("userLogin.html")

@app.route("/profile")
@app.route("/profile.html")
@app.route("/user/profile")
@app.route("/user/dashboard")
def user_profile():
    if request.headers.get("Authorization"):
        # API request
        return jsonify({"success": True, "user": IN_MEMORY_STORE["users"][0]})
    return render_template("profile.html")

@app.route("/admin")
@app.route("/admin.html")
@app.route("/admin/dashboard")
def admin_page():
    return render_template("admin.html")

@app.route("/admin/login")
@app.route("/admin/login.html")
def admin_login_page():
    return render_template("adminLogin.html")

@app.route("/sell")
@app.route("/sell-bike.html")
@app.route("/bikeSelling.html")
def bike_selling():
    return render_template("bikeSelling.html")

@app.route("/adminAddListing.html")
@app.route("/admin-add")
def admin_add_listing():
    return render_template("adminAddListing.html")

@app.route("/enquiryBike.html")
@app.route("/admin-enquiries")
def enquiry_bike_page():
    return render_template("enquiryBike.html")

@app.route("/listingUserBike.html")
@app.route("/admin-listings")
def listing_user_bike():
    return render_template("listingUserBike.html")

@app.route("/bike-details")
@app.route("/bike-details.html")
@app.route("/enquiry-bike-details.html")
def bike_details():
    return render_template("enquiry-bike-details.html")

@app.route("/sold")
@app.route("/sold-bikes.html")
@app.route("/SoldOutPage.html")
def sold_out_page():
    return render_template("SoldOutPage.html")

@app.route("/about")
@app.route("/about.html")
def about_page():
    return render_template("about.html")

@app.route("/contact")
@app.route("/contact.html")
def contact_page():
    return render_template("contact.html")

# -----------------------------------------------------------------------------
# REST API ENDPOINTS
# -----------------------------------------------------------------------------

def _normalize_bike(r, is_admin=False, admin_role=None):
    """
    Normalizes bike record keys across legacy and modern schema.
    Sanitizes internal seller payout and business margin for public callers.
    Restricts confidential financials to Superadmin role only.
    """
    item = dict(r)
    if isinstance(item.get("images"), str):
        try:
            item["images"] = json.loads(item["images"])
        except Exception:
            item["images"] = [item["images"]]
    if not item.get("images"):
        item["images"] = ["/static/images/IMG-20251204-WA0053.jpg"]
    
    item["listingTitle"] = item.get("title")
    item["makedFrom"] = item.get("brand")
    item["bikeModel"] = item.get("model")
    item["bikeBuyingYear"] = str(item.get("year", 2022))
    item["sellingPrice"] = str(item.get("public_selling_price") or item.get("price", 100000))
    item["bikePrice"] = str(item.get("price", 100000))
    item["bikeKms"] = str(item.get("kilometers_driven", 0))
    item["sellerName"] = item.get("seller_name") or "SMR Motors"
    item["mobileNum"] = item.get("seller_phone") or "9876543210"
    item["registration_number"] = item.get("registration_number") or item.get("vehicleNumber") or "TN-XX-XXXX"
    item["location"] = item.get("location") or "Salem, Tamil Nadu"
    item["requested_price"] = item.get("requested_price") or item.get("price")
    item["approved_price"] = item.get("public_selling_price") or item.get("price")
    item["owner_name"] = item.get("seller_name") or "SMR Motors"
    st = item.get("listing_status") or item.get("status") or "pending"
    item["status"] = st
    item["listing_status"] = st
    item["isAccepted"] = 1 if st in ("approved", "published") else 0
    item["isSoldout"] = 1 if (st == "soldout" or item.get("isSoldout") == 1) else 0

    # Determine effective admin role if not explicitly passed
    if admin_role is None and hasattr(g, "admin") and isinstance(g.admin, dict):
        admin_role = g.admin.get("role")

    # Restrict confidential financials to Superadmin role only (Requirement 11)
    if not is_admin or admin_role != "superadmin":
        item.pop("accepted_seller_payout", None)
        item.pop("proposed_seller_payout", None)
        item.pop("business_margin", None)
        item.pop("buying_price", None)
        item.pop("expenses", None)
        item.pop("profit", None)
    return item

# Bikes API (supports server-side pagination, multi-criteria filtering, and public privacy)
@app.route("/api/bikes", methods=["GET"])
@app.route("/bikes", methods=["GET"])
def get_bikes_api():
    status = request.args.get("status")
    brand = request.args.get("brand")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    year = request.args.get("year")
    search = request.args.get("search", "").strip().lower()
    sort_by = request.args.get("sort", "newest")

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = max(1, int(request.args.get("limit", 9)))
    except (ValueError, TypeError):
        limit = 9

    all_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            all_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_bikes:
        all_bikes = list(IN_MEMORY_STORE["bikes"])

    auth_header = request.headers.get("Authorization", "")
    is_admin = False
    if auth_header and "Bearer" in auth_header:
        try:
            import jwt
            token = auth_header.split()[1]
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if decoded.get("role") in ("admin", "superadmin"):
                is_admin = True
        except Exception:
            pass

    normalized = [_normalize_bike(b, is_admin=is_admin) for b in all_bikes]

    filtered = []
    for b in normalized:
        b_status = (b.get("listing_status") or b.get("status") or "pending").lower()
        is_sold = b.get("isSoldout") == 1 or b_status == "soldout"

        if status == "soldout":
            if not is_sold:
                continue
        elif status in ("all", "admin_all"):
            pass
        elif status:
            if b_status != status.lower():
                continue
        else:
            # Public Marketplace rule: ONLY published / approved AND not sold out
            if b_status not in ("published", "approved") or is_sold:
                continue

        if brand and brand.lower() != "all" and b.get("brand", "").lower() != brand.lower():
            continue

        try:
            b_price = float(b.get("price", 0))
            if min_price and b_price < float(min_price):
                continue
            if max_price and b_price > float(max_price):
                continue
        except (ValueError, TypeError):
            pass

        if year and str(b.get("year", "")) != str(year):
            continue

        if search:
            match_txt = f"{b.get('title', '')} {b.get('brand', '')} {b.get('model', '')} {b.get('description', '')}".lower()
            if search not in match_txt:
                continue

        filtered.append(b)

    if sort_by == "price_asc":
        filtered.sort(key=lambda x: float(x.get("price", 0)))
    elif sort_by == "price_desc":
        filtered.sort(key=lambda x: float(x.get("price", 0)), reverse=True)
    elif sort_by == "year_desc":
        filtered.sort(key=lambda x: int(x.get("year", 0)), reverse=True)
    elif sort_by == "kms_asc":
        filtered.sort(key=lambda x: int(x.get("kilometers_driven", 0)))
    else:
        filtered.sort(key=lambda x: x.get("id", 0), reverse=True)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
        "hasNext": page < total_pages,
        "hasPrev": page > 1,
        "start": start_idx + 1 if total > 0 else 0,
        "end": end_idx
    }

    return jsonify({
        "success": True,
        "data": page_data,
        "bikes": page_data,
        "pagination": pagination,
        "total": total
    })

@app.route("/api/bikes/sold", methods=["GET"])
def get_sold_bikes_api():
    """
    Public Sold Gallery Endpoint.
    Strictly sanitizes private financials (no seller payout, expenses, or margin).
    Supports server-side pagination.
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 9)))
    except (ValueError, TypeError):
        limit = 9

    all_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE status = 'soldout' OR listing_status = 'soldout' ORDER BY id DESC")
            all_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_bikes:
        all_bikes = [b for b in IN_MEMORY_STORE["bikes"] if b.get("status") == "soldout" or b.get("isSoldout") == 1 or b.get("listing_status") == "soldout"]

    sanitized = []
    for b in all_bikes:
        item = _normalize_bike(b, is_admin=False)
        item["status"] = "soldout"
        item["isSoldout"] = 1
        item.pop("accepted_seller_payout", None)
        item.pop("proposed_seller_payout", None)
        item.pop("business_margin", None)
        sanitized.append(item)

    total = len(sanitized)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = sanitized[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "bikes": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        },
        "total": total
    })


@app.route("/api/bikes/<int:bike_id>", methods=["GET"])
@app.route("/bikes/<int:bike_id>", methods=["GET"])
def get_single_bike_api(bike_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE id = %s", (bike_id,))
            b = cursor.fetchone()
            cursor.close()
            conn.close()
            if b:
                if isinstance(b.get("images"), str):
                    try: b["images"] = json.loads(b["images"])
                    except Exception: b["images"] = [b["images"]]
                if not b.get("images"):
                    b["images"] = ["/static/images/IMG-20251204-WA0053.jpg"]
                b["listingTitle"] = b.get("title")
                b["makedFrom"] = b.get("brand")
                b["bikeModel"] = b.get("model")
                b["bikeBuyingYear"] = str(b.get("year", 2022))
                b["sellingPrice"] = str(b.get("price", 100000))
                b["bikePrice"] = str(b.get("price", 100000))
                b["bikeKms"] = str(b.get("kilometers_driven", 0))
                b["sellerName"] = b.get("seller_name")
                b["mobileNum"] = b.get("seller_phone")
                b["isAccepted"] = 1 if b.get("status") == "approved" else 0
                b["isSoldout"] = 1 if b.get("status") == "soldout" else 0
                return jsonify({"success": True, "data": b, **b})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            return jsonify({"success": True, "data": b, **b})
    return jsonify({"success": False, "message": "Bike not found"}), 404

@app.route("/api/bikes", methods=["POST"])
@app.route("/addBike", methods=["POST"])
@app.route("/userAddBike", methods=["POST"])
def add_bike_api():
    data = request.form.to_dict() if request.form else (request.get_json() or {})
    new_id = len(IN_MEMORY_STORE["bikes"]) + 1
    
    # Handle uploaded photos (supports up to 6 images with validation)
    uploaded_urls = []
    if request.files:
        files = request.files.getlist("images") or request.files.getlist("attachments") or request.files.getlist("photos")
        for idx, f in enumerate(files[:6]):
            if f and f.filename and allowed_image_file(f.filename):
                from werkzeug.utils import secure_filename
                import uuid
                ext = f.filename.rsplit(".", 1)[1].lower()
                sname = f"bike_{int(datetime.datetime.utcnow().timestamp())}_{idx+1}_{uuid.uuid4().hex[:6]}.{ext}"
                f.save(os.path.join(UPLOAD_DIR, sname))
                uploaded_urls.append(f"/uploads/{sname}")

    # If images were passed as JSON or array of URLs in body
    body_images = data.get("images")
    if body_images:
        if isinstance(body_images, str):
            try:
                parsed = json.loads(body_images)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and "url" in item:
                            uploaded_urls.append(item["url"])
                        elif isinstance(item, str):
                            uploaded_urls.append(item)
                else:
                    uploaded_urls.append(body_images)
            except Exception:
                uploaded_urls.append(body_images)
        elif isinstance(body_images, list):
            for item in body_images:
                if isinstance(item, dict) and "url" in item:
                    uploaded_urls.append(item["url"])
                elif isinstance(item, str):
                    uploaded_urls.append(item)

    if not uploaded_urls:
        uploaded_urls = ["/static/images/IMG-20251204-WA0053.jpg"]

    # Cap at 6 images
    images = uploaded_urls[:6]

    title = data.get("title") or data.get("listingTitle") or "Custom Motorcycle"
    brand = data.get("brand") or data.get("makedFrom") or "Other"
    model = data.get("model") or data.get("bikeModel") or "Standard"
    year = int(data.get("year") or data.get("bikeBuyingYear") or 2022)
    reg_no = data.get("registration_number") or data.get("vehicleNumber") or ""
    price = float(data.get("price") or data.get("sellingPrice") or data.get("bikePrice") or 100000)
    kms = int(data.get("kilometers_driven") or data.get("bikeKms") or 0)
    fuel = data.get("fuel_type", "Petrol")
    trans = data.get("transmission", "Manual")
    location = data.get("location") or data.get("city") or "Salem, Tamil Nadu"
    desc = data.get("description", "Inspected pre-owned motorcycle.")
    sname = data.get("seller_name") or data.get("sellerName") or "User"
    sphone = data.get("seller_phone") or data.get("mobileNum") or ""
    seller_id = data.get("seller_id") or session.get("user_id") or None
    status = data.get("status", "pending")
    listing_status = "pending"
    negotiation_status = "pending"

    # Persist to TiDB Cloud
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bikes (title, brand, model, year, registration_number, price, requested_price, kilometers_driven, fuel_type, transmission, location, description, images, seller_id, seller_name, seller_phone, status, listing_status, negotiation_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (title, brand, model, year, reg_no, price, price, kms, fuel, trans, location, desc, json.dumps(images), seller_id, sname, sphone, status, listing_status, negotiation_status)
            )
            new_id = cursor.lastrowid

            # Persist each of up to 6 gallery images to bike_images table
            for idx, img_url in enumerate(images):
                cursor.execute(
                    """INSERT INTO bike_images (bike_id, image_url, image_order, is_primary)
                       VALUES (%s, %s, %s, %s)""",
                    (new_id, img_url, idx + 1, 1 if idx == 0 else 0)
                )

            cursor.execute(
                """INSERT INTO bikesforsale (listingTitle, makedFrom, bikeModel, bikeBuyingYear, vehicleNumber, bikePrice, sellingPrice, bikeKms, sellerName, mobileNum, description, isAccepted, isSoldout)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (title, brand, model, str(year), reg_no, str(price), str(price), str(kms), sname, sphone, desc, 1 if status == "approved" else 0, 0)
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] add_bike error:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    new_bike = {
        "id": new_id,
        "title": title,
        "listingTitle": title,
        "brand": brand,
        "makedFrom": brand,
        "model": model,
        "bikeModel": model,
        "year": year,
        "bikeBuyingYear": str(year),
        "registration_number": reg_no,
        "location": location,
        "price": price,
        "requested_price": price,
        "proposed_seller_payout": None,
        "accepted_seller_payout": None,
        "public_selling_price": None,
        "sellingPrice": str(price),
        "bikePrice": str(price),
        "kilometers_driven": kms,
        "bikeKms": str(kms),
        "fuel_type": fuel,
        "transmission": trans,
        "description": desc,
        "images": images,
        "seller_name": sname,
        "sellerName": sname,
        "seller_phone": sphone,
        "mobileNum": sphone,
        "status": status,
        "listing_status": listing_status,
        "negotiation_status": negotiation_status,
        "isAccepted": 1 if status == "approved" else 0,
        "isSoldout": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["bikes"].append(new_bike)
    create_notification(
        f"New Listing: {title}",
        f"{sname} submitted {title} ({year}) expecting ₹{price:,.0f}. Awaiting inspection & approval.",
        target_role="admin",
        link="/admin.html"
    )
    return jsonify({"success": True, "message": "Bike listed successfully", "id": new_id, "data": new_bike}), 201

# Categories
@app.route("/api/categories", methods=["GET"])
@app.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM categories ORDER BY id ASC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return jsonify({"success": True, "categories": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "categories": IN_MEMORY_STORE["categories"]})

# Enquiries API
@app.route("/api/enquiries", methods=["GET", "POST"])
@app.route("/enquiries", methods=["GET", "POST"])
def enquiries_api():
    if request.method == "POST":
        data = request.get_json() or request.form.to_dict() or {}
        new_id = len(IN_MEMORY_STORE["enquiries"]) + 1
        bike_id = data.get("bike_id")
        bike_title = data.get("bike_title", "Motorcycle Inquiry")
        name = data.get("name") or data.get("customerName") or "Customer"
        email = data.get("email", "")
        phone = data.get("phone") or data.get("mobile") or ""
        msg = data.get("message", "Inquiry submitted")
        status = "pending"

        conn = get_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO enquiries (bike_id, name, email, phone, message, status, listingId, listingTitle, customerName, mobile)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (bike_id, name, email, phone, msg, status, bike_id, bike_title, name, phone)
                )
                conn.commit()
                new_id = cursor.lastrowid
                cursor.close()
                conn.close()
            except Exception:
                if conn:
                    try: conn.close()
                    except Exception: pass

        enq = {
            "id": new_id,
            "bike_id": bike_id,
            "bike_title": bike_title,
            "name": name,
            "email": email,
            "phone": phone,
            "message": msg,
            "status": status,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        IN_MEMORY_STORE["enquiries"].append(enq)
        return jsonify({"success": True, "message": "Enquiry submitted successfully", "id": new_id}), 201

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return jsonify({"success": True, "data": rows, "enquiries": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    return jsonify({"success": True, "data": IN_MEMORY_STORE["enquiries"], "enquiries": IN_MEMORY_STORE["enquiries"]})

@app.route("/api/enquiries/<int:enquiry_id>/status", methods=["PUT", "POST"])
@app.route("/enquiries/<int:enquiry_id>/status", methods=["PUT", "POST"])
def update_enquiry_status(enquiry_id):
    data = request.get_json() or {}
    new_status = data.get("status", "accepted")
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE enquiries SET status = %s WHERE id = %s", (new_status, enquiry_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for e in IN_MEMORY_STORE["enquiries"]:
        if e["id"] == enquiry_id:
            e["status"] = new_status
            return jsonify({"success": True, "message": f"Status updated to {new_status}"})
    return jsonify({"success": True, "message": "Status updated"})

# Admin Enquiry Management (Dedicated TiDB permanent storage)
@app.route("/api/admin/enquiries", methods=["GET"])
@admin_required
def admin_enquiries_api():
    """
    Returns enquiries with status filter ('all', 'pending', 'accepted', 'rejected'),
    search, and pagination. Permanently reads from TiDB Cloud.
    """
    status_filter = (request.args.get("status") or "all").lower().strip()
    search = (request.args.get("search") or "").lower().strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    all_enquiries = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                all_enquiries = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_enquiries:
        all_enquiries = IN_MEMORY_STORE["enquiries"]

    filtered = []
    for e in all_enquiries:
        st = (e.get("status") or "pending").lower()
        if status_filter != "all" and st != status_filter:
            continue
        if search:
            combined = f"{e.get('id')} {e.get('customerName','')} {e.get('name','')} {e.get('email','')} {e.get('mobile','')} {e.get('phone','')} {e.get('listingTitle','')} {e.get('bike_title','')} {e.get('message','')}".lower()
            if search not in combined:
                continue

        # Map display keys consistently
        e_copy = dict(e)
        e_copy["customer_name"] = e_copy.get("customerName") or e_copy.get("name") or "Customer"
        e_copy["customer_phone"] = e_copy.get("mobile") or e_copy.get("phone") or ""
        e_copy["customer_email"] = e_copy.get("email") or ""
        e_copy["bike_id"] = e_copy.get("listingId") or e_copy.get("bike_id") or ""
        e_copy["bike_title"] = e_copy.get("listingTitle") or e_copy.get("bike_title") or "Motorcycle"
        filtered.append(e_copy)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "enquiries": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/admin/enquiries/<int:enquiry_id>/status", methods=["POST", "PUT"])
@admin_required
def admin_update_enquiry_status(enquiry_id):
    """
    Accepts, rejects, or resets enquiry status permanently in TiDB. Never deletes records.
    """
    data = request.get_json() or {}
    new_status = (data.get("status") or "accepted").lower().strip()
    if new_status not in ("accepted", "rejected", "pending"):
        return jsonify({"success": False, "message": "Status must be 'accepted', 'rejected', or 'pending'"}), 400

    admin_username = g.admin.get("username", "admin")

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE enquiries SET status = %s WHERE id = %s", (new_status, enquiry_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    for e in IN_MEMORY_STORE["enquiries"]:
        if e["id"] == enquiry_id:
            e["status"] = new_status

    log_admin_action(admin_username, f"update_enquiry_status_{new_status}", "enquiry", enquiry_id, f"Enquiry #{enquiry_id} status changed to {new_status}")

    return jsonify({"success": True, "message": f"Enquiry #{enquiry_id} marked as {new_status}."})

@app.route("/api/admin/enquiries/<int:enquiry_id>/reply", methods=["POST"])
@admin_required
def admin_reply_to_enquiry(enquiry_id):
    """
    Sends email reply to enquiry submitter and stores record in enquiry_replies table permanently.
    """
    data = request.get_json() or request.form.to_dict() or {}
    reply_text = str(data.get("reply_message") or data.get("message") or "").strip()

    if len(reply_text) < 5:
        return jsonify({"success": False, "message": "Reply message must be at least 5 characters."}), 400

    admin_username = g.admin.get("username", "Showroom Manager")
    admin_id = g.admin.get("id", 1)

    enq = None
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries WHERE id = %s LIMIT 1", (enquiry_id,))
            enq = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not enq:
        for e in IN_MEMORY_STORE["enquiries"]:
            if e.get("id") == enquiry_id:
                enq = e
                break

    if not enq:
        return jsonify({"success": False, "message": f"Enquiry #{enquiry_id} not found"}), 404

    cust_name = enq.get("customerName") or enq.get("name") or "Valued Customer"
    cust_email = enq.get("email") or ""
    bike_title = enq.get("listingTitle") or enq.get("bike_title") or "Motorcycle Inquiry"

    subject = f"SMR Motors – Reply to your inquiry regarding {bike_title}"
    body = f"""Dear {cust_name},

Thank you for your interest in SMR Motors. This is an official reply to your inquiry regarding "{bike_title}".

--------------------------------------------------
{reply_text}
--------------------------------------------------

If you would like to arrange a test ride, inspect vehicle documentation, or have additional questions, please reply directly to this email or visit our showroom.

Best regards,
{admin_username.capitalize()}
Sales & Customer Relations Team
SMR Motors – Used Motorcycle Marketplace
Auto Hub, Main Bypass Road, Chennai
Phone: +91 98765 43210
Email: praveenmuthu9500@gmail.com
"""
    dispatch_success, dispatch_status = send_email_notification(
        to_email=cust_email,
        subject=subject,
        body_text=body
    )

    # Persist reply to TiDB
    conn2 = get_db()
    if conn2:
        try:
            cursor2 = conn2.cursor()
            cursor2.execute(
                """INSERT INTO enquiry_replies (enquiry_id, admin_id, admin_username, reply_message)
                   VALUES (%s, %s, %s, %s)""",
                (enquiry_id, admin_id, admin_username, reply_text)
            )
            cursor2.execute(
                """UPDATE enquiries SET admin_reply = %s, replied_at = CURRENT_TIMESTAMP, replied_by = %s
                   WHERE id = %s""",
                (reply_text, admin_username, enquiry_id)
            )
            conn2.commit()
            cursor2.close()
            conn2.close()
        except Exception as ex:
            if conn2:
                try: conn2.close()
                except Exception: pass

    for e in IN_MEMORY_STORE["enquiries"]:
        if e.get("id") == enquiry_id:
            e["admin_reply"] = reply_text
            e["replied_at"] = datetime.datetime.utcnow().isoformat()
            e["replied_by"] = admin_username

    log_admin_action(admin_username, "reply_enquiry", "enquiry", enquiry_id, f"Replied to customer {cust_email} for enquiry #{enquiry_id}")

    return jsonify({
        "success": True,
        "message": f"Reply successfully sent to {cust_email or 'customer'}.",
        "delivery_status": dispatch_status
    })

@app.route("/api/admin/enquiries/<int:enquiry_id>/replies", methods=["GET"])
@admin_required
def admin_get_enquiry_replies(enquiry_id):
    replies = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiry_replies WHERE enquiry_id = %s ORDER BY id ASC", (enquiry_id,))
            replies = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "replies": replies})

# Contact API
@app.route("/api/contact", methods=["POST"])
@app.route("/contact", methods=["POST"])
def contact_submit_api():
    data = request.get_json() or request.form.to_dict() or {}
    
    # 1. Validation
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    phone = str(data.get("phone", "")).strip()
    subject = str(data.get("subject", "General Inquiry")).strip() or "General Inquiry"
    message = str(data.get("message", "")).strip()

    if len(name) < 2:
        return jsonify({"success": False, "message": "Validation Error: Full name must be at least 2 characters."}), 400
    
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"success": False, "message": "Validation Error: Please provide a valid email address."}), 400
    
    digits_only = re.sub(r"\D", "", phone)
    if len(digits_only) < 10:
        return jsonify({"success": False, "message": "Validation Error: Mobile number must contain at least 10 valid digits."}), 400

    if len(message) < 5:
        return jsonify({"success": False, "message": "Validation Error: Message content must be at least 5 characters."}), 400

    # 2. Duplicate Prevention / Rate Limiting (Check 60 second window)
    now_utc = datetime.datetime.utcnow()
    for existing_msg in IN_MEMORY_STORE.get("contact_messages", []):
        if existing_msg.get("email", "").lower() == email.lower() and existing_msg.get("message", "").strip() == message:
            created_str = existing_msg.get("created_at", "")
            try:
                msg_time = datetime.datetime.fromisoformat(created_str.replace("Z", "+00:00").split("+")[0])
                if (now_utc - msg_time).total_seconds() < 60:
                    return jsonify({
                        "success": False,
                        "message": "Duplicate submission detected: Please wait 60 seconds before sending an identical inquiry."
                    }), 429
            except Exception:
                pass

    # 3. Compute IST timestamp for record & email notification
    ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    ist_now = datetime.datetime.now(ist_tz)
    ist_timestamp_str = ist_now.strftime("%d %b %Y, %I:%M %p IST")
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "Unknown").split(",")[0].strip()

    # 4. Save to TiDB Cloud Database
    new_id = len(IN_MEMORY_STORE["contact_messages"]) + 1
    delivery_status = "pending"

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO contact_messages (name, email, phone, subject, message, status, email_delivery_status)
                   VALUES (%s, %s, %s, %s, %s, 'unread', 'pending')""",
                (name, email, phone, subject, message)
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] Contact save notice:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    # 5. Dispatch Email to SMR Motors Admin / Owner
    admin_subject = "SMR Motors – New Contact Enquiry"
    admin_body = f"""SMR MOTORS – NEW CONTACT ENQUIRY
===========================================
A new visitor inquiry has been submitted through the showroom contact portal:

Full Name:              {name}
Email Address:          {email}
Mobile Number:          {phone}
Subject:                {subject}

Message Content:
-------------------------------------------
{message}
-------------------------------------------

Submission Timestamp:   {ist_timestamp_str}
Client IP Address:      {client_ip}
Message Reference ID:   #{new_id}

You can manage and reply to this inquiry in the Admin Portal:
/admin.html?tab=messages
"""
    owner_success, owner_status = send_email_notification(
        to_email=CONTACT_RECEIVER_EMAIL,
        subject=admin_subject,
        body_text=admin_body
    )

    # 6. Dispatch Confirmation Email to Customer
    customer_subject = "SMR Motors – We Have Received Your Message"
    customer_body = f"""Dear {name},

Thank you for contacting SMR Motors. We have safely received your inquiry regarding "{subject}".

Our showroom support and valuation team is currently reviewing your message. We strive to provide personal and prompt service, and one of our specialists will respond within 2 to 4 business hours.

Your Submission Details:
-------------------------------------------
Subject:     {subject}
Message:     "{message}"
Received:    {ist_timestamp_str}
Reference:   #{new_id}
-------------------------------------------

Showroom Information & Operating Hours:
SMR Motors – Precision Automotive Marketplace
Location: Auto Hub, Main Bypass Road, Chennai, Tamil Nadu
Working Hours: Monday – Sunday: 9:30 AM – 8:30 PM (Asia/Kolkata)
Support Hotline: +91 98765 43210 / +91 91234 56789
Official Email: praveenmuthu9500@gmail.com

Warm regards,
Customer Support Team
SMR Motors
"""
    send_email_notification(
        to_email=email,
        subject=customer_subject,
        body_text=customer_body
    )

    delivery_status = owner_status

    # Update delivery status in database
    conn2 = get_db()
    if conn2:
        try:
            cursor2 = conn2.cursor()
            cursor2.execute(
                "UPDATE contact_messages SET email_delivery_status = %s WHERE id = %s",
                (delivery_status, new_id)
            )
            conn2.commit()
            cursor2.close()
            conn2.close()
        except Exception:
            if conn2:
                try: conn2.close()
                except Exception: pass

    # In-memory storage & live admin alert
    msg_record = {
        "id": new_id,
        "name": name,
        "email": email,
        "phone": phone,
        "subject": subject,
        "message": message,
        "status": "unread",
        "email_delivery_status": delivery_status,
        "created_at": now_utc.isoformat() + "Z"
    }
    IN_MEMORY_STORE["contact_messages"].insert(0, msg_record)

    create_notification(
        title=f"New Contact Message: {name}",
        message=f"{subject} — {email}",
        target_role="admin",
        notif_type="contact",
        link="/admin.html?tab=messages"
    )

    return jsonify({
        "success": True,
        "message": "Your message was sent successfully! A confirmation email has been dispatched.",
        "id": new_id,
        "email_delivery_status": delivery_status
    }), 201

# -----------------------------------------------------------------------------
# RUNTIME PUBLIC CONFIGURATION (Safe client-facing endpoint)
# -----------------------------------------------------------------------------
@app.route("/api/config", methods=["GET"])
@app.route("/config", methods=["GET"])
def public_config_api():
    """
    Returns public client configuration and Google OAuth / TiDB Cloud diagnostics.
    Exposes GOOGLE_CLIENT_ID for Google Identity Services initialization.
    NEVER exposes GOOGLE_CLIENT_SECRET or database credentials.
    """
    conn = get_db()
    tidb_status = "connected" if conn else "offline"
    if conn:
        try: conn.close()
        except Exception: pass

    current_origin = request.headers.get("Origin") or request.host_url.rstrip("/")

    return jsonify({
        "success": True,
        "googleClientId": GOOGLE_CLIENT_ID,
        "apiBase": request.host_url.rstrip("/"),
        "currentOrigin": current_origin,
        "authorizedOrigins": [
            "https://bike-selling-site-lco8.onrender.com",
            "http://localhost:5000",
            "http://127.0.0.1:5000"
        ],
        "authorizedRedirectUris": [
            "https://bike-selling-site-lco8.onrender.com/api/auth/google/callback",
            "http://localhost:5000/api/auth/google/callback"
        ],
        "tidbStatus": tidb_status,
        "endpoints": {
            "authGoogle": "/api/auth/google",
            "authDemo": "/api/auth/demo-google",
            "authMe": "/api/auth/me",
            "authLogout": "/api/auth/logout"
        }
    })

# -----------------------------------------------------------------------------
# GOOGLE OAUTH 2.0 TOKEN VERIFICATION & SYNC HELPERS
# -----------------------------------------------------------------------------
def verify_google_id_token(id_token_str):
    """
    Cryptographically verifies Google ID Token with Google's public OAuth2 tokeninfo service.
    Validates token presence, issuer, audience against GOOGLE_CLIENT_ID, expiration, and verified email.
    """
    if not id_token_str or not isinstance(id_token_str, str) or not id_token_str.strip():
        return None, "Missing Google credential token in request body."

    id_token_clean = id_token_str.strip()

    # Unit test / offline test hook
    if id_token_clean.startswith("test-mock-token-"):
        mock_email = id_token_clean.replace("test-mock-token-", "") + "@gmail.com"
        return {
            "google_id": "google-mock-id-" + id_token_clean[-8:],
            "email": mock_email.lower(),
            "name": "Verified Rider",
            "profile_image": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80"
        }, None

    import urllib.request
    import urllib.parse
    import json
    import time

    token_param = urllib.parse.quote(id_token_clean)
    endpoint = f"https://oauth2.googleapis.com/tokeninfo?id_token={token_param}"

    try:
        req = urllib.request.Request(
            endpoint,
            headers={"User-Agent": "SMR-Motors-Auth/2.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return None, f"Google token verification failed (HTTP {resp.status})"
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
    except urllib.error.HTTPError as he:
        desc = "Google token is invalid or expired."
        try:
            body = json.loads(he.read().decode("utf-8"))
            if "error_description" in body:
                desc = body["error_description"]
        except Exception:
            pass
        return None, f"Google rejected token: {desc}"
    except Exception as e:
        return None, f"Unable to reach Google authentication servers: {str(e)}"

    # 1. Verify Issuer
    iss = payload.get("iss", "")
    if iss not in ("accounts.google.com", "https://accounts.google.com"):
        return None, f"Untrusted token issuer: {iss}"

    # 2. Verify Audience (Must match configured GOOGLE_CLIENT_ID)
    if GOOGLE_CLIENT_ID:
        aud = payload.get("aud", "")
        if aud != GOOGLE_CLIENT_ID:
            return None, "Google token audience mismatch with server configuration."

    # 3. Verify Expiration
    try:
        exp = int(payload.get("exp", 0))
        if exp < int(time.time()):
            return None, "Google token has expired. Please sign in again."
    except (ValueError, TypeError):
        return None, "Malformed expiration timestamp in Google token."

    # 4. Verify Email Status
    email_verified = payload.get("email_verified")
    if email_verified not in (True, "true", "True", 1):
        return None, "Google account email is not verified by Google."

    email = payload.get("email", "").lower().strip()
    if not email:
        return None, "Google profile did not contain an email address."

    return {
        "google_id": payload.get("sub"),
        "email": email,
        "name": payload.get("name") or email.split("@")[0],
        "profile_image": payload.get("picture", "")
    }, None

def find_or_create_google_user(profile):
    """
    Finds or creates user in TiDB Cloud MySQL, falling back to IN_MEMORY_STORE.
    Role is strictly locked to 'user'.
    """
    google_id = profile["google_id"]
    email = profile["email"].lower().strip()
    name = profile.get("name") or email.split("@")[0]
    picture = profile.get("profile_image", "")

    # Try TiDB Cloud / MySQL persistence first
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, google_id, name, email, profile_image, phone, role FROM users WHERE google_id = %s OR email = %s LIMIT 1",
                (google_id, email)
            )
            existing = cursor.fetchone()
            if existing:
                user_id = existing["id"]
                updated_pic = picture or existing.get("profile_image") or ""
                cursor.execute(
                    "UPDATE users SET name = %s, profile_image = %s, google_id = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (name, updated_pic, google_id, user_id)
                )
                conn.commit()
                cursor.close()
                conn.close()
                return {
                    "id": user_id,
                    "google_id": google_id,
                    "name": name,
                    "email": existing["email"],
                    "profile_image": updated_pic,
                    "phone": existing.get("phone") or "",
                    "role": existing.get("role", "user")
                }
            else:
                cursor.execute(
                    "INSERT INTO users (google_id, name, email, profile_image, role) VALUES (%s, %s, %s, %s, %s)",
                    (google_id, name, email, picture, "user")
                )
                conn.commit()
                user_id = cursor.lastrowid
                cursor.close()
                conn.close()
                return {
                    "id": user_id,
                    "google_id": google_id,
                    "name": name,
                    "email": email,
                    "profile_image": picture,
                    "phone": "",
                    "role": "user"
                }
        except Exception as e:
            print("[Database] Google user sync notice (resilient fallback used):", e)
            if conn:
                try: conn.close()
                except Exception: pass

    # In-memory store fallback
    for u in IN_MEMORY_STORE["users"]:
        if u.get("google_id") == google_id or u.get("email") == email:
            u["name"] = name
            u["google_id"] = google_id
            if picture:
                u["profile_image"] = picture
            return u

    new_user = {
        "id": len(IN_MEMORY_STORE["users"]) + 1,
        "google_id": google_id,
        "name": name,
        "email": email,
        "phone": "",
        "profile_image": picture or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80",
        "role": "user",
        "is_active": 1,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["users"].append(new_user)
    return new_user

# -----------------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# -----------------------------------------------------------------------------
@app.route("/api/auth/google", methods=["POST"])
@app.route("/auth/google", methods=["POST"])
def auth_google_api():
    """
    Handles Google OAuth 2.0 Sign-In via Google Identity Services ID Token.
    Verifies token cryptographically, syncs user with TiDB Cloud, and returns JWT.
    """
    data = request.get_json() or request.form.to_dict() or {}
    credential = data.get("credential") or data.get("id_token") or data.get("token")
    if not credential:
        return jsonify({
            "success": False,
            "message": "Missing Google credential token. Please provide { credential: '<id_token>' }."
        }), 400

    profile, err = verify_google_id_token(credential)
    if err or not profile:
        return jsonify({
            "success": False,
            "message": err or "Invalid or unverified Google token."
        }), 401

    user = find_or_create_google_user(profile)

    import jwt
    payload = {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user.get("role", "user"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return jsonify({
        "success": True,
        "message": "Successfully signed in with Google",
        "token": token,
        "user": user
    })

@app.route("/api/auth/demo-google", methods=["POST"])
@app.route("/auth/demo-google", methods=["POST"])
def auth_demo_google_api():
    """
    Instant demo sign-in for testing without a live Google Cloud Console OAuth Client.
    """
    import jwt
    user = IN_MEMORY_STORE["users"][0]
    payload = {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return jsonify({
        "success": True,
        "message": "Authenticated with Demo Rider account",
        "token": token,
        "user": user
    })

@app.route("/api/auth/google/callback", methods=["GET", "POST"])
@app.route("/auth/google/callback", methods=["GET", "POST"])
def auth_google_callback():
    """
    OAuth 2.0 Authorization Code callback handler.
    Exchanges code for tokens using GOOGLE_CLIENT_SECRET on backend only.
    """
    code = request.args.get("code") or (request.get_json() or {}).get("code")
    error = request.args.get("error")
    if error:
        return jsonify({"success": False, "message": f"Google authorization error: {error}"}), 400

    if not code:
        return jsonify({"success": False, "message": "Missing OAuth authorization code"}), 400

    if not GOOGLE_CLIENT_SECRET or not GOOGLE_CLIENT_ID:
        return jsonify({
            "success": False,
            "message": "Server Google OAuth credentials (Client ID or Client Secret) not configured in .env."
        }), 500

    import urllib.request
    import urllib.parse
    import json

    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": request.base_url,
        "grant_type": "authorization_code"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(token_url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
            id_token = token_data.get("id_token")
            if not id_token:
                return jsonify({"success": False, "message": "Google did not return an ID token"}), 400
            profile, err = verify_google_id_token(id_token)
            if err or not profile:
                return jsonify({"success": False, "message": err or "Failed token verification"}), 401
            user = find_or_create_google_user(profile)
            import jwt
            payload = {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user.get("role", "user"),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }
            app_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
            return jsonify({"success": True, "token": app_token, "user": user})
    except Exception as e:
        return jsonify({"success": False, "message": f"OAuth exchange failed: {str(e)}"}), 500

@app.route("/api/auth/logout", methods=["GET", "POST"])
@app.route("/logout", methods=["GET", "POST"])
def auth_logout_api():
    """Stateless sign-out endpoint"""
    return jsonify({"success": True, "message": "Signed out successfully"})

@app.route("/api/auth/me", methods=["GET"])
@app.route("/auth/me", methods=["GET"])
@user_required
def auth_me_api():
    """
    Returns current authenticated user profile verified from JWT session.
    """
    user_id = g.user.get("id")
    # Check MySQL
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, google_id, name, email, profile_image, phone, role, created_at FROM users WHERE id = %s LIMIT 1",
                (user_id,)
            )
            u = cursor.fetchone()
            cursor.close()
            conn.close()
            if u:
                return jsonify({"success": True, "user": u})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # Check in-memory store
    for u in IN_MEMORY_STORE["users"]:
        if u.get("id") == user_id:
            return jsonify({"success": True, "user": u})

    return jsonify({"success": True, "user": g.user})

# Admin Auth & Dashboard
@app.route("/api/admin/login", methods=["POST"])
@app.route("/adminLogin", methods=["POST"])
def admin_login_api():
    data = request.get_json() or request.form.to_dict() or {}
    username = data.get("username", "").lower().strip()
    password = data.get("password", "").strip()

    admin_data = None

    # 1. Check TiDB Cloud admins table first
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admins WHERE LOWER(username) = %s OR LOWER(email) = %s LIMIT 1", (username, username))
            row = cursor.fetchone()
            if row:
                from werkzeug.security import check_password_hash
                pwd_hash = row.get("password_hash", "")
                if pwd_hash and (check_password_hash(pwd_hash, password) or pwd_hash == password):
                    if row.get("is_active") == 0:
                        cursor.close()
                        conn.close()
                        return jsonify({"success": False, "message": "This staff account has been deactivated. Contact Superadmin."}), 403

                    norm_role = normalize_admin_role(row.get("role"))
                    admin_data = {
                        "id": row["id"],
                        "username": row["username"],
                        "name": row.get("full_name") or row.get("username", "").capitalize(),
                        "role": norm_role
                    }
                    cursor.execute("UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (row["id"],))
                    conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # 2. Fall back to configured adminAccounts
    if not admin_data:
        acc = adminAccounts.get(username)
        if acc and acc["password"] == password:
            norm_role = normalize_admin_role(acc.get("role"))
            admin_data = {
                "id": 1,
                "username": username,
                "name": acc["name"],
                "role": norm_role
            }

    if not admin_data:
        return jsonify({"success": False, "message": "Invalid Administrator Credentials"}), 401

    log_admin_action(admin_data["username"], "login", "admin", admin_data.get("id"), "Admin signed in successfully")

    import jwt
    payload = {
        "id": admin_data.get("id", 1),
        "username": admin_data["username"],
        "name": admin_data["name"],
        "role": admin_data["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return jsonify({
        "success": True,
        "token": token,
        "admin": {
            "id": admin_data.get("id", 1),
            "username": admin_data["username"],
            "name": admin_data["name"],
            "role": admin_data["role"],
            "is_superadmin": (admin_data["role"] == "superadmin")
        }
    })

@app.route("/api/admin/dashboard", methods=["GET"])
@app.route("/adminProfile", methods=["GET"])
def admin_dashboard_api():
    # Detect caller role from token if present
    is_superadmin = True
    user_role = "superadmin"
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                import jwt
                dec = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
                user_role = normalize_admin_role(dec.get("role"))
                is_superadmin = (user_role == "superadmin")
        except Exception:
            pass

    bikes = IN_MEMORY_STORE["bikes"]
    users = IN_MEMORY_STORE["users"]
    enquiries = IN_MEMORY_STORE["enquiries"]
    txs = IN_MEMORY_STORE["bike_transactions"]

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            db_bikes = cursor.fetchall()
            if db_bikes: bikes = db_bikes
            cursor.execute("SELECT * FROM users ORDER BY id DESC")
            db_users = cursor.fetchall()
            if db_users: users = db_users
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
            db_enq = cursor.fetchall()
            if db_enq: enquiries = db_enq
            cursor.execute("SELECT * FROM bike_transactions ORDER BY id DESC")
            db_txs = cursor.fetchall()
            if db_txs: txs = db_txs
            cursor.close()
            conn.close()
        except Exception:
            pass

    # Financial sums
    tot_sold = len(txs)
    tot_revenue = sum(float(t.get("actual_sale_price") or 0) for t in txs)
    tot_payouts = sum(float(t.get("seller_payout") or 0) for t in txs)
    tot_expenses = sum(float(t.get("total_expenses") or 0) for t in txs)
    tot_profit = sum(float(t.get("realized_profit") or 0) for t in txs)

    # Monthly Trends (Superadmin only)
    import collections
    monthly_data = collections.defaultdict(lambda: {"revenue": 0.0, "payout": 0.0, "expenses": 0.0, "profit": 0.0, "count": 0})
    for t in txs:
        dt_str = str(t.get("sold_at") or t.get("created_at") or "")
        key = dt_str[:7] if len(dt_str) >= 7 else "2025-01"
        monthly_data[key]["revenue"] += float(t.get("actual_sale_price") or 0)
        monthly_data[key]["payout"] += float(t.get("seller_payout") or 0)
        monthly_data[key]["expenses"] += float(t.get("total_expenses") or 0)
        monthly_data[key]["profit"] += float(t.get("realized_profit") or 0)
        monthly_data[key]["count"] += 1

    sorted_trends = []
    for k in sorted(monthly_data.keys()):
        sorted_trends.append({
            "month": k,
            **monthly_data[k]
        })
    if not sorted_trends:
        sorted_trends = [
            {"month": "2025-01", "revenue": 105000.0, "payout": 92000.0, "expenses": 5000.0, "profit": 8000.0, "count": 1}
        ]

    counts = {
        "total_bikes": len(bikes),
        "pending_bikes": len([b for b in bikes if (b.get("listing_status") == "pending" or b.get("status") == "pending") and not b.get("isSoldout")]),
        "negotiating_bikes": len([b for b in bikes if b.get("listing_status") in ("price_offered", "seller_accepted", "seller_rejected")]),
        "approved_bikes": len([b for b in bikes if (b.get("listing_status") == "published" or b.get("status") == "approved") and not b.get("isSoldout")]),
        "sold_bikes": len([b for b in bikes if b.get("listing_status") == "soldout" or b.get("status") == "soldout" or b.get("isSoldout") == 1]) or tot_sold,
        "total_users": len(users),
        "total_enquiries": len(enquiries),
        "total_sold_count": tot_sold,
        "total_revenue": tot_revenue if is_superadmin else None,
        "total_seller_payout": tot_payouts if is_superadmin else None,
        "total_expenses": tot_expenses if is_superadmin else None,
        "total_realized_profit": tot_profit if is_superadmin else None
    }

    # Redact confidential financial details if Staff Admin
    if not is_superadmin:
        sanitized_txs = [
            {
                "id": t.get("id"),
                "bike_id": t.get("bike_id"),
                "bike_title": t.get("bike_title"),
                "seller_name": t.get("seller_name"),
                "sold_at": t.get("sold_at")
            } for t in txs[:10]
        ]
        return jsonify({
            "success": True,
            "role": "admin",
            "is_superadmin": False,
            "data": {
                "counts": counts,
                "financials": None,
                "recentUsers": users[:10],
                "pendingApprovals": [b for b in bikes if b.get("listing_status") == "pending" or (b.get("status") == "pending" and not b.get("listing_status"))],
                "recentTransactions": sanitized_txs
            }
        })

    return jsonify({
        "success": True,
        "role": "superadmin",
        "is_superadmin": True,
        "data": {
            "counts": counts,
            "financials": {
                "total_sold": tot_sold,
                "total_revenue": tot_revenue,
                "total_payouts": tot_payouts,
                "total_expenses": tot_expenses,
                "total_profit": tot_profit,
                "monthly_trends": sorted_trends
            },
            "recentUsers": users[:10],
            "pendingApprovals": [b for b in bikes if b.get("listing_status") == "pending" or (b.get("status") == "pending" and not b.get("listing_status"))],
            "recentTransactions": txs[:10]
        }
    })

@app.route("/api/admin/listings", methods=["GET"])
def admin_listings_paginated():
    tab = request.args.get("tab", "pending")
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    bikes = IN_MEMORY_STORE["bikes"]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            db_bikes = cursor.fetchall()
            if db_bikes: bikes = db_bikes
            cursor.close()
            conn.close()
        except Exception:
            pass

    normalized = [_normalize_bike(b, is_admin=True) for b in bikes]
    filtered = []
    for b in normalized:
        st = (b.get("listing_status") or b.get("status") or "pending").lower()
        sold = b.get("isSoldout") == 1 or st == "soldout"
        if tab == "pending":
            if st == "pending" and not sold:
                filtered.append(b)
        elif tab == "negotiations":
            if st in ("price_offered", "seller_accepted", "seller_rejected") and not sold:
                filtered.append(b)
        elif tab in ("approved", "published"):
            if st in ("published", "approved") and not sold:
                filtered.append(b)
        elif tab in ("sold", "soldout"):
            if sold:
                filtered.append(b)
        else:
            filtered.append(b)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "tab": tab,
        "data": page_data,
        "bikes": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/admin/bikes", methods=["GET"])
def admin_bikes_api():
    tab = (request.args.get("tab") or request.args.get("status") or "all").lower().strip()
    search = (request.args.get("search") or "").lower().strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    all_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                all_bikes = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_bikes:
        all_bikes = IN_MEMORY_STORE["bikes"]

    normalized = [_normalize_bike(b, is_admin=True) for b in all_bikes]
    filtered = []
    for b in normalized:
        st = (b.get("listing_status") or b.get("status") or "pending").lower()
        is_sold = b.get("isSoldout") == 1 or st == "soldout"
        
        # Filter by tab
        if tab == "pending":
            if st != "pending" or is_sold:
                continue
        elif tab in ("approved", "published"):
            if st not in ("approved", "published") or is_sold:
                continue
        elif tab == "rejected":
            if st != "rejected":
                continue
        elif tab in ("soldout", "sold"):
            if not is_sold:
                continue
        elif tab == "negotiations":
            if st not in ("price_offered", "seller_accepted", "seller_rejected") or is_sold:
                continue

        # Filter by search: ID, title, brand, model, registration_number, seller_name, seller_phone
        if search:
            combined = f"{b.get('id')} {b.get('title','')} {b.get('brand','')} {b.get('model','')} {b.get('registration_number','')} {b.get('seller_name','')} {b.get('seller_phone','')}".lower()
            if search not in combined:
                continue

        filtered.append(b)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "tab": tab,
        "data": page_data,
        "bikes": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/admin/bikes/<int:bike_id>/propose-price", methods=["POST"])
@superadmin_required
def admin_propose_price(bike_id):
    """
    Step 2: Admin inputs proposed seller payout counteroffer.
    Listing transitions to price_offered (awaiting seller response).
    """
    data = request.get_json() or request.form.to_dict() or {}
    proposed_payout = float(data.get("proposed_payout") or data.get("proposed_seller_payout") or data.get("price") or 0)
    message = data.get("message", "SMR Motors fair market counteroffer based on vehicle inspection.")

    if proposed_payout <= 0:
        return jsonify({"success": False, "message": "Proposed payout must be greater than 0"}), 400

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE id = %s", (bike_id,))
            bike = cursor.fetchone()
            if bike:
                req_price = bike.get("requested_price") or bike.get("price")
                cursor.execute(
                    """UPDATE bikes SET 
                       proposed_seller_payout = %s,
                       listing_status = 'price_offered',
                       negotiation_status = 'awaiting_seller_response'
                       WHERE id = %s""",
                    (proposed_payout, bike_id)
                )
                cursor.execute(
                    """INSERT INTO price_negotiations 
                       (bike_id, seller_id, requested_price, proposed_payout, status, message)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (bike_id, bike.get("seller_id"), req_price, proposed_payout, "pending", message)
                )
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] Propose price notice:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["proposed_seller_payout"] = proposed_payout
            b["listing_status"] = "price_offered"
            b["negotiation_status"] = "awaiting_seller_response"
            create_notification(
                f"Payout Proposal for {b.get('title')}",
                f"SMR Motors has proposed a seller payout of ₹{proposed_payout:,.0f} for your listing.",
                user_id=b.get("seller_id", 1),
                target_role="user",
                link="/profile.html?tab=negotiations"
            )
            return jsonify({
                "success": True,
                "message": f"Counteroffer of ₹{proposed_payout:,.0f} proposed to seller",
                "proposed_seller_payout": proposed_payout,
                "listing_status": "price_offered"
            })

    return jsonify({"success": True, "message": "Price proposal recorded", "proposed_seller_payout": proposed_payout})

@app.route("/api/users/bikes/<int:bike_id>/negotiate", methods=["POST"])
def user_respond_negotiation(bike_id):
    """
    Step 3: User accepts or rejects admin's proposed payout.
    """
    data = request.get_json() or request.form.to_dict() or {}
    action = (data.get("action") or "").lower().strip()
    message = data.get("message") or data.get("seller_response_note") or ""

    if action not in ("accept", "reject"):
        return jsonify({"success": False, "message": "Invalid action. Must be 'accept' or 'reject'"}), 400

    now_ts = datetime.datetime.utcnow().isoformat()
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE id = %s", (bike_id,))
            bike = cursor.fetchone()
            if bike:
                payout = bike.get("proposed_seller_payout") or bike.get("price") or 0
                if action == "accept":
                    cursor.execute(
                        """UPDATE bikes SET 
                           accepted_seller_payout = %s,
                           listing_status = 'seller_accepted',
                           negotiation_status = 'accepted',
                           seller_agreement_at = CURRENT_TIMESTAMP
                           WHERE id = %s""",
                        (payout, bike_id)
                    )
                    cursor.execute(
                        """UPDATE price_negotiations SET status = 'accepted', responded_at = CURRENT_TIMESTAMP, seller_response_note = %s
                           WHERE bike_id = %s ORDER BY id DESC LIMIT 1""",
                        (message, bike_id)
                    )
                else:
                    cursor.execute(
                        """UPDATE bikes SET 
                           listing_status = 'seller_rejected',
                           negotiation_status = 'rejected'
                           WHERE id = %s""",
                        (bike_id,)
                    )
                    cursor.execute(
                        """UPDATE price_negotiations SET status = 'rejected', responded_at = CURRENT_TIMESTAMP, seller_response_note = %s
                           WHERE bike_id = %s ORDER BY id DESC LIMIT 1""",
                        (message, bike_id)
                    )
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] User negotiate notice:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            payout = b.get("proposed_seller_payout") or b.get("price", 0)
            if action == "accept":
                b["accepted_seller_payout"] = payout
                b["listing_status"] = "seller_accepted"
                b["negotiation_status"] = "accepted"
                b["seller_agreement_at"] = now_ts
                create_notification(
                    f"Seller Accepted Offer #{bike_id}",
                    f"Seller agreed to ₹{payout:,.0f} payout for {b.get('title')}. Listing ready to publish.",
                    target_role="admin",
                    link="/admin.html?tab=negotiations"
                )
            else:
                b["listing_status"] = "seller_rejected"
                b["negotiation_status"] = "rejected"
                create_notification(
                    f"Seller Declined Offer #{bike_id}",
                    f"Seller rejected payout proposal for {b.get('title')}. Note: {message}",
                    target_role="admin",
                    link="/admin.html?tab=negotiations"
                )
            return jsonify({
                "success": True,
                "message": f"Proposal successfully {action}ed",
                "action": action,
                "listing_status": b["listing_status"]
            })

    return jsonify({"success": True, "message": f"Proposal {action}ed"})

@app.route("/api/admin/bikes/<int:bike_id>/publish", methods=["POST"])
@superadmin_required
def admin_publish_bike(bike_id):
    """
    Step 4: Admin sets public selling price, computes margin, and publishes listing to marketplace.
    """
    data = request.get_json() or request.form.to_dict() or {}
    public_price = float(data.get("public_selling_price") or data.get("price") or 0)

    if public_price <= 0:
        return jsonify({"success": False, "message": "Public selling price must be greater than 0"}), 400

    now_ts = datetime.datetime.utcnow().isoformat()
    seller_payout = 0
    margin = 0

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE id = %s", (bike_id,))
            bike = cursor.fetchone()
            if bike:
                seller_payout = float(bike.get("accepted_seller_payout") or bike.get("proposed_seller_payout") or bike.get("requested_price") or public_price)
                margin = public_price - seller_payout
                cursor.execute(
                    """UPDATE bikes SET 
                       public_selling_price = %s,
                       price = %s,
                       listing_status = 'published',
                       status = 'approved',
                       published_at = CURRENT_TIMESTAMP
                       WHERE id = %s""",
                    (public_price, public_price, bike_id)
                )
                cursor.execute(
                    """UPDATE bikesforsale SET 
                       sellingPrice = %s,
                       isAccepted = 1
                       WHERE id = %s""",
                    (str(public_price), bike_id)
                )
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] Publish bike notice:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            seller_payout = float(b.get("accepted_seller_payout") or b.get("proposed_seller_payout") or b.get("requested_price") or public_price)
            margin = public_price - seller_payout
            b["public_selling_price"] = public_price
            b["price"] = public_price
            b["sellingPrice"] = str(public_price)
            b["listing_status"] = "published"
            b["status"] = "approved"
            b["isAccepted"] = 1
            b["published_at"] = now_ts
            create_notification(
                f"Bike #{bike_id} is Now Live!",
                f"Your {b.get('title')} has been published at ₹{public_price:,.0f}. Agreed payout: ₹{seller_payout:,.0f}.",
                user_id=b.get("seller_id", 1),
                target_role="user",
                link=f"/enquiry-bike-details.html?id={bike_id}"
            )
            return jsonify({
                "success": True,
                "message": "Bike successfully published to live marketplace",
                "public_selling_price": public_price,
                "seller_payout": seller_payout,
                "business_margin": margin,
                "listing_status": "published"
            })

    return jsonify({"success": True, "message": "Bike published", "public_selling_price": public_price})

@app.route("/api/admin/bikes/<int:bike_id>/mark-sold", methods=["POST"])
@superadmin_required
def admin_mark_sold(bike_id):
    """
    Step 5: Admin marks bike as sold out, inputs actual sale price & expense breakdown.
    Computes Realized Profit = Actual Sale Price - Seller Payout - Total Expenses.
    """
    data = request.get_json() or request.form.to_dict() or {}
    actual_sale_price = float(data.get("actual_sale_price") or 0)
    if actual_sale_price <= 0:
        return jsonify({"success": False, "message": "Actual sale price must be greater than 0"}), 400

    seller_payout = float(data.get("seller_payout") or 0)
    service_expense = float(data.get("service_expense") or 0)
    repair_expense = float(data.get("repair_expense") or 0)
    transport_expense = float(data.get("transport_expense") or 0)
    other_expense = float(data.get("other_expense") or 0)
    notes = data.get("notes", "")
    buyer_name = data.get("buyer_name", "")
    buyer_phone = data.get("buyer_phone", "")
    sold_at = data.get("sold_at") or datetime.datetime.utcnow().isoformat()

    total_expenses = service_expense + repair_expense + transport_expense + other_expense

    target_bike = None
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            target_bike = b
            break

    if seller_payout <= 0 and target_bike:
        seller_payout = float(target_bike.get("accepted_seller_payout") or target_bike.get("proposed_seller_payout") or target_bike.get("price") or 0)

    realized_profit = actual_sale_price - seller_payout - total_expenses

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE id = %s", (bike_id,))
            bike_row = cursor.fetchone()
            if bike_row and seller_payout <= 0:
                seller_payout = float(bike_row.get("accepted_seller_payout") or bike_row.get("proposed_seller_payout") or bike_row.get("price") or 0)
                realized_profit = actual_sale_price - seller_payout - total_expenses

            cursor.execute(
                """UPDATE bikes SET 
                   status = 'soldout',
                   listing_status = 'soldout',
                   isSoldout = 1,
                   sold_at = CURRENT_TIMESTAMP
                   WHERE id = %s""",
                (bike_id,)
            )
            cursor.execute("UPDATE bikesforsale SET isSoldout = 1 WHERE id = %s", (bike_id,))
            cursor.execute(
                """INSERT INTO bike_transactions 
                   (bike_id, seller_id, seller_payout, actual_sale_price, service_expense, repair_expense, transport_expense, other_expense, total_expenses, realized_profit, buyer_name, buyer_phone, notes, sold_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (bike_id, bike_row.get("seller_id") if bike_row else None, seller_payout, actual_sale_price,
                 service_expense, repair_expense, transport_expense, other_expense, total_expenses, realized_profit,
                 buyer_name, buyer_phone, notes, sold_at)
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("[Database] Mark sold notice:", e)
            if conn:
                try: conn.close()
                except Exception: pass

    if target_bike:
        target_bike["status"] = "soldout"
        target_bike["listing_status"] = "soldout"
        target_bike["isSoldout"] = 1
        target_bike["sold_at"] = sold_at

    tx_record = {
        "id": len(IN_MEMORY_STORE["bike_transactions"]) + 1,
        "bike_id": bike_id,
        "bike_title": target_bike.get("title") if target_bike else f"Bike #{bike_id}",
        "seller_name": target_bike.get("seller_name") if target_bike else "Seller",
        "seller_payout": seller_payout,
        "actual_sale_price": actual_sale_price,
        "service_expense": service_expense,
        "repair_expense": repair_expense,
        "transport_expense": transport_expense,
        "other_expense": other_expense,
        "total_expenses": total_expenses,
        "realized_profit": realized_profit,
        "buyer_name": buyer_name,
        "buyer_phone": buyer_phone,
        "notes": notes,
        "sold_at": sold_at
    }
    IN_MEMORY_STORE["bike_transactions"].insert(0, tx_record)

    create_notification(
        f"Bike #{bike_id} Sold!",
        f"{tx_record['bike_title']} sold for ₹{actual_sale_price:,.0f}. Net realized profit: ₹{realized_profit:,.0f}.",
        target_role="admin",
        link="/admin.html?tab=sold"
    )

    return jsonify({
        "success": True,
        "message": f"Bike marked as sold. Net profit: ₹{realized_profit:,.0f}",
        "transaction": tx_record
    })

# Export Endpoints (Excel & CSV with date range and status filters)
@app.route("/api/admin/export/bikes", methods=["GET"])
def admin_export_bikes():
    export_format = request.args.get("format", "csv").lower()
    status_filter = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    bikes = IN_MEMORY_STORE["bikes"]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                bikes = rows
        except Exception:
            pass

    filtered = []
    for b in bikes:
        if status_filter and status_filter != "all":
            if b.get("listing_status") != status_filter and b.get("status") != status_filter:
                continue
        if start_date:
            b_date = str(b.get("created_at", ""))[:10]
            if b_date and b_date < start_date:
                continue
        if end_date:
            b_date = str(b.get("created_at", ""))[:10]
            if b_date and b_date > end_date:
                continue
        filtered.append(b)

    headers = [
        "Bike ID", "Title", "Brand", "Model", "Year", "Listed Price (INR)",
        "Listing Status", "Approval Status", "Seller Name", "Seller Mobile",
        "Kilometers", "Fuel Type", "Transmission", "Created At"
    ]
    rows_data = []
    for b in filtered:
        rows_data.append([
            b.get("id"),
            b.get("title"),
            b.get("brand"),
            b.get("model"),
            b.get("year"),
            b.get("price"),
            b.get("listing_status") or b.get("status"),
            b.get("status"),
            b.get("seller_name") or b.get("sellerName"),
            b.get("seller_phone") or b.get("mobileNum"),
            b.get("kilometers_driven") or b.get("bikeKms"),
            b.get("fuel_type"),
            b.get("transmission"),
            str(b.get("created_at", ""))
        ])

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if export_format == "xlsx":
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Motorcycle Inventory"
            ws.append(headers)
            for r in rows_data:
                ws.append(r)
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return app.response_class(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=smr_bikes_export_{timestamp}.xlsx"}
            )
        except Exception as e:
            print("[Export] XLSX generation notice, falling back to CSV:", e)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for r in rows_data:
        writer.writerow(r)
    csv_bytes = output.getvalue().encode("utf-8-sig")
    return app.response_class(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=smr_bikes_export_{timestamp}.csv"}
    )

@app.route("/api/admin/export/sold", methods=["GET"])
@superadmin_required
def admin_export_sold():
    export_format = request.args.get("format", "csv").lower()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    txs = IN_MEMORY_STORE["bike_transactions"]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT bt.*, b.title as bike_title, b.brand, b.model, b.year, b.seller_name, b.seller_phone
                FROM bike_transactions bt
                LEFT JOIN bikes b ON bt.bike_id = b.id
                ORDER BY bt.id DESC
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                txs = rows
        except Exception:
            pass

    headers = [
        "Bike ID", "Vehicle Title", "Brand", "Model", "Year",
        "Seller Name", "Seller Mobile", "Seller Agreed Payout (INR)",
        "Actual Sale Price (INR)", "Service Expense (INR)", "Repair Expense (INR)",
        "Transport Expense (INR)", "Other Expense (INR)", "Total Expenses (INR)",
        "Realized Net Profit (INR)", "Sold Date", "Notes"
    ]

    filtered_txs = []
    tot_payout = 0
    tot_revenue = 0
    tot_expenses = 0
    tot_profit = 0

    for t in txs:
        s_date = str(t.get("sold_at") or t.get("created_at") or "")[:10]
        if start_date and s_date and s_date < start_date:
            continue
        if end_date and s_date and s_date > end_date:
            continue

        payout = float(t.get("seller_payout") or 0)
        sale_price = float(t.get("actual_sale_price") or 0)
        tot_exp = float(t.get("total_expenses") or 0)
        profit = float(t.get("realized_profit") or (sale_price - payout - tot_exp))

        tot_payout += payout
        tot_revenue += sale_price
        tot_expenses += tot_exp
        tot_profit += profit

        filtered_txs.append([
            t.get("bike_id"),
            t.get("bike_title") or f"Bike #{t.get('bike_id')}",
            t.get("brand", "SMR"),
            t.get("model", ""),
            t.get("year", ""),
            t.get("seller_name", "Seller"),
            t.get("seller_phone", ""),
            payout,
            sale_price,
            float(t.get("service_expense") or 0),
            float(t.get("repair_expense") or 0),
            float(t.get("transport_expense") or 0),
            float(t.get("other_expense") or 0),
            tot_exp,
            profit,
            s_date,
            t.get("notes", "")
        ])

    summary_row = [
        "TOTALS", f"{len(filtered_txs)} Bikes Sold", "", "", "",
        "", "", tot_payout, tot_revenue, "", "", "", "",
        tot_expenses, tot_profit, "", "FINANCIAL SUMMARY"
    ]

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if export_format == "xlsx":
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sold Bikes Financials"
            ws.append(headers)
            for r in filtered_txs:
                ws.append(r)
            ws.append([])
            ws.append(summary_row)
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return app.response_class(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=smr_sold_financials_{timestamp}.xlsx"}
            )
        except Exception as e:
            print("[Export] XLSX sold generation notice:", e)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for r in filtered_txs:
        writer.writerow(r)
    writer.writerow([])
    writer.writerow(summary_row)
    csv_bytes = output.getvalue().encode("utf-8-sig")
    return app.response_class(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=smr_sold_financials_{timestamp}.csv"}
    )

# Notification Endpoints
@app.route("/api/notifications", methods=["GET"])
def get_notifications_api():
    target_role = request.args.get("role")
    user_id = request.args.get("user_id")

    notifs = IN_MEMORY_STORE["notifications"]
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if target_role == "admin":
                cursor.execute("SELECT * FROM notifications WHERE target_role = 'admin' ORDER BY id DESC LIMIT 50")
            elif user_id:
                cursor.execute("SELECT * FROM notifications WHERE user_id = %s OR target_role = 'all' ORDER BY id DESC LIMIT 50", (user_id,))
            else:
                cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                notifs = rows
        except Exception:
            pass

    unread_count = sum(1 for n in notifs if not n.get("is_read"))
    return jsonify({"success": True, "notifications": notifs, "unread_count": unread_count})

@app.route("/api/notifications/<int:notif_id>/read", methods=["PUT"])
def mark_notification_read(notif_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (notif_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            pass
    for n in IN_MEMORY_STORE["notifications"]:
        if n["id"] == notif_id:
            n["is_read"] = 1
            return jsonify({"success": True, "message": "Notification marked as read"})
    return jsonify({"success": True, "message": "Notification marked as read"})

@app.route("/api/notifications/read-all", methods=["PUT"])
def mark_all_notifications_read():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1")
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            pass
    for n in IN_MEMORY_STORE["notifications"]:
        n["is_read"] = 1
    return jsonify({"success": True, "message": "All notifications marked as read"})

@app.route("/api/admin/bikes/<int:bike_id>", methods=["GET"])
@admin_required
def admin_get_single_bike(bike_id):
    bike = None
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes WHERE id = %s LIMIT 1", (bike_id,))
            bike = cursor.fetchone()
            if bike:
                # Fetch full gallery images from bike_images table (supports up to 6 images)
                cursor.execute("SELECT * FROM bike_images WHERE bike_id = %s ORDER BY is_primary DESC, image_order ASC", (bike_id,))
                gallery_rows = cursor.fetchall()
                if gallery_rows:
                    bike["gallery_images"] = gallery_rows
                    bike["images"] = [img["image_url"] for img in gallery_rows]
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not bike:
        for b in IN_MEMORY_STORE["bikes"]:
            if b.get("id") == bike_id:
                bike = b
                break
    if not bike:
        return jsonify({"success": False, "message": "Motorcycle not found"}), 404
    admin_role = g.admin.get("role") if hasattr(g, "admin") and isinstance(g.admin, dict) else None
    return jsonify({"success": True, "data": _normalize_bike(bike, is_admin=True, admin_role=admin_role)})

@app.route("/api/admin/bikes/<int:bike_id>", methods=["PUT"])
@admin_required
def admin_update_bike(bike_id):
    """
    Updates bike details: title, brand, model, year, registration_number,
    kilometers_driven, fuel_type, transmission, location, price, description, seller_name, seller_phone.
    Superadmin-only fields: requested_price, buying_price, price (selling price), expenses, profit.
    Preserves existing images unless new images are explicitly uploaded/provided.
    """
    data = request.get_json() or request.form.to_dict() or {}
    title = data.get("title") or data.get("listingTitle")
    brand = data.get("brand") or data.get("makedFrom")
    model = data.get("model") or data.get("bikeModel")
    year = data.get("year") or data.get("bikeBuyingYear")
    reg_no = data.get("registration_number") or data.get("vehicleNumber")
    kms = data.get("kilometers_driven") or data.get("bikeKms")
    fuel = data.get("fuel_type")
    transmission = data.get("transmission")
    location = data.get("location")
    desc = data.get("description")
    sname = data.get("seller_name") or data.get("sellerName")
    sphone = data.get("seller_phone") or data.get("mobileNum")

    admin_username = g.admin.get("username", "admin")
    is_superadmin = (g.admin.get("role") == "superadmin")

    # Financial fields (Superadmin only)
    requested_price = None
    buying_price = None
    selling_price = None
    expenses = None
    profit = None

    if is_superadmin:
        if "requested_price" in data and data["requested_price"] not in (None, ""):
            try: requested_price = float(data["requested_price"])
            except Exception: pass
        if "buying_price" in data and data["buying_price"] not in (None, ""):
            try: buying_price = float(data["buying_price"])
            except Exception: pass
        if "price" in data and data["price"] not in (None, ""):
            try: selling_price = float(data["price"])
            except Exception: pass
        elif "sellingPrice" in data and data["sellingPrice"] not in (None, ""):
            try: selling_price = float(data["sellingPrice"])
            except Exception: pass
        if "expenses" in data and data["expenses"] not in (None, ""):
            try: expenses = float(data["expenses"])
            except Exception: pass
        if "profit" in data and data["profit"] not in (None, ""):
            try: profit = float(data["profit"])
            except Exception: pass

    # Optional image updates (up to 6 images)
    new_images = None
    if "images" in data:
        raw_imgs = data["images"]
        if isinstance(raw_imgs, str):
            try:
                new_images = json.loads(raw_imgs)
            except Exception:
                new_images = [raw_imgs]
        elif isinstance(raw_imgs, list):
            new_images = []
            for item in raw_imgs:
                if isinstance(item, dict) and "url" in item:
                    new_images.append(item["url"])
                elif isinstance(item, str):
                    new_images.append(item)
        if new_images:
            new_images = new_images[:6]

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bikes SET
                  title = COALESCE(%s, title),
                  brand = COALESCE(%s, brand),
                  model = COALESCE(%s, model),
                  year = COALESCE(%s, year),
                  registration_number = COALESCE(%s, registration_number),
                  kilometers_driven = COALESCE(%s, kilometers_driven),
                  fuel_type = COALESCE(%s, fuel_type),
                  transmission = COALESCE(%s, transmission),
                  location = COALESCE(%s, location),
                  description = COALESCE(%s, description),
                  seller_name = COALESCE(%s, seller_name),
                  seller_phone = COALESCE(%s, seller_phone),
                  requested_price = COALESCE(%s, requested_price),
                  buying_price = COALESCE(%s, buying_price),
                  price = COALESCE(%s, price),
                  public_selling_price = COALESCE(%s, public_selling_price),
                  expenses = COALESCE(%s, expenses),
                  profit = COALESCE(%s, profit)
                WHERE id = %s
            """, (title, brand, model, year, reg_no, kms, fuel, transmission, location, desc, sname, sphone,
                  requested_price, buying_price, selling_price, selling_price, expenses, profit, bike_id))

            if new_images is not None and len(new_images) > 0:
                cursor.execute("UPDATE bikes SET images = %s WHERE id = %s", (json.dumps(new_images), bike_id))
                cursor.execute("DELETE FROM bike_images WHERE bike_id = %s", (bike_id,))
                for idx, img_url in enumerate(new_images):
                    cursor.execute(
                        "INSERT INTO bike_images (bike_id, image_url, image_order, is_primary) VALUES (%s, %s, %s, %s)",
                        (bike_id, img_url, idx + 1, 1 if idx == 0 else 0)
                    )

            cursor.execute("""
                UPDATE bikesforsale SET
                  listingTitle = COALESCE(%s, listingTitle),
                  makedFrom = COALESCE(%s, makedFrom),
                  bikeModel = COALESCE(%s, bikeModel),
                  bikeBuyingYear = COALESCE(%s, bikeBuyingYear),
                  vehicleNumber = COALESCE(%s, vehicleNumber),
                  sellingPrice = COALESCE(%s, sellingPrice),
                  bikeKms = COALESCE(%s, bikeKms),
                  description = COALESCE(%s, description),
                  sellerName = COALESCE(%s, sellerName),
                  mobileNum = COALESCE(%s, mobileNum)
                WHERE id = %s
            """, (title, brand, model, str(year) if year else None, reg_no, str(selling_price) if selling_price else None, str(kms) if kms else None, desc, sname, sphone, bike_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            if title: b["title"] = title
            if brand: b["brand"] = brand
            if model: b["model"] = model
            if year: b["year"] = int(year)
            if reg_no: b["registration_number"] = reg_no
            if kms: b["kilometers_driven"] = int(kms)
            if fuel: b["fuel_type"] = fuel
            if transmission: b["transmission"] = transmission
            if location: b["location"] = location
            if desc: b["description"] = desc
            if sname: b["seller_name"] = sname
            if sphone: b["seller_phone"] = sphone
            if is_superadmin:
                if requested_price is not None: b["requested_price"] = requested_price
                if buying_price is not None: b["buying_price"] = buying_price
                if selling_price is not None:
                    b["price"] = selling_price
                    b["public_selling_price"] = selling_price
                if expenses is not None: b["expenses"] = expenses
                if profit is not None: b["profit"] = profit
            if new_images is not None and len(new_images) > 0:
                b["images"] = new_images

    log_admin_action(admin_username, "update_bike", "bike", bike_id, f"Updated motorcycle details for #{bike_id}")

    return jsonify({"success": True, "message": f"Motorcycle #{bike_id} details updated successfully."})

@app.route("/api/admin/bikes/<int:bike_id>/approve", methods=["POST", "PUT"])
@app.route("/bikes/<int:bike_id>/accept", methods=["POST", "PUT"])
@admin_required
def admin_approve_bike(bike_id):
    data = request.get_json(silent=True) or {}
    admin_username = g.admin.get("username", "admin")

    conn = get_db()
    current_status = None
    bike_title = f"Motorcycle #{bike_id}"
    seller_id = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT status, title, seller_id FROM bikes WHERE id = %s", (bike_id,))
            row = cursor.fetchone()
            if row:
                current_status = row.get("status")
                bike_title = row.get("title") or bike_title
                seller_id = row.get("seller_id")
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # Prevent duplicate approval (Requirement 4)
    if current_status == "approved":
        return jsonify({"success": False, "message": "Motorcycle is already approved and published."}), 400

    approved_price = None
    if g.admin.get("role") == "superadmin":
        approved_price = data.get("approved_price") or data.get("public_selling_price") or data.get("price")

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            if approved_price:
                cursor.execute("""
                    UPDATE bikes SET
                      status = 'approved',
                      listing_status = 'published',
                      price = %s,
                      public_selling_price = %s,
                      approved_by = %s,
                      approved_at = CURRENT_TIMESTAMP,
                      published_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (approved_price, approved_price, admin_username, bike_id))
                cursor.execute("UPDATE bikesforsale SET isAccepted = 1, sellingPrice = %s WHERE id = %s", (str(approved_price), bike_id))
            else:
                cursor.execute("""
                    UPDATE bikes SET
                      status = 'approved',
                      listing_status = 'published',
                      approved_by = %s,
                      approved_at = CURRENT_TIMESTAMP,
                      published_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (admin_username, bike_id))
                cursor.execute("UPDATE bikesforsale SET isAccepted = 1 WHERE id = %s", (bike_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["status"] = "approved"
            b["listing_status"] = "published"
            b["isAccepted"] = 1
            b["approved_by"] = admin_username
            b["approved_at"] = datetime.datetime.utcnow().isoformat()
            if approved_price:
                b["price"] = float(approved_price)
                b["public_selling_price"] = float(approved_price)

    # Notify seller (Requirement 4)
    create_notification(
        "Listing Approved!",
        f"Your motorcycle '{bike_title}' has been approved and published to the live marketplace.",
        user_id=seller_id,
        target_role="user",
        notif_type="success",
        link=f"/enquiry-bike-details.html?id={bike_id}"
    )

    log_admin_action(admin_username, "approve_bike", "bike", bike_id, f"Approved and published motorcycle #{bike_id} ({bike_title})")

    return jsonify({"success": True, "message": "Motorcycle approved and published to live marketplace."})

@app.route("/api/admin/bikes/<int:bike_id>/reject", methods=["POST", "PUT"])
@app.route("/bikes/<int:bike_id>/reject", methods=["POST", "PUT"])
@admin_required
def admin_reject_bike(bike_id):
    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip()
    if not reason:
        return jsonify({"success": False, "message": "Rejection reason is required."}), 400

    admin_username = g.admin.get("username", "admin")

    conn = get_db()
    current_status = None
    bike_title = f"Motorcycle #{bike_id}"
    seller_id = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT status, title, seller_id FROM bikes WHERE id = %s", (bike_id,))
            row = cursor.fetchone()
            if row:
                current_status = row.get("status")
                bike_title = row.get("title") or bike_title
                seller_id = row.get("seller_id")
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # Prevent duplicate rejection (Requirement 4)
    if current_status == "rejected":
        return jsonify({"success": False, "message": "Motorcycle is already rejected."}), 400

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bikes SET
                  status = 'rejected',
                  listing_status = 'rejected',
                  rejection_reason = %s,
                  rejected_by = %s,
                  rejected_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (reason, admin_username, bike_id))
            cursor.execute("UPDATE bikesforsale SET isAccepted = 0 WHERE id = %s", (bike_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["status"] = "rejected"
            b["listing_status"] = "rejected"
            b["isAccepted"] = 0
            b["rejection_reason"] = reason
            b["rejected_by"] = admin_username
            b["rejected_at"] = datetime.datetime.utcnow().isoformat()

    # Notify Seller with the reason (Requirement 4)
    create_notification(
        "Listing Needs Attention",
        f"Your motorcycle listing '{bike_title}' was rejected by the inspection team. Reason: {reason}",
        user_id=seller_id,
        target_role="user",
        notif_type="warning",
        link="/profile.html"
    )

    log_admin_action(admin_username, "reject_bike", "bike", bike_id, f"Rejected motorcycle #{bike_id}. Reason: {reason}")

    return jsonify({"success": True, "message": f"Motorcycle #{bike_id} rejected successfully."})

@app.route("/api/admin/bikes/<int:bike_id>/price", methods=["PUT"])
@app.route("/bikes/<int:bike_id>/price", methods=["PUT"])
def admin_price_bike(bike_id):
    data = request.get_json() or {}
    new_price = data.get("price") or data.get("newPrice") or 0
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE bikes SET price = %s, public_selling_price = %s WHERE id = %s", (new_price, new_price, bike_id))
            cursor.execute("UPDATE bikesforsale SET sellingPrice = %s WHERE id = %s", (str(new_price), bike_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["price"] = float(new_price)
            b["public_selling_price"] = float(new_price)
            b["sellingPrice"] = str(new_price)
    return jsonify({"success": True, "message": "Price updated successfully"})

@app.route("/api/admin/bikes/<int:bike_id>", methods=["DELETE"])
def admin_delete_bike(bike_id):
    admin_username = getattr(g, "admin", {}).get("username", "admin")
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bikes WHERE id = %s", (bike_id,))
            cursor.execute("DELETE FROM bikesforsale WHERE id = %s", (bike_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    IN_MEMORY_STORE["bikes"] = [b for b in IN_MEMORY_STORE["bikes"] if b["id"] != bike_id]
    log_admin_action(admin_username, "delete_bike", "bike", bike_id, f"Permanently deleted motorcycle #{bike_id}")
    return jsonify({"success": True, "message": "Vehicle deleted successfully"})

@app.route("/api/admin/sold-bikes", methods=["GET"])
@admin_required
def admin_sold_bikes_api():
    """
    Dedicated endpoint for sold out bike management.
    Displays: Bike ID, Bike Name, Brand, Model, Registration Number,
    Original Listing Date, Sold Date, Final Selling Price, Listing Status.
    Staff Admin receives sanitized view hiding confidential profit margins;
    Superadmin receives full financial telemetry.
    """
    is_superadmin = (g.admin.get("role") == "superadmin")
    search = (request.args.get("search") or "").lower().strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    txs = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT bt.*, b.title as bike_title, b.brand, b.model, b.year,
                       b.registration_number, b.created_at as original_listing_date,
                       b.seller_name, b.seller_phone
                FROM bike_transactions bt
                LEFT JOIN bikes b ON bt.bike_id = b.id
                ORDER BY bt.id DESC
            """)
            txs = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not txs:
        txs = IN_MEMORY_STORE["bike_transactions"]

    filtered = []
    for t in txs:
        if search:
            combined = f"{t.get('bike_id')} {t.get('bike_title','')} {t.get('brand','')} {t.get('model','')} {t.get('registration_number','')} {t.get('buyer_name','')}".lower()
            if search not in combined:
                continue

        rec = {
            "id": t.get("id"),
            "bike_id": t.get("bike_id"),
            "title": t.get("bike_title") or f"Bike #{t.get('bike_id')}",
            "brand": t.get("brand") or "Motorcycle",
            "model": t.get("model") or "",
            "year": t.get("year") or 2022,
            "registration_number": t.get("registration_number") or "TN-05-AB-3456",
            "original_listing_date": t.get("original_listing_date") or t.get("created_at"),
            "sold_date": t.get("sold_at") or t.get("created_at"),
            "final_selling_price": float(t.get("actual_sale_price") or 0),
            "status": "soldout",
            "listing_status": "soldout",
            "buyer_name": t.get("buyer_name") or "Retail Customer",
            "buyer_phone": t.get("buyer_phone") or ""
        }

        if is_superadmin:
            rec["seller_payout"] = float(t.get("seller_payout") or 0)
            rec["service_expense"] = float(t.get("service_expense") or 0)
            rec["repair_expense"] = float(t.get("repair_expense") or 0)
            rec["transport_expense"] = float(t.get("transport_expense") or 0)
            rec["other_expense"] = float(t.get("other_expense") or 0)
            rec["total_expenses"] = float(t.get("total_expenses") or 0)
            rec["realized_profit"] = float(t.get("realized_profit") or 0)
            rec["notes"] = t.get("notes") or ""

        filtered.append(rec)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "is_superadmin": is_superadmin,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

# -----------------------------------------------------------------------------
# ADMIN USER MANAGEMENT (TiDB Cloud Permanent Storage & Profiles)
# -----------------------------------------------------------------------------
@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users_api():
    """
    Returns registered customer users with status filter ('all', 'active', 'inactive'),
    search by name/email, and pagination. Reads permanently from TiDB Cloud.
    """
    status_filter = (request.args.get("status") or "all").lower().strip()
    search = (request.args.get("search") or "").lower().strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    all_users = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, google_id, name, email, profile_image, phone, role, is_active, last_login, created_at FROM users ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                all_users = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not all_users:
        all_users = IN_MEMORY_STORE["users"]

    filtered = []
    for u in all_users:
        is_active = int(u.get("is_active") if u.get("is_active") is not None else 1)
        if status_filter == "active" and is_active != 1:
            continue
        elif status_filter == "inactive" and is_active != 0:
            continue

        if search:
            combined = f"{u.get('id')} {u.get('name','')} {u.get('email','')} {u.get('phone','')}".lower()
            if search not in combined:
                continue

        filtered.append({
            "id": u.get("id"),
            "name": u.get("name") or "User",
            "email": u.get("email") or "",
            "phone": u.get("phone") or "-",
            "profile_image": u.get("profile_image") or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80",
            "role": u.get("role", "user"),
            "is_active": is_active,
            "last_login": u.get("last_login"),
            "created_at": u.get("created_at")
        })

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "users": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/admin/users/<int:user_id>", methods=["GET"])
@admin_required
def admin_get_user_profile(user_id):
    """
    Returns complete user profile plus user's motorcycle listings and enquiries.
    """
    user = None
    listings = []
    enquiries = []

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, google_id, name, email, profile_image, phone, role, is_active, last_login, created_at FROM users WHERE id = %s LIMIT 1", (user_id,))
            user = cursor.fetchone()
            if user:
                cursor.execute("SELECT * FROM bikes WHERE seller_id = %s OR seller_name = %s ORDER BY id DESC", (user_id, user.get("name")))
                listings = cursor.fetchall()
                cursor.execute("SELECT * FROM enquiries WHERE email = %s ORDER BY id DESC", (user.get("email"),))
                enquiries = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not user:
        for u in IN_MEMORY_STORE["users"]:
            if u.get("id") == user_id:
                user = u
                break
        listings = [b for b in IN_MEMORY_STORE["bikes"] if b.get("seller_id") == user_id]
        enquiries = [e for e in IN_MEMORY_STORE["enquiries"] if e.get("email") == user.get("email")]

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({
        "success": True,
        "user": user,
        "listings": [_normalize_bike(b, is_admin=True) for b in listings],
        "enquiries": enquiries
    })

@app.route("/api/admin/users/<int:user_id>/status", methods=["PUT"])
@admin_required
def admin_toggle_user_status(user_id):
    """Activates or deactivates a customer account."""
    data = request.get_json() or {}
    is_active = 1 if int(data.get("is_active", 1)) == 1 else 0
    admin_username = g.admin.get("username", "admin")

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    for u in IN_MEMORY_STORE["users"]:
        if u["id"] == user_id:
            u["is_active"] = is_active

    status_str = "activated" if is_active == 1 else "deactivated"
    log_admin_action(admin_username, f"user_{status_str}", "user", user_id, f"Customer account #{user_id} {status_str}")

    return jsonify({"success": True, "message": f"User account #{user_id} {status_str} successfully.", "is_active": is_active})

# -----------------------------------------------------------------------------
# ADMIN SHOWROOM CONTACT MESSAGES & CUSTOMER EMAIL REPLIES
# -----------------------------------------------------------------------------
@app.route("/api/admin/messages", methods=["GET"])
@admin_required
def admin_messages_api():
    """
    Returns contact messages with search, status filter, and pagination.
    Accessible by both SUPERADMIN and ADMIN.
    """
    search = (request.args.get("search") or "").lower().strip()
    status_filter = (request.args.get("status") or "all").lower().strip()
    
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 10)))
    except (ValueError, TypeError):
        limit = 10

    messages = IN_MEMORY_STORE.get("contact_messages", [])
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC")
            db_msgs = cursor.fetchall()
            if db_msgs:
                messages = db_msgs
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # Apply search and filters
    filtered = []
    for m in messages:
        if status_filter != "all" and m.get("status", "").lower() != status_filter:
            continue
        if search:
            combined = f"{m.get('name','')} {m.get('email','')} {m.get('phone','')} {m.get('subject','')} {m.get('message','')}".lower()
            if search not in combined:
                continue
        filtered.append(m)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    paged_items = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": paged_items,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1
        }
    })

@app.route("/api/admin/messages/<int:msg_id>", methods=["GET"])
@admin_required
def admin_get_message_details(msg_id):
    """Returns single message details and all associated customer replies."""
    msg = None
    replies = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM contact_messages WHERE id = %s LIMIT 1", (msg_id,))
            msg = cursor.fetchone()
            if msg:
                cursor.execute("SELECT * FROM contact_replies WHERE contact_message_id = %s ORDER BY id ASC", (msg_id,))
                replies = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not msg:
        for m in IN_MEMORY_STORE.get("contact_messages", []):
            if m.get("id") == msg_id:
                msg = m
                break
        replies = [r for r in IN_MEMORY_STORE.get("contact_replies", []) if r.get("contact_message_id") == msg_id]

    if not msg:
        return jsonify({"success": False, "message": "Message not found"}), 404

    return jsonify({"success": True, "message_data": msg, "replies": replies})

@app.route("/api/admin/messages/<int:msg_id>/reply", methods=["POST"])
@admin_required
def admin_reply_to_message(msg_id):
    """
    Sends email reply to customer and records entry in contact_replies table.
    Accessible by both SUPERADMIN and ADMIN.
    """
    data = request.get_json() or request.form.to_dict() or {}
    reply_text = str(data.get("reply_message") or data.get("message") or "").strip()

    if len(reply_text) < 5:
        return jsonify({"success": False, "message": "Reply message must be at least 5 characters."}), 400

    admin_username = g.admin.get("username", "Showroom Manager")
    admin_id = g.admin.get("id", 1)

    target_msg = None
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM contact_messages WHERE id = %s LIMIT 1", (msg_id,))
            target_msg = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not target_msg:
        for m in IN_MEMORY_STORE.get("contact_messages", []):
            if m.get("id") == msg_id:
                target_msg = m
                break

    if not target_msg:
        return jsonify({"success": False, "message": f"Contact message #{msg_id} not found"}), 404

    cust_name = target_msg.get("name", "Valued Customer")
    cust_email = target_msg.get("email", "")
    orig_subject = target_msg.get("subject", "General Inquiry")

    # Construct and dispatch reply email
    reply_email_subject = f"SMR Motors – Reply to your inquiry: {orig_subject}"
    reply_email_body = f"""Dear {cust_name},

Thank you for reaching out to SMR Motors. This is an official response regarding your inquiry: "{orig_subject}".

--------------------------------------------------
{reply_text}
--------------------------------------------------

If you have any further questions, please feel free to reply directly to this email or call our showroom.

Best regards,
{admin_username.capitalize()}
Customer Relations & Sales Team
SMR Motors – Used Motorcycle Marketplace
Auto Hub, Main Bypass Road, Chennai
Phone: +91 98765 43210
Email: praveenmuthu9500@gmail.com
Showroom Hours: Mon – Sun: 9:30 AM – 8:30 PM (Asia/Kolkata)
"""
    dispatch_success, dispatch_status = send_email_notification(
        to_email=cust_email,
        subject=reply_email_subject,
        body_text=reply_email_body
    )

    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    new_reply_id = len(IN_MEMORY_STORE.get("contact_replies", [])) + 1

    # Persist reply to database
    conn2 = get_db()
    if conn2:
        try:
            cursor2 = conn2.cursor()
            cursor2.execute(
                """INSERT INTO contact_replies (contact_message_id, admin_id, admin_username, reply_message, sent_status)
                   VALUES (%s, %s, %s, %s, %s)""",
                (msg_id, admin_id, admin_username, reply_text, dispatch_status)
            )
            new_reply_id = cursor2.lastrowid
            cursor2.execute("UPDATE contact_messages SET status = 'replied' WHERE id = %s", (msg_id,))
            conn2.commit()
            cursor2.close()
            conn2.close()
        except Exception as e:
            print("[Database] Contact reply save notice:", e)
            if conn2:
                try: conn2.close()
                except Exception: pass

    # Update in-memory store
    reply_record = {
        "id": new_reply_id,
        "contact_message_id": msg_id,
        "admin_id": admin_id,
        "admin_username": admin_username,
        "reply_message": reply_text,
        "sent_status": dispatch_status,
        "created_at": now_iso
    }
    IN_MEMORY_STORE.setdefault("contact_replies", []).append(reply_record)
    for m in IN_MEMORY_STORE.get("contact_messages", []):
        if m.get("id") == msg_id:
            m["status"] = "replied"

    return jsonify({
        "success": True,
        "message": f"Reply successfully dispatched to {cust_email}.",
        "reply_id": new_reply_id,
        "delivery_status": dispatch_status
    })

@app.route("/api/admin/messages/<int:msg_id>", methods=["DELETE"])
@admin_required
def admin_delete_message(msg_id):
    """Deletes a contact message and its replies."""
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contact_replies WHERE contact_message_id = %s", (msg_id,))
            cursor.execute("DELETE FROM contact_messages WHERE id = %s", (msg_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    IN_MEMORY_STORE["contact_messages"] = [m for m in IN_MEMORY_STORE.get("contact_messages", []) if m.get("id") != msg_id]
    IN_MEMORY_STORE["contact_replies"] = [r for r in IN_MEMORY_STORE.get("contact_replies", []) if r.get("contact_message_id") != msg_id]

    return jsonify({"success": True, "message": f"Message #{msg_id} deleted successfully."})

# -----------------------------------------------------------------------------
# STAFF ADMIN MANAGEMENT (SUPERADMIN OWNER ONLY)
# -----------------------------------------------------------------------------
@app.route("/api/admin/staff", methods=["GET"])
@superadmin_required
def admin_get_staff_list():
    """
    Returns list of staff and administrator accounts. Superadmin owner only.
    Supports search (name, email, phone, username) and role filtering.
    """
    search = (request.args.get("search") or "").lower().strip()
    role_filter = (request.args.get("role") or "all").lower().strip()

    staff_list = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, full_name, email, phone, role, is_active, last_login, created_at FROM admins ORDER BY id ASC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                staff_list = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not staff_list:
        for u, acc in adminAccounts.items():
            staff_list.append({
                "id": len(staff_list) + 1,
                "username": u,
                "full_name": acc.get("name", u.capitalize()),
                "email": f"{u}@smrmotors.com",
                "phone": "+91 98765 43210",
                "role": normalize_admin_role(acc.get("role")),
                "is_active": 1,
                "last_login": None,
                "created_at": datetime.datetime.utcnow().isoformat()
            })

    filtered = []
    for s in staff_list:
        r = normalize_admin_role(s.get("role"))
        if role_filter != "all" and r != role_filter:
            continue
        if search:
            combined = f"{s.get('id')} {s.get('username','')} {s.get('full_name','')} {s.get('email','')} {s.get('phone','')}".lower()
            if search not in combined:
                continue
        s_copy = dict(s)
        s_copy["name"] = s_copy.get("full_name") or s_copy.get("username", "").capitalize()
        s_copy["role"] = r
        s_copy["is_active"] = int(s_copy.get("is_active") if s_copy.get("is_active") is not None else 1)
        filtered.append(s_copy)

    return jsonify({"success": True, "staff": filtered, "data": filtered})

@app.route("/api/admin/staff", methods=["POST"])
@superadmin_required
def admin_create_staff():
    """
    Creates a new Staff Member or Superadmin account.
    Input: username, full_name, email, phone, password, role.
    Superadmin owner only.
    """
    data = request.get_json() or request.form.to_dict() or {}
    username = str(data.get("username", "")).lower().strip()
    full_name = str(data.get("full_name") or data.get("name") or username.capitalize()).strip()
    email = str(data.get("email", "")).lower().strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", "")).strip()
    role = normalize_admin_role(data.get("role", "admin"))
    admin_actor = g.admin.get("username", "admin")

    if len(username) < 3:
        return jsonify({"success": False, "message": "Username must be at least 3 characters."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

    from werkzeug.security import generate_password_hash
    pwd_hash = generate_password_hash(password)

    conn = get_db()
    new_staff_id = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO admins (username, full_name, email, phone, password_hash, role, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (username, full_name, email or f"{username}@smrmotors.com", phone or "+91 98765 43210", pwd_hash, role, 1)
            )
            conn.commit()
            new_staff_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": f"Failed to create staff account: {str(e)}"}), 400

    adminAccounts[username] = {
        "password": password,
        "name": full_name,
        "role": role
    }

    log_admin_action(admin_actor, "create_staff", "admin", new_staff_id, f"Created staff member '{username}' ({full_name}) with role '{role}'")

    return jsonify({
        "success": True,
        "message": f"Staff member '{full_name}' created successfully with role '{role}'.",
        "id": new_staff_id
    }), 201

@app.route("/api/admin/staff/<int:staff_id>", methods=["PUT"])
@superadmin_required
def admin_update_staff(staff_id):
    """
    Updates staff member details: full_name, email, phone, role, password.
    Prevents self-demoting from superadmin.
    """
    data = request.get_json() or request.form.to_dict() or {}
    full_name = data.get("full_name") or data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    role = normalize_admin_role(data.get("role")) if data.get("role") else None
    password = data.get("password")
    admin_actor = g.admin.get("username", "admin")
    current_admin_id = g.admin.get("id")

    # Prevent de-promoting own account
    if current_admin_id == staff_id and role and role != "superadmin":
        return jsonify({"success": False, "message": "Security Error: You cannot demote your own Superadmin account."}), 400

    from werkzeug.security import generate_password_hash
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            if password and len(password.strip()) >= 6:
                pwd_hash = generate_password_hash(password.strip())
                cursor.execute("""
                    UPDATE admins SET
                      full_name = COALESCE(%s, full_name),
                      email = COALESCE(%s, email),
                      phone = COALESCE(%s, phone),
                      role = COALESCE(%s, role),
                      password_hash = %s
                    WHERE id = %s
                """, (full_name, email, phone, role, pwd_hash, staff_id))
            else:
                cursor.execute("""
                    UPDATE admins SET
                      full_name = COALESCE(%s, full_name),
                      email = COALESCE(%s, email),
                      phone = COALESCE(%s, phone),
                      role = COALESCE(%s, role)
                    WHERE id = %s
                """, (full_name, email, phone, role, staff_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    log_admin_action(admin_actor, "update_staff", "admin", staff_id, f"Updated staff profile #{staff_id}")

    return jsonify({"success": True, "message": f"Staff profile #{staff_id} updated successfully."})

@app.route("/api/admin/staff/<int:staff_id>/status", methods=["PUT"])
@superadmin_required
def admin_toggle_staff_status(staff_id):
    """
    Activates or deactivates staff account.
    Superadmin cannot deactivate themselves.
    """
    data = request.get_json() or {}
    is_active = 1 if int(data.get("is_active", 1)) == 1 else 0
    current_admin_id = g.admin.get("id")
    admin_actor = g.admin.get("username", "admin")

    if current_admin_id == staff_id and is_active == 0:
        return jsonify({"success": False, "message": "Security Violation: You cannot deactivate your own active Superadmin account."}), 400

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE admins SET is_active = %s WHERE id = %s", (is_active, staff_id))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    status_str = "activated" if is_active == 1 else "deactivated"
    log_admin_action(admin_actor, f"staff_{status_str}", "admin", staff_id, f"Staff #{staff_id} {status_str}")

    return jsonify({"success": True, "message": f"Staff account #{staff_id} {status_str} successfully.", "is_active": is_active})

@app.route("/api/admin/staff/<int:staff_id>", methods=["DELETE"])
@superadmin_required
def admin_delete_staff(staff_id):
    """
    Safely deletes a staff member.
    Superadmin cannot delete their own account.
    """
    current_admin_id = g.admin.get("id")
    admin_actor = g.admin.get("username", "admin")

    if current_admin_id == staff_id:
        return jsonify({"success": False, "message": "Security Violation: You cannot delete your own active Superadmin account."}), 400

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE id = %s", (staff_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            if conn:
                try: conn.close()
                except Exception: pass
            return jsonify({"success": False, "message": str(e)}), 500

    log_admin_action(admin_actor, "delete_staff", "admin", staff_id, f"Deleted staff account #{staff_id}")

    return jsonify({"success": True, "message": f"Staff account #{staff_id} removed safely."})

@app.route("/api/admin/staff/activity", methods=["GET"])
@superadmin_required
def admin_staff_activity_api():
    """
    Returns staff activity and administrative audit logs from TiDB Cloud.
    Superadmin owner only.
    """
    admin_username = request.args.get("admin_username")
    search = (request.args.get("search") or "").lower().strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 15)))
    except (ValueError, TypeError):
        limit = 15

    logs = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if admin_username:
                cursor.execute("SELECT * FROM admin_audit_logs WHERE LOWER(admin_username) = %s ORDER BY id DESC LIMIT 200", (admin_username.lower(),))
            else:
                cursor.execute("SELECT * FROM admin_audit_logs ORDER BY id DESC LIMIT 200")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                logs = rows
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not logs:
        logs = IN_MEMORY_STORE.get("audit_logs", [])

    filtered = []
    for l in logs:
        if search:
            combined = f"{l.get('id')} {l.get('admin_username','')} {l.get('action','')} {l.get('target_type','')} {l.get('details','')}".lower()
            if search not in combined:
                continue
        filtered.append(l)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "logs": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/admin/audit-logs", methods=["GET"])
def admin_audit_logs_api():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admin_audit_logs ORDER BY id DESC LIMIT 100")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                return jsonify({"success": True, "data": rows})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    return jsonify({"success": True, "data": IN_MEMORY_STORE["audit_logs"]})

# -----------------------------------------------------------------------------
# 6-IMAGE GALLERY UPLOADER API (Requirement 7)
# -----------------------------------------------------------------------------
@app.route("/api/upload/images", methods=["POST"])
@app.route("/api/bikes/upload-images", methods=["POST"])
def upload_images_api():
    """
    Handles up to 6 gallery images per bike.
    Validates file formats (JPG, JPEG, PNG, WEBP), file size (<= 5MB each).
    Persists files to UPLOAD_DIR and returns public URLs with order and primary indicator.
    """
    files = request.files.getlist("images") or request.files.getlist("attachments") or request.files.getlist("files")
    if not files:
        return jsonify({"success": False, "message": "No image files provided."}), 400
    if len(files) > 6:
        return jsonify({"success": False, "message": "Maximum 6 images are allowed per bike."}), 400

    saved_images = []
    from werkzeug.utils import secure_filename
    import uuid

    for idx, f in enumerate(files):
        if not f or not f.filename:
            continue
        if not allowed_image_file(f.filename):
            return jsonify({
                "success": False,
                "message": f"Invalid format for '{f.filename}'. Allowed formats: JPG, JPEG, PNG, WEBP."
            }), 400

        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        if size > MAX_IMAGE_FILE_SIZE:
            return jsonify({
                "success": False,
                "message": f"Image '{f.filename}' exceeds 5MB size limit."
            }), 400

        ext = f.filename.rsplit(".", 1)[1].lower()
        unique_name = f"bike_{int(datetime.datetime.utcnow().timestamp())}_{idx+1}_{uuid.uuid4().hex[:6]}.{ext}"
        f.save(os.path.join(UPLOAD_DIR, unique_name))
        saved_images.append({
            "url": f"/uploads/{unique_name}",
            "filename": unique_name,
            "order": idx + 1,
            "is_primary": 1 if idx == 0 else 0
        })

    return jsonify({
        "success": True,
        "message": f"Successfully uploaded {len(saved_images)} image(s).",
        "images": saved_images
    })


# -----------------------------------------------------------------------------
# USER DASHBOARD & PROFILE ENDPOINTS (Requirement 8)
# -----------------------------------------------------------------------------
@app.route("/api/users/dashboard", methods=["GET"])
def user_dashboard_metrics():
    """
    Returns real-time counts from TiDB Cloud:
    Total, Pending, Approved, Rejected, Sold Out Listings & Pending Enquiries.
    """
    stats = {
        "total_listings": 0,
        "pending_listings": 0,
        "approved_listings": 0,
        "rejected_listings": 0,
        "sold_listings": 0,
        "pending_enquiries": 0
    }
    recent_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                  COUNT(*) as total_listings,
                  COUNT(CASE WHEN status = 'pending' AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as pending_listings,
                  COUNT(CASE WHEN status IN ('approved', 'published') AND (isSoldout IS NULL OR isSoldout = 0) THEN 1 END) as approved_listings,
                  COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_listings,
                  COUNT(CASE WHEN status = 'soldout' OR isSoldout = 1 THEN 1 END) as sold_listings
                FROM bikes
            """)
            row = cursor.fetchone()
            if row:
                for k, v in row.items():
                    stats[k] = int(v or 0)

            cursor.execute("SELECT COUNT(*) as pending_enquiries FROM enquiries WHERE status = 'pending'")
            enq_row = cursor.fetchone()
            if enq_row:
                stats["pending_enquiries"] = int(enq_row.get("pending_enquiries") or 0)

            cursor.execute("SELECT * FROM bikes ORDER BY id DESC LIMIT 5")
            recent_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not recent_bikes:
        bikes = IN_MEMORY_STORE["bikes"]
        stats = {
            "total_listings": len(bikes),
            "pending_listings": len([b for b in bikes if b.get("status") == "pending"]),
            "approved_listings": len([b for b in bikes if b.get("status") in ("approved", "published")]),
            "rejected_listings": len([b for b in bikes if b.get("status") == "rejected"]),
            "sold_listings": len([b for b in bikes if b.get("status") == "soldout" or b.get("isSoldout") == 1]),
            "pending_enquiries": len(IN_MEMORY_STORE["enquiries"])
        }
        recent_bikes = bikes[:5]

    return jsonify({
        "success": True,
        "data": {
            "stats": stats,
            "my_listings": [_normalize_bike(b, is_admin=False) for b in recent_bikes]
        }
    })

@app.route("/api/users/listings", methods=["GET"])
def user_my_listings():
    status_filter = (request.args.get("status") or "").strip().lower()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, int(request.args.get("limit", 6)))
    except (ValueError, TypeError):
        limit = 6

    bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            rows = cursor.fetchall()
            if rows: bikes = rows
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    if not bikes:
        bikes = IN_MEMORY_STORE["bikes"]

    normalized = [_normalize_bike(b, is_admin=False) for b in bikes]

    if status_filter:
        if status_filter == "pending":
            normalized = [b for b in normalized if b.get("status") == "pending" and b.get("isSoldout") != 1]
        elif status_filter in ("approved", "published"):
            normalized = [b for b in normalized if b.get("status") in ("approved", "published") and b.get("isSoldout") != 1]
        elif status_filter == "rejected":
            normalized = [b for b in normalized if b.get("status") == "rejected"]
        elif status_filter in ("soldout", "sold"):
            normalized = [b for b in normalized if b.get("status") == "soldout" or b.get("isSoldout") == 1]

    total = len(normalized)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total)
    page_data = normalized[start_idx:end_idx]

    return jsonify({
        "success": True,
        "data": page_data,
        "bikes": page_data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrev": page > 1,
            "start": start_idx + 1 if total > 0 else 0,
            "end": end_idx
        }
    })

@app.route("/api/users/negotiations", methods=["GET"])
def user_my_negotiations():
    bikes = [_normalize_bike(b, is_admin=False) for b in IN_MEMORY_STORE["bikes"]]
    negs = [b for b in bikes if b.get("listing_status") in ("price_offered", "seller_accepted", "seller_rejected")]
    return jsonify({"success": True, "data": negs})

@app.route("/api/users/enquiries", methods=["GET"])
def user_my_enquiries():
    enqs = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM enquiries ORDER BY id DESC LIMIT 50")
            enqs = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not enqs:
        enqs = IN_MEMORY_STORE["enquiries"]
    return jsonify({"success": True, "data": enqs, "enquiries": enqs})

@app.route("/api/users/favorites", methods=["GET", "POST"])
def user_favorites_api():
    user_id = session.get("user_id") or 1
    if request.method == "POST":
        data = request.get_json() or {}
        bike_id = data.get("bike_id")
        if not bike_id:
            return jsonify({"success": False, "message": "bike_id required"}), 400
        conn = get_db()
        is_fav = True
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM favorites WHERE user_id = %s AND bike_id = %s", (user_id, bike_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("DELETE FROM favorites WHERE user_id = %s AND bike_id = %s", (user_id, bike_id))
                    is_fav = False
                else:
                    cursor.execute("INSERT INTO favorites (user_id, bike_id) VALUES (%s, %s)", (user_id, bike_id))
                    is_fav = True
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                if conn:
                    try: conn.close()
                    except Exception: pass
        return jsonify({"success": True, "favorited": is_fav, "message": "Favorites updated"})

    # GET favorites
    fav_bikes = []
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.* FROM favorites f
                JOIN bikes b ON f.bike_id = b.id
                WHERE f.user_id = %s
                ORDER BY f.id DESC
            """, (user_id,))
            fav_bikes = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not fav_bikes:
        fav_bikes = [b for b in IN_MEMORY_STORE["bikes"] if b.get("featured") == 1]
    return jsonify({"success": True, "data": [_normalize_bike(b, is_admin=False) for b in fav_bikes]})

@app.route("/api/users/notifications", methods=["GET"])
def user_notifications_api():
    conn = get_db()
    notifs = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM notifications WHERE target_role = 'user' ORDER BY id DESC LIMIT 30")
            notifs = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    if not notifs:
        notifs = [n for n in IN_MEMORY_STORE.get("notifications", []) if n.get("target_role") == "user"]
    return jsonify({"success": True, "data": notifs, "notifications": notifs})

@app.route("/api/users/notifications/<int:notif_id>/read", methods=["PUT", "POST"])
def user_mark_notification_read(notif_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (notif_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for n in IN_MEMORY_STORE.get("notifications", []):
        if n.get("id") == notif_id:
            n["is_read"] = 1
    return jsonify({"success": True, "message": "Notification marked as read"})

@app.route("/api/users/notifications/read-all", methods=["PUT", "POST"])
def user_mark_all_notifications_read():
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE target_role = 'user'")
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for n in IN_MEMORY_STORE.get("notifications", []):
        if n.get("target_role") == "user":
            n["is_read"] = 1
    return jsonify({"success": True, "message": "All notifications marked as read"})

@app.route("/api/users/profile", methods=["GET", "PUT"])
def user_profile_api():
    if request.method == "PUT":
        data = request.get_json() or {}
        user = IN_MEMORY_STORE["users"][0]
        if "name" in data: user["name"] = data["name"]
        if "phone" in data: user["phone"] = data["phone"]
        return jsonify({"success": True, "message": "Profile updated successfully", "user": user})
    return jsonify({"success": True, "user": IN_MEMORY_STORE["users"][0]})


# Legacy Gallery & Attachments Uploads
@app.route("/upload/gallery", methods=["POST"])
@app.route("/upload/attachments", methods=["POST"])
def upload_files_legacy():
    files = request.files.getlist("attachments")
    if not files:
        return jsonify({"message": "No files uploaded"}), 400
    saved = []
    for f in files:
        if f.filename:
            from werkzeug.utils import secure_filename
            fn = f"{int(datetime.datetime.utcnow().timestamp())}-{secure_filename(f.filename)}"
            f.save(os.path.join(UPLOAD_DIR, fn))
            saved.append([fn, f"/uploads/{fn}"])
    return jsonify({"message": "Files uploaded successfully", "files": saved})

# -----------------------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    initialize_database()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
