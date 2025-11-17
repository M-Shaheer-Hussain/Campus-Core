# SMS/ui/update_student_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QGroupBox, QLabel,
    QDialog, QFormLayout # Added QDialog, QFormLayout
)
from .add_student_form import StudentFormWidget
# REMOVED: from .search_student_widget import SearchStudentWidget
from .student_search_dialog import StudentSearchDialog # Added StudentSearchDialog
# --- FIX: Update imports to Service/Common layers ---
from business.student_service import get_student_details_by_id, update_student
from common.utils import show_warning
# --- END FIX ---

class UpdateStudentWidget(QWidget):
    """
    A widget for updating an existing student.
    Contains Search, the reusable StudentFormWidget, and Update logic.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_student_id = None
        self.current_person_id = None
        
        main_layout = QVBoxLayout(self)
        
        # --- 1. Search Group (Modified to use dialog) ---
        search_group = QGroupBox("1. Find Student to Update")
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
        
        # --- 2. Form Group ---
        self.form_group = QGroupBox("2. Update Student Details")
        form_layout = QVBoxLayout()
        self.form_widget = StudentFormWidget()
        self.btn_update = QPushButton("Save Changes")
        self.btn_update.setObjectName("primaryButton")
        self.btn_update.clicked.connect(self.handle_submit_update)
        
        form_layout.addWidget(self.form_widget)
        form_layout.addWidget(self.btn_update)
        self.form_group.setLayout(form_layout)
        
        # Add to main layout
        main_layout.addWidget(search_group)
        main_layout.addWidget(self.form_group)
        
        # Start with form disabled
        self.form_group.setEnabled(False)

    # REMOVED: on_student_selected method and logic related to self.search_widget.
    
    def open_student_search(self):
        """Opens the student search dialog and retrieves the selected student."""
        dialog = StudentSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            student_id, student_name = dialog.get_selected_student()
            if student_id:
                self.student_id_label.setText(str(student_id))
                self.student_name_label.setText(student_name)
                self.load_student_for_update(student_id)

    def load_student_for_update(self, student_id):
        """Fetches and loads student data into the form."""
        
        # Clear previous connection if it exists (for robustness)
        try:
            self.form_widget.contact_rows[-1].last_input().returnPressed.disconnect()
            self.form_widget.add_contact_btn.clicked.disconnect()
        except (AttributeError, IndexError, TypeError):
             pass 

        try:
            # Fetch all details for this student
            student_data = get_student_details_by_id(student_id)
            if not student_data:
                show_warning(self, "Error", "Could not fetch student details.")
                self.form_group.setEnabled(False)
                self.current_student_id = None
                self.current_person_id = None
                return
                
            # Populate the form with this data
            self.form_widget.populate_data(student_data)
            
            # Store IDs needed for the update
            self.current_student_id = student_data['student_id']
            self.current_person_id = student_data['person_id']
            
            # Enable the form and reset connections
            self.form_group.setEnabled(True)
            self.form_widget.contact_rows[-1].last_input().returnPressed.connect(self.btn_update.click)
            self.form_widget.add_contact_btn.clicked.connect(self.on_add_contact_row)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load student data: {e}")
            self.form_group.setEnabled(False)
            self.current_student_id = None
            self.current_person_id = None

    def on_add_contact_row(self):
        """When a new contact row is added, chain its 'Enter' to the update button."""
        new_row = self.form_widget.add_contact_row()
        new_row.last_input().returnPressed.connect(self.btn_update.click)

    def handle_submit_update(self):
        """
        Handles the logic for *updating* an existing student. (Calls Service Layer)
        """
        if not self.current_student_id or not self.current_person_id:
            show_warning(self, "Error", "No student selected.")
            return

        # 1. Get validated data from the form
        data, contacts, family_id, is_valid = self.form_widget.get_data()
        
        if not is_valid:
            return # Validation failed
            
        # 2. Call the backend update operation
        success, message = update_student(
            student_id=self.current_student_id,
            person_id=self.current_person_id,
            data=data,
            contacts=contacts,
            family_id=family_id
        )
        
        if success:
            QMessageBox.information(self, "Success", "Student record updated successfully.")
            # Clear and disable everything
            self.form_widget.clear_fields()
            self.form_group.setEnabled(False)
            # Cannot clear selection as search_widget is gone, but we can clear the labels
            self.student_id_label.setText("N/A")
            self.student_name_label.setText("N/A")
            self.current_student_id = None
            self.current_person_id = None
        else:
            QMessageBox.critical(self, "Error", f"Failed to update student:\n{message}")