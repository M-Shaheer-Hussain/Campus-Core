# SMS/ui/add_teacher_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout,
    QComboBox, QMessageBox, QHBoxLayout, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from business.teacher_service import add_teacher, TEACHER_ROLES
from common.utils import (
    show_warning, validate_required_fields, validate_date_format, 
    validate_phone_length, validate_is_float, validate_is_not_future_date,
    validate_is_positive_non_zero_float
)
from datetime import datetime

class ContactRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Phone", "Email"])
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Value (e.g., 03XXYYYYYYY or email@example.com)")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;") 

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.type_combo, 2)
        row_layout.addWidget(self.value_input, 5)
        row_layout.addWidget(self.remove_btn, 1)

    def last_input(self):
        return self.value_input


class SubjectRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Subject Name (e.g., Mathematics)")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;")
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.subject_input, 1)
        row_layout.addWidget(self.remove_btn)
    
    def get_subject(self):
        return self.subject_input.text().strip()


class QualificationRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.degree_input = QLineEdit()
        self.degree_input.setPlaceholderText("Degree (e.g., M.Sc)")
        self.institution_input = QLineEdit()
        self.institution_input.setPlaceholderText("Institution")
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Year")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;")
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.degree_input, 2)
        row_layout.addWidget(self.institution_input, 3)
        row_layout.addWidget(self.year_input, 1)
        row_layout.addWidget(self.remove_btn)
    
    def get_data(self):
        return {
            'degree': self.degree_input.text().strip(),
            'institution': self.institution_input.text().strip(),
            'year': self.year_input.text().strip() or None
        }


class ExperienceRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.institution_input = QLineEdit()
        self.institution_input.setPlaceholderText("Institution")
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Position")
        self.start_date_input = QLineEdit()
        self.start_date_input.setPlaceholderText("Start Date (YYYY-MM-DD)")
        self.end_date_input = QLineEdit()
        self.end_date_input.setPlaceholderText("End Date (YYYY-MM-DD)")
        self.years_input = QLineEdit()
        self.years_input.setPlaceholderText("Years")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;")
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.institution_input, 2)
        row_layout.addWidget(self.position_input, 2)
        row_layout.addWidget(self.start_date_input, 1)
        row_layout.addWidget(self.end_date_input, 1)
        row_layout.addWidget(self.years_input, 1)
        row_layout.addWidget(self.remove_btn)
    
    def get_data(self):
        return {
            'institution': self.institution_input.text().strip(),
            'position': self.position_input.text().strip(),
            'start_date': self.start_date_input.text().strip() or None,
            'end_date': self.end_date_input.text().strip() or None,
            'years_of_experience': self.years_input.text().strip() or None
        }


class ClassSectionRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Class Name (e.g., Grade 10)")
        self.section_input = QLineEdit()
        self.section_input.setPlaceholderText("Section (e.g., A)")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;")
        
        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.class_input, 2)
        row_layout.addWidget(self.section_input, 1)
        row_layout.addWidget(self.remove_btn)
    
    def get_data(self):
        return {
            'class_name': self.class_input.text().strip(),
            'section': self.section_input.text().strip() or None
        }


class AddTeacherWidget(QWidget):
    """
    A widget for adding a new teacher.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contact_rows = []
        self.subject_rows = []
        self.qualification_rows = []
        self.experience_rows = []
        self.class_section_rows = []
        self.setStyleSheet(open("assets/style.qss").read())
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Add New Teacher")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_content = QWidget()
        form_layout = QFormLayout(form_content)
        
        # --- Personal Info ---
        self.first_name = QLineEdit()
        self.middle_name = QLineEdit()
        self.last_name = QLineEdit()
        self.father_name = QLineEdit()
        self.dob = QLineEdit()
        self.dob.setPlaceholderText("YYYY-MM-DD")
        self.address = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])

        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Middle Name:", self.middle_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Father Name:", self.father_name)
        form_layout.addRow("Date of Birth:", self.dob)
        form_layout.addRow("Gender:", self.gender)
        form_layout.addRow("Address:", self.address)
        
        # --- Teacher Info ---
        self.joining_date = QLineEdit()
        self.joining_date.setText(datetime.now().strftime("%Y-%m-%d"))
        self.joining_date.setPlaceholderText("YYYY-MM-DD")
        self.salary = QLineEdit()
        self.salary.setPlaceholderText("e.g., 50000")
        self.rating = QComboBox()
        self.rating.addItems(["1", "2", "3", "4", "5"])
        self.rating.setCurrentIndex(2)  # Default to 3
        self.role_combo = QComboBox()
        self.role_combo.addItems(TEACHER_ROLES)
        self.security_deposit = QLineEdit()
        self.security_deposit.setText("0")
        self.security_deposit.setPlaceholderText("e.g., 10000")
        
        form_layout.addRow("Joining Date:", self.joining_date)
        form_layout.addRow("Salary:", self.salary)
        form_layout.addRow("Rating (1-5):", self.rating)
        form_layout.addRow("Role:", self.role_combo)
        form_layout.addRow("Security Deposit:", self.security_deposit)
        
        # --- Contact Info Setup ---
        self.contact_list_layout = QVBoxLayout()
        contact_frame = QFrame()
        contact_frame.setLayout(self.contact_list_layout)
        self.add_contact_btn = QPushButton("Add Contact")
        self.add_contact_btn.setObjectName("secondaryButton")
        
        form_layout.addRow(QLabel("Contacts:"))
        form_layout.addRow(contact_frame)
        form_layout.addRow("", self.add_contact_btn)
        
        # --- Subjects Setup ---
        self.subject_list_layout = QVBoxLayout()
        subject_frame = QFrame()
        subject_frame.setLayout(self.subject_list_layout)
        self.add_subject_btn = QPushButton("Add Subject")
        self.add_subject_btn.setObjectName("secondaryButton")
        
        form_layout.addRow(QLabel("Subjects:"))
        form_layout.addRow(subject_frame)
        form_layout.addRow("", self.add_subject_btn)
        
        # --- Qualifications Setup ---
        self.qualification_list_layout = QVBoxLayout()
        qualification_frame = QFrame()
        qualification_frame.setLayout(self.qualification_list_layout)
        self.add_qualification_btn = QPushButton("Add Qualification")
        self.add_qualification_btn.setObjectName("secondaryButton")
        
        form_layout.addRow(QLabel("Qualifications:"))
        form_layout.addRow(qualification_frame)
        form_layout.addRow("", self.add_qualification_btn)
        
        # --- Experience Setup ---
        self.experience_list_layout = QVBoxLayout()
        experience_frame = QFrame()
        experience_frame.setLayout(self.experience_list_layout)
        self.add_experience_btn = QPushButton("Add Experience")
        self.add_experience_btn.setObjectName("secondaryButton")
        
        form_layout.addRow(QLabel("Experience:"))
        form_layout.addRow(experience_frame)
        form_layout.addRow("", self.add_experience_btn)
        
        # --- Class Sections Setup ---
        self.class_section_list_layout = QVBoxLayout()
        class_section_frame = QFrame()
        class_section_frame.setLayout(self.class_section_list_layout)
        self.add_class_section_btn = QPushButton("Add Class/Section")
        self.add_class_section_btn.setObjectName("secondaryButton")
        
        form_layout.addRow(QLabel("Class/Section Assignments:"))
        form_layout.addRow(class_section_frame)
        form_layout.addRow("", self.add_class_section_btn)

        scroll_area.setWidget(form_content)
        layout.addWidget(scroll_area)
        
        # Submit button (create before add_contact_row so it exists when connecting)
        self.btn_submit = QPushButton("Add Teacher")
        self.btn_submit.setObjectName("primaryButton")
        layout.addWidget(self.btn_submit)
        
        self.setLayout(layout)
        
        # Add initial contact row after submit button is created
        self.add_contact_row()

        # --- Connections ---
        self.add_contact_btn.clicked.connect(self.add_contact_row)
        self.add_subject_btn.clicked.connect(self.add_subject_row)
        self.add_qualification_btn.clicked.connect(self.add_qualification_row)
        self.add_experience_btn.clicked.connect(self.add_experience_row)
        self.add_class_section_btn.clicked.connect(self.add_class_section_row)
        self.btn_submit.clicked.connect(self.handle_submit)
        self.init_enter_key_navigation()

    def add_contact_row(self):
        new_row = ContactRow()
        new_row.remove_btn.clicked.connect(lambda: self.remove_contact_row(new_row))
        
        if self.contact_rows:
            prev_input_field = self.contact_rows[-1].last_input()
        else:
            prev_input_field = self.security_deposit
            
        prev_input_field.returnPressed.connect(new_row.type_combo.setFocus)
        new_row.value_input.returnPressed.connect(self.btn_submit.click)
        
        self.contact_rows.append(new_row)
        self.contact_list_layout.addWidget(new_row)
        
        return new_row

    def remove_contact_row(self, row_to_remove):
        if len(self.contact_rows) <= 1:
            show_warning(self, "Error", "You must have at least one contact entry.")
            return

        idx = self.contact_rows.index(row_to_remove)
        
        prev_input_field = self.contact_rows[idx-1].last_input() if idx > 0 else self.security_deposit
        
        try:
            prev_input_field.returnPressed.disconnect()
        except TypeError:
            pass
        
        if idx < len(self.contact_rows) - 1:
             next_input_field = self.contact_rows[idx+1].type_combo
             prev_input_field.returnPressed.connect(next_input_field.setFocus)
        else:
            # If this was the last row, connect previous to submit
            prev_input_field.returnPressed.connect(self.btn_submit.click)

        self.contact_rows.remove(row_to_remove)
        row_to_remove.deleteLater()

    def add_subject_row(self):
        new_row = SubjectRow()
        new_row.remove_btn.clicked.connect(lambda: self.remove_subject_row(new_row))
        self.subject_rows.append(new_row)
        self.subject_list_layout.addWidget(new_row)
        return new_row

    def remove_subject_row(self, row_to_remove):
        self.subject_rows.remove(row_to_remove)
        row_to_remove.deleteLater()

    def add_qualification_row(self):
        new_row = QualificationRow()
        new_row.remove_btn.clicked.connect(lambda: self.remove_qualification_row(new_row))
        self.qualification_rows.append(new_row)
        self.qualification_list_layout.addWidget(new_row)
        return new_row

    def remove_qualification_row(self, row_to_remove):
        self.qualification_rows.remove(row_to_remove)
        row_to_remove.deleteLater()

    def add_experience_row(self):
        new_row = ExperienceRow()
        new_row.remove_btn.clicked.connect(lambda: self.remove_experience_row(new_row))
        self.experience_rows.append(new_row)
        self.experience_list_layout.addWidget(new_row)
        return new_row

    def remove_experience_row(self, row_to_remove):
        self.experience_rows.remove(row_to_remove)
        row_to_remove.deleteLater()

    def add_class_section_row(self):
        new_row = ClassSectionRow()
        new_row.remove_btn.clicked.connect(lambda: self.remove_class_section_row(new_row))
        self.class_section_rows.append(new_row)
        self.class_section_list_layout.addWidget(new_row)
        return new_row

    def remove_class_section_row(self, row_to_remove):
        self.class_section_rows.remove(row_to_remove)
        row_to_remove.deleteLater()

    def init_enter_key_navigation(self):
        self.first_name.returnPressed.connect(self.middle_name.setFocus)
        self.middle_name.returnPressed.connect(self.last_name.setFocus)
        self.last_name.returnPressed.connect(self.father_name.setFocus)
        self.father_name.returnPressed.connect(self.dob.setFocus)
        self.dob.returnPressed.connect(self.address.setFocus)
        self.address.returnPressed.connect(self.joining_date.setFocus)
        self.joining_date.returnPressed.connect(self.salary.setFocus)
        self.salary.returnPressed.connect(self.role_combo.setFocus)
        self.role_combo.activated.connect(lambda *_: self.security_deposit.setFocus())
        # Connect security_deposit to first contact row if it exists, otherwise to submit
        if self.contact_rows:
            self.security_deposit.returnPressed.connect(self.contact_rows[0].type_combo.setFocus)
        else:
            self.security_deposit.returnPressed.connect(self.btn_submit.click)

    def get_data(self):
        """
        Collects and validates form data.
        Returns (data_dict, contacts_list, is_valid: bool, subjects, qualifications, experiences, class_sections)
        """
        data = {
            'first_name': self.first_name.text().strip(),
            'middle_name': self.middle_name.text().strip() or None,
            'last_name': self.last_name.text().strip(),
            'father_name': self.father_name.text().strip(),
            'dob': self.dob.text().strip(),
            'address': self.address.text().strip(),
            'gender': self.gender.currentText(),
            'joining_date': self.joining_date.text().strip(),
            'salary': self.salary.text().strip(),
            'rating': self.rating.currentText(),
            'role': self.role_combo.currentText(),
            'security_deposit': self.security_deposit.text().strip() or "0"
        }
        
        # Validate required fields
        required = ['first_name', 'last_name', 'father_name', 
                   'dob', 'address', 'joining_date', 'salary']
        display_names = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'father_name': 'Father Name',
            'dob': 'Date of Birth',
            'address': 'Address',
            'joining_date': 'Joining Date',
            'salary': 'Salary'
        }
        
        is_valid, error_msg = validate_required_fields(data, required, display_names)
        if not is_valid:
            show_warning(self, "Validation Error", error_msg)
            return None, None, False, None, None, None, None
        
        # Validate dates
        is_valid, error_msg = validate_date_format(data['dob'])
        if not is_valid:
            show_warning(self, "Invalid Date", error_msg)
            return None, None, False, None, None, None, None
            
        is_valid, error_msg = validate_date_format(data['joining_date'])
        if not is_valid:
            show_warning(self, "Invalid Date", error_msg)
            return None, None, False, None, None, None, None
        
        # Validate salary
        is_valid, error_msg = validate_is_positive_non_zero_float(data['salary'])
        if not is_valid:
            show_warning(self, "Invalid Salary", error_msg)
            return None, None, False, None, None, None, None
        
        # Validate security deposit
        if data['security_deposit']:
            is_valid, error_msg = validate_is_float(data['security_deposit'])
            if not is_valid:
                show_warning(self, "Invalid Security Deposit", error_msg)
                return None, None, False, None, None, None, None
        else:
            data['security_deposit'] = "0"

        salary_value = float(data['salary'])
        security_value = float(data['security_deposit'])
        if security_value > salary_value:
            show_warning(
                self,
                "Validation Error",
                "Security deposit cannot be greater than the teacher's salary."
            )
            return None, None, False, None, None, None, None
        
        # Collect contacts
        contacts = []
        for row in self.contact_rows:
            contact_type = row.type_combo.currentText().lower()
            value = row.value_input.text().strip()
            
            if not value:
                continue
                
            # Validate phone length
            if contact_type == "phone":
                is_valid, error_msg = validate_phone_length(value)
                if not is_valid:
                    show_warning(self, "Invalid Phone", error_msg)
                    return None, None, False, None, None, None, None
            
            contacts.append({
                'type': contact_type,
                'value': value,
                'label': 'primary'  # Default label
            })
        
        if not contacts:
            show_warning(self, "Validation Error", "At least one contact is required.")
            return None, None, False, None, None, None, None
        
        # Check for at least one phone
        if not any(c['type'] == 'phone' for c in contacts):
            show_warning(self, "Validation Error", "At least one phone number must be provided.")
            return None, None, False
        
        # Collect subjects
        subjects = []
        for row in self.subject_rows:
            subject = row.get_subject()
            if subject:
                subjects.append(subject)
        
        # Collect qualifications
        qualifications = []
        for row in self.qualification_rows:
            qual_data = row.get_data()
            if qual_data.get('degree'):
                qualifications.append(qual_data)
        
        # Collect experiences
        experiences = []
        for row in self.experience_rows:
            exp_data = row.get_data()
            if exp_data.get('institution'):
                experiences.append(exp_data)
        
        # Collect class sections
        class_sections = []
        for row in self.class_section_rows:
            cs_data = row.get_data()
            if cs_data.get('class_name'):
                class_sections.append(cs_data)
        
        return data, contacts, True, subjects, qualifications, experiences, class_sections

    def handle_submit(self):
        """Handles the logic for adding a new teacher."""
        result = self.get_data()
        if result[2] is False:  # is_valid is False
            return
        
        data, contacts, is_valid, subjects, qualifications, experiences, class_sections = result
        
        try:
            # Call the backend operation
            success, status_msg, teacher_id = add_teacher(
                data['first_name'], data['middle_name'], data['last_name'],
                data['father_name'], data['dob'], 
                data['address'], data['gender'], contacts,
                data['joining_date'], data['salary'], data['rating'],
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
        self.first_name.clear()
        self.middle_name.clear()
        self.last_name.clear()
        self.father_name.clear()
        self.dob.clear()
        self.address.clear()
        self.gender.setCurrentIndex(0)
        self.joining_date.setText(datetime.now().strftime("%Y-%m-%d"))
        self.salary.clear()
        self.rating.setCurrentIndex(2)
        self.role_combo.setCurrentIndex(0)
        self.security_deposit.setText("0")
        
        # Clear contacts (keep one row)
        while len(self.contact_rows) > 1:
            self.remove_contact_row(self.contact_rows[-1])
        if self.contact_rows:
            self.contact_rows[0].value_input.clear()
        
        # Clear subjects
        while self.subject_rows:
            self.remove_subject_row(self.subject_rows[0])
        
        # Clear qualifications
        while self.qualification_rows:
            self.remove_qualification_row(self.qualification_rows[0])
        
        # Clear experiences
        while self.experience_rows:
            self.remove_experience_row(self.experience_rows[0])
        
        # Clear class sections
        while self.class_section_rows:
            self.remove_class_section_row(self.class_section_rows[0])

