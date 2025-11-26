# SMS/ui/complaint_status_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from business.complaint_service import get_complaints_by_teacher
from business.teacher_service import search_teachers


class ComplaintStatusWidget(QWidget):
    """
    Widget for admin to view all complaints against teachers.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_all_complaints()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Complaint Status")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Filter by Teacher:")
        self.teacher_filter = QComboBox()
        self.teacher_filter.addItem("All Teachers")
        self.teacher_filter.currentIndexChanged.connect(self.on_filter_changed)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self.load_all_complaints)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.teacher_filter, 1)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Complaint ID", "Teacher ID", "Teacher Name", 
            "Complaint Date", "Complaint Details", "Registered By"
        ])
        
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        # Style header
        header_font = QFont()
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)
        
        # Make complaint details column wider
        self.table.setColumnWidth(4, 400)
        
        layout.addWidget(self.table)
        
        # Info label
        info_label = QLabel("View all registered complaints against teachers. Use the filter to view complaints for a specific teacher.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)
    
    def load_all_complaints(self):
        """Loads all complaints from all teachers."""
        try:
            # Block signals to prevent recursion when updating filter
            self.teacher_filter.blockSignals(True)
            
            # Get all active teachers for filter dropdown
            teachers = search_teachers("", status_filter="All Teachers")
            self.teacher_filter.clear()
            self.teacher_filter.addItem("All Teachers")
            for teacher in teachers:
                teacher_name = teacher.get('full_name', '')
                teacher_id = teacher.get('teacher_id', '')
                self.teacher_filter.addItem(f"{teacher_name} (ID: {teacher_id})", teacher_id)
            
            # Set to "All Teachers" and unblock signals
            self.teacher_filter.setCurrentIndex(0)
            self.teacher_filter.blockSignals(False)
            
            # Load all complaints
            all_complaints = []
            for teacher in teachers:
                teacher_id = teacher.get('teacher_id')
                complaints = get_complaints_by_teacher(teacher_id)
                for complaint in complaints:
                    complaint['teacher_id'] = teacher_id
                    complaint['teacher_name'] = teacher.get('full_name', 'N/A')
                    all_complaints.append(complaint)
            
            # Sort by complaint date (newest first)
            all_complaints.sort(key=lambda x: x.get('complaint_date', ''), reverse=True)
            
            self.display_complaints(all_complaints)
            
        except Exception as e:
            # Unblock signals even on error
            self.teacher_filter.blockSignals(False)
            QMessageBox.critical(self, "Error", f"Failed to load complaints:\n{e}")
    
    def on_filter_changed(self):
        """Filters complaints by selected teacher."""
        selected_index = self.teacher_filter.currentIndex()
        if selected_index == 0:  # "All Teachers"
            self.load_all_complaints()
        else:
            teacher_id = self.teacher_filter.itemData(selected_index)
            if teacher_id:
                try:
                    complaints = get_complaints_by_teacher(teacher_id)
                    # Get teacher name
                    teachers = search_teachers("", status_filter="All Teachers")
                    teacher_name = "N/A"
                    for teacher in teachers:
                        if teacher.get('teacher_id') == teacher_id:
                            teacher_name = teacher.get('full_name', 'N/A')
                            break
                    
                    for complaint in complaints:
                        complaint['teacher_id'] = teacher_id
                        complaint['teacher_name'] = teacher_name
                    
                    self.display_complaints(complaints)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load complaints:\n{e}")
    
    def display_complaints(self, complaints):
        """Displays complaints in the table."""
        self.table.setRowCount(len(complaints))
        
        for row, complaint in enumerate(complaints):
            self.table.setItem(row, 0, QTableWidgetItem(str(complaint.get('id', 'N/A'))))
            self.table.setItem(row, 1, QTableWidgetItem(str(complaint.get('teacher_id', 'N/A'))))
            self.table.setItem(row, 2, QTableWidgetItem(complaint.get('teacher_name', 'N/A')))
            self.table.setItem(row, 3, QTableWidgetItem(str(complaint.get('complaint_date', 'N/A'))))
            
            complaint_text = complaint.get('complaint_text', '')
            complaint_item = QTableWidgetItem(complaint_text)
            complaint_item.setToolTip(complaint_text)  # Show full text on hover
            self.table.setItem(row, 4, complaint_item)
            
            self.table.setItem(row, 5, QTableWidgetItem(complaint.get('registered_by', 'N/A')))
        
        if not complaints:
            self.table.setRowCount(1)
            no_data_item = QTableWidgetItem("No complaints found.")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(0, 0, no_data_item)
            self.table.setSpan(0, 0, 1, 6)

