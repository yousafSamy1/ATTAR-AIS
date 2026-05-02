import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                            QSpinBox, QDoubleSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from database.db_config import DatabaseConnection

class InventoryModule(QWidget):
    product_deleted = pyqtSignal(int)  # Signal emitted when a product is deleted
    product_added = pyqtSignal()  # Signal emitted when a product is added
    product_updated = pyqtSignal()  # Signal emitted when a product is updated
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_products()
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_products)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header with modern styling
        header = QLabel("Inventory Management")
        header.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(header)

        # Add Product Form
        self.form_layout = QVBoxLayout()
        self.form_layout.setSpacing(15)
        
        # Input fields styling
        input_style = """
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
            }
        """
        
        # Product Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Product Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        self.form_layout.addLayout(name_layout)

        # Product Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_input = QLineEdit()
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        self.form_layout.addLayout(desc_layout)

        # Unit Price
        price_layout = QHBoxLayout()
        price_label = QLabel("Unit Price:")
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.01)
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price_input)
        self.form_layout.addLayout(price_layout)

        # Quantity
        qty_layout = QHBoxLayout()
        qty_label = QLabel("Initial Quantity:")
        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(0)
        self.qty_input.setMaximum(9999)
        qty_layout.addWidget(qty_label)
        qty_layout.addWidget(self.qty_input)
        self.form_layout.addLayout(qty_layout)

        # Minimum Quantity
        min_qty_layout = QHBoxLayout()
        min_qty_label = QLabel("Minimum Quantity:")
        self.min_qty_input = QSpinBox()
        self.min_qty_input.setMinimum(0)
        self.min_qty_input.setMaximum(9999)
        min_qty_layout.addWidget(min_qty_label)
        min_qty_layout.addWidget(self.min_qty_input)
        self.form_layout.addLayout(min_qty_layout)

        # Add Product Button with modern styling
        self.add_btn = QPushButton("Add Product")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        self.add_btn.clicked.connect(self.add_product)
        self.form_layout.addWidget(self.add_btn)

        # Apply input styling
        self.setStyleSheet(input_style)

        layout.addLayout(self.form_layout)

        # Products Table with modern styling
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Unit Price", "Quantity", "Min. Quantity"])
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.products_table.setStyleSheet("""
            QTableWidget {
                background-color: #2c3e50;
                gridline-color: #34495e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QTableWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.products_table)

        # Action Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Edit button with modern styling
        edit_btn = QPushButton("Edit Selected")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
        """)
        edit_btn.clicked.connect(self.edit_selected_product)
        buttons_layout.addWidget(edit_btn)

        # Delete button with modern styling
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_product)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)    def edit_selected_product(self):
        selected_rows = self.products_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a product to edit")
            return

        row = self.products_table.currentRow()
        
        try:
            # Get all necessary items first
            id_item = self.products_table.item(row, 0)
            name_item = self.products_table.item(row, 1)
            desc_item = self.products_table.item(row, 2)
            price_item = self.products_table.item(row, 3)
            qty_item = self.products_table.item(row, 4)
            min_qty_item = self.products_table.item(row, 5)
            
            # Check if any item is None or not a QTableWidgetItem
            if not all([isinstance(x, QTableWidgetItem) for x in [id_item, name_item, desc_item, price_item, qty_item, min_qty_item]]):
                QMessageBox.warning(self, "Error", "Could not get complete product information")
                return

            try:
                product_id = int(id_item.data(Qt.ItemDataRole.DisplayRole))
                current_name = name_item.data(Qt.ItemDataRole.DisplayRole)
                current_desc = desc_item.data(Qt.ItemDataRole.DisplayRole)
                current_price = float(price_item.data(Qt.ItemDataRole.DisplayRole).replace("$", ""))
                current_qty = int(qty_item.data(Qt.ItemDataRole.DisplayRole))
                current_min_qty = int(min_qty_item.data(Qt.ItemDataRole.DisplayRole))
            except (ValueError, AttributeError) as e:
                QMessageBox.warning(self, "Error", f"Invalid data format: {str(e)}")
                return

            # Fill the form with current values
            self.name_input.setText(current_name)
            self.desc_input.setText(current_desc)
            self.price_input.setValue(current_price)
            self.qty_input.setValue(current_qty)
            self.min_qty_input.setValue(current_min_qty)
            
            # Hide add button
            self.add_btn.hide()
            
            # Create and show update button
            if not hasattr(self, 'update_btn') or self.update_btn is None:
                self.update_btn = QPushButton("Update Product")
                self.update_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12;
                        color: white;
                        padding: 12px 20px;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: bold;
                        min-width: 120px;
                        margin-top: 10px;
                    }
                    QPushButton:hover {
                        background-color: #d68910;
                    }
                    QPushButton:pressed {
                        background-color: #b9770e;
                    }
                """)
                self.update_btn.clicked.connect(lambda: self.update_product(product_id))
                self.form_layout.addWidget(self.update_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing product: {str(e)}")

    def update_product(self, product_id):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products 
                    SET name=?, description=?, unit_price=?, quantity=?, minimum_quantity=?
                    WHERE id=?
                """, (
                    self.name_input.text().strip(),
                    self.desc_input.text().strip(),
                    self.price_input.value(),
                    self.qty_input.value(),
                    self.min_qty_input.value(),
                    product_id
                ))

            QMessageBox.information(self, "Success", "Product updated successfully!")
            
            # Clear form
            self.name_input.clear()
            self.desc_input.clear()
            self.price_input.setValue(0.01)
            self.qty_input.setValue(0)
            self.min_qty_input.setValue(0)
            
            # Remove update button and show add button
            if hasattr(self, 'update_btn') and self.update_btn is not None:
                self.update_btn.deleteLater()
                self.update_btn = None
            
            self.add_btn.show()
            
            # Reload products
            self.load_products()
            # Emit signal for product updated
            self.product_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating product: {str(e)}")

    def delete_selected_product(self):
        selected_rows = self.products_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a product to delete")
            return

        row = self.products_table.currentRow()
        
        try:
            id_item = self.products_table.item(row, 0)
            name_item = self.products_table.item(row, 1)
            
            # Check if items exist and are QTableWidgetItems
            if not all([isinstance(x, QTableWidgetItem) for x in [id_item, name_item]]):
                QMessageBox.warning(self, "Error", "Could not get product information")
                return
            
            try:
                product_id = int(id_item.data(Qt.ItemDataRole.DisplayRole))
                product_name = name_item.data(Qt.ItemDataRole.DisplayRole)
            except (ValueError, AttributeError) as e:
                QMessageBox.warning(self, "Error", f"Invalid data format: {str(e)}")
                return

            reply = QMessageBox.question(self, 'Confirm Delete',
                                       f'Are you sure you want to delete product "{product_name}"?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    with DatabaseConnection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))

                    QMessageBox.information(self, "Success", "Product deleted successfully!")
                    self.load_products()

                    # Emit the product_deleted signal
                    self.product_deleted.emit(product_id)

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error deleting product: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error accessing product data: {str(e)}")

    def load_products(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products ORDER BY name")
                products = cursor.fetchall()

                self.products_table.setRowCount(len(products))
                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        item = QTableWidgetItem(str(value))                        # Make all columns read-only
                        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                        if j == 3:  # Format unit price as currency
                            item = QTableWidgetItem(f"${float(value):.2f}")
                        item.setBackground(QColor("#393939"))  # Set dark background for all rows
                        item.setForeground(QColor("white"))  # Set white text for better contrast
                        self.products_table.setItem(i, j, item)

                # Highlight low stock items with a different color
                for row in range(self.products_table.rowCount()):
                    item_qty = self.products_table.item(row, 4)
                    item_min_qty = self.products_table.item(row, 5)
                    
                    if isinstance(item_qty, QTableWidgetItem) and isinstance(item_min_qty, QTableWidgetItem):
                        try:
                            quantity = int(item_qty.data(Qt.ItemDataRole.DisplayRole))
                            min_quantity = int(item_min_qty.data(Qt.ItemDataRole.DisplayRole))
                            
                            if quantity <= min_quantity:
                                for col in range(self.products_table.columnCount()):
                                    item = self.products_table.item(row, col)
                                    if isinstance(item, QTableWidgetItem):
                                        item.setBackground(QColor("#662222"))  # Darker red for low stock
                                        item.setForeground(QColor("white"))  # Keep white text
                        except (ValueError, AttributeError):
                            continue

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading products: {str(e)}")

    def showEvent(self, a0):
        """Called when the widget becomes visible"""
        super().showEvent(a0)
        self.load_products()  # Refresh data when widget becomes visible

    def hideEvent(self, a0):
        """Called when the widget becomes hidden"""
        super().hideEvent(a0)
        self.refresh_timer.stop()  # Stop refresh timer when widget is hidden

    def add_product(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Product name is required")
            return

        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO products (name, description, unit_price, quantity, minimum_quantity)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.name_input.text().strip(),
                    self.desc_input.text().strip(),
                    self.price_input.value(),
                    self.qty_input.value(),
                    self.min_qty_input.value()
                ))

            QMessageBox.information(self, "Success", "Product added successfully!")

            # Clear form
            self.name_input.clear()
            self.desc_input.clear()
            self.price_input.setValue(0.01)
            self.qty_input.setValue(0)
            self.min_qty_input.setValue(0)
            
            # Reload products
            self.load_products()
            # Emit signal for product added
            self.product_added.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding product: {str(e)}")
