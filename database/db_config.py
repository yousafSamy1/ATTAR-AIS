# Python Standard Libraries
import sqlite3      # SQLite database engine - Lightweight, serverless, self-contained database
from pathlib import Path  # Object-oriented filesystem paths - Platform-independent path manipulation
import os
import sys

# Define the database file path that works both in development and when packaged
def get_db_path():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (PyInstaller)
        application_path = os.path.dirname(sys.executable)
    else:
        # If run from a Python interpreter
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(application_path, "accounting.db")

DB_FILE = get_db_path()

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.committed = False

    def __enter__(self):
        self.connection = sqlite3.connect(str(DB_FILE))
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            try:
                if exc_type or exc_val or exc_tb:
                    if not self.committed:
                        self.connection.rollback()
                else:
                    if not self.committed:
                        self.connection.commit()
            finally:
                self.connection.close()
                self.connection = None

def init_database():
    """Initialize the database with required tables"""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        # Create accounting tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
                balance DECIMAL(15,2) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                reference_no TEXT UNIQUE,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS journal_entry_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_entry_id INTEGER,
                account_id INTEGER,
                description TEXT,
                debit DECIMAL(15,2) DEFAULT 0,
                credit DECIMAL(15,2) DEFAULT 0,
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );

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
            );
        """)
        
        # Insert default accounts if they don't exist
        default_accounts = [
            # Assets
            ('1000', 'Cash', 'asset'),
            ('1050', 'Bank', 'asset'),
            ('1100', 'Accounts Receivable', 'asset'),
            ('1200', 'Inventory', 'asset'),
            ('1300', 'Equipment', 'asset'),
            ('1350', 'Accumulated Depreciation', 'asset'),  # Contra-asset, but 'asset' for balance logic

            # Liabilities
            ('2000', 'Accounts Payable', 'liability'),
            ('2100', 'Salaries Payable', 'liability'),
            ('2200', 'Rent Payable', 'liability'),
            ('2300', 'Utilities Payable', 'liability'),

            # Equity
            ('3000', 'Owner Capital', 'equity'),
            ('3100', 'Retained Earnings', 'equity'),
            ('3200', 'Drawing', 'equity'),

            # Revenue
            ('4000', 'Sales Revenue', 'revenue'),
            ('4100', 'Wholesale Revenue', 'revenue'),

            # Expenses
            ('5000', 'Cost of Goods Sold', 'expense'),
            ('6000', 'Salaries Expense', 'expense'),
            ('6100', 'Rent Expense', 'expense'),
            ('6200', 'Utilities Expense', 'expense'),
            ('6300', 'Maintenance Expense', 'expense'),
            ('6400', 'Transportation Expense', 'expense'),
            ('6500', 'Supplies Expense', 'expense'),
            ('6600', 'Bad Debt Expense', 'expense'),
            ('6700', 'Depreciation Expense', 'expense'),
            ('6800', 'Miscellaneous Expense', 'expense')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO accounts (code, name, type)
            VALUES (?, ?, ?)
        ''', default_accounts)
        
        # Create other tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                unit_price REAL NOT NULL,
                quantity REAL DEFAULT 0,
                minimum_quantity REAL DEFAULT 0,
                product_type TEXT DEFAULT 'bulk',
                pieces_per_unit INTEGER DEFAULT 1,
                piece_price REAL DEFAULT 0,
                expiry_date DATE
            );
        """)

        # Migration: Add columns to products if they don't exist
        cursor.execute("PRAGMA table_info(products)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'product_type' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN product_type TEXT DEFAULT 'bulk'")
        if 'pieces_per_unit' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN pieces_per_unit INTEGER DEFAULT 1")
        if 'piece_price' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN piece_price REAL DEFAULT 0")
        if 'expiry_date' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN expiry_date DATE")

        # Migration for purchase_items
        cursor.execute("PRAGMA table_info(purchase_items)")
        p_items_columns = [info[1] for info in cursor.fetchall()]
        if 'expiry_date' not in p_items_columns and len(p_items_columns) > 0:
            cursor.execute("ALTER TABLE purchase_items ADD COLUMN expiry_date DATE")

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payment_type TEXT DEFAULT 'cash',
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );

            CREATE TABLE IF NOT EXISTS sales_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES sales_invoices (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER,
                date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payment_type TEXT DEFAULT 'cash',
                due_date TEXT,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            );

            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                expiry_date DATE,
                FOREIGN KEY (invoice_id) REFERENCES purchase_invoices (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS revenues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS purchase_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL,
                date TEXT,
                supplier_id INTEGER,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            );

            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER UNIQUE,
                instructions TEXT,
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                ingredient_id INTEGER,
                quantity REAL, 
                FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                FOREIGN KEY (ingredient_id) REFERENCES products(id)
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                module TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        # Migration: Add columns to products if they don't exist
        cursor.execute("PRAGMA table_info(products)")
        cols = [info[1] for info in cursor.fetchall()]
        if 'is_recipe' not in cols:
            cursor.execute("ALTER TABLE products ADD COLUMN is_recipe INTEGER DEFAULT 0")
        if 'unit_cost' not in cols:
            cursor.execute("ALTER TABLE products ADD COLUMN unit_cost REAL DEFAULT 0")

        # Migration: Add payment_type to invoices
        cursor.execute("PRAGMA table_info(sales_invoices)")
        s_cols = [info[1] for info in cursor.fetchall()]
        if 'payment_type' not in s_cols and len(s_cols) > 0:
            cursor.execute("ALTER TABLE sales_invoices ADD COLUMN payment_type TEXT DEFAULT 'cash'")

        cursor.execute("PRAGMA table_info(purchase_invoices)")
        p_cols = [info[1] for info in cursor.fetchall()]
        if 'payment_type' not in p_cols and len(p_cols) > 0:
            cursor.execute("ALTER TABLE purchase_invoices ADD COLUMN payment_type TEXT DEFAULT 'cash'")
        if 'due_date' not in p_cols and len(p_cols) > 0:
            cursor.execute("ALTER TABLE purchase_invoices ADD COLUMN due_date TEXT")
            
        # Migration: Ensure sales status is correct (Cash sales should be 'paid')
        cursor.execute("UPDATE sales_invoices SET status = 'paid', paid_amount = total_amount WHERE payment_type = 'cash' AND status = 'pending'")
        
        # Migration: Ensure paid_amount is initialized for all purchase invoices
        cursor.execute("UPDATE purchase_invoices SET paid_amount = total_amount WHERE paid_amount IS NULL AND payment_type = 'cash'")
        cursor.execute("UPDATE purchase_invoices SET paid_amount = 0 WHERE paid_amount IS NULL AND payment_type = 'credit'")
        
        # Data Repair: Recalculate total_amount for invoices that were saved as 0 due to a UI bug
        cursor.execute("""
            UPDATE purchase_invoices 
            SET total_amount = (
                SELECT COALESCE(SUM(quantity * unit_price), 0)
                FROM purchase_items
                WHERE invoice_id = purchase_invoices.id
            )
            WHERE total_amount = 0
        """)
        
        # Re-initialize paid_amount for the repaired records if they are cash
        cursor.execute("UPDATE purchase_invoices SET paid_amount = total_amount WHERE payment_type = 'cash' AND (paid_amount = 0 OR paid_amount IS NULL) AND total_amount > 0")
        
        # Data Repair: Backfill missing due_date for credit invoices (default to invoice date)
        cursor.execute("""
            UPDATE purchase_invoices 
            SET due_date = date
            WHERE payment_type = 'credit' AND due_date IS NULL
        """)

        # Insert default admin if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                          ('admin', 'admin123', 'admin'))

# Initialize database when module is imported
init_database()

def log_action(user_id, username, action, module, details=None):
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (user_id, username, action, module, details)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, action, module, details))
    except Exception as e:
        print(f"Failed to log action: {e}")
