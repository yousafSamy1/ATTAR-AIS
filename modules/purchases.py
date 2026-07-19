from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                            QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QHeaderView, QDialog, QDateEdit)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from database.db_config import DatabaseConnection
from typing import Optional, Tuple, Any, cast, List, Dict, Set
from datetime import datetime, timedelta
from modules.theme import COLORS, get_button_style, get_action_button_style
from modules.localization import tr

class ProductDefinitionDialog(QDialog):
    def __init__(self, parent=None, edit_id=None):
        super().__init__(parent)
        self.edit_id = edit_id
        self.setWindowTitle("Add New Product" if not edit_id else "Edit Product")
        self.setMinimumWidth(500)
        self.init_ui()
        if edit_id:
            self.load_product_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QVBoxLayout()

        # Product Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        form_layout.addWidget(QLabel("Product Name:"))
        form_layout.addWidget(self.name_input)

        # Description
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        form_layout.addWidget(QLabel("Description:"))
        form_layout.addWidget(self.desc_input)

        # Product Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Bulk (Weight)", "Packaged (Cartons/Bags)"])
        self.type_combo.currentIndexChanged.connect(self.toggle_fields)
        form_layout.addWidget(QLabel("Product Type:"))
        form_layout.addWidget(self.type_combo)

        # Unit Price
        self.price_input = QLineEdit()
        price_validator = QDoubleValidator(0.00, 999999.99, 2)
        price_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.price_input.setValidator(price_validator)
        self.price_label = QLabel("Selling Unit Price (EGP):")
        form_layout.addWidget(self.price_label)
        form_layout.addWidget(self.price_input)

        # Initial Quantity
        qty_layout = QHBoxLayout()
        self.qty_input = QLineEdit()
        qty_validator = QDoubleValidator(0.00, 999999.99, 2)
        qty_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.qty_input.setValidator(qty_validator)
        self.qty_unit = QComboBox()
        qty_layout.addWidget(self.qty_input)
        qty_layout.addWidget(self.qty_unit)
        form_layout.addWidget(QLabel("Initial Quantity:"))
        form_layout.addLayout(qty_layout)

        # Minimum Quantity
        min_qty_layout = QHBoxLayout()
        self.min_qty_input = QLineEdit()
        self.min_qty_input.setValidator(qty_validator)
        self.min_qty_unit = QComboBox()
        min_qty_layout.addWidget(self.min_qty_input)
        min_qty_layout.addWidget(self.min_qty_unit)
        form_layout.addWidget(QLabel("Minimum Quantity Alert:"))
        form_layout.addLayout(min_qty_layout)

        # Packaged Specific
        self.packaged_container = QWidget()
        pkg_layout = QVBoxLayout(self.packaged_container)
        self.pieces_input = QLineEdit()
        self.pieces_input.setValidator(QIntValidator(1, 1000))
        pkg_layout.addWidget(QLabel("Bags per Carton:"))
        pkg_layout.addWidget(self.pieces_input)
        
        self.bag_price_input = QLineEdit()
        self.bag_price_input.setValidator(price_validator)
        pkg_layout.addWidget(QLabel("Selling Price per Bag (EGP):"))
        pkg_layout.addWidget(self.bag_price_input)
        
        form_layout.addWidget(self.packaged_container)
        self.packaged_container.hide()

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Product")
        save_btn.setStyleSheet(f"background-color: {COLORS['green']}; color: white; padding: 8px; font-weight: bold;")
        save_btn.clicked.connect(self.save_product)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.toggle_fields(0)

    def toggle_fields(self, index):
        is_packaged = (index == 1)
        self.packaged_container.setVisible(is_packaged)
        self.qty_unit.clear()
        self.min_qty_unit.clear()
        if is_packaged:
            self.price_label.setText("Selling Price per Carton (EGP):")
            self.qty_unit.addItem("Carton")
            self.min_qty_unit.addItem("Carton")
        else:
            self.price_label.setText("Selling Unit Price / Kg (EGP):")
            self.qty_unit.addItems(["Gram (g)", "Kilogram (kg)"])
            self.min_qty_unit.addItems(["Gram (g)", "Kilogram (kg)"])

    def load_product_data(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE id=?", (self.edit_id,))
                row = cursor.fetchone()
                if row:
                    p = dict(row)
                    self.name_input.setText(p['name'])
                    self.desc_input.setText(p['description'])
                    self.price_input.setText(str(p['unit_price']))
                    is_pkg = p.get('product_type') == 'packaged'
                    self.type_combo.setCurrentIndex(1 if is_pkg else 0)
                    self.qty_input.setText(str(p['quantity']))
                    self.min_qty_input.setText(str(p['minimum_quantity']))
                    if is_pkg:
                        self.pieces_input.setText(str(p.get('pieces_per_unit', 1)))
                        self.bag_price_input.setText(str(p.get('piece_price', 0)))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load product: {e}")

    def save_product(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required")
            return

        try:
            p_type = 'packaged' if self.type_combo.currentIndex() == 1 else 'bulk'
            qty = float(self.qty_input.text() or '0')
            min_qty = float(self.min_qty_input.text() or '0')
            price = float(self.price_input.text() or '0')
            
            if p_type == 'bulk':
                if self.qty_unit.currentText() == "Gram (g)": qty /= 1000.0
                if self.min_qty_unit.currentText() == "Gram (g)": min_qty /= 1000.0
            
            pieces = int(self.pieces_input.text() or '1') if p_type == 'packaged' else 1
            piece_price = float(self.bag_price_input.text() or '0') if p_type == 'packaged' else 0

            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                if self.edit_id:
                    cursor.execute("""
                        UPDATE products SET name=?, description=?, unit_price=?, quantity=?, 
                        minimum_quantity=?, product_type=?, pieces_per_unit=?, piece_price=?
                        WHERE id=?
                    """, (name, self.desc_input.text(), price, qty, min_qty, p_type, pieces, piece_price, self.edit_id))
                else:
                    cursor.execute("""
                        INSERT INTO products (name, description, unit_price, quantity, minimum_quantity, product_type, pieces_per_unit, piece_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (name, self.desc_input.text(), price, qty, min_qty, p_type, pieces, piece_price))
                conn.commit()
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

class PurchaseDetailsDialog(QDialog):
    def __init__(self, parent, purchase_id):
        super().__init__(parent)
        self.setWindowTitle(f"Purchase Details - Invoice #{purchase_id}")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.date, s.name as supplier, p.total_amount
                    FROM purchase_invoices p
                    LEFT JOIN suppliers s ON p.supplier_id = s.id
                    WHERE p.id = ?
                """, (purchase_id,))
                purchase = cursor.fetchone()
                
                if not purchase:
                    layout.addWidget(QLabel("Purchase not found"))
                    return
                
                info_layout = QHBoxLayout()
                info_layout.addWidget(QLabel(f"<b>Date:</b> {purchase['date']}"))
                info_layout.addStretch()
                info_layout.addWidget(QLabel(f"<b>Supplier:</b> {purchase['supplier']}"))
                layout.addLayout(info_layout)
                
                table = QTableWidget()
                table.setColumnCount(4)
                table.setHorizontalHeaderLabels(["Product", "Quantity", "Price", "Total"])
                table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                
                cursor.execute("""
                    SELECT pr.name, pi.quantity, pi.unit_price, (pi.quantity * pi.unit_price) as total
                    FROM purchase_items pi
                    JOIN products pr ON pi.product_id = pr.id
                    WHERE pi.invoice_id = ?
                """, (purchase_id,))
                items = cursor.fetchall()
                
                table.setRowCount(len(items))
                for i, item in enumerate(items):
                    table.setItem(i, 0, QTableWidgetItem(item['name']))
                    qty = item['quantity']
                    qty_str = f"{qty*1000:.0f} g" if qty < 1 else f"{qty:.3f} kg"
                    table.setItem(i, 1, QTableWidgetItem(qty_str))
                    table.setItem(i, 2, QTableWidgetItem(f"EGP {item['unit_price']:.2f}"))
                    table.setItem(i, 3, QTableWidgetItem(f"EGP {item['total']:.2f}"))
                
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                layout.addWidget(table)
                
                total_lbl = QLabel(f"<b>Total Amount:</b> EGP {purchase['total_amount']:.2f}")
                total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                total_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['red']}; font-weight: bold; margin-top: 10px;")
                layout.addWidget(total_lbl)
                
        except Exception as e:
            layout.addWidget(QLabel(f"Error loading details: {str(e)}"))
            
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class PurchaseProductWidget(QWidget):
    product_changed = pyqtSignal(object)

    def __init__(self, parent=None, used_products=None):
        super().__init__(parent)
        self.used_products = used_products if used_products else set()
        self.init_ui()
        self.load_products()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(200)
        self.product_combo.setMinimumHeight(32)
        self.product_combo.setStyleSheet("""
            QComboBox {
                border: none;
                padding-left: 5px;
                background: transparent;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.product_combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self.product_combo)
        self.setLayout(layout)
    
    def _on_index_changed(self, index):
        data = self.product_combo.currentData()
        self.product_changed.emit(data)

    def load_products(self):
        try:
            current_product_id = None
            current_data = self.product_combo.currentData()
            if isinstance(current_data, dict):
                current_product_id = current_data.get('id')
            
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products ORDER BY name")
                products = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
                
                self.product_combo.blockSignals(True)
                self.product_combo.clear()
                self.product_combo.addItem("Select Product", None)
                
                for product in products:
                    if product['id'] not in self.used_products or product['id'] == current_product_id:
                        avail = product['quantity']
                        avail_str = f"{avail*1000:.0f}g" if avail < 1 else f"{avail:.2f}kg"
                        self.product_combo.addItem(f"{product['name']} ({avail_str})", product)
                self.product_combo.blockSignals(False)
            
            if current_product_id:
                for i in range(self.product_combo.count()):
                    data = self.product_combo.itemData(i)
                    if isinstance(data, dict) and data.get('id') == current_product_id:
                        self.product_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Error loading products: {e}")

    def get_product_data(self):
        return self.product_combo.currentData()

class PurchasesModule(QWidget):
    # Add signal
    purchase_added = pyqtSignal()
    supplier_added = pyqtSignal()
    
    def __init__(self, auto_accounting, user=None):
        super().__init__()
        self.auto_accounting = auto_accounting
        self.user = user
        self.used_products = set()  # Track selected products
        self.initUI()
        # Check credit due alerts after UI init
        QTimer.singleShot(500, self.check_credit_due_alerts)

    def toggle_due_date_visibility(self):
        if self.payment_combo.currentData() == 'credit':
            self.due_date_label.show()
            self.due_date_edit.show()
        else:
            self.due_date_label.hide()
            self.due_date_edit.hide()

    # Existing methods unchanged ...

    def save_purchase(self):
        if not self.validate_purchase():
            return
        
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                
                # Recalculate total_amount from items to be 100% sure we don't save 0
                total_amount = 0.0
                for row in range(self.products_table.rowCount()):
                    qty_spin = self.products_table.cellWidget(row, 3)
                    unit_combo = self.products_table.cellWidget(row, 4)
                    price_spin = self.products_table.cellWidget(row, 5)
                    if qty_spin and unit_combo and price_spin:
                        try:
                            q = float(qty_spin.text().replace(',', '.') or '0')
                            p = float(price_spin.text().replace(',', '.') or '0')
                            f = unit_combo.currentData() or 1.0
                            total_amount += (q * f * p)
                        except: pass

                # Determine due date and status for credit purchases
                due_date = None
                status = 'paid'
                paid_amount = total_amount
                if payment_type == 'credit':
                    due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
                    status = 'pending'
                    paid_amount = 0
                
                cursor.execute("""
                    INSERT INTO purchase_invoices (supplier_id, date, total_amount, payment_type, due_date, status, paid_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (supplier_id, date, total_amount, payment_type, due_date, status, paid_amount))
                
                invoice_id = cursor.lastrowid
                
                # Add purchase items
                for row in range(self.products_table.rowCount()):
                    product_widget = self.products_table.cellWidget(row, 0)
                    qty_spin = self.products_table.cellWidget(row, 3)
                    unit_combo = self.products_table.cellWidget(row, 4)
                    price_spin = self.products_table.cellWidget(row, 5)
                    
                    if not all([product_widget, qty_spin, unit_combo, price_spin]): continue
                    
                    product_data = product_widget.get_product_data()
                    if not product_data or not isinstance(product_data, dict): continue
                    
                    product_id = product_data['id']
                    
                    try:
                        qty = float(qty_spin.text().replace(',', '.') or '0')
                        unit_price = float(price_spin.text().replace(',', '.') or '0')
                    except ValueError:
                        qty = 0.0
                        unit_price = 0.0
                        
                    unit = unit_combo.currentText()
                    unit_factor = unit_combo.currentData() or 1.0
                    base_qty = qty * unit_factor
                    
                    expiry_spin = self.products_table.cellWidget(row, 6)
                    months = 12
                    try: months = int(expiry_spin.text() or '12')
                    except: pass
                    
                    expiry_date = (datetime.now() + timedelta(days=months*30)).strftime("%Y-%m-%d")
                    
                    cursor.execute("""
                        INSERT INTO purchase_items (invoice_id, product_id, quantity, unit_price, expiry_date)
                        VALUES (?, ?, ?, ?, ?)
                    """, (invoice_id, product_id, base_qty, unit_price, expiry_date))
                    
                    # Log to Purchase History for Trends
                    cursor.execute("""
                        INSERT INTO purchase_history (product_id, price, date, supplier_id)
                        VALUES (?, ?, ?, ?)
                    """, (product_id, unit_price, date, supplier_id))
                    
                    cursor.execute("""
                        UPDATE products 
                        SET quantity = quantity + ?, 
                            unit_cost = ?,
                            expiry_date = ?
                        WHERE id = ?
                    """, (base_qty, unit_price, expiry_date, product_id))
                
                # Create journal entries using the same cursor
                self.auto_accounting.create_purchase_journal_entry(
                    cursor=cursor,
                    purchase_id=invoice_id,
                    supplier_id=supplier_id,
                    total_amount=total_amount,
                    date=date,
                    payment_type=payment_type
                )
                
                conn.commit()
                from database.db_config import log_action
                log_action(self.user['id'], self.user['username'], 'New Purchase', 'Purchases', f'Invoice #{invoice_id} - Total: {total_amount}')
                
                # Emit signals for UI refresh
                self.purchase_added.emit()
                self.load_products()
                QMessageBox.information(self, tr('success'), tr('purchase_saved_success'))
                self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"{tr('error_saving_purchase')}: {e}")

    def check_credit_due_alerts(self):
        """Alert user if any credit purchase is due within the next 5 days."""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                today = datetime.now().date()
                alert_date = today + timedelta(days=5)
                cursor.execute(
                    """
                    SELECT id, supplier_id, due_date, total_amount FROM purchase_invoices
                    WHERE payment_type = 'credit' AND due_date IS NOT NULL AND date(due_date) <= ? AND date(due_date) >= ?
                    AND status = 'pending'
                    """,
                    (alert_date.isoformat(), today.isoformat())
                )
                rows = cursor.fetchall()
                if rows:
                    msgs = []
                    for row in rows:
                        supplier_name = ''
                        sup_id = row['supplier_id']
                        if sup_id:
                            cur2 = conn.cursor()
                            cur2.execute("SELECT name FROM suppliers WHERE id = ?", (sup_id,))
                            sup = cur2.fetchone()
                            supplier_name = sup['name'] if sup else 'Unknown'
                        msgs.append(f"Invoice #{row['id']} (Supplier: {supplier_name}) due on {row['due_date']}: EGP {row['total_amount']:.2f}")
                    QMessageBox.warning(self, tr('credit_due_alert'), "\n".join(msgs))
        except Exception as e:
            print(f"Credit due alert error: {e}")

    def load_products(self):
        """Reload products in all product widgets when inventory changes"""
        for row in range(self.products_table.rowCount()):
            product_widget = self.products_table.cellWidget(row, 0)
            if isinstance(product_widget, PurchaseProductWidget):
                product_widget.load_products()
        if self.products_table.rowCount() == 0:
            self.add_product_row()  # Add initial row
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Purchase Invoice")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)

        # Create supplier selection
        supplier_layout = QHBoxLayout()
        self.supplier_combo = QComboBox()
        self.supplier_combo.setMinimumWidth(200)
        self.load_suppliers()
        
        self.add_supplier_btn = QPushButton("✨ Add New Supplier")
        self.add_supplier_btn.setStyleSheet(get_button_style('blue', padding="6px 12px"))
        self.add_supplier_btn.clicked.connect(self.add_new_supplier)
        
        supplier_layout.addWidget(QLabel("Supplier:"))
        supplier_layout.addWidget(self.supplier_combo)
        supplier_layout.addWidget(self.add_supplier_btn)
        
        # Add spacing before payment type
        supplier_layout.addSpacing(20)
        
        # Payment Type
        supplier_layout.addWidget(QLabel(tr('payment_type') + ":"))
        self.payment_combo = QComboBox()
        self.payment_combo.setMinimumWidth(150)
        self.payment_combo.addItem(tr('cash'), 'cash')
        self.payment_combo.addItem(tr('credit'), 'credit')
        supplier_layout.addWidget(self.payment_combo)
        
        # Due date widgets (hidden unless credit)
        self.due_date_label = QLabel(tr('due_date') + ":")
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat('yyyy-MM-dd')
        # Default to 30 days from today, with today as minimum
        self.due_date_edit.setMinimumDate(datetime.now().date())
        self.due_date_edit.setDate(datetime.now().date() + timedelta(days=30))
        # Initially hide
        self.due_date_label.hide()
        self.due_date_edit.hide()
        supplier_layout.addWidget(self.due_date_label)
        supplier_layout.addWidget(self.due_date_edit)

        # Connect payment type change to toggle due date visibility
        self.payment_combo.currentIndexChanged.connect(self.toggle_due_date_visibility)
        
        supplier_layout.addStretch()
        layout.addLayout(supplier_layout)
        
        # Create product table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(9)
        self.products_table.setHorizontalHeaderLabels([
            tr('product_name'),
            tr('current_stock'),
            tr('type'),
            tr('quantity'), 
            tr('unit'),
            tr('price'),
            tr('duration_mo'),
            tr('total'),
            tr('action')
        ])
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(60)
        self.products_table.verticalHeader().setMinimumSectionSize(60)
        self.products_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Style headers
        header = self.products_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Product Name
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Stock
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Type
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Quantity
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Unit
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Price
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)    # Exp. Mo
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)    # Total  
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)    # Action
            
            # Set column widths - Balanced for header visibility
            self.products_table.setColumnWidth(1, 130)  # Current Stock
            self.products_table.setColumnWidth(2, 80)   # Type
            self.products_table.setColumnWidth(3, 100)  # Quantity
            self.products_table.setColumnWidth(4, 120)  # Unit
            self.products_table.setColumnWidth(5, 100)  # Price
            self.products_table.setColumnWidth(6, 110)  # Exp. (Mo)
            self.products_table.setColumnWidth(7, 100)  # Total
            self.products_table.setColumnWidth(8, 130)  # Action
            
        layout.addWidget(self.products_table)
        
        # Create buttons
        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("➕ Add Product Row")
        self.add_row_btn.setStyleSheet(get_button_style('green'))
        
        self.add_new_btn = QPushButton("✨ Define New Product")
        self.add_new_btn.setStyleSheet(get_button_style('accent2'))
        self.add_new_btn.clicked.connect(self.add_new_product)
        
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.add_new_btn)
        btn_layout.addStretch()
        
        # Total Amount
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_label = QLabel("Total Amount:")
        total_label.setStyleSheet(f"font-weight: bold; color: {COLORS['text_sub']};")
        self.total_amount = QLabel("EGP 0.00")
        self.total_amount.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent']};")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_amount)
        
        # Save button
        self.save_btn = QPushButton("💾 Save Purchase")
        self.save_btn.setStyleSheet(get_button_style('accent'))
        
        layout.addLayout(btn_layout)
        layout.addLayout(total_layout)
        layout.addWidget(self.save_btn)
          # Connect signals
        self.add_row_btn.clicked.connect(self.add_product_row)
        self.save_btn.clicked.connect(self.save_purchase)
        
        # Internal styling for table widgets to prevent text cutoff
        self.products_table.setStyleSheet(self.products_table.styleSheet() + f"""
            QLineEdit, QComboBox {{
                padding: 4px 8px;
                margin: 2px;
            }}
        """)
    
    def setup_connections(self, suppliers_module):
        """Connect to suppliers module signals"""
        suppliers_module.supplier_added.connect(self.load_suppliers)
        
    def add_new_supplier(self):
        """Open dialog to define a new supplier directly from Purchases"""
        from modules.suppliers import SupplierDialog
        dialog = SupplierDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO suppliers (name, phone, email, address)
                        VALUES (?, ?, ?, ?)
                    """, (data['name'], data['phone'], data['email'], data['address']))
                self.load_suppliers()
                # Set combo to the newly added supplier
                index = self.supplier_combo.findText(data['name'])
                if index >= 0:
                    self.supplier_combo.setCurrentIndex(index)
                
                # Emit signal so main window can refresh other modules
                self.supplier_added.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add supplier: {e}")

    def add_new_product(self):
        """Open dialog to define a brand new product"""
        dialog = ProductDefinitionDialog(self)
        if dialog.exec():
            # Signal was emitted by the dialog logic via parent if needed, 
            # but here we just need to refresh our own lists
            self.load_products()
            # Also emit global signal so Inventory knows
            self.purchase_added.emit() 

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
        product_widget.product_changed.connect(lambda data: self.product_selected(row, data))
        self.products_table.setCellWidget(row, 0, product_widget)

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

        # Unit ComboBox (Initially empty, populated when product is selected)
        unit_combo = QComboBox()
        unit_combo.setMinimumWidth(80)
        unit_combo.setMinimumHeight(32)
        unit_combo.addItem("---", None)
        unit_combo.currentIndexChanged.connect(lambda _, w=unit_combo: self.unit_changed(self.products_table.indexAt(w.pos()).row()))
        self.products_table.setCellWidget(row, 4, unit_combo)

        # Price SpinBox (now QLineEdit)
        price_spin = QLineEdit()
        price_spin.setText("0.00")
        price_val = QRegularExpressionValidator(QRegularExpression(r'^\d+[\.,]?\d*$'))
        price_spin.setValidator(price_val)
        price_spin.setMinimumWidth(70)
        price_spin.textChanged.connect(lambda _, w=price_spin: self.update_row_total(self.products_table.indexAt(w.pos()).row()))
        self.products_table.setCellWidget(row, 5, price_spin)

        # Expiry Months input
        expiry_spin = QLineEdit()
        expiry_spin.setText("12")  # Default to 12 months
        expiry_spin.setValidator(QRegularExpressionValidator(QRegularExpression(r'^\d+$')))
        expiry_spin.setMinimumWidth(80)
        expiry_spin.setMinimumHeight(32)
        expiry_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.products_table.setCellWidget(row, 6, expiry_spin)

        # Total Column
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.products_table.setItem(row, 7, total_item)

        delete_btn = QPushButton("🗑️ Remove")
        delete_btn.setFixedSize(110, 32)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(get_action_button_style('red'))
        delete_btn.clicked.connect(self.delete_row)
        self.products_table.setCellWidget(row, 8, delete_btn)

    def product_selected(self, row, product_data):
        if not product_data: return
        
        p_type = product_data.get('product_type', 'bulk')
        
        # Update Stock column
        avail = product_data['quantity']
        if p_type == 'packaged':
            avail_str = f"{avail:.0f} Carton(s)"
        else:
            avail_str = f"{avail*1000:.0f} g" if avail < 1 else f"{avail:.3f} kg"
        self.products_table.item(row, 1).setText(avail_str)
        
        # Update Type column
        type_text = "Packaged" if p_type == 'packaged' else "Bulk"
        self.products_table.item(row, 2).setText(type_text)
        
        # Update units
        unit_combo = self.products_table.cellWidget(row, 4)
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
            
        # Update price and quantity based on selection
        price_spin = self.products_table.cellWidget(row, 5)
        if price_spin and isinstance(price_spin, QLineEdit):
            price_spin.setText(str(product_data.get('unit_price', 0.0)))
            
        self.update_row_total(row)

    def unit_changed(self, row):
        """Handle unit changes to update price if necessary"""
        if row < 0 or row >= self.products_table.rowCount(): return
        product_widget = self.products_table.cellWidget(row, 0)
        unit_combo = self.products_table.cellWidget(row, 4)
        price_spin = self.products_table.cellWidget(row, 5)
        
        if not all([product_widget, unit_combo, price_spin]): return
        
        product_data = product_widget.get_product_data()
        if not product_data or not isinstance(product_data, dict): return
        
        unit = unit_combo.currentText()
        if product_data.get('product_type') == 'packaged':
            if unit == "Bag":
                price_spin.setText(str(product_data.get('piece_price', 0)))
            else:
                price_spin.setText(str(product_data.get('unit_price', 0)))
                
        self.update_row_total(row)

    def update_row_total(self, row: int):
        if row < 0 or row >= self.products_table.rowCount(): return
        qty_spin = self.products_table.cellWidget(row, 3)
        unit_combo = cast(QComboBox, self.products_table.cellWidget(row, 4))
        price_spin = self.products_table.cellWidget(row, 5)
        
        if not qty_spin or not unit_combo or not price_spin:
            return
            
        try:
            qty = float(qty_spin.text().replace(',', '.') or '0')
            price = float(price_spin.text().replace(',', '.') or '0')
        except ValueError:
            qty = 0.0
            price = 0.0
        unit_factor = unit_combo.currentData() or 1.0
        total = (qty * unit_factor) * price
            
        self.products_table.item(row, 7).setText(f"{total:.2f}")
        self.update_total_amount()
    
    def update_total_amount(self):
        total = 0.0
        for row in range(self.products_table.rowCount()):
            # Column 7 is 'Total' (0-indexed)
            if total_item := self.products_table.item(row, 7):
                if text := total_item.text():
                    try:
                        total += float(text)
                    except ValueError:
                        pass
        self.total_amount.setText(f"EGP {total:.2f}")
    
    def delete_row(self):
        button = self.sender()
        if not button: return
        index = self.products_table.indexAt(button.pos())
        if not index.isValid(): return
        
        row = index.row()
        # Get the product widget to remove its product ID from used set
        product_widget = self.products_table.cellWidget(row, 0)
        if isinstance(product_widget, PurchaseProductWidget):
            data = product_widget.get_product_data()
            if data and isinstance(data, dict):
                product_id = data.get('id')
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
                
            # NEW: Validate quantity is > 0
            qty_spin = self.products_table.cellWidget(row, 3)
            if qty_spin:
                try:
                    q = float(qty_spin.text().replace(',', '.') or '0')
                    if q <= 0:
                        QMessageBox.warning(self, "Validation Error", f"Quantity must be greater than 0 in row {row + 1}")
                        return False
                except:
                    QMessageBox.warning(self, "Validation Error", f"Invalid quantity in row {row + 1}")
                    return False
                
        return True

    


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

    def open_view_by_id(self, purchase_id):
        """Open detailed view for a specific purchase"""
        dialog = PurchaseDetailsDialog(self, purchase_id)
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