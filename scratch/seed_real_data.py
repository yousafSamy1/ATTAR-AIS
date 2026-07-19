import sqlite3
import datetime
import os

db_path = "database/accounting.db"

def wipe_and_seed():
    print(f"Connecting to DB: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. WIPE ALL TRANSACTION DATA
        print("Wiping existing financial data...")
        tables_to_clear = [
            "general_ledger", "journal_entry_items", "journal_entries",
            "expenses", "revenues", 
            "sales_items", "sales_invoices",
            "purchase_items", "purchase_invoices",
            "purchase_history"
        ]
        
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

        # Reset balances and quantities
        cursor.execute("UPDATE accounts SET balance = 0")
        cursor.execute("UPDATE customers SET balance = 0")
        cursor.execute("UPDATE suppliers SET balance = 0")
        cursor.execute("UPDATE products SET quantity = 0")

        # Ensure we have at least one supplier and customer for our real data
        cursor.execute("INSERT OR IGNORE INTO suppliers (id, name) VALUES (1, 'Al-Madina Spice Traders')")
        cursor.execute("INSERT OR IGNORE INTO customers (id, name) VALUES (1, 'Al-Nour Pharmacy')")
        
        # Ensure we have some products
        cursor.execute("INSERT OR IGNORE INTO products (id, name, unit_price, unit_cost, quantity) VALUES (1, 'Premium Cumin', 150, 100, 0)")
        cursor.execute("INSERT OR IGNORE INTO products (id, name, unit_price, unit_cost, quantity) VALUES (2, 'Pure Saffron', 800, 500, 0)")

        # 2. HELPER TO CREATE JOURNAL ENTRIES
        def create_je(date, ref, desc, lines):
            cursor.execute("INSERT INTO journal_entries (date, reference_no, description) VALUES (?, ?, ?)", (date, ref, desc))
            je_id = cursor.lastrowid
            
            for line in lines:
                acc_code, line_desc, debit, credit = line
                cursor.execute("SELECT id, type, balance FROM accounts WHERE code = ?", (acc_code,))
                acc = cursor.fetchone()
                
                if not acc:
                    print(f"Account {acc_code} not found! Check your chart of accounts.")
                    continue
                    
                # Insert JE Item
                cursor.execute("INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)",
                               (je_id, acc['id'], line_desc, debit, credit))
                
                # Insert GL Entry
                cursor.execute("INSERT INTO general_ledger (account_id, journal_entry_id, date, description, debit, credit) VALUES (?, ?, ?, ?, ?, ?)",
                               (acc['id'], je_id, date, line_desc, debit, credit))
                
                # Update Account Balance
                if acc['type'] in ('asset', 'expense'):
                    balance_change = debit - credit
                else:
                    balance_change = credit - debit
                    
                cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (balance_change, acc['id']))

        print("Seeding new real data...")
        base_date = datetime.date.today().replace(day=1) # Start of current month

        # --- TRANSACTION 1: Owner Capital Injection ---
        date1 = base_date.strftime("%Y-%m-%d")
        create_je(date1, "JE-001", "Initial Capital Investment", [
            ("1000", "Capital Deposit", 100000, 0),    # Debit Cash
            ("3000", "Owner Investment", 0, 100000)    # Credit Owner Capital
        ])

        # --- TRANSACTION 2: Pay Rent for the Shop ---
        date2 = (base_date + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)", (date2, "Rent", "Monthly Shop Rent", 5000))
        exp_id = cursor.lastrowid
        create_je(date2, f"EXP-{exp_id}", "Monthly Rent Payment", [
            ("6100", "May Rent", 5000, 0),             # Debit Rent Expense
            ("1000", "Cash Paid for Rent", 0, 5000)    # Credit Cash
        ])

        # --- TRANSACTION 3: Purchase Inventory (Cash) ---
        date3 = (base_date + datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO purchase_invoices (supplier_id, date, total_amount, payment_type, paid_amount, status) VALUES (1, ?, 5000, 'cash', 5000, 'paid')", (date3,))
        pur_id1 = cursor.lastrowid
        cursor.execute("INSERT INTO purchase_items (invoice_id, product_id, quantity, unit_price) VALUES (?, 1, 50, 100)", (pur_id1,))
        cursor.execute("UPDATE products SET quantity = quantity + 50 WHERE id = 1")
        
        create_je(date3, f"PUR-{pur_id1}", "Purchase of Premium Cumin", [
            ("1200", "Inventory Received", 5000, 0),   # Debit Inventory
            ("1000", "Cash Paid to Supplier", 0, 5000) # Credit Cash
        ])

        # --- TRANSACTION 4: Purchase Inventory (Credit) ---
        date4 = (base_date + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO purchase_invoices (supplier_id, date, total_amount, payment_type, paid_amount, status) VALUES (1, ?, 10000, 'credit', 0, 'pending')", (date4,))
        pur_id2 = cursor.lastrowid
        cursor.execute("INSERT INTO purchase_items (invoice_id, product_id, quantity, unit_price) VALUES (?, 2, 20, 500)", (pur_id2,))
        cursor.execute("UPDATE products SET quantity = quantity + 20 WHERE id = 2")
        cursor.execute("UPDATE suppliers SET balance = balance + 10000 WHERE id = 1")
        
        create_je(date4, f"PUR-{pur_id2}", "Purchase of Pure Saffron", [
            ("1200", "Inventory Received", 10000, 0),  # Debit Inventory
            ("2000", "Accounts Payable", 0, 10000)     # Credit Accounts Payable
        ])

        # --- TRANSACTION 5: Cash Sale to Walk-in Customer ---
        date5 = (base_date + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO sales_invoices (customer_id, date, total_amount, payment_type, paid_amount, status) VALUES (1, ?, 1500, 'cash', 1500, 'paid')", (date5,))
        sale_id1 = cursor.lastrowid
        cursor.execute("INSERT INTO sales_items (invoice_id, product_id, quantity, unit_price) VALUES (?, 1, 10, 150)", (sale_id1,))
        cursor.execute("UPDATE products SET quantity = quantity - 10 WHERE id = 1")
        
        create_je(date5, f"SALE-{sale_id1}", "Cash Sale of Cumin", [
            ("1000", "Cash Received", 1500, 0),        # Debit Cash
            ("4000", "Sales Revenue", 0, 1500),        # Credit Revenue
            ("5000", "Cost of Goods Sold", 1000, 0),   # Debit COGS (10kg * 100 EGP)
            ("1200", "Inventory Sold", 0, 1000)        # Credit Inventory
        ])

        # --- TRANSACTION 6: Credit Sale to Pharmacy ---
        date6 = (base_date + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO sales_invoices (customer_id, date, total_amount, payment_type, paid_amount, status) VALUES (1, ?, 1600, 'credit', 0, 'pending')", (date6,))
        sale_id2 = cursor.lastrowid
        cursor.execute("INSERT INTO sales_items (invoice_id, product_id, quantity, unit_price) VALUES (?, 2, 2, 800)", (sale_id2,))
        cursor.execute("UPDATE products SET quantity = quantity - 2 WHERE id = 2")
        cursor.execute("UPDATE customers SET balance = balance + 1600 WHERE id = 1")
        
        create_je(date6, f"SALE-{sale_id2}", "Credit Sale of Saffron", [
            ("1100", "Accounts Receivable", 1600, 0),  # Debit A/R
            ("4000", "Sales Revenue", 0, 1600),        # Credit Revenue
            ("5000", "Cost of Goods Sold", 1000, 0),   # Debit COGS (2kg * 500 EGP)
            ("1200", "Inventory Sold", 0, 1000)        # Credit Inventory
        ])

        # --- TRANSACTION 7: Utilities Expense ---
        date7 = (base_date + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)", (date7, "Utilities", "Electricity Bill", 800))
        exp_id2 = cursor.lastrowid
        create_je(date7, f"EXP-{exp_id2}", "Electricity Bill Payment", [
            ("6200", "Utilities Paid", 800, 0),        # Debit Utilities Expense
            ("1000", "Cash Paid", 0, 800)              # Credit Cash
        ])
        
        conn.commit()
        print("Database wiped and realistic seed data inserted successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    wipe_and_seed()
