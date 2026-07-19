
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLineEdit, QMessageBox, QDialog, QFormLayout, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from database.db_config import DatabaseConnection
from modules.theme import COLORS, get_button_style, get_action_button_style
from modules.localization import tr

class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("User Details")
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.user_edit = QLineEdit()
        self.pass_edit = QLineEdit()
        self.role_combo = QComboBox()
        self.role_combo.addItems(["staff", "admin"])

        if self.user_data:
            self.user_edit.setText(self.user_data.get('username', ''))
            self.pass_edit.setText(self.user_data.get('password', ''))
            self.role_combo.setCurrentText(self.user_data.get('role', 'staff'))

        form.addRow("Username:", self.user_edit)
        form.addRow("Password:", self.pass_edit)
        form.addRow("Role:", self.role_combo)
        layout.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(get_button_style('accent'))
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet(get_button_style('bg_mid'))
        cancel_btn.clicked.connect(self.reject)
        
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def get_data(self):
        return {
            'username': self.user_edit.text().strip(),
            'password': self.pass_edit.text().strip(),
            'role': self.role_combo.currentText()
        }

class UsersModule(QWidget):
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        header = QLabel("Staff Management")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_main']}; margin-bottom: 20px; background: transparent; border: none; border-bottom: 2px solid {COLORS['border']}; padding-bottom: 8px;")
        layout.addWidget(header)

        btn_h = QHBoxLayout()
        add_btn = QPushButton("➕ Create New Account")
        add_btn.setFixedWidth(220)
        add_btn.setStyleSheet(get_button_style('accent'))
        add_btn.clicked.connect(self.add_user)
        btn_h.addWidget(add_btn)
        btn_h.addStretch()
        layout.addLayout(btn_h)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Username
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 280)
        self.table.verticalHeader().setDefaultSectionSize(55)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"QTableWidget {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        layout.addWidget(self.table)

    def load_users(self):
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role FROM users")
                users = cursor.fetchall()
                self.table.setRowCount(len(users))
                for i, user in enumerate(users):
                    self.table.setItem(i, 0, QTableWidgetItem(str(user['id'])))
                    self.table.setItem(i, 1, QTableWidgetItem(user['username']))
                    self.table.setItem(i, 2, QTableWidgetItem(user['role'].upper()))
                    
                    # Action Buttons Container
                    actions_widget = QWidget()
                    actions_widget.setMinimumHeight(50)
                    actions_widget.setStyleSheet("background: transparent; border: none;")
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(5, 5, 5, 5)
                    actions_layout.setSpacing(8)
                    
                    edit_btn = QPushButton("✏️ Edit")
                    edit_btn.setFixedSize(120, 32)
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.setStyleSheet(get_action_button_style('accent'))
                    edit_btn.clicked.connect(lambda _, r=i: self.edit_user(r))
                    
                    del_btn = QPushButton("🗑️ Delete")
                    del_btn.setFixedSize(120, 32)
                    del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    del_btn.setStyleSheet(get_action_button_style('red'))
                    del_btn.clicked.connect(lambda _, r=i: self.delete_user(r))
                    
                    actions_layout.addStretch()
                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(del_btn)
                    actions_layout.addStretch()
                    
                    self.table.setCellWidget(i, 3, actions_widget)
                    self.table.setRowHeight(i, 50)
        except Exception as e:
            print(f"User load error: {e}")

    def delete_user(self, row):
        uid = self.table.item(row, 0).text()
        username = self.table.item(row, 1).text()
        
        if username == 'admin':
            QMessageBox.warning(self, "Security", "The primary admin account cannot be deleted.")
            return

        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete staff account '{username}'?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id=?", (uid,))
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {e}")

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                                  (data['username'], data['password'], data['role']))
                self.load_users()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create user: {e}")

    def edit_user(self, row):
        uid = self.table.item(row, 0).text()
        dialog = UserDialog(self, {'username': self.table.item(row, 1).text(), 'role': self.table.item(row, 2).text().lower()})
        if dialog.exec():
            data = dialog.get_data()
            try:
                with DatabaseConnection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?", 
                                  (data['username'], data['password'], data['role'], uid))
                self.load_users()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not update user: {e}")

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.user = None
        self.setWindowTitle("Attar AIS - Secure Login")
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"background: #0f172a; color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)
        
        logo = QLabel("🌿")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 48px;")
        layout.addWidget(logo)
        
        self.u_input = QLineEdit()
        self.u_input.setPlaceholderText("Username")
        self.u_input.setStyleSheet("padding: 10px; border-radius: 6px; background: #1e293b; border: 1px solid #334155;")
        layout.addWidget(self.u_input)
        
        self.p_input = QLineEdit()
        self.p_input.setPlaceholderText("Password")
        self.p_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.p_input.setStyleSheet("padding: 10px; border-radius: 6px; background: #1e293b; border: 1px solid #334155;")
        layout.addWidget(self.p_input)
        
        self.login_btn = QPushButton("Access System")
        self.login_btn.setFixedHeight(40)
        self.login_btn.setStyleSheet(f"background: {COLORS['accent']}; color: white; font-weight: bold; border-radius: 6px;")
        self.login_btn.clicked.connect(self.do_login)
        layout.addWidget(self.login_btn)

    def do_login(self):
        u, p = self.u_input.text(), self.p_input.text()
        try:
            with DatabaseConnection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
                res = cur.fetchone()
                if res:
                    self.user = dict(res)
                    from database.db_config import log_action
                    log_action(self.user['id'], self.user['username'], 'Login', 'Auth', 'User logged into system')
                    self.accept()
                else:
                    QMessageBox.warning(self, "Failed", "Invalid username or password")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
