# SMS/dal/login_dal.py
from dal.db_init import connect_db

def dal_validate_admin(first_name, last_name, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id
        FROM admin a
        JOIN fullname f ON a.person_id = f.person_id
        WHERE f.first_name = ? AND f.last_name = ? AND a.password = ?
    """, (first_name, last_name, password))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

def dal_validate_receptionist(first_name, last_name, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id
        FROM receptionist r
        JOIN fullname f ON r.person_id = f.person_id
        WHERE f.first_name = ? AND f.last_name = ? AND r.password = ?
    """, (first_name, last_name, password))
    result = cursor.fetchone()
    conn.close()
    return bool(result)