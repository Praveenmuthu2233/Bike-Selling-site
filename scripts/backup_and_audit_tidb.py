import os
import sys
import json
import datetime
from dotenv import dotenv_values

sys.stdout.reconfigure(encoding='utf-8')

vals = dotenv_values('my-node-app/.env')
host = vals.get('DB_HOST') or vals.get('TIDB_HOST') or "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
port = int(vals.get('DB_PORT') or vals.get('TIDB_PORT') or 4000)
user = vals.get('DB_USER') or vals.get('TIDB_USER') or "hH3EBvquLgqPWEo.root"
password = vals.get('DB_PASSWORD') or vals.get('TIDB_PASSWORD') or ""
database = vals.get('DB_NAME') or vals.get('TIDB_DATABASE') or "smr_motors"

print(f"TiDB Audit Script Initialized")
print(f"Target: {host}:{port}, Database: {database}, User: {user[:5]}***")

def test_connection():
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl_ca='certs/isrgrootx1.pem',
            ssl_verify_cert=True,
            ssl_verify_identity=False,
            connection_timeout=8
        )
        return conn, None
    except Exception as e:
        return None, str(e)

conn, err = test_connection()
if not conn:
    print(f"\n[Notice] Cannot connect to TiDB Cloud with current credentials: {err}")
    print("If you recently reset your TiDB Cloud password, please update TIDB_PASSWORD in my-node-app/.env")
    sys.exit(2)

print("\n[Connected successfully to TiDB Cloud smr_motors!]")

# Create backups directory
os.makedirs("backups", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"backups/backup_smr_motors_{timestamp}.sql"

cursor = conn.cursor(dictionary=True)
cursor.execute("SHOW TABLES")
tables = [list(r.values())[0] for r in cursor.fetchall()]
print(f"Found {len(tables)} tables: {', '.join(tables)}")

# 1. Generate full backup SQL
print(f"Generating full SQL backup to {backup_file}...")
with open(backup_file, "w", encoding="utf-8") as bf:
    bf.write(f"-- SMR Motors TiDB Cloud Database Backup\n-- Date: {datetime.datetime.now().isoformat()}\n-- Database: {database}\n\n")
    bf.write("SET FOREIGN_KEY_CHECKS=0;\n\n")

    for t in tables:
        # Get create table statement
        c2 = conn.cursor()
        c2.execute(f"SHOW CREATE TABLE `{t}`")
        create_sql = c2.fetchone()[1]
        bf.write(f"-- Table structure for `{t}`\n{create_sql};\n\n")
        c2.close()

        # Dump rows
        cursor.execute(f"SELECT * FROM `{t}`")
        rows = cursor.fetchall()
        if rows:
            cols = list(rows[0].keys())
            cols_str = ", ".join([f"`{c}`" for c in cols])
            bf.write(f"-- Dumping data for `{t}` ({len(rows)} rows)\n")
            for r in rows:
                vals_list = []
                for c in cols:
                    v = r[c]
                    if v is None:
                        vals_list.append("NULL")
                    elif isinstance(v, (int, float)):
                        vals_list.append(str(v))
                    else:
                        escaped = str(v).replace("\\", "\\\\").replace("'", "\\'")
                        vals_list.append(f"'{escaped}'")
                bf.write(f"INSERT INTO `{t}` ({cols_str}) VALUES ({', '.join(vals_list)});\n")
            bf.write("\n")
    bf.write("SET FOREIGN_KEY_CHECKS=1;\n")

print(f"Backup completed successfully ({os.path.getsize(backup_file):,} bytes)")

# 2. Audit records and identify dummy candidates
print("\nAuditing tables for dummy vs genuine records...")

audit_report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "database": database,
    "backup_file": backup_file,
    "tables_audited": {},
    "suspected_dummy": {
        "bikes": [],
        "enquiries": [],
        "users": [],
        "chat_conversations": [],
        "notifications": []
    },
    "confirmed_genuine": {
        "bikes": [],
        "enquiries": [],
        "users": [],
        "admins": []
    }
}

# Audit Bikes
cursor.execute("SELECT id, title, brand, model, price, vehicle_number, seller_name, seller_phone, status FROM bikes")
bikes = cursor.fetchall()
for b in bikes:
    title_lower = (b.get('title') or '').lower()
    seller_lower = (b.get('seller_name') or '').lower()
    phone = str(b.get('seller_phone') or '')
    reg = str(b.get('vehicle_number') or '')

    is_dummy = (
        any(k in title_lower for k in ['test', 'dummy', 'sample', 'asdf', 'qwerty', 'fake'])
        or any(k in seller_lower for k in ['test', 'dummy', 'sample', 'asdf'])
        or phone in ['0000000000', '1234567890', '9999999999', '1111111111', '']
        or reg in ['TN-XX-XXXX', 'TEST', '']
    )
    if is_dummy:
        audit_report["suspected_dummy"]["bikes"].append(b)
    else:
        audit_report["confirmed_genuine"]["bikes"].append(b)

# Audit Users
cursor.execute("SELECT id, name, email, role, created_at FROM users")
users = cursor.fetchall()
for u in users:
    email_lower = (u.get('email') or '').lower()
    name_lower = (u.get('name') or '').lower()
    is_dummy = (
        any(k in email_lower for k in ['test', 'example.com', 'demo', 'fake'])
        or any(k in name_lower for k in ['demo rider', 'test user'])
    )
    if is_dummy:
        audit_report["suspected_dummy"]["users"].append(u)
    else:
        audit_report["confirmed_genuine"]["users"].append(u)

# Audit Admins (Protect production admins)
cursor.execute("SELECT id, username, full_name, email, role FROM admins")
admins = cursor.fetchall()
audit_report["confirmed_genuine"]["admins"] = admins

# Audit Enquiries
cursor.execute("SELECT id, bike_id, name, email, phone, message, status FROM enquiries")
enquiries = cursor.fetchall()
for e in enquiries:
    msg_lower = (e.get('message') or '').lower()
    name_lower = (e.get('name') or '').lower()
    phone = str(e.get('phone') or '')
    is_dummy = (
        any(k in msg_lower for k in ['test', 'testing', 'asdf', 'dummy', 'sample'])
        or any(k in name_lower for k in ['test', 'dummy'])
        or phone in ['0000000000', '1234567890']
    )
    if is_dummy:
        audit_report["suspected_dummy"]["enquiries"].append(e)
    else:
        audit_report["confirmed_genuine"]["enquiries"].append(e)

cursor.close()
conn.close()

with open("backups/audit_report.json", "w", encoding="utf-8") as jf:
    json.dump(audit_report, jf, indent=2, default=str)

print("\nAudit summary:")
print(f"  - Genuine bikes: {len(audit_report['confirmed_genuine']['bikes'])}")
print(f"  - Suspected dummy bikes: {len(audit_report['suspected_dummy']['bikes'])}")
print(f"  - Genuine users: {len(audit_report['confirmed_genuine']['users'])}")
print(f"  - Suspected dummy users: {len(audit_report['suspected_dummy']['users'])}")
print(f"  - Preserved admin accounts: {len(audit_report['confirmed_genuine']['admins'])}")
print(f"  - Genuine enquiries: {len(audit_report['confirmed_genuine']['enquiries'])}")
print(f"  - Suspected dummy enquiries: {len(audit_report['suspected_dummy']['enquiries'])}")
print("Audit report written to backups/audit_report.json")
