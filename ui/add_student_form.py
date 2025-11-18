# SMS/ui/add_student_form.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout,
    QComboBox, QMessageBox, QHBoxLayout, QScrollArea, QFrame, QSizePolicy,
    QRadioButton, QStackedWidget, QGroupBox, QDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
# --- FIX: Update imports to Service/Common layers ---
from business.student_service import get_next_family_ssn, get_or_create_family, check_family_ssn_exists # ADDED IMPORT
from common.utils import (
    show_warning, validate_required_fields, validate_date_format, 
    validate_phone_length, validate_is_float, validate_ssn,
    validate_is_not_future_date, validate_is_positive_non_zero_float
)
# --- END FIX ---
from .family_search_dialog import FamilySearchDialog
from datetime import datetime

class ContactRow(QWidget):
    def __init__(self, parent=None, prev_input=None):
        super().__init__(parent)
        self.prev_input = prev_input 
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Phone", "Email"])
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Value (e.g., 03XXYYYYYYY or email@example.com)")
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Label (e.g. Primary)")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setObjectName("secondaryButton")
        self.remove_btn.setStyleSheet("padding: 2px;") 

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.type_combo, 2)
        row_layout.addWidget(self.value_input, 5)
        row_layout.addWidget(self.label_input, 3)
        row_layout.addWidget(self.remove_btn, 1)

        self.type_combo.currentIndexChanged.connect(self.value_input.setFocus)
        self.value_input.returnPressed.connect(self.label_input.setFocus)

    def last_input(self):
        return self.label_input


class StudentFormWidget(QWidget):
    """
    A reusable form widget for student data (personal, family, academic, contact).
    Does not handle submission logic.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(open("assets/style.qss").read())
        self.contact_rows = []
        self.selected_family_id = None
        self.next_available_ssn = "20001"
        
        self.init_ui()
        self.load_initial_data()

    def load_initial_data(self):
        """Fetches data needed when the form loads, like the next SSN. (Calls Service)"""
        self.next_available_ssn = get_next_family_ssn()
        # MODIFIED: Set value on the new QLineEdit input field
        self.new_family_ssn_input.setText(self.next_available_ssn)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0) # Make it fill its container
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_content = QWidget()
        form_layout = QFormLayout(form_content)
        
        # --- Personal Info ---
        self.first_name = QLineEdit()
        self.middle_name = QLineEdit()
        self.last_name = QLineEdit()
        self.father_name = QLineEdit()
        self.mother_name = QLineEdit()
        self.dob = QLineEdit()
        self.dob.setPlaceholderText("YYYY-MM-DD")
        self.address = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])

        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Middle Name:", self.middle_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Father Name:", self.father_name)
        form_layout.addRow("Mother Name:", self.mother_name)
        form_layout.addRow("Date of Birth:", self.dob)
        form_layout.addRow("Gender:", self.gender)
        form_layout.addRow("Address:", self.address)
        
        # --- Family Info Selection ---
        family_group = QGroupBox("Family Information")
        family_layout = QVBoxLayout()
        
        self.radio_create_new = QRadioButton("Create New Family")
        self.radio_link_existing = QRadioButton("Link to Existing Family")
        self.radio_create_new.setChecked(True)
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_create_new)
        radio_layout.addWidget(self.radio_link_existing)
        family_layout.addLayout(radio_layout)

        self.family_stack = QStackedWidget()
        
        # Page 1: Create New Family
        new_family_widget = QWidget()
        new_family_layout = QFormLayout(new_family_widget)
        
        # MODIFIED: Changed QLabel to QLineEdit for manual SSN input
        self.new_family_ssn_input = QLineEdit() 
        self.new_family_ssn_input.setPlaceholderText("Enter a unique Family SSN (5 digits)")
        
        self.new_family_name_input = QLineEdit()
        self.new_family_name_input.setPlaceholderText("e.g., The Khan Family")
        
        # MODIFIED: Added new SSN input field
        new_family_layout.addRow("New Family SSN:", self.new_family_ssn_input) 
        new_family_layout.addRow("Family Name:", self.new_family_name_input)
        
        # Page 2: Link Existing Family
        link_family_widget = QWidget()
        link_family_layout = QVBoxLayout(link_family_widget)
        self.search_family_btn = QPushButton("Search for Family...")
        self.search_family_btn.setObjectName("secondaryButton")
        self.linked_family_label = QLabel("Selected Family: N/A")
        link_family_layout.addWidget(self.search_family_btn)
        link_family_layout.addWidget(self.linked_family_label)

        self.family_stack.addWidget(new_family_widget)
        self.family_stack.addWidget(link_family_widget)
        
        family_layout.addWidget(self.family_stack)
        family_group.setLayout(family_layout)
        form_layout.addRow(family_group)

        # --- Academic Info ---
        self.date_of_admission = QLineEdit()
        self.date_of_admission.setText(datetime.now().strftime("%Y-%m-%d")) 
        self.date_of_admission.setPlaceholderText("YYYY-MM-DD")
        self.monthly_fee = QLineEdit()
        self.annual_fund = QLineEdit()
        self.student_class = QLineEdit()
        form_layout.addRow("Date of Admission:", self.date_of_admission)
        form_layout.addRow("Monthly Fee:", self.monthly_fee)
        form_layout.addRow("Annual Fund:", self.annual_fund)
        form_layout.addRow("Class:", self.student_class)
        
        # --- Contact Info Setup ---
        self.contact_list_layout = QVBoxLayout()
        contact_frame = QFrame()
        contact_frame.setLayout(self.contact_list_layout)
        self.add_contact_btn = QPushButton("Add Contact")
        self.add_contact_btn.setObjectName("secondaryButton")
        
        form_layout.addRow(QLabel("Contacts:"))
        form_layout.addRow(contact_frame)
        form_layout.addRow("", self.add_contact_btn)

        self.add_contact_row()
        
        scroll_area.setWidget(form_content)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

        # --- Connections ---
        self.radio_create_new.toggled.connect(lambda: self.family_stack.setCurrentIndex(0))
        self.radio_link_existing.toggled.connect(lambda: self.family_stack.setCurrentIndex(1))
        self.search_family_btn.clicked.connect(self.open_family_search)
        self.init_enter_key_navigation()

    def add_contact_row(self):
        new_row = ContactRow()
        new_row.remove_btn.clicked.connect(lambda: self.remove_contact_row(new_row))
        
        # Chain from the last available input
        if self.contact_rows:
            prev_input_field = self.contact_rows[-1].last_input()
        else:
            prev_input_field = self.student_class
            
        prev_input_field.returnPressed.connect(new_row.type_combo.setFocus)
        
        self.contact_rows.append(new_row)
        self.contact_list_layout.addWidget(new_row)
        
        # The new row's last input is now the end of the chain
        return new_row

    def remove_contact_row(self, row_to_remove):
        if len(self.contact_rows) <= 1:
            show_warning(self, "Error", "You must have at least one contact entry.")
            return

        idx = self.contact_rows.index(row_to_remove)
        
        prev_input_field = self.contact_rows[idx-1].last_input() if idx > 0 else self.student_class
        
        # Disconnect the old connection
        try:
            prev_input_field.returnPressed.disconnect()
        except TypeError:
            pass # No connection existed
        
        # Re-chain to the next row (if it exists) or do nothing
        if idx < len(self.contact_rows) - 1:
             next_input_field = self.contact_rows[idx+1].type_combo
             prev_input_field.returnPressed.connect(next_input_field.setFocus)

        self.contact_rows.remove(row_to_remove)
        row_to_remove.deleteLater()
        
    def init_enter_key_navigation(self):
        self.first_name.returnPressed.connect(self.middle_name.setFocus)
        self.middle_name.returnPressed.connect(self.last_name.setFocus)
        self.last_name.returnPressed.connect(self.father_name.setFocus)
        self.father_name.returnPressed.connect(self.mother_name.setFocus)
        self.mother_name.returnPressed.connect(self.dob.setFocus)
        self.dob.returnPressed.connect(self.address.setFocus)
        self.address.returnPressed.connect(self.gender.setFocus)
        
        # MODIFIED: Chain from gender to the NEW SSN input
        self.gender.activated.connect(self.new_family_ssn_input.setFocus)
        
        # MODIFIED: Chain from NEW SSN input to the Family Name input
        self.new_family_ssn_input.returnPressed.connect(self.new_family_name_input.setFocus)
        
        # MODIFIED: Chain from Family Name input to Admission Date input
        self.new_family_name_input.returnPressed.connect(self.date_of_admission.setFocus)
        
        self.date_of_admission.returnPressed.connect(self.monthly_fee.setFocus)
        self.monthly_fee.returnPressed.connect(self.annual_fund.setFocus)
        self.annual_fund.returnPressed.connect(self.student_class.setFocus)

    def open_family_search(self):
        """Opens the family search dialog and saves the result."""
        dialog = FamilySearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            fam_id, fam_ssn, fam_name = dialog.get_selected_family()
            if fam_id:
                self.selected_family_id = fam_id
                self.linked_family_label.setText(f"Selected: {fam_name} ({fam_ssn})")
                self.linked_family_label.setStyleSheet("color: green; font-weight: bold;")
        
    def get_data(self):
        """
        Validates all fields and returns the data for submission.
        (MODIFIED: Logic reordered to defer family creation until all validation passes)
        """
        data = {
            "first_name": self.first_name.text().strip(),
            "middle_name": self.middle_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "father_name": self.father_name.text().strip(),
            "mother_name": self.mother_name.text().strip(),
            "dob": self.dob.text().strip(),
            "gender": self.gender.currentText(),
            "address": self.address.text().strip(),
            "date_of_admission": self.date_of_admission.text().strip(),
            "monthly_fee": self.monthly_fee.text().strip(),
            "annual_fund": self.annual_fund.text().strip(),
            "student_class": self.student_class.text().strip(),
        }

        required_fields = [
            "first_name", "last_name", "father_name", "mother_name", "dob",
            "gender", "address", "date_of_admission", 
            "monthly_fee", "annual_fund", "student_class"
        ]
        
        # --- 1. Basic Validation (Required Fields) ---
        is_valid, error_message = validate_required_fields(data, required_fields)
        if not is_valid:
            show_warning(self, "Validation Error", error_message)
            return None, None, None, False

        # --- 2. Date and Fee Validations (All client-side checks MUST pass) ---
        
        # 2.1. Validate DOB format
        is_valid_dob, dob_msg = validate_date_format(data['dob'])
        if not is_valid_dob:
            show_warning(self, "Invalid Date", f"Date of Birth: {dob_msg}")
            return None, None, None, False
        
        # 2.2. Validate Admission Date format and rule: MUST NOT BE FUTURE
        is_valid_adm_format, adm_format_msg = validate_date_format(data['date_of_admission'])
        if not is_valid_adm_format:
            show_warning(self, "Invalid Date", f"Date of Admission: {adm_format_msg}")
            return None, None, None, False

        is_valid_adm_future, adm_future_msg = validate_is_not_future_date(data['date_of_admission'])
        if not is_valid_adm_future:
            show_warning(self, "Invalid Date", f"Date of Admission: {adm_future_msg}")
            return None, None, None, False

        # 2.3. Validate Minimum Monthly Fee (> 0)
        is_valid_mon, mon_msg = validate_is_positive_non_zero_float(data['monthly_fee'])
        if not is_valid_mon:
            show_warning(self, "Invalid Fee", f"Monthly Fee: {mon_msg}")
            return None, None, None, False
            
        # 2.4. Validate Annual Fund (Can be 0, so use original is_float)
        is_valid_ann, ann_msg = validate_is_float(data['annual_fund'])
        if not is_valid_ann:
            show_warning(self, "Invalid Fund", f"Annual Fund: {ann_msg}")
            return None, None, None, False
            
        # --- 3. Contact Validation (MUST pass) ---
        contacts = []
        has_phone = False
        if not self.contact_rows:
            show_warning(self, "Validation Error", "At least one contact entry is required.")
            return None, None, None, False
            
        for i, row in enumerate(self.contact_rows):
            contact_type = row.type_combo.currentText()
            value = row.value_input.text().strip()
            label = row.label_input.text().strip()
            if not value:
                 show_warning(self, "Validation Error", f"Contact {i+1} value cannot be empty.")
                 return None, None, None, False
            if contact_type == "Phone":
                has_phone = True
                is_valid, phone_msg = validate_phone_length(value)
                if not is_valid:
                    show_warning(self, "Validation Error", f"Contact {i+1} (Phone): {phone_msg}")
                    return None, None, None, False
            contacts.append({"type": contact_type, "value": value, "label": label if label else "primary"})
        
        if not has_phone:
            show_warning(self, "Validation Error", "At least one contact must be a phone number.")
            return None, None, None, False


        # --- 4. Family ID/Creation Logic (NOW SAFE: Runs only after all validation passes) ---
        final_family_id = None
        if self.radio_create_new.isChecked():
            new_ssn = self.new_family_ssn_input.text().strip() 
            new_name = self.new_family_name_input.text().strip()
            
            # 4.1. Validate New SSN Format (5 digits)
            is_valid_ssn, ssn_msg = validate_ssn(new_ssn, required_length=5) 
            if not is_valid_ssn:
                show_warning(self, "Validation Error", f"Family SSN: {ssn_msg}")
                return None, None, None, False
                
            # 4.2. Validate Family Name
            if not new_name:
                show_warning(self, "Validation Error", "A Family Name is required to create a new family.")
                return None, None, None, False
                
            # 4.3. CHECK FOR UNIQUENESS (BUSINESS RULE: MUST BE UNIQUE FOR NEW FAMILY)
            if check_family_ssn_exists(new_ssn):
                 show_warning(self, "Validation Error", f"The Family SSN '{new_ssn}' is already allocated. Please choose the 'Link to Existing Family' option or enter a unique SSN.")
                 return None, None, None, False
            
            # 4.4. Call Service to Create Family (DB WRITE HAPPENS HERE)
            final_family_id = get_or_create_family(new_ssn, new_name)
            
        else: # Link to existing
            if not self.selected_family_id:
                show_warning(self, "Validation Error", "Please use the 'Search' button to select a family.")
                return None, None, None, False
            final_family_id = self.selected_family_id
            
        if not final_family_id:
            show_warning(self, "Family Error", "Could not create or link the family record.")
            return None, None, None, False

        # --- 5. Return Data for Student Creation ---
        return data, contacts, final_family_id, True

    def populate_data(self, student_data):
        # FIX: The missing 'clear_fields' definition was here. 
        # The corrected method body relies on 'clear_fields' being defined below.
        self.clear_fields()
        
        self.first_name.setText(student_data.get('first_name', ''))
        self.middle_name.setText(student_data.get('middle_name', ''))
        self.last_name.setText(student_data.get('last_name', ''))
        self.father_name.setText(student_data.get('fathername', ''))
        self.mother_name.setText(student_data.get('mothername', ''))
        self.dob.setText(student_data.get('dob', ''))
        self.address.setText(student_data.get('address', ''))
        self.gender.setCurrentText(student_data.get('gender', 'Male'))
        
        if student_data.get('family_id'):
            self.radio_link_existing.setChecked(True)
            self.selected_family_id = student_data['family_id']
            fam_name = student_data.get('family_name', 'N/A')
            fam_ssn = student_data.get('family_SSN', 'N/A')
            self.linked_family_label.setText(f"Selected: {fam_name} ({fam_ssn})")
            self.linked_family_label.setStyleSheet("color: green; font-weight: bold;")
        
        self.date_of_admission.setText(student_data.get('date_of_admission', ''))
        self.monthly_fee.setText(str(student_data.get('monthly_fee', '0.0')))
        self.annual_fund.setText(str(student_data.get('annual_fund', '0.0')))
        self.student_class.setText(student_data.get('class', ''))

        for row in list(self.contact_rows):
            row.deleteLater()
        self.contact_rows.clear()
        
        contacts = student_data.get('contacts', [])
        if not contacts:
            self.add_contact_row()
        else:
            for contact in contacts:
                new_row = self.add_contact_row()
                new_row.type_combo.setCurrentText(contact.get('type', 'phone'))
                new_row.value_input.setText(contact.get('value', ''))
                new_row.label_input.setText(contact.get('label', ''))

    def clear_fields(self):
        for field in [self.first_name, self.middle_name, self.last_name, self.father_name,
                      self.mother_name, self.dob, self.address, 
                      self.monthly_fee, self.annual_fund, self.student_class,
                      self.new_family_name_input]: 
            field.clear()
            
        # MODIFIED: Clear the SSN input field
        self.new_family_ssn_input.clear()
            
        self.date_of_admission.setText(datetime.now().strftime("%Y-%m-%d"))
        self.gender.setCurrentIndex(0)
        
        self.radio_create_new.setChecked(True)
        self.load_initial_data() # This re-fetches the next SSN and sets it on the input
        self.linked_family_label.setText("Selected Family: N/A")
        self.linked_family_label.setStyleSheet("")
        self.selected_family_id = None
        
        for row in list(self.contact_rows):
            row.deleteLater()
        self.contact_rows.clear()
        
        try:
            # Important: Disconnect the chain before calling add_contact_row, 
            # otherwise the chain might be corrupted if the old connection was the last item.
            self.student_class.returnPressed.disconnect()
        except TypeError:
            pass 
            
        self.add_contact_row()