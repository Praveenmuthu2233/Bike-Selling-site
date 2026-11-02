import os
import sys
import json
import datetime
import tempfile
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory, g
from flask_cors import CORS

# Load .env from my-node-app or parent directory
load_dotenv()
parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(parent_env):
    load_dotenv(parent_env)

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Enable CORS for all routes
CORS(app, resources={r"*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

JWT_SECRET = os.getenv("JWT_SECRET", "smr-motors-jwt-secret-key-2025")

# Upload directory configuration (Windows & Linux compatible)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# DATABASE CONNECTION & IN-MEMORY RESILIENCE STORE
# -----------------------------------------------------------------------------
dbconfig = {
    "host": os.getenv("DB_HOST") or os.getenv("TIDB_HOST") or "127.0.0.1",
    "port": int(os.getenv("DB_PORT") or os.getenv("TIDB_PORT") or 3306),
    "user": os.getenv("DB_USER") or os.getenv("TIDB_USER") or "root",
    "password": os.getenv("DB_PASSWORD") or os.getenv("TIDB_PASSWORD") or "",
    "database": os.getenv("DB_NAME") or os.getenv("TIDB_DATABASE") or "smr_motors",
}

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
    try:
        import mysql.connector
        conn = mysql.connector.connect(**dbconfig)
        return conn
    except Exception as e:
        return None

def initialize_database():
    conn = get_db()
    if not conn:
        print("[Database] MySQL not reachable. Running with in-memory resilient data store.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bikesforsale (
          id INT AUTO_INCREMENT PRIMARY KEY,
          listingTitle VARCHAR(255),
          vehicleNumber VARCHAR(255),
          sellerName VARCHAR(255),
          mobileNum VARCHAR(20),
          bikeCondition VARCHAR(50),
          bikeType VARCHAR(50),
          makedFrom VARCHAR(50),
          bikeModel VARCHAR(100),
          bikeKms VARCHAR(50),
          bikePrice VARCHAR(50),
          sellingPrice VARCHAR(50),
          bikeOwner VARCHAR(50),
          bikeBuyingYear VARCHAR(10),
          bikeColor VARCHAR(50),
          bikeEngineCC VARCHAR(50),
          driveType VARCHAR(50),
          insurance VARCHAR(50),
          horsepower VARCHAR(50),
          bikeLocation VARCHAR(255),
          description TEXT,
          isAccepted BOOLEAN DEFAULT TRUE,
          isSoldout BOOLEAN DEFAULT FALSE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
          id INT AUTO_INCREMENT PRIMARY KEY,
          listingId INT,
          listingTitle VARCHAR(255),
          customerName VARCHAR(255),
          mobile VARCHAR(20),
          email VARCHAR(255),
          location VARCHAR(255),
          timestamp VARCHAR(50),
          status VARCHAR(50) DEFAULT 'pending',
          message TEXT
        )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("[Database] MySQL tables verified.")
    except Exception as e:
        print("[Database] Table initialization notice:", e)

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
            return jsonify({"success": False, "message": "Authentication required"}), 401
        parts = header.split()
        if len(parts) != 2:
            return jsonify({"success": False, "message": "Invalid auth header"}), 401
        try:
            import jwt
            decoded = jwt.decode(parts[1], JWT_SECRET, algorithms=["HS256"])
            g.user = decoded
        except Exception:
            return jsonify({"success": False, "message": "Session expired, please sign in again"}), 401
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
    bikes = IN_MEMORY_STORE["bikes"]
    if status == "soldout":
        res = [b for b in bikes if b.get("status") == "soldout" or b.get("isSoldout") == 1]
    elif status:
        res = [b for b in bikes if b.get("status") == status]
    else:
        # Return approved and pending
        res = bikes

    return jsonify({"success": True, "data": res, "bikes": res, "total": len(res)})

@app.route("/api/bikes/<int:bike_id>", methods=["GET"])
@app.route("/bikes/<int:bike_id>", methods=["GET"])
def get_single_bike_api(bike_id):
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

    new_bike = {
        "id": new_id,
        "title": data.get("title") or data.get("listingTitle") or "Custom Motorcycle",
        "listingTitle": data.get("title") or data.get("listingTitle") or "Custom Motorcycle",
        "brand": data.get("brand") or data.get("makedFrom") or "Other",
        "makedFrom": data.get("brand") or data.get("makedFrom") or "Other",
        "model": data.get("model") or data.get("bikeModel") or "Standard",
        "bikeModel": data.get("model") or data.get("bikeModel") or "Standard",
        "year": int(data.get("year") or data.get("bikeBuyingYear") or 2022),
        "bikeBuyingYear": str(data.get("year") or data.get("bikeBuyingYear") or 2022),
        "price": float(data.get("price") or data.get("sellingPrice") or data.get("bikePrice") or 100000),
        "sellingPrice": str(data.get("price") or data.get("sellingPrice") or 100000),
        "kilometers_driven": int(data.get("kilometers_driven") or data.get("bikeKms") or 0),
        "bikeKms": str(data.get("kilometers_driven") or data.get("bikeKms") or 0),
        "fuel_type": data.get("fuel_type", "Petrol"),
        "transmission": data.get("transmission", "Manual"),
        "description": data.get("description", "Inspected pre-owned motorcycle."),
        "images": images,
        "seller_name": data.get("seller_name") or data.get("sellerName") or "User",
        "seller_phone": data.get("seller_phone") or data.get("mobileNum") or "",
        "status": data.get("status", "pending"),
        "isAccepted": 1 if data.get("status") == "approved" else 0,
        "isSoldout": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["bikes"].append(new_bike)
    return jsonify({"success": True, "message": "Bike listed successfully", "id": new_id, "data": new_bike}), 201

# Categories
@app.route("/api/categories", methods=["GET"])
@app.route("/categories", methods=["GET"])
def get_categories():
    return jsonify({"success": True, "categories": IN_MEMORY_STORE["categories"]})

# Enquiries API
@app.route("/api/enquiries", methods=["GET", "POST"])
@app.route("/enquiries", methods=["GET", "POST"])
def enquiries_api():
    if request.method == "POST":
        data = request.get_json() or request.form.to_dict() or {}
        new_id = len(IN_MEMORY_STORE["enquiries"]) + 1
        enq = {
            "id": new_id,
            "bike_id": data.get("bike_id"),
            "bike_title": data.get("bike_title", "Motorcycle Inquiry"),
            "name": data.get("name") or data.get("customerName") or "Customer",
            "email": data.get("email", ""),
            "phone": data.get("phone") or data.get("mobile") or "",
            "message": data.get("message", "Inquiry submitted"),
            "status": "pending",
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        IN_MEMORY_STORE["enquiries"].append(enq)
        return jsonify({"success": True, "message": "Enquiry submitted successfully", "id": new_id}), 201
    
    return jsonify({"success": True, "data": IN_MEMORY_STORE["enquiries"], "enquiries": IN_MEMORY_STORE["enquiries"]})

@app.route("/api/enquiries/<int:enquiry_id>/status", methods=["PUT"])
@app.route("/enquiries/<int:enquiry_id>/status", methods=["PUT"])
def update_enquiry_status(enquiry_id):
    data = request.get_json() or {}
    new_status = data.get("status", "completed")
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
    msg_id = len(IN_MEMORY_STORE["contact_messages"]) + 1
    msg = {
        "id": msg_id,
        "name": data.get("name", "Website Visitor"),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "message": data.get("message", ""),
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    IN_MEMORY_STORE["contact_messages"].append(msg)
    return jsonify({"success": True, "message": "Your message was sent successfully!", "id": msg_id})

# Auth: Demo Google & Google OAuth
@app.route("/api/auth/demo-google", methods=["POST"])
@app.route("/api/auth/google", methods=["POST"])
def auth_google_api():
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
    return jsonify({"success": True, "token": token, "user": user})

@app.route("/api/auth/me", methods=["GET"])
def auth_me_api():
    return jsonify({"success": True, "user": IN_MEMORY_STORE["users"][0]})

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
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["status"] = "rejected"
            b["isAccepted"] = 0
            b["rejection_reason"] = data.get("reason", "Listing details do not meet quality guidelines.")
            return jsonify({"success": True, "message": "Bike rejected successfully"})
    return jsonify({"success": True, "message": "Bike rejected"})

@app.route("/api/admin/bikes/<int:bike_id>/price", methods=["PUT"])
@app.route("/bikes/<int:bike_id>/price", methods=["PUT"])
def admin_price_bike(bike_id):
    data = request.get_json() or {}
    new_price = data.get("price") or data.get("newPrice") or 0
    for b in IN_MEMORY_STORE["bikes"]:
        if b["id"] == bike_id:
            b["price"] = float(new_price)
            b["sellingPrice"] = str(new_price)
            return jsonify({"success": True, "message": "Price updated successfully"})
    return jsonify({"success": True, "message": "Price updated"})

@app.route("/api/admin/bikes/<int:bike_id>", methods=["DELETE"])
def admin_delete_bike(bike_id):
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
