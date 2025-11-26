from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QLabel,
    QFormLayout,
    QDialog,
)

from business.teacher_service import get_teacher_details_by_id, update_teacher
from common.utils import show_warning
from ui.teacher_form_widget import TeacherFormWidget
from ui.teacher_search_dialog import TeacherSearchDialog


class UpdateTeacherWidget(QWidget):
    """
    Mirrors the update student workflow to allow editing existing teacher profiles.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_teacher_id = None
        self.current_person_id = None

        main_layout = QVBoxLayout(self)

        search_group = QGroupBox("1. Find Teacher to Update")
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

        form_group = QGroupBox("2. Update Teacher Details")
        form_layout = QVBoxLayout()
        self.form_widget = TeacherFormWidget()
        self.btn_update = QPushButton("Save Changes")
        self.btn_update.setObjectName("primaryButton")
        self.btn_update.clicked.connect(self.handle_submit_update)

        form_layout.addWidget(self.form_widget)
        form_layout.addWidget(self.btn_update)
        form_group.setLayout(form_layout)
        form_group.setEnabled(False)

        self.form_group = form_group

        main_layout.addWidget(search_group)
        main_layout.addWidget(form_group)

    def open_teacher_search(self):
        dialog = TeacherSearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            teacher_id, teacher_name = dialog.get_selected_teacher()
            if teacher_id:
                self.teacher_id_label.setText(str(teacher_id))
                self.teacher_name_label.setText(teacher_name or "N/A")
                self.load_teacher_for_update(teacher_id)

    def load_teacher_for_update(self, teacher_id):
        try:
            teacher_data = get_teacher_details_by_id(teacher_id)
            if not teacher_data:
                show_warning(self, "Error", "Could not fetch teacher details.")
                self.reset_selection()
                return

            self.form_widget.populate_data(teacher_data)
            self.current_teacher_id = teacher_data.get("teacher_id")
            self.current_person_id = teacher_data.get("person_id")
            if not self.current_person_id:
                show_warning(self, "Error", "Teacher record missing person identifier.")
                self.reset_selection()
                return

            self.form_group.setEnabled(True)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load teacher data: {exc}")
            self.reset_selection()

    def reset_selection(self):
        self.teacher_id_label.setText("N/A")
        self.teacher_name_label.setText("N/A")
        self.current_teacher_id = None
        self.current_person_id = None
        self.form_group.setEnabled(False)
        self.form_widget.clear_fields()

    def handle_submit_update(self):
        if not self.current_teacher_id or not self.current_person_id:
            show_warning(self, "Error", "No teacher selected.")
            return

        data, contacts, is_valid, subjects, qualifications, experiences, class_sections = (
            self.form_widget.get_form_data()
        )
        if not is_valid:
            return

        success, message = update_teacher(
            teacher_id=self.current_teacher_id,
            person_id=self.current_person_id,
            data=data,
            contacts=contacts,
            subjects=subjects,
            qualifications=qualifications,
            experiences=experiences,
            class_sections=class_sections,
        )

        if success:
            QMessageBox.information(self, "Success", message)
            self.reset_selection()
        else:
            QMessageBox.critical(self, "Error", f"Failed to update teacher:\n{message}")

