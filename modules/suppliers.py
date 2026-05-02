import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                            QFormLayout, QMessageBox, QDialog, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db_config import DatabaseConnection

class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Supplier")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # Create form fields
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        
        # Add form validation
        self.name_edit.setPlaceholderText("Enter supplier name")
        self.phone_edit.setPlaceholderText("Enter phone number")
        self.email_edit.setPlaceholderText("Enter email address")
        self.address_edit.setPlaceholderText("Enter address")
        
        # Add fields to layout
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Address:", self.address_edit)
        
        # Add buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow("", button_box)
        
        self.setLayout(layout)
        
        # Fill data if editing
        if supplier_data:
            self.name_edit.setText(supplier_data.get('name', ''))
            self.phone_edit.setText(supplier_data.get('phone', ''))
            self.email_edit.setText(supplier_data.get('email', ''))
            self.address_edit.setText(supplier_data.get('address', ''))
    
    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Supplier name is required")
            self.name_edit.setFocus()
            return
        
        self.accept()
    
    def get_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'address': self.address_edit.text().strip()
        }

class SuppliersModule(QWidget):
    supplier_added = pyqtSignal()  # Signal to emit when supplier is added
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_suppliers()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create top buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Supplier")
        self.edit_btn = QPushButton("Edit Supplier")
        self.delete_btn = QPushButton("Delete Supplier")
        
        # Style buttons
        button_style = "color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;"
        self.add_btn.setStyleSheet(f"background-color: #27AE60; {button_style}")
        self.edit_btn.setStyleSheet(f"background-color: #2471A3; {button_style}")
        self.delete_btn.setStyleSheet(f"background-color: #C0392B; {button_style}")
        
        # Add buttons to layout
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
        
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
            header.setStretchLastSection(True)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Connect button signals
        self.add_btn.clicked.connect(self.add_supplier)
        self.edit_btn.clicked.connect(self.edit_supplier)
        self.delete_btn.clicked.connect(self.delete_supplier)
        self.table.itemDoubleClicked.connect(self.edit_supplier)
        
        main_layout.addWidget(self.table)
    
    def load_suppliers(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, phone, email, address 
                    FROM suppliers
                    ORDER BY name
                """)
                suppliers = cursor.fetchall()
                
                self.table.setRowCount(len(suppliers))
                for row, supplier in enumerate(suppliers):
                    for col, value in enumerate(supplier):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        self.table.setItem(row, col, item)
                
                # Adjust column widths
                self.table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load suppliers: {str(e)}")
    
    def add_supplier(self):
        try:
            dialog = SupplierDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO suppliers (name, phone, email, address)
                        VALUES (?, ?, ?, ?)
                    """, (data['name'], data['phone'], data['email'], data['address']))
                self.load_suppliers()
                QMessageBox.information(self, "Success", "Supplier added successfully")
                self.supplier_added.emit()  # Emit signal when supplier is added
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add supplier: {str(e)}")
    
    def edit_supplier(self):
        try:
            current_row = self.table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Warning", "Please select a supplier to edit")
                return
            
            # Get row data safely
            row_data = {}
            for col, key in enumerate(['id', 'name', 'phone', 'email', 'address']):
                item = self.table.item(current_row, col)
                if not item:
                    QMessageBox.warning(self, "Error", f"Invalid data in row: {key} is missing")
                    return
                row_data[key] = item.text()
            
            dialog = SupplierDialog(self, row_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE suppliers 
                        SET name=?, phone=?, email=?, address=?
                        WHERE id=?
                    """, (data['name'], data['phone'], data['email'], data['address'], row_data['id']))
                self.load_suppliers()
                QMessageBox.information(self, "Success", "Supplier updated successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update supplier: {str(e)}")
    
    def delete_supplier(self):
        try:
            current_row = self.table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Warning", "Please select a supplier to delete")
                return
            
            id_item = self.table.item(current_row, 0)
            name_item = self.table.item(current_row, 1)
            if not id_item:
                QMessageBox.warning(self, "Error", "Could not get supplier ID")
                return
            
            supplier_name = name_item.text() if name_item else "this supplier"
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {supplier_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM suppliers WHERE id=?", (id_item.text(),))
                self.load_suppliers()
                QMessageBox.information(self, "Success", "Supplier deleted successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete supplier: {str(e)}")

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