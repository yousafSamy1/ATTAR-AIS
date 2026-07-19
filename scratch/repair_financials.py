from database.db_config import DatabaseConnection
from modules.auto_accounting import AutoAccountingModule

def repair_accounting():
    auto = AutoAccountingModule()
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        # Find all purchase invoices where ledger entries are 0 but items have value
        cursor.execute("""
            SELECT pi.id, pi.total_amount, pi.supplier_id, pi.date, pi.payment_type,
                   (SELECT SUM(quantity * unit_price) FROM purchase_items WHERE invoice_id = pi.id) as calc_total
            FROM purchase_invoices pi
        """)
        invoices = cursor.fetchall()
        
        for inv in invoices:
            if inv['calc_total'] > 0:
                print(f"Repairing Invoice #{inv['id']} (Total: {inv['calc_total']})...")
                
                # Update total_amount in invoice table if it was 0
                if inv['total_amount'] == 0:
                    cursor.execute("UPDATE purchase_invoices SET total_amount = ?, paid_amount = ? WHERE id = ?", 
                                 (inv['calc_total'], inv['calc_total'] if inv['payment_type'] == 'cash' else 0, inv['id']))
                
                # Delete old 0-value ledger entries
                cursor.execute("DELETE FROM general_ledger WHERE description LIKE ? OR description LIKE ?", 
                             (f"Purchase Invoice #{inv['id']}", f"Purchase Invoice #{inv['id']} (%)"))
                cursor.execute("DELETE FROM journal_entry_items WHERE journal_entry_id IN (SELECT id FROM journal_entries WHERE reference_no = ?)", 
                             (f"PUR-{inv['id']}",))
                cursor.execute("DELETE FROM journal_entries WHERE reference_no = ?", (f"PUR-{inv['id']}",))
                
                # Re-create correct ledger entries
                auto.create_purchase_journal_entry(cursor, inv['id'], inv['supplier_id'], inv['calc_total'], inv['date'], inv['payment_type'])
        
        # Find all expenses where ledger entries are missing
        print("Checking for missing expense entries...")
        cursor.execute("""
            SELECT id, amount, category, date 
            FROM expenses 
            WHERE NOT EXISTS (
                SELECT 1 FROM journal_entries WHERE reference_no = 'EXP-' || expenses.id
            )
        """)
        missing_expenses = cursor.fetchall()
        for exp in missing_expenses:
            print(f"Repairing Expense #{exp['id']} ({exp['category']} - {exp['amount']})...")
            auto.create_expense_journal_entry(cursor, exp['id'], exp['amount'], exp['category'], exp['date'])

        # Reset account balances and re-calculate from general_ledger
        print("Re-calculating account balances...")
        cursor.execute("UPDATE accounts SET balance = 0")
        
        cursor.execute("SELECT account_id, debit, credit FROM general_ledger")
        entries = cursor.fetchall()
        for entry in entries:
            cursor.execute("SELECT type FROM accounts WHERE id = ?", (entry['account_id'],))
            acc_type = cursor.fetchone()['type']
            
            if acc_type in ('asset', 'expense'):
                change = entry['debit'] - entry['credit']
            else:
                change = entry['credit'] - entry['debit']
                
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (change, entry['account_id']))
            
        conn.commit()
        print("Financial Reports Repaired Successfully!")

if __name__ == "__main__":
    repair_accounting()
