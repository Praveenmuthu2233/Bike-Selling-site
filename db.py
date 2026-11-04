"""
SMR Motors - Central TiDB Cloud Database Connection Module
===========================================================
Reliable, TLS-secured, pooled database connection manager for TiDB Cloud.
- Automatic URI & environment variable parsing (DB_* and TIDB_* variants)
- Resilient SSL/TLS certificate resolution (local certs & Linux system CAs)
- Connection pooling with stale connection detection (auto-ping & reconnect)
- Graceful direct connection fallback on pool exhaustion
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

# Support full connection string / URI if provided (Render, Heroku, TiDB Cloud)
RAW_URI = (
    os.getenv("DATABASE_URL")
    or os.getenv("TIDB_URI")
    or os.getenv("MYSQL_URL")
    or os.getenv("DB_URL")
    or ""
).strip()

def _clean_str(val):
    if not val:
        return ""
    return str(val).strip("'\" \t\r\n")

# Defaults & Environment Variable Priority
DB_HOST = _clean_str(os.getenv("DB_HOST") or os.getenv("TIDB_HOST") or os.getenv("MYSQL_HOST"))
DB_PORT = int(_clean_str(os.getenv("DB_PORT") or os.getenv("TIDB_PORT") or os.getenv("MYSQL_PORT")) or 4000)
DB_USER = _clean_str(os.getenv("DB_USER") or os.getenv("TIDB_USER") or os.getenv("MYSQL_USER"))
DB_PASSWORD = _clean_str(os.getenv("DB_PASSWORD") or os.getenv("TIDB_PASSWORD") or os.getenv("MYSQL_PASSWORD"))
DB_NAME = _clean_str(os.getenv("DB_NAME") or os.getenv("TIDB_DATABASE") or os.getenv("MYSQL_DATABASE") or "smr_motors")

# Parse connection URI if individual host/user not explicitly set
if RAW_URI and (not DB_HOST or DB_HOST in ("127.0.0.1", "localhost")):
    try:
        # e.g. mysql://user:password@host:port/database
        parsed = urllib.parse.urlparse(RAW_URI)
        if parsed.hostname:
            DB_HOST = parsed.hostname
        if parsed.port:
            DB_PORT = int(parsed.port)
        if parsed.username:
            DB_USER = urllib.parse.unquote(parsed.username)
        if parsed.password:
            DB_PASSWORD = urllib.parse.unquote(parsed.password)
        if parsed.path and len(parsed.path) > 1:
            DB_NAME = parsed.path.lstrip("/")
    except Exception as e:
        print("[Database Config Notice] Could not parse DATABASE_URL:", e)

# Fallback protection against localhost in production environments
is_production = bool(
    os.getenv("RENDER")
    or os.getenv("DYNO")
    or os.getenv("VERCEL")
    or os.getenv("FLASK_ENV") == "production"
    or os.getenv("NODE_ENV") == "production"
)

# Standard SMR Motors TiDB Cloud Serverless Host
TIDB_DEFAULT_HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
if not DB_HOST:
    # If unconfigured, default to the production cluster hostname
    DB_HOST = TIDB_DEFAULT_HOST

# Security check: never target system database
if DB_NAME.lower() == "sys":
    raise ValueError("Security Violation: 'sys' database cannot be used for application data. Set DB_NAME=smr_motors.")

# -----------------------------------------------------------------------------
# 2. SSL / TLS CERTIFICATE CONFIGURATION
# -----------------------------------------------------------------------------
# TiDB Cloud requires TLS encryption
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
        # Do not force ssl_verify_identity to allow flexible cloud SAN certificates
        db_config["ssl_verify_identity"] = False
    else:
        # Fall back to TLS handshake without explicit CA file (supported by TiDB Serverless)
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
        # Use a dynamic pool name to avoid 'Pool already exists' errors on re-init
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
                    # Connection is dead; close and try direct
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
        "last_error": _last_connect_error if not is_connected else None
    }
