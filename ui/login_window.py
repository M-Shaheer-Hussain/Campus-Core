from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
# --- FIX: Update imports to Service Layer ---
from business.login_service import validate_admin, validate_receptionist
# --- END FIX ---

class LoginWindow(QWidget):
    def __init__(self, role, go_back_callback, open_dashboard_callback):
        super().__init__()
        self.role = role
        self.go_back_callback = go_back_callback
        self.open_dashboard_callback = open_dashboard_callback

        self.setWindowTitle(f"{role} Login - School Management System")
        self.setFixedSize(600, 400)
        self.setStyleSheet(open("assets/style.qss").read())  # match existing style

        self.init_ui()
        self.init_connections()

    def init_ui(self):
        # Title
        self.title_label = QLabel(f"{self.role} Login")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.title_label.setObjectName("titleLabel")

        # Username / Password inputs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username (FirstName LastName)")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Buttons
        self.btn_login = QPushButton("Login")
        self.btn_back = QPushButton("Back")
        self.btn_login.setObjectName("primaryButton")
        self.btn_back.setObjectName("secondaryButton")

        # Layouts
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.username_input)
        input_layout.addWidget(self.password_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_login)
        button_layout.addWidget(self.btn_back)

        main_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(self.title_label)
        main_layout.addSpacing(40)
        main_layout.addLayout(input_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def init_connections(self):
        self.btn_login.clicked.connect(self.handle_login)
        self.btn_back.clicked.connect(self.handle_back)
        # Enter key navigation
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password.")
            return

        # Validate based on role (Calls Service Layer)
        if self.role == "Admin":
            valid = validate_admin(username, password)
        else:
            valid = validate_receptionist(username, password)

        if valid:
            QMessageBox.information(self, "Success", f"{self.role} logged in successfully!")
            self.open_dashboard_callback(self.role, username)
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")

    def handle_back(self):
        self.close()
        self.go_back_callback()