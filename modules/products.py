
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLineEdit, QMessageBox, QDialog, QFormLayout, QComboBox, 
                             QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor
from database.db_config import DatabaseConnection
from modules.theme import COLORS, get_button_style, get_action_button_style
from modules.localization import tr

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(tr('product_details'))
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["bulk", "packaged"])
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        
        self.min_qty_spin = QDoubleSpinBox()
        self.min_qty_spin.setMaximum(999999)

        if self.product_data:
            self.name_edit.setText(self.product_data.get('name', ''))
            self.desc_edit.setText(self.product_data.get('description', ''))
            self.type_combo.setCurrentText(self.product_data.get('product_type', 'bulk'))
            self.price_spin.setValue(self.product_data.get('unit_price', 0.0))
            self.min_qty_spin.setValue(self.product_data.get('minimum_quantity', 0.0))

        form.addRow(f"{tr('product_name')}:", self.name_edit)
        form.addRow(f"{tr('description')}:", self.desc_edit)
        form.addRow(f"{tr('type')}:", self.type_combo)
        form.addRow(f"{tr('price')}:", self.price_spin)
        form.addRow(f"{tr('min_qty')}:", self.min_qty_spin)
        
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns = QHBoxLayout()
        save_btn = QPushButton("💾 " + tr('save'))
        save_btn.setStyleSheet(get_button_style('accent'))
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ " + tr('cancel'))
        cancel_btn.setStyleSheet(get_button_style('bg_mid'))
        cancel_btn.clicked.connect(self.reject)
        
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'description': self.desc_edit.text(),
            'product_type': self.type_combo.currentText(),
            'unit_price': self.price_spin.value(),
            'minimum_quantity': self.min_qty_spin.value()
        }

class ProductsModule(QWidget):
    product_changed = pyqtSignal()

    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        self.load_products()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel(tr('products'))
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        add_btn = QPushButton(f"➕ {tr('add_product')}")
        add_btn.setFixedWidth(220)
        add_btn.setStyleSheet(get_button_style('accent'))
        add_btn.clicked.connect(self.add_product)
        is_admin = self.user and self.user.get('role') == 'admin'
        add_btn.setVisible(is_admin)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {tr('search_products')}")
        self.search_input.setStyleSheet(f"padding: 10px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: {COLORS['bg_card']};")
        self.search_input.textChanged.connect(self.filter_products)
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", tr('product_name'), tr('description'), tr('type'), tr('price'), tr('actions')
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def load_products(self):
        self.table.setRowCount(0)
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, description, product_type, unit_price FROM products ORDER BY name ASC")
                products = cursor.fetchall()
                
                # Standardized admin check
                is_admin = False
                if self.user and hasattr(self.user, 'get'):
                    is_admin = (self.user.get('role') == 'admin')
                
                self.table.setColumnHidden(5, not is_admin)
                
                for row_idx, product in enumerate(products):
                    self.table.insertRow(row_idx)
                    for col_idx, data in enumerate(product[:5]):
                        item = QTableWidgetItem(str(data))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        # Explicitly make cells non-editable
                        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                        self.table.setItem(row_idx, col_idx, item)
                    
                    # Actions
                    if not is_admin:
                        continue
                        
                    actions_widget = QWidget()
                    actions_widget.setMinimumHeight(50)
                    actions_widget.setStyleSheet("background: transparent; border: none;")
                    act_layout = QHBoxLayout(actions_widget)
                    act_layout.setContentsMargins(5, 5, 5, 5)
                    act_layout.setSpacing(8)
                    
                    # Restrict editing/deleting to admin only
                    can_edit = is_admin 
                    
                    edit_btn = QPushButton("✏️ " + tr('edit'))
                    edit_btn.setFixedSize(120, 32)
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.setStyleSheet(get_action_button_style('accent'))
                    edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_product(r))
                    edit_btn.setVisible(can_edit)
                    
                    del_btn = QPushButton("🗑️ " + tr('delete'))
                    del_btn.setFixedSize(120, 32)
                    del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    del_btn.setStyleSheet(get_action_button_style('red'))
                    del_btn.clicked.connect(lambda _, r=row_idx: self.delete_product(r))
                    del_btn.setVisible(can_edit)
                    
                    act_layout.addStretch()
                    act_layout.addWidget(edit_btn)
                    act_layout.addWidget(del_btn)
                    act_layout.addStretch()
                    self.table.setRowHeight(row_idx, 50)
                    self.table.setCellWidget(row_idx, 5, actions_widget)
                
                # Fix column widths
                header = self.table.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Name
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Actions
                self.table.setColumnWidth(0, 45)
                self.table.setColumnWidth(5, 280)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load products: {str(e)}")

    def add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO products (name, description, product_type, unit_price, minimum_quantity, quantity)
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (data['name'], data['description'], data['product_type'], 
                          data['unit_price'], data['minimum_quantity']))
                    conn.commit()
                self.load_products()
                self.product_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add product: {str(e)}")

    def edit_product(self, row):
        p_id = self.table.item(row, 0).text()
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE id=?", (p_id,))
                columns = [column[0] for column in cursor.description]
                product = dict(zip(columns, cursor.fetchone()))
                
            dialog = ProductDialog(self, product)
            if dialog.exec():
                data = dialog.get_data()
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE products 
                        SET name=?, description=?, product_type=?, unit_price=?, minimum_quantity=?
                        WHERE id=?
                    """, (data['name'], data['description'], data['product_type'], 
                          data['unit_price'], data['minimum_quantity'], p_id))
                    conn.commit()
                self.load_products()
                self.product_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not edit product: {str(e)}")

    def delete_product(self, row):
        p_id = self.table.item(row, 0).text()
        p_name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(self, 'Delete Product', 
                                    f"Are you sure you want to delete '{p_name}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM products WHERE id=?", (p_id,))
                    conn.commit()
                self.load_products()
                self.product_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete product: {str(e)}")

    def filter_products(self):
        text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
