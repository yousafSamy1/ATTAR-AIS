import sqlite3
import os

db_path = "database/attar_ais.db"
print("DB Path exists:", os.path.exists(db_path))

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
except Exception as e:
    print("Error:", e)
