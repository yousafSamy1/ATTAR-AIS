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
    QComboBox,         # Drop-down selection
    QMessageBox,       # Modal message dialog
    QHeaderView,       # Header view for tables
    QTabWidget         # Tabbed widget for sections
)
from PyQt6.QtCore import (
    Qt,               # Core non-widget functionality
    QTimer,           # Timer for periodic events
    pyqtSignal        # Signal/slot communication
)
from datetime import datetime
from PyQt6.QtGui import QColor  # Color handling

# Database Configuration
from database.db_config import DatabaseConnection  # Custom database connection handler
from modules.theme import COLORS, get_button_style
from modules.localization import tr

class InventoryModule(QWidget):
    product_deleted = pyqtSignal(int)  # Signal emitted when a product is deleted
    product_added = pyqtSignal()  # Signal emitted when a product is added
    product_updated = pyqtSignal()  # Signal emitted when a product is updated
    
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self._alert_shown = False
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
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Header
        header = QLabel("Inventory Management")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)

        # Sections (Tabs)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLORS['border']}; border-top: none; background: {COLORS['bg_card']}; border-radius: 0 0 6px 6px; }}
            QTabBar::tab {{ background: {COLORS['bg']}; color: {COLORS['text_dim']}; padding: 12px 24px; font-weight: bold; border: 1px solid {COLORS['border']}; border-bottom: none; border-radius: 6px 6px 0 0; margin-right: 2px; }}
            QTabBar::tab:selected {{ background: {COLORS['bg_card']}; color: {COLORS['accent']}; border-bottom: 2px solid {COLORS['accent']}; }}
        """)
        
        # Bulk Tab
        self.bulk_tab = QWidget()
        self.bulk_layout = QVBoxLayout(self.bulk_tab)
        self.bulk_table = self.create_table()
        self.bulk_layout.addWidget(self.bulk_table)
        self.tabs.addTab(self.bulk_tab, f"📦 {tr('bulk_products')}")
        
        # Packaged Tab
        self.packaged_tab = QWidget()
        self.packaged_layout = QVBoxLayout(self.packaged_tab)
        self.packaged_table = self.create_table()
        self.packaged_layout.addWidget(self.packaged_table)
        self.tabs.addTab(self.packaged_tab, f"🏷️ {tr('packaged_products')}")
        
        # Low Stock Tab
        self.low_stock_tab = QWidget()
        self.low_stock_layout = QVBoxLayout(self.low_stock_tab)
        self.low_stock_table = self.create_table()
        self.low_stock_layout.addWidget(self.low_stock_table)
        self.tabs.addTab(self.low_stock_tab, f"⚠️ {tr('low_stock')}")

        # Near Expired Tab
        self.expiry_tab = QWidget()
        self.expiry_layout = QVBoxLayout(self.expiry_tab)
        self.expiry_table = self.create_table()
        self.expiry_layout.addWidget(self.expiry_table)
        self.tabs.addTab(self.expiry_tab, f"⏰ {tr('near_expired')}")
        
        layout.addWidget(self.tabs)

        # Action Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Robust admin check
        is_admin = False
        if self.user and hasattr(self.user, 'get'):
            is_admin = (self.user.get('role') == 'admin')
        
        can_edit = is_admin

        # Edit button with modern styling
        edit_btn = QPushButton("✏️ " + (tr('edit') + " " + tr('selected') if tr('selected') != 'selected' else "Edit Selected"))
        edit_btn.setStyleSheet(get_button_style('blue'))
        edit_btn.clicked.connect(self.edit_selected_product)
        edit_btn.setVisible(can_edit)
        buttons_layout.addWidget(edit_btn)

        # Delete button with modern styling
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setStyleSheet(get_button_style('red'))
        delete_btn.clicked.connect(self.delete_selected_product)
        delete_btn.setVisible(can_edit)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # Create search layout
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products by name, description...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 16px;
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 14px;
                background-color: {COLORS['bg_card']};
                margin-bottom: 10px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        layout.insertLayout(1, search_layout)

    def create_table(self):
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "ID", 
            tr('product_name'), 
            tr('description'), 
            tr('price'), 
            tr('quantity'), 
            tr('min_qty'), 
            tr('expiry')
        ])
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(40)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.itemDoubleClicked.connect(self.edit_selected_product)
        
        # Configure column stretching
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Product Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description
        
        return table
        
        # Create search layout
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products by name, description...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 16px;
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 14px;
                background-color: {COLORS['bg_card']};
                margin-bottom: 10px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        layout.insertLayout(1, search_layout)

    def get_active_table(self):
        return self.tabs.currentWidget().findChild(QTableWidget)

    def edit_selected_product(self):
        table = self.get_active_table()
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a product to edit")
            return

        try:
            id_item = table.item(row, 0)
            if not id_item: return
            product_id = int(id_item.text())
            
            # Show the same ProductDefinitionDialog for editing
            from modules.purchases import ProductDefinitionDialog
            dialog = ProductDefinitionDialog(self, edit_id=product_id)
            if dialog.exec():
                self.load_products()
                self.product_updated.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing product: {str(e)}")

    def delete_selected_product(self):
        table = self.get_active_table()
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select a product to delete")
            return
        
        try:
            id_item = table.item(row, 0)
            name_item = table.item(row, 1)
            
            if not all([isinstance(x, QTableWidgetItem) for x in [id_item, name_item]]):
                QMessageBox.warning(self, "Error", "Could not get product information")
                return
            
            product_id = int(id_item.text())
            product_name = name_item.text()

            reply = QMessageBox.question(self, 'Confirm Delete',
                                       f'Are you sure you want to delete product "{product_name}"?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
                
                QMessageBox.information(self, "Success", "Product deleted successfully!")
                self.load_products()
                self.product_deleted.emit(product_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting product: {str(e)}")

    def toggle_product_type_fields(self, index):
        pass # Moved to dialog

    def load_products(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products ORDER BY name")
                products = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

                bulk_products = [p for p in products if p.get('product_type') != 'packaged']
                packaged_products = [p for p in products if p.get('product_type') == 'packaged']
                low_stock_products = [p for p in products if p.get('quantity', 0) <= p.get('minimum_quantity', 0)]
                
                # Near Expired filter (<= 30 days or already expired)
                near_expired_products = []
                today = datetime.now()
                for p in products:
                    expiry_date_str = p.get('expiry_date')
                    if expiry_date_str:
                        try:
                            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                            if (expiry_date - today).days <= 30:
                                near_expired_products.append(p)
                        except:
                            pass

                self.populate_table(self.bulk_table, bulk_products)
                self.populate_table(self.packaged_table, packaged_products)
                self.populate_table(self.low_stock_table, low_stock_products)
                self.populate_table(self.expiry_table, near_expired_products)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading products: {str(e)}")

    def populate_table(self, table, products):
        table.setRowCount(len(products))
        for row, product in enumerate(products):
            table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            table.setItem(row, 1, QTableWidgetItem(product['name']))
            table.setItem(row, 2, QTableWidgetItem(product['description']))
            
            p_type = product.get('product_type', 'bulk')
            price = product['unit_price']
            qty = product['quantity']
            min_qty = product['minimum_quantity']
            
            if p_type == 'packaged':
                table.setItem(row, 3, QTableWidgetItem(f"EGP {price:.2f}/Ctn (Bag: {product['piece_price']:.2f})"))
                table.setItem(row, 4, QTableWidgetItem(f"{qty:.0f} Cartons"))
                table.setItem(row, 5, QTableWidgetItem(f"{min_qty:.0f} Cartons"))
            else:
                qty_str = f"{qty*1000:.0f} g" if qty < 1 else f"{qty:.3f} kg"
                min_qty_str = f"{min_qty*1000:.0f} g" if min_qty < 1 else f"{min_qty:.3f} kg"
                table.setItem(row, 3, QTableWidgetItem(f"EGP {price:.2f}/kg"))
                table.setItem(row, 4, QTableWidgetItem(qty_str))
                table.setItem(row, 5, QTableWidgetItem(min_qty_str))
            
            # Expiry Column
            expiry_str = "N/A"
            expiry_date_str = product.get('expiry_date')
            if expiry_date_str:
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                    today = datetime.now()
                    diff = expiry_date - today
                    days_left = diff.days
                    
                    if days_left < 0:
                        expiry_str = f"❌ Expired ({abs(days_left)}d ago)"
                    elif days_left == 0:
                        expiry_str = "⚠️ Expires Today"
                    elif days_left < 30:
                        expiry_str = f"⚠️ {days_left} days left"
                    else:
                        months = days_left // 30
                        expiry_str = f"✅ {months} months left"
                except:
                    expiry_str = expiry_date_str
            
            table.setItem(row, 6, QTableWidgetItem(expiry_str))
            
            for col in range(7):
                item = table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    
                    # Color coding for expiry
                    if col == 6:
                        if "❌" in expiry_str:
                            item.setForeground(QColor("#EF4444")) # Red
                        elif "⚠️" in expiry_str:
                            item.setForeground(QColor("#F59E0B")) # Amber
                        elif "✅" in expiry_str:
                            item.setForeground(QColor("#10B981")) # Green
                    
        header = table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
            for i in range(table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def filter_products(self):
        search_text = self.search_input.text().lower()
        for table in [self.bulk_table, self.packaged_table, self.low_stock_table, self.expiry_table]:
            for row in range(table.rowCount()):
                match = False
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item and search_text in item.text().lower():
                        match = True
                        break
                table.setRowHidden(row, not match)
            
    def show_low_stock_warning(self):
        """Show warning for products below minimum quantity"""
        if self._alert_shown:
            return
            
        low_stock_products = []
        for row in range(self.low_stock_table.rowCount()):
            name_item = self.low_stock_table.item(row, 1)
            qty_item = self.low_stock_table.item(row, 4)
            min_qty_item = self.low_stock_table.item(row, 5)
            if all([name_item, qty_item, min_qty_item]):
                low_stock_products.append(f"{name_item.text()} (Current: {qty_item.text()}, Min: {min_qty_item.text()})")
        
        if low_stock_products:
            warning_msg = "⚠️ Low Stock Alert ⚠️\n\n"
            warning_msg += "The following products need to be restocked:\n\n"
            warning_msg += "\n".join(f"• {name}" for name in low_stock_products)
            warning_msg += "\n\nPlease create purchase orders for these items."
            QMessageBox.warning(self, "Low Stock Warning", warning_msg)
            self._alert_shown = True

    def showEvent(self, a0):
        """Called when the widget becomes visible"""
        super().showEvent(a0)
        self.load_products()
        # Show warning after 500ms delay
        self.warning_timer.start(500)
        self.bulk_table.clearSelection()
        self.packaged_table.clearSelection()
        self.low_stock_table.clearSelection()
        self.expiry_table.clearSelection()

    def hideEvent(self, a0):
        """Called when the widget becomes hidden"""
        super().hideEvent(a0)
        self.refresh_timer.stop()
        self.bulk_table.clearSelection()
        self.packaged_table.clearSelection()
        self.low_stock_table.clearSelection()
