
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QFrame, QScrollArea, QGridLayout, 
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QLinearGradient, QColor, QPalette, QBrush, QFont

# Project Modules
from database.db_config import init_database, DatabaseConnection, log_action
from modules.sales import SalesModule
from modules.purchases import PurchasesModule
from modules.inventory import InventoryModule
from modules.products import ProductsModule
from modules.customers import CustomersModule
from modules.suppliers import SuppliersModule
from modules.expenses import ExpensesModule
from modules.revenue import RevenueModule
from modules.accounting import AccountingModule
from modules.auto_accounting import AutoAccountingModule
from modules.financial_reports import FinancialReportsModule
from modules.localization import tr, save_lang
from modules.theme import COLORS, apply_theme, get_current_theme, save_theme
from modules.kpis import KPIModule
from modules.users import UsersModule, LoginDialog
from modules.recipes import RecipesModule
from modules.tutorial import TutorialDialog
from modules.audit_log import AuditLogModule

class MainWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        print("DEBUG: MainWindow Init Started — User:", user.get('username') if user else 'None')
        self.current_user = user
        self.setWindowTitle(f"Attar AIS Pro [v1.0.4] - {user['username']}")
        self.setMinimumSize(1300, 850)
        self.restart_requested = False
        
        apply_theme(self)
        self.auto_accounting = AutoAccountingModule()
        self.active_button = None
        self.nav_buttons = {}
        self.kpi_labels = {}
        
        self.init_ui()
        # Defer initial refresh to ensure everything is initialized
        QTimer.singleShot(500, self.refresh_dashboard)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        self.main_layout.addWidget(self.sidebar)

        # Main Content
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Initialize modules
        try:
            # Core Modules
            self.sales_module      = SalesModule(self.auto_accounting, self.current_user)
            self.purchases_module  = PurchasesModule(self.auto_accounting, self.current_user)
            self.products_module   = ProductsModule(self.current_user)
            self.inventory_module  = InventoryModule(self.current_user)
            self.customers_module  = CustomersModule(self.current_user)
            self.suppliers_module  = SuppliersModule(self.current_user)
            self.revenue_module    = RevenueModule()
            self.expenses_module   = ExpensesModule(self.auto_accounting, self.current_user)
            self.accounting_module = AccountingModule(self.current_user)
            self.financial_module  = FinancialReportsModule(self.current_user)
            self.kpi_module        = KPIModule(self.current_user)
            self.users_module      = UsersModule(self.current_user)
            self.recipes_module    = RecipesModule(self.current_user)
            self.audit_module      = AuditLogModule(self.current_user)

            # Connections
            self.sales_module.setup_connections(self.customers_module)
            self.sales_module.customer_added.connect(self.customers_module.load_customers)
            self.sales_module.sale_added.connect(self.financial_module.refresh_current_view)
            self.purchases_module.setup_connections(self.suppliers_module)
            self.purchases_module.supplier_added.connect(self.suppliers_module.load_suppliers)
            self.purchases_module.purchase_added.connect(self.financial_module.refresh_current_view)
            self.expenses_module.expense_added.connect(self.financial_module.refresh_current_view)
            self.expenses_module.expense_added.connect(self.kpi_module.refresh_data)
            self.sales_module.sale_added.connect(self.kpi_module.refresh_data)
            self.purchases_module.purchase_added.connect(self.kpi_module.refresh_data)

            # Add to stack
            self.stack.addWidget(self._build_dashboard_pro()) # 0
            self.stack.addWidget(self.sales_module)           # 1
            self.stack.addWidget(self.purchases_module)       # 2
            self.stack.addWidget(self.products_module)        # 3
            self.stack.addWidget(self.inventory_module)       # 4
            self.stack.addWidget(self.customers_module)       # 5
            self.stack.addWidget(self.suppliers_module)       # 6
            self.stack.addWidget(self.revenue_module)         # 7
            self.stack.addWidget(self.expenses_module)        # 8
            self.stack.addWidget(self.recipes_module)         # 9
            self.stack.addWidget(self.accounting_module)      # 10
            self.stack.addWidget(self.financial_module)       # 11
            self.stack.addWidget(self.kpi_module)             # 12
            self.stack.addWidget(self.users_module)           # 13
            self.stack.addWidget(self.audit_module)           # 14
        except Exception as e:
            QMessageBox.critical(self, "Module Loading Error", f"A critical error occurred during module initialization:\n\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}")
            # Initialize missing modules to empty widgets to prevent further crashes
            for mod in ['sales_module', 'purchases_module', 'products_module', 'inventory_module', 
                        'customers_module', 'suppliers_module', 'expenses_module', 'accounting_module',
                        'financial_module', 'kpi_module', 'users_module', 'recipes_module']:
                if not hasattr(self, mod):
                    setattr(self, mod, QWidget())

        # Timers
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_dashboard)
        self._refresh_timer.start(10000)
        
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"background-color: {COLORS['sidebar']}; border-right: 1px solid {COLORS['sidebar_mid']};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QFrame()
        header.setStyleSheet(f"background: #020617; border-bottom: 2px solid {COLORS['sidebar_mid']};")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(20, 30, 20, 30)
        logo = QLabel("🌿 ATTAR AIS")
        logo.setStyleSheet(f"color: {COLORS['accent']}; font-size: 22px; font-weight: 900; letter-spacing: 1px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(logo)
        
        toggles = QHBoxLayout()
        btn_s = f"background: {COLORS['bg_card']}; color: {COLORS['text_main']}; border: 1px solid {COLORS['sidebar_mid']}; border-radius: 8px; padding: 6px; font-size: 11px; font-weight: bold;"
        l_btn = QPushButton("EN/AR")
        l_btn.setStyleSheet(btn_s)
        l_btn.clicked.connect(self.toggle_language)
        t_btn = QPushButton("☀️/🌙")
        t_btn.setStyleSheet(btn_s)
        t_btn.clicked.connect(self.toggle_theme)
        toggles.addWidget(l_btn)
        toggles.addWidget(t_btn)
        hl.addLayout(toggles)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        nav_cont = QWidget()
        self.nav_layout = QVBoxLayout(nav_cont)
        self.nav_layout.setContentsMargins(10, 20, 10, 20)
        self.nav_layout.setSpacing(5)

        items = [
            ("🏠", tr('dashboard'), 0),
            ("💰", tr('sales'), 1),
            ("🛒", tr('purchases'), 2),
            ("✨", tr('products'), 3),
            ("📦", tr('inventory'), 4),
            ("👤", tr('customers'), 5),
            ("🏭", tr('suppliers'), 6),
            ("💰", tr('revenue'), 7),
            ("💸", tr('expenses'), 8),
            ("🌿", tr('mixes'), 9),
        ]

        for ico, lbl, idx in items:
            btn = self._make_nav_btn(ico, lbl, idx)
            self.nav_layout.addWidget(btn)
            self.nav_buttons[idx] = btn

        if self.current_user and self.current_user.get('role') == 'admin':
            self.nav_layout.addWidget(self._section_lbl(tr('accounting')))
            
            # Management & Advanced Tools
            btn_acc = self._make_nav_btn("📊", tr('general_journal'), 10)
            btn_fin = self._make_nav_btn("💰", tr('financials'), 11)
            btn_kpi = self._make_nav_btn("📈", tr('analytics'), 12)
            btn_staff = self._make_nav_btn("👥", tr('staff_accounts'), 13)
            btn_audit = self._make_nav_btn("🔍", tr('audit_log'), 14)
            
            self.nav_buttons[10] = btn_acc
            self.nav_buttons[11] = btn_fin
            self.nav_buttons[12] = btn_kpi
            self.nav_buttons[13] = btn_staff
            self.nav_buttons[14] = btn_audit
            
            self.nav_layout.addWidget(btn_acc)
            self.nav_layout.addWidget(btn_fin)
            self.nav_layout.addWidget(btn_kpi)
            self.nav_layout.addWidget(btn_staff)
            self.nav_layout.addWidget(btn_audit)

            # Training
            self.nav_layout.addWidget(self._section_lbl(tr('training')))
            btn_tut = self._make_nav_btn("🎓", tr('employee_guide'), 99)
            self.nav_layout.addWidget(btn_tut)
            self.nav_buttons[99] = btn_tut

        self.nav_layout.addStretch()
        logout = QPushButton(f"🚪 {tr('logout')}")
        logout.setStyleSheet(f"color: {COLORS['red']}; text-align: left; padding-left: 20px; border: none; font-weight: bold; font-size: 13px; margin-bottom: 20px;")
        logout.clicked.connect(self.logout)
        self.nav_layout.addWidget(logout)

        scroll.setWidget(nav_cont)
        layout.addWidget(scroll)
        return sidebar

    def _make_nav_btn(self, icon, label, idx):
        btn = QPushButton(f"  {icon}   {label}")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._nav_style(idx == 0))
        btn.clicked.connect(lambda _, b=btn, i=idx: self._nav_click(b, i))
        return btn

    def _nav_style(self, active):
        bg = COLORS['sidebar_active'] if active else "transparent"
        fg = "white" if active else COLORS['text_dim']
        border = f"border-left: 4px solid {COLORS['accent']};" if active else "border-left: 4px solid transparent;"
        return f"""
            QPushButton {{
                text-align: left; 
                padding-left: 15px; 
                {border}
                background: {bg}; 
                color: {fg}; 
                font-weight: {'bold' if active else '500'}; 
                border-radius: 0px 10px 10px 0px; 
                margin: 2px 0px; 
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background: {COLORS['sidebar_mid'] if not active else bg};
                color: white;
            }}
        """

    def _nav_click(self, btn, idx):
        if idx == 99:
            dialog = TutorialDialog(self)
            dialog.exec()
            return

        # Deselect all buttons first
        for b in self.nav_buttons.values():
            b.setStyleSheet(self._nav_style(False))
        
        # Highlight new button
        btn.setStyleSheet(self._nav_style(True))
        self.active_button = btn
        self.stack.setCurrentIndex(idx)
        if idx == 0: self.refresh_dashboard()
        elif idx == 7: self.revenue_module.load_revenue()
        elif idx == 8: self.expenses_module.load_expenses()
        elif idx == 12: self.kpi_module.refresh_data()
        elif idx == 14: self.audit_module.load_logs()

    def _section_lbl(self, text):
        l = QLabel(f"  {text}")
        l.setStyleSheet(f"color: #475569; font-size: 10px; font-weight: 900; margin-top: 25px; margin-bottom: 8px;")
        return l

    def _build_dashboard_pro(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(35, 35, 35, 35)
        l.setSpacing(25)
        
        # 1. Welcome Banner
        self.banner = QFrame()
        self.banner.setFixedHeight(120)
        self.banner.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['sidebar']}, stop:1 {COLORS['sidebar_active']}); border-radius: 20px;")
        bl = QHBoxLayout(self.banner)
        bl.setContentsMargins(40, 0, 40, 0)
        
        username = self.current_user.get('username', 'Admin') if self.current_user else 'Admin'
        greeting = QLabel(f"{tr('welcome')}{username}! 🌿")
        greeting.setStyleSheet("color: white; font-size: 24px; font-weight: 800; background: transparent;")
        bl.addWidget(greeting)
        bl.addStretch()
        self.time_lbl = QLabel(datetime.now().strftime("%I:%M:%S %p"))
        self.time_lbl.setStyleSheet("color: white; font-size: 18px; font-weight: 500; background: transparent;")
        bl.addWidget(self.time_lbl)
        l.addWidget(self.banner)

        # 2. Alert Bar
        self.alert_bar = QFrame()
        self.alert_bar.setFixedHeight(50)
        self.alert_bar.setStyleSheet(f"background: #7F1D1D; border-radius: 15px; border: none;")
        al = QHBoxLayout(self.alert_bar)
        al.setContentsMargins(20, 0, 20, 0)
        al.addWidget(QLabel("⚠️"))
        self.alert_summary = QLabel(tr('inventory_attention'))
        self.alert_summary.setStyleSheet("color: white; font-weight: 900; font-size: 14px;")
        al.addWidget(self.alert_summary)
        al.addStretch()
        self.alert_pills = QLabel("")
        self.alert_pills.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; font-weight: bold;")
        al.addWidget(self.alert_pills)
        l.addWidget(self.alert_bar)

        # 3. Metrics
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        l.addLayout(self.grid)
        
        defs = [
            (tr('today_sales_title'), "kpi_today", COLORS["accent"], "💰"),
            (tr('monthly_rev_title'), "kpi_month", COLORS["blue"], "📈"),
            (tr('inv_val_title'),     "kpi_inv",   COLORS["yellow"], "📦"),
            (tr('payables'),          "kpi_payables", COLORS["red"], "💳"),
        ]
        for i, (title, key, color, icon) in enumerate(defs):
            self.grid.addWidget(self._create_pro_card(title, key, color, icon), 0, i)

        # 4. Recent Activities
        rl = QLabel(tr('recent_activities'))
        rl.setStyleSheet(f"color: {COLORS['text_main']}; font-weight: 900; font-size: 18px; margin-top: 15px; background: transparent;")
        l.addWidget(rl)
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels([tr('date'), tr('type'), tr('description'), tr('amount')])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setShowGrid(False)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_card']};
                alternate-background-color: {COLORS['bg'] if get_current_theme() == 'dark' else '#F8FAFC'};
                border: 1.5px solid {COLORS['border']};
                border-radius: 20px;
                padding: 10px;
            }}
            QTableWidget::item {{ padding: 10px; border: none; }}
        """)
        l.addWidget(self.activity_table)
        
        return w

    def _create_pro_card(self, title, key, color, icon):
        f = QFrame()
        f.setFixedHeight(170)
        # Smoother card: No inner boxes, use a cleaner sidebar accent
        f.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']}; 
                border-radius: 20px; 
                border: 1.5px solid {COLORS['border']};
                border-left: 6px solid {color};
            }}
        """)
        l = QVBoxLayout(f)
        l.setContentsMargins(30, 25, 30, 25)
        
        h = QHBoxLayout()
        i_lbl = QLabel(icon)
        i_lbl.setStyleSheet(f"background: rgba(0,0,0,0.1); border-radius: 12px; padding: 10px; font-size: 22px; border: none;")
        h.addWidget(i_lbl)
        h.addStretch()
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: 900; font-size: 11px; letter-spacing: 1.5px; border: none; background: transparent;")
        h.addWidget(t_lbl)
        l.addLayout(h)
        
        vl = QLabel("—")
        vl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 900; margin-top: 15px; border: none; background: transparent;")
        vl.setWordWrap(True)
        l.addWidget(vl)
        
        self.kpi_labels[key] = vl
        return f

    def _update_clock(self):
        self.time_lbl.setText(datetime.now().strftime("%I:%M:%S %p"))

    def refresh_dashboard(self):
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                
                # Metrics
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE date = date('now')")
                today = cur.fetchone()[0]
                
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
                month = cur.fetchone()[0]
                
                cur.execute("SELECT COALESCE(SUM(quantity*unit_price), 0) FROM products")
                inv = cur.fetchone()[0]
                
                self.kpi_labels["kpi_today"].setText(f"EGP {today or 0:,.2f}")
                self.kpi_labels["kpi_month"].setText(f"EGP {month or 0:,.2f}")
                self.kpi_labels["kpi_inv"].setText(f"EGP {inv or 0:,.2f}")

                # Alerts (Low Stock & Credit Due)
                today_str = datetime.now().strftime("%Y-%m-%d")
                near_due_str = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                
                cur.execute("SELECT COUNT(*) FROM products WHERE quantity <= minimum_quantity")
                low_stock = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT COUNT(*) FROM purchase_invoices 
                    WHERE payment_type = 'credit' AND status = 'pending' 
                    AND due_date IS NOT NULL AND due_date <= ?
                """, (near_due_str,))
                credit_due = cur.fetchone()[0]
                
                if low_stock > 0 or credit_due > 0:
                    self.alert_bar.show()
                    alert_text = []
                    summary_text = []
                    if low_stock > 0:
                        alert_text.append(f"({low_stock}) {tr('low_stock_title')}")
                        summary_text.append(tr('inventory_attention'))
                    if credit_due > 0:
                        alert_text.append(f"({credit_due}) {tr('credit_due_alert')}")
                        summary_text.append(tr('credit_due_alert'))
                    
                    self.alert_summary.setText(" & ".join(summary_text))
                    self.alert_pills.setText(" | ".join(alert_text))
                else:
                    self.alert_bar.hide()
                
                # Payables
                cur.execute("SELECT COALESCE(SUM(total_amount - COALESCE(paid_amount, 0)), 0) FROM purchase_invoices WHERE payment_type = 'credit' AND status = 'pending'")
                payables = cur.fetchone()[0]
                self.kpi_labels["kpi_payables"].setText(f"EGP {payables:,.2f}")

                # Recent Activities
                cur.execute(f"""
                    SELECT date, '{tr('sale')}' as type, '{tr('sale')} #' || id as desc, total_amount as amt FROM sales_invoices
                    UNION ALL
                    SELECT date, '{tr('purchase')}' as type, '{tr('purchase')} #' || id as desc, total_amount as amt FROM purchase_invoices
                    UNION ALL
                    SELECT date, '{tr('expense')}' as type, category as desc, amount as amt FROM expenses
                    ORDER BY date DESC LIMIT 7
                """)
                rows = cur.fetchall()
                self.activity_table.setRowCount(len(rows))
                for i, r in enumerate(rows):
                    self.activity_table.setItem(i, 0, QTableWidgetItem(r["date"]))
                    self.activity_table.setItem(i, 1, QTableWidgetItem(r["type"]))
                    self.activity_table.setItem(i, 2, QTableWidgetItem(r["desc"]))
                    item = QTableWidgetItem(f"EGP {r['amt']:,.2f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.activity_table.setItem(i, 3, item)

        except Exception as e: 
            print(f"Refresh Error: {e}")
            # Optionally show a small status bar message instead of a dialog to avoid interrupting the user

    def logout(self):
        log_action(self.current_user['id'], self.current_user['username'], 'Logout', 'Auth', 'User logged out')
        self.close()
        subprocess.Popen([sys.executable, "main.py"])

    def toggle_theme(self):
        theme = 'light' if get_current_theme() == 'dark' else 'dark'
        save_theme(theme)
        self.restart_requested = True
        self.close()

    def toggle_language(self):
        lang = 'ar' if tr('dashboard') == 'Dashboard' else 'en'
        save_lang(lang)
        self.restart_requested = True
        self.close()

def main():
    init_database()
    app = QApplication(sys.argv)
    user = None
    while True:
        if not user:
            login = LoginDialog()
            if not login.exec(): break
            user = login.user
            
        window = MainWindow(user)
        window.show()
        app.exec()
        
        if hasattr(window, 'restart_requested') and window.restart_requested:
            continue
        else:
            break

import traceback

def global_exception_handler(exctype, value, tb):
    """Global handler for uncaught exceptions to prevent silent crashes"""
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(f"CRITICAL ERROR:\n{err_msg}")
    
    # Try to show a GUI message box if QApplication exists
    if QApplication.instance():
        QMessageBox.critical(None, "Critical System Error", 
                            f"The application encountered a serious problem and might need to restart.\n\nError: {value}")
    sys.exit(1)

# Install the handler
sys.excepthook = global_exception_handler

if __name__ == "__main__":
    main()
