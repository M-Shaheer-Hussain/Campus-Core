# SMS/ui/make_payment_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox,
    QFormLayout, QGroupBox, QComboBox, QDialog
)
from PyQt5.QtCore import Qt
from datetime import datetime
from .student_search_dialog import StudentSearchDialog
# --- FIX: Update imports to Service/Common layers ---
from business.due_service import get_unpaid_dues_for_student, make_payment
from common.utils import show_warning, validate_is_positive_float # <-- NEW IMPORT
# --- END FIX ---

from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QPainter, QFont, QColor

class MakePaymentWidget(QWidget):
    """
    A widget to find a student, view their unpaid dues, and make a payment.
    """
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.selected_student_id = None
        self.selected_student_name = None
        self.selected_pending_due_id = None
        self.selected_amount_remaining = 0.0
        self.received_by_user = username
        
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

        # --- 2. Unpaid Dues Group ---
        self.dues_group = QGroupBox("2. Select Due to Pay")
        dues_layout = QVBoxLayout()
        
        self.dues_table = QTableWidget()
        self.dues_table.setColumnCount(6)
        self.dues_table.setHorizontalHeaderLabels([
            "Due ID", "Due Type", "Amount Due", "Total Paid", "Amount Remaining", "Due Date"
        ])
        self.dues_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.dues_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dues_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dues_table.itemClicked.connect(self.on_due_selected)
        
        dues_layout.addWidget(self.dues_table)
        self.dues_group.setLayout(dues_layout)
        main_layout.addWidget(self.dues_group)

        # --- 3. Payment Form Group ---
        self.payment_group = QGroupBox("3. Enter Payment Details")
        payment_layout = QFormLayout()
        
        self.amount_to_pay_input = QLineEdit()
        self.amount_to_pay_input.setPlaceholderText("e.g., 5000.00")
        
        self.payment_mode_combo = QComboBox()
        self.payment_mode_combo.addItems(["Cash", "Credit Card", "Bank Transfer"])
        
        self.received_by_label = QLabel(self.received_by_user)
        self.received_by_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        self.submit_payment_btn = QPushButton("Submit Payment")
        self.submit_payment_btn.setObjectName("primaryButton")
        self.submit_payment_btn.clicked.connect(self.handle_submit_payment)
        
        payment_layout.addRow("Amount to Pay:", self.amount_to_pay_input)
        payment_layout.addRow("Payment Mode:", self.payment_mode_combo)
        payment_layout.addRow("Received By:", self.received_by_label) 
        payment_layout.addRow(self.submit_payment_btn)
        
        self.payment_group.setLayout(payment_layout)
        main_layout.addWidget(self.payment_group)
        
        main_layout.addStretch()
        
        # Initial state
        self.dues_group.setEnabled(False)
        self.payment_group.setEnabled(False)

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
                self.load_unpaid_dues()

    def load_unpaid_dues(self):
        """Loads the unpaid dues for the selected student into the table. (Calls Service)"""
        if not self.selected_student_id:
            return
            
        dues = get_unpaid_dues_for_student(self.selected_student_id)
        self.dues_table.setRowCount(0) # Clear table
        
        if not dues:
            self.dues_group.setEnabled(False)
            self.payment_group.setEnabled(False)
            show_warning(self, "No Dues", "This student has no pending dues.")
            return
            
        self.dues_group.setEnabled(True)
        self.payment_group.setEnabled(False) # Disable payment until a due is selected
        
        for row, due in enumerate(dues):
            self.dues_table.insertRow(row)
            self.dues_table.setItem(row, 0, QTableWidgetItem(str(due['pending_due_id'])))
            self.dues_table.setItem(row, 1, QTableWidgetItem(due['due_type']))
            self.dues_table.setItem(row, 2, QTableWidgetItem(f"{due['amount_due']:.2f}"))
            self.dues_table.setItem(row, 3, QTableWidgetItem(f"{due['total_paid']:.2f}"))
            self.dues_table.setItem(row, 4, QTableWidgetItem(f"{due['amount_remaining']:.2f}"))
            self.dues_table.setItem(row, 5, QTableWidgetItem(due['due_date']))
        
        self.dues_table.resizeColumnsToContents()

    def on_due_selected(self, item):
        """Fires when a due is clicked. Populates the payment form."""
        selected_row = self.dues_table.currentRow()
        if selected_row < 0:
            return

        self.selected_pending_due_id = int(self.dues_table.item(selected_row, 0).text())
        self.selected_amount_remaining = float(self.dues_table.item(selected_row, 4).text())
        
        self.amount_to_pay_input.setText(f"{self.selected_amount_remaining:.2f}")
        self.payment_group.setEnabled(True)

    def handle_submit_payment(self):
        """Validates and submits the payment. (Applies NO OVERPAYMENT Rule)"""
        amount_str = self.amount_to_pay_input.text().strip()
        payment_mode = self.payment_mode_combo.currentText()
        payment_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        due_type = self.dues_table.item(self.dues_table.currentRow(), 1).text()

        # --- Validation ---
        if not self.selected_pending_due_id:
            show_warning(self, "Error", "Please select a due from the table.")
            return

        # 1. Validate amount is a positive number (using new common utility)
        is_valid_float, float_msg = validate_is_positive_float(amount_str)
        if not is_valid_float:
            show_warning(self, "Error", f"Payment amount: {float_msg}")
            return

        try:
            amount_to_pay = float(amount_str)
            if amount_to_pay <= 0:
                show_warning(self, "Error", "Payment amount must be greater than zero.")
                return
            
            # --- BUSINESS RULE: NO OVERPAYMENT ALLOWED ---
            if amount_to_pay > self.selected_amount_remaining:
                show_warning(self, "Validation Error", 
                             f"Payment amount ({amount_to_pay:.2f}) cannot exceed the remaining due amount ({self.selected_amount_remaining:.2f}).")
                return

        except ValueError:
            # Should not happen if validate_is_positive_float is correct
            show_warning(self, "Error", "Payment amount must be a valid number.")
            return
            
        # --- Submit to Database (Calls Service Layer) ---
        success, message, new_payment_id = make_payment(
            self.selected_pending_due_id,
            amount_to_pay,
            payment_mode,
            payment_timestamp, 
            self.received_by_user
        )
        
        if success:
            QMessageBox.information(self, "Success", f"Payment of {amount_to_pay:.2f} recorded. New status: {message.title()}")
            
            receipt_details = {
                "receipt_id": new_payment_id,
                "student_name": self.student_name_label.text(),
                "student_id": self.student_id_label.text(),
                "payment_timestamp": payment_timestamp,
                "amount_paid": amount_to_pay,
                "payment_mode": payment_mode,
                "due_type": due_type,
                "amount_remaining": self.selected_amount_remaining - amount_to_pay,
                "received_by": self.received_by_user
            }
            self.prompt_to_print_receipt(receipt_details)
            
            # Refresh
            self.load_unpaid_dues()
            self.payment_group.setEnabled(False)
            self.amount_to_pay_input.clear()
            self.selected_pending_due_id = None
        else:
            QMessageBox.critical(self, "Payment Failed", f"The payment could not be recorded:\n{message}")

    def prompt_to_print_receipt(self, details):
        reply = QMessageBox.question(self, "Print Receipt",
            f"Payment successful. Do you want to print a receipt (ID: {details['receipt_id']})?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
        if reply == QMessageBox.Yes:
            self.print_receipt(details)

    def print_receipt(self, details):
        """
        Opens a QPrintDialog and prints a formatted receipt.
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
            
            painter.setFont(title_font)
            painter.drawText(1000, y_pos, "School Management System")
            y_pos += 300
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "OFFICIAL PAYMENT RECEIPT")
            y_pos += 200
            
            painter.setPen(QColor(Qt.black))
            painter.drawLine(1000, y_pos, 7000, y_pos)
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Receipt ID:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, str(details['receipt_id']))
            y_pos += 200

            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Payment Date/Time:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['payment_timestamp'])
            y_pos += 200

            painter.drawLine(1000, y_pos, 7000, y_pos)
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Student ID:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['student_id'])
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Student Name:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['student_name'])
            y_pos += 200
            
            painter.drawLine(1000, y_pos, 7000, y_pos)
            y_pos += 200

            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Payment For:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['due_type'])
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Payment Mode:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['payment_mode'])
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Received By:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, details['received_by'])
            y_pos += 200
            
            y_pos += 200 # Extra space
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Amount Paid:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, f"{details['amount_paid']:.2f}")
            y_pos += 200
            
            painter.setFont(header_font)
            painter.drawText(1000, y_pos, "Amount Remaining on this Due:")
            painter.setFont(body_font)
            painter.drawText(3000, y_pos, f"{details['amount_remaining']:.2f}")
            y_pos += 400
            
            painter.setFont(body_font)
            painter.drawText(1000, y_pos, "Thank you for your payment.")
            
            painter.end()
        else:
            show_warning(self, "Print Cancelled", "The receipt was not printed.")