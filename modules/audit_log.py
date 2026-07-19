import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QHeaderView, 
                            QComboBox, QDateEdit, QLineEdit)
from PyQt6.QtCore import Qt, QDate
from database.db_config import DatabaseConnection
from modules.theme import COLORS

class AuditLogModule(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.user = current_user
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Security Audit Logs")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']};")
        layout.addWidget(header)

        # Filters
        filter_layout = QHBoxLayout()
        
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.load_logs)
        
        self.user_filter = QLineEdit()
        self.user_filter.setPlaceholderText("Filter by Username...")
        self.user_filter.textChanged.connect(self.load_logs)
        
        self.module_filter = QComboBox()
        self.module_filter.addItems(["All Modules", "Auth", "Sales", "Purchases", "Inventory", "Expenses", "Revenue", "Products"])
        self.module_filter.currentIndexChanged.connect(self.load_logs)

        filter_layout.addWidget(QLabel("Date:"))
        filter_layout.addWidget(self.date_filter)
        filter_layout.addWidget(QLabel("User:"))
        filter_layout.addWidget(self.user_filter)
        filter_layout.addWidget(QLabel("Module:"))
        filter_layout.addWidget(self.module_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "User", "Action", "Module", "Details"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        self.load_logs()

    def load_logs(self):
        date_str = self.date_filter.date().toString("yyyy-MM-dd")
        user_str = self.user_filter.text()
        module_str = self.module_filter.currentText()
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                query = "SELECT timestamp, username, action, module, details FROM audit_logs WHERE timestamp LIKE ?"
                params = [f"{date_str}%"]
                
                if user_str:
                    query += " AND username LIKE ?"
                    params.append(f"%{user_str}%")
                
                if module_str != "All Modules":
                    query += " AND module = ?"
                    params.append(module_str)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                logs = cursor.fetchall()
                
                self.table.setRowCount(len(logs))
                for i, log in enumerate(logs):
                    self.table.setItem(i, 0, QTableWidgetItem(log['timestamp']))
                    self.table.setItem(i, 1, QTableWidgetItem(log['username']))
                    self.table.setItem(i, 2, QTableWidgetItem(log['action']))
                    self.table.setItem(i, 3, QTableWidgetItem(log['module']))
                    self.table.setItem(i, 4, QTableWidgetItem(log['details'] or ""))
                    
        except Exception as e:
            print(f"Error loading audit logs: {e}")
