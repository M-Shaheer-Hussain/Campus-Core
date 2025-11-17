# SMS/ui/student_search_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox
)
from .search_student_widget import SearchStudentWidget # Import the widget

class StudentSearchDialog(QDialog):
    """
    A reusable dialog window that contains the SearchStudentWidget
    and returns a selected student.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search and Select Student")
        self.setMinimumSize(1000, 600) # Set a good default size
        self.selected_student_id = None
        self.selected_student_name = None

        main_layout = QVBoxLayout(self)
        
        # --- Search Widget ---
        # We pass enable_double_click=False so double-clicking doesn't
        # open *another* details window from here.
        self.search_widget = SearchStudentWidget(enable_double_click=False)
        main_layout.addWidget(self.search_widget)
        
        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        
        # Disable OK by default
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
        main_layout.addWidget(self.button_box)
        
        # --- Connections ---
        # Connect the search widget's selection signal to enable the OK button
        self.search_widget.results_tree.itemSelectionChanged.connect(self.on_selection_changed)
        # Also allow double-click to act as "OK"
        self.search_widget.results_tree.itemDoubleClicked.connect(self.on_accept)

    def on_selection_changed(self):
        """Enable the OK button if a student is selected."""
        student_id, student_name = self.search_widget.get_selected_student()
        if student_id:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            
    def on_accept(self):
        """Store the selected student and accept the dialog."""
        student_id, student_name = self.search_widget.get_selected_student()
        if student_id:
            self.selected_student_id = student_id
            self.selected_student_name = student_name
            self.accept() # Close the dialog with "Accepted" status

    def get_selected_student(self):
        """Public method for the parent window to retrieve the result."""
        return self.selected_student_id, self.selected_student_name