from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from modules.theme import COLORS
from modules.localization import tr, get_saved_lang

class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('tutorial_title'))
        self.setFixedSize(600, 450)
        
        lang = get_saved_lang()
        if lang == 'ar':
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg_card']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.header_label = QLabel(tr('tutorial_welcome'))
        self.header_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['accent']}; padding-bottom: 10px; background: transparent;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        layout.addWidget(self.stack)

        self.pages_data = [
            {"title": tr('tut_1_title'), "desc": tr('tut_1_desc')},
            {"title": tr('tut_2_title'), "desc": tr('tut_2_desc')},
            {"title": tr('tut_3_title'), "desc": tr('tut_3_desc')},
            {"title": tr('tut_4_title'), "desc": tr('tut_4_desc')},
            {"title": tr('tut_5_title'), "desc": tr('tut_5_desc')},
            {"title": tr('tut_6_title'), "desc": tr('tut_6_desc')},
            {"title": tr('tut_7_title'), "desc": tr('tut_7_desc')},
        ]

        for page in self.pages_data:
            page_widget = QWidget()
            page_layout = QVBoxLayout(page_widget)
            page_layout.setContentsMargins(10, 20, 10, 20)

            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['sidebar_mid']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(20, 30, 20, 30)
            frame_layout.setSpacing(20)

            title_lbl = QLabel(page["title"])
            title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['sidebar_text']}; border: none; background: transparent;")
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

            desc_lbl = QLabel(page["desc"])
            desc_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['accent2']}; border: none; background: transparent;")
            desc_lbl.setWordWrap(True)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            frame_layout.addWidget(title_lbl)
            frame_layout.addWidget(desc_lbl)
            frame_layout.addStretch()

            page_layout.addWidget(frame)
            self.stack.addWidget(page_widget)

        # Navigation Buttons
        nav_layout = QHBoxLayout()
        
        self.btn_close = QPushButton(tr('tut_close'))
        self.btn_close.setStyleSheet(f"background-color: {COLORS['red']}; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        self.btn_close.clicked.connect(self.close)

        self.btn_prev = QPushButton(tr('tut_prev'))
        self.btn_prev.setStyleSheet(f"background-color: {COLORS['sidebar_mid']}; color: {COLORS['sidebar_text']}; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        self.btn_prev.clicked.connect(self.go_prev)

        self.btn_next = QPushButton(tr('tut_next'))
        self.btn_next.setStyleSheet(f"background-color: {COLORS['accent']}; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
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
            self.btn_next.setText(tr('tut_finish'))
            try:
                self.btn_next.clicked.disconnect()
            except:
                pass
            self.btn_next.clicked.connect(self.close)
        else:
            self.btn_next.setText(tr('tut_next'))
            try:
                self.btn_next.clicked.disconnect()
            except:
                pass
            self.btn_next.clicked.connect(self.go_next)
