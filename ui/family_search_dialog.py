# SMS/ui/family_search_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
# --- FIX: Update imports to Service Layer ---
from business.student_service import search_families
# --- END FIX ---

class FamilySearchDialog(QDialog):
    """
    A reusable dialog to search for and select an existing family.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search and Select Family")
        self.setMinimumSize(700, 500)
        
        self.selected_family_id = None
        self.selected_family_ssn = None
        self.selected_family_name = None

        main_layout = QVBoxLayout(self)
        
        # --- Search Bar ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Family SSN or Family Name...")
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primaryButton")
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_btn)
        
        # --- Results Table ---
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Family ID", "Family SSN", "Family Name"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.results_table)
        main_layout.addWidget(self.button_box)
        
        # --- Connections ---
        self.search_btn.clicked.connect(self.on_search)
        self.search_input.returnPressed.connect(self.on_search)
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.results_table.itemDoubleClicked.connect(self.on_accept)

    def on_search(self):
        """Performs the search and populates the table. (Calls Service)"""
        search_term = self.search_input.text().strip()
        if not search_term:
            return
            
        results = search_families(search_term)
        self.results_table.setRowCount(0)
        
        for row, family in enumerate(results):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(str(family['id'])))
            self.results_table.setItem(row, 1, QTableWidgetItem(family['family_SSN']))
            self.results_table.setItem(row, 2, QTableWidgetItem(family['family_name']))

    def on_selection_changed(self):
        """Enables the OK button when a family is selected."""
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(len(self.results_table.selectedItems()) > 0)

    def on_accept(self):
        """Stores the selected family data and accepts the dialog."""
        selected_row = self.results_table.currentRow()
        if selected_row < 0:
            return
            
        self.selected_family_id = int(self.results_table.item(selected_row, 0).text())
        self.selected_family_ssn = self.results_table.item(selected_row, 1).text()
        self.selected_family_name = self.results_table.item(selected_row, 2).text()
        self.accept()

    def get_selected_family(self):
        """Public method to retrieve the result."""
        return self.selected_family_id, self.selected_family_ssn, self.selected_family_name