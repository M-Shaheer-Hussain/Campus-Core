# SMS/ui/search_teacher_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QMessageBox, QLabel,
    QHeaderView, QDialog, QFormLayout, QDialogButtonBox, QSizePolicy,
    QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from business.teacher_service import search_teachers, get_teacher_details_by_id, update_teacher_security_deposit, get_teacher_security_funds
from common.utils import validate_is_positive_float, show_warning
from ui.teacher_details_window import TeacherDetailsWindow

class SecurityDepositDialog(QDialog):
    """Dialog for adding to a teacher's security deposit."""
    def __init__(self, parent=None, current_deposit=0, salary=0, teacher_name=""):
        super().__init__(parent)
        self.setWindowTitle(f"Add Security Deposit - {teacher_name}")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.current_deposit = float(current_deposit or 0)
        self.salary = float(salary or 0)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.current_label = QLabel(f"Current Security Deposit: {self.current_deposit:.2f}")
        form_layout.addRow("", self.current_label)

        salary_label = QLabel(f"Teacher Salary: {self.salary:.2f}")
        form_layout.addRow("", salary_label)

        remaining_capacity = max(self.salary - self.current_deposit, 0)
        self.remaining_label = QLabel(f"Maximum additional deposit: {remaining_capacity:.2f}")
        self.remaining_label.setStyleSheet("color: #2c3e50; font-weight: 600;")
        form_layout.addRow("", self.remaining_label)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter additional security deposit amount")
        form_layout.addRow("Additional Amount:", self.amount_input)

        helper = QLabel("Tip: Amount will be ADDED to the current deposit and cannot exceed the salary.")
        helper.setWordWrap(True)
        helper.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        form_layout.addRow("", helper)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.amount_input.setFocus()
        self.amount_input.returnPressed.connect(buttons.accepted.emit)
    
    def get_amount(self):
        """Returns the entered amount as float, or None if invalid."""
        text = self.amount_input.text().strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None


class SearchTeacherWidget(QWidget):
    """
    A widget for searching teachers and managing their security deposits.
    """
    def __init__(self, parent=None, enable_double_click=True):
        super().__init__(parent)
        self.TEACHER_ID_ROLE = Qt.UserRole + 1
        self.TEACHER_DATA_ROLE = Qt.UserRole + 2
        self.enable_double_click = enable_double_click
        self.details_window = None
        
        self.init_ui()
        self.init_connections()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Search Input Group
        search_controls_layout = QHBoxLayout()
        search_bar_layout = QHBoxLayout()
        self.search_label = QLabel("Search by Teacher ID or Name:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("e.g., '1' or 'John Doe'")
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primaryButton")
        
        search_bar_layout.addWidget(self.search_label)
        search_bar_layout.addWidget(self.search_input, 1)
        search_bar_layout.addWidget(self.search_btn)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Active Teachers", "Left Teachers", "All Teachers"])
        self.status_filter.setCurrentIndex(0)
        self.status_filter.setToolTip("Filter results by employment status")

        search_controls_layout.addLayout(search_bar_layout, 1)
        search_controls_layout.addWidget(self.status_filter)

        main_layout.addLayout(search_controls_layout)
        
        # Results Tree
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(9)
        self.results_tree.setHeaderLabels([
            "Teacher ID", "Full Name", "Role", "Joining Date", "Salary", 
            "Rating", "Security Deposit", "Status", "Actions"
        ])
        
        self.results_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_tree.setRootIsDecorated(False)
        
        # Set column widths
        header = self.results_tree.header()
        # Make the name column sized to contents and keep status/actions readable.
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(120)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.results_tree.setColumnWidth(8, 220)
        
        main_layout.addWidget(self.results_tree)
        
        # Info label
        info_label = QLabel("Double-click a teacher to view full details. Use 'Check Security Funds' to view security information or 'Update Security Deposit' to modify the amount.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        main_layout.addWidget(info_label)

    def init_connections(self):
        self.search_btn.clicked.connect(self.on_search)
        self.search_input.returnPressed.connect(self.on_search)
        self.status_filter.currentIndexChanged.connect(self.on_search)
        if self.enable_double_click:
            self.results_tree.itemDoubleClicked.connect(self.on_view_details)

    def on_search(self):
        """Searches for teachers."""
        search_term = self.search_input.text().strip()
        
        self.results_tree.clear()
        
        if not search_term:
            QMessageBox.warning(self, "Search Error", "Please enter a search term.")
            return
            
        try:
            results = search_teachers(search_term, status_filter=self.status_filter.currentText())
            self.populate_tree(results)
            
            if not results:
                QMessageBox.information(self, "No Results", "No teachers found matching your search.")
        except Exception as e:
            print(f"Search Error: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred during search:\n{e}")

    def populate_tree(self, results):
        """Populates the tree widget with search results."""
        if not results:
            return
        
        for teacher in results:
            item = QTreeWidgetItem(self.results_tree)
            # Ensure the row is tall enough to fully display the action buttons
            # (set size hint on the Actions column so the widget cell height
            # increases accordingly).
            item.setSizeHint(8, QSize(0, 40))
            item.setText(0, str(teacher.get('teacher_id', '')))
            item.setText(1, teacher.get('full_name', ''))
            item.setText(2, teacher.get('role', ''))
            item.setText(3, teacher.get('joining_date', '') or '')
            item.setText(4, f"{teacher.get('salary', 0):.2f}")
            item.setText(5, str(teacher.get('rating', '')))
            item.setText(6, f"{teacher.get('security_deposit', 0):.2f}")

            status_label = teacher.get('status_label') or ("Active" if teacher.get('is_active', 1) else "Left")
            if teacher.get('is_active', 1) == 0 and teacher.get('date_of_leaving'):
                status_label += f" (Left: {teacher.get('date_of_leaving')})"
            item.setText(7, status_label)
            
            # Store teacher_id in item data
            item.setData(0, self.TEACHER_ID_ROLE, teacher.get('teacher_id'))
            item.setData(0, self.TEACHER_DATA_ROLE, teacher)

            if teacher.get('is_active', 1) == 0:
                font = QFont(self.font())
                font.setStrikeOut(True)
                for col in range(self.results_tree.columnCount()):
                    item.setFont(col, font)
            
            # Add action buttons column
            button_container = QWidget()
            # Stack the buttons vertically so their labels remain readable even on
            # narrow window sizes.
            button_layout = QVBoxLayout(button_container)
            button_layout.setContentsMargins(4, 4, 4, 4)
            button_layout.setSpacing(6)
            button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Check Security button
            check_btn = QPushButton("Security Info")
            check_btn.setObjectName("secondaryButton")
            check_btn.setMinimumHeight(30)
            check_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            check_btn.setToolTip("View security deposit and elapsed time details")
            check_btn.clicked.connect(
                lambda checked, tid=teacher.get('teacher_id'),
                name=teacher.get('full_name', ''): self.on_check_security_funds(tid, name)
            )

            # Update Security button
            update_btn = QPushButton("Add Deposit")
            update_btn.setObjectName("secondaryButton")
            update_btn.setMinimumHeight(30)
            update_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            update_btn.setToolTip("Add to the existing security deposit")
            update_btn.clicked.connect(
                lambda checked, tid=teacher.get('teacher_id'),
                name=teacher.get('full_name', ''),
                current=teacher.get('security_deposit', 0),
                salary=teacher.get('salary', 0): self.on_update_security(tid, name, current, salary)
            )

            button_layout.addWidget(check_btn)
            button_layout.addWidget(update_btn)
            button_container.setMinimumWidth(150)
            
            self.results_tree.setItemWidget(item, 8, button_container)

    def get_selected_teacher(self):
        """Returns currently selected teacher id and name."""
        selected_items = self.results_tree.selectedItems()
        if not selected_items:
            return None, None
        item = selected_items[0]
        teacher_id = item.data(0, self.TEACHER_ID_ROLE)
        teacher_name = item.text(1)
        return teacher_id, teacher_name

    def on_view_details(self, item, column):
        """Opens the detailed teacher profile window."""
        teacher_id = item.data(0, self.TEACHER_ID_ROLE)
        if not teacher_id:
            return
        
        try:
            details = get_teacher_details_by_id(teacher_id)
            if not details:
                QMessageBox.warning(self, "Error", "Teacher details not found.")
                return
            self.details_window = TeacherDetailsWindow(details)
            self.details_window.show()
            self.details_window.raise_()
            self.details_window.activateWindow()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error retrieving teacher details:\n{e}")

    def on_check_security_funds(self, teacher_id, teacher_name):
        """Shows security funds information for the teacher."""
        try:
            security_info = get_teacher_security_funds(teacher_id)
            if not security_info:
                QMessageBox.warning(self, "Error", "Teacher security information not found.")
                return
            
            # Build message
            msg = f"""
<b>Security Funds Information</b><br><br>
<b>Teacher:</b> {teacher_name}<br>
<b>Teacher ID:</b> {teacher_id}<br><br>
<b>Joining Date:</b> {security_info.get('joining_date', 'N/A')}<br>
<b>Current Security Deposit:</b> {security_info.get('security_deposit', 0):.2f}<br><br>
<b>Time Elapsed:</b><br>
  • Days: {security_info.get('days_elapsed', 0)}<br>
  • Months: {security_info.get('months_elapsed', 0):.2f}<br>
  • Years: {security_info.get('years_elapsed', 0):.2f}<br>
"""
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Security Funds Check")
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(msg)
            msg_box.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error retrieving security funds:\n{e}")

    def on_update_security(self, teacher_id, teacher_name, current_deposit, salary):
        """Opens dialog to add to the security deposit."""
        current_deposit = float(current_deposit or 0)
        salary = float(salary or 0)

        if salary <= 0:
            QMessageBox.warning(self, "Salary Required", "Cannot add security deposit because salary information is missing.")
            return

        if current_deposit >= salary:
            QMessageBox.information(self, "Limit Reached", "Security deposit already equals the teacher's salary.")
            return

        dialog = SecurityDepositDialog(self, current_deposit, salary, teacher_name)
        
        if dialog.exec_() == QDialog.Accepted:
            new_amount = dialog.get_amount()
            
            if new_amount is None:
                show_warning(self, "Invalid Input", "Please enter a valid number for security deposit.")
                return
            if new_amount == 0:
                show_warning(self, "Invalid Input", "Additional amount must be greater than zero.")
                return
            
            # Validate the amount
            is_valid, error_msg = validate_is_positive_float(str(new_amount))
            if not is_valid:
                show_warning(self, "Validation Error", error_msg)
                return
            
            # Update security deposit
            success, message = update_teacher_security_deposit(teacher_id, new_amount)
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Refresh the search results
                self.on_search()
            else:
                QMessageBox.critical(self, "Error", f"Failed to update security deposit:\n{message}")

