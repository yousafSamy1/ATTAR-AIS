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
            ('1000', 'Cash', 'asset'),
            ('1100', 'Accounts Receivable', 'asset'),
            ('1200', 'Inventory', 'asset'),
            ('2000', 'Accounts Payable', 'liability'),
            ('3000', 'Owner''s Equity', 'equity'),
            ('4000', 'Sales Revenue', 'revenue'),
            ('5000', 'Cost of Goods Sold', 'expense'),
            ('6000', 'Operating Expenses', 'expense')
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
                quantity INTEGER DEFAULT 0,
                minimum_quantity INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sales_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );

            CREATE TABLE IF NOT EXISTS sales_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
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
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            );

            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
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
        """)

# Initialize database when module is imported
init_database()
