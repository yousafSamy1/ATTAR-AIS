from database.db_config import DatabaseConnection
import json

def check_items():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM purchase_items WHERE invoice_id = 55')
        rows = cursor.fetchall()
        print(json.dumps([dict(r) for r in rows], indent=2))

if __name__ == "__main__":
    check_items()
