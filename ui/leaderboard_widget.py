# SMS/ui/leaderboard_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from business.complaint_service import get_teacher_leaderboard


class LeaderboardWidget(QWidget):
    """
    Displays teacher leaderboard ranked by complaint count.
    Rank 5 = no complaints (best), Rank 1 = most complaints (worst).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_leaderboard()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Teacher Leaderboard")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Info label
        info_label = QLabel(
            "Teachers are ranked based on complaints. Rank 5 = No complaints (Best), "
            "Rank 1 = Most complaints (Worst)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Rank", "Teacher ID", "Full Name", "Role", 
            "Joining Date", "Salary", "Complaints"
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
        
        layout.addWidget(self.table)
    
    def load_leaderboard(self):
        """Loads and displays the teacher leaderboard."""
        try:
            teachers = get_teacher_leaderboard()
            self.table.setRowCount(len(teachers))
            
            for row, teacher in enumerate(teachers):
                rank = teacher.get('rank', 5)
                teacher_id = teacher.get('teacher_id', '')
                full_name = teacher.get('full_name', '')
                role = teacher.get('role', '')
                joining_date = teacher.get('joining_date', '') or 'N/A'
                salary = teacher.get('salary', 0)
                complaint_count = teacher.get('complaint_count', 0)
                
                # Rank column with color coding
                rank_item = QTableWidgetItem(str(rank))
                rank_item.setTextAlignment(Qt.AlignCenter)
                if rank == 5:
                    rank_item.setBackground(QColor(144, 238, 144))  # Light green
                elif rank == 4:
                    rank_item.setBackground(QColor(173, 216, 230))  # Light blue
                elif rank == 3:
                    rank_item.setBackground(QColor(255, 255, 224))  # Light yellow
                elif rank == 2:
                    rank_item.setBackground(QColor(255, 218, 185))  # Peach
                else:
                    rank_item.setBackground(QColor(255, 182, 193))  # Light pink
                
                self.table.setItem(row, 0, rank_item)
                self.table.setItem(row, 1, QTableWidgetItem(str(teacher_id)))
                self.table.setItem(row, 2, QTableWidgetItem(full_name))
                self.table.setItem(row, 3, QTableWidgetItem(role))
                self.table.setItem(row, 4, QTableWidgetItem(str(joining_date)))
                self.table.setItem(row, 5, QTableWidgetItem(f"{salary:.2f}"))
                
                complaint_item = QTableWidgetItem(str(complaint_count))
                complaint_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 6, complaint_item)
            
            if not teachers:
                self.table.setRowCount(1)
                no_data_item = QTableWidgetItem("No active teachers found.")
                no_data_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(0, 0, no_data_item)
                self.table.setSpan(0, 0, 1, 7)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load leaderboard:\n{e}")

