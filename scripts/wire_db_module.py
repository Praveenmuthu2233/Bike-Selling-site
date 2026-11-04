import re

app_py_path = "my-node-app/app.py"

with open(app_py_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update sys.path near top of app.py
target_top = """app_dir = os.path.dirname(os.path.abspath(__file__))
local_env = os.path.join(app_dir, ".env")"""

replace_top = """app_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(app_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if root_dir not in sys.path:
    sys.path.insert(1, root_dir)

local_env = os.path.join(app_dir, ".env")"""

if target_top in content:
    content = content.replace(target_top, replace_top, 1)
    print("1. sys.path updated")
else:
    print("1. sys.path target NOT found")

# 2. Replace lines 158-204 DB config block with imports from db.py
target_db_block = """# -----------------------------------------------------------------------------
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
    print(f"[Database Config] TLS certificate verification active using CA: {os.path.basename(ssl_ca_path)}")"""

replace_db_block = """# -----------------------------------------------------------------------------
# TIDB CLOUD DATABASE CONNECTION (Centralized db module)
# -----------------------------------------------------------------------------
try:
    from db import (
        get_db,
        get_db_cursor,
        get_db_diagnostics,
        db_config as dbconfig,
        DB_HOST,
        DB_PORT,
        DB_USER,
        DB_PASSWORD,
        DB_NAME,
        resolved_ssl_ca as ssl_ca_path,
        is_ssl_required as is_ssl
    )
except ImportError:
    from .db import (
        get_db,
        get_db_cursor,
        get_db_diagnostics,
        db_config as dbconfig,
        DB_HOST,
        DB_PORT,
        DB_USER,
        DB_PASSWORD,
        DB_NAME,
        resolved_ssl_ca as ssl_ca_path,
        is_ssl_required as is_ssl
    )"""

if target_db_block in content:
    content = content.replace(target_db_block, replace_db_block, 1)
    print("2. Centralized db import replaced")
else:
    print("2. DB config target NOT found")

# 3. Replace old get_db definition
target_get_db = """_tidb_pool = None

def get_db():
    \"\"\"
    Returns an active TLS-encrypted MySQL connection to TiDB Cloud using connection pooling.
    Handles connection errors gracefully without leaking credentials.
    \"\"\"
    global _tidb_pool
    try:
        import mysql.connector
        from mysql.connector import pooling
        if _tidb_pool is None:
            pool_cfg = dict(dbconfig)
            pool_cfg["pool_name"] = "smr_tidb_pool"
            pool_cfg["pool_size"] = 10
            pool_cfg["pool_reset_session"] = True
            _tidb_pool = pooling.MySQLConnectionPool(**pool_cfg)
        conn = _tidb_pool.get_connection()
        if conn and conn.is_connected():
            return conn
    except Exception as pool_err:
        # If pool is exhausted or closed, reset pool reference
        _tidb_pool = None

    # Direct connection fallback with ping verification
    try:
        import mysql.connector
        conn = mysql.connector.connect(**dbconfig)
        return conn
    except Exception as e:
        err_msg = str(e)
        if DB_PASSWORD and DB_PASSWORD in err_msg:
            err_msg = err_msg.replace(DB_PASSWORD, "[PROTECTED]")
        print("[Database Connection Error]:", err_msg)
        return None"""

replace_get_db = """# Note: get_db() is imported from the central db.py module with resilient pooling,
# auto-reconnect ping, dynamic pool naming, direct fallback, and TLS configuration."""

if target_get_db in content:
    content = content.replace(target_get_db, replace_get_db, 1)
    print("3. Old get_db definition replaced")
else:
    print("3. Old get_db target NOT found")

# 4. Update public_config_api and add /api/health
target_config_api = """    conn = get_db()
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
    })"""

replace_config_api = """    diag = get_db_diagnostics()
    tidb_status = diag.get("status", "offline")

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
        "database": {
            "status": tidb_status,
            "targetHost": diag.get("target_host"),
            "targetPort": diag.get("target_port"),
            "targetDatabase": diag.get("target_database"),
            "sslActive": diag.get("ssl_active"),
            "caUsed": diag.get("ca_file_used")
        },
        "endpoints": {
            "authGoogle": "/api/auth/google",
            "authDemo": "/api/auth/demo-google",
            "authMe": "/api/auth/me",
            "authLogout": "/api/auth/logout",
            "health": "/api/health"
        }
    })

@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check_api():
    \"\"\"
    Public health check endpoint reporting TiDB Cloud database connectivity status.
    Returns 200 OK when connected, 503 Service Unavailable when TiDB Cloud is disconnected.
    \"\"\"
    diag = get_db_diagnostics()
    is_healthy = (diag.get("status") == "connected")
    status_code = 200 if is_healthy else 503
    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "service": "smr-motors-backend",
        "database": diag
    }), status_code"""

if target_config_api in content:
    content = content.replace(target_config_api, replace_config_api, 1)
    print("4. Config API and Health API updated")
else:
    print("4. Config API target NOT found")

# 5. Add report route decorators and format fallback to admin_reports_export_api
target_reports = """@app.route("/api/admin/reports/export", methods=["GET", "POST"])
def admin_reports_export_api():
    \"\"\"
    Unified PDF, Excel, and CSV download endpoint with Date, Status, Brand, and Keyword filters.
    Strictly forbids financial reports for Staff Admins (HTTP 403).
    \"\"\"
    admin, err = resolve_export_admin()
    if not admin:
        return jsonify({"success": False, "message": err or "Authentication required"}), 401 if "Missing" in (err or "") else 403

    is_superadmin = (admin.get("role") == "superadmin")
    report_type = (request.args.get("type") or "listings").lower().strip()
    export_format = (request.args.get("format") or "pdf").lower().strip()"""

replace_reports = """@app.route("/api/admin/reports/export", methods=["GET", "POST"])
@app.route("/api/admin/reports", methods=["GET"])
@app.route("/api/admin/reports/bikes", methods=["GET"])
@app.route("/api/admin/reports/bikes.pdf", methods=["GET"])
@app.route("/api/admin/reports/bikes.xlsx", methods=["GET"])
def admin_reports_export_api():
    \"\"\"
    Unified PDF, Excel, and CSV download endpoint with Date, Status, Brand, and Keyword filters.
    Strictly forbids financial reports for Staff Admins (HTTP 403).
    \"\"\"
    admin, err = resolve_export_admin()
    if not admin:
        return jsonify({"success": False, "message": err or "Authentication required"}), 401 if "Missing" in (err or "") else 403

    is_superadmin = (admin.get("role") == "superadmin")
    path_lower = request.path.lower()
    report_type = (request.args.get("type") or ("bikes" if "bikes" in path_lower else "listings")).lower().strip()
    export_format = request.args.get("format")
    if not export_format:
        if path_lower.endswith(".pdf"):
            export_format = "pdf"
        elif path_lower.endswith(".xlsx") or path_lower.endswith(".excel"):
            export_format = "xlsx"
        else:
            export_format = "pdf"
    export_format = export_format.lower().strip()"""

if target_reports in content:
    content = content.replace(target_reports, replace_reports, 1)
    print("5. Reports endpoints updated")
else:
    print("5. Reports target NOT found")

with open(app_py_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Wiring completed successfully.")
