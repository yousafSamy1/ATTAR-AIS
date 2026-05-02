from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from database.db_config import DatabaseConnection

# Reuse colors from main
COLORS = {
    "bg":            "#F8FAFC",
    "bg_card":       "#FFFFFF",
    "sidebar":       "#0F172A",
    "accent":        "#059669",
    "accent2":       "#10B981",
    "green":         "#059669",
    "red":           "#DC2626",
    "blue":          "#2563EB",
    "yellow":        "#D97706",
    "text_main":     "#0F172A",
    "text_sub":      "#475569",
    "text_dim":      "#94A3B8",
    "border":        "#E2E8F0",
}

class KPIModule(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(24)
        
        self._kpi_labels = {}
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        # Header
        header = QLabel("Analytics & Performance KPIs")
        header.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['sidebar']};")
        self.layout.addWidget(header)

        sub_header = QLabel("Real-time business intelligence and performance metrics")
        sub_header.setStyleSheet(f"font-size: 14px; color: {COLORS['text_sub']}; margin-bottom: 10px;")
        self.layout.addWidget(sub_header)

        # Scroll Area for KPIs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(20)

        kpi_defs = [
            ("Gross Profit Margin",      "kpi_gross_margin",     COLORS["accent"],    "📊", "Profitability"),
            ("Avg. Order Value",         "kpi_avg_order",        COLORS["blue"],      "🛒", "Sales Efficiency"),
            ("Inventory Turnover",       "kpi_inv_turnover",     COLORS["green"],     "🔄", "Stock Velocity"),
            ("Top Selling Product",      "kpi_top_product",      COLORS["yellow"],    "🏆", "Popularity"),
            ("Low Stock Alerts",         "kpi_low_stock",        COLORS["red"],       "⚠️", "Risk Management"),
            ("Receivables Collection",   "kpi_collection_rate",  COLORS["accent"],    "💳", "Cash Flow"),
            ("Expense / Revenue Ratio",  "kpi_expense_ratio",    COLORS["text_sub"],  "📉", "Burn Rate"),
            ("Sales Growth (MoM)",       "kpi_sales_growth",     COLORS["green"],     "🚀", "Growth Trend"),
        ]

        for i, (title, key, color, icon, category) in enumerate(kpi_defs):
            card = self._create_enhanced_card(title, key, color, icon, category)
            self.grid_layout.addWidget(card, i // 4, i % 4)

        scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def _create_enhanced_card(self, title, key, color, icon, category):
        card = QFrame()
        card.setMinimumHeight(180)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Category Badge
        badge_layout = QHBoxLayout()
        badge = QLabel(f"  {category.upper()}  ")
        badge.setStyleSheet(f"""
            background-color: {COLORS['bg']};
            color: {COLORS['text_sub']};
            font-size: 9px;
            font-weight: bold;
            border-radius: 10px;
            padding: 4px;
        """)
        badge_layout.addWidget(badge)
        badge_layout.addStretch()
        
        # Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {color};")
        badge_layout.addWidget(icon_lbl)
        layout.addLayout(badge_layout)
        
        layout.addSpacing(10)
        
        # Title
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 13px; font-weight: 500;")
        layout.addWidget(t_lbl)
        
        # Value
        v_lbl = QLabel("—")
        v_lbl.setStyleSheet(f"color: {COLORS['text_main']}; font-size: 32px; font-weight: 800;")
        layout.addWidget(v_lbl)
        
        # Visual Progress/Indicator
        progress = QProgressBar()
        progress.setFixedHeight(6)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg']};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        progress.setValue(0)
        layout.addWidget(progress)
        
        self._kpi_labels[key] = (v_lbl, progress, color)
        return card

    def refresh_data(self):
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()

                # 1. Gross Profit Margin
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) t FROM sales_invoices")
                total_revenue = cur.fetchone()["t"]
                cur.execute("""
                    SELECT COALESCE(SUM(si.quantity * p.unit_price), 0) t
                    FROM sales_items si
                    JOIN products p ON si.product_id = p.id
                """)
                total_cogs = cur.fetchone()["t"]
                margin = ((total_revenue - total_cogs) / total_revenue * 100) if total_revenue > 0 else 0
                self._update_kpi("kpi_gross_margin", f"{margin:.1f}%", int(margin))

                # 2. Avg Order
                cur.execute("SELECT COUNT(*) c, COALESCE(SUM(total_amount), 0) t FROM sales_invoices")
                row = cur.fetchone()
                avg = row["t"] / row["c"] if row["c"] > 0 else 0
                self._update_kpi("kpi_avg_order", f"EGP {avg:,.0f}", min(100, int(avg/100)))

                # 3. Turnover
                cur.execute("SELECT COALESCE(SUM(quantity * unit_price), 0) t FROM products")
                inv_val = cur.fetchone()["t"]
                turnover = (total_cogs / inv_val) if inv_val > 0 else 0
                self._update_kpi("kpi_inv_turnover", f"{turnover:.2f}x", min(100, int(turnover*10)))

                # 4. Top Product
                cur.execute("""
                    SELECT p.name, SUM(si.quantity) q 
                    FROM sales_items si JOIN products p ON si.product_id=p.id 
                    GROUP BY p.id ORDER BY q DESC LIMIT 1
                """)
                top = cur.fetchone()
                self._update_kpi("kpi_top_product", top["name"] if top else "—", 100 if top else 0)

                # 5. Low Stock
                cur.execute("SELECT COUNT(*) c FROM products WHERE quantity <= minimum_quantity")
                low = cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) c FROM products")
                total_p = cur.fetchone()["c"]
                low_p = (low / total_p * 100) if total_p > 0 else 0
                self._update_kpi("kpi_low_stock", f"{low} items", int(low_p))

                # 6. Collection
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) t, COALESCE(SUM(paid_amount), 0) p FROM sales_invoices")
                rec = cur.fetchone()
                coll = (rec["p"] / rec["t"] * 100) if rec["t"] > 0 else 0
                self._update_kpi("kpi_collection_rate", f"{coll:.1f}%", int(coll))

                # 7. Expense Ratio
                cur.execute("SELECT COALESCE(SUM(amount), 0) t FROM expenses")
                exp = cur.fetchone()["t"]
                ratio = (exp / total_revenue * 100) if total_revenue > 0 else 0
                self._update_kpi("kpi_expense_ratio", f"{ratio:.1f}%", int(ratio))

                # 8. Growth
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) t FROM sales_invoices WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
                cur_m = cur.fetchone()["t"]
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) t FROM sales_invoices WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now', '-1 month')")
                pre_m = cur.fetchone()["t"]
                growth = ((cur_m - pre_m) / pre_m * 100) if pre_m > 0 else (100 if cur_m > 0 else 0)
                self._update_kpi("kpi_sales_growth", f"{'+' if growth>=0 else ''}{growth:.1f}%", abs(int(growth)))

        except Exception as e:
            print(f"KPI Refresh Error: {e}")

    def _update_kpi(self, key, text, val):
        if key in self._kpi_labels:
            lbl, prog, color = self._kpi_labels[key]
            lbl.setText(text)
            prog.setValue(max(0, min(100, val)))
