import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'accounting.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Checking accounts table:")
cursor.execute("SELECT * FROM accounts")
for row in cursor.fetchall():
    print(row)

conn.close()
