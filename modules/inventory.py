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
    QSpinBox,          # Integer input spinner
    QDoubleSpinBox,    # Decimal input spinner
    QMessageBox,       # Modal message dialog
    QHeaderView        # Header view for tables
)
from PyQt6.QtCore import (
    Qt,               # Core non-widget functionality
    QTimer,           # Timer for periodic events
    pyqtSignal        # Signal/slot communication
)
from PyQt6.QtGui import QColor  # Color handling

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler

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
        
        # Set up warning delay timer
        self.warning_timer = QTimer()
        self.warning_timer.setSingleShot(True)  # Run only once
        self.warning_timer.timeout.connect(self.show_low_stock_warning)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Inventory Management")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1C1008; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid #E8DDD0; padding-bottom: 8px;")
        layout.addWidget(header)

        # Form layout setup
        self.form_layout = QVBoxLayout()
        
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
        self.add_btn = QPushButton("+ Add Product")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.add_btn.clicked.connect(self.add_product)
        self.form_layout.addWidget(self.add_btn)
        
        layout.addLayout(self.form_layout)
        
        # Products Table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Unit Price", "Quantity", "Min. Quantity"])
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(40)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.products_table)

        # Action Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Edit button with modern styling
        edit_btn = QPushButton("Edit Selected")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2471A3;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1A5276; }
        """)
        edit_btn.clicked.connect(self.edit_selected_product)
        buttons_layout.addWidget(edit_btn)

        # Delete button with modern styling
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #C0392B;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A93226; }
        """)
        delete_btn.clicked.connect(self.delete_selected_product)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        self.products_table.itemDoubleClicked.connect(self.edit_selected_product)

        # Enable form inputs by default
        self.set_form_enabled(True)

    def set_form_enabled(self, enabled: bool):
        """Enable or disable all form inputs"""
        self.name_input.setReadOnly(not enabled)
        self.desc_input.setReadOnly(not enabled)
        self.price_input.setReadOnly(not enabled)
        self.qty_input.setReadOnly(not enabled)
        self.min_qty_input.setReadOnly(not enabled)

    def edit_selected_product(self):
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
            
            # Check if any item is None
            if not all([id_item, name_item, desc_item, price_item, qty_item, min_qty_item]):
                QMessageBox.warning(self, "Error", "Could not get complete product information")
                return

            try:
                product_id = int(id_item.text())
                current_name = name_item.text()
                current_desc = desc_item.text()
                current_price = float(price_item.text().replace("$", ""))
                current_qty = int(qty_item.text())
                current_min_qty = int(min_qty_item.text())
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
                        background-color: #C8760A;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #A06008; }
                """)
                self.update_btn.clicked.connect(lambda: self.update_product(product_id))
                self.form_layout.addWidget(self.update_btn)
                self.update_btn.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing product: {str(e)}")

    def update_product(self, product_id):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Product name is required")
            return

        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products
                    SET name = ?, description = ?, unit_price = ?, quantity = ?, minimum_quantity = ?
                    WHERE id = ?
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
            
            # Reload products with center alignment
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
            
            if not all([isinstance(x, QTableWidgetItem) for x in [id_item, name_item]]):
                QMessageBox.warning(self, "Error", "Could not get product information")
                return
            
            try:
                product_id = int(id_item.text())
                product_name = name_item.text()
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
                low_stock_products = []  # Track products below minimum quantity
                
                for i, product in enumerate(products):
                    for j, value in enumerate(product):
                        item = QTableWidgetItem(str(value))
                        if j == 3:  # Format unit price as currency
                            item = QTableWidgetItem(f"${float(value):.2f}")
                        
                        # Set center alignment for all columns
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                            
                        # Make all cells read-only
                        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                        
                        # Highlight products with quantity below minimum
                        if j == 4 and product['quantity'] <= product['minimum_quantity']:
                            item.setBackground(QColor('#FDEDEC'))
                            item.setForeground(QColor('#C0392B'))
                            low_stock_products.append(f"{product['name']} (Current: {product['quantity']}, Min: {product['minimum_quantity']})")
                            
                        self.products_table.setItem(i, j, item)

                # Set column widths
                header = self.products_table.horizontalHeader()
                if header:
                    header.setStretchLastSection(True)
                    for i in range(self.products_table.columnCount()):
                        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading products: {str(e)}")

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
            self.product_added.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding product: {str(e)}")

    def show_low_stock_warning(self):
        """Show warning for products below minimum quantity"""
        low_stock_products = []
        for row in range(self.products_table.rowCount()):
            qty_item = self.products_table.item(row, 4)  # Quantity column
            min_qty_item = self.products_table.item(row, 5)  # Minimum Quantity column
            name_item = self.products_table.item(row, 1)  # Name column
            
            if all([qty_item, min_qty_item, name_item]) and isinstance(qty_item, QTableWidgetItem) and isinstance(min_qty_item, QTableWidgetItem) and isinstance(name_item, QTableWidgetItem):
                try:
                    qty = int(qty_item.text())
                    min_qty = int(min_qty_item.text())
                    if qty <= min_qty:
                        low_stock_products.append(f"{name_item.text()} (Current: {qty}, Min: {min_qty})")
                except (ValueError, AttributeError):
                    continue
        
        if low_stock_products:
            warning_msg = "⚠️ Low Stock Alert ⚠️\n\n"
            warning_msg += "The following products need to be restocked:\n\n"
            warning_msg += "\n".join(f"• {name}" for name in low_stock_products)
            warning_msg += "\n\nPlease create purchase orders for these items."
            QMessageBox.warning(self, "Low Stock Warning", warning_msg)

    def showEvent(self, a0):
        """Called when the widget becomes visible"""
        super().showEvent(a0)
        self.load_products()
        # Show warning after 500ms delay
        self.warning_timer.start(500)
        if hasattr(self, 'products_table'):
            self.products_table.clearSelection()

    def hideEvent(self, a0):
        """Called when the widget becomes hidden"""
        super().hideEvent(a0)
        self.refresh_timer.stop()
        if hasattr(self, 'products_table'):
            self.products_table.clearSelection()
