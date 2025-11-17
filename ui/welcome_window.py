# SMS/ui/welcome_window.py
import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.signup_window import SignupWindow
from ui.receptionist_dashboard import ReceptionistDashboard
from ui.login_window import LoginWindow 
# --- NEW IMPORT: Admin Dashboard ---
from ui.admin_dashboard import AdminDashboard
# --- FIX: Update imports ---
from dal.db_init import initialize_db
from business.due_service import add_monthly_fees_for_all_students # Script logic now in Service
# --- End of new imports ---

class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome - School Management System")
        self.setFixedSize(600, 400)
        self.setStyleSheet(open("assets/style.qss").read())
        
        # --- Run critical startup tasks ---
        initialize_db()  # Ensure DB and default admin exist
        self.run_automated_tasks() # Run automated scripts
        # --- End of task section ---

        # Persistent references
        self.signup_window = None
        self.dashboard_window = None

        self.init_ui()

    def run_automated_tasks(self):
        """
        Runs any automated tasks, like checking for monthly fee generation.
        """
        print("Checking for automated tasks...")
        # This function is safe to call daily.
        # It has its own internal checks for the date and to prevent duplicates.
        add_monthly_fees_for_all_students()

    def init_ui(self):
        # Title
        title = QLabel("Welcome to School Management System")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setObjectName("titleLabel")

        # Buttons
        self.btn_login_admin = QPushButton("Admin Login")
        self.btn_login_recep = QPushButton("Receptionist Login")
        self.btn_signup = QPushButton("Sign Up (Receptionist)")
        self.btn_login_admin.setObjectName("primaryButton")
        self.btn_login_recep.setObjectName("primaryButton")
        self.btn_signup.setObjectName("secondaryButton")

        # Layout
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.btn_login_admin)
        button_layout.addWidget(self.btn_login_recep)
        button_layout.addWidget(self.btn_signup)
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)

        main_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(title)
        main_layout.addSpacing(40)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # Connections
        self.btn_signup.clicked.connect(self.open_signup_window)
        self.btn_login_admin.clicked.connect(lambda: self.open_login_window("Admin"))
        self.btn_login_recep.clicked.connect(lambda: self.open_login_window("Receptionist"))

    def open_signup_window(self):
        if self.signup_window is None:
            self.signup_window = SignupWindow(self.show)
        self.signup_window.show()
        self.hide()

    def open_login_window(self, role):
        self.login_window = LoginWindow(role, self.show, self.open_dashboard)
        self.login_window.show()
        self.hide()

    def open_dashboard(self, role, username):
        if role == "Admin":
            self.dashboard_window = AdminDashboard(username, self.show)
        else:
            self.dashboard_window = ReceptionistDashboard(username, self.show)
            
        self.dashboard_window.show()