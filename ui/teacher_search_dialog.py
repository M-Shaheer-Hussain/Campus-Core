from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

from ui.search_teacher_widget import SearchTeacherWidget


class TeacherSearchDialog(QDialog):
    """
    Dialog wrapper that embeds the SearchTeacherWidget and returns the selected teacher.
    Mirrors the student update search UX.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search and Select Teacher")
        self.setMinimumSize(1000, 600)
        self.selected_teacher_id = None
        self.selected_teacher_name = None

        layout = QVBoxLayout(self)
        self.search_widget = SearchTeacherWidget(enable_double_click=False)
        layout.addWidget(self.search_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.search_widget.results_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.search_widget.results_tree.itemDoubleClicked.connect(lambda *_: self.on_accept())

    def on_selection_changed(self):
        teacher_id, _ = self.search_widget.get_selected_teacher()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(bool(teacher_id))

    def on_accept(self):
        teacher_id, teacher_name = self.search_widget.get_selected_teacher()
        if teacher_id:
            self.selected_teacher_id = teacher_id
            self.selected_teacher_name = teacher_name
            self.accept()

    def get_selected_teacher(self):
        return self.selected_teacher_id, self.selected_teacher_name

