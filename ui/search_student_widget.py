# SMS/ui/search_student_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QMessageBox, QLabel,
    QHeaderView, QCheckBox 
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
# --- FIX: Update imports to Service Layer ---
from business.student_service import search_students
# --- END FIX ---
from ui.student_details_window import StudentDetailsWindow 

class SearchStudentWidget(QWidget):
    """
    A reusable widget for searching students.
    Double-clicking a student opens a separate details window.
    """
    def __init__(self, parent=None, enable_double_click=True):
        super().__init__(parent)
        self.STUDENT_ID_ROLE = Qt.UserRole + 1 
        self.STUDENT_DATA_ROLE = Qt.UserRole + 2
        
        self.details_window = None 
        self.enable_double_click = enable_double_click
        
        # --- FIX: Ensure checkbox attribute exists immediately ---
        self.checkbox_include_inactive = QCheckBox("Include Inactive (Left) Students")
        # --- END FIX ---
        
        self.init_ui()
        self.init_connections()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        search_control_layout = QHBoxLayout() # Container for search bar and checkbox
        
        # Search Input Group
        search_bar_layout = QHBoxLayout()
        self.search_label = QLabel("Search by Student ID, Family SSN (5 digits), or Name:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("e.g., '101' or '10001' or 'John Doe'")
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primaryButton")
        
        search_bar_layout.addWidget(self.search_label)
        search_bar_layout.addWidget(self.search_input, 1) 
        search_bar_layout.addWidget(self.search_btn)
        
        search_control_layout.addLayout(search_bar_layout, 1)
        
        # New Checkbox for Inactive Students (already declared in __init__)
        self.checkbox_include_inactive.setChecked(False) # Default to active only
        search_control_layout.addWidget(self.checkbox_include_inactive)
        
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(9)
        self.results_tree.setHeaderLabels([
            "Student ID", "Full Name", "Class", "Family Name", "Family SSN",
            "Father's Name", "Mother's Name", "Monthly Fee", "Annual Fund"
        ])
        
        self.results_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_tree.setRootIsDecorated(False) 
        
        main_layout.addLayout(search_control_layout) # Use the new combined layout
        main_layout.addWidget(self.results_tree)

    def init_connections(self):
        self.search_btn.clicked.connect(self.on_search)
        self.search_input.returnPressed.connect(self.on_search)
        # Connect checkbox state change to trigger new search
        self.checkbox_include_inactive.stateChanged.connect(self.on_search) 
        
        if self.enable_double_click:
            self.results_tree.itemDoubleClicked.connect(self.on_open_details_window) 

    def on_search(self):
        """(Calls Service Layer)"""
        search_term = self.search_input.text().strip()
        include_inactive = self.checkbox_include_inactive.isChecked() # Check the flag
        
        self.results_tree.clear() 
        
        if not search_term:
            return
            
        try:
            # Pass the flag to the service layer
            results = search_students(search_term, include_inactive=include_inactive) 
            self.populate_tree(results)
        except Exception as e:
            print(f"Search Error: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred during search:\n{e}")

    def populate_tree(self, results):
        if not results:
            return 

        for student_data in results:
            item = QTreeWidgetItem(self.results_tree)
            
            item.setText(0, str(student_data['student_id']))
            item.setText(1, student_data['full_name'])
            item.setText(2, student_data['class'])
            item.setText(3, student_data.get('family_name', 'N/A'))
            item.setText(4, student_data.get('family_SSN', 'N/A'))
            item.setText(5, student_data['father_name'])
            item.setText(6, student_data['mother_name'])
            item.setText(7, f"{student_data['monthly_fee']:.2f}")
            item.setText(8, f"{student_data['annual_fund']:.2f}")
            
            # Highlight inactive students if present
            if student_data.get('is_active') == 0:
                font = QFont()
                font.setStrikeOut(True)
                item.setText(1, f"{student_data['full_name']} (LEFT)")
                for i in range(self.results_tree.columnCount()):
                    item.setFont(i, font)

            item.setData(0, self.STUDENT_ID_ROLE, student_data['student_id'])
            item.setData(0, self.STUDENT_DATA_ROLE, student_data)
            
        for i in range(self.results_tree.columnCount()):
            self.results_tree.resizeColumnToContents(i)

    def on_open_details_window(self, item, column):
        """
        Passes the whole data dictionary to the details window.
        """
        student_data = item.data(0, self.STUDENT_DATA_ROLE)
        
        if not student_data:
            return
            
        self.details_window = StudentDetailsWindow(student_data=student_data)
        self.details_window.show()
        
    def get_selected_student(self):
        """
        A public method to get the currently selected student.
        """
        selected_items = self.results_tree.selectedItems()
        if not selected_items:
            return None, None
            
        item = selected_items[0]
        student_id = item.data(0, self.STUDENT_ID_ROLE)
        student_name = item.text(1)
        
        return student_id, student_name