# SMS/ui/payment_history_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTreeWidget, 
    QTreeWidgetItem, QAbstractItemView, QGroupBox, QFormLayout, QDialog,
    QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .student_search_dialog import StudentSearchDialog
# --- FIX: Update imports to Service Layer ---
from business.due_service import get_all_student_dues_with_summary, get_payments_for_due
# --- END FIX ---

class PaymentHistoryWidget(QWidget):
    """
    A widget to find a student and display their complete payment history
    grouped by due, with installments shown as children.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_student_id = None
        self.selected_student_name = None
        self.DUE_ID_ROLE = Qt.UserRole + 1 # Role to store the pending_due_id
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- 1. Student Selection Group ---
        student_group = QGroupBox("1. Select Student")
        student_layout = QFormLayout()
        
        self.student_id_label = QLabel("N/A")
        self.student_name_label = QLabel("N/A")
        self.search_student_btn = QPushButton("Search for Student")
        self.search_student_btn.setObjectName("secondaryButton")
        self.search_student_btn.clicked.connect(self.open_student_search)
        
        student_layout.addRow("Student ID:", self.student_id_label)
        student_layout.addRow("Student Name:", self.student_name_label)
        student_layout.addRow(self.search_student_btn)
        
        student_group.setLayout(student_layout)
        main_layout.addWidget(student_group)

        # --- 2. Payment History Group ---
        history_group = QGroupBox("2. Payment History")
        history_layout = QVBoxLayout()
        
        self.history_tree = QTreeWidget()
        # --- FIX: Column count is now 7 for the new Time column ---
        self.history_tree.setColumnCount(7)
        self.history_tree.setHeaderLabels([
            "Description", "Date Added", "Status", "Total Due", "Total Paid", "Remaining", "Details"
        ])
        self.history_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_tree.setAlternatingRowColors(True)
        self.history_tree.setRootIsDecorated(True) # Show expand arrows
        
        self.history_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # --- FIX: Set column 6 (the empty one) to stretch ---
        self.history_tree.header().setSectionResizeMode(6, QHeaderView.Stretch)
        
        history_layout.addWidget(self.history_tree)
        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group, 1) # Give tree more space
        
        self.history_tree.itemExpanded.connect(self.on_due_expand)
        
        history_group.setEnabled(False)

    def open_student_search(self):
        """Opens the search dialog and retrieves the selected student."""
        dialog = StudentSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            student_id, student_name = dialog.get_selected_student()
            if student_id:
                self.selected_student_id = student_id
                self.selected_student_name = student_name
                self.student_id_label.setText(str(student_id))
                self.student_name_label.setText(student_name)
                self.history_tree.parentWidget().setEnabled(True)
                self.load_dues_summary()

    def load_dues_summary(self):
        """Loads the summary of all dues for the selected student. (Calls Service)"""
        if not self.selected_student_id:
            return
            
        dues_summary = get_all_student_dues_with_summary(self.selected_student_id)
        self.history_tree.clear() # Clear tree
        
        if not dues_summary:
            item = QTreeWidgetItem(self.history_tree, ["This student has no due history."])
            item.setDisabled(True)
            return
            
        bold_font = QFont()
        bold_font.setBold(True)
        
        for due in dues_summary:
            due_item = QTreeWidgetItem(self.history_tree)
            due_item.setFont(0, bold_font)
            
            status = due['status'].title()
            if status != "Paid":
                status = "Uncompleted"
            
            due_item.setText(0, due['due_type'])
            due_item.setText(1, due['due_date'])
            due_item.setText(2, status)
            due_item.setText(3, f"{due['amount_due']:.2f}")
            due_item.setText(4, f"{due['total_paid']:.2f}")
            due_item.setText(5, f"{due['amount_remaining']:.2f}")
            
            due_item.setData(0, self.DUE_ID_ROLE, due['pending_due_id'])
            
            placeholder = QTreeWidgetItem(due_item, ["Loading installments..."])
            placeholder.setDisabled(True)

        # --- FIX: Resize all columns *except* the stretched column 6 ---
        for i in range(self.history_tree.columnCount() - 1):
            self.history_tree.resizeColumnToContents(i)

    def on_due_expand(self, item):
        """Lazy-loads the installments (payments) for a due. (Calls Service)"""
        if item.childCount() != 1 or item.child(0).text(0) != "Loading installments...":
            return # Already loaded
            
        item.takeChild(0) # Remove the placeholder
        
        pending_due_id = item.data(0, self.DUE_ID_ROLE)
        if not pending_due_id:
            return
            
        payments = get_payments_for_due(pending_due_id)
        
        if not payments:
            child = QTreeWidgetItem(item, ["  No individual payments found for this due."])
            child.setDisabled(True)
            return
            
        # Add headers for the installments
        header_font = QFont()
        header_font.setItalic(True)
        header = QTreeWidgetItem(item)
        
        # --- FIX: Adjust header for 7-column layout ---
        header.setText(0, "  Installment")
        header.setText(1, "Payment Date")
        header.setText(2, "Payment Time") # <-- NEW HEADER
        header.setText(3, "Amount Paid") 
        header.setText(4, "Payment Mode") 
        header.setText(5, "Received By")
        
        header.setFont(0, header_font)
        header.setFont(1, header_font)
        header.setFont(2, header_font)
        header.setFont(3, header_font)
        header.setFont(4, header_font)
        header.setFont(5, header_font)
        header.setDisabled(True)
        
        # Add each installment
        for i, payment in enumerate(payments):
            child = QTreeWidgetItem(item)
            
            # --- FIX: Split timestamp into date and time ---
            timestamp_str = payment['payment_timestamp']
            payment_date = "N/A"
            payment_time = "N/A"
            if timestamp_str:
                parts = timestamp_str.split(" ")
                if len(parts) == 2:
                    payment_date = parts[0]
                    payment_time = parts[1]
                else:
                    payment_date = parts[0] # Fallback
            
            # --- FIX: Populate new 7-column layout ---
            child.setText(0, f"  Installment {i + 1}")
            child.setText(1, payment_date)
            child.setText(2, payment_time) # <-- NEW DATA
            child.setText(3, f"{payment['amount_paid']:.2f}")
            child.setText(4, payment['payment_mode'])
            child.setText(5, payment['received_by_user'])