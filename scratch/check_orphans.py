from database.db_config import DatabaseConnection
import json

def check_orphans():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT je.reference_no 
            FROM journal_entries je 
            WHERE je.reference_no LIKE 'PUR-%' 
            AND NOT EXISTS (
                SELECT 1 FROM purchase_invoices pi 
                WHERE CAST(pi.id AS TEXT) = SUBSTR(je.reference_no, 5)
            )
        """)
        rows = cursor.fetchall()
        print("Orphaned Purchases (No invoice found):")
        print(json.dumps([dict(r) for r in rows], indent=2))
        
        cursor.execute("""
            SELECT je.reference_no 
            FROM journal_entries je 
            WHERE je.reference_no LIKE 'SALE-%' 
            AND NOT EXISTS (
                SELECT 1 FROM sales_invoices si 
                WHERE CAST(si.id AS TEXT) = SUBSTR(je.reference_no, 6)
            )
        """)
        rows = cursor.fetchall()
        print("\nOrphaned Sales (No invoice found):")
        print(json.dumps([dict(r) for r in rows], indent=2))

if __name__ == "__main__":
    check_orphans()
