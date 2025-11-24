from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt
from datetime import datetime

from ui.teacher_search_dialog import TeacherSearchDialog
from business.teacher_service import get_teacher_details_by_id, remove_teacher
from common.utils import show_warning, validate_date_format, validate_is_not_future_date


class RemoveTeacherWidget(QWidget):
    """
    Widget that allows admins to mark a teacher as left/inactive (similar to student removal flow).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_teacher_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        search_group = QGroupBox("1. Find Teacher to Mark as Left")
        search_layout = QFormLayout()

        self.teacher_id_label = QLabel("N/A")
        self.teacher_name_label = QLabel("N/A")
        self.teacher_role_label = QLabel("N/A")

        self.search_teacher_btn = QPushButton("Search for Teacher")
        self.search_teacher_btn.setObjectName("secondaryButton")
        self.search_teacher_btn.clicked.connect(self.open_teacher_search)

        search_layout.addRow("Teacher ID:", self.teacher_id_label)
        search_layout.addRow("Teacher Name:", self.teacher_name_label)
        search_layout.addRow("Role:", self.teacher_role_label)
        search_layout.addRow(self.search_teacher_btn)

        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        self.remove_group = QGroupBox("2. Leaving Details")
        remove_layout = QFormLayout()

        self.leaving_date_input = QLineEdit()
        self.leaving_date_input.setPlaceholderText("YYYY-MM-DD")
        self.leaving_date_input.setText(datetime.now().strftime("%Y-%m-%d"))

        self.btn_remove = QPushButton("Confirm (Mark as Left)")
        self.btn_remove.setObjectName("primaryButton")
        self.btn_remove.clicked.connect(self.handle_remove_teacher)

        remove_layout.addRow("Date of Leaving:", self.leaving_date_input)
        remove_layout.addRow(self.btn_remove)

        self.remove_group.setLayout(remove_layout)
        self.remove_group.setEnabled(False)
        main_layout.addWidget(self.remove_group)
        main_layout.addStretch()

        self.leaving_date_input.returnPressed.connect(self.btn_remove.click)

    def open_teacher_search(self):
        dialog = TeacherSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            teacher_id, teacher_name = dialog.get_selected_teacher()
            if teacher_id:
                details = get_teacher_details_by_id(teacher_id)
                if details and details.get('is_active') == 0:
                    left_on = details.get('date_of_leaving', 'N/A')
                    show_warning(self, "Already Left", f"Teacher ID {teacher_id} is already marked as left (Date: {left_on}).")
                    self.clear_selection()
                    return

                self.current_teacher_id = teacher_id
                self.teacher_id_label.setText(str(teacher_id))
                self.teacher_name_label.setText(teacher_name)
                self.teacher_role_label.setText(details.get('role', 'N/A') if details else "N/A")
                self.remove_group.setEnabled(True)
                self.leaving_date_input.setFocus()
            else:
                self.clear_selection()

    def handle_remove_teacher(self):
        if not self.current_teacher_id:
            show_warning(self, "Error", "Please select a teacher first.")
            return

        date_of_leaving = self.leaving_date_input.text().strip()

        is_valid_format, error_msg = validate_date_format(date_of_leaving)
        if not is_valid_format:
            show_warning(self, "Validation Error", error_msg)
            return

        is_valid_future, future_msg = validate_is_not_future_date(date_of_leaving)
        if not is_valid_future:
            show_warning(self, "Validation Error", future_msg)
            return

        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Mark teacher ID {self.current_teacher_id} as left on {date_of_leaving}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, message = remove_teacher(self.current_teacher_id, date_of_leaving)
            if success:
                QMessageBox.information(self, "Success", message)
                self.clear_selection()
            else:
                QMessageBox.critical(self, "Error", message)

    def clear_selection(self):
        self.current_teacher_id = None
        self.teacher_id_label.setText("N/A")
        self.teacher_name_label.setText("N/A")
        self.teacher_role_label.setText("N/A")
        self.remove_group.setEnabled(False)
        self.leaving_date_input.setText(datetime.now().strftime("%Y-%m-%d"))

