import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                            QFormLayout, QMessageBox, QDialog, QComboBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database.db_config import DatabaseConnection
from datetime import datetime
from modules.theme import COLORS, get_button_style

class RevenueModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("Revenue Management")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']};")
        layout.addWidget(header)

        # Filters
        filter_layout = QHBoxLayout()
        
        # Month Filter
        self.month_filter = QComboBox()
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Add last 12 months
        for i in range(12):
            month = current_month - i
            year = current_year
            if month <= 0:
                month += 12
                year -= 1
            month_str = f"{year}-{month:02d}"
            self.month_filter.addItem(datetime(year, month, 1).strftime("%B %Y"), month_str)
        
        self.month_filter.currentIndexChanged.connect(self.load_revenue)
        filter_layout.addWidget(QLabel("Select Month:"))
        filter_layout.addWidget(self.month_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Customer", "Amount", "Status"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(3, 150)
        
        layout.addWidget(self.table)
        self.load_revenue()

    def load_revenue(self):
        month_str = self.month_filter.currentData()
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.id, s.date, c.name as customer, s.total_amount, s.status, s.payment_type
                    FROM sales_invoices s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    WHERE s.date LIKE ?
                    ORDER BY s.date DESC
                """, (f"{month_str}%",))
                sales = cursor.fetchall()
                
                self.table.setRowCount(len(sales))
                for i, sale in enumerate(sales):
                    self.table.setItem(i, 0, QTableWidgetItem(str(sale['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(sale['date']))
                    self.table.setItem(i, 2, QTableWidgetItem(sale['customer'] or "Walking Customer"))
                    
                    amt_text = f"EGP {sale['total_amount']:,.2f}\n[{sale['payment_type'].title()}]"
                    amt_item = QTableWidgetItem(amt_text)
                    amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, 3, amt_item)
                    
                    status_item = QTableWidgetItem(sale['status'].upper())
                    if sale['status'] == 'paid':
                        status_item.setForeground(QColor("#10b981"))
                    else:
                        status_item.setForeground(QColor(COLORS['accent']))
                    self.table.setItem(i, 4, status_item)
                    
                    self.table.setRowHeight(i, 60)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load revenue: {str(e)}")
