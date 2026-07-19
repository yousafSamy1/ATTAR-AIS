import sqlite3
import datetime

db_path = "database/accounting.db"

def seed_more_products():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        new_products = [
            ('Cinnamon Sticks', 120, 80),
            ('Black Pepper', 200, 150),
            ('Turmeric Powder', 90, 60),
            ('Cardamom Pods', 600, 450),
            ('Cloves', 350, 250),
            ('Ginger Root', 110, 75),
            ('Nutmeg', 280, 200),
            ('Star Anise', 220, 160),
            ('Coriander Seeds', 80, 50),
            ('Fennel Seeds', 85, 55)
        ]

        product_ids = []
        for name, price, cost in new_products:
            cursor.execute("INSERT OR IGNORE INTO products (name, unit_price, unit_cost, quantity) VALUES (?, ?, ?, 0)", (name, price, cost))
            # get the id
            cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
            product_ids.append(cursor.fetchone()['id'])
            
        # Add 50 quantity to all products except the last 3
        # Let's get all product ids
        cursor.execute("SELECT id FROM products")
        all_p_ids = [row['id'] for row in cursor.fetchall()]
        
        # Shuffle or just leave the last 3 out of stock
        in_stock_ids = all_p_ids[:-3]
        out_of_stock_ids = all_p_ids[-3:]
        
        # We will create a Purchase Invoice for the in_stock_ids
        total_purchase_amount = 0
        purchase_items = []
        
        for p_id in in_stock_ids:
            # check current quantity
            cursor.execute("SELECT quantity, unit_cost FROM products WHERE id = ?", (p_id,))
            row = cursor.fetchone()
            current_q = row['quantity']
            unit_cost = row['unit_cost']
            
            if current_q < 50:
                qty_to_add = 50 - current_q
                subtotal = qty_to_add * unit_cost
                total_purchase_amount += subtotal
                purchase_items.append((p_id, qty_to_add, unit_cost))
                
                # update qty
                cursor.execute("UPDATE products SET quantity = 50 WHERE id = ?", (p_id,))
        
        for p_id in out_of_stock_ids:
            # Set to 0 just in case
            cursor.execute("UPDATE products SET quantity = 0 WHERE id = ?", (p_id,))
            
        # Create Purchase Invoice
        if total_purchase_amount > 0:
            date_now = datetime.date.today().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO purchase_invoices (supplier_id, date, total_amount, payment_type, paid_amount, status) VALUES (1, ?, ?, 'credit', 0, 'pending')", (date_now, total_purchase_amount))
            pur_id = cursor.lastrowid
            
            for p_id, qty, cost in purchase_items:
                cursor.execute("INSERT INTO purchase_items (invoice_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)", (pur_id, p_id, qty, cost))
                
            cursor.execute("UPDATE suppliers SET balance = balance + ? WHERE id = 1", (total_purchase_amount,))
            
            # Create Journal Entry
            cursor.execute("INSERT INTO journal_entries (date, reference_no, description) VALUES (?, ?, ?)", (date_now, f"PUR-{pur_id}", "Bulk Stock Purchase"))
            je_id = cursor.lastrowid
            
            # Debit Inventory (1200)
            cursor.execute("SELECT id, type, balance FROM accounts WHERE code = '1200'")
            acc_inv = cursor.fetchone()
            cursor.execute("INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)", (je_id, acc_inv['id'], "Bulk Inventory Purchase", total_purchase_amount, 0))
            cursor.execute("INSERT INTO general_ledger (account_id, journal_entry_id, date, description, debit, credit) VALUES (?, ?, ?, ?, ?, ?)", (acc_inv['id'], je_id, date_now, "Bulk Inventory Purchase", total_purchase_amount, 0))
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (total_purchase_amount, acc_inv['id']))
            
            # Credit Accounts Payable (2000)
            cursor.execute("SELECT id, type, balance FROM accounts WHERE code = '2000'")
            acc_ap = cursor.fetchone()
            cursor.execute("INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)", (je_id, acc_ap['id'], "Accounts Payable", 0, total_purchase_amount))
            cursor.execute("INSERT INTO general_ledger (account_id, journal_entry_id, date, description, debit, credit) VALUES (?, ?, ?, ?, ?, ?)", (acc_ap['id'], je_id, date_now, "Accounts Payable", 0, total_purchase_amount))
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (total_purchase_amount, acc_ap['id']))

        conn.commit()
        print("More products and quantities seeded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_more_products()
