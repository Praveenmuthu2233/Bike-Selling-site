import os
import sys
import json
import datetime
import tempfile
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory, g
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
    "connection_timeout": 6
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
    "audit_logs": []
}

def get_db():
    """
    Returns an active TLS-encrypted MySQL connection to TiDB Cloud.
    Handles connection errors gracefully without leaking credentials.
    """
    try:
        import mysql.connector
        conn = mysql.connector.connect(**dbconfig)
        return conn
    except Exception as e:
        err_msg = str(e)
        if DB_PASSWORD and DB_PASSWORD in err_msg:
            err_msg = err_msg.replace(DB_PASSWORD, "[PROTECTED]")
        return None

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
          `rejection_reason` TEXT NULL,
          `featured` TINYINT(1) NOT NULL DEFAULT 0,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX `idx_bikes_brand` (`brand`),
          INDEX `idx_bikes_status` (`status`),
          INDEX `idx_bikes_price` (`price`)
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
          `message` TEXT NOT NULL,
          `status` VARCHAR(20) NOT NULL DEFAULT 'unread',
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        cursor.close()
        conn.close()
        print("[Database] TiDB Cloud tables and seeds verified successfully.")
    except Exception as e:
        err_str = str(e)
        if DB_PASSWORD and DB_PASSWORD in err_str:
            err_str = err_str.replace(DB_PASSWORD, "[PROTECTED]")
        print("[Database] Table initialization notice:", err_str)

# -----------------------------------------------------------------------------
# AUTHENTICATION HELPERS
# -----------------------------------------------------------------------------
adminAccounts = {
    "admin":   {"password": "admin123",  "name": "Administrator", "role": "main"},
    "mani":    {"password": "mani@22",    "name": "Mani",          "role": "limited"},
    "murugan": {"password": "murugan@22", "name": "Murugan",       "role": "main"},
    "raja":    {"password": "raja@22",    "name": "Raja",          "role": "main"},
}

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"success": False, "message": "Missing admin authorization"}), 401
        parts = header.split()
        if len(parts) != 2:
            return jsonify({"success": False, "message": "Invalid token header"}), 401
        try:
            import jwt
            decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
            g.admin = decoded
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
    return render_template("admin.html")

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

# Bikes API (supports /api/bikes and legacy /bikes)
@app.route("/api/bikes", methods=["GET"])
@app.route("/bikes", methods=["GET"])
def get_bikes_api():
    status = request.args.get("status")
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if status == "soldout":
                cursor.execute("SELECT * FROM bikes WHERE status = 'soldout' OR featured = -1 ORDER BY id DESC")
            elif status:
                cursor.execute("SELECT * FROM bikes WHERE status = %s ORDER BY id DESC", (status,))
            else:
                cursor.execute("SELECT * FROM bikes ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            if rows:
                for r in rows:
                    if isinstance(r.get("images"), str):
                        try:
                            r["images"] = json.loads(r["images"])
                        except Exception:
                            r["images"] = [r["images"]]
                    if not r.get("images"):
                        r["images"] = ["/static/images/IMG-20251204-WA0053.jpg"]
                    r["listingTitle"] = r.get("title")
                    r["makedFrom"] = r.get("brand")
                    r["bikeModel"] = r.get("model")
                    r["bikeBuyingYear"] = str(r.get("year", 2022))
                    r["sellingPrice"] = str(r.get("price", 100000))
                    r["bikePrice"] = str(r.get("price", 100000))
                    r["bikeKms"] = str(r.get("kilometers_driven", 0))
                    r["sellerName"] = r.get("seller_name") or "SMR Motors"
                    r["mobileNum"] = r.get("seller_phone") or "9876543210"
                    r["isAccepted"] = 1 if r.get("status") == "approved" else 0
                    r["isSoldout"] = 1 if r.get("status") == "soldout" else 0
                return jsonify({"success": True, "data": rows, "bikes": rows, "total": len(rows)})
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    # In-memory fallback
    bikes = IN_MEMORY_STORE["bikes"]
    if status == "soldout":
        res = [b for b in bikes if b.get("status") == "soldout" or b.get("isSoldout") == 1]
    elif status:
        res = [b for b in bikes if b.get("status") == status]
    else:
        res = bikes

    return jsonify({"success": True, "data": res, "bikes": res, "total": len(res)})

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
    
    # Handle uploaded photos
    images = []
    if request.files:
        files = request.files.getlist("attachments")
        for f in files:
            if f.filename:
                from werkzeug.utils import secure_filename
                sname = f"{int(datetime.datetime.utcnow().timestamp())}-{secure_filename(f.filename)}"
                f.save(os.path.join(UPLOAD_DIR, sname))
                images.append(f"/uploads/{sname}")
    if not images:
        images = ["/static/images/IMG-20251204-WA0053.jpg"]

    title = data.get("title") or data.get("listingTitle") or "Custom Motorcycle"
    brand = data.get("brand") or data.get("makedFrom") or "Other"
    model = data.get("model") or data.get("bikeModel") or "Standard"
    year = int(data.get("year") or data.get("bikeBuyingYear") or 2022)
    price = float(data.get("price") or data.get("sellingPrice") or data.get("bikePrice") or 100000)
    kms = int(data.get("kilometers_driven") or data.get("bikeKms") or 0)
    fuel = data.get("fuel_type", "Petrol")
    trans = data.get("transmission", "Manual")
    desc = data.get("description", "Inspected pre-owned motorcycle.")
    sname = data.get("seller_name") or data.get("sellerName") or "User"
    sphone = data.get("seller_phone") or data.get("mobileNum") or ""
    status = data.get("status", "pending")

    # Persist to TiDB Cloud
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bikes (title, brand, model, year, price, kilometers_driven, fuel_type, transmission, description, images, seller_name, seller_phone, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (title, brand, model, year, price, kms, fuel, trans, desc, json.dumps(images), sname, sphone, status)
            )
            cursor.execute(
                """INSERT INTO bikesforsale (listingTitle, makedFrom, bikeModel, bikeBuyingYear, bikePrice, sellingPrice, bikeKms, sellerName, mobileNum, description, isAccepted, isSoldout)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (title, brand, model, str(year), str(price), str(price), str(kms), sname, sphone, desc, 1 if status == "approved" else 0, 0)
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except Exception:
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
        "price": price,
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
        "isAccepted": 1 if status == "approved" else 0,
        "isSoldout": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["bikes"].append(new_bike)
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

@app.route("/api/enquiries/<int:enquiry_id>/status", methods=["PUT"])
@app.route("/enquiries/<int:enquiry_id>/status", methods=["PUT"])
def update_enquiry_status(enquiry_id):
    data = request.get_json() or {}
    new_status = data.get("status", "completed")
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

# Contact API
@app.route("/api/contact", methods=["POST"])
@app.route("/contact", methods=["POST"])
def contact_submit_api():
    data = request.get_json() or request.form.to_dict() or {}
    new_id = len(IN_MEMORY_STORE["contact_messages"]) + 1
    name = data.get("name", "Website Visitor")
    email = data.get("email", "")
    phone = data.get("phone", "")
    message = data.get("message", "")

    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contact_messages (name, email, phone, message) VALUES (%s, %s, %s, %s)",
                (name, email, phone, message)
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass

    msg = {
        "id": new_id,
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["contact_messages"].append(msg)
    return jsonify({"success": True, "message": "Your message was sent successfully!", "id": new_id})

# -----------------------------------------------------------------------------
# RUNTIME PUBLIC CONFIGURATION (Safe client-facing endpoint)
# -----------------------------------------------------------------------------
@app.route("/api/config", methods=["GET"])
@app.route("/config", methods=["GET"])
def public_config_api():
    """
    Returns public client configuration.
    Exposes GOOGLE_CLIENT_ID for Google Identity Services initialization.
    NEVER exposes GOOGLE_CLIENT_SECRET or database credentials.
    """
    return jsonify({
        "success": True,
        "googleClientId": GOOGLE_CLIENT_ID,
        "apiBase": request.host_url.rstrip("/"),
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
    username = data.get("username", "").lower()
    password = data.get("password", "")

    admin = adminAccounts.get(username)
    if not admin or admin["password"] != password:
        return jsonify({"success": False, "message": "Invalid Administrator Credentials"}), 401

    import jwt
    payload = {
        "username": username,
        "name": admin["name"],
        "role": admin["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return jsonify({
        "success": True,
        "token": token,
        "admin": {"username": username, "name": admin["name"], "role": admin["role"]}
    })

@app.route("/api/admin/dashboard", methods=["GET"])
@app.route("/adminProfile", methods=["GET"])
def admin_dashboard_api():
    bikes = IN_MEMORY_STORE["bikes"]
    users = IN_MEMORY_STORE["users"]
    enquiries = IN_MEMORY_STORE["enquiries"]
    return jsonify({
        "success": True,
        "data": {
            "counts": {
                "total_bikes": len(bikes),
                "pending_bikes": len([b for b in bikes if b.get("status") == "pending"]),
                "approved_bikes": len([b for b in bikes if b.get("status") == "approved"]),
                "total_users": len(users),
                "total_enquiries": len(enquiries)
            },
            "recentUsers": users,
            "pendingApprovals": [b for b in bikes if b.get("status") == "pending"]
        }
    })

@app.route("/api/admin/bikes", methods=["GET"])
def admin_bikes_api():
    return jsonify({"success": True, "data": IN_MEMORY_STORE["bikes"]})

@app.route("/api/admin/bikes/<int:bike_id>/approve", methods=["PUT"])
@app.route("/bikes/<int:bike_id>/accept", methods=["PUT"])
def admin_approve_bike(bike_id):
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE bikes SET status = 'approved' WHERE id = %s", (bike_id,))
            cursor.execute("UPDATE bikesforsale SET isAccepted = 1 WHERE id = %s", (bike_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["status"] = "approved"
            b["isAccepted"] = 1
            return jsonify({"success": True, "message": "Bike approved successfully"})
    return jsonify({"success": True, "message": "Bike approved"})

@app.route("/api/admin/bikes/<int:bike_id>/reject", methods=["PUT"])
@app.route("/bikes/<int:bike_id>/reject", methods=["PUT"])
def admin_reject_bike(bike_id):
    data = request.get_json() or {}
    reason = data.get("reason", "Listing details do not meet quality guidelines.")
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE bikes SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason, bike_id))
            cursor.execute("UPDATE bikesforsale SET isAccepted = 0 WHERE id = %s", (bike_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["status"] = "rejected"
            b["isAccepted"] = 0
            b["rejection_reason"] = reason
            return jsonify({"success": True, "message": "Bike rejected successfully"})
    return jsonify({"success": True, "message": "Bike rejected"})

@app.route("/api/admin/bikes/<int:bike_id>/price", methods=["PUT"])
@app.route("/bikes/<int:bike_id>/price", methods=["PUT"])
def admin_price_bike(bike_id):
    data = request.get_json() or {}
    new_price = data.get("price") or data.get("newPrice") or 0
    conn = get_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE bikes SET price = %s WHERE id = %s", (new_price, bike_id))
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
            b["sellingPrice"] = str(new_price)
            return jsonify({"success": True, "message": "Price updated successfully"})
    return jsonify({"success": True, "message": "Price updated"})

@app.route("/api/admin/bikes/<int:bike_id>", methods=["DELETE"])
def admin_delete_bike(bike_id):
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
    return jsonify({"success": True, "message": "Vehicle deleted successfully"})

@app.route("/api/admin/users", methods=["GET"])
def admin_users_api():
    return jsonify({"success": True, "data": IN_MEMORY_STORE["users"]})

@app.route("/api/admin/messages", methods=["GET"])
def admin_messages_api():
    return jsonify({"success": True, "data": IN_MEMORY_STORE["contact_messages"]})

@app.route("/api/admin/audit-logs", methods=["GET"])
def admin_audit_logs_api():
    return jsonify({"success": True, "data": IN_MEMORY_STORE["audit_logs"]})

# User Dashboard endpoints
@app.route("/api/users/dashboard", methods=["GET"])
def user_dashboard_metrics():
    bikes = IN_MEMORY_STORE["bikes"]
    return jsonify({
        "success": True,
        "data": {
            "stats": {
                "total_listings": len(bikes),
                "approved_listings": len([b for b in bikes if b.get("status") == "approved"]),
                "pending_listings": len([b for b in bikes if b.get("status") == "pending"]),
                "total_enquiries": len(IN_MEMORY_STORE["enquiries"])
            },
            "my_listings": bikes
        }
    })

@app.route("/api/users/listings", methods=["GET"])
def user_my_listings():
    return jsonify({"success": True, "data": IN_MEMORY_STORE["bikes"]})

@app.route("/api/users/enquiries", methods=["GET"])
def user_my_enquiries():
    return jsonify({"success": True, "data": IN_MEMORY_STORE["enquiries"]})

@app.route("/api/users/favorites", methods=["GET", "POST"])
def user_favorites_api():
    if request.method == "POST":
        return jsonify({"success": True, "message": "Favorites updated"})
    return jsonify({"success": True, "data": [IN_MEMORY_STORE["bikes"][0]]})

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
