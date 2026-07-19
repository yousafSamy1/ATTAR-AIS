
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QDoubleSpinBox, QDialog, QMessageBox,
    QFormLayout
)
from PyQt6.QtCore import Qt
from database.db_config import DatabaseConnection
from modules.theme import COLORS, get_current_theme, get_button_style, get_action_button_style
from modules.localization import tr

class RecipeDialog(QDialog):
    def __init__(self, parent=None, recipe_id=None):
        super().__init__(parent)
        self.recipe_id = recipe_id
        self.setWindowTitle("Herb Mixture / Smart Bundle")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Form
        form_card = QFrame()
        form_card.setStyleSheet(f"background: {COLORS['bg_card']}; border: 1.5px solid {COLORS['border']}; border-radius: 15px;")
        fl = QFormLayout(form_card)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(15)
        
        self.product_selector = QComboBox()
        self.product_selector.setMinimumHeight(40)
        self.load_products()
        fl.addRow(f"{tr('product_name')}:", self.product_selector)
        
        self.instructions = QLineEdit()
        self.instructions.setMinimumHeight(40)
        self.instructions.setPlaceholderText("Enter mixing instructions...")
        fl.addRow("Instructions:", self.instructions)
        layout.addWidget(form_card)
        
        # Table
        layout.addWidget(QLabel("INGREDIENTS LIST"))
        self.ing_table = QTableWidget()
        self.ing_table.setColumnCount(3)
        self.ing_table.setHorizontalHeaderLabels(["Ingredient", "Qty", "Action"])
        self.ing_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ing_table.verticalHeader().setVisible(False)
        self.ing_table.setFixedHeight(250)
        self.ing_table.setStyleSheet(f"""
            QTableWidget {{ background: {COLORS['bg_card']}; border: 1.5px solid {COLORS['border']}; border-radius: 12px; }}
            QHeaderView::section {{ background: {COLORS['sidebar']}; color: white; padding: 5px; }}
        """)
        layout.addWidget(self.ing_table)
        
        # Add Input Row
        add_h = QHBoxLayout()
        self.ing_selector = QComboBox()
        self.ing_selector.setMinimumHeight(40)
        self.ing_selector.setMinimumWidth(200)
        self.load_ingredients()
        
        self.qty_box = QDoubleSpinBox()
        self.qty_box.setMinimumHeight(40)
        self.qty_box.setRange(0.001, 10000)
        
        self.add_ing_btn = QPushButton("➕ Add")
        self.add_ing_btn.setMinimumHeight(40)
        self.add_ing_btn.setStyleSheet(get_button_style('blue'))
        self.add_ing_btn.clicked.connect(self.add_ingredient_row)
        
        add_h.addWidget(self.ing_selector)
        add_h.addWidget(self.qty_box)
        add_h.addWidget(self.add_ing_btn)
        layout.addLayout(add_h)
        
        # Footer
        self.save_btn = QPushButton("💾 Save Recipe")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setStyleSheet(get_button_style('accent', padding="12px"))
        self.save_btn.clicked.connect(self.save_recipe)
        layout.addWidget(self.save_btn)

    def load_products(self):
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                # Load ALL products to ensure the dropdown isn't empty
                cur.execute("SELECT id, name FROM products ORDER BY is_recipe DESC, name ASC")
                for r in cur.fetchall():
                    self.product_selector.addItem(r["name"], r["id"])
        except Exception as e: print(f"Load products error: {e}")

    def load_ingredients(self):
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM products WHERE is_recipe=0 ORDER BY name ASC")
                for r in cur.fetchall():
                    self.ing_selector.addItem(r["name"], r["id"])
        except Exception as e: print(f"Load ingredients error: {e}")

    def add_ingredient_row(self):
        row = self.ing_table.rowCount()
        self.ing_table.insertRow(row)
        self.ing_table.setRowHeight(row, 45)
        
        item = QTableWidgetItem(self.ing_selector.currentText())
        item.setData(Qt.ItemDataRole.UserRole, self.ing_selector.currentData())
        self.ing_table.setItem(row, 0, item)
        self.ing_table.setItem(row, 1, QTableWidgetItem(f"{self.qty_box.value():.3f}"))
        
        del_btn = QPushButton("🗑️ Delete")
        del_btn.setFixedSize(110, 32)
        del_btn.setStyleSheet(get_action_button_style('red'))
        del_btn.clicked.connect(lambda: self.ing_table.removeRow(self.ing_table.currentRow()))
        self.ing_table.setCellWidget(row, 2, del_btn)

    def save_recipe(self):
        pid = self.product_selector.currentData()
        if not pid: return
        
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                # 1. Update or Insert Recipe
                cur.execute("INSERT OR REPLACE INTO recipes (product_id, instructions) VALUES (?, ?)", (pid, self.instructions.text()))
                
                # Get the recipe ID (either newly inserted or existing)
                cur.execute("SELECT id FROM recipes WHERE product_id=?", (pid,))
                rid = cur.fetchone()["id"]

                # 2. Update Product as a recipe
                cur.execute("UPDATE products SET is_recipe=1 WHERE id=?", (pid,))

                # 3. Save Ingredients
                cur.execute("DELETE FROM recipe_ingredients WHERE recipe_id=?", (rid,))
                for r in range(self.ing_table.rowCount()):
                    ing_id = self.ing_table.item(r, 0).data(Qt.ItemDataRole.UserRole)
                    qty = float(self.ing_table.item(r, 1).text())
                    cur.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (?, ?, ?)", (rid, ing_id, qty))
                
                conn.commit()
            QMessageBox.information(self, "Success", "Mixture saved successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mixture: {e}")

class RecipesModule(QWidget):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Header
        t = QLabel("🌿 Herb Mixtures & Smart Bundles")
        t.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(t)

        is_admin = False
        if self.user and isinstance(self.user, dict):
            is_admin = (self.user.get('role') == 'admin')
        elif self.user and hasattr(self.user, 'get'):
            is_admin = (self.user.get('role') == 'admin')
        
        # Add Recipe Button
        btn_h = QHBoxLayout()
        add_btn = QPushButton("➕ Define New Mixture")
        add_btn.setFixedWidth(220)
        add_btn.setStyleSheet(get_button_style('accent'))
        add_btn.clicked.connect(lambda: self.open_dialog())
        add_btn.setVisible(is_admin)
        btn_h.addWidget(add_btn)
        btn_h.addStretch()
        layout.addLayout(btn_h)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Mix Name", "Ingredients Count", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 280)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                alternate-background-color: {COLORS['bg'] if get_current_theme() == 'dark' else '#F8FAFC'};
                border: 1.5px solid {COLORS['border']};
                border-radius: 15px;
            }}
            QTableWidget::item {{
                color: {COLORS['text_main']};
                padding: 10px;
                font-size: 14px;
            }}
        """)
        self.table.horizontalHeader().setMinimumHeight(50)
        self.table.verticalHeader().setDefaultSectionSize(60)
        layout.addWidget(self.table)
        
        self.load_recipes()

    def load_recipes(self):
        try:
            # Start loading data

            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT r.id, p.name, (SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id=r.id) as ings 
                    FROM recipes r JOIN products p ON r.product_id = p.id
                """)
                rows = cur.fetchall()
                self.table.setRowCount(len(rows))
                self.table.setColumnHidden(2, not (self.user and self.user.get('role') == 'admin'))
                
                for i, r in enumerate(rows):
                    self.table.setItem(i, 0, QTableWidgetItem(str(r["name"])))
                    self.table.setItem(i, 1, QTableWidgetItem(f"{r['ings']} Ingredients"))
                    
                    # Actions Container (Admin Only)
                    if self.user and self.user.get('role') == 'admin':
                        actions_widget = QWidget()
                        actions_widget.setMinimumHeight(50)
                        actions_widget.setStyleSheet("background: transparent; border: none;")
                        actions_layout = QHBoxLayout(actions_widget)
                        actions_layout.setContentsMargins(5, 5, 5, 5)
                        actions_layout.setSpacing(10)
                        
                        edit_btn = QPushButton("✏️ Edit")
                        edit_btn.setFixedSize(120, 32)
                        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        edit_btn.setStyleSheet(get_action_button_style('accent'))
                        edit_btn.clicked.connect(lambda _, rid=r["id"]: self.open_dialog(rid))
                        
                        del_btn = QPushButton("🗑️ Remove")
                        del_btn.setFixedSize(120, 32)
                        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        del_btn.setStyleSheet(get_action_button_style('red'))
                        del_btn.clicked.connect(lambda _, rid=r["id"]: self.delete_recipe(rid))
                        
                        actions_layout.addStretch()
                        actions_layout.addWidget(edit_btn)
                        actions_layout.addWidget(del_btn)
                        actions_layout.addStretch()
                        self.table.setRowHeight(i, 50)
                        self.table.setCellWidget(i, 2, actions_widget)
        except Exception as e:
            print(f"Load recipes error: {e}")
            import traceback
            traceback.print_exc()

    def delete_recipe(self, rid):
        if QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this mixture?") == QMessageBox.StandardButton.Yes:
            try:
                with DatabaseConnection() as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM recipe_ingredients WHERE recipe_id=?", (rid,))
                    cur.execute("DELETE FROM recipes WHERE id=?", (rid,))
                    conn.commit()
                self.load_recipes()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def open_dialog(self, rid=None):
        if RecipeDialog(self, rid).exec():
            self.load_recipes()
