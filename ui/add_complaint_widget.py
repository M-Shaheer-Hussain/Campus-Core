# SMS/ui/add_complaint_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
from business.complaint_service import add_complaint
from business.teacher_service import search_teachers
from ui.teacher_search_dialog import TeacherSearchDialog
from common.utils import show_warning


class AddComplaintWidget(QWidget):
    """
    Widget for adding complaints against teachers.
    """
    
    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.username = username or "Admin"
        self.selected_teacher_id = None
        self.selected_teacher_name = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Register Complaint Against Teacher")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Search Group
        search_group = QGroupBox("1. Select Teacher")
        search_layout = QFormLayout()
        
        self.teacher_id_label = QLabel("N/A")
        self.teacher_name_label = QLabel("N/A")
        
        self.search_teacher_btn = QPushButton("Search for Teacher")
        self.search_teacher_btn.setObjectName("secondaryButton")
        self.search_teacher_btn.clicked.connect(self.open_teacher_search)
        
        search_layout.addRow("Teacher ID:", self.teacher_id_label)
        search_layout.addRow("Teacher Name:", self.teacher_name_label)
        search_layout.addRow(self.search_teacher_btn)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Complaint Form Group
        self.complaint_group = QGroupBox("2. Complaint Details")
        complaint_layout = QFormLayout()
        
        self.complaint_date = QLineEdit()
        self.complaint_date.setText(datetime.now().strftime("%Y-%m-%d"))
        self.complaint_date.setPlaceholderText("YYYY-MM-DD")
        
        self.complaint_text = QTextEdit()
        self.complaint_text.setPlaceholderText("Enter complaint details...")
        self.complaint_text.setMinimumHeight(150)
        
        complaint_layout.addRow("Complaint Date:", self.complaint_date)
        complaint_layout.addRow("Complaint Details:", self.complaint_text)
        
        self.submit_btn = QPushButton("Register Complaint")
        self.submit_btn.setObjectName("primaryButton")
        self.submit_btn.clicked.connect(self.handle_submit)
        
        complaint_layout.addRow(self.submit_btn)
        self.complaint_group.setLayout(complaint_layout)
        self.complaint_group.setEnabled(False)
        
        layout.addWidget(self.complaint_group)
        layout.addStretch()
    
    def open_teacher_search(self):
        """Opens teacher search dialog."""
        dialog = TeacherSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            teacher_id, teacher_name = dialog.get_selected_teacher()
            if teacher_id:
                self.selected_teacher_id = teacher_id
                self.selected_teacher_name = teacher_name
                self.teacher_id_label.setText(str(teacher_id))
                self.teacher_name_label.setText(teacher_name or "N/A")
                self.complaint_group.setEnabled(True)
    
    def handle_submit(self):
        """Handles complaint submission."""
        if not self.selected_teacher_id:
            show_warning(self, "Error", "Please select a teacher first.")
            return
        
        complaint_text = self.complaint_text.toPlainText().strip()
        if not complaint_text:
            show_warning(self, "Error", "Please enter complaint details.")
            return
        
        complaint_date = self.complaint_date.text().strip()
        if not complaint_date:
            show_warning(self, "Error", "Please enter complaint date.")
            return
        
        success, message = add_complaint(
            self.selected_teacher_id,
            complaint_text,
            complaint_date,
            self.username
        )
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.reset_form()
        else:
            QMessageBox.critical(self, "Error", f"Failed to register complaint:\n{message}")
    
    def reset_form(self):
        """Resets the form after successful submission."""
        self.selected_teacher_id = None
        self.selected_teacher_name = None
        self.teacher_id_label.setText("N/A")
        self.teacher_name_label.setText("N/A")
        self.complaint_date.setText(datetime.now().strftime("%Y-%m-%d"))
        self.complaint_text.clear()
        self.complaint_group.setEnabled(False)

