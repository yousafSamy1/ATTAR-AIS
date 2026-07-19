
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from database.db_config import DatabaseConnection
from modules.theme import COLORS, get_button_style
from modules.localization import tr

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Attar AIS - Login")
        self.setFixedSize(380, 480)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main background frame
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 380, 480)
        self.main_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 20px;
                border: 1px solid {COLORS['border']};
            }}
        """)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Logo/Title
        title_lbl = QLabel("ATTAR AIS")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {COLORS['accent']}; border: none;")
        layout.addWidget(title_lbl)

        subtitle = QLabel("Inventory & Accounting")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_dim']}; border: none; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Inputs
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setMinimumHeight(45)
        self.user_input.setStyleSheet(self._input_style())
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setMinimumHeight(45)
        self.pass_input.setStyleSheet(self._input_style())
        layout.addWidget(self.pass_input)

        layout.addStretch()

        # Login Button
        login_btn = QPushButton("🔓 LOGIN")
        login_btn.setMinimumHeight(50)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet(get_button_style('accent', font_size=14))
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        # Close/Exit Button
        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet(f"color: {COLORS['text_dim']}; border: none; font-size: 12px;")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self.reject)
        layout.addWidget(exit_btn)

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {COLORS['bg']};
                color: {COLORS['text_main']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 10px;
                padding: 5px 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {COLORS['accent']};
            }}
        """

    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password.")
            return

        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                user = cursor.fetchone()

                if user:
                    self.user_data = dict(user)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to database: {e}")

    def get_user(self):
        return self.user_data
