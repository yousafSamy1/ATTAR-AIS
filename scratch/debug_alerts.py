import sqlite3
import os

db_path = r"c:\me\collage\ATTAR (2)\ATTAR\database\accounting.db"
if not os.path.exists(db_path):
    print("DB not found")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("--- Credit Pending Invoices ---")
    cur.execute("SELECT id, date, due_date, status, payment_type FROM purchase_invoices WHERE payment_type='credit'")
    for row in cur.fetchall():
        print(row)
    
    print("\n--- Testing Alert Query ---")
    from datetime import datetime, timedelta
    today_str = datetime.now().strftime("%Y-%m-%d")
    near_due_str = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    print(f"Today: {today_str}, Near Due: {near_due_str}")
    
    cur.execute("""
        SELECT COUNT(*) FROM purchase_invoices 
        WHERE payment_type = 'credit' AND status = 'pending' 
        AND due_date IS NOT NULL AND due_date <= ?
    """, (near_due_str,))
    print(f"Count: {cur.fetchone()[0]}")
    conn.close()
