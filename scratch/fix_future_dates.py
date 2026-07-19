import sqlite3
import datetime

db_path = "database/accounting.db"

def fix_future_dates():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        today = datetime.date.today().strftime("%Y-%m-%d")
        print(f"Updating all future dates to today ({today})...")
        
        tables_with_date = [
            "journal_entries",
            "general_ledger",
            "expenses",
            "revenues",
            "sales_invoices",
            "purchase_invoices"
        ]
        
        for table in tables_with_date:
            cursor.execute(f"UPDATE {table} SET date = ? WHERE date > ?", (today, today))
            print(f"Updated {cursor.rowcount} rows in {table}.")

        conn.commit()
        print("Successfully fixed all future dates!")

    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_future_dates()
