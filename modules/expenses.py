import sys
import os
from pathlib import Path
from PyQt6.QtCore import pyqtSignal

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                            QFormLayout, QMessageBox, QDialog, QComboBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database.db_config import DatabaseConnection
from datetime import datetime
from modules.theme import COLORS, get_button_style

class ExpenseDialog(QDialog):
    def __init__(self, parent=None, expense_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Expense")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.date_edit)
        
        # Description
        self.description_edit = QLineEdit()
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_edit)
        
        # Amount
        self.amount_edit = QLineEdit()
        layout.addWidget(QLabel("Amount:"))
        layout.addWidget(self.amount_edit)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Utilities",
            "Rent",
            "Salaries",
            "Supplies",
            "Maintenance",
            "Transportation",
            "Purchase",
            "Other"
        ])
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self.category_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(get_button_style('accent'))
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet(get_button_style('bg_mid'))
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Fill data if editing
        if expense_data:
            self.date_edit.setDate(QDate.fromString(expense_data['date'], Qt.DateFormat.ISODate))
            self.description_edit.setText(expense_data['description'])
            self.amount_edit.setText(str(expense_data['amount']))
            self.category_combo.setCurrentText(expense_data['category'])
    
    def get_data(self):
        return {
            'date': self.date_edit.date().toString(Qt.DateFormat.ISODate),
            'description': self.description_edit.text(),
            'amount': float(self.amount_edit.text() or 0),
            'category': self.category_combo.currentText()
        }

class ExpensesModule(QWidget):
    # Add signal
    expense_added = pyqtSignal()
    
    def __init__(self, auto_accounting, user=None):
        super().__init__()
        self.auto_accounting = auto_accounting
        self.user = user
        self.init_ui()
        self.load_expenses()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Add header
        header = QLabel("Expense Management")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)
        
        # Create top buttons and style
        btn_h = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add Expense")
        self.add_btn.setStyleSheet(get_button_style('green'))
        # Robust admin check
        is_admin = False
        if self.user and hasattr(self.user, 'get'):
            is_admin = (self.user.get('role') == 'admin')
            
        self.add_btn.setVisible(is_admin)
        btn_h.addWidget(self.add_btn)
        btn_h.addStretch()
        layout.addLayout(btn_h)
        
        # Create filter layout
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 10, 0, 10)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems([
            "Utilities",
            "Rent",
            "Salaries",
            "Supplies",
            "Maintenance",
            "Transportation",
            "Purchase",
            "Other"
        ])
        self.category_filter.setStyleSheet(f"""
            QComboBox {{
                padding: 5px;
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                min-width: 150px;
            }}
        """)
        self.category_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search description...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 5px 12px;
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                min-width: 250px;
            }}
        """)
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        
        # Month Filter
        self.month_filter = QComboBox()
        current_month = datetime.now().month
        current_year = datetime.now().year
        self.month_filter.addItem("All Months", "all")
        for i in range(12):
            month = current_month - i
            year = current_year
            if month <= 0:
                month += 12
                year -= 1
            m_str = f"{year}-{month:02d}"
            self.month_filter.addItem(datetime(year, month, 1).strftime("%B %Y"), m_str)
        
        self.month_filter.currentIndexChanged.connect(self.load_expenses)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.month_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Description", "Amount", "Category"])
        
        # Make table read-only
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Connect buttons
        self.add_btn.clicked.connect(self.add_expense)
        self.table.itemDoubleClicked.connect(self.edit_expense)
        
        # Configure table behavior
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description
        self.table.setColumnWidth(0, 60)   # ID
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(3, 180)  # Amount (wider for multi-line)
        self.table.setColumnWidth(4, 120)  # Category
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Category
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_expenses(self):
        month_str = self.month_filter.currentData()
        cat_filter = self.category_filter.currentText()
        search_text = self.search_input.text().lower()
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, date, description, amount, category, 'expense' as source, 0 as unpaid, 'Cash' as payment_type
                    FROM expenses
                    WHERE 1=1
                """
                params = []
                
                if month_str != "all":
                    query += " AND date LIKE ?"
                    params.append(f"{month_str}%")
                
                query += """
                    UNION ALL
                    SELECT id, date, 'Purchase Invoice #' || id || ' (' || status || ')' as description, total_amount as amount, 'Purchase' as category, 'purchase' as source, (total_amount - COALESCE(paid_amount, 0)) as unpaid, payment_type
                    FROM purchase_invoices
                    WHERE 1=1
                """
                
                if month_str != "all":
                    query += " AND date LIKE ?"
                    params.append(f"{month_str}%")
                
                query += " ORDER BY date DESC"
                
                cursor.execute(query, params)
                expenses = cursor.fetchall()
                
                self.table.setRowCount(len(expenses))
                for i, expense in enumerate(expenses):
                    # ID column
                    id_item = QTableWidgetItem(str(expense['id']))
                    id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 0, id_item)
                    
                    # Date column
                    date_item = QTableWidgetItem(expense['date'])
                    date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 1, date_item)
                    
                    # Description column
                    desc_item = QTableWidgetItem(expense['description'])
                    desc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 2, desc_item)
                    
                    # Amount column
                    amount_text = f"EGP {expense['amount']:.2f}\n[{expense['payment_type'].title()}]"
                    if expense['unpaid'] > 0:
                        amount_text += f"\n(Unpaid: {expense['unpaid']:.2f})"
                    amount_item = QTableWidgetItem(amount_text)
                    amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 3, amount_item)
                    
                    # Adjust row height for the multi-line text
                    self.table.setRowHeight(i, 70)
                    
                    # Category column
                    category_item = QTableWidgetItem(expense['category'])
                    category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    if expense['source'] == 'purchase':
                        category_item.setForeground(QColor(COLORS['accent']))
                    self.table.setItem(i, 4, category_item)
                    
                    # Store source in a hidden data role
                    id_item.setData(Qt.ItemDataRole.UserRole, expense['source'])
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load expenses: {str(e)}")
    
    def add_expense(self):
        dialog = ExpenseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                if not self.validate_expense_data(data):
                    return
                    
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO expenses (date, description, amount, category)
                            VALUES (?, ?, ?, ?)
                        """, (data['date'], data['description'], data['amount'], data['category']))
                        
                        expense_id = cursor.lastrowid
                        
                        # Create journal entries
                        self.auto_accounting.create_expense_journal_entry(
                            cursor,
                            expense_id,
                            data['amount'],
                            data['category'],
                            data['date']
                        )
                        
                        # Emit signal that expense was added
                        self.expense_added.emit()
                        
                        conn.commit()
                        from database.db_config import log_action
                        log_action(self.user['id'], self.user['username'], 'New Expense', 'Expenses', f"{data['category']} - {data['amount']} EGP")
                        QMessageBox.information(self, "Success", "Expense added successfully!")
                        self.load_expenses()
                        
                    except Exception as e:
                        conn.rollback()
                        raise Exception(f"Database error: {str(e)}")
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add expense: {str(e)}")
    
    def open_edit_by_id(self, expense_id):
        """Open edit dialog for a specific expense ID"""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, date, description, amount, category FROM expenses WHERE id=?", (expense_id,))
                expense = cursor.fetchone()
                if not expense:
                    QMessageBox.warning(self, "Error", f"Expense ID {expense_id} not found")
                    return
                
                # Format data for dialog
                row_data = {
                    'id': str(expense['id']),
                    'date': expense['date'],
                    'description': expense['description'],
                    'amount': expense['amount'],
                    'category': expense['category']
                }
                
                dialog = ExpenseDialog(self, row_data)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_data()
                    cursor.execute("""
                        UPDATE expenses 
                        SET date=?, description=?, amount=?, category=?
                        WHERE id=?
                    """, (data['date'], data['description'], data['amount'], data['category'], expense_id))
                    conn.commit()
                    self.load_expenses()
                    self.expense_added.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit expense: {str(e)}")

    def edit_expense(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an expense to edit")
            return
        
        try:
            # Check source
            source = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if source == 'purchase':
                QMessageBox.information(self, "Info", "Purchase invoices can only be edited in the Purchases module.")
                return

            # Get row data
            row_data = {}
            # Columns: ID, Date, Description, Amount, Category
            row_data['id'] = self.table.item(current_row, 0).text()
            row_data['date'] = self.table.item(current_row, 1).text()
            row_data['description'] = self.table.item(current_row, 2).text()
            # Remove currency sign for amount
            amount_text = self.table.item(current_row, 3).text().replace('EGP', '').replace('$', '').strip()
            row_data['amount'] = float(amount_text)
            row_data['category'] = self.table.item(current_row, 4).text()
            
            dialog = ExpenseDialog(self, row_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE expenses 
                        SET date=?, description=?, amount=?, category=?
                        WHERE id=?
                    """, (data['date'], data['description'], data['amount'], data['category'], row_data['id']))
                    conn.commit()
                self.load_expenses()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit expense: {str(e)}")
    
    def apply_filters(self):
        category = self.category_filter.currentText()
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            # Category check
            category_item = self.table.item(row, 4)
            if not category_item: continue
            row_category = category_item.text()
            category_match = (category == "All Categories" or row_category == category)
            
            # Search check
            search_match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    search_match = True
                    break
            
            self.table.setRowHidden(row, not (category_match and search_match))

    def validate_expense_data(self, data):
        """Validate expense data before saving"""
        if not data['amount'] or data['amount'] <= 0:
            QMessageBox.warning(self, "Warning", "Please enter a valid amount")
            return False
            
        if not data['description'].strip():
            QMessageBox.warning(self, "Warning", "Please enter a description")
            return False
            
        return True

    def showEvent(self, a0):
        """Called when the widget becomes visible"""
        super().showEvent(a0)
        if hasattr(self, 'table'):
            self.table.clearSelection()
        
    def hideEvent(self, a0):
        """Called when the widget becomes hidden"""
        super().hideEvent(a0)
        if hasattr(self, 'table'):
            self.table.clearSelection()
