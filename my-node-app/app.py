import os
import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import bcrypt
import jwt

load_dotenv()

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)


JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

CORS(app, resources={r"*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization"])


UPLOAD_DIR = os.path.join("/tmp", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# @app.route("/uploads/<path:filename>")
# def uploads(filename):
#     return send_from_directory(UPLOAD_DIR, filename)

# dbconfig = {
#     "host": os.getenv("DB_HOST"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "database": os.getenv("DB_NAME"),
# }

def get_db():
    return mysql.connector.connect(**dbconfig)


def initialize_database():
    queries = [
        """
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
          isAccepted BOOLEAN DEFAULT FALSE,
          isSoldout BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS enquiries (
          id INT AUTO_INCREMENT PRIMARY KEY,
          listingId INT,
          listingTitle VARCHAR(255),
          customerName VARCHAR(255),
          mobile VARCHAR(20),
          email VARCHAR(255),
          location VARCHAR(255),
          timestamp VARCHAR(50),
          status VARCHAR(50) DEFAULT 'Not updated',
          message TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS soldOutBike (
          id INT AUTO_INCREMENT PRIMARY KEY,
          originalBikeId INT,
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
          soldOutDate DATETIME DEFAULT NOW(),
          image VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS signUpList (
          id INT AUTO_INCREMENT PRIMARY KEY,
          firstName VARCHAR(50),
          lastName VARCHAR(50),
          mobileNumber VARCHAR(10) NOT NULL UNIQUE,
          email VARCHAR(100),
          signUpPassword VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS gallery_uploads (
          id INT AUTO_INCREMENT PRIMARY KEY,
          fileName VARCHAR(255),
          filePath VARCHAR(255),
          uploadedAt DATETIME DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS attachments_uploads (
          id INT AUTO_INCREMENT PRIMARY KEY,
          fileName VARCHAR(255),
          filePath VARCHAR(255),
          uploadedAt DATETIME DEFAULT NOW()
        )
        """
    ]
    conn = get_db()
    cursor = conn.cursor()
    for q in queries:
        cursor.execute(q)
    conn.commit()
    cursor.close()
    conn.close()
    

adminAccounts = {
    "mani":    {"password": "mani@22",    "name": "Mani",    "role": "limited"},
    "murugan": {"password": "murugan@22", "name": "Murugan", "role": "main"},
    "raja":    {"password": "raja@22",    "name": "Raja",    "role": "main"},
}

roles = {
    "main": {
        "routeAccess": True,
        "canDelete": True,
        "canUpdate": True,
        "hideFields": []
    },
    "limited": {
        "routeAccess": True,
        "canDelete": False,
        "canUpdate": False,
        "hideFields": ["sellingPrice"]
    }
}

def apply_data_restriction(data, fields):
    new_list = []
    for row in data:
        item = dict(row)
        for f in fields:
            item.pop(f, None)
        new_list.append(item)
    return new_list


from functools import wraps
from flask import g

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"message": "Missing admin token"}), 401
        parts = header.split()
        if len(parts) != 2:
            return jsonify({"message": "Missing admin token"}), 401
        token = parts[1]
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            return jsonify({"message": "Invalid admin token"}), 401
        g.admin = decoded
        return f(*args, **kwargs)
    return wrapper

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not header:
            return jsonify({"message": "Missing token"}), 401
        parts = header.split()
        if len(parts) != 2:
            return jsonify({"message": "Missing token"}), 401
        token = parts[1]
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            return jsonify({"message": "Invalid token"}), 401
        g.user = decoded
        return f(*args, **kwargs)
    return wrapper


@app.post("/adminLogin")
def admin_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    admin = adminAccounts.get(username)
    if not admin or admin["password"] != password:
        return jsonify({"success": False, "message": "Invalid Credentials"})

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
        "admin": {
            "name": admin["name"],
            "role": admin["role"]
        }
    })

@app.get("/adminProfile")
@admin_required
def admin_profile():
    return jsonify({
        "success": True,
        "admin": g.admin
    })

@app.post("/addUser")
def add_user():
    data = request.get_json()
    firstName = data.get("firstName")
    lastName = data.get("lastName")
    mobileNumber = data.get("mobileNumber")
    email = data.get("email")
    signUpPassword = data.get("signUpPassword")

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM signUpList WHERE mobileNumber = %s",
        (mobileNumber,)
    )
    existing = cursor.fetchall()
    if existing:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Mobile number already registered!"})

    hashed = bcrypt.hashpw(signUpPassword.encode("utf-8"), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO signUpList (firstName, lastName, mobileNumber, email, signUpPassword) "
            "VALUES (%s, %s, %s, %s, %s)",
            (firstName, lastName, mobileNumber, email, hashed.decode("utf-8"))
        )
        conn.commit()
    except Exception:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Registration failed"}), 500

    cursor.close()
    conn.close()
    return jsonify({"success": True, "message": "User registered successfully"})

@app.post("/login")
def login():
    data = request.get_json()
    mobileNumber = data.get("mobileNumber")
    signUpPassword = data.get("signUpPassword")

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM signUpList WHERE mobileNumber = %s",
        (mobileNumber,)
    )
    results = cursor.fetchall()
    if not results:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Mobile number not found"})

    user = results[0]
    if not bcrypt.checkpw(signUpPassword.encode("utf-8"), user["signUpPassword"].encode("utf-8")):
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Wrong password"})

    payload = {
        "id": user["id"],
        "mobile": user["mobileNumber"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"]
        }
    })

@app.get("/profile")
@user_required
def profile():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT firstName, lastName, mobileNumber, email FROM signUpList WHERE id = %s",
        (g.user["id"],)
    )
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    if not res:
        return jsonify(None)
    return jsonify(res[0])

@app.get("/checkMobile/<mobile>")
def check_mobile(mobile):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM signUpList WHERE mobileNumber = %s",
        (mobile,)
    )
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"exists": len(res) > 0})


@app.post("/addBike")
def add_bike():
    data = request.get_json()
    bikeData = {
        **data,
        "isAccepted": 1 if data.get("isAccepted") else 0,
        "isSoldout": 1 if data.get("isSoldout") else 0
    }

    conn = get_db()
    cursor = conn.cursor()
    placeholders = ", ".join(f"{k}=%s" for k in bikeData.keys())
    sql = f"INSERT INTO bikesforsale SET {placeholders}"
    cursor.execute(sql, tuple(bikeData.values()))
    conn.commit()
    bike_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({"message": "Bike added successfully", "id": bike_id})

@app.post("/userAddBike")
def user_add_bike():
    data = request.get_json()
    fields = [
        "listingTitle", "vehicleNumber", "sellerName", "mobileNum",
        "bikeCondition", "bikeType", "makedFrom", "bikeModel",
        "bikeKms", "bikePrice", "sellingPrice", "bikeOwner",
        "bikeBuyingYear", "bikeColor", "bikeEngineCC", "driveType",
        "insurance", "horsepower", "bikeLocation", "description"
    ]
    bikeData = {f: data.get(f) for f in fields}
    bikeData["isAccepted"] = 1 if data.get("isAccepted") else 0
    bikeData["isSoldout"] = 1 if data.get("isSoldout") else 0

    conn = get_db()
    cursor = conn.cursor()
    placeholders = ", ".join(f"{k}=%s" for k in bikeData.keys())
    sql = f"INSERT INTO bikesforsale SET {placeholders}"
    cursor.execute(sql, tuple(bikeData.values()))
    conn.commit()
    bike_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Bike Added Successfully", "id": bike_id})

@app.get("/bikes")
def get_bikes():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bikesforsale")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(res)

@app.get("/bikes/<int:bike_id>")
def get_bike(bike_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bikesforsale WHERE id = %s", (bike_id,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(res[0] if res else None)

@app.put("/bikes/<int:bike_id>/accept")
def accept_bike(bike_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bikesforsale SET isAccepted = 1 WHERE id = %s", (bike_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.put("/bikes/<int:bike_id>/reject")
def reject_bike(bike_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bikesforsale SET isAccepted = 0 WHERE id = %s", (bike_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.put("/bikes/<int:bike_id>/price")
def update_bike_price(bike_id):
    data = request.get_json()
    newPrice = data.get("newPrice")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bikesforsale SET sellingPrice = %s WHERE id = %s",
        (newPrice, bike_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.put("/bikes/<int:bike_id>/soldout")
def move_to_soldout(bike_id):
    conn = get_db()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO soldOutBike (
      originalBikeId,
      listingTitle, vehicleNumber, sellerName, mobileNum, bikeCondition,
      bikeType, makedFrom, bikeModel, bikeKms, bikePrice, sellingPrice, bikeOwner,
      bikeBuyingYear, bikeColor, bikeEngineCC, driveType, insurance, horsepower,
      bikeLocation, description, soldOutDate, image
    )
    SELECT 
      id,
      listingTitle, vehicleNumber, sellerName, mobileNum, bikeCondition,
      bikeType, makedFrom, bikeModel, bikeKms, bikePrice, sellingPrice, bikeOwner,
      bikeBuyingYear, bikeColor, bikeEngineCC, driveType, insurance, horsepower,
      bikeLocation, description, NOW(), NULL
    FROM bikesforsale WHERE id = %s
    """
    cursor.execute(insert_query, (bike_id,))
    cursor.execute("DELETE FROM bikesforsale WHERE id = %s", (bike_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Bike moved to Sold Out list successfully"})


from werkzeug.utils import secure_filename

@app.post("/upload/gallery")
def upload_gallery():
    files = request.files.getlist("attachments")
    if not files:
        return jsonify({"message": "No files uploaded"}), 400

    conn = get_db()
    cursor = conn.cursor()
    file_values = []
    for f in files:
        filename = secure_filename(f.filename)
        saved_name = f"{int(datetime.datetime.utcnow().timestamp() * 1000)}-{filename}"
        path = os.path.join(UPLOAD_DIR, saved_name)
        f.save(path)
        file_values.append((saved_name, path))

    cursor.executemany(
        "INSERT INTO gallery_uploads (fileName, filePath) VALUES (%s, %s)",
        file_values
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Gallery uploaded successfully", "files": file_values})

@app.post("/upload/attachments")
def upload_attachments():
    files = request.files.getlist("attachments")
    if not files:
        return jsonify({"message": "No files uploaded"}), 400

    conn = get_db()
    cursor = conn.cursor()
    file_values = []
    for f in files:
        filename = secure_filename(f.filename)
        saved_name = f"{int(datetime.datetime.utcnow().timestamp() * 1000)}-{filename}"
        path = os.path.join(UPLOAD_DIR, saved_name)
        f.save(path)
        file_values.append((saved_name, path))

    cursor.executemany(
        "INSERT INTO attachments_uploads (fileName, filePath) VALUES (%s, %s)",
        file_values
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Attachments uploaded successfully", "files": file_values})

@app.get("/gallery")
def get_gallery():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM gallery_uploads ORDER BY uploadedAt DESC")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(res)

@app.get("/attachments")
def get_attachments():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attachments_uploads ORDER BY uploadedAt DESC")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(res)


@app.post("/enquiries")
def add_enquiry():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    placeholders = ", ".join(f"{k}=%s" for k in data.keys())
    sql = f"INSERT INTO enquiries SET {placeholders}"
    cursor.execute(sql, tuple(data.values()))
    conn.commit()
    enquiry_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Enquiry submitted successfully", "id": enquiry_id})

@app.get("/enquiries")
def get_enquiries():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM enquiries")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(res)

@app.delete("/deleteEnquiry/<int:enquiry_id>")
def delete_enquiry(enquiry_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enquiries WHERE id = %s", (enquiry_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Enquiry deleted successfully"})

@app.put("/enquiries/<int:enquiry_id>/status")
def update_enquiry_status(enquiry_id):
    data = request.get_json()
    status = data.get("status")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE enquiries SET status = %s WHERE id = %s",
        (status, enquiry_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Status updated successfully"})

@app.put("/enquiries/<int:enquiry_id>/message")
def update_enquiry_message(enquiry_id):
    data = request.get_json()
    msg = data.get("message")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE enquiries SET message = %s WHERE id = %s",
        (msg, enquiry_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Message updated successfully"})

@app.get("/enquiries/<mobile>")
def get_enquiries_by_mobile(mobile):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM enquiries WHERE mobile = %s",
        (mobile,)
    )
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(res)

@app.get("/soldout")
@admin_required
def get_soldout():
    username = g.admin.get("username")
    if not username:
        return jsonify({"message": "Unauthorized admin"}), 403

    username_lower = username.lower()
    admin = adminAccounts.get(username_lower)
    if not admin:
        return jsonify({"message": "Unauthorized admin"}), 403

    roleRule = roles.get(admin["role"])
    if not roleRule or not roleRule["routeAccess"]:
        return jsonify({"message": "Route access denied"}), 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM soldOutBike")
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    finalData = results
    if roleRule["hideFields"]:
        finalData = apply_data_restriction(results, roleRule["hideFields"])

    return jsonify({
        "adminUsername": username_lower,
        "role": admin["role"],
        "permissions": {
            "canUpdate": roleRule["canUpdate"],
            "canDelete": roleRule["canDelete"]
        },
        "data": finalData
    })

from flask import render_template

# @app.before_first_request
# def setup_db():
#     initialize_database()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/bike-details")
def bike_details():
    return render_template("bike-details.html")

if __name__ == "__main__":
    initialize_database()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
