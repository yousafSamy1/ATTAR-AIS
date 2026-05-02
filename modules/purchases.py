from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                            QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db_config import DatabaseConnection
from typing import Optional, Tuple, Any, cast, List, Dict, Set
from datetime import datetime

class PurchaseProductWidget(QWidget):
    def __init__(self, parent=None, used_products=None):
        super().__init__(parent)
        self.used_products = used_products if used_products else set()
        self.init_ui()
        self.load_products()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Product ComboBox
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(200)
        self.product_combo.setMinimumHeight(32)
        self.product_combo.setStyleSheet("QComboBox::drop-down { border: none; } QComboBox::down-arrow { image: none; }")
        layout.addWidget(self.product_combo)
        
        self.setLayout(layout)
    
    def load_products(self):
        try:
            current_product_id = None
            current_data = self.product_combo.currentData()
            if isinstance(current_data, tuple) and len(current_data) > 0:
                current_product_id = current_data[0]
            
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                # Load all products regardless of quantity
                cursor.execute("SELECT id, name, unit_price FROM products ORDER BY name")
                products = cursor.fetchall()
                
                self.product_combo.clear()
                self.product_combo.addItem("Select Product", None)
                
                for product in products:
                    # Add only unused products or the current product
                    if product['id'] not in self.used_products or product['id'] == current_product_id:
                        self.product_combo.addItem(
                            product['name'], 
                            (product['id'], product['unit_price'])
                        )
            
            # Restore previous selection if it exists
            if current_product_id:
                for i in range(self.product_combo.count()):
                    data = self.product_combo.itemData(i)
                    if isinstance(data, tuple) and len(data) > 0 and data[0] == current_product_id:
                        self.product_combo.setCurrentIndex(i)
                        break
                    
        except Exception as e:
            parent = self.parent()
            if parent and isinstance(parent, QWidget):
                QMessageBox.critical(parent, "Error", f"Failed to load products: {str(e)}")

    def get_product_data(self):
        data = self.product_combo.currentData()
        if not data:
            return None
            
        try:
            product_id, unit_price = data
            return (product_id, unit_price)
        except (ValueError, TypeError):
            return None

class PurchasesModule(QWidget):
    # Add signal
    purchase_added = pyqtSignal()
    
    def __init__(self, auto_accounting):
        super().__init__()
        self.auto_accounting = auto_accounting
        self.used_products = set()  # Track selected products
        self.initUI()

    def load_products(self):
        """Reload products in all product widgets when inventory changes"""
        for row in range(self.products_table.rowCount()):
            product_widget = self.products_table.cellWidget(row, 0)
            if isinstance(product_widget, PurchaseProductWidget):
                product_widget.load_products()
        self.add_product_row()  # Add initial row
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Purchase Invoice")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1C1008; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid #E8DDD0; padding-bottom: 8px;")
        layout.addWidget(header)

        # Create supplier selection
        supplier_layout = QHBoxLayout()
        self.supplier_combo = QComboBox()
        self.supplier_combo.setMinimumWidth(200)
        self.load_suppliers()
        supplier_layout.addWidget(QLabel("Supplier:"))
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addStretch()
        layout.addLayout(supplier_layout)
        
        # Create product table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Product Name",
            "Quantity", 
            "Price",
            "Total",
            "Action"
        ])
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(48)
        
        # Style headers
        header = self.products_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Product Name
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Quantity
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Price
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Total  
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Action
            
            # Set column widths
            self.products_table.setColumnWidth(1, 100)  # Quantity
            self.products_table.setColumnWidth(2, 120)  # Price
            self.products_table.setColumnWidth(3, 100)  # Total
            self.products_table.setColumnWidth(4, 80)   # Action
            
        layout.addWidget(self.products_table)
        
        # Create buttons
        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("+ Add Product Row")
        self.add_row_btn.setStyleSheet("background-color: #27AE60; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addStretch()
        
        # Total Amount
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("Total Amount:")
        total_label.setStyleSheet("font-weight: bold; color: #6B4C2A;")
        self.total_amount = QLabel("EGP 0.00")
        self.total_amount.setStyleSheet("font-size: 20px; font-weight: bold; color: #C8760A;")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount)
        
        # Save button
        self.save_btn = QPushButton("Save Purchase")
        self.save_btn.setStyleSheet("background-color: #C8760A; color: white; padding: 10px 24px; font-weight: bold; border-radius: 6px;")
        
        layout.addLayout(btn_layout)
        layout.addLayout(total_layout)
        layout.addWidget(self.save_btn)
          # Connect signals
        self.add_row_btn.clicked.connect(self.add_product_row)
        self.save_btn.clicked.connect(self.save_purchase)
    
    def setup_connections(self, suppliers_module):
        """Connect to suppliers module signals"""
        suppliers_module.supplier_added.connect(self.load_suppliers)
        
    def load_suppliers(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
                suppliers = cursor.fetchall()
                
                self.supplier_combo.clear()
                self.supplier_combo.addItem("Select Supplier", None)
                for supplier in suppliers:
                    self.supplier_combo.addItem(supplier['name'], supplier['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load suppliers: {str(e)}")
    
    def add_product_row(self):
        row = self.products_table.rowCount()
        self.products_table.insertRow(row)
        
        # Product Selection Widget
        product_widget = PurchaseProductWidget(parent=self, used_products=self.used_products)
        self.products_table.setCellWidget(row, 0, product_widget)

        # Quantity SpinBox
        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(1)
        quantity_spin.setMaximum(9999)
        quantity_spin.setMinimumWidth(80)
        quantity_spin.setMinimumHeight(32)
        quantity_spin.valueChanged.connect(lambda: self.update_row_total(row))
        self.products_table.setCellWidget(row, 1, quantity_spin)

        # Price SpinBox
        price_spin = QDoubleSpinBox()
        price_spin.setMinimum(0.01)
        price_spin.setMaximum(999999.99)
        price_spin.setDecimals(2)
        price_spin.setMinimumWidth(100)
        price_spin.valueChanged.connect(lambda: self.update_row_total(row))
        self.products_table.setCellWidget(row, 2, price_spin)

        # Total Column
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.products_table.setItem(row, 3, total_item)

        # Delete Button
        delete_btn = QPushButton("Remove")
        delete_btn.setStyleSheet("background-color: #C0392B; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold;")
        delete_btn.clicked.connect(lambda: self.delete_row(row))
        self.products_table.setCellWidget(row, 4, delete_btn)

        # Connect the product widget's signal
        product_widget.product_combo.currentIndexChanged.connect(lambda: self.product_selected(row))

    def product_selected(self, row: int):
        product_widget = self.products_table.cellWidget(row, 0)
        if not isinstance(product_widget, PurchaseProductWidget):
            return
          # Get the selected product data
        data = product_widget.get_product_data()
        if data:
            product_id, unit_price = data
            self.used_products.add(product_id)  # Add to used products set
            
            # Refresh other rows' product lists to hide this product
            for r in range(self.products_table.rowCount()):
                if r != row:
                    other_widget = self.products_table.cellWidget(r, 0)
                    if isinstance(other_widget, PurchaseProductWidget):
                        other_widget.load_products()
        
        self.update_row_total(row)

    def update_row_total(self, row: int):
        quantity_spin = cast(QSpinBox, self.products_table.cellWidget(row, 1))
        price_spin = cast(QDoubleSpinBox, self.products_table.cellWidget(row, 2))
        
        if not quantity_spin or not price_spin:
            return
            
        quantity = quantity_spin.value()
        price = price_spin.value()
        total = quantity * price
        
        total_item = self.products_table.item(row, 3)
        if not total_item:
            total_item = QTableWidgetItem()
            total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.products_table.setItem(row, 3, total_item)
        
        total_item.setText(f"{total:.2f}")
        self.update_total_amount()
    
    def update_total_amount(self):
        total = 0.0
        for row in range(self.products_table.rowCount()):
            if total_item := self.products_table.item(row, 3):
                if text := total_item.text():
                    try:
                        total += float(text)
                    except ValueError:
                        pass
        self.total_amount.setText(f"EGP {total:.2f}")
    
    def delete_row(self, row: int):
        # Get the product widget to remove its product ID from used set
        product_widget = self.products_table.cellWidget(row, 0)
        if isinstance(product_widget, PurchaseProductWidget):
            data = product_widget.get_product_data()
            if data:
                product_id, _ = data
                self.used_products.discard(product_id)  # Remove from used products
                
                # Refresh other rows' product lists
                for r in range(self.products_table.rowCount()):
                    if r != row:
                        other_widget = self.products_table.cellWidget(r, 0)
                        if isinstance(other_widget, PurchaseProductWidget):
                            other_widget.load_products()
        
        self.products_table.removeRow(row)
        self.update_total_amount()
    
    def validate_purchase(self) -> bool:
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "Validation Error", "Please select a supplier")
            return False
            
        if self.products_table.rowCount() == 0:
            QMessageBox.warning(self, "Validation Error", "Please add at least one product")
            return False
            
        for row in range(self.products_table.rowCount()):
            # Fix: Cast to PurchaseProductWidget instead of QComboBox
            product_widget = self.products_table.cellWidget(row, 0)
            if not isinstance(product_widget, PurchaseProductWidget):
                QMessageBox.warning(self, "Validation Error", f"Invalid product widget in row {row + 1}")
                return False
            
            # Use the get_product_data method instead of currentData
            if not product_widget.get_product_data():
                QMessageBox.warning(self, "Validation Error", f"Please select a product in row {row + 1}")
                return False
                
        return True

    
    def save_purchase(self):
        if not self.validate_purchase():
            return
            
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Create purchase invoice
                supplier_id = self.supplier_combo.currentData()
                total_amount = float(self.total_amount.text().replace("EGP", "").strip())
                date = datetime.now().strftime("%Y-%m-%d")
                
                cursor.execute("""
                    INSERT INTO purchase_invoices (supplier_id, date, total_amount)
                    VALUES (?, ?, ?)
                """, (supplier_id, date, total_amount))
                
                invoice_id = cursor.lastrowid
                
                # Add purchase items
                for row in range(self.products_table.rowCount()):
                    product_widget = self.products_table.cellWidget(row, 0)
                    quantity_spin = self.products_table.cellWidget(row, 1)
                    price_spin = self.products_table.cellWidget(row, 2)
                    
                    if not all([product_widget, quantity_spin, price_spin]):
                        continue
                    
                    product_data = product_widget.get_product_data()
                    if not product_data:
                        continue
                    
                    product_id = product_data[0]
                    quantity = quantity_spin.value()
                    unit_price = price_spin.value()
                    
                    cursor.execute("""
                        INSERT INTO purchase_items (invoice_id, product_id, quantity, unit_price)
                        VALUES (?, ?, ?, ?)
                    """, (invoice_id, product_id, quantity, unit_price))
                    
                    # Update product quantity
                    cursor.execute("""
                        UPDATE products 
                        SET quantity = quantity + ?
                        WHERE id = ?
                    """, (quantity, product_id))
                
                # Create journal entries using the same cursor
                self.auto_accounting.create_purchase_journal_entry(
                    cursor=cursor,
                    purchase_id=invoice_id,
                    supplier_id=supplier_id,
                    total_amount=total_amount,
                    date=date
                )
                
                conn.commit()
                
                # Emit signal that purchase was added
                self.purchase_added.emit()
                
                QMessageBox.information(self, "Success", "Purchase recorded successfully!")
                self.clear_form()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save purchase: {str(e)}")

    def clear_form(self):
        """Clear the purchase form after successful submission"""
        # Reset supplier selection
        self.supplier_combo.setCurrentIndex(0)
        
        # Clear the products table
        self.products_table.setRowCount(0)
        
        # Reset the used products set
        self.used_products.clear()
        
        # Reset total amount
        self.total_amount.setText("EGP 0.00")
        
        # Add an empty row
        self.add_product_row()

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