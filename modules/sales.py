# Python Standard Libraries
import sys              # System-specific parameters and functions
import os               # Operating system interface
from pathlib import Path  # Object-oriented filesystem paths
from datetime import datetime  # Date and time handling
from typing import Optional, Tuple, Any, List, Dict, cast  # Type hinting support

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
    QComboBox,         # Drop-down selection
    QSpinBox,          # Integer input spinner
    QDoubleSpinBox,    # Decimal input spinner
    QMessageBox,       # Modal message dialog
    QHeaderView        # Header view for tables
)
from PyQt6.QtCore import (
    Qt,               # Core non-widget functionality
    pyqtSignal        # Signal/slot communication
)

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler

class SalesModule(QWidget):
    # Add signal
    sale_added = pyqtSignal()
    
    def __init__(self, auto_accounting):
        super().__init__()
        self.auto_accounting = auto_accounting
        self.products: List[Dict] = []
        self.init_ui()
        self.load_customers()
        self.load_products()
        
    def setup_connections(self, customers_module):
        """Connect to customers module signals"""
        customers_module.customer_added.connect(self.load_customers)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("Sales Invoice")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1C1008; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid #E8DDD0; padding-bottom: 8px;")
        layout.addWidget(header)

        # Customer Selection
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Customer:")
        customer_label.setMinimumWidth(80)
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(200)
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_combo)
        customer_layout.addStretch()
        layout.addLayout(customer_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price", "Total", "Action"])
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(65)
        
        if header := self.products_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        layout.addWidget(self.products_table)

        # Add Product Button
        add_product_btn = QPushButton("+ Add Product Row")
        add_product_btn.setStyleSheet("background-color: #27AE60; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        add_product_btn.clicked.connect(self.add_product_row)
        layout.addWidget(add_product_btn)

        # Total Amount
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("Total Amount:")
        total_label.setStyleSheet("font-weight: bold; color: #6B4C2A;")
        self.total_amount = QLabel("EGP 0.00")
        self.total_amount.setStyleSheet("font-size: 20px; font-weight: bold; color: #C8760A;")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount)
        layout.addLayout(total_layout)

        # Save Button
        save_btn = QPushButton("Save Invoice")
        save_btn.setStyleSheet("background-color: #C8760A; color: white; padding: 10px 24px; font-weight: bold; border-radius: 6px;")
        save_btn.clicked.connect(self.save_invoice)
        layout.addWidget(save_btn)

    def load_customers(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM customers ORDER BY name")
                customers = cursor.fetchall()
                
                self.customer_combo.clear()
                self.customer_combo.addItem("Select Customer", None)
                for customer in customers:
                    self.customer_combo.addItem(customer['name'], customer['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customers: {str(e)}")

    def load_products(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, unit_price, quantity FROM products WHERE quantity > 0")
                self.products = cursor.fetchall()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
            self.products = []

    def add_product_row(self):
        if not self.products:
            QMessageBox.warning(self, "Warning", "No products available in inventory")
            return

        row = self.products_table.rowCount()
        self.products_table.insertRow(row)

        # Product ComboBox
        product_combo = QComboBox()
        product_combo.setMinimumWidth(200)
        product_combo.setMinimumHeight(32)
        product_combo.setStyleSheet("QComboBox::drop-down { border: none; } QComboBox::down-arrow { image: none; }")
        product_combo.addItem("Select Product", None)
        for product in self.products:
            product_combo.addItem(product['name'], (product['id'], product['unit_price'], product['quantity']))
        product_combo.currentIndexChanged.connect(lambda: self.product_selected(row))
        self.products_table.setCellWidget(row, 0, product_combo)

        # Quantity SpinBox
        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(1)
        quantity_spin.setMaximum(9999)
        quantity_spin.setMinimumWidth(80)
        quantity_spin.setMinimumHeight(32)
        quantity_spin.valueChanged.connect(lambda: self.update_row_total(row))
        self.products_table.setCellWidget(row, 1, quantity_spin)

        # Unit Price
        price_spin = QDoubleSpinBox()
        price_spin.setMinimum(0.01)
        price_spin.setMaximum(999999.99)
        price_spin.setDecimals(2)
        price_spin.setEnabled(False)
        price_spin.setMinimumWidth(100)
        price_spin.setMinimumHeight(32)
        price_spin.valueChanged.connect(lambda: self.update_row_total(row))
        self.products_table.setCellWidget(row, 2, price_spin)

        # Total
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.products_table.setItem(row, 3, total_item)

        # Delete Button
        delete_btn = QPushButton("Remove")
        delete_btn.setStyleSheet("background-color: #C0392B; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        delete_btn.clicked.connect(lambda: self.delete_row(row))
        self.products_table.setCellWidget(row, 4, delete_btn)

        # Set column widths
        self.products_table.setColumnWidth(1, 100)  # Quantity
        self.products_table.setColumnWidth(2, 120)  # Unit Price
        self.products_table.setColumnWidth(3, 120)  # Total
        self.products_table.setColumnWidth(4, 120)  # Action

    def get_row_widgets(self, row: int) -> Tuple[Optional[QComboBox], Optional[QSpinBox], Optional[QDoubleSpinBox], Optional[QTableWidgetItem]]:
        try:
            product_widget = self.products_table.cellWidget(row, 0)
            quantity_widget = self.products_table.cellWidget(row, 1)
            price_widget = self.products_table.cellWidget(row, 2)
            total_item = self.products_table.item(row, 3)

            if isinstance(product_widget, QComboBox) and \
               isinstance(quantity_widget, QSpinBox) and \
               isinstance(price_widget, QDoubleSpinBox):
                return cast(QComboBox, product_widget), \
                       cast(QSpinBox, quantity_widget), \
                       cast(QDoubleSpinBox, price_widget), \
                       total_item
            return None, None, None, None
        except:
            return None, None, None, None

    def product_selected(self, row: int) -> None:
        widgets = self.get_row_widgets(row)
        if not all(widgets):
            return

        product_combo, quantity_spin, price_spin, _ = widgets
        try:
            product_data = cast(QComboBox, product_combo).currentData()
            if isinstance(product_data, tuple) and len(product_data) >= 3:
                product_id, price, max_quantity = product_data[:3]  # Take first 3 elements
                if isinstance(price, (int, float)) and isinstance(max_quantity, (int, float)):
                    cast(QDoubleSpinBox, price_spin).setValue(float(price))
                    cast(QSpinBox, quantity_spin).setMaximum(int(max_quantity))
                    if cast(QSpinBox, quantity_spin).value() > max_quantity:
                        cast(QSpinBox, quantity_spin).setValue(1)
                    return

            # If we get here, we have invalid data
            cast(QDoubleSpinBox, price_spin).setValue(0.0)
            cast(QSpinBox, quantity_spin).setMaximum(9999)
            cast(QSpinBox, quantity_spin).setValue(1)
        except (ValueError, AttributeError, TypeError):
            pass
        
        self.update_row_total(row)

    def update_row_total(self, row: int) -> None:
        widgets = self.get_row_widgets(row)
        if not all(widgets[:-1]):  # Skip total_item in the check
            return

        _, quantity_spin, price_spin, total_item = widgets
        try:
            quantity = cast(QSpinBox, quantity_spin).value()
            price = cast(QDoubleSpinBox, price_spin).value()
            total = quantity * price

            if not total_item:
                total_item = QTableWidgetItem()
                total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.products_table.setItem(row, 3, total_item)

            if total_item:
                total_item.setText(f"{total:.2f}")
            
            self.update_total()
        except (ValueError, AttributeError, TypeError):
            pass

    def update_total(self) -> None:
        total = 0.0
        for row in range(self.products_table.rowCount()):
            if total_item := self.products_table.item(row, 3):
                if text := total_item.text():
                    try:
                        total += float(text)
                    except ValueError:
                        pass
        self.total_amount.setText(f"EGP {total:.2f}")

    def delete_row(self, row: int) -> None:
        if 0 <= row < self.products_table.rowCount():
            self.products_table.removeRow(row)
            self.update_total()

    def validate_invoice(self) -> bool:
        try:
            customer_id = self.customer_combo.currentData()
            if not customer_id:
                QMessageBox.warning(self, "Validation Error", "Please select a customer")
                return False

            if self.products_table.rowCount() == 0:
                QMessageBox.warning(self, "Validation Error", "Please add at least one product")
                return False

            for row in range(self.products_table.rowCount()):
                widgets = self.get_row_widgets(row)
                if not all(widgets[:-1]):  # Skip total_item in the check
                    QMessageBox.warning(self, "Validation Error", f"Invalid widgets in row {row + 1}")
                    return False

                product_combo = cast(QComboBox, widgets[0])
                if not product_combo.currentData():
                    QMessageBox.warning(self, "Validation Error", f"Please select a product in row {row + 1}")
                    return False

            return True
        except (AttributeError, TypeError):
            QMessageBox.critical(self, "Error", "Invalid widget state")
            return False

    def save_invoice(self) -> None:
        if not self.validate_invoice():
            return

        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                try:
                    # Create invoice
                    customer_id = self.customer_combo.currentData()
                    total_amount = float(self.total_amount.text().replace("EGP", "").strip())
                    date = datetime.now().strftime("%Y-%m-%d")
                    
                    cursor.execute("""
                        INSERT INTO sales_invoices (customer_id, date, total_amount)
                        VALUES (?, ?, ?)
                    """, (customer_id, date, total_amount))
                    
                    invoice_id = cursor.lastrowid

                    # Calculate total cost of goods sold
                    total_cogs = 0

                    # Add invoice items and update inventory
                    for row in range(self.products_table.rowCount()):
                        widgets = self.get_row_widgets(row)
                        if not all(widgets[:-1]):  # Skip total_item in the check
                            continue

                        product_combo = cast(QComboBox, widgets[0])
                        quantity_spin = cast(QSpinBox, widgets[1])
                        price_spin = cast(QDoubleSpinBox, widgets[2])

                        product_data = product_combo.currentData()
                        if not isinstance(product_data, tuple) or len(product_data) < 1:
                            continue

                        product_id = product_data[0]
                        quantity = quantity_spin.value()
                        unit_price = price_spin.value()

                        # Check available quantity again before inserting
                        cursor.execute("SELECT quantity, unit_price FROM products WHERE id = ?", (product_id,))
                        if not (result := cursor.fetchone()):
                            raise ValueError(f"Product not found")
                            
                        available_qty = result['quantity']
                        cost_price = result['unit_price']
                        if available_qty < quantity:
                            product_name = product_combo.currentText()
                            raise ValueError(f"Insufficient quantity for '{product_name}'")

                        cursor.execute("""
                            INSERT INTO sales_items (invoice_id, product_id, quantity, unit_price)
                            VALUES (?, ?, ?, ?)
                        """, (invoice_id, product_id, quantity, unit_price))

                        cursor.execute("""
                            UPDATE products 
                            SET quantity = quantity - ? 
                            WHERE id = ?
                        """, (quantity, product_id))

                        # Calculate COGS for this item
                        total_cogs += cost_price * quantity

                    # Create journal entries
                    self.auto_accounting.create_sales_journal_entry(
                        cursor=cursor,
                        sale_id=invoice_id,
                        customer_id=customer_id,
                        total_amount=total_amount,
                        cost_of_goods=total_cogs,
                        date=date
                    )

                    conn.commit()
                    QMessageBox.information(self, "Success", "Invoice saved successfully!")
                    
                    # Clear form
                    self.customer_combo.setCurrentIndex(0)
                    self.products_table.setRowCount(0)
                    self.total_amount.setText("EGP 0.00")
                    self.load_products()  # Reload products to get updated quantities

                    # Emit signal that sale was added
                    self.sale_added.emit()

                except Exception as e:
                    conn.rollback()
                    raise Exception(f"Database error: {str(e)}")

        except ValueError as e:
            QMessageBox.critical(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save invoice: {str(e)}")

    def showEvent(self, a0):
        """Called when the widget becomes visible"""
        super().showEvent(a0)
        if hasattr(self, 'products_table'):
            self.products_table.clearSelection()
        
    def hideEvent(self, a0):
        """Called when the widget becomes hidden"""
        super().hideEvent(a0)
        if hasattr(self, 'products_table'):
            self.products_table.clearSelection()
