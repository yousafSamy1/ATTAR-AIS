from database.db_config import DatabaseConnection
import json

def check_invoices():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, total_amount, payment_type FROM purchase_invoices WHERE total_amount = 0')
        rows = cursor.fetchall()
        print("Invoices with 0 total_amount:")
        print(json.dumps([dict(r) for r in rows], indent=2))
        
        cursor.execute('SELECT invoice_id, SUM(quantity * unit_price) as calc_total FROM purchase_items GROUP BY invoice_id')
        rows = cursor.fetchall()
        print("\nCalculated totals from items:")
        print(json.dumps([dict(r) for r in rows], indent=2))

if __name__ == "__main__":
    check_invoices()
