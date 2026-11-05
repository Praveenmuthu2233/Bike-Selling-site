-- SMR Motors Fresh Superadmin Account
USE smr_motors;
INSERT INTO admins (username, email, password_hash, role, created_at)
VALUES ('admin', 'admin@smrmotors.com', 'pbkdf2:sha256:1000000$D3mzeRh6dkjvCOvn$cca34c362adb52f551f00e44e97ae081a1068268329e50f6e9a1296ebfc0cfbf', 'superadmin', NOW());
