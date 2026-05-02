from database.db_config import DatabaseConnection
from datetime import datetime, timedelta

def insert_test_data():
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        # Add test customers
        cursor.execute("""
            INSERT INTO customers (name, contact_person, phone, email, address)
            VALUES 
            ('محل عطار الخير', 'أحمد محمود', '010-123-4567', 'ahmed@attarkhair.com', 'شارع التحرير'),
            ('Cafe B', 'Jane Smith', '234-567-8901', 'jane@cafeb.com', '456 Oak Ave')
        """)
        
        # Add test suppliers
        cursor.execute("""
            INSERT INTO suppliers (name, contact_person, phone, email, address)
            VALUES 
            ('موردو التوابل المتحدة', 'محمد علي', '011-234-5678', 'info@spicesupply.com', 'شارع الجلاء'),
            ('بيت العطارة', 'فاطمة حسن', '012-345-6789', 'fatma@attar.com', 'شارع النيل')
        """)
        
        # Get customer IDs
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row['id'] for row in cursor.fetchall()]
        
        # Get supplier IDs
        cursor.execute("SELECT id FROM suppliers")
        supplier_ids = [row['id'] for row in cursor.fetchall()]
        
        # Add sales invoices
        today = datetime.now()
        for customer_id in customer_ids:
            # Add multiple invoices per customer
            for i in range(3):
                invoice_date = (today - timedelta(days=i*5)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO sales_invoices (customer_id, date, total_amount, paid_amount, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (customer_id, invoice_date, 1000.00, 500.00, 'partial'))
                
                # Get the invoice ID
                invoice_id = cursor.lastrowid
                
                # Create journal entry for the sale
                cursor.execute("""
                    INSERT INTO journal_entries (date, reference_no, description)
                    VALUES (?, ?, ?)
                """, (invoice_date, f'INV-{invoice_id}', f'Sales Invoice #{invoice_id}'))
                
                journal_entry_id = cursor.lastrowid
                
                # Create journal entry items
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, ?, 0
                    FROM accounts WHERE code = '1100'
                """, (journal_entry_id, f'Sales Invoice #{invoice_id}', 1000.00))
                
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, 0, ?
                    FROM accounts WHERE code = '4000'
                """, (journal_entry_id, f'Sales Invoice #{invoice_id}', 1000.00))
                
                # Create payment entry
                payment_date = (today - timedelta(days=i*5-1)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO journal_entries (date, reference_no, description)
                    VALUES (?, ?, ?)
                """, (payment_date, f'PAY-RCV-{invoice_id}', f'Payment received for Invoice #{invoice_id}'))
                
                payment_entry_id = cursor.lastrowid
                
                # Create payment entry items
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, ?, 0
                    FROM accounts WHERE code = '1000'
                """, (payment_entry_id, f'Payment for Invoice #{invoice_id}', 500.00))
                
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, 0, ?
                    FROM accounts WHERE code = '1100'
                """, (payment_entry_id, f'Payment for Invoice #{invoice_id}', 500.00))
        
        # Add purchase invoices
        for supplier_id in supplier_ids:
            # Add multiple invoices per supplier
            for i in range(3):
                invoice_date = (today - timedelta(days=i*5)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO purchase_invoices (supplier_id, date, total_amount, paid_amount, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (supplier_id, invoice_date, 800.00, 400.00, 'partial'))
                
                # Get the invoice ID
                invoice_id = cursor.lastrowid
                
                # Create journal entry for the purchase
                cursor.execute("""
                    INSERT INTO journal_entries (date, reference_no, description)
                    VALUES (?, ?, ?)
                """, (invoice_date, f'PO-{invoice_id}', f'Purchase Invoice #{invoice_id}'))
                
                journal_entry_id = cursor.lastrowid
                
                # Create journal entry items
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, ?, 0
                    FROM accounts WHERE code = '1200'
                """, (journal_entry_id, f'Purchase Invoice #{invoice_id}', 800.00))
                
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, 0, ?
                    FROM accounts WHERE code = '2000'
                """, (journal_entry_id, f'Purchase Invoice #{invoice_id}', 800.00))
                
                # Create payment entry
                payment_date = (today - timedelta(days=i*5-1)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO journal_entries (date, reference_no, description)
                    VALUES (?, ?, ?)
                """, (payment_date, f'PAY-MADE-{invoice_id}', f'Payment made for Invoice #{invoice_id}'))
                
                payment_entry_id = cursor.lastrowid
                
                # Create payment entry items
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, ?, 0
                    FROM accounts WHERE code = '2000'
                """, (payment_entry_id, f'Payment for Invoice #{invoice_id}', 400.00))
                
                cursor.execute("""
                    INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit)
                    SELECT ?, id, ?, 0, ?
                    FROM accounts WHERE code = '1000'
                """, (payment_entry_id, f'Payment for Invoice #{invoice_id}', 400.00))

if __name__ == "__main__":
    insert_test_data() 