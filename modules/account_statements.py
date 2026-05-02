import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTableWidget, QTableWidgetItem, QComboBox,
                           QHeaderView, QDialog, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from database.db_config import DatabaseConnection
from datetime import datetime, timedelta

class AccountStatementDialog(QDialog):
    def __init__(self, parent=None, entity_type="customer"):
        super().__init__(parent)
        self.entity_type = entity_type  # "customer" or "supplier"
        self.init_ui()
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle(f"{'Customer' if self.entity_type == 'customer' else 'Supplier'} Account Statement")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"{'Customer' if self.entity_type == 'customer' else 'Supplier'} Account Statement")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Entity Selection
        selection_layout = QHBoxLayout()
        entity_label = QLabel(f"Select {'Customer' if self.entity_type == 'customer' else 'Supplier'}:")
        self.entity_combo = QComboBox()
        self.load_entities()
        
        # Date Range
        date_layout = QHBoxLayout()
        from_label = QLabel("From:")
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        
        to_label = QLabel("To:")
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        
        selection_layout.addWidget(entity_label)
        selection_layout.addWidget(self.entity_combo)
        selection_layout.addStretch()
        selection_layout.addWidget(from_label)
        selection_layout.addWidget(self.from_date)
        selection_layout.addWidget(to_label)
        selection_layout.addWidget(self.to_date)
        
        layout.addLayout(selection_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", 
            "Reference", 
            "Description", 
            "Debit", 
            "Credit", 
            "Balance"
        ])
        
        # Make table read-only
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 100)  # Date
        self.table.setColumnWidth(1, 120)  # Reference
        self.table.setColumnWidth(3, 100)  # Debit
        self.table.setColumnWidth(4, 100)  # Credit
        self.table.setColumnWidth(5, 120)  # Balance
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_statement)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.entity_combo.currentIndexChanged.connect(self.refresh_statement)
        self.from_date.dateChanged.connect(self.refresh_statement)
        self.to_date.dateChanged.connect(self.refresh_statement)
        
    def load_entities(self):
        """Load customers or suppliers into combo box"""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                table = "customers" if self.entity_type == "customer" else "suppliers"
                cursor.execute(f"SELECT id, name FROM {table} ORDER BY name")
                entities = cursor.fetchall()
                
                self.entity_combo.clear()
                self.entity_combo.addItem("Select...", None)
                for entity in entities:
                    self.entity_combo.addItem(entity['name'], entity['id'])
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load {self.entity_type}s: {str(e)}")
            
    def refresh_statement(self):
        """Refresh the account statement"""
        entity_id = self.entity_combo.currentData()
        if not entity_id:
            self.table.setRowCount(0)
            return
            
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Get opening balance
                if self.entity_type == "customer":
                    cursor.execute("""
                        SELECT 
                            COALESCE(
                                (
                                    SELECT SUM(total_amount - COALESCE(paid_amount, 0))
                                    FROM sales_invoices
                                    WHERE customer_id = ? AND date < ?
                                ), 0
                            ) as opening_balance
                    """, (entity_id, self.from_date.date().toString("yyyy-MM-dd")))
                else:
                    cursor.execute("""
                        SELECT 
                            COALESCE(
                                (
                                    SELECT SUM(total_amount - COALESCE(paid_amount, 0))
                                    FROM purchase_invoices
                                    WHERE supplier_id = ? AND date < ?
                                ), 0
                            ) as opening_balance
                    """, (entity_id, self.from_date.date().toString("yyyy-MM-dd")))
                
                opening_balance = cursor.fetchone()['opening_balance']
                running_balance = opening_balance
                
                # Get transactions
                if self.entity_type == "customer":
                    cursor.execute("""
                        SELECT 
                            date,
                            'INV-' || id as reference,
                            'Sales Invoice #' || id as description,
                            total_amount as debit,
                            0 as credit
                        FROM sales_invoices
                        WHERE customer_id = ? AND date BETWEEN ? AND ?
                        
                        UNION ALL
                        
                        SELECT 
                            je.date,
                            je.reference_no,
                            jei.description,
                            0 as debit,
                            jei.credit
                        FROM journal_entries je
                        JOIN journal_entry_items jei ON je.id = jei.journal_entry_id
                        JOIN accounts a ON jei.account_id = a.id
                        WHERE a.code = '1100'  -- Accounts Receivable
                        AND je.reference_no LIKE 'PAY-RCV-%'
                        AND je.date BETWEEN ? AND ?
                        AND EXISTS (
                            SELECT 1 
                            FROM sales_invoices si 
                            WHERE si.customer_id = ?
                            AND je.reference_no LIKE '%' || si.id
                        )
                        
                        ORDER BY date, reference
                    """, (
                        entity_id, 
                        self.from_date.date().toString("yyyy-MM-dd"),
                        self.to_date.date().toString("yyyy-MM-dd"),
                        self.from_date.date().toString("yyyy-MM-dd"),
                        self.to_date.date().toString("yyyy-MM-dd"),
                        entity_id
                    ))
                else:
                    cursor.execute("""
                        SELECT 
                            date,
                            'INV-' || id as reference,
                            'Purchase Invoice #' || id as description,
                            0 as debit,
                            total_amount as credit
                        FROM purchase_invoices
                        WHERE supplier_id = ? AND date BETWEEN ? AND ?
                        
                        UNION ALL
                        
                        SELECT 
                            je.date,
                            je.reference_no,
                            jei.description,
                            jei.debit,
                            0 as credit
                        FROM journal_entries je
                        JOIN journal_entry_items jei ON je.id = jei.journal_entry_id
                        JOIN accounts a ON jei.account_id = a.id
                        WHERE a.code = '2000'  -- Accounts Payable
                        AND je.reference_no LIKE 'PAY-MADE-%'
                        AND je.date BETWEEN ? AND ?
                        AND EXISTS (
                            SELECT 1 
                            FROM purchase_invoices pi 
                            WHERE pi.supplier_id = ?
                            AND je.reference_no LIKE '%' || pi.id
                        )
                        
                        ORDER BY date, reference
                    """, (
                        entity_id,
                        self.from_date.date().toString("yyyy-MM-dd"),
                        self.to_date.date().toString("yyyy-MM-dd"),
                        self.from_date.date().toString("yyyy-MM-dd"),
                        self.to_date.date().toString("yyyy-MM-dd"),
                        entity_id
                    ))
                
                transactions = cursor.fetchall()
                
                # Display results
                self.table.setRowCount(len(transactions) + 1)  # +1 for opening balance
                
                # Add opening balance row
                date_item = QTableWidgetItem(self.from_date.date().toString("yyyy-MM-dd"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(0, 0, date_item)
                
                ref_item = QTableWidgetItem("")
                ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(0, 1, ref_item)
                
                desc_item = QTableWidgetItem("Opening Balance")
                desc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(0, 2, desc_item)
                
                debit_item = QTableWidgetItem("")
                debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(0, 3, debit_item)
                
                credit_item = QTableWidgetItem("")
                credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(0, 4, credit_item)
                
                balance_item = QTableWidgetItem(f"${opening_balance:.2f}")
                balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(0, 5, balance_item)
                
                # Style opening balance row
                for col in range(6):
                    item = self.table.item(0, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.lightGray)
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                
                # Add transactions
                for i, trans in enumerate(transactions, 1):
                    # Update running balance
                    running_balance += trans['debit'] - trans['credit']
                    
                    # Date
                    date_item = QTableWidgetItem(trans['date'])
                    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 0, date_item)
                    
                    # Reference
                    ref_item = QTableWidgetItem(trans['reference'])
                    ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 1, ref_item)
                    
                    # Description
                    desc_item = QTableWidgetItem(trans['description'])
                    desc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 2, desc_item)
                    
                    # Debit
                    debit_item = QTableWidgetItem(f"${trans['debit']:.2f}" if trans['debit'] > 0 else "")
                    debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 3, debit_item)
                    
                    # Credit
                    credit_item = QTableWidgetItem(f"${trans['credit']:.2f}" if trans['credit'] > 0 else "")
                    credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 4, credit_item)
                    
                    # Balance
                    balance_item = QTableWidgetItem(f"${running_balance:.2f}")
                    balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 5, balance_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh statement: {str(e)}") 