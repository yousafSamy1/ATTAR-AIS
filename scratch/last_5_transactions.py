import sqlite3
import os

db_path = 'database/accounting.db'
if not os.path.exists(db_path):
    print(f'Database not found at {db_path}')
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = """
SELECT * FROM (
    SELECT date, 'Sale' as type, 
            'Invoice #' || id as description,
            total_amount as amount
    FROM sales_invoices
    UNION ALL
    SELECT date, 'Purchase' as type,
            'Purchase #' || id as description,
            total_amount as amount
    FROM purchase_invoices
    UNION ALL
    SELECT date, 'Expense' as type, 
            category || ' - ' || description as description, 
            amount
    FROM expenses
) ORDER BY date DESC, amount DESC LIMIT 5
"""

cur.execute(query)
rows = cur.fetchall()

print('| Date | Type | Description | Amount |')
print('|------|------|-------------|--------|')
for row in rows:
    print(f'| {row["date"]} | {row["type"]} | {row["description"]} | EGP {row["amount"]:,.2f} |')

conn.close()
