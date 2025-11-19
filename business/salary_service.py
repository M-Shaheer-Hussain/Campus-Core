# business/salary_service.py

from dal.db_connection import get_connection


def calculate_monthly_salary(teacher_id, month, year):
    conn = get_connection()
    cursor = conn.cursor()

    # Correct table name
    cursor.execute("SELECT salary FROM teacher WHERE id = ?", (teacher_id,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Teacher not found"}

    salary = row[0]

    gross = salary
    deductions = 0
    net_pay = gross - deductions

    return {
        "gross": gross,
        "deductions": deductions,
        "net_pay": net_pay,
        "error": None
    }



def save_monthly_salaries(salary_list):
    """
    salary_list = [
        {
            teacher_id: ,
            month: ,
            year: ,
            gross: ,
            deductions: ,
            net_pay:
        }
    ]
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()

        for s in salary_list:
            cursor.execute("""
                INSERT INTO salary_records (teacher_id, month, year, gross, deductions, net_pay)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                s["teacher_id"],
                s["month"],
                s["year"],
                s["gross"],
                s["deductions"],
                s["net_pay"],
            ))

        conn.commit()
        return True

    except Exception as e:
        print("Error saving salary:", e)
        return False
