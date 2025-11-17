# SMS/ui/add_student_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from .add_student_form import StudentFormWidget
# --- FIX: Update imports to Service layers ---
from business.student_service import add_student
from business.due_service import add_specific_monthly_fee
# --- END FIX ---

class AddStudentWidget(QWidget):
    """
    A widget for adding a new student. It contains the reusable
    StudentFormWidget and handles the submission logic for *creating* students.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Create the reusable form
        self.form_widget = StudentFormWidget()
        
        # 2. Create the submit button
        self.btn_submit = QPushButton("Add Student")
        self.btn_submit.setObjectName("primaryButton")
        
        # 3. Set up the layout
        main_layout = QVBoxLayout(self)
        title = QLabel("Add New Student")
        title.setObjectName("titleLabel")
        # --- This line is now fixed ---
        title.setAlignment(Qt.AlignCenter) 
        main_layout.addWidget(title)
        main_layout.addWidget(self.form_widget)
        main_layout.addWidget(self.btn_submit)
        
        # 4. Connect signals
        self.btn_submit.clicked.connect(self.handle_submit_add)
        
        # Connect the form's last contact row to the submit button
        self.form_widget.contact_rows[-1].last_input().returnPressed.connect(self.btn_submit.click)
        # Re-connect add_contact_row to chain to the submit button
        self.form_widget.add_contact_btn.clicked.connect(self.on_add_contact_row)

    def on_add_contact_row(self):
        """When a new contact row is added, chain its 'Enter' to the submit button."""
        new_row = self.form_widget.add_contact_row()
        new_row.last_input().returnPressed.connect(self.btn_submit.click)

    def handle_submit_add(self):
        """
        Handles the logic for *adding* a new student. (Calls Service Layer)
        """
        # 1. Get validated data from the form
        data, contacts, family_id, is_valid = self.form_widget.get_data()
        
        if not is_valid:
            return # Validation failed, warnings already shown
            
        # 2. Call the backend operation
        success, status_msg, student_id, fee_amount, due_type_name = add_student(
            data['first_name'], data['middle_name'], data['last_name'], data['father_name'],
            data['mother_name'], data['dob'], data['address'], data['gender'], contacts,
            data['date_of_admission'], data['monthly_fee'], data['annual_fund'], 
            data['student_class'], family_id
        )

        if success:
            # 3. Handle the response (e.g., ask for fee confirmation)
            if status_msg == "NEEDS_FEE_CONFIRMATION":
                reply = QMessageBox.question(self, "Confirm Monthly Fee",
                    f"Student added successfully (ID: {student_id}).\n\n"
                    f"The fee '{due_type_name}' has already been posted for other students this month.\n\n"
                    f"Do you want to add this fee to this new student?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                
                if reply == QMessageBox.Yes:
                    add_specific_monthly_fee(student_id, fee_amount, due_type_name)
                    QMessageBox.information(self, "Success", "Student and monthly fee added successfully!")
                else:
                    QMessageBox.information(self, "Success", "Student added successfully. Monthly fee was *not* applied.")
            
            else: # Standard "SUCCESS" message
                QMessageBox.information(self, "Success", "Student added successfully!")
            
            self.form_widget.clear_fields()
        else:
            QMessageBox.critical(self, "Error", f"Failed to add student:\n{status_msg}")