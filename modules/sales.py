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
    QHeaderView,        # Header view for tables
    QDialog
)
from PyQt6.QtCore import (
    Qt,               # Core non-widget functionality
    pyqtSignal        # Signal/slot communication
)

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler
from modules.theme import COLORS, get_button_style, get_action_button_style
from modules.localization import tr
from modules.customers import CustomerDialog

class SaleDetailsDialog(QDialog):
    def __init__(self, parent, sale_id):
        super().__init__(parent)
        self.setWindowTitle(f"Sale Details - Invoice #{sale_id}")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.date, c.name as customer, s.total_amount
                    FROM sales_invoices s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    WHERE s.id = ?
                """, (sale_id,))
                sale = cursor.fetchone()
                
                if not sale:
                    layout.addWidget(QLabel("Sale not found"))
                    return
                
                info_layout = QHBoxLayout()
                info_layout.addWidget(QLabel(f"<b>Date:</b> {sale['date']}"))
                info_layout.addStretch()
                info_layout.addWidget(QLabel(f"<b>Customer:</b> {sale['customer']}"))
                layout.addLayout(info_layout)
                
                table = QTableWidget()
                table.setColumnCount(4)
                table.setHorizontalHeaderLabels(["Product", "Quantity", "Price", "Total"])
                table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                
                cursor.execute("""
                    SELECT p.name, si.quantity, si.unit_price, (si.quantity * si.unit_price) as total
                    FROM sales_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.invoice_id = ?
                """, (sale_id,))
                items = cursor.fetchall()
                
                table.setRowCount(len(items))
                for i, item in enumerate(items):
                    table.setItem(i, 0, QTableWidgetItem(item['name']))
                    # Show in kg or g based on amount
                    qty = item['quantity']
                    qty_str = f"{qty*1000:.0f} g" if qty < 1 else f"{qty:.3f} kg"
                    table.setItem(i, 1, QTableWidgetItem(qty_str))
                    table.setItem(i, 2, QTableWidgetItem(f"EGP {item['unit_price']:.2f}"))
                    table.setItem(i, 3, QTableWidgetItem(f"EGP {item['total']:.2f}"))
                
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                layout.addWidget(table)
                
                total_lbl = QLabel(f"<b>Total Amount:</b> EGP {sale['total_amount']:.2f}")
                total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                total_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['green']}; font-weight: bold; margin-top: 10px;")
                layout.addWidget(total_lbl)
                
        except Exception as e:
            layout.addWidget(QLabel(f"Error loading details: {str(e)}"))
            
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class SalesModule(QWidget):
    # Add signal
    sale_added = pyqtSignal()
    customer_added = pyqtSignal()
    
    def __init__(self, auto_accounting, user=None):
        super().__init__()
        self.auto_accounting = auto_accounting
        self.user = user
        self.products: List[Dict] = []
        self.init_ui()
        self.load_customers()
        self.load_products()
        
    def setup_connections(self, customers_module):
        """Connect to customers module signals"""
        customers_module.customer_added.connect(self.load_customers)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Header
        header = QLabel("Sales Invoice")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)

        # Customer Selection
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Customer:")
        customer_label.setMinimumWidth(80)
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(200)
        
        # Add New Customer Button
        self.add_customer_btn = QPushButton("➕")
        self.add_customer_btn.setToolTip("Add New Customer")
        self.add_customer_btn.setFixedSize(32, 32)
        self.add_customer_btn.setStyleSheet(get_action_button_style('green'))
        self.add_customer_btn.clicked.connect(self.add_new_customer)
        
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_combo)
        customer_layout.addWidget(self.add_customer_btn)
        
        # Add spacing before payment type
        customer_layout.addSpacing(20)

        # Payment Type
        payment_label = QLabel(tr('payment_type') + ":")
        payment_label.setMinimumWidth(100)
        self.payment_combo = QComboBox()
        self.payment_combo.setMinimumWidth(150)
        self.payment_combo.addItem(tr('cash'), 'cash')
        self.payment_combo.addItem(tr('credit'), 'credit')
        customer_layout.addWidget(payment_label)
        customer_layout.addWidget(self.payment_combo)

        customer_layout.addStretch()
        layout.addLayout(customer_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels(["Product", "Stock", "Type", "Quantity", "Unit", "Unit Price", "Total", "Action"])
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(60)
        self.products_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        if header := self.products_table.horizontalHeader():
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
            
            # Set explicit column widths - Balanced for header visibility
            self.products_table.setColumnWidth(1, 130) # Stock
            self.products_table.setColumnWidth(2, 80)  # Type
            self.products_table.setColumnWidth(3, 100) # Quantity
            self.products_table.setColumnWidth(4, 120) # Unit
            self.products_table.setColumnWidth(5, 100) # Price
            self.products_table.setColumnWidth(6, 110) # Total
            self.products_table.setColumnWidth(7, 130) # Action
        
        layout.addWidget(self.products_table)

        # Add Product Button
        add_product_btn = QPushButton("➕ Add Product Row")
        add_product_btn.setStyleSheet(get_button_style('green'))
        add_product_btn.clicked.connect(self.add_product_row)
        layout.addWidget(add_product_btn)

        # Total Amount
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("Total Amount:")
        total_label.setStyleSheet(f"font-weight: bold; color: {COLORS['text_sub']};")
        self.total_amount = QLabel("EGP 0.00")
        self.total_amount.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent']};")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount)
        layout.addLayout(total_layout)

        # Save Button
        save_btn = QPushButton("💾 Save Invoice")
        save_btn.setStyleSheet(get_button_style('accent'))
        # Internal styling for table widgets to prevent text cutoff
        self.products_table.setStyleSheet(self.products_table.styleSheet() + f"""
            QLineEdit, QComboBox {{
                padding: 4px 8px;
                margin: 2px;
            }}
        """)
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

    def add_new_customer(self):
        """Open dialog to add a new customer and refresh the list"""
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
                    
                # Refresh customers list
                self.load_customers()
                
                # Try to select the newly added customer
                # We need to find the ID of the last inserted row
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM customers ORDER BY id DESC LIMIT 1")
                    last_id = cursor.fetchone()
                    if last_id:
                        index = self.customer_combo.findData(last_id['id'])
                        if index >= 0:
                            self.customer_combo.setCurrentIndex(index)
                
                # Emit signal so other modules can refresh
                self.customer_added.emit()
                
                QMessageBox.information(self, "Success", "Customer added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add customer: {str(e)}")

    def load_products(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE quantity > 0 ORDER BY name ASC")
                # Convert sqlite3.Row to dict for easier access
                self.products = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
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
            avail = product['quantity']
            avail_str = f"{avail*1000:.0f}g" if avail < 1 else f"{avail:.2f}kg"
            product_combo.addItem(f"{product['name']} ({avail_str})", product) # Store full dict
        product_combo.currentIndexChanged.connect(lambda _, w=product_combo: self.product_selected(self.products_table.indexAt(w.pos()).row()))
        self.products_table.setCellWidget(row, 0, product_combo)

        # Stock Item (Read-only)
        stock_item = QTableWidgetItem("---")
        stock_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.products_table.setItem(row, 1, stock_item)

        # Type Item (Read-only)
        type_item = QTableWidgetItem("---")
        type_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.products_table.setItem(row, 2, type_item)

        # Quantity SpinBox (now QLineEdit)
        quantity_spin = QLineEdit()
        quantity_spin.setText("0.0")
        quantity_spin.setText("0.0")
        from PyQt6.QtGui import QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression
        qty_val = QRegularExpressionValidator(QRegularExpression(r'^\d+[\.,]?\d*$'))
        quantity_spin.setValidator(qty_val)
        quantity_spin.setMinimumWidth(80)
        quantity_spin.setMinimumHeight(32)
        quantity_spin.textChanged.connect(lambda _, w=quantity_spin: self.update_row_total(self.products_table.indexAt(w.pos()).row()))
        self.products_table.setCellWidget(row, 3, quantity_spin)

        # Unit ComboBox
        unit_combo = QComboBox()
        unit_combo.addItem("---", None)
        unit_combo.setMinimumWidth(100)
        unit_combo.setMinimumHeight(32)
        unit_combo.currentIndexChanged.connect(lambda _, w=unit_combo: self.unit_changed(self.products_table.indexAt(w.pos()).row()))
        self.products_table.setCellWidget(row, 4, unit_combo)

        # Unit Price (now QLineEdit)
        price_spin = QLineEdit()
        price_spin.setText("0.00")
        price_val = QRegularExpressionValidator(QRegularExpression(r'^\d+[\.,]?\d*$'))
        price_spin.setValidator(price_val)
        price_spin.setEnabled(True)
        price_spin.setMinimumWidth(100)
        price_spin.setMinimumHeight(32)
        price_spin.textChanged.connect(lambda _, w=price_spin: self.update_row_total(self.products_table.indexAt(w.pos()).row()))
        self.products_table.setCellWidget(row, 5, price_spin)

        # Total
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.products_table.setItem(row, 6, total_item)

        delete_btn = QPushButton("🗑️ Remove")
        delete_btn.setFixedSize(110, 32)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(get_action_button_style('red'))
        delete_btn.clicked.connect(self.delete_row)
        self.products_table.setCellWidget(row, 7, delete_btn)

        # Set column widths
        self.products_table.setColumnWidth(1, 120)  # Stock
        self.products_table.setColumnWidth(2, 90)   # Type
        self.products_table.setColumnWidth(3, 110)  # Quantity
        self.products_table.setColumnWidth(4, 130)  # Unit
        self.products_table.setColumnWidth(5, 120)  # Unit Price
        self.products_table.setColumnWidth(6, 120)  # Total
        self.products_table.setColumnWidth(7, 100)  # Action

    def get_row_widgets(self, row: int) -> Tuple[Optional[QComboBox], Optional[QDoubleSpinBox], Optional[QComboBox], Optional[QDoubleSpinBox], Optional[QTableWidgetItem]]:
        try:
            product_widget = self.products_table.cellWidget(row, 0)
            quantity_widget = self.products_table.cellWidget(row, 3)
            unit_widget = self.products_table.cellWidget(row, 4)
            price_widget = self.products_table.cellWidget(row, 5)
            total_item = self.products_table.item(row, 6)

            if isinstance(product_widget, QComboBox) and \
               isinstance(quantity_widget, QLineEdit) and \
               isinstance(unit_widget, QComboBox) and \
               isinstance(price_widget, QLineEdit):
                return cast(QComboBox, product_widget), \
                       cast(QLineEdit, quantity_widget), \
                       cast(QComboBox, unit_widget), \
                       cast(QLineEdit, price_widget), \
                       total_item
            return None, None, None, None, None
        except:
            return None, None, None, None, None

    def unit_changed(self, row: int) -> None:
        if row < 0 or row >= self.products_table.rowCount(): return
        widgets = self.get_row_widgets(row)
        if not all(widgets[:-1]): return
        
        product_data = widgets[0].currentData()
        unit = widgets[2].currentText()
        price_spin = widgets[3]
        
        if product_data and product_data.get('product_type') == 'packaged':
            if unit.lower() == "bag":
                price_spin.setText(str(product_data.get('piece_price', 0)))
            else:
                price_spin.setText(str(product_data.get('unit_price', 0)))
        
        self.update_max_quantity(row)
        self.update_row_total(row)

    def update_max_quantity(self, row: int) -> None:
        if row < 0 or row >= self.products_table.rowCount(): return
        widgets = self.get_row_widgets(row)
        product_combo, quantity_spin, unit_combo, _, _ = widgets
        product_data = product_combo.currentData()
        if not product_data: return
        
        available_qty = product_data['quantity']
        unit = unit_combo.currentText()
        p_type = product_data.get('product_type', 'bulk')
        
        if p_type == 'packaged':
            pass
        else:
            pass

    def product_selected(self, row: int) -> None:
        if row < 0 or row >= self.products_table.rowCount(): return
        widgets = self.get_row_widgets(row)
        if not widgets[0]: return
        
        product_combo = widgets[0]
        product_data = product_combo.currentData()
        if not product_data: return
        
        p_type = product_data.get('product_type', 'bulk')
        
        # Update Stock column
        avail = product_data['quantity']
        avail_str = f"{avail*1000:.0f} g" if avail < 1 else f"{avail:.3f} kg"
        stock_item = QTableWidgetItem(avail_str)
        stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        stock_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.products_table.setItem(row, 1, stock_item)
        
        # Update Type column
        type_text = "Packaged" if p_type == 'packaged' else "Bulk"
        type_item = QTableWidgetItem(type_text)
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        type_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.products_table.setItem(row, 2, type_item)
        
        unit_combo = widgets[2]
        if unit_combo:
            unit_combo.blockSignals(True)
            unit_combo.clear()
            unit_combo.blockSignals(True)
            unit_combo.clear()
            if p_type == 'packaged':
                unit_combo.addItem(tr('carton'), 1.0)
                unit_combo.addItem(tr('bag'), 1.0 / float(product_data.get('pieces_per_unit', 1)))
            else:
                unit_combo.addItem(tr('kilograms'), 1.0)
                unit_combo.addItem(tr('grams'), 0.001)
            unit_combo.blockSignals(False)
        
        price_spin = widgets[3]
        if price_spin:
            price_spin.setText(str(product_data['unit_price']))
            
        self.update_max_quantity(row)
        self.update_row_total(row)

    def update_row_total(self, row: int) -> None:
        if row < 0 or row >= self.products_table.rowCount(): return
        widgets = self.get_row_widgets(row)
        if not all(widgets[:-1]):
            return
        
        _, quantity_spin, unit_combo, price_spin, _ = widgets
        try:
            qty = float(quantity_spin.text().replace(',', '.') or '0')
            price = float(price_spin.text().replace(',', '.') or '0')
        except ValueError:
            qty = 0.0
            price = 0.0
            
        unit_factor = unit_combo.currentData() or 1.0
        
        total = (qty * unit_factor) * price
            
        self.products_table.setItem(row, 6, QTableWidgetItem(f"{total:.2f}"))
        self.update_total()

    def update_total(self) -> None:
        total = 0.0
        for row in range(self.products_table.rowCount()):
            if total_item := self.products_table.item(row, 6):
                if text := total_item.text():
                    try:
                        total += float(text)
                    except ValueError:
                        pass
        self.total_amount.setText(f"EGP {total:.2f}")

    def delete_row(self) -> None:
        button = self.sender()
        if not button: return
        index = self.products_table.indexAt(button.pos())
        if not index.isValid(): return
        
        row = index.row()
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
                    customer_id = self.customer_combo.currentData()
                    payment_type = self.payment_combo.currentData()
                    total_amount = float(self.total_amount.text().replace("EGP ", "").replace(",", ""))
                    date = datetime.now().strftime("%Y-%m-%d")
                    
                    status = 'paid' if payment_type == 'cash' else 'pending'
                    paid_amt = total_amount if payment_type == 'cash' else 0
                    
                    cursor.execute("""
                        INSERT INTO sales_invoices (customer_id, date, total_amount, payment_type, status, paid_amount)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (customer_id, date, total_amount, payment_type, status, paid_amt))
                    
                    invoice_id = cursor.lastrowid
                    total_cogs = 0

                    for row in range(self.products_table.rowCount()):
                        widgets = self.get_row_widgets(row)
                        if not widgets[0]: continue
                        
                        product_combo, quantity_spin, unit_combo, price_spin, _ = widgets
                        product_data = product_combo.currentData()
                        product_id = product_data['id']
                        
                        try:
                            qty = float(quantity_spin.text().replace(',', '.') or '0')
                            unit_price = float(price_spin.text().replace(',', '.') or '0')
                        except ValueError:
                            qty = 0.0
                            unit_price = 0.0
                            
                        unit = unit_combo.currentText()
                        
                        unit_factor = unit_combo.currentData() or 1.0
                        base_qty = qty * unit_factor
                        
                        # Check if it's a recipe (Mixture)
                        cursor.execute("SELECT is_recipe, id FROM products WHERE id=?", (product_id,))
                        p_info = cursor.fetchone()
                        
                        if p_info['is_recipe']:
                            # Get Ingredients
                            cursor.execute("""
                                SELECT ri.ingredient_id, ri.quantity, p.unit_cost 
                                FROM recipe_ingredients ri
                                JOIN products p ON ri.ingredient_id = p.id
                                WHERE ri.recipe_id = (SELECT id FROM recipes WHERE product_id = ?)
                            """, (product_id,))
                            ingredients = cursor.fetchall()
                            
                            if not ingredients:
                                raise ValueError(f"Mixture '{product_combo.currentText()}' has no defined ingredients!")

                            for ing in ingredients:
                                ing_id = ing['ingredient_id']
                                ing_qty_per_unit = ing['quantity']
                                total_ing_qty = base_qty * ing_qty_per_unit
                                
                                # Deduct Ingredient
                                cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (total_ing_qty, ing_id))
                                total_cogs += (ing['unit_cost'] or 0) * total_ing_qty
                        else:
                            # Normal Product
                            cursor.execute("SELECT quantity, unit_cost FROM products WHERE id=?", (product_id,))
                            res = cursor.fetchone()
                            available_qty = res['quantity']
                            cost_price = res['unit_cost'] or 0

                            if available_qty < base_qty:
                                product_name = product_combo.currentText()
                                raise ValueError(f"Insufficient quantity for '{product_name}'")

                            cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (base_qty, product_id))
                            total_cogs += cost_price * base_qty

                        # Record the Sale Item (always record the product sold)
                        cursor.execute("""
                            INSERT INTO sales_items (invoice_id, product_id, quantity, unit_price)
                            VALUES (?, ?, ?, ?)
                        """, (invoice_id, product_id, base_qty, unit_price))

                    if self.auto_accounting:
                        self.auto_accounting.create_sales_journal_entry(
                            cursor, invoice_id, customer_id, total_amount, total_cogs, date, payment_type
                        )

                    conn.commit()
                    from database.db_config import log_action
                    log_action(self.user['id'], self.user['username'], 'New Sale', 'Sales', f'Invoice #{invoice_id} - Total: {total_amount}')
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

    def open_view_by_id(self, sale_id):
        """Open detailed view for a specific sale"""
        dialog = SaleDetailsDialog(self, sale_id)
        dialog.exec()

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
