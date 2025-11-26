# SMS/dal/complaint_dal.py
import sqlite3
from dal.db_init import connect_db


def dal_add_complaint(teacher_id, complaint_text, complaint_date, registered_by=None):
    """
    Adds a new complaint against a teacher.
    Returns True on success, raises exception on error.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO complaint (teacher_id, complaint_text, complaint_date, registered_by)
            VALUES (?, ?, ?, ?)
        """, (teacher_id, complaint_text, complaint_date, registered_by))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def dal_get_complaints_by_teacher(teacher_id):
    """
    Gets all complaints for a specific teacher.
    Returns list of dictionaries.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, teacher_id, complaint_text, complaint_date, registered_by
            FROM complaint
            WHERE teacher_id = ?
            ORDER BY complaint_date DESC
        """, (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def dal_get_complaint_count_by_teacher(teacher_id):
    """
    Gets the total count of complaints for a specific teacher.
    Returns integer count.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM complaint
            WHERE teacher_id = ?
        """, (teacher_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def dal_get_teacher_leaderboard():
    """
    Gets all teachers with their complaint counts, ordered by complaint count (ascending).
    Teachers with fewer complaints rank higher (rank 5 = no complaints, rank 1 = most complaints).
    Returns list of dictionaries with teacher info and complaint count.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                t.id as teacher_id,
                f.first_name || ' ' || COALESCE(f.middle_name || ' ', '') || f.last_name as full_name,
                t.role,
                t.joining_date,
                t.salary,
                t.is_active,
                COUNT(c.id) as complaint_count
            FROM teacher t
            JOIN person p ON t.person_id = p.id
            JOIN fullname f ON f.person_id = p.id
            LEFT JOIN complaint c ON t.id = c.teacher_id
            WHERE t.is_active = 1
            GROUP BY t.id, f.first_name, f.middle_name, f.last_name, t.role, t.joining_date, t.salary, t.is_active
            ORDER BY complaint_count ASC, t.id DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

