
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QBrush, QPolygonF
from database.db_config import DatabaseConnection
from datetime import datetime, timedelta
from modules.theme import COLORS, get_current_theme
from modules.localization import tr

class TrendChart(QWidget):
    def __init__(self, title=""):
        super().__init__()
        self.setMinimumHeight(280)
        self.title = title
        self.data_sales = [0] * 7
        self.data_expenses = [0] * 7
        self.labels = ["", "", "", "", "", "", ""]

    def set_data(self, sales, expenses, labels):
        self.data_sales = sales
        self.data_expenses = expenses
        self.labels = labels
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin_x, margin_y = 70, 50 # Increased margins for text visibility
        pw, ph = w - 2*margin_x, h - 2*margin_y
        max_val = max(max(self.data_sales + self.data_expenses), 100) * 1.2

        # Draw Title
        p.setPen(QColor(COLORS['text_main'])) # Use brighter text
        p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.drawText(margin_x, margin_y - 20, self.title.upper())

        # Draw Grid Lines & Axis Labels
        p.setFont(QFont("Segoe UI", 9))
        for i in range(5):
            y = h - margin_y - (i * ph / 4)
            p.setOpacity(0.1)
            p.setPen(QPen(QColor(COLORS["text_main"]), 1))
            p.drawLine(margin_x, int(y), w - margin_x, int(y))
            p.setOpacity(1.0)
            p.setPen(QColor(COLORS["text_dim"]))
            p.drawText(5, int(y + 5), f"{int(i * max_val / 4):,}")

        def get_poly(data):
            poly = QPolygonF()
            poly.append(QPointF(margin_x, h - margin_y))
            for i, val in enumerate(data):
                x = margin_x + (i * pw / (len(data)-1))
                y = h - margin_y - (val / max_val * ph)
                poly.append(QPointF(x, y))
            poly.append(QPointF(w - margin_x, h - margin_y))
            return poly

        # Draw Area
        p.setOpacity(0.2)
        p.setBrush(QBrush(QColor(COLORS["accent"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(get_poly(self.data_sales))
        p.setBrush(QBrush(QColor(COLORS["red"])))
        p.drawPolygon(get_poly(self.data_expenses))
        p.setOpacity(1.0)

        # Draw Lines
        def draw_line(data, color):
            p.setPen(QPen(QColor(color), 4, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
            for i in range(len(data)-1):
                x1 = margin_x + (i * pw / (len(data)-1))
                y1 = h - margin_y - (data[i] / max_val * ph)
                x2 = margin_x + ((i+1) * pw / (len(data)-1))
                y2 = h - margin_y - (data[i+1] / max_val * ph)
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                
        draw_line(self.data_sales, COLORS["accent"])
        draw_line(self.data_expenses, COLORS["red"])

        # Date Labels
        p.setPen(QColor(COLORS["text_main"]))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        for i, lbl in enumerate(self.labels):
            x = margin_x + (i * pw / (len(self.labels)-1))
            p.drawText(int(x - 20), h - 15, lbl)

class DistributionChart(QWidget):
    def __init__(self, title=""):
        super().__init__()
        self.setMinimumHeight(240)
        self.title = title
        self.data = [] # List of (name, value, color)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 50
        
        # Title
        p.setPen(QColor(COLORS['text_main']))
        p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.drawText(20, 30, self.title.upper())

        if not self.data: return
        
        max_val = max([x[1] for x in self.data]) or 1
        bar_height = 30
        spacing = 40
        
        p.setFont(QFont("Segoe UI", 10))
        for i, (name, val, color) in enumerate(self.data):
            y = 60 + i * spacing
            # Name
            p.setPen(QColor(COLORS['text_dim']))
            p.drawText(20, y + 20, name)
            
            # Bar
            bar_w = (val / max_val) * (w - 200)
            rect = QRectF(150, y, bar_w, bar_height)
            p.setOpacity(0.2)
            p.setBrush(QBrush(QColor(color)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(150, y, w - 200, bar_height), 6, 6)
            p.setOpacity(1.0)
            p.drawRoundedRect(rect, 6, 6)
            
            # Value
            p.setPen(QColor(COLORS['text_main']))
            p.drawText(int(160 + bar_w), y + 20, f"{val:,.0f}")

class KPIModule(QWidget):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(35, 35, 35, 35)
        self.layout.setSpacing(25)
        
        self._kpi_labels = {}
        self._setup_ui()
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(10000) # Refresh every 10 seconds
        
        # Initial refresh (deferred slightly to ensure UI is ready)
        QTimer.singleShot(100, self.refresh_data)

    def _setup_ui(self):
        # Header
        header = QLabel(tr("analytics"))
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        self.layout.addWidget(header)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(content)
        vbox.setSpacing(30)

        # 1. KPI Grid
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setSpacing(15)
        grid.setContentsMargins(0, 0, 0, 0)
        kpi_defs = [
            (tr("gross_margin"),      "kpi_gross_margin",     COLORS["accent"],    "📊", "Profitability"),
            ("Avg. Order Value",         "kpi_avg_order",        COLORS["blue"],      "🛒", "Sales Efficiency"),
            (tr("inv_turnover"),       "kpi_inv_turnover",     COLORS["green"],     "🔄", "Stock Velocity"),
            ("Top Selling Product",      "kpi_top_product",      COLORS["yellow"],    "🏆", "Popularity"),
            ("Low Stock Alerts",         "kpi_low_stock",        COLORS["red"],       "⚠️", "Risk Management"),
            (tr("collection_rate"),  "kpi_collection_rate",  COLORS["accent"],    "💳", "Cash Flow"),
            (tr("expense_ratio"),  "kpi_expense_ratio",    COLORS["text_sub"],  "📉", "Burn Rate"),
            ("Sales Growth (MoM)",       "kpi_sales_growth",     COLORS["green"],     "🚀", "Growth Trend"),
        ]
        for i, (title, key, color, icon, category) in enumerate(kpi_defs):
            grid.addWidget(self._create_enhanced_card(title, key, color, icon, category), i // 4, i % 4)
        vbox.addWidget(grid_container)

        # 2. Charts Row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)

        # Trend Chart Card
        self.trend_chart = TrendChart(tr("sales_trend"))
        trend_card = QFrame()
        trend_card.setStyleSheet(f"background: {COLORS['bg_card']}; border: 1.5px solid {COLORS['border']}; border-radius: 24px;")
        tl = QVBoxLayout(trend_card)
        tl.addWidget(self.trend_chart)
        charts_row.addWidget(trend_card, 2)

        # Distribution Chart Card
        self.dist_chart = DistributionChart("Revenue by Category")
        dist_card = QFrame()
        dist_card.setStyleSheet(f"background: {COLORS['bg_card']}; border: 1.5px solid {COLORS['border']}; border-radius: 24px;")
        dl = QVBoxLayout(dist_card)
        dl.addWidget(self.dist_chart)
        charts_row.addWidget(dist_card, 1)

        vbox.addLayout(charts_row)

        # 3. AI Insights Section
        self.ai_card = QFrame()
        self.ai_card.setStyleSheet(f"background: {COLORS['accent_light'] if get_current_theme() == 'light' else COLORS['sidebar_mid']}; border: 2px solid {COLORS['accent']}; border-radius: 24px;")
        al = QVBoxLayout(self.ai_card)
        al.setContentsMargins(30, 25, 30, 25)
        
        ai_header = QHBoxLayout()
        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        ai_title = QLabel("ATTAR AI ASSISTANT SUGGESTIONS")
        ai_title.setStyleSheet(f"color: {COLORS['accent']}; font-weight: 900; letter-spacing: 2px; font-size: 13px; border: none; background: transparent;")
        ai_header.addWidget(ai_icon)
        ai_header.addWidget(ai_title)
        ai_header.addStretch()
        al.addLayout(ai_header)
        
        self.ai_text = QLabel("Analyzing your data...")
        self.ai_text.setWordWrap(True)
        self.ai_text.setStyleSheet(f"color: {COLORS['text_main']}; font-size: 15px; line-height: 150%; border: none; background: transparent; margin-top: 10px;")
        al.addWidget(self.ai_text)
        
        vbox.addWidget(self.ai_card)

        scroll.setWidget(content)
        self.layout.addWidget(scroll)

    def _create_enhanced_card(self, title, key, color, icon, category):
        card = QFrame()
        card.setMinimumHeight(150)
        card.setStyleSheet(f"QFrame {{ background: {COLORS['bg_card']}; border: 1.5px solid {COLORS['border']}; border-radius: 18px; }}")
        l = QVBoxLayout(card)
        l.setContentsMargins(15, 15, 15, 15)
        
        bl = QHBoxLayout()
        badge = QLabel(f"  {category.upper()}  ")
        badge.setStyleSheet(f"background: {COLORS['bg']}; color: {COLORS['text_dim']}; font-size: 8px; font-weight: 800; border-radius: 6px; padding: 2px 5px; border: none;")
        bl.addWidget(badge)
        bl.addStretch()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 18px; color: {color}; border: none; background: transparent;")
        bl.addWidget(icon_lbl)
        l.addLayout(bl)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        l.addWidget(t_lbl)
        v_lbl = QLabel("—")
        v_lbl.setStyleSheet(f"color: {COLORS['text_main']}; font-size: 24px; font-weight: 900; border: none; background: transparent;")
        l.addWidget(v_lbl)
        l.addStretch()
        
        prog = QProgressBar()
        prog.setFixedHeight(5)
        prog.setTextVisible(False)
        prog.setStyleSheet(f"QProgressBar {{ background: {COLORS['bg']}; border-radius: 2px; border: none; }} QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}")
        l.addWidget(prog)
        
        self._kpi_labels[key] = (v_lbl, prog)
        return card

    def refresh_data(self):
        if not self.isVisible():
            return
            
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()

                # Basic Metrics
                cur.execute("SELECT COALESCE(SUM(total_amount), 0) t FROM sales_invoices")
                total_sales = cur.fetchone()["t"]
                cur.execute("SELECT COALESCE(SUM(si.quantity * p.unit_cost), 0) t FROM sales_items si JOIN products p ON si.product_id = p.id")
                total_cogs = cur.fetchone()["t"]
                margin = ((total_sales - total_cogs) / total_sales * 100) if total_sales > 0 else 0
                self._update_kpi("kpi_gross_margin", f"{margin:.1f}%", int(margin))

                cur.execute("SELECT COUNT(*) c, COALESCE(SUM(total_amount), 0) t FROM sales_invoices")
                row = cur.fetchone()
                avg = row["t"] / row["c"] if row["c"] > 0 else 0
                self._update_kpi("kpi_avg_order", f"EGP {avg:,.0f}", min(100, int(avg/100)))

                cur.execute("SELECT p.name, SUM(si.quantity) q FROM sales_items si JOIN products p ON si.product_id=p.id GROUP BY p.id ORDER BY q DESC LIMIT 1")
                top = cur.fetchone()
                self._update_kpi("kpi_top_product", top["name"] if top else "—", 100 if top else 0)

                cur.execute("SELECT COUNT(*) c FROM products WHERE quantity <= minimum_quantity")
                low_stock_count = cur.fetchone()["c"]
                self._update_kpi("kpi_low_stock", f"{low_stock_count} items", int(low_stock_count * 10))

                # Expense Ratio
                cur.execute("SELECT COALESCE(SUM(amount), 0) t FROM expenses")
                total_exp = cur.fetchone()["t"]
                ratio = (total_exp / total_sales * 100) if total_sales > 0 else 0
                self._update_kpi("kpi_expense_ratio", f"{ratio:.1f}%", int(ratio))

                # Trends
                days = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)][::-1]
                s_data, e_data = [], []
                for d in days:
                    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE date = ?", (d,))
                    s_data.append(cur.fetchone()[0])
                    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?", (d,))
                    e_data.append(cur.fetchone()[0])
                self.trend_chart.set_data(s_data, e_data, [datetime.strptime(d, "%Y-%m-%d").strftime("%d %b") for d in days])

                # Distribution Chart (Top 5 Products by Revenue)
                cur.execute("""
                    SELECT p.name, SUM(si.quantity * si.unit_price) rev 
                    FROM sales_items si JOIN products p ON si.product_id = p.id 
                    GROUP BY p.id ORDER BY rev DESC LIMIT 5
                """)
                dist_data = [(r["name"], r["rev"], COLORS["blue"] if i % 2 == 0 else COLORS["accent"]) for i, r in enumerate(cur.fetchall())]
                self.dist_chart.set_data(dist_data)

                # Credit Due Alerts
                today_date = datetime.now().date()
                near_due_date = today_date + timedelta(days=5)
                cur.execute("""
                    SELECT COUNT(*) c FROM purchase_invoices 
                    WHERE payment_type = 'credit' AND status = 'pending' 
                    AND due_date IS NOT NULL AND date(due_date) <= ? AND date(due_date) >= ?
                """, (near_due_date.isoformat(), today_date.isoformat()))
                credit_alerts_count = cur.fetchone()["c"]

                # AI Insights Generation
                insights = []
                if credit_alerts_count > 0:
                    insights.append(f"🔴 CRITICAL: {credit_alerts_count} credit purchase(s) are due within 5 days. Check Purchases for details.")
                if low_stock_count > 0: insights.append(f"⚠️ You have {low_stock_count} items with low stock. Reorder them soon to avoid lost sales.")
                if margin < 20: insights.append(f"💡 Your gross margin ({margin:.1f}%) is lower than usual. Consider reviewing your purchase prices.")
                if ratio > 30: insights.append(f"📉 Expenses are high ({ratio:.1f}% of revenue). Look for cost-saving opportunities in your overhead.")
                if not insights: insights.append("✅ Your business is performing well! Sales are steady and inventory levels are healthy.")
                
                self.ai_text.setText(" • " + "\n • ".join(insights))

        except Exception as e: print(f"KPI Refresh Error: {e}")

    def _update_kpi(self, key, text, val):
        if key in self._kpi_labels:
            lbl, prog = self._kpi_labels[key]
            lbl.setText(text)
            prog.setValue(max(0, min(100, val)))
