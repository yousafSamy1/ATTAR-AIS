# Python Standard Libraries
import sys              # System-specific parameters and functions
import os               # Operating system interface
from pathlib import Path  # Object-oriented filesystem paths

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# PyQt6 GUI Components
from PyQt6.QtWidgets import (
    QWidget,           # Base widget class
    QVBoxLayout,       # Vertical layout manager
    QHBoxLayout,       # Horizontal layout manager
    QPushButton,       # Standard push button
    QLabel,            # Text or image display
    QLineEdit,         # Single-line text input
    QTableWidget,      # Table/grid widget
    QTableWidgetItem,  # Table cell item
    QFormLayout,       # Form-style layout
    QMessageBox,       # Modal message dialog
    QDialog,           # Dialog window class
    QHeaderView        # Header view for tables
)
from PyQt6.QtCore import (
    Qt,               # Core non-widget functionality
    pyqtSignal        # Signal/slot communication
)

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler
from modules.theme import COLORS, get_button_style

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Customer")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # Create form fields
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        
        # Add fields to layout
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Address:", self.address_edit)
        
        # Add buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(get_button_style('accent'))
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet(get_button_style('bg_mid'))
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
        self.setLayout(layout)
        
        # Fill data if editing
        if customer_data:
            self.name_edit.setText(customer_data['name'])
            self.phone_edit.setText(customer_data['phone'])
            self.email_edit.setText(customer_data['email'])
            self.address_edit.setText(customer_data['address'])
    
    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'phone': self.phone_edit.text(),
            'email': self.email_edit.text(),
            'address': self.address_edit.text()
        }

class CustomersModule(QWidget):
    customer_added = pyqtSignal()  # Signal to emit when customer is added
    
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)
        
        # Add header
        header = QLabel("Customer Management")
        header.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        main_layout.addWidget(header)
        
        # Create button layout
        btn_layout = QHBoxLayout()
        
        # Create buttons and style using theme helpers
        self.add_btn = QPushButton("➕ Add Customer")
        self.edit_btn = QPushButton("✏️ Edit Customer")
        self.delete_btn = QPushButton("🗑️ Delete Customer")
        
        self.add_btn.setFixedWidth(200)
        self.edit_btn.setFixedWidth(200)
        self.delete_btn.setFixedWidth(200)
        
        self.add_btn.setStyleSheet(get_button_style('green'))
        self.edit_btn.setStyleSheet(get_button_style('blue'))
        self.delete_btn.setStyleSheet(get_button_style('red'))
        
        # Add buttons to layout
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
        
        # Create search layout
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search customers by name, phone, email...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 14px;
                background-color: {COLORS['bg_card']};
                margin-top: 10px;
                margin-bottom: 5px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.search_input)
        
        main_layout.addLayout(search_layout)
        
        # Create and setup table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Email", "Address"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Make table read-only
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configure table columns
        header = self.table.horizontalHeader()
        if header:
            header.setMinimumSectionSize(50)
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Address
        
        # Set column widths
        self.table.setColumnWidth(0, 50)    # ID
        self.table.setColumnWidth(1, 200)   # Name
        self.table.setColumnWidth(2, 120)   # Phone
        self.table.setColumnWidth(3, 200)   # Email
        self.table.setColumnWidth(4, 250)   # Address
        
        # Add table to main layout
        main_layout.addWidget(self.table)
        
        # Connect button signals
        # Robust role check
        is_admin = False
        is_staff = False
        if self.user and hasattr(self.user, 'get'):
            role = self.user.get('role')
            is_admin = (role == 'admin')
            is_staff = (role in ['admin', 'staff'])
            
        self.add_btn.setVisible(is_staff)
        self.edit_btn.setVisible(is_staff)
        self.delete_btn.setVisible(is_admin)
        
        self.add_btn.clicked.connect(self.add_customer)
        self.edit_btn.clicked.connect(self.edit_customer)
        self.delete_btn.clicked.connect(self.delete_customer)
        self.table.itemDoubleClicked.connect(self.edit_customer)
    
    def load_customers(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, phone, email, address 
                    FROM customers
                    ORDER BY name
                """)
                customers = cursor.fetchall()
                
                self.table.setRowCount(len(customers))
                for row, customer in enumerate(customers):
                    for col, value in enumerate(customer):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        self.table.setItem(row, col, item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customers: {str(e)}")
    
    def add_customer(self):
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO customers (name, phone, email, address)
                        VALUES (?, ?, ?, ?)
                    """, (data['name'], data['phone'], data['email'], data['address']))
                    conn.commit()
                self.load_customers()
                self.customer_added.emit()  # Emit signal when customer is added
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add customer: {str(e)}")
    
    def edit_customer(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a customer to edit")
            return
        
        try:
            # Get row data
            row_data = {}
            for col, key in enumerate(['id', 'name', 'phone', 'email', 'address']):
                item = self.table.item(current_row, col)
                if not item:
                    raise ValueError(f"Invalid data in row: {key} is missing")
                row_data[key] = item.text()
            
            dialog = CustomerDialog(self, row_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE customers 
                        SET name=?, phone=?, email=?, address=?
                        WHERE id=?
                    """, (data['name'], data['phone'], data['email'], data['address'], row_data['id']))
                    conn.commit()
                self.load_customers()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit customer: {str(e)}")
    
    def filter_customers(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
    def delete_customer(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a customer to delete")
            return
        
        try:
            id_item = self.table.item(current_row, 0)
            if not id_item:
                raise ValueError("Could not get customer ID")
            
            customer_id = id_item.text()
            name_item = self.table.item(current_row, 1)
            customer_name = name_item.text() if name_item else "this customer"
            
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {customer_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
                    conn.commit()
                self.load_customers()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete customer: {str(e)}")

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
