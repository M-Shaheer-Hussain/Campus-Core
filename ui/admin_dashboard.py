# SMS/ui/admin_dashboard.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QButtonGroup, QApplication, QStyle, QMessageBox 
)
from PyQt5.QtCore import Qt
from ui.add_student_widget import AddStudentWidget
from ui.update_student_widget import UpdateStudentWidget
from ui.search_student_widget import SearchStudentWidget
from ui.add_due_widget import AddDueWidget
from ui.make_payment_widget import MakePaymentWidget
from ui.payment_history_widget import PaymentHistoryWidget

class AdminDashboard(QWidget):
    """
    Admin Dashboard: Uses the same core functional widgets as the Receptionist 
    but has a distinct UI structure and styling for clarity and privilege separation.
    """
    def __init__(self, username, go_back_callback=None):
        super().__init__()
        self.username = username
        self.go_back_callback = go_back_callback
        self.setWindowTitle(f"Admin Dashboard - {username}")
        
        self.setFixedSize(1000, 600)
        self.setStyleSheet(open("assets/style.qss").read())
        
        # --- Get standard icons ---
        style = self.style()
        
        self.add_icon = style.standardIcon(QStyle.SP_FileDialogNewFolder)
        self.update_icon = style.standardIcon(QStyle.SP_DriveHDIcon)
        self.search_icon = style.standardIcon(QStyle.SP_FileDialogDetailedView)
        self.add_due_icon = style.standardIcon(QStyle.SP_FileLinkIcon)
        self.payment_icon = style.standardIcon(QStyle.SP_DialogApplyButton)
        self.history_icon = style.standardIcon(QStyle.SP_DialogResetButton)
        self.logout_icon = style.standardIcon(QStyle.SP_DialogCancelButton)

        self.init_ui()
        self.show_search_student()
        self.btn_search_student.setChecked(True)

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- CRITICAL FOR STYLING: Set unique object name for CSS targeting ---
        self.setObjectName("AdminDashboardFrame") 
        self.setLayout(main_layout)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("sidebarFrame") 

        # --- Button Group ---
        self.sidebar_button_group = QButtonGroup(self)
        self.sidebar_button_group.setExclusive(True)

        # --- Reused Buttons (Functional Widgets Only) ---
        self.btn_add_student = QPushButton(" Add Student")
        self.btn_add_student.setIcon(self.add_icon)
        
        self.btn_update_student = QPushButton(" Update Student")
        self.btn_update_student.setIcon(self.update_icon)
        
        self.btn_search_student = QPushButton(" Search Student")
        self.btn_search_student.setIcon(self.search_icon)
        
        self.btn_add_due = QPushButton(" Add Manual Due")
        self.btn_add_due.setIcon(self.add_due_icon)
        
        self.btn_make_payment = QPushButton(" Make Payment")
        self.btn_make_payment.setIcon(self.payment_icon)
        
        self.btn_payment_history = QPushButton(" Payment History")
        self.btn_payment_history.setIcon(self.history_icon)

        self.btn_logout = QPushButton(" Logout")
        self.btn_logout.setIcon(self.logout_icon)
        
        buttons = [
            self.btn_add_student, self.btn_update_student, self.btn_search_student,
            self.btn_add_due, self.btn_make_payment, self.btn_payment_history
        ]
        
        sidebar_layout = QVBoxLayout(sidebar)
        for button in buttons:
            button.setObjectName("sidebarButton")
            button.setCheckable(True)
            self.sidebar_button_group.addButton(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()
        
        self.btn_logout.setObjectName("sidebarButton")
        sidebar_layout.addWidget(self.btn_logout)

        # Content Area
        self.content_area = QFrame()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_area.setObjectName("contentArea")
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel(f"Welcome, {self.username}")
        header.setAlignment(Qt.AlignRight)
        header.setObjectName("headerLabel")

        self.content_layout.addWidget(header)
        
        self.content_stack = QFrame()
        self.content_stack_layout = QVBoxLayout(self.content_stack)
        self.content_stack_layout.setContentsMargins(20, 10, 20, 10)
        self.content_layout.addWidget(self.content_stack, 1)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_area, 1)

        # Connect actions (reusable widgets)
        self.btn_add_student.clicked.connect(self.show_add_student)
        self.btn_update_student.clicked.connect(self.show_update_student)
        self.btn_search_student.clicked.connect(self.show_search_student)
        self.btn_add_due.clicked.connect(self.show_add_due)
        self.btn_make_payment.clicked.connect(self.show_make_payment)
        self.btn_payment_history.clicked.connect(self.show_payment_history)
        self.btn_logout.clicked.connect(self.handle_logout)

    def _clear_content_area(self):
        """Helper function to clear the content area."""
        for i in reversed(range(self.content_stack_layout.count())):
            item = self.content_stack_layout.takeAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_add_student(self):
        self._clear_content_area()
        form = AddStudentWidget()
        self.content_stack_layout.addWidget(form)

    def show_update_student(self):
        self._clear_content_area()
        widget = UpdateStudentWidget()
        self.content_stack_layout.addWidget(widget)

    def show_search_student(self):
        self._clear_content_area()
        widget = SearchStudentWidget(enable_double_click=True)
        self.content_stack_layout.addWidget(widget)

    def show_add_due(self):
        self._clear_content_area()
        widget = AddDueWidget()
        self.content_stack_layout.addWidget(widget)

    def show_make_payment(self):
        self._clear_content_area()
        widget = MakePaymentWidget(username=self.username)
        self.content_stack_layout.addWidget(widget)

    def show_payment_history(self):
        self._clear_content_area()
        widget = PaymentHistoryWidget()
        self.content_stack_layout.addWidget(widget)

    def handle_logout(self):
        self.close()
        if self.go_back_callback:
            self.go_back_callback()