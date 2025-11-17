# SMS/ui/remove_student_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QGroupBox, QLabel,
    QDialog, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt
from datetime import datetime
from .student_search_dialog import StudentSearchDialog
from business.student_service import get_student_details_by_id, remove_student
from common.utils import show_warning, validate_date_format, validate_is_not_future_date

class RemoveStudentWidget(QWidget):
    """
    Admin-only widget to mark a student as inactive/removed.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_student_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- 1. Find Student Group ---
        search_group = QGroupBox("1. Find Student to Remove")
        search_layout = QFormLayout()
        
        self.student_id_label = QLabel("N/A")
        self.student_name_label = QLabel("N/A")
        
        self.search_student_btn = QPushButton("Search for Student")
        self.search_student_btn.setObjectName("secondaryButton")
        self.search_student_btn.clicked.connect(self.open_student_search)
        
        search_layout.addRow("Student ID:", self.student_id_label)
        search_layout.addRow("Student Name:", self.student_name_label)
        search_layout.addRow(self.search_student_btn)
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # --- 2. Removal Details Group ---
        self.remove_group = QGroupBox("2. Removal Details")
        remove_layout = QFormLayout()
        
        self.leaving_date_input = QLineEdit()
        self.leaving_date_input.setPlaceholderText("YYYY-MM-DD")
        self.leaving_date_input.setText(datetime.now().strftime("%Y-%m-%d"))

        self.btn_remove = QPushButton("Confirm Removal (Mark Inactive)")
        self.btn_remove.setObjectName("primaryButton")
        self.btn_remove.clicked.connect(self.handle_remove_student)
        
        remove_layout.addRow("Date of Leaving:", self.leaving_date_input)
        remove_layout.addRow(self.btn_remove)
        
        self.remove_group.setLayout(remove_layout)
        main_layout.addWidget(self.remove_group)
        
        main_layout.addStretch()
        
        # Initial state
        self.remove_group.setEnabled(False)

        # Enter key navigation
        self.leaving_date_input.returnPressed.connect(self.btn_remove.click)

    def open_student_search(self):
        """Opens the student search dialog and retrieves the selected student."""
        dialog = StudentSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            student_id, student_name = dialog.get_selected_student()
            if student_id:
                # Check if the student is already inactive (optional, but robust)
                details = get_student_details_by_id(student_id)
                if details and details.get('is_active') == 0:
                     show_warning(self, "Warning", f"Student ID {student_id} is already marked as inactive (Left: {details.get('date_of_leaving', 'N/A')}).")
                     self.clear_selection()
                     return
                     
                self.current_student_id = student_id
                self.student_id_label.setText(str(student_id))
                self.student_name_label.setText(student_name)
                self.remove_group.setEnabled(True)
                self.leaving_date_input.setFocus()
            else:
                self.clear_selection()


    def handle_remove_student(self):
        if not self.current_student_id:
            show_warning(self, "Error", "Please select a student to remove first.")
            return

        date_of_leaving = self.leaving_date_input.text().strip()
        
        # 1. Validate Date
        is_valid_format, error_msg = validate_date_format(date_of_leaving)
        if not is_valid_format:
            show_warning(self, "Validation Error", f"Date of Leaving: {error_msg}")
            return

        is_valid_future, future_msg = validate_is_not_future_date(date_of_leaving)
        if not is_valid_future:
            show_warning(self, "Validation Error", f"Date of Leaving: {future_msg}")
            return
            
        # 2. Confirmation
        reply = QMessageBox.question(self, "Confirm Removal",
            f"Are you sure you want to mark Student ID {self.current_student_id} as REMOVED (Inactive)?\n"
            f"All their data and payment history will be preserved.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            # 3. Call service
            success, message = remove_student(self.current_student_id, date_of_leaving)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.clear_selection()
            else:
                QMessageBox.critical(self, "Error", f"Removal failed:\n{message}")

    def clear_selection(self):
        self.current_student_id = None
        self.student_id_label.setText("N/A")
        self.student_name_label.setText("N/A")
        self.remove_group.setEnabled(False)
        self.leaving_date_input.setText(datetime.now().strftime("%Y-%m-%d"))