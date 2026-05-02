import sqlite3
import os

def init_accounting_db():
    db_path = os.path.join(os.path.dirname(__file__), 'accounting.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create accounts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
        balance DECIMAL(15,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create journal entries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        reference_no TEXT UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create journal entry items table
    cursor.execute('''    CREATE TABLE IF NOT EXISTS journal_entry_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        journal_entry_id INTEGER,
        account_id INTEGER,
        description TEXT,
        debit DECIMAL(15,2) DEFAULT 0,
        credit DECIMAL(15,2) DEFAULT 0,
        FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id),
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )
    ''')
    
    # Create general ledger table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS general_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        journal_entry_id INTEGER,
        date DATE NOT NULL,
        description TEXT,
        debit DECIMAL(15,2) DEFAULT 0,
        credit DECIMAL(15,2) DEFAULT 0,
        balance DECIMAL(15,2) DEFAULT 0,
        FOREIGN KEY (account_id) REFERENCES accounts(id),
        FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id)
    )
    ''')
    
    # Insert default accounts
    default_accounts = [
        ('1000', 'Cash', 'asset'),
        ('1100', 'Accounts Receivable', 'asset'),
        ('1200', 'Inventory', 'asset'),
        ('2000', 'Accounts Payable', 'liability'),
        ('3000', 'Owner\'s Equity', 'equity'),
        ('4000', 'Sales Revenue', 'revenue'),
        ('5000', 'Cost of Goods Sold', 'expense'),
        ('6000', 'Operating Expenses', 'expense')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO accounts (code, name, type)
    VALUES (?, ?, ?)
    ''', default_accounts)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_accounting_db()
