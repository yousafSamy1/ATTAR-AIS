
import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QComboBox, QFormLayout, QDoubleSpinBox, QDateEdit,
                             QMessageBox, QFrame, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database.db_config import DatabaseConnection
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Union

from modules.theme import COLORS, get_current_theme, get_button_style
from modules.localization import tr

class AccountingModule(QWidget):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        
    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(tr('accounting'))
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)
        
        # Journal Entry Form Card
        self.form_card = QFrame()
        self.form_card.setObjectName("FormCard")
        self.form_card.setStyleSheet(f"""
            QFrame#FormCard {{
                background: {COLORS['bg_card']}; 
                border-radius: 20px; 
                border: 1.5px solid {COLORS['border']};
            }}
            QLabel {{
                background: transparent;
                color: {COLORS['text_sub']};
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
        """)
        form_vbox = QVBoxLayout(self.form_card)
        form_vbox.setContentsMargins(30, 30, 30, 30)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumWidth(250)
        form_layout.addRow(f"{tr('date')}:", self.date_edit)
        
        # Reference Number
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. JE-001")
        form_layout.addRow(f"{tr('reference')}:", self.ref_input)
        
        # Description
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Enter transaction summary...")
        form_layout.addRow(f"{tr('description')}:", self.desc_input)
        
        form_vbox.addLayout(form_layout)
        layout.addWidget(self.form_card)
        
        # Table Section Header
        tl = QLabel("ENTRY LINES")
        tl.setStyleSheet(f"color: {COLORS['accent']}; font-weight: 900; font-size: 11px; letter-spacing: 2px; background: transparent; border: none;")
        layout.addWidget(tl)

        # Journal Entry Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Type", "Description", "Debit", "Credit"])
        
        # Explicit Header Styling
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setMinimumHeight(50)
        
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setShowGrid(False)
        self.items_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                alternate-background-color: {COLORS['bg'] if get_current_theme() == 'dark' else '#F8FAFC'};
                border: 1.5px solid {COLORS['border']};
                border-radius: 15px;
            }}
            QTableWidget::item {{
                color: {COLORS['text_main']};
                border: none;
            }}
        """)
        layout.addWidget(self.items_table)
        
        # Totals Card
        totals_card = QFrame()
        totals_card.setStyleSheet(f"background: {COLORS['bg_card']}; border-radius: 12px; border: 1.5px solid {COLORS['border']};")
        th = QHBoxLayout(totals_card)
        th.setContentsMargins(20, 15, 20, 15)
        
        self.debit_total_label = QLabel("Total Debit: EGP 0.00")
        self.debit_total_label.setStyleSheet(f"color: {COLORS['accent']}; font-weight: 900; font-size: 14px; background: transparent; border: none;")
        
        self.credit_total_label = QLabel("Total Credit: EGP 0.00")
        self.credit_total_label.setStyleSheet(f"color: {COLORS['blue']}; font-weight: 900; font-size: 14px; background: transparent; border: none;")
        
        th.addWidget(self.debit_total_label)
        th.addStretch()
        th.addWidget(self.credit_total_label)
        layout.addWidget(totals_card)
        
        # Actions
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        add_item_btn = QPushButton("➕ Add Entry Line")
        add_item_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_item_btn.setStyleSheet(get_button_style('accent', padding="12px 25px"))
        add_item_btn.clicked.connect(self.add_entry_line)
        
        save_btn = QPushButton("💾 Post Journal Entry")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(get_button_style('blue', padding="12px 25px"))
        save_btn.clicked.connect(self.save_journal_entry)
        
        clear_btn = QPushButton("🧹 Clear Form")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(get_button_style('red', padding="12px 25px"))
        clear_btn.clicked.connect(self.clear_form)
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Select Adjusting Entry Template...",
            "Accrued Salaries",
            "Accrued Rent",
            "Utilities Payable",
            "Depreciation",
            "Bad Debt"
        ])
        self.template_combo.setStyleSheet(get_button_style('bg_mid', padding="12px 15px"))
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        
        button_layout.addWidget(self.template_combo)
        button_layout.addWidget(add_item_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.add_entry_line()
        self.add_entry_line()

    def apply_template(self, index):
        if index == 0: return
        
        template = self.template_combo.currentText()
        self.clear_form()
        self.ref_input.setText(f"ADJ-{datetime.now().strftime('%m%d')}")
        
        # Add two lines explicitly (since clear_form leaves it empty)
        self.add_entry_line()
        self.add_entry_line()
        
        debit_account = None
        credit_account = None
        desc = ""
        
        if template == "Accrued Salaries":
            debit_account = "6000"  # Salaries Expense
            credit_account = "2100" # Salaries Payable
            desc = "Accrued salaries for the month"
        elif template == "Accrued Rent":
            debit_account = "6100"  # Rent Expense
            credit_account = "2200" # Rent Payable
            desc = "Accrued rent for the month"
        elif template == "Utilities Payable":
            debit_account = "6200"  # Utilities Expense
            credit_account = "2300" # Utilities Payable
            desc = "Accrued utilities for the month"
        elif template == "Depreciation":
            debit_account = "6700"  # Depreciation Expense
            credit_account = "1350" # Accumulated Depreciation
            desc = "Monthly depreciation expense"
        elif template == "Bad Debt":
            debit_account = "6600"  # Bad Debt Expense
            credit_account = "1100" # Accounts Receivable
            desc = "Write-off bad debt"
            
        self.desc_input.setText(desc)
        
        # Set first row (Debit)
        account_combo_1 = self.items_table.cellWidget(0, 0)
        desc_input_1 = self.items_table.cellWidget(0, 1)
        if account_combo_1:
            index1 = account_combo_1.findData(debit_account)
            if index1 >= 0: account_combo_1.setCurrentIndex(index1)
        if desc_input_1: desc_input_1.setText(desc)
        
        # Set second row (Credit)
        account_combo_2 = self.items_table.cellWidget(1, 0)
        desc_input_2 = self.items_table.cellWidget(1, 1)
        if account_combo_2:
            index2 = account_combo_2.findData(credit_account)
            if index2 >= 0: account_combo_2.setCurrentIndex(index2)
        if desc_input_2: desc_input_2.setText(desc)
        
        self.template_combo.setCurrentIndex(0)

    def add_entry_line(self) -> None:
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setRowHeight(row, 50)
        
        table_widget_style = f"""
            border: none; 
            background: transparent; 
            color: {COLORS['text_main']};
            padding: 5px;
            font-size: 14px;
        """
        
        account_combo = QComboBox()
        account_combo.setStyleSheet(table_widget_style)
        self.load_accounts(account_combo)
        self.items_table.setCellWidget(row, 0, account_combo)
        
        desc_item = QTableWidgetItem("")
        self.items_table.setItem(row, 1, desc_item)
        
        debit_spin = QDoubleSpinBox()
        debit_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        debit_spin.setStyleSheet(table_widget_style + f"font-weight: bold; color: {COLORS['accent']};")
        debit_spin.setMaximum(999999999.99)
        debit_spin.setDecimals(2)
        debit_spin.valueChanged.connect(self.on_amount_changed)
        self.items_table.setCellWidget(row, 2, debit_spin)
        
        credit_spin = QDoubleSpinBox()
        credit_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        credit_spin.setStyleSheet(table_widget_style + f"font-weight: bold; color: {COLORS['blue']};")
        credit_spin.setMaximum(999999999.99)
        credit_spin.setDecimals(2)
        credit_spin.valueChanged.connect(self.on_amount_changed)
        self.items_table.setCellWidget(row, 3, credit_spin)

    def load_accounts(self, combo: QComboBox) -> None:
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT code, name FROM accounts ORDER BY code")
                accounts = cursor.fetchall()
                for acc in accounts:
                    combo.addItem(f"{acc['code']} - {acc['name']}", acc['code'])
        except Exception as e:
            print(f"Error loading accounts: {e}")

    def on_amount_changed(self, _) -> None:
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        for row in range(self.items_table.rowCount()):
            debit_widget = self.items_table.cellWidget(row, 2)
            credit_widget = self.items_table.cellWidget(row, 3)
            if isinstance(debit_widget, QDoubleSpinBox):
                total_debit += Decimal(str(debit_widget.value()))
            if isinstance(credit_widget, QDoubleSpinBox):
                total_credit += Decimal(str(credit_widget.value()))
        self.debit_total_label.setText(f"Total Debit: EGP {total_debit:,.2f}")
        self.credit_total_label.setText(f"Total Credit: EGP {total_credit:,.2f}")

    def save_journal_entry(self) -> None:
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        lines = []
        for row in range(self.items_table.rowCount()):
            acc_combo = self.items_table.cellWidget(row, 0)
            desc_item = self.items_table.item(row, 1)
            debit_widget = self.items_table.cellWidget(row, 2)
            credit_widget = self.items_table.cellWidget(row, 3)
            acc_code = acc_combo.currentData()
            desc = desc_item.text() if desc_item else ""
            debit = Decimal(str(debit_widget.value()))
            credit = Decimal(str(credit_widget.value()))
            if debit > 0 or credit > 0:
                lines.append({'account_code': acc_code, 'description': desc or self.desc_input.text(), 'debit': debit, 'credit': credit})
                total_debit += debit
                total_credit += credit
        if total_debit != total_credit:
            QMessageBox.warning(self, "Unbalanced Entry", f"Debits (EGP {total_debit:,.2f}) must equal Credits (EGP {total_credit:,.2f})")
            return
        if not lines:
            QMessageBox.warning(self, "Empty Entry", "Please add at least one transaction line.")
            return
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                # Use correct table name 'journal_entries' and correct columns
                cursor.execute("INSERT INTO journal_entries (date, reference_no, description) VALUES (?, ?, ?)", 
                             (self.date_edit.date().toString(Qt.DateFormat.ISODate), self.ref_input.text(), self.desc_input.text()))
                header_id = cursor.lastrowid
                
                for line in lines:
                    # Use correct table name 'journal_entry_items' and correct columns
                    cursor.execute("INSERT INTO journal_entry_items (journal_entry_id, account_id, description, debit, credit) VALUES (?, (SELECT id FROM accounts WHERE code=?), ?, ?, ?)", 
                                 (header_id, line['account_code'], line['description'], float(line['debit']), float(line['credit'])))
                conn.commit()
                QMessageBox.information(self, "Success", "Journal entry posted successfully!")
                self.clear_form()
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to save entry: {e}")

    def clear_form(self) -> None:
        self.ref_input.clear()
        self.desc_input.clear()
        self.items_table.setRowCount(0)
        self.add_entry_line()
        self.add_entry_line()
        self.on_amount_changed(0)
