import os
import sys

# Inject legacy Clever Cloud variables to simulate Render's environment
os.environ["DATABASE_URL"] = "mysql://uqq3xyz:secretpass@bnyo89tbxsbcgu4v6ofp-mysql.services.clever-cloud.com/bnyo89tbxsbcgu4v6ofp"
os.environ["DB_HOST"] = "bnyo89tbxsbcgu4v6ofp-mysql.services.clever-cloud.com"
os.environ["DB_NAME"] = "bnyo89tbxsbcgu4v6ofp"
os.environ["DB_PORT"] = "4000"

sys.path.insert(0, 'my-node-app')
# Force reload db module
if 'db' in sys.modules:
    del sys.modules['db']

import db

print("Simulated Render Environment with legacy Clever Cloud variables:")
print("  db.DB_HOST:", db.DB_HOST)
print("  db.DB_PORT:", db.DB_PORT)
print("  db.DB_NAME:", db.DB_NAME)
print("  db.config_source:", db.config_source)

assert "clever-cloud" not in db.DB_HOST, "Clever Cloud host must be rejected!"
assert db.DB_NAME == "smr_motors", "Database must be smr_motors!"
assert db.DB_HOST == "gateway01.ap-southeast-1.prod.aws.tidbcloud.com", "Must default to TiDB Cloud!"

print("\nAll legacy Clever Cloud rejection assertions PASSED!")
