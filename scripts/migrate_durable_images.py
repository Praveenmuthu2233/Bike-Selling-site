import os
import sys
import mimetypes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import get_db

print("[Durable Image Migration] Starting TiDB image synchronization...")

conn = get_db()
if not conn:
    print("[ERROR] Cannot connect to TiDB Cloud!")
    sys.exit(1)

cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS `durable_images` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `filename` VARCHAR(255) NOT NULL UNIQUE,
  `mime_type` VARCHAR(100) NOT NULL DEFAULT 'image/jpeg',
  `file_size` INT NOT NULL DEFAULT 0,
  `image_data` LONGBLOB NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_di_filename` (`filename`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
""")
conn.commit()

# Find all upload dirs
upload_dirs = [
    os.path.join(APP_DIR, "public", "uploads"),
    os.path.join(BASE_DIR, "public", "uploads")
]

synced_count = 0
for udir in upload_dirs:
    if not os.path.exists(udir):
        continue
    for fname in os.listdir(udir):
        if fname.startswith(".") or fname.endswith(".gitkeep"):
            continue
        fpath = os.path.join(udir, fname)
        if not os.path.isfile(fpath):
            continue

        # Check if already in durable_images
        cur.execute("SELECT id FROM durable_images WHERE filename = %s", (fname,))
        if cur.fetchone():
            continue

        try:
            with open(fpath, "rb") as img_f:
                blob = img_f.read()
            mime, _ = mimetypes.guess_type(fname)
            mime = mime or "image/jpeg"
            fsize = len(blob)

            cur.execute("""
                INSERT INTO durable_images (filename, mime_type, file_size, image_data)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE file_size=VALUES(file_size), image_data=VALUES(image_data)
            """, (fname, mime, fsize, blob))
            conn.commit()
            synced_count += 1
            print(f"  + Synced {fname} ({fsize} bytes, {mime}) to TiDB Cloud")
        except Exception as e:
            print(f"  ! Error syncing {fname}: {e}")

cur.execute("SELECT COUNT(*) FROM durable_images")
total = cur.fetchone()[0]
print(f"[Durable Image Migration] Completed. Total durable images in TiDB Cloud: {total} (New: {synced_count})")

cur.close()
conn.close()
