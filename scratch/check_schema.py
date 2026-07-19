
import sqlite3
conn = sqlite3.connect('database/attar.db')
cur = conn.cursor()
for table in ['recipes', 'recipe_ingredients', 'products']:
    cur.execute(f"PRAGMA table_info({table})")
    print(f"Table: {table}")
    for col in cur.fetchall():
        print(col)
conn.close()
