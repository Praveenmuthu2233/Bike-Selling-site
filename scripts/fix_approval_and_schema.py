import os

def apply_fixes():
    app_path = os.path.join("my-node-app", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update chat_conversations table definition in initialize_database()
    old_create_conv = """        CREATE TABLE IF NOT EXISTS `chat_conversations` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `user_id` INT NOT NULL,
          `subject` VARCHAR(255) NOT NULL DEFAULT 'General Support Inquiry',
          `bike_id` INT NULL,
          `status` VARCHAR(50) NOT NULL DEFAULT 'open',
          `assigned_admin_id` INT NULL,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"""

    new_create_conv = """        CREATE TABLE IF NOT EXISTS `chat_conversations` (
          `id` INT AUTO_INCREMENT PRIMARY KEY,
          `user_id` INT NOT NULL,
          `subject` VARCHAR(255) NOT NULL DEFAULT 'General Support Inquiry',
          `bike_id` INT NULL,
          `status` VARCHAR(50) NOT NULL DEFAULT 'open',
          `assigned_admin_id` INT NULL,
          `last_message_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
          `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"""

    if old_create_conv in content:
        content = content.replace(old_create_conv, new_create_conv, 1)
        print("Updated CREATE TABLE chat_conversations with last_message_at column")
    else:
        print("old_create_conv not matched")

    # 2. Add incremental schema migration in initialize_database()
    old_mig = """        # Incremental schema migrations
        try:
            cursor.execute("ALTER TABLE `enquiries` ADD COLUMN `user_id` INT NULL")
            conn.commit()
        except Exception:
            pass"""

    new_mig = """        # Incremental schema migrations
        try:
            cursor.execute("ALTER TABLE `enquiries` ADD COLUMN `user_id` INT NULL")
            conn.commit()
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE `chat_conversations` ADD COLUMN `last_message_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP")
            conn.commit()
            print("[Database Schema] Added last_message_at column to chat_conversations.")
        except Exception:
            pass"""

    if old_mig in content:
        content = content.replace(old_mig, new_mig, 1)
        print("Added incremental migration for chat_conversations.last_message_at")
    else:
        print("old_mig not matched")

    # 3. Update admin_approve_bike query at line 5228
    old_approve_update = """                    cursor.execute(\"\"\"
                        UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
                    \"\"\", (conv_id,))"""

    new_approve_update = """                    try:
                        cursor.execute(\"\"\"
                            UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
                        \"\"\", (conv_id,))
                    except Exception:
                        cursor.execute(\"\"\"
                            UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s
                        \"\"\", (conv_id,))"""

    if old_approve_update in content:
        content = content.replace(old_approve_update, new_approve_update, 1)
        print("Fixed UPDATE chat_conversations query in admin_approve_bike")
    else:
        print("old_approve_update not matched, checking with normalized whitespace")

    # 4. Update admin_verify_bike_document query at line 8244
    old_verify_update = """            cursor.execute(\"\"\"
                UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
            \"\"\", (conv_id,))"""

    new_verify_update = """            try:
                cursor.execute(\"\"\"
                    UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP, last_message_at = CURRENT_TIMESTAMP WHERE id = %s
                \"\"\", (conv_id,))
            except Exception:
                cursor.execute(\"\"\"
                    UPDATE chat_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s
                \"\"\", (conv_id,))"""

    if old_verify_update in content:
        content = content.replace(old_verify_update, new_verify_update, 1)
        print("Fixed UPDATE chat_conversations query in admin_verify_bike_document")
    else:
        print("old_verify_update not matched")

    # Write file
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("app.py updated successfully")

if __name__ == "__main__":
    apply_fixes()
