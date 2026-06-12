"""
Run a quick diagnostic against the application's DB layer.
Usage:
    python scripts/test_db_connection.py

It will import `db.get_db_info()` and print JSON diagnostics.
"""
import json
import sys
import os

# Ensure the project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from db import get_db_info
except Exception as e:
    print("Error: could not import db module:", e)
    sys.exit(2)

info = get_db_info()
print(json.dumps(info, indent=2))
