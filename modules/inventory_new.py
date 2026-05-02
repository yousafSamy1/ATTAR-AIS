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
        # ... existing code ...
        pass

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

            # Change add button to update
            if hasattr(self, 'update_btn'):
                self.update_btn.deleteLater()
            
            self.update_btn = QPushButton("Update Product")
            self.update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
            self.update_btn.clicked.connect(lambda: self.update_product(product_id))
            layout = self.findChild(QVBoxLayout)
            layout.insertWidget(layout.count()-2, self.update_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing product: {str(e)}")

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
                        item = QTableWidgetItem(str(value))
                        if j == 0:  # Make ID column read-only
                            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                        elif j == 3:  # Format unit price as currency
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

    # ... existing code ...
