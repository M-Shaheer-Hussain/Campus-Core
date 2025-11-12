# SMS/ui/student_details_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.student_operations import get_student_contacts
from core.due_operations import get_unpaid_dues_for_student

class StudentDetailsWindow(QWidget):
    """
    A separate window to show all details for a selected student
    using a master-detail (List/Table) layout.
    """
    def __init__(self, student_data, parent=None):
        super().__init__(parent)
        self.student_data = student_data
        self.student_id = self.student_data.get('student_id')
        self.student_name = self.student_data.get('full_name', 'N/A')
        
        self.ITEM_TYPE_ROLE = Qt.UserRole + 2
        self.TYPE_CONTACT_HEADER = 2
        self.TYPE_DUE_HEADER = 3
        
        # Window setup
        self.setWindowTitle(f"Details for {self.student_name} (ID: {self.student_id})")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(open("assets/style.qss").read())
        self.setObjectName("DetailsWindow")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel(f"Student Profile: {self.student_name}")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; padding: 15px; background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.category_tree = self.create_category_tree()
        content_layout.addWidget(self.category_tree)

        self.detail_stack = QStackedWidget()
        
        # --- Create a new summary page ---
        self.summary_page = self.create_summary_page()
        self.contact_page = self.create_contact_page()
        self.dues_page = self.create_dues_page()
        
        self.detail_stack.addWidget(self.summary_page) # Add summary page first
        self.detail_stack.addWidget(self.contact_page)
        self.detail_stack.addWidget(self.dues_page)
        
        content_layout.addWidget(self.detail_stack, 1)
        main_layout.addLayout(content_layout)

        self.category_tree.currentItemChanged.connect(self.on_category_changed)
        
        self.load_categories()

    def load_categories(self):
        """
        Loads the top-level headers.
        """
        self.category_tree.clear()
        bold_font = QFont()
        bold_font.setBold(True)
        
        summary_item = QTreeWidgetItem(self.category_tree, ["Student Summary"])
        summary_item.setFont(0, bold_font)

        contacts_node = QTreeWidgetItem(self.category_tree, ["Contact Info"])
        contacts_node.setFont(0, bold_font)
        
        dues_node = QTreeWidgetItem(self.category_tree, ["Pending Dues"])
        dues_node.setFont(0, bold_font)
        
        # Set the default selection to Summary
        self.category_tree.setCurrentItem(summary_item)

    def create_category_tree(self):
        """Creates the left-side category tree."""
        tree = QTreeWidget()
        tree.setObjectName("CategoryTree")
        tree.setFixedWidth(220)
        tree.setHeaderHidden(True)
        return tree

    # --- UPDATED: This is now the Summary Page ---
    def create_summary_page(self):
        """Creates the main student & family info summary page."""
        page_widget = QWidget()
        layout = QFormLayout(page_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Helper to create bold labels
        def create_bold_label(text):
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            return label
            
        def create_data_label(text):
            label = QLabel(str(text))
            label.setFont(QFont("Segoe UI", 11))
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            return label

        # Student Info
        layout.addRow(create_bold_label("Student ID:"), create_data_label(self.student_id))
        layout.addRow(create_bold_label("Full Name:"), create_data_label(self.student_name))
        layout.addRow(create_bold_label("Class:"), create_data_label(self.student_data.get('class', 'N/A')))
        
        # --- NEW: Family Info ---
        layout.addRow(create_bold_label("Family Name:"), create_data_label(self.student_data.get('family_name', 'N/A')))
        layout.addRow(create_bold_label("Family SSN:"), create_data_label(self.student_data.get('family_SSN', 'N/A')))
        
        # Other Info
        layout.addRow(create_bold_label("Father's Name:"), create_data_label(self.student_data.get('father_name', 'N/A')))
        layout.addRow(create_bold_label("Mother's Name:"), create_data_label(self.student_data.get('mother_name', 'N/A')))

        # Financial Info
        layout.addRow(create_bold_label("Monthly Fee:"), create_data_label(f"{self.student_data.get('monthly_fee', 0.0):.2f}"))
        layout.addRow(create_bold_label("Annual Fund:"), create_data_label(f"{self.student_data.get('annual_fund', 0.0):.2f}"))
        
        return page_widget

    def create_contact_page(self):
        """Creates the 'Contact Info' table page."""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Type", "Label", "Value"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        contacts = get_student_contacts(self.student_id)
        table.setRowCount(len(contacts))
        
        if not contacts:
             table.setRowCount(1)
             item = QTableWidgetItem("No contact info on file.")
             item.setTextAlignment(Qt.AlignCenter)
             table.setItem(0, 0, item)
             table.setSpan(0, 0, 1, 3)
        else:
            for row, contact in enumerate(contacts):
                contact_type = contact.get('type')
                contact_label = contact.get('label')
                contact_value = contact.get('value')
                display_type = (contact_type or "N/A").title()
                display_label = (contact_label or "N/A").title()
                display_value = contact_value or "N/A"
                table.setItem(row, 0, QTableWidgetItem(display_type))
                table.setItem(row, 1, QTableWidgetItem(display_label))
                table.setItem(row, 2, QTableWidgetItem(display_value))
        
        return table

    def create_dues_page(self):
        """Creates the 'Pending Dues' table page."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Due Type", "Amount Due", "Total Paid", "Amount Remaining", "Due Date", "Status"
        ])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        dues = get_unpaid_dues_for_student(self.student_id)
        table.setRowCount(len(dues))

        if not dues:
            table.setRowCount(1)
            item = QTableWidgetItem("No pending dues on file.")
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, 6)
        else:
            for row, due in enumerate(dues):
                due_type = due.get('due_type')
                amount = due.get('amount_due', 0.0)
                total_paid = due.get('total_paid', 0.0)
                amount_remaining = due.get('amount_remaining', 0.0)
                due_date = due.get('due_date')
                status = due.get('status')
                
                display_type = (due_type or "N/A").title()
                display_amount = f"{amount:.2f}"
                display_total_paid = f"{total_paid:.2f}"
                display_remaining = f"{amount_remaining:.2f}"
                display_date = due_date or "N/A"
                display_status = (status or "N/A").title()

                table.setItem(row, 0, QTableWidgetItem(display_type))
                table.setItem(row, 1, QTableWidgetItem(display_amount))
                table.setItem(row, 2, QTableWidgetItem(display_total_paid))
                table.setItem(row, 3, QTableWidgetItem(display_remaining))
                table.setItem(row, 4, QTableWidgetItem(display_date))
                table.setItem(row, 5, QTableWidgetItem(display_status))

        return table

    def on_category_changed(self, current_item, previous_item):
        """Switches the QStackedWidget page based on category selection."""
        if not current_item:
            self.detail_stack.setCurrentWidget(self.summary_page)
            return

        item_text = current_item.text(0)
        
        if item_text == "Contact Info":
            self.detail_stack.setCurrentWidget(self.contact_page)
        elif item_text == "Pending Dues":
            self.detail_stack.setCurrentWidget(self.dues_page)
        else: # Default to summary
            self.detail_stack.setCurrentWidget(self.summary_page)