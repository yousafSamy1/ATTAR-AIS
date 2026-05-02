from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("دليل الموظف الجديد - نظام عطارة")
        self.setFixedSize(600, 450)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        self.header_label = QLabel("مرحباً بك في نظام إدارة محل العطارة")
        self.header_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #065F46; padding-bottom: 10px;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)

        # Stacked Widget for Pages
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.pages_data = [
            {
                "title": "🏠 1. لوحة القيادة (Dashboard)",
                "desc": "تعرض ملخصاً عاماً لمبيعات ومصروفات المحل وحركة العمل اليومية بشكل سريع. يمكنك من خلالها معرفة الأرباح اليومية والشهرية فوراً."
            },
            {
                "title": "💰 2. المبيعات (Sales)",
                "desc": "من هنا يمكنك إنشاء فواتير البيع للعملاء وتسجيل المنتجات المباعة. بمجرد حفظ الفاتورة، سيقوم النظام تلقائياً بخصم الكمية من المخزن وتسجيل الإيراد المالي."
            },
            {
                "title": "🛒 3. المشتريات (Purchases)",
                "desc": "مخصصة لتسجيل البضاعة التي تشتريها من الموردين. بمجرد إدخال الفاتورة، ستزيد كمية التوابل والأعشاب في المخزن لتكون جاهزة للبيع."
            },
            {
                "title": "📦 4. المخزن (Inventory)",
                "desc": "هنا تتابع كل الأصناف الموجودة في المحل وكمياتها. يمكنك إضافة أصناف جديدة، وتعديل الأسعار، وتعرف المنتجات التي قاربت على النفاد لشرائها."
            },
            {
                "title": "👥 5. العملاء والموردين (Customers & Suppliers)",
                "desc": "لتسجيل بيانات وتفاصيل (التجار والموردين) الذين نشتري منهم، و(العملاء) الدائمين لتسهيل إصدار الفواتير ومتابعة حساباتهم."
            },
            {
                "title": "💸 6. المصروفات (Expenses)",
                "desc": "لتسجيل أي مصروفات يومية تخرج من الدرج مثل: (الكهرباء، الإيجار، الرواتب، أو النثريات) حتى تكون الحسابات دقيقة ولا يوجد عجز."
            },
            {
                "title": "📊 7. الحسابات والتقارير (Accounting & Reports)",
                "desc": "هذا القسم مخصص غالباً للإدارة. يحتوي على (قيود اليومية، دفتر الأستاذ، قائمة الدخل، والميزانية) لمعرفة صافي الأرباح وحالة المحل المالية بدقة."
            }
        ]

        for page in self.pages_data:
            page_widget = QWidget()
            page_layout = QVBoxLayout(page_widget)
            page_layout.setContentsMargins(10, 20, 10, 20)

            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #F1F5F9;
                    border: 1px solid #CBD5E1;
                    border-radius: 12px;
                }
            """)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(20, 30, 20, 30)
            frame_layout.setSpacing(20)

            title_lbl = QLabel(page["title"])
            title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B; border: none;")
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

            desc_lbl = QLabel(page["desc"])
            desc_lbl.setStyleSheet("font-size: 16px; color: #475569; border: none; line-height: 1.5;")
            desc_lbl.setWordWrap(True)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

            frame_layout.addWidget(title_lbl)
            frame_layout.addWidget(desc_lbl)
            frame_layout.addStretch()

            page_layout.addWidget(frame)
            self.stack.addWidget(page_widget)

        # Navigation Buttons
        nav_layout = QHBoxLayout()
        
        self.btn_close = QPushButton("إغلاق البرنامج التعليمي")
        self.btn_close.setStyleSheet("background-color: #DC2626; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        self.btn_close.clicked.connect(self.close)

        self.btn_prev = QPushButton("السابق")
        self.btn_prev.setStyleSheet("background-color: #64748B; color: white; padding: 10px; border-radius: 6px; font-weight: bold; width: 100px;")
        self.btn_prev.clicked.connect(self.go_prev)

        self.btn_next = QPushButton("التالي")
        self.btn_next.setStyleSheet("background-color: #059669; color: white; padding: 10px; border-radius: 6px; font-weight: bold; width: 100px;")
        self.btn_next.clicked.connect(self.go_next)

        nav_layout.addWidget(self.btn_close)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)

        layout.addLayout(nav_layout)
        
        self.update_buttons()

    def go_next(self):
        curr = self.stack.currentIndex()
        if curr < self.stack.count() - 1:
            self.stack.setCurrentIndex(curr + 1)
        self.update_buttons()

    def go_prev(self):
        curr = self.stack.currentIndex()
        if curr > 0:
            self.stack.setCurrentIndex(curr - 1)
        self.update_buttons()

    def update_buttons(self):
        curr = self.stack.currentIndex()
        self.btn_prev.setEnabled(curr > 0)
        
        if curr == self.stack.count() - 1:
            self.btn_next.setText("إنهاء")
            self.btn_next.clicked.disconnect()
            self.btn_next.clicked.connect(self.close)
        else:
            self.btn_next.setText("التالي")
            try:
                self.btn_next.clicked.disconnect()
            except:
                pass
            self.btn_next.clicked.connect(self.go_next)
