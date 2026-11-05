"""
SMR Motors - Superadmin Account Creation Script & SQL Generator
Generates a secure password hash (werkzeug PBKDF2:SHA256) and creates or outputs
the SQL insert statement for the fresh Superadmin account in TiDB Cloud.
"""
import sys
from werkzeug.security import generate_password_hash

def main():
    print("=" * 60)
    print("  SMR Motors - Fresh Superadmin Account Generator")
    print("=" * 60)
    
    username = input("Enter Superadmin Username (default: admin): ").strip() or "admin"
    email = input("Enter Superadmin Email (default: admin@smrmotors.com): ").strip() or "admin@smrmotors.com"
    password = input("Enter Superadmin Password (default: Admin@Smr2026!): ").strip() or "Admin@Smr2026!"
    role = "superadmin"
    
    # Generate secure hash
    pw_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    print("\nAccount Details:")
    print(f"  Username     : {username}")
    print(f"  Email        : {email}")
    print(f"  Password     : {password}")
    print(f"  Role         : {role}")
    print(f"  Password Hash: {pw_hash}")
    
    sql = f"""-- Insert Fresh Superadmin Account
USE smr_motors;
INSERT INTO admins (username, email, password_hash, role, created_at)
VALUES ('{username}', '{email}', '{pw_hash}', '{role}', NOW());
"""
    print("\n" + "=" * 60)
    print("  SQL Statement (Run in TiDB Cloud SQL Editor):")
    print("=" * 60)
    print(sql)
    
    # Save SQL to file
    with open("sql/insert_fresh_superadmin.sql", "w", encoding="utf-8") as f:
        f.write(sql)
    print("Saved SQL statement to sql/insert_fresh_superadmin.sql\n")

if __name__ == "__main__":
    main()
