from database.db_config import DatabaseConnection
import json

def check_ledger():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM general_ledger WHERE description LIKE "%Purchase Invoice%"')
        rows = cursor.fetchall()
        print(json.dumps([dict(r) for r in rows], indent=2))

if __name__ == "__main__":
    check_ledger()
