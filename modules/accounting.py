import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                            QComboBox, QFormLayout, QDoubleSpinBox, QDateEdit,
                            QMessageBox)
from PyQt6.QtCore import Qt, QDate
from database.db_config import DatabaseConnection
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Union

class AccountingModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Accounting Module")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)
        
        # Journal Entry Form
        form_group = QWidget()
        form_layout = QFormLayout(form_group)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_edit)
        
        # Reference Number
        self.ref_input = QLineEdit()
        form_layout.addRow("Reference No:", self.ref_input)
        
        # Description
        self.desc_input = QLineEdit()
        form_layout.addRow("Description:", self.desc_input)
        
        layout.addWidget(form_group)
        
        # Journal Entry Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Account", "Description", "Debit", "Credit"])
        self.items_table.setColumnWidth(0, 200)  # Account column
        self.items_table.setColumnWidth(1, 200)  # Description column
        layout.addWidget(self.items_table)
        
        # Add Item Button
        add_item_btn = QPushButton("Add Entry Line")
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #27ae60;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #27ae60;
            }
        """)
        add_item_btn.clicked.connect(self.add_entry_line)
        
        # Totals Display
        totals_layout = QHBoxLayout()
        self.debit_total_label = QLabel("Total Debit: $0.00")
        self.credit_total_label = QLabel("Total Credit: $0.00")
        totals_layout.addWidget(self.debit_total_label)
        totals_layout.addWidget(self.credit_total_label)
        layout.addLayout(totals_layout)
        
        # Save Button
        save_btn = QPushButton("Post Journal Entry")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        save_btn.clicked.connect(self.save_journal_entry)
        
        # Clear Button
        clear_btn = QPushButton("Clear Form")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.clear_form)
        
        # Add buttons to layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(add_item_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Initialize with one empty row
        self.add_entry_line()

    def add_entry_line(self) -> None:
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Account ComboBox
        account_combo = QComboBox()
        self.load_accounts(account_combo)
        self.items_table.setCellWidget(row, 0, account_combo)
        
        # Description
        desc_item = QTableWidgetItem("")
        self.items_table.setItem(row, 1, desc_item)
        
        # Debit Amount
        debit_spin = QDoubleSpinBox()
        debit_spin.setMaximum(999999999.99)
        debit_spin.setDecimals(2)
        debit_spin.valueChanged.connect(self.on_amount_changed)
        self.items_table.setCellWidget(row, 2, debit_spin)
        
        # Credit Amount
        credit_spin = QDoubleSpinBox()
        credit_spin.setMaximum(999999999.99)
        credit_spin.setDecimals(2)
        credit_spin.valueChanged.connect(self.on_amount_changed)
        self.items_table.setCellWidget(row, 3, credit_spin)

    def load_accounts(self, combo: QComboBox) -> None:
        """Load accounts into the combo box"""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, code, name FROM accounts ORDER BY code")
                accounts = cursor.fetchall()
                
                for account in accounts:
                    combo.addItem(f"{account[1]} - {account[2]}", account[0])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load accounts: {str(e)}")

    def round_decimal(self, value: float) -> Decimal:
        """Round a float value to 2 decimal places"""
        dec = Decimal(str(value))
        return dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def on_amount_changed(self) -> None:
        """Update totals when any amount changes"""
        debit_total = Decimal('0.00')
        credit_total = Decimal('0.00')
        
        for row in range(self.items_table.rowCount()):
            debit_spin = self.items_table.cellWidget(row, 2)
            credit_spin = self.items_table.cellWidget(row, 3)
            
            if isinstance(debit_spin, QDoubleSpinBox) and isinstance(credit_spin, QDoubleSpinBox):
                debit_total += self.round_decimal(debit_spin.value())
                credit_total += self.round_decimal(credit_spin.value())
        
        self.debit_total_label.setText(f"Total Debit: ${debit_total:,.2f}")
        self.credit_total_label.setText(f"Total Credit: ${credit_total:,.2f}")
        
        # Use exact decimal comparison
        if abs(debit_total - credit_total) < Decimal('0.01'):
            style = "color: black"
        else:
            style = "color: red"
        self.debit_total_label.setStyleSheet(style)
        self.credit_total_label.setStyleSheet(style)

    def validate_entry(self) -> List[Dict[str, Union[int, str, Decimal]]]:
        """Validate the journal entry and return a list of valid entries"""
        if not self.ref_input.text() or not self.desc_input.text():
            raise ValueError("Reference number and description are required")

        debit_total = Decimal('0.00')
        credit_total = Decimal('0.00')
        entries = []
        has_valid_entry = False

        for row in range(self.items_table.rowCount()):
            account_combo = self.items_table.cellWidget(row, 0)
            debit_spin = self.items_table.cellWidget(row, 2)
            credit_spin = self.items_table.cellWidget(row, 3)
            
            # Skip invalid cells
            if not isinstance(account_combo, QComboBox) or \
               not isinstance(debit_spin, QDoubleSpinBox) or \
               not isinstance(credit_spin, QDoubleSpinBox):
                continue

            # Get values
            debit = self.round_decimal(debit_spin.value())
            credit = self.round_decimal(credit_spin.value())
            desc_item = self.items_table.item(row, 1)
            desc_text = desc_item.text() if desc_item else ""

            # Skip empty entries (both debit and credit are 0)
            if debit == 0 and credit == 0:
                continue

            # Can't have both debit and credit
            if debit > 0 and credit > 0:
                raise ValueError("Entry line cannot have both debit and credit amounts")

            has_valid_entry = True
            debit_total += debit
            credit_total += credit
            
            entries.append({
                'account_id': account_combo.currentData(),
                'description': desc_text,
                'debit': debit,
                'credit': credit
            })

        if not has_valid_entry:
            raise ValueError("At least one valid entry line is required")

        # Convert to string and back to avoid floating point comparison issues
        debit_str = f"{debit_total:.2f}"
        credit_str = f"{credit_total:.2f}"
        debit_normalized = Decimal(debit_str)
        credit_normalized = Decimal(credit_str)

        if debit_normalized != credit_normalized:
            raise ValueError(f"Journal entry must balance. Difference: ${abs(debit_normalized - credit_normalized):,.2f}")

        return entries

    def save_journal_entry(self) -> None:
        """Save the journal entry to the database"""
        try:
            entries = self.validate_entry()
            
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Create journal entry header
                cursor.execute("""
                    INSERT INTO journal_entries (date, reference_no, description)
                    VALUES (?, ?, ?)
                """, (
                    self.date_edit.date().toString("yyyy-MM-dd"),
                    self.ref_input.text(),
                    self.desc_input.text()
                ))
                
                journal_entry_id = cursor.lastrowid
                
                # Create journal entry items and update general ledger
                for entry in entries:
                    # Convert Decimal values to float for SQLite
                    debit = float(entry['debit'])
                    credit = float(entry['credit'])
                    
                    # Insert journal entry item
                    cursor.execute("""
                        INSERT INTO journal_entry_items 
                        (journal_entry_id, account_id, description, debit, credit)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        journal_entry_id,
                        entry['account_id'],
                        entry['description'],
                        debit,
                        credit
                    ))
                    
                    # Update account balance based on account type
                    cursor.execute("""
                        UPDATE accounts 
                        SET balance = balance + CASE
                            WHEN type IN ('asset', 'expense') THEN (? - ?)
                            ELSE (? - ?)
                        END
                        WHERE id = ?
                    """, (debit, credit, credit, debit, entry['account_id']))
                    
                    # Add to general ledger
                    cursor.execute("""
                        INSERT INTO general_ledger
                        (account_id, journal_entry_id, date, description, debit, credit)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        entry['account_id'],
                        journal_entry_id,
                        self.date_edit.date().toString("yyyy-MM-dd"),
                        entry['description'],
                        debit,
                        credit
                    ))

                QMessageBox.information(self, "Success", "Journal entry posted successfully")
                self.clear_form()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            if isinstance(e, sqlite3.Error):
                print(f"Database error: {str(e)}")

    def clear_form(self) -> None:
        """Clear the form after successful entry"""
        self.date_edit.setDate(QDate.currentDate())
        self.ref_input.clear()
        self.desc_input.clear()
        self.items_table.setRowCount(0)
        self.add_entry_line()
        self.on_amount_changed()

    def showEvent(self, a0):
        """Called when the widget becomes visible"""
        super().showEvent(a0)
        if hasattr(self, 'items_table'):
            self.items_table.clearSelection()
        
    def hideEvent(self, a0):
        """Called when the widget becomes hidden"""
        super().hideEvent(a0)
        if hasattr(self, 'items_table'):
            self.items_table.clearSelection()
