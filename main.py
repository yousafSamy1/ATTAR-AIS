import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QMessageBox, QDialog,
    QTableWidget, QTableWidgetItem, QFormLayout, QHeaderView, QMenu,
    QFrame, QScrollArea, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QAction

from database.db_config import DatabaseConnection, init_database
from modules.sales import SalesModule
from modules.purchases import PurchasesModule
from modules.inventory import InventoryModule
from modules.customers import CustomersModule
from modules.suppliers import SuppliersModule
from modules.expenses import ExpensesModule
from modules.financial_reports import FinancialReportsModule
from modules.auto_accounting import AutoAccountingModule
from modules.kpis import KPIModule

# =========================================================
#  Attar AIS — Ultra Premium Slate & Emerald Theme
# =========================================================
COLORS = {
    "bg":            "#F8FAFC",   # Very light slate/gray
    "bg_card":       "#FFFFFF",   # Pure white
    "bg_mid":        "#F1F5F9",   # Soft slate for alternating rows
    "sidebar":       "#0F172A",   # Deep slate 900
    "sidebar_mid":   "#1E293B",   # Slate 800 (hover)
    "sidebar_active":"#065F46",   # Emerald 800 (active state)
    "accent":        "#059669",   # Emerald 600 (primary buttons)
    "accent2":       "#10B981",   # Emerald 500 (highlights)
    "accent_light":  "#ECFDF5",   # Emerald 50 (selections)
    "green":         "#059669",
    "green_light":   "#D1FAE5",
    "red":           "#DC2626",   # Red 600
    "red_light":     "#FEE2E2",
    "yellow":        "#D97706",   # Amber 600
    "yellow_light":  "#FEF3C7",
    "blue":          "#2563EB",   # Blue 600
    "blue_light":    "#DBEAFE",
    "text_main":     "#0F172A",   # Slate 900
    "text_sub":      "#475569",   # Slate 600
    "text_dim":      "#94A3B8",   # Slate 400
    "border":        "#E2E8F0",   # Slate 200
    "separator":     "#CBD5E1",   # Slate 300
}

GLOBAL_STYLE = f"""
QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text_main']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}}
QScrollBar:vertical {{
    background: {COLORS['separator']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['green']};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {COLORS['separator']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['green']};
    border-radius: 4px;
}}
QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_mid']};
    color: {COLORS['text_main']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    font-size: 13px;
    selection-background-color: {COLORS['green_light']};
}}
QTableWidget::item {{
    padding: 10px 14px;
    border-bottom: 1px solid {COLORS['separator']};
}}
QTableWidget::item:selected {{
    background-color: {COLORS['green_light']};
    color: {COLORS['green']};
}}
QHeaderView::section {{
    background-color: {COLORS['sidebar']};
    color: white;
    padding: 11px 14px;
    border: none;
    border-right: 1px solid {COLORS['sidebar_mid']};
    font-weight: bold;
    font-size: 13px;
    letter-spacing: 0.8px;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QTextEdit {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_main']};
    border: 1.5px solid {COLORS['border']};
    border-radius: 7px;
    padding: 8px 12px;
    font-size: 13px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1.5px solid {COLORS['green']};
    background-color: {COLORS['green_light']};
}}
QComboBox::drop-down {{ border: none; padding-right: 10px; }}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_main']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['green_light']};
    selection-color: {COLORS['green']};
}}
QMessageBox {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_main']}; }}
QDialog {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_main']}; }}
QPushButton {{
    background-color: {COLORS['sidebar']};
    color: white;
    border: none;
    border-radius: 7px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {COLORS['sidebar_mid']}; }}
QPushButton:pressed {{ background-color: {COLORS['accent']}; color: white; }}
"""


def make_card(title, value, color, icon="", bg_light=""):
    card = QFrame()
    card.setMinimumHeight(138)
    bg = bg_light if bg_light else COLORS['bg_card']
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {bg};
            border: 1px solid {COLORS['border']};
            border-left: 6px solid {color};
            border-radius: 14px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(8)

    top = QHBoxLayout()
    icon_lbl = QLabel(icon)
    icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
    top.addWidget(icon_lbl)
    top.addStretch()
    t = QLabel(title.upper())
    t.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; font-weight: bold; background: transparent; border: none; letter-spacing: 1.5px;")
    t.setAlignment(Qt.AlignmentFlag.AlignRight)
    top.addWidget(t)
    layout.addLayout(top)

    v = QLabel(value)
    v.setStyleSheet(f"color: {color}; font-size: 25px; font-weight: bold; background: transparent; border: none;")
    layout.addWidget(v)
    return card, v


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attar AIS  —  Spice & Herb Store Management")
        self.setMinimumSize(1280, 820)
        self.active_button = None
        self._metric_labels = {}

        self.setStyleSheet(GLOBAL_STYLE)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QHBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg']};")
        root_layout.addWidget(self.stack, 1)

        self.auto_accounting   = AutoAccountingModule()
        self.sales_module      = SalesModule(self.auto_accounting)
        self.purchases_module  = PurchasesModule(self.auto_accounting)
        self.inventory_module  = InventoryModule()
        self.customers_module  = CustomersModule()
        self.suppliers_module  = SuppliersModule()
        self.expenses_module   = ExpensesModule(self.auto_accounting)
        self.financial_module  = FinancialReportsModule()
        self.kpi_module        = KPIModule()

        for mod in [self.sales_module, self.purchases_module, self.inventory_module,
                    self.customers_module, self.suppliers_module,
                    self.expenses_module, self.financial_module, self.kpi_module]:
            mod.setStyleSheet(GLOBAL_STYLE)

        self.sales_module.setup_connections(self.customers_module)
        self.purchases_module.setup_connections(self.suppliers_module)

        self.inventory_module.product_added.connect(self.sales_module.load_products)
        self.inventory_module.product_added.connect(self.purchases_module.load_products)
        self.inventory_module.product_updated.connect(self.sales_module.load_products)
        self.inventory_module.product_updated.connect(self.purchases_module.load_products)
        self.inventory_module.product_deleted.connect(self.sales_module.load_products)
        self.inventory_module.product_deleted.connect(self.purchases_module.load_products)

        self.sales_module.sale_added.connect(self.refresh_dashboard)
        self.purchases_module.purchase_added.connect(self.refresh_dashboard)
        self.expenses_module.expense_added.connect(self.refresh_dashboard)

        self.welcome_widget = self._build_dashboard()
        self.stack.addWidget(self.welcome_widget)
        self.stack.addWidget(self.sales_module)
        self.stack.addWidget(self.purchases_module)
        self.stack.addWidget(self.inventory_module)
        self.stack.addWidget(self.customers_module)
        self.stack.addWidget(self.suppliers_module)
        self.stack.addWidget(self.expenses_module)
        self.stack.addWidget(self.financial_module)
        self.stack.addWidget(self.kpi_module)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_dashboard)
        self._refresh_timer.start(8000)

    # ----------------------------------------------------------
    # Sidebar
    # ----------------------------------------------------------
    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(238)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-right: 1px solid #0F2018;
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(130)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #020617, stop:1 {COLORS['sidebar']});
                border-bottom: 2px solid {COLORS['sidebar_mid']};
            }}
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(4)

        emoji_lbl = QLabel("🌿")
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_lbl.setStyleSheet("font-size: 38px; background: transparent; border: none;")
        logo_layout.addWidget(emoji_lbl)

        title_lbl = QLabel("ATTAR  AIS")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"""
            color: {COLORS['accent2']};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 5px;
            background: transparent;
            border: none;
        """)
        logo_layout.addWidget(title_lbl)

        sub_lbl = QLabel("Spice & Herb Store")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("color: #6BAF85; font-size: 10px; background: transparent; border: none; letter-spacing: 1.5px;")
        logo_layout.addWidget(sub_lbl)
        layout.addWidget(logo_frame)

        nav_items = [
            ("🏠", "Dashboard",     0),
            ("💰", "Sales",         1),
            ("🛒", "Purchases",     2),
            ("📦", "Inventory",     3),
            ("👤", "Customers",     4),
            ("🏭", "Suppliers",     5),
            ("💸", "Expenses",      6),
        ]

        layout.addSpacing(10)
        for icon, label, idx in nav_items:
            btn = self._make_nav_btn(icon, label, idx)
            layout.addWidget(btn)

        layout.addWidget(self._section_label("ACCOUNTING"))
        layout.addWidget(self._make_nav_btn("📒", "Journal Entries", 7))

        layout.addWidget(self._section_label("REPORTS & ANALYTICS"))
        layout.addWidget(self._make_nav_btn("📈", "Business Analytics", 8))

        reports_btn = QPushButton("   📊  Account Statement")
        reports_btn.setStyleSheet(self._nav_btn_style())
        reports_btn.setFixedHeight(50)

        reports_menu = QMenu(self)
        reports_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_main']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{ padding: 10px 20px; border-radius: 6px; }}
            QMenu::item:selected {{
                background-color: {COLORS['green_light']};
                color: {COLORS['green']};
            }}
        """)
        customer_action = QAction("👤  Customer Statement", self)
        customer_action.triggered.connect(lambda: self._show_account_statement("customer"))
        supplier_action = QAction("🏭  Supplier Statement", self)
        supplier_action.triggered.connect(lambda: self._show_account_statement("supplier"))
        reports_menu.addAction(customer_action)
        reports_menu.addAction(supplier_action)
        reports_btn.setMenu(reports_menu)
        layout.addWidget(reports_btn)

        layout.addStretch()

        tut_btn = QPushButton("   🎓  دليل الموظف الجديد")
        tut_btn.setStyleSheet(self._nav_btn_style())
        tut_btn.setFixedHeight(50)
        tut_btn.clicked.connect(self._show_tutorial)
        layout.addWidget(tut_btn)

        footer = QLabel("v2.5 · Premium Edition")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #64748B; font-size: 11px; padding: 12px; background: transparent; border: none; letter-spacing: 1px;")
        layout.addWidget(footer)

        return sidebar

    def _nav_btn_style(self, active=False):
        if active:
            return f"""
                QPushButton {{
                    background-color: {COLORS['sidebar_active']};
                    color: white;
                    border: none;
                    border-radius: 0;
                    border-left: 4px solid {COLORS['accent2']};
                    padding: 0 16px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {COLORS['sidebar_active']}; }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_dim']};
                border: none;
                border-left: 4px solid transparent;
                border-radius: 0;
                padding: 0 16px;
                text-align: left;
                font-size: 14px;
                font-weight: normal;
                transition: 0.3s;
            }}
            QPushButton:hover {{
                background-color: {COLORS['sidebar_mid']};
                color: white;
                border-left: 4px solid {COLORS['text_sub']};
            }}
        """

    def _make_nav_btn(self, icon, label, idx):
        btn = QPushButton(f"  {icon}  {label}")
        btn.setFixedHeight(50)
        btn.setStyleSheet(self._nav_btn_style(idx == 0))
        btn.setFont(QFont("Segoe UI", 11))
        if idx == 0:
            self.active_button = btn

        def _on_click(*args, b=btn, i=idx):
            if self.active_button:
                self.active_button.setStyleSheet(self._nav_btn_style(False))
            b.setStyleSheet(self._nav_btn_style(True))
            self.active_button = b
            self.stack.setCurrentIndex(i)
        btn.clicked.connect(_on_click)
        return btn

    def _section_label(self, text):
        lbl = QLabel(f"  {text}")
        lbl.setFixedHeight(34)
        lbl.setStyleSheet(f"""
            color: {COLORS['text_sub']};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2.5px;
            background-color: {COLORS['sidebar']};
            border-top: 1px solid {COLORS['sidebar_mid']};
            padding-top: 8px;
        """)
        return lbl

    # ----------------------------------------------------------
    # Dashboard
    # ----------------------------------------------------------
    def _build_dashboard(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ background: {COLORS['bg']}; border: none; }}")

        container = QWidget()
        container.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        # ── Header banner ──────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['sidebar']}, stop:1 {COLORS['sidebar_active']});
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }}
        """)
        hdr_layout = QHBoxLayout(header_frame)
        hdr_layout.setContentsMargins(30, 24, 30, 24)

        left_hdr = QVBoxLayout()
        t1 = QLabel("✨ Attar AIS Pro — Spice & Herb Management")
        t1.setStyleSheet(f"color: white; font-size: 24px; font-weight: bold; background: transparent; border: none;")
        t2 = QLabel("Enterprise Accounting Information System · Live Metrics")
        t2.setStyleSheet(f"color: {COLORS['green_light']}; font-size: 13px; background: transparent; border: none; letter-spacing: 0.8px;")
        left_hdr.addWidget(t1)
        left_hdr.addWidget(t2)
        hdr_layout.addLayout(left_hdr)
        hdr_layout.addStretch()

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(f"color: {COLORS['green_light']}; font-size: 13px; background: transparent; border: none; font-weight: bold;")
        self._update_clock()
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self._update_clock)
        clock_timer.start(1000)
        hdr_layout.addWidget(self._clock_lbl)
        layout.addWidget(header_frame)

        # ── Metric Cards ──────────────────────────
        cards_label = QLabel("  KEY METRICS")
        cards_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; font-weight: bold; letter-spacing: 2.5px; background: transparent;")
        layout.addWidget(cards_label)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        metric_defs = [
            ("Today's Sales",    "sales_today",      COLORS["accent"],   "💰", COLORS["accent_light"]),
            ("Monthly Revenue",  "monthly_revenue",  COLORS["green"],    "📈", COLORS["green_light"]),
            ("Inventory Value",  "inventory_value",  COLORS["blue"],     "📦", COLORS["blue_light"]),
            ("Receivables",      "receivables",      COLORS["yellow"],   "🧾", COLORS["yellow_light"]),
            ("Payables",         "payables",         COLORS["red"],      "🏭", COLORS["red_light"]),
            ("Monthly Expenses", "monthly_expenses", COLORS["text_sub"], "💸", COLORS["separator"]),
        ]

        # self._metric_labels was already defined above or we define it here
        for i, (title, key, color, icon, bg_light) in enumerate(metric_defs):
            card, val_lbl = make_card(title, "Loading...", color, icon, bg_light)
            self._metric_labels[key] = val_lbl
            cards_grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(cards_grid)

        # ── Recent Transactions ───────────────────
        act_label = QLabel("  RECENT TRANSACTIONS")
        act_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; font-weight: bold; letter-spacing: 2.5px; background: transparent;")
        layout.addWidget(act_label)

        act_frame = QFrame()
        act_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        act_layout = QVBoxLayout(act_frame)
        act_layout.setContentsMargins(16, 16, 16, 16)

        self.activities_table = QTableWidget()
        self.activities_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activities_table.setColumnCount(4)
        self.activities_table.setHorizontalHeaderLabels(["Date", "Type", "Description", "Amount"])
        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setShowGrid(False)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        hdr = self.activities_table.horizontalHeader()
        if hdr:
            hdr.setStretchLastSection(True)
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        vhdr = self.activities_table.verticalHeader()
        if vhdr:
            vhdr.setVisible(False)
        self.activities_table.setMinimumHeight(220)
        act_layout.addWidget(self.activities_table)
        layout.addWidget(act_frame)

        scroll.setWidget(container)
        self._refresh_metrics()
        self._refresh_activities()
        return scroll

    def _update_clock(self):
        from datetime import datetime
        now = datetime.now()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self._clock_lbl.setText(f"{days[now.weekday()]}  {now.strftime('%Y/%m/%d')}   🕐  {now.strftime('%H:%M:%S')}")

    def _refresh_metrics(self):
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                queries = {
                    "sales_today":      "SELECT COALESCE(SUM(total_amount),0) t FROM sales_invoices WHERE date=DATE('now')",
                    "monthly_revenue":  "SELECT COALESCE(SUM(total_amount),0) t FROM sales_invoices WHERE strftime('%Y-%m',date)=strftime('%Y-%m','now')",
                    "inventory_value":  "SELECT COALESCE(SUM(quantity*unit_price),0) t FROM products",
                    "receivables":      "SELECT COALESCE(SUM(balance),0) t FROM customers WHERE balance>0",
                    "payables":         "SELECT COALESCE(SUM(balance),0) t FROM suppliers WHERE balance>0",
                    "monthly_expenses": "SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE strftime('%Y-%m',date)=strftime('%Y-%m','now')",
                }
                for key, q in queries.items():
                    cur.execute(q)
                    val = cur.fetchone()["t"]
                    lbl = self._metric_labels.get(key)
                    if lbl:
                        lbl.setText(f"EGP {val:,.2f}")
        except Exception as e:
            print(f"Metrics error: {e}")


    def _refresh_activities(self):
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT * FROM (
                        SELECT date,'Sale' type,
                            CASE WHEN c.name IS NOT NULL THEN c.name||' — Invoice #'||s.id
                                 ELSE 'Sales Invoice #'||s.id END description,
                            total_amount amount
                        FROM sales_invoices s LEFT JOIN customers c ON s.customer_id=c.id
                        UNION ALL
                        SELECT date,'Purchase' type,
                            CASE WHEN su.name IS NOT NULL THEN su.name||' — Invoice #'||p.id
                                 ELSE 'Purchase Invoice #'||p.id END description,
                            total_amount amount
                        FROM purchase_invoices p LEFT JOIN suppliers su ON p.supplier_id=su.id
                        UNION ALL
                        SELECT date,'Expense' type, category||' — '||description description, amount
                        FROM expenses
                    ) ORDER BY date DESC LIMIT 12
                """)
                rows = cur.fetchall()
                self.activities_table.setRowCount(len(rows))
                type_colors = {
                    "Sale":     COLORS["green"],
                    "Purchase": COLORS["red"],
                    "Expense":  COLORS["yellow"],
                }
                for i, row in enumerate(rows):
                    items = [
                        QTableWidgetItem(row["date"]),
                        QTableWidgetItem(row["type"]),
                        QTableWidgetItem(row["description"]),
                        QTableWidgetItem(f"EGP {row['amount']:,.2f}"),
                    ]
                    items[1].setForeground(QColor(type_colors.get(row["type"], COLORS["text_main"])))
                    for col, item in enumerate(items):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        self.activities_table.setItem(i, col, item)
        except Exception as e:
            print(f"Activities error: {e}")

    def refresh_dashboard(self):
        self._refresh_metrics()
        self._refresh_activities()
        if hasattr(self, 'kpi_module'):
            self.kpi_module.refresh_data()

    def _show_account_statement(self, entity_type):
        from modules.account_statements import AccountStatementDialog
        dialog = AccountStatementDialog(self, entity_type)
        dialog.exec()

    def _show_tutorial(self):
        from modules.tutorial import TutorialDialog
        dialog = TutorialDialog(self)
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Attar AIS")
    init_database()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
