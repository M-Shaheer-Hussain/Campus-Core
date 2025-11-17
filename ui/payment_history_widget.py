# SMS/ui/payment_history_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTreeWidget, 
    QTreeWidgetItem, QAbstractItemView, QGroupBox, QFormLayout, QDialog,
    QHeaderView, QMessageBox # Added QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QColor # Added QPainter, QColor
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter # Added QPrintDialog, QPrinter
from .student_search_dialog import StudentSearchDialog
# --- FIX: Update imports to Service Layer ---
from business.due_service import get_all_student_dues_with_summary, get_payments_for_due
# --- END FIX ---
from common.utils import show_warning # Added show_warning
from datetime import datetime # Added datetime for slip generation timestamp

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
        
        # New: Print Button
        self.btn_print_slip = QPushButton("Generate Payment Slip/Challan")
        self.btn_print_slip.setObjectName("secondaryButton")
        self.btn_print_slip.clicked.connect(self.prompt_to_print_slip)
        
        history_layout.addWidget(self.history_tree)
        history_layout.addWidget(self.btn_print_slip) # Add the button
        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group, 1) # Give tree more space
        
        self.history_tree.itemExpanded.connect(self.on_due_expand)
        self.history_tree.itemSelectionChanged.connect(self.on_due_selection_changed) # New selection signal
        
        history_group.setEnabled(False)
        self.btn_print_slip.setEnabled(False) # Disable by default

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

    def on_due_selection_changed(self):
        """Enables the print button only if a top-level due item is selected."""
        selected_items = self.history_tree.selectedItems()
        if not selected_items:
            self.btn_print_slip.setEnabled(False)
            return
            
        item = selected_items[0]
        # Only enable if a top-level item (due) is selected (i.e., it has the DUE_ID_ROLE and no parent)
        due_id = item.data(0, self.DUE_ID_ROLE)
        
        if due_id and item.parent() is None:
             self.btn_print_slip.setEnabled(True)
        else:
             self.btn_print_slip.setEnabled(False)

    def prompt_to_print_slip(self):
        selected_items = self.history_tree.selectedItems()
        if not selected_items:
            show_warning(self, "No Selection", "Please select a Due from the history list.")
            return

        item = selected_items[0]
        
        # Retrieve necessary data from the selected item's text fields
        due_id = item.data(0, self.DUE_ID_ROLE)
        due_type = item.text(0)
        amount_due = item.text(3)
        amount_remaining = item.text(5)
        due_date = item.text(1)
        
        # We need the student info
        student_id = self.selected_student_id
        student_name = self.selected_student_name
        
        if not due_id:
            show_warning(self, "Error", "Could not retrieve due ID for the selected item.")
            return
            
        slip_details = {
            "due_id": due_id,
            "student_name": student_name,
            "student_id": student_id,
            "date_generated": datetime.now().strftime("%Y-%m-%d"),
            "due_type": due_type,
            "amount_due": amount_due,
            "amount_remaining": amount_remaining,
            "due_date": due_date
        }

        reply = QMessageBox.question(self, "Print Slip/Challan",
            f"Do you want to print a payment slip/challan for '{due_type}' (ID: {due_id})?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
        if reply == QMessageBox.Yes:
            self.print_slip(slip_details)
            
    def print_slip(self, details):
        """
        Opens a QPrintDialog and prints a formatted payment slip/challan.
        """
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec_() == QDialog.Accepted:
            painter = QPainter()
            painter.begin(printer)
            
            title_font = QFont("Arial", 14, QFont.Bold)
            header_font = QFont("Arial", 10, QFont.Bold)
            body_font = QFont("Arial", 10)
            
            y_pos = 1000 
            
            # Title
            painter.setFont(title_font)
            painter.drawText(1000, y_pos, "School Management System")
            y_pos += 300
            
            painter.setFont(title_font)
            painter.drawText(1000, y_pos, "OFFICIAL PAYMENT SLIP / CHALLAN")
            y_pos += 200
            
            painter.setPen(QColor(Qt.black))
            painter.drawLine(1000, y_pos, 7000, y_pos)
            y_pos += 200
            
            # Due ID and Date Generated
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Due ID:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, str(details['due_id']))
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Date Generated:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['date_generated'])
            y_pos += 200
            
            painter.drawLine(1000, y_pos, 7000, y_pos)
            y_pos += 200
            
            # Student Info
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Student ID:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, str(details['student_id']))
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Student Name:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['student_name'])
            y_pos += 200
            
            painter.drawLine(1000, y_pos, 7000, y_pos)
            y_pos += 300 

            # Payment Details
            painter.setFont(title_font)
            painter.drawText(1000, y_pos, "AMOUNT DUE")
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Due Type:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['due_type'])
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Due Date:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['due_date'])
            y_pos += 300
            
            # Key Amounts
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Total Amount Payable:")
            painter.setFont(title_font) 
            painter.drawText(4000, y_pos, f"Rs. {details['amount_due']}")
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Amount Remaining:")
            painter.setFont(title_font)
            painter.drawText(4000, y_pos, f"Rs. {details['amount_remaining']}")
            y_pos += 400
            
            painter.setFont(body_font)
            painter.drawText(1000, y_pos, "Please pay the remaining amount by the due date.")
            
            painter.end()
        else:
            show_warning(self, "Print Cancelled", "The slip was not printed.")