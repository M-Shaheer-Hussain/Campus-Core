from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
    QTreeWidgetItem, QStackedWidget, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TeacherDetailsWindow(QWidget):
    """
    Displays full teacher information in a dedicated window, mirroring the
    student search experience (categories on the left, details on the right).
    """

    def __init__(self, teacher_data, parent=None):
        super().__init__(parent)
        self.teacher_data = teacher_data or {}
        self.teacher_id = self.teacher_data.get("teacher_id")
        self.teacher_name = self._build_full_name()

        self.setWindowTitle(f"Teacher Profile: {self.teacher_name} (ID: {self.teacher_id})")
        self.setMinimumSize(1100, 700)
        self.setObjectName("TeacherDetailsWindow")

        try:
            with open("assets/style.qss", "r", encoding="utf-8") as stylesheet:
                self.setStyleSheet(stylesheet.read())
        except (FileNotFoundError, OSError):
            # Style is optional; ignore missing file.
            pass

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(f"Teacher Profile: {self.teacher_name}")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; padding: 15px; background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(content_layout)

        self.category_tree = self._create_category_tree()
        content_layout.addWidget(self.category_tree)

        self.detail_stack = QStackedWidget()
        content_layout.addWidget(self.detail_stack, 1)

        # Create detail pages
        self.summary_page = self._create_summary_page()
        self.contacts_page = self._create_contacts_page()
        self.subjects_page = self._create_subjects_page()
        self.qualifications_page = self._create_qualifications_page()
        self.experiences_page = self._create_experiences_page()
        self.class_assignments_page = self._create_class_assignments_page()

        for page in (
            self.summary_page,
            self.contacts_page,
            self.subjects_page,
            self.qualifications_page,
            self.experiences_page,
            self.class_assignments_page,
        ):
            self.detail_stack.addWidget(page)

        self.category_tree.currentItemChanged.connect(self._on_category_changed)
        self._load_categories()

    def _build_full_name(self):
        first = self.teacher_data.get("first_name", "")
        middle = self.teacher_data.get("middle_name", "")
        last = self.teacher_data.get("last_name", "")
        parts = [part.strip() for part in (first, middle, last) if part and part.strip()]
        return " ".join(parts) if parts else self.teacher_data.get("full_name", "N/A")

    def _create_category_tree(self):
        tree = QTreeWidget()
        tree.setObjectName("TeacherCategoryTree")
        tree.setFixedWidth(230)
        tree.setHeaderHidden(True)
        return tree

    def _load_categories(self):
        self.category_tree.clear()
        bold_font = QFont()
        bold_font.setBold(True)

        categories = [
            ("Summary", self.summary_page),
            ("Contact Info", self.contacts_page),
            ("Subjects", self.subjects_page),
            ("Qualifications", self.qualifications_page),
            ("Experience", self.experiences_page),
            ("Class Assignments", self.class_assignments_page),
        ]

        for label, widget in categories:
            item = QTreeWidgetItem(self.category_tree, [label])
            item.setFont(0, bold_font)
            item.setData(0, Qt.UserRole, widget)

        if self.category_tree.topLevelItemCount():
            self.category_tree.setCurrentItem(self.category_tree.topLevelItem(0))

    def _create_summary_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        def bold_label(text):
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 11, QFont.Bold))
            return label

        def value_label(value):
            label = QLabel(str(value))
            label.setFont(QFont("Segoe UI", 11))
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            return label

        status = "Active"
        if self.teacher_data.get("is_active") == 0:
            leave_date = self.teacher_data.get("date_of_leaving") or "N/A"
            status = f"Left ({leave_date})"

        layout.addRow(bold_label("Teacher ID:"), value_label(self.teacher_id or "N/A"))
        layout.addRow(bold_label("Full Name:"), value_label(self.teacher_name))
        layout.addRow(bold_label("Father Name:"), value_label(self.teacher_data.get("fathername", "N/A")))
        layout.addRow(bold_label("Date of Birth:"), value_label(self.teacher_data.get("dob", "N/A")))
        layout.addRow(bold_label("Gender:"), value_label(self.teacher_data.get("gender", "N/A")))
        layout.addRow(bold_label("Role:"), value_label(self.teacher_data.get("role", "N/A")))
        layout.addRow(bold_label("Rating:"), value_label(self.teacher_data.get("rating", "N/A")))
        layout.addRow(bold_label("Joining Date:"), value_label(self.teacher_data.get("joining_date", "N/A")))
        layout.addRow(bold_label("Status:"), value_label(status))
        layout.addRow(bold_label("Address:"), value_label(self.teacher_data.get("address", "N/A")))

        salary = self.teacher_data.get("salary", 0.0)
        security = self.teacher_data.get("security_deposit", 0.0)
        layout.addRow(bold_label("Salary:"), value_label(f"{salary:.2f}"))
        layout.addRow(bold_label("Security Deposit:"), value_label(f"{security:.2f}"))

        return page

    def _create_contacts_page(self):
        contacts = self.teacher_data.get("contacts", [])
        headers = ["Type", "Label", "Value"]
        rows = []
        for contact in contacts:
            rows.append([
                (contact.get("type") or "N/A").title(),
                (contact.get("label") or "N/A").title(),
                contact.get("value") or "N/A",
            ])
        empty_message = "No contact information on file."
        return self._build_table_page(headers, rows, empty_message)

    def _create_subjects_page(self):
        subjects = self.teacher_data.get("subjects", [])
        headers = ["Subject"]
        rows = [[subject] for subject in subjects]
        return self._build_table_page(headers, rows, "No subjects assigned.")

    def _create_qualifications_page(self):
        qualifications = self.teacher_data.get("qualifications", [])
        headers = ["Degree", "Institution", "Year"]
        rows = []
        for qual in qualifications:
            rows.append([
                qual.get("degree", "N/A"),
                qual.get("institution", "N/A"),
                qual.get("year", "N/A"),
            ])
        return self._build_table_page(headers, rows, "No qualifications listed.")

    def _create_experiences_page(self):
        experiences = self.teacher_data.get("experiences", [])
        headers = ["Institution", "Position", "Duration", "Years"]
        rows = []
        for exp in experiences:
            duration_parts = []
            if exp.get("start_date"):
                duration_parts.append(exp["start_date"])
            if exp.get("end_date"):
                duration_parts.append(exp["end_date"])
            duration = " - ".join(duration_parts) if duration_parts else "N/A"
            rows.append([
                exp.get("institution", "N/A"),
                exp.get("position", "N/A"),
                duration,
                exp.get("years_of_experience", "N/A"),
            ])
        return self._build_table_page(headers, rows, "No experience records available.")

    def _create_class_assignments_page(self):
        assignments = self.teacher_data.get("class_sections", [])
        headers = ["Class", "Section"]
        rows = []
        for cls in assignments:
            rows.append([
                cls.get("class_name", "N/A"),
                cls.get("section", "N/A"),
            ])
        return self._build_table_page(headers, rows, "No class assignments available.")

    def _build_table_page(self, headers, rows, empty_message):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        if not rows:
            table.setRowCount(1)
            message_item = QTableWidgetItem(empty_message)
            message_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, message_item)
            table.setSpan(0, 0, 1, len(headers))
        else:
            table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                for col_index, value in enumerate(row):
                    table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

        return table

    def _on_category_changed(self, current_item, previous_item):
        if not current_item:
            self.detail_stack.setCurrentWidget(self.summary_page)
            return

        widget = current_item.data(0, Qt.UserRole)
        if widget:
            self.detail_stack.setCurrentWidget(widget)
        else:
            self.detail_stack.setCurrentWidget(self.summary_page)

