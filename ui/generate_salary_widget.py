from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
from business.teacher_service import search_teachers
from business.salary_service import calculate_monthly_salary, save_monthly_salaries


class GenerateMonthlySalaryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Monthly Salary (UC-21)")
        self.salary_records = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # TITLE
        title = QLabel("Generate Monthly Salary")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # MONTH + YEAR SELECTION
        row = QHBoxLayout()
        self.month_box = QComboBox()
        self.month_box.addItems([
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ])
        self.year_box = QComboBox()
        self.year_box.addItems([str(y) for y in range(2020, 2035)])
        row.addWidget(QLabel("Month:"))
        row.addWidget(self.month_box)
        row.addWidget(QLabel("Year:"))
        row.addWidget(self.year_box)
        layout.addLayout(row)

        # GENERATE BUTTON
        self.btn_generate = QPushButton("Generate Monthly Salary")
        self.btn_generate.clicked.connect(self.generate_salary)
        layout.addWidget(self.btn_generate)

        # TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Teacher ID", "Name", "Gross", "Deductions", "Net Pay"])
        layout.addWidget(self.table)

        # CONFIRM BUTTON (BLUE)
        self.btn_confirm = QPushButton("Confirm and Save Salary")
        self.btn_confirm.clicked.connect(self.save_salary)
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.setStyleSheet("background-color: #007BFF; color: white; font-weight: bold;")
        self.btn_confirm.setFixedHeight(50)  # Height badha di
        layout.addWidget(self.btn_confirm)

        self.setLayout(layout)

    def generate_salary(self):
        month = self.month_box.currentText()
        year = self.year_box.currentText()
        self.salary_records.clear()
        self.table.setRowCount(0)

        try:
            teachers = search_teachers("")
            if not teachers:
                QMessageBox.warning(self, "Error", "No teachers found in system.")
                return

            for teacher in teachers:
                teacher_id = teacher.get('teacher_id')
                name = teacher.get('full_name', 'Unknown')

                salary_data = calculate_monthly_salary(teacher_id, month, year)
                if salary_data.get("error"):
                    continue  # skip teacher with error

                gross = salary_data.get("gross", 0)
                deductions = salary_data.get("deductions", 0)
                net_pay = salary_data.get("net_pay", 0)

                # Populate table
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(teacher_id)))
                self.table.setItem(row, 1, QTableWidgetItem(name))
                self.table.setItem(row, 2, QTableWidgetItem(str(gross)))
                self.table.setItem(row, 3, QTableWidgetItem(str(deductions)))
                self.table.setItem(row, 4, QTableWidgetItem(str(net_pay)))

                # Store in memory
                self.salary_records.append({
                    "teacher_id": teacher_id,
                    "month": month,
                    "year": year,
                    "gross": gross,
                    "deductions": deductions,
                    "net_pay": net_pay
                })

            if self.salary_records:
                self.btn_confirm.setEnabled(True)
                QMessageBox.information(self, "Success", "Salary summary generated!")
            else:
                QMessageBox.warning(self, "Warning", "No valid salary records generated.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred:\n{e}")

    def save_salary(self):
        if not self.salary_records:
            QMessageBox.warning(self, "Error", "No salary data to save.")
            return

        try:
            success = save_monthly_salaries(self.salary_records)
            if success:
                QMessageBox.information(self, "Saved", "Monthly salary saved successfully.")
                self.btn_confirm.setEnabled(False)
                self.table.setRowCount(0)
                self.salary_records.clear()
            else:
                QMessageBox.critical(self, "Error", "Saving failed.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Saving failed:\n{e}")
