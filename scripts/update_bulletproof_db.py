import re

db_code = '''"""
SMR Motors - Central TiDB Cloud Database Connection Module
===========================================================
Reliable, TLS-secured, pooled database connection manager for TiDB Cloud.
- Automatic URI & environment variable parsing (TIDB_* and DB_* variants)
- Strict rejection of legacy third-party hosts (e.g. Clever Cloud)
- Resilient SSL/TLS certificate resolution (local certs & Linux system CAs)
- Connection pooling with stale connection detection (auto-ping & reconnect)
- Dynamic pool naming preventing collision errors
- Context manager for leak-free cursor and connection lifecycle
"""

import os
import sys
import time
import urllib.parse
from contextlib import contextmanager

# -----------------------------------------------------------------------------
# 1. ENVIRONMENT CONFIGURATION & RESOLUTION
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

def _clean_str(val):
    if not val:
        return ""
    return str(val).strip("'\\\" \\t\\r\\n")

def _is_invalid_legacy_host(h):
    if not h:
        return False
    h_lower = str(h).lower()
    return "clever-cloud.com" in h_lower or "bnyo89tbxsbc" in h_lower

# Standard SMR Motors TiDB Cloud Serverless Gateway
TIDB_DEFAULT_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"

# Check raw environment inputs
raw_tidb_host = _clean_str(os.getenv("TIDB_HOST"))
raw_db_host = _clean_str(os.getenv("DB_HOST"))
raw_mysql_host = _clean_str(os.getenv("MYSQL_HOST"))

raw_uri = _clean_str(
    os.getenv("TIDB_URI")
    or os.getenv("DATABASE_URL")
    or os.getenv("MYSQL_URL")
    or os.getenv("DB_URL")
)

config_source = "TIDB_DEFAULT_HOST"

# Parse connection URI if provided, strictly filtering out legacy Clever Cloud URIs
uri_host = ""
uri_port = None
uri_user = ""
uri_pass = ""
uri_db = ""
if raw_uri:
    if _is_invalid_legacy_host(raw_uri):
        print(f"[Database Config Warning] Detected and ignored legacy Clever Cloud URI in environment variable.")
    else:
        try:
            parsed = urllib.parse.urlparse(raw_uri)
            if parsed.hostname and not _is_invalid_legacy_host(parsed.hostname):
                uri_host = parsed.hostname
                uri_port = parsed.port
                uri_user = urllib.parse.unquote(parsed.username) if parsed.username else ""
                uri_pass = urllib.parse.unquote(parsed.password) if parsed.password else ""
                if parsed.path and len(parsed.path) > 1:
                    clean_path = parsed.path.lstrip("/")
                    if not _is_invalid_legacy_host(clean_path):
                        uri_db = clean_path
        except Exception as e:
            print("[Database Config Notice] Could not parse connection URI:", e)

# Host Resolution Hierarchy:
# 1. TIDB_HOST (explicit TiDB variable, highest priority)
# 2. DB_HOST (only if valid and NOT Clever Cloud)
# 3. URI host (only if valid and NOT Clever Cloud)
# 4. TIDB_DEFAULT_HOST (always guaranteed to target TiDB Cloud)
if raw_tidb_host and not _is_invalid_legacy_host(raw_tidb_host):
    DB_HOST = raw_tidb_host
    config_source = "TIDB_HOST"
elif raw_db_host and not _is_invalid_legacy_host(raw_db_host) and raw_db_host not in ("127.0.0.1", "localhost"):
    DB_HOST = raw_db_host
    config_source = "DB_HOST"
elif uri_host:
    DB_HOST = uri_host
    config_source = "DATABASE_URL"
else:
    DB_HOST = TIDB_DEFAULT_HOST
    config_source = "TIDB_DEFAULT_HOST"

if _is_invalid_legacy_host(raw_db_host):
    print(f"[Database Config Warning] Ignored legacy Clever Cloud DB_HOST '{raw_db_host}'. Using TiDB Cloud host '{DB_HOST}'.")

# Port Resolution
raw_tidb_port = _clean_str(os.getenv("TIDB_PORT"))
raw_db_port = _clean_str(os.getenv("DB_PORT"))
if raw_tidb_port and raw_tidb_port.isdigit():
    DB_PORT = int(raw_tidb_port)
elif raw_db_port and raw_db_port.isdigit():
    DB_PORT = int(raw_db_port)
elif uri_port:
    DB_PORT = int(uri_port)
else:
    DB_PORT = 4000

# User Resolution
raw_tidb_user = _clean_str(os.getenv("TIDB_USER"))
raw_db_user = _clean_str(os.getenv("DB_USER"))
if raw_tidb_user:
    DB_USER = raw_tidb_user
elif raw_db_user and not raw_db_user.startswith("uqq3"):
    DB_USER = raw_db_user
elif uri_user and not uri_user.startswith("uqq3"):
    DB_USER = uri_user
else:
    DB_USER = raw_db_user or "root"

# Password Resolution
raw_tidb_pass = _clean_str(os.getenv("TIDB_PASSWORD"))
raw_db_pass = _clean_str(os.getenv("DB_PASSWORD"))
if raw_tidb_pass:
    DB_PASSWORD = raw_tidb_pass
elif raw_db_pass:
    DB_PASSWORD = raw_db_pass
elif uri_pass:
    DB_PASSWORD = uri_pass
else:
    DB_PASSWORD = ""

# Database Name Resolution: strictly enforce smr_motors
raw_tidb_db = _clean_str(os.getenv("TIDB_DATABASE"))
raw_db_db = _clean_str(os.getenv("DB_NAME"))
if raw_tidb_db and raw_tidb_db.lower() not in ("sys", "bnyo89tbxsbcgu4v6ofp"):
    DB_NAME = raw_tidb_db
elif raw_db_db and raw_db_db.lower() not in ("sys", "bnyo89tbxsbcgu4v6ofp"):
    DB_NAME = raw_db_db
elif uri_db and uri_db.lower() not in ("sys", "bnyo89tbxsbcgu4v6ofp"):
    DB_NAME = uri_db
else:
    DB_NAME = "smr_motors"

# Security check: never target system database
if DB_NAME.lower() == "sys":
    raise ValueError("Security Violation: 'sys' database cannot be used for application data. Set DB_NAME=smr_motors.")

# -----------------------------------------------------------------------------
# 2. SSL / TLS CERTIFICATE CONFIGURATION
# -----------------------------------------------------------------------------
is_ssl_required = (
    "tidbcloud.com" in DB_HOST.lower()
    or os.getenv("DB_SSL", "true").lower() in ("true", "1", "yes")
    or os.getenv("TIDB_SSL", "true").lower() in ("true", "1", "yes")
)

ca_env = _clean_str(os.getenv("DB_SSL_CA") or os.getenv("TIDB_SSL_CA"))

candidate_ca_paths = []
if ca_env:
    candidate_ca_paths.extend([
        ca_env if os.path.isabs(ca_env) else os.path.join(BASE_DIR, ca_env),
        ca_env if os.path.isabs(ca_env) else os.path.join(PROJECT_ROOT, ca_env)
    ])

# Standard local paths in repository
candidate_ca_paths.extend([
    os.path.join(BASE_DIR, "certs", "isrgrootx1.pem"),
    os.path.join(PROJECT_ROOT, "certs", "isrgrootx1.pem"),
    os.path.join(PROJECT_ROOT, "my-node-app", "certs", "isrgrootx1.pem"),
    # Standard Linux / Render system CA bundles
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/cert.pem"
])

resolved_ssl_ca = None
for p in candidate_ca_paths:
    if p and os.path.isfile(p):
        resolved_ssl_ca = os.path.abspath(p)
        break

# Build base connection dictionary
db_config = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "connection_timeout": 15,
    "autocommit": False
}

if is_ssl_required:
    if resolved_ssl_ca:
        db_config["ssl_ca"] = resolved_ssl_ca
        db_config["ssl_verify_cert"] = True
        db_config["ssl_verify_identity"] = False
    else:
        db_config["ssl_disabled"] = False

# Diagnostic info without sensitive credentials
_masked_user = (DB_USER[:4] + "***") if len(DB_USER) > 4 else "***"
_masked_host = DB_HOST[:12] + "..." if len(DB_HOST) > 16 else DB_HOST

# -----------------------------------------------------------------------------
# 3. CONNECTION POOLING & RESILIENT GET_DB
# -----------------------------------------------------------------------------
_connection_pool = None
_last_pool_error = None
_last_connect_error = None

def _get_pool():
    global _connection_pool, _last_pool_error
    if _connection_pool is not None:
        return _connection_pool

    try:
        from mysql.connector import pooling
        pool_kwargs = dict(db_config)
        # Use dynamic pool name to avoid 'Pool already exists' errors on re-init
        pool_kwargs["pool_name"] = f"smr_pool_{int(time.time())}"
        try:
            pool_size = max(3, min(20, int(os.getenv("DB_CONNECTION_LIMIT", 10))))
        except (ValueError, TypeError):
            pool_size = 10
        pool_kwargs["pool_size"] = pool_size
        pool_kwargs["pool_reset_session"] = True
        _connection_pool = pooling.MySQLConnectionPool(**pool_kwargs)
        return _connection_pool
    except Exception as e:
        _last_pool_error = str(e)
        return None

def get_db():
    """
    Returns an active, ping-verified MySQL connection to TiDB Cloud.
    Prioritizes connection pooling; falls back to direct connection.
    Automatically detects stale sockets and reconnects.
    """
    global _connection_pool, _last_connect_error
    conn = None

    # Attempt 1: Get from pool with auto-ping
    pool = _get_pool()
    if pool:
        try:
            conn = pool.get_connection()
            if conn:
                try:
                    conn.ping(reconnect=True, attempts=2, delay=1)
                    return conn
                except Exception:
                    try: conn.close()
                    except Exception: pass
                    conn = None
        except Exception as pe:
            _last_connect_error = f"Pool get failed: {pe}"
            conn = None

    # Attempt 2: Direct connection with ping verification
    try:
        import mysql.connector
        conn = mysql.connector.connect(**db_config)
        if conn:
            conn.ping(reconnect=True, attempts=3, delay=1)
            return conn
    except Exception as de:
        err_msg = str(de)
        if DB_PASSWORD and DB_PASSWORD in err_msg:
            err_msg = err_msg.replace(DB_PASSWORD, "[PROTECTED]")
        _last_connect_error = err_msg
        print(f"[Database Connection Error] Could not connect to TiDB Cloud ({_masked_host}:{DB_PORT}): {err_msg}")
        return None

    return None

@contextmanager
def get_db_cursor(commit=False, dictionary=True):
    """
    Context manager that yields (conn, cursor).
    Automatically commits if commit=True and no exception occurs.
    Rolls back on exception and safely releases connection back to pool.
    """
    conn = get_db()
    if not conn:
        raise ConnectionError(f"Database connection unavailable ({_last_connect_error or 'Check TiDB Cloud credentials'})")
    cursor = None
    try:
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
        if commit:
            conn.commit()
    except Exception:
        if conn:
            try: conn.rollback()
            except Exception: pass
        raise
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if conn:
            try: conn.close()
            except Exception: pass

def get_db_diagnostics():
    """Returns safe diagnostic information for the /api/config and /api/health endpoints."""
    conn = get_db()
    is_connected = bool(conn)
    server_version = None
    if conn:
        try:
            server_version = conn.get_server_info()
            conn.close()
        except Exception:
            pass

    return {
        "status": "connected" if is_connected else "offline",
        "target_host": _masked_host,
        "target_port": DB_PORT,
        "target_database": DB_NAME,
        "target_user": _masked_user,
        "ssl_active": is_ssl_required,
        "ca_file_used": os.path.basename(resolved_ssl_ca) if resolved_ssl_ca else "builtin_tls",
        "server_version": server_version,
        "config_source": config_source,
        "last_error": _last_connect_error if not is_connected else None
    }
'''

with open("my-node-app/db.py", "w", encoding="utf-8") as f:
    f.write(db_code)

with open("db.py", "w", encoding="utf-8") as f:
    f.write(db_code)

print("Updated my-node-app/db.py and db.py successfully.")
