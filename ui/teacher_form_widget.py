from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QScrollArea,
    QFrame,
    QPushButton,
    QFormLayout,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt

from business.teacher_service import TEACHER_ROLES
from common.utils import (
    show_warning,
    validate_required_fields,
    validate_date_format,
    validate_phone_length,
    validate_is_float,
    validate_is_positive_non_zero_float,
)


class _BaseRow(QWidget):
    """Utility base class that exposes helper methods for dynamic rows."""

    def clear(self):
        """Clear the row inputs if implemented by subclasses."""
        pass


class ContactRow(_BaseRow):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.type_combo, 2)
        layout.addWidget(self.value_input, 5)
        layout.addWidget(self.remove_btn, 1)

    def last_input(self):
        return self.value_input

    def clear(self):
        self.value_input.clear()
        self.type_combo.setCurrentIndex(0)


class SubjectRow(_BaseRow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Subject Name (e.g., Mathematics)")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.subject_input, 1)
        layout.addWidget(self.remove_btn)

    def get_subject(self):
        return self.subject_input.text().strip()

    def clear(self):
        self.subject_input.clear()


class QualificationRow(_BaseRow):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.degree_input, 2)
        layout.addWidget(self.institution_input, 3)
        layout.addWidget(self.year_input, 1)
        layout.addWidget(self.remove_btn)

    def get_data(self):
        return {
            "degree": self.degree_input.text().strip(),
            "institution": self.institution_input.text().strip(),
            "year": self.year_input.text().strip() or None,
        }

    def clear(self):
        self.degree_input.clear()
        self.institution_input.clear()
        self.year_input.clear()


class ExperienceRow(_BaseRow):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.institution_input, 2)
        layout.addWidget(self.position_input, 2)
        layout.addWidget(self.start_date_input, 1)
        layout.addWidget(self.end_date_input, 1)
        layout.addWidget(self.years_input, 1)
        layout.addWidget(self.remove_btn)

    def get_data(self):
        return {
            "institution": self.institution_input.text().strip(),
            "position": self.position_input.text().strip(),
            "start_date": self.start_date_input.text().strip() or None,
            "end_date": self.end_date_input.text().strip() or None,
            "years_of_experience": self.years_input.text().strip() or None,
        }

    def clear(self):
        self.institution_input.clear()
        self.position_input.clear()
        self.start_date_input.clear()
        self.end_date_input.clear()
        self.years_input.clear()


class ClassSectionRow(_BaseRow):
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

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.class_input, 2)
        layout.addWidget(self.section_input, 1)
        layout.addWidget(self.remove_btn)

    def get_data(self):
        return {
            "class_name": self.class_input.text().strip(),
            "section": self.section_input.text().strip() or None,
        }

    def clear(self):
        self.class_input.clear()
        self.section_input.clear()


class TeacherFormWidget(QWidget):
    """
    Reusable form widget shared by both Add and Update teacher flows.
    Exposes helper methods to collect, clear, and populate data.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.contact_rows = []
        self.subject_rows = []
        self.qualification_rows = []
        self.experience_rows = []
        self.class_section_rows = []

        self._init_form()

    def _init_form(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_content = QWidget()
        self.form_layout = QFormLayout(form_content)

        # Personal Info
        self.first_name = QLineEdit()
        self.middle_name = QLineEdit()
        self.last_name = QLineEdit()
        self.father_name = QLineEdit()
        self.dob = QLineEdit()
        self.dob.setPlaceholderText("YYYY-MM-DD")
        self.address = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])

        self.form_layout.addRow("First Name:", self.first_name)
        self.form_layout.addRow("Middle Name:", self.middle_name)
        self.form_layout.addRow("Last Name:", self.last_name)
        self.form_layout.addRow("Father Name:", self.father_name)
        self.form_layout.addRow("Date of Birth:", self.dob)
        self.form_layout.addRow("Gender:", self.gender)
        self.form_layout.addRow("Address:", self.address)

        # Teacher Info
        self.joining_date = QLineEdit()
        self.joining_date.setPlaceholderText("YYYY-MM-DD")
        self.salary = QLineEdit()
        self.salary.setPlaceholderText("e.g., 50000")
        self.rating = QComboBox()
        self.rating.addItems(["1", "2", "3", "4", "5"])
        self.role_combo = QComboBox()
        self.role_combo.addItems(TEACHER_ROLES)
        self.security_deposit = QLineEdit()
        self.security_deposit.setPlaceholderText("e.g., 10000")

        self.form_layout.addRow("Joining Date:", self.joining_date)
        self.form_layout.addRow("Salary:", self.salary)
        self.form_layout.addRow("Rating (1-5):", self.rating)
        self.form_layout.addRow("Role:", self.role_combo)
        self.form_layout.addRow("Security Deposit:", self.security_deposit)

        # Contacts
        self.contact_list_layout = QVBoxLayout()
        contact_frame = QFrame()
        contact_frame.setLayout(self.contact_list_layout)
        self.add_contact_btn = QPushButton("Add Contact")
        self.add_contact_btn.setObjectName("secondaryButton")
        self.add_contact_btn.clicked.connect(self.add_contact_row)

        self.form_layout.addRow(QLabel("Contacts:"))
        self.form_layout.addRow(contact_frame)
        self.form_layout.addRow("", self.add_contact_btn)

        # Subjects
        self.subject_list_layout = QVBoxLayout()
        subject_frame = QFrame()
        subject_frame.setLayout(self.subject_list_layout)
        self.add_subject_btn = QPushButton("Add Subject")
        self.add_subject_btn.setObjectName("secondaryButton")
        self.add_subject_btn.clicked.connect(self.add_subject_row)

        self.form_layout.addRow(QLabel("Subjects:"))
        self.form_layout.addRow(subject_frame)
        self.form_layout.addRow("", self.add_subject_btn)

        # Qualifications
        self.qualification_list_layout = QVBoxLayout()
        qualification_frame = QFrame()
        qualification_frame.setLayout(self.qualification_list_layout)
        self.add_qualification_btn = QPushButton("Add Qualification")
        self.add_qualification_btn.setObjectName("secondaryButton")
        self.add_qualification_btn.clicked.connect(self.add_qualification_row)

        self.form_layout.addRow(QLabel("Qualifications:"))
        self.form_layout.addRow(qualification_frame)
        self.form_layout.addRow("", self.add_qualification_btn)

        # Experience
        self.experience_list_layout = QVBoxLayout()
        experience_frame = QFrame()
        experience_frame.setLayout(self.experience_list_layout)
        self.add_experience_btn = QPushButton("Add Experience")
        self.add_experience_btn.setObjectName("secondaryButton")
        self.add_experience_btn.clicked.connect(self.add_experience_row)

        self.form_layout.addRow(QLabel("Experience:"))
        self.form_layout.addRow(experience_frame)
        self.form_layout.addRow("", self.add_experience_btn)

        # Class Sections
        self.class_section_list_layout = QVBoxLayout()
        class_section_frame = QFrame()
        class_section_frame.setLayout(self.class_section_list_layout)
        self.add_class_section_btn = QPushButton("Add Class/Section")
        self.add_class_section_btn.setObjectName("secondaryButton")
        self.add_class_section_btn.clicked.connect(self.add_class_section_row)

        self.form_layout.addRow(QLabel("Class/Section Assignments:"))
        self.form_layout.addRow(class_section_frame)
        self.form_layout.addRow("", self.add_class_section_btn)

        scroll_area.setWidget(form_content)
        layout.addWidget(scroll_area)

        self._set_defaults()

    def _set_defaults(self):
        self.joining_date.setText(datetime.now().strftime("%Y-%m-%d"))
        self.rating.setCurrentIndex(2)
        self.security_deposit.setText("0")
        self._ensure_minimum_contact_row()

    # --- Dynamic row helpers -------------------------------------------------
    def _ensure_minimum_contact_row(self):
        if not self.contact_rows:
            self.add_contact_row()

    def add_contact_row(self):
        row = ContactRow()
        row.remove_btn.clicked.connect(lambda: self.remove_contact_row(row))
        self.contact_rows.append(row)
        self.contact_list_layout.addWidget(row)
        return row

    def remove_contact_row(self, row):
        if len(self.contact_rows) <= 1:
            show_warning(self, "Error", "You must have at least one contact entry.")
            return
        self.contact_rows.remove(row)
        row.deleteLater()

    def add_subject_row(self):
        row = SubjectRow()
        row.remove_btn.clicked.connect(lambda: self.remove_subject_row(row))
        self.subject_rows.append(row)
        self.subject_list_layout.addWidget(row)
        return row

    def remove_subject_row(self, row):
        self.subject_rows.remove(row)
        row.deleteLater()

    def add_qualification_row(self):
        row = QualificationRow()
        row.remove_btn.clicked.connect(lambda: self.remove_qualification_row(row))
        self.qualification_rows.append(row)
        self.qualification_list_layout.addWidget(row)
        return row

    def remove_qualification_row(self, row):
        self.qualification_rows.remove(row)
        row.deleteLater()

    def add_experience_row(self):
        row = ExperienceRow()
        row.remove_btn.clicked.connect(lambda: self.remove_experience_row(row))
        self.experience_rows.append(row)
        self.experience_list_layout.addWidget(row)
        return row

    def remove_experience_row(self, row):
        self.experience_rows.remove(row)
        row.deleteLater()

    def add_class_section_row(self):
        row = ClassSectionRow()
        row.remove_btn.clicked.connect(lambda: self.remove_class_section_row(row))
        self.class_section_rows.append(row)
        self.class_section_list_layout.addWidget(row)
        return row

    def remove_class_section_row(self, row):
        self.class_section_rows.remove(row)
        row.deleteLater()

    # --- Data helpers --------------------------------------------------------
    def get_form_data(self):
        """
        Collects and validates form data.
        Returns (data_dict, contacts_list, is_valid, subjects, qualifications, experiences, class_sections)
        """
        data = {
            "first_name": self.first_name.text().strip(),
            "middle_name": self.middle_name.text().strip() or None,
            "last_name": self.last_name.text().strip(),
            "father_name": self.father_name.text().strip(),
            "dob": self.dob.text().strip(),
            "address": self.address.text().strip(),
            "gender": self.gender.currentText(),
            "joining_date": self.joining_date.text().strip(),
            "salary": self.salary.text().strip(),
            "rating": self.rating.currentText(),
            "role": self.role_combo.currentText(),
            "security_deposit": self.security_deposit.text().strip() or "0",
        }

        required = [
            "first_name",
            "last_name",
            "father_name",
            "dob",
            "address",
            "joining_date",
            "salary",
        ]
        display_names = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "father_name": "Father Name",
            "dob": "Date of Birth",
            "address": "Address",
            "joining_date": "Joining Date",
            "salary": "Salary",
        }

        is_valid, error_msg = validate_required_fields(data, required, display_names)
        if not is_valid:
            show_warning(self, "Validation Error", error_msg)
            return None, None, False, None, None, None, None

        is_valid, error_msg = validate_date_format(data["dob"])
        if not is_valid:
            show_warning(self, "Invalid Date", error_msg)
            return None, None, False, None, None, None, None

        is_valid, error_msg = validate_date_format(data["joining_date"])
        if not is_valid:
            show_warning(self, "Invalid Date", error_msg)
            return None, None, False, None, None, None, None

        is_valid, error_msg = validate_is_positive_non_zero_float(data["salary"])
        if not is_valid:
            show_warning(self, "Invalid Salary", error_msg)
            return None, None, False, None, None, None, None

        if data["security_deposit"]:
            is_valid, error_msg = validate_is_float(data["security_deposit"])
            if not is_valid:
                show_warning(self, "Invalid Security Deposit", error_msg)
                return None, None, False, None, None, None, None
        else:
            data["security_deposit"] = "0"

        salary_value = float(data["salary"])
        security_value = float(data["security_deposit"])
        if security_value > salary_value:
            show_warning(
                self,
                "Validation Error",
                "Security deposit cannot be greater than the teacher's salary.",
            )
            return None, None, False, None, None, None, None

        # Contacts
        contacts = []
        for row in self.contact_rows:
            contact_type = row.type_combo.currentText().lower()
            value = row.value_input.text().strip()
            if not value:
                continue
            if contact_type == "phone":
                is_valid, error_msg = validate_phone_length(value)
                if not is_valid:
                    show_warning(self, "Invalid Phone", error_msg)
                    return None, None, False, None, None, None, None
            contacts.append(
                {
                    "type": contact_type,
                    "value": value,
                    "label": "primary",
                }
            )

        if not contacts:
            show_warning(self, "Validation Error", "At least one contact is required.")
            return None, None, False, None, None, None, None

        if not any(c["type"] == "phone" for c in contacts):
            show_warning(self, "Validation Error", "At least one phone number must be provided.")
            return None, None, False, None, None, None, None

        subjects = [row.get_subject() for row in self.subject_rows if row.get_subject()]
        qualifications = []
        for row in self.qualification_rows:
            data_q = row.get_data()
            if data_q.get("degree"):
                qualifications.append(data_q)

        experiences = []
        for row in self.experience_rows:
            data_e = row.get_data()
            if data_e.get("institution"):
                experiences.append(data_e)

        class_sections = []
        for row in self.class_section_rows:
            data_cs = row.get_data()
            if data_cs.get("class_name"):
                class_sections.append(data_cs)

        return data, contacts, True, subjects, qualifications, experiences, class_sections

    def clear_fields(self):
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

        self._clear_row_list(self.subject_rows, self.subject_list_layout)
        self._clear_row_list(self.qualification_rows, self.qualification_list_layout)
        self._clear_row_list(self.experience_rows, self.experience_list_layout)
        self._clear_row_list(self.class_section_rows, self.class_section_list_layout)
        self._clear_row_list(self.contact_rows, self.contact_list_layout, keep_one=True)

    def _clear_row_list(self, rows, layout, keep_one=False):
        while rows:
            row = rows.pop()
            layout.removeWidget(row)
            row.deleteLater()
        if keep_one:
            self.add_contact_row()

    def populate_data(self, teacher_data):
        """
        Populate the form with existing teacher data for editing.
        """
        self.first_name.setText(str(teacher_data.get("first_name", "") or ""))
        self.middle_name.setText(str(teacher_data.get("middle_name") or ""))
        self.last_name.setText(str(teacher_data.get("last_name", "") or ""))
        self.father_name.setText(str(teacher_data.get("fathername", "") or ""))
        self.dob.setText(str(teacher_data.get("dob", "") or ""))
        self.address.setText(str(teacher_data.get("address", "") or ""))

        gender_value = (teacher_data.get("gender") or "Male").title()
        gender_index = self.gender.findText(gender_value, Qt.MatchFixedString)
        if gender_index != -1:
            self.gender.setCurrentIndex(gender_index)

        self.joining_date.setText(str(teacher_data.get("joining_date", "") or ""))
        salary = teacher_data.get("salary")
        self.salary.setText(str(salary) if salary is not None else "")
        rating = str(teacher_data.get("rating", "3"))
        rating_index = self.rating.findText(rating, Qt.MatchFixedString)
        if rating_index != -1:
            self.rating.setCurrentIndex(rating_index)
        role = teacher_data.get("role") or TEACHER_ROLES[-1]
        role_index = self.role_combo.findText(role, Qt.MatchFixedString)
        if role_index != -1:
            self.role_combo.setCurrentIndex(role_index)
        security = teacher_data.get("security_deposit")
        self.security_deposit.setText(str(security or 0))

        self._populate_contacts(teacher_data.get("contacts", []))
        self._populate_subjects(teacher_data.get("subjects", []))
        self._populate_qualifications(teacher_data.get("qualifications", []))
        self._populate_experiences(teacher_data.get("experiences", []))
        self._populate_class_sections(teacher_data.get("class_sections", []))

    def _populate_contacts(self, contacts):
        self._clear_row_list(self.contact_rows, self.contact_list_layout, keep_one=False)
        if not contacts:
            self.add_contact_row()
            return

        for contact in contacts:
            row = self.add_contact_row()
            contact_type = (contact.get("type") or "phone").title()
            index = row.type_combo.findText(contact_type, Qt.MatchFixedString)
            if index != -1:
                row.type_combo.setCurrentIndex(index)
            row.value_input.setText(str(contact.get("value", "") or ""))

    def _populate_subjects(self, subjects):
        self._clear_row_list(self.subject_rows, self.subject_list_layout)
        for subject in subjects:
            row = self.add_subject_row()
            row.subject_input.setText(str(subject or ""))

    def _populate_qualifications(self, qualifications):
        self._clear_row_list(self.qualification_rows, self.qualification_list_layout)
        for qualification in qualifications:
            row = self.add_qualification_row()
            row.degree_input.setText(str(qualification.get("degree", "") or ""))
            row.institution_input.setText(str(qualification.get("institution", "") or ""))
            row.year_input.setText(str(qualification.get("year") or ""))

    def _populate_experiences(self, experiences):
        self._clear_row_list(self.experience_rows, self.experience_list_layout)
        for experience in experiences:
            row = self.add_experience_row()
            row.institution_input.setText(str(experience.get("institution", "") or ""))
            row.position_input.setText(str(experience.get("position", "") or ""))
            row.start_date_input.setText(str(experience.get("start_date", "") or ""))
            row.end_date_input.setText(str(experience.get("end_date", "") or ""))
            row.years_input.setText(str(experience.get("years_of_experience") or ""))

    def _populate_class_sections(self, class_sections):
        self._clear_row_list(self.class_section_rows, self.class_section_list_layout)
        for class_section in class_sections:
            row = self.add_class_section_row()
            row.class_input.setText(str(class_section.get("class_name", "") or ""))
            row.section_input.setText(str(class_section.get("section", "") or ""))

