from database.db_config import DatabaseConnection
import json

def check_inventory_ledger():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                je.reference_no,
                a.name as account_name,
                gl.debit,
                gl.credit,
                CASE
                    WHEN je.reference_no LIKE 'SALE%' THEN (
                        SELECT c.name FROM sales_invoices si JOIN customers c ON si.customer_id = c.id WHERE CAST(si.id AS TEXT) = SUBSTR(je.reference_no, 6) LIMIT 1
                    )
                    WHEN je.reference_no LIKE 'PUR%' THEN (
                        SELECT s.name FROM purchase_invoices pi JOIN suppliers s ON pi.supplier_id = s.id WHERE CAST(pi.id AS TEXT) = SUBSTR(je.reference_no, 5) LIMIT 1
                    )
                    ELSE NULL
                END as entity_name
            FROM general_ledger gl
            JOIN accounts a ON gl.account_id = a.id
            JOIN journal_entries je ON gl.journal_entry_id = je.id
            WHERE a.code = '1200'
        """)
        rows = cursor.fetchall()
        print(json.dumps([dict(r) for r in rows], indent=2))

if __name__ == "__main__":
    check_inventory_ledger()
