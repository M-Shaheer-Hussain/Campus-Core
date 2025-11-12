# SMS/ui/signup_window.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from core.db_receptionist import add_receptionist
from core.emailer import generate_code, send_code
# Import reusable utilities
from core.utils import (
    show_warning, validate_required_fields, validate_dob_not_current_year,
    validate_password_length
)
from datetime import datetime

class SignupWindow(QWidget):
    def __init__(self, go_back_callback):
        super().__init__()
        self.setWindowTitle("Receptionist Sign-Up")
        self.setFixedSize(500, 700)
        self.setStyleSheet(self.load_styles())
        self.go_back_callback = go_back_callback
        self.verification_code = None
        self.init_ui()

    def load_styles(self):
        return """
        QWidget {
            background-color: #f0f2f5;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        QLabel#titleLabel {
            font-size: 22px;
            font-weight: bold;
            color: #333;
        }
        QLineEdit, QComboBox {
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 14px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #4a90e2;
        }
        QPushButton {
            background-color: #4a90e2;
            color: white;
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #357ABD;
        }
        QPushButton:pressed {
            background-color: #2A5C9B;
        }
        QComboBox {
            background-color: white;
        }
        """

    def init_ui(self):
        title = QLabel("Receptionist Sign-Up", self)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        # Input fields
        self.first_name = QLineEdit(); self.first_name.setPlaceholderText("First Name")
        self.middle_name = QLineEdit(); self.middle_name.setPlaceholderText("Middle Name (optional)")
        self.last_name = QLineEdit(); self.last_name.setPlaceholderText("Last Name")
        self.father_name = QLineEdit(); self.father_name.setPlaceholderText("Father Name")
        self.mother_name = QLineEdit(); self.mother_name.setPlaceholderText("Mother Name")
        self.dob = QLineEdit(); self.dob.setPlaceholderText("DOB (YYYY-MM-DD)")
        self.address = QLineEdit(); self.address.setPlaceholderText("Address")

        # Gender dropdown
        self.gender = QComboBox()
        self.gender.addItems(["Select Gender", "Male", "Female", "Other"])

        # Contacts
        self.email = QLineEdit(); self.email.setPlaceholderText("Email")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("Phone Number")

        # Password
        self.password = QLineEdit(); self.password.setPlaceholderText("Password (min 8 chars)")
        self.password.setEchoMode(QLineEdit.Password)

        # Verification code
        self.code_input = QLineEdit(); self.code_input.setPlaceholderText("Enter Verification Code")

        # Buttons
        self.btn_generate = QPushButton("Generate Code")
        self.btn_add = QPushButton("Sign Up")
        self.btn_back = QPushButton("Back")

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 20, 50, 20)
        layout.setSpacing(12)
        layout.addWidget(title)
        for w in [self.first_name, self.middle_name, self.last_name,
                  self.father_name, self.mother_name, self.dob, self.address,
                  self.gender, self.email, self.phone, self.password,
                  self.code_input, self.btn_generate, self.btn_add, self.btn_back]:
            layout.addWidget(w)
        self.setLayout(layout)

        # Button connections
        self.btn_generate.clicked.connect(self.handle_generate_code)
        self.btn_add.clicked.connect(self.handle_signup)
        self.btn_back.clicked.connect(self.handle_back)

        # Enter key navigation
        self.first_name.returnPressed.connect(lambda: self.middle_name.setFocus())
        self.middle_name.returnPressed.connect(lambda: self.last_name.setFocus())
        self.last_name.returnPressed.connect(lambda: self.father_name.setFocus())
        self.father_name.returnPressed.connect(lambda: self.mother_name.setFocus())
        self.mother_name.returnPressed.connect(lambda: self.dob.setFocus())
        self.dob.returnPressed.connect(lambda: self.address.setFocus())
        self.address.returnPressed.connect(lambda: self.gender.setFocus())
        self.email.returnPressed.connect(lambda: self.phone.setFocus())
        self.phone.returnPressed.connect(lambda: self.password.setFocus())
        self.password.returnPressed.connect(lambda: self.code_input.setFocus())
        self.code_input.returnPressed.connect(self.handle_signup)

    def handle_generate_code(self):
        self.verification_code = generate_code()
        send_code(self.verification_code)
        QMessageBox.information(self, "Code Sent", "Verification code sent to admin email.")

    def handle_signup(self):
        # Collect inputs into a dictionary
        data = {
            "first": self.first_name.text().strip(),
            "middle": self.middle_name.text().strip(),
            "last": self.last_name.text().strip(),
            "father": self.father_name.text().strip(),
            "mother": self.mother_name.text().strip(),
            "dob": self.dob.text().strip(),
            "address": self.address.text().strip(),
            "gender": self.gender.currentText(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "password": self.password.text().strip(),
            "code": self.code_input.text().strip(),
        }

        required_fields = [
            "first", "last", "father", "mother", "dob",
            "address", "email", "phone", "password", "code"
        ]

        # Use display names for clearer error messages
        display_names = {
            "first": "First Name", "last": "Last Name", "father": "Father Name",
            "mother": "Mother Name", "dob": "DOB", "address": "Address",
            "email": "Email", "phone": "Phone Number", "password": "Password", "code": "Verification Code"
        }
        
        # 1. Validate required fields
        is_valid, error_message = validate_required_fields(data, required_fields, display_names)
        if not is_valid:
            show_warning(self, "Validation Error", error_message)
            return
        
        # 2. Validate Gender selection (special case for QComboBox initial item)
        if data['gender'] == "Select Gender":
            show_warning(self, "Validation Error", "Please select a valid Gender.")
            return

        # 3. Validate password length
        is_valid, error_message = validate_password_length(data['password'])
        if not is_valid:
            show_warning(self, "Error", error_message)
            return

        # 4. DOB validation: format and not current year
        is_valid, error_message = validate_dob_not_current_year(data['dob'])
        if not is_valid:
            show_warning(self, "Invalid Date", error_message)
            return

        # 5. Verification code check
        if self.verification_code is None:
            show_warning(self, "Error", "Please generate verification code first.")
            return
        if data['code'] != self.verification_code:
            QMessageBox.critical(self, "Error", "Incorrect verification code.")
            return

        # Contacts structure is updated to be consistent with db_receptionist
        contacts = [
            {"type": "email", "value": data['email'], "label": "primary"},
            {"type": "phone", "value": data['phone'], "label": "primary"}
        ]

        try:
            add_receptionist(data['father'], data['mother'], data['dob'], data['address'], data['gender'],
                              data['first'], data['middle'], data['last'], data['password'], contacts)
            QMessageBox.information(self, "Success", "Receptionist added successfully!")
            self.handle_back()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not add receptionist:\n{e}")

    def handle_back(self):
        self.close()
        self.go_back_callback()