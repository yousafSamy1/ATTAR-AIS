from database.db_config import DatabaseConnection

def cleanup_ledger():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        # Delete entries where both debit and credit are 0 (useless noise)
        cursor.execute('DELETE FROM general_ledger WHERE debit = 0 AND credit = 0')
        cursor.execute('DELETE FROM journal_entry_items WHERE debit = 0 AND credit = 0')
        conn.commit()
        print("Useless 0-value ledger entries removed.")

if __name__ == "__main__":
    cleanup_ledger()
