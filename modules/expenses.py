import sys
import os
from pathlib import Path
from PyQt6.QtCore import pyqtSignal

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                            QFormLayout, QMessageBox, QDialog, QComboBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from database.db_config import DatabaseConnection
from datetime import datetime

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
            "Other"
        ])
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self.category_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
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
    
    def __init__(self, auto_accounting):
        super().__init__()
        self.auto_accounting = auto_accounting
        self.init_ui()
        self.load_expenses()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Add header
        header = QLabel("Expense Management")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1C1008; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid #E8DDD0; padding-bottom: 8px;")
        layout.addWidget(header)
        
        # Create top buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Expense")
        
        # Style buttons
        button_style = "color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;"
        self.add_btn.setStyleSheet(f"background-color: #27AE60; {button_style}")
        
        # Add buttons to layout with spacing
        btn_layout.setSpacing(10)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Description", "Amount", "Category"])
        
        # Make table read-only
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Connect buttons
        self.add_btn.clicked.connect(self.add_expense)
        self.table.itemDoubleClicked.connect(self.edit_expense)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_expenses(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, date, description, amount, category 
                    FROM expenses
                    ORDER BY date DESC
                """)
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
                    amount_item = QTableWidgetItem(f"${expense['amount']:.2f}")
                    amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 3, amount_item)
                    
                    # Category column
                    category_item = QTableWidgetItem(expense['category'])
                    category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 4, category_item)
                    
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
                        QMessageBox.information(self, "Success", "Expense added successfully!")
                        self.load_expenses()
                        
                    except Exception as e:
                        conn.rollback()
                        raise Exception(f"Database error: {str(e)}")
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add expense: {str(e)}")
    
    def edit_expense(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an expense to edit")
            return
        
        try:
            # Get row data
            row_data = {}
            # Columns: ID, Date, Description, Amount, Category
            row_data['id'] = self.table.item(current_row, 0).text()
            row_data['date'] = self.table.item(current_row, 1).text()
            row_data['description'] = self.table.item(current_row, 2).text()
            # Remove $ sign for amount
            amount_text = self.table.item(current_row, 3).text().replace('$', '')
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
