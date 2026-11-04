import os
import sys

# Ensure my-node-app directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "my-node-app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Expose app object for Gunicorn WSGI runner (gunicorn app:app)
import importlib.util

_spec = importlib.util.spec_from_file_location("smr_backend_app", os.path.join(APP_DIR, "app.py"))
_main_module = importlib.util.module_from_spec(_spec)
sys.modules["smr_backend_app"] = _main_module
_spec.loader.exec_module(_main_module)

app = _main_module.app
initialize_database = getattr(_main_module, "initialize_database", None)
get_db = getattr(_main_module, "get_db", None)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
