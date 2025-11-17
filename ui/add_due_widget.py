# SMS/ui/add_due_widget.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout,
    QMessageBox, QHBoxLayout, QDialog
)
from PyQt5.QtCore import Qt, QDate
# --- FIX: Update imports to Service/Common layers ---
from business.due_service import add_manual_due
from common.utils import (
    show_warning, validate_required_fields, validate_date_format, validate_is_float,
    validate_is_not_future_date # <-- NEW IMPORT
)
from datetime import datetime
from .student_search_dialog import StudentSearchDialog
from business.student_service import check_student_exists # Service Layer
# --- END FIX ---

class AddDueWidget(QWidget):
    """
    A form widget for manually adding a new pending due to a student.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_student_id = None # Store the ID of the selected student
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Add Manual Due")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form_layout = QFormLayout()
        
        # --- Student Search Section ---
        self.student_id_input = QLineEdit()
        self.student_id_input.setReadOnly(True)
        self.student_id_input.setPlaceholderText("Click 'Search' to select a student")
        
        self.student_name_input = QLineEdit()
        self.student_name_input.setReadOnly(True)
        
        self.search_student_btn = QPushButton("Search for Student")
        self.search_student_btn.setObjectName("secondaryButton")
        self.search_student_btn.clicked.connect(self.open_student_search)

        form_layout.addRow("Student ID:", self.student_id_input)
        form_layout.addRow("Student Name:", self.student_name_input)
        form_layout.addRow("", self.search_student_btn)
        
        # --- Due Details Section ---
        self.due_type_input = QLineEdit()
        self.due_type_input.setPlaceholderText("e.g., Exam Fee, Fine, Sports Fund")
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g., 1500.00")
        
        self.due_date_input = QLineEdit()
        self.due_date_input.setPlaceholderText("YYYY-MM-DD")
        self.due_date_input.setText(datetime.now().strftime("%Y-%m-%d"))

        form_layout.addRow("Due Type:", self.due_type_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Due Date:", self.due_date_input)

        self.btn_submit = QPushButton("Add Due")
        self.btn_submit.setObjectName("primaryButton")
        self.btn_submit.clicked.connect(self.handle_submit)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(self.btn_submit)

        self.init_enter_key_navigation()

    def init_enter_key_navigation(self):
        # We can't chain from the read-only fields, so we chain from the button
        self.search_student_btn.clicked.connect(self.due_type_input.setFocus)
        self.due_type_input.returnPressed.connect(self.amount_input.setFocus)
        self.amount_input.returnPressed.connect(self.due_date_input.setFocus)
        self.due_date_input.returnPressed.connect(self.btn_submit.click)

    def open_student_search(self):
        """
        Opens the reusable student search dialog.
        """
        dialog = StudentSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted: # If the user clicked "OK"
            student_id, student_name = dialog.get_selected_student()
            if student_id:
                self.selected_student_id = student_id
                self.student_id_input.setText(str(self.selected_student_id))
                self.student_name_input.setText(student_name)
                # Set focus to the next logical field
                self.due_type_input.setFocus()

    def handle_submit(self):
        data = {
            "due_type": self.due_type_input.text().strip(),
            "amount": self.amount_input.text().strip(),
            "due_date": self.due_date_input.text().strip()
        }
        
        # 1. Validate Student Selection
        if not self.selected_student_id:
            show_warning(self, "Validation Error", "Please search for and select a student.")
            return

        # 2. Validate required fields
        is_valid, error_msg = validate_required_fields(data, data.keys())
        if not is_valid:
            show_warning(self, "Validation Error", error_msg)
            return
            
        # 3. Validate Amount
        is_valid, error_msg = validate_is_float(data['amount'])
        if not is_valid:
            show_warning(self, "Validation Error", f"Amount: {error_msg}")
            return
        amount = float(data['amount'])

        # 4. Validate Date & Apply Business Rule: Due Date Must Not Be Past
        is_valid_format, error_msg = validate_date_format(data['due_date'])
        if not is_valid_format:
            show_warning(self, "Validation Error", f"Due Date: {error_msg}")
            return

        is_valid_future, future_msg = validate_is_not_future_date(data['due_date'])
        if not is_valid_future:
            show_warning(self, "Validation Error", f"Due Date: {future_msg}")
            return
            
        # 5. Add to database
        try:
            success = add_manual_due(
                self.selected_student_id, 
                data['due_type'], 
                amount, 
                data['due_date']
            )
            if success:
                QMessageBox.information(self, "Success", f"Due successfully added for Student ID {self.selected_student_id}.")
                self.clear_fields()
            else:
                QMessageBox.critical(self, "Error", "Failed to add due. Check logs.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def clear_fields(self):
        self.selected_student_id = None
        self.student_id_input.clear()
        self.student_name_input.clear()
        self.due_type_input.clear()
        self.amount_input.clear()
        self.due_date_input.setText(datetime.now().strftime("%Y-%m-%d"))