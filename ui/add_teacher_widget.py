# SMS/ui/add_teacher_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from business.teacher_service import add_teacher
from ui.teacher_form_widget import TeacherFormWidget


class AddTeacherWidget(QWidget):
    """
    A widget for adding a new teacher.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(open("assets/style.qss").read())

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Add New Teacher")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.form_widget = TeacherFormWidget()
        layout.addWidget(self.form_widget)

        self.btn_submit = QPushButton("Add Teacher")
        self.btn_submit.setObjectName("primaryButton")
        layout.addWidget(self.btn_submit)
        self.setLayout(layout)

        self.btn_submit.clicked.connect(self.handle_submit)

    def handle_submit(self):
        """Handles the logic for adding a new teacher."""
        result = self.form_widget.get_form_data()
        if result[2] is False:  # is_valid is False
            return
        
        data, contacts, is_valid, subjects, qualifications, experiences, class_sections = result
        
        try:
            # Call the backend operation
            success, status_msg, teacher_id = add_teacher(
                data['first_name'], data['middle_name'], data['last_name'],
                data['father_name'], data['dob'], 
                data['address'], data['gender'], contacts,
                data['joining_date'], data['salary'],
                data['security_deposit'], role=data['role'],
                subjects=subjects, qualifications=qualifications,
                experiences=experiences, class_sections=class_sections
            )

            if success:
                QMessageBox.information(self, "Success", f"Teacher added successfully! (ID: {teacher_id})")
                self.clear_fields()
            else:
                QMessageBox.critical(self, "Error", f"Failed to add teacher:\n{status_msg}")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error adding teacher: {error_details}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{str(e)}\n\nPlease check the console for details.")

    def clear_fields(self):
        """Clears all form fields."""
        self.form_widget.clear_fields()

