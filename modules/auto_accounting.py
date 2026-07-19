# PyQt6 Core Components
from PyQt6.QtCore import (
    QObject,         # Base class for objects that can emit signals
    pyqtSignal       # Signal/slot communication mechanism
)

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler

# Python Standard Libraries
from decimal import Decimal  # Precise decimal arithmetic
from datetime import datetime  # Date and time handling

class AutoAccountingModule(QObject):
    """
    This module handles automatic journal entries for all transactions in the system.
    It is used by other modules to create journal entries when transactions occur.
    """
    
    # Signal emitted when a journal entry is created, passing the entry ID
    journal_entry_created = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
    
    def create_sales_journal_entry(self, cursor, sale_id: int, customer_id: int, total_amount: float, 
                                 cost_of_goods: float, date: str, payment_type: str = 'cash') -> None:
        """Create journal entries for a sales transaction"""
        try:
            # Create the journal entry header
            cursor.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (
                date,
                f"SALE-{sale_id}",
                f"Sales Invoice #{sale_id}"
            ))
            
            journal_entry_id = cursor.lastrowid
            if journal_entry_id is None:
                raise Exception("Failed to create journal entry - no ID returned")
            
            # 1. Debit Asset Account (Cash or A/R)
            asset_account = "1000" if payment_type == 'cash' else "1100"
            self._create_journal_item(cursor, journal_entry_id, asset_account, 
                                   f"Sales Invoice #{sale_id} ({payment_type})", total_amount, 0)
            
            # 2. Credit Sales Revenue
            self._create_journal_item(cursor, journal_entry_id, "4000",
                                   f"Sales Invoice #{sale_id}", 0, total_amount)
            
            # 2. COGS (Debit COGS, Credit Inventory) - Only if cost > 0
            if cost_of_goods > 0:
                self._create_journal_item(cursor, journal_entry_id, "5000",
                                       f"COGS for Sale #{sale_id}", cost_of_goods, 0)
                self._create_journal_item(cursor, journal_entry_id, "1200",
                                       f"COGS for Sale #{sale_id}", 0, cost_of_goods)
            
            # Update customer balance ONLY if it's a credit sale
            if payment_type == 'credit':
                cursor.execute("""
                    UPDATE customers 
                    SET balance = balance + ?
                    WHERE id = ?
                """, (total_amount, customer_id))
            
            self.journal_entry_created.emit(journal_entry_id)
                
        except Exception as e:
            raise Exception(f"Failed to create sales journal entry: {str(e)}")
    
    def create_purchase_journal_entry(self, cursor, purchase_id: int, supplier_id: int, 
                                    total_amount: float, date: str, payment_type: str = 'cash') -> None:
        """Create journal entries for a purchase transaction"""
        try:
            # Create the journal entry header
            cursor.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (
                date,
                f"PUR-{purchase_id}",
                f"Purchase Invoice #{purchase_id}"
            ))
            
            journal_entry_id = cursor.lastrowid
            
            # 1. Debit Inventory
            self._create_journal_item(cursor, journal_entry_id, "1200",
                                   f"Purchase Invoice #{purchase_id}", total_amount, 0)
            
            # 2. Credit Liability or Cash (A/P or Cash)
            payment_account = "2000" if payment_type == 'credit' else "1000"
            self._create_journal_item(cursor, journal_entry_id, payment_account, 
                                   f"Purchase Invoice #{purchase_id} ({payment_type})", 0, total_amount)
            
            # Update supplier balance ONLY if it's a credit purchase
            if payment_type == 'credit':
                cursor.execute("""
                    UPDATE suppliers 
                    SET balance = balance + ?
                    WHERE id = ?
                """, (total_amount, supplier_id))
            
            self.journal_entry_created.emit(journal_entry_id)
                
        except Exception as e:
            raise Exception(f"Failed to create purchase journal entry: {str(e)}")
    
    def create_expense_journal_entry(self, cursor, expense_id: int, amount: float, 
                                   category: str, date: str) -> None:
        """Create journal entries for an expense transaction"""
        try:
            # Create the journal entry header
            cursor.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (
                date,
                f"EXP-{expense_id}",
                f"Expense #{expense_id} - {category}"
            ))
            
            journal_entry_id = cursor.lastrowid
            
            # Map category to specific account
            category_map = {
                "Salaries": "6000",
                "Rent": "6100",
                "Utilities": "6200",
                "Maintenance": "6300",
                "Transportation": "6400",
                "Supplies": "6500",
                "Bad Debt": "6600",
                "Depreciation": "6700",
                "Purchase": "5000",
                "Other": "6800"
            }
            
            account_code = category_map.get(category, "6800")
            
            # 1. Debit Specific Expense Account
            self._create_journal_item(cursor, journal_entry_id, account_code,
                                   f"Expense #{expense_id} - {category}", amount, 0)
            
            # 2. Credit Cash
            self._create_journal_item(cursor, journal_entry_id, "1000",
                                   f"Expense #{expense_id} - {category}", 0, amount)
            
            self.journal_entry_created.emit(journal_entry_id)
                
        except Exception as e:
            raise Exception(f"Failed to create expense journal entry: {str(e)}")
    
    def create_payment_received_entry(self, cursor, customer_id: int, amount: float, 
                                    invoice_id: int, date: str) -> None:
        """Create journal entries for payment received from customer"""
        try:
            # Create the journal entry header
            cursor.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (
                date,
                f"PAY-RCV-{invoice_id}",
                f"Payment Received for Invoice #{invoice_id}"
            ))
            
            journal_entry_id = cursor.lastrowid
            
            # 1. Debit Cash
            self._create_journal_item(cursor, journal_entry_id, "1000",
                                   f"Payment for Invoice #{invoice_id}", amount, 0)
            
            # 2. Credit Accounts Receivable
            self._create_journal_item(cursor, journal_entry_id, "1100",
                                   f"Payment for Invoice #{invoice_id}", 0, amount)
            
            # Update customer balance
            cursor.execute("""
                UPDATE customers 
                SET balance = balance - ?
                WHERE id = ?
            """, (amount, customer_id))
            
            self.journal_entry_created.emit(journal_entry_id)
                
        except Exception as e:
            raise Exception(f"Failed to create payment received entry: {str(e)}")
    
    def create_payment_made_entry(self, cursor, supplier_id: int, amount: float, 
                                invoice_id: int, date: str) -> None:
        """Create journal entries for payment made to supplier"""
        try:
            # Create the journal entry header
            cursor.execute("""
                INSERT INTO journal_entries (date, reference_no, description)
                VALUES (?, ?, ?)
            """, (
                date,
                f"PAY-MADE-{invoice_id}",
                f"Payment Made for Invoice #{invoice_id}"
            ))
            
            journal_entry_id = cursor.lastrowid
            
            # 1. Debit Accounts Payable
            self._create_journal_item(cursor, journal_entry_id, "2000",
                                   f"Payment for Invoice #{invoice_id}", amount, 0)
            
            # 2. Credit Cash
            self._create_journal_item(cursor, journal_entry_id, "1000",
                                   f"Payment for Invoice #{invoice_id}", 0, amount)
            
            # Update supplier balance
            cursor.execute("""
                UPDATE suppliers 
                SET balance = balance - ?
                WHERE id = ?
            """, (amount, supplier_id))
            
            self.journal_entry_created.emit(journal_entry_id)
                
        except Exception as e:
            raise Exception(f"Failed to create payment made entry: {str(e)}")
    
    def _create_journal_item(self, cursor, journal_entry_id: int, account_code: str,
                           description: str, debit: float, credit: float) -> None:
        """Helper method to create a journal entry item and update the general ledger"""
        
        # Get account ID from code
        cursor.execute("SELECT id, type FROM accounts WHERE code = ?", (account_code,))
        account = cursor.fetchone()
        if not account:
            raise Exception(f"Account with code {account_code} not found")
        
        account_id = account['id']
        account_type = account['type']
        
        # Insert journal entry item
        cursor.execute("""
            INSERT INTO journal_entry_items 
            (journal_entry_id, account_id, description, debit, credit)
            VALUES (?, ?, ?, ?, ?)
        """, (
            journal_entry_id,
            account_id,
            description,
            debit,
            credit
        ))
        
        # Get the date for the general ledger entry
        cursor.execute("SELECT date FROM journal_entries WHERE id = ?", (journal_entry_id,))
        date = cursor.fetchone()['date']
        
        # Add to general ledger
        cursor.execute("""
            INSERT INTO general_ledger
            (account_id, journal_entry_id, date, description, debit, credit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            account_id,
            journal_entry_id,
            date,
            description,
            debit,
            credit
        ))
        
        # Update account balance based on account type
        if account_type in ('asset', 'expense'):
            balance_change = debit - credit
        else:
            balance_change = credit - debit
            
        cursor.execute("""
            UPDATE accounts 
            SET balance = balance + ?
            WHERE id = ?
        """, (balance_change, account_id)) 