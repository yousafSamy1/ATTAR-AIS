from database.db_config import DatabaseConnection
import json

def check_balances():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT code, name, type, balance FROM accounts")
        accounts = cursor.fetchall()
        print(json.dumps([dict(a) for a in accounts], indent=2))

if __name__ == "__main__":
    check_balances()
