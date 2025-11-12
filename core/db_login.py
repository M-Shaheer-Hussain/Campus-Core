import sqlite3

DB_PATH = "data/campuscore.db"

def validate_admin(username, password):
    """
    Admin username: 'FirstName LastName'
    """
    if " " not in username:
        return False
    first_name, last_name = username.strip().split(" ", 1)

    conn = sqlite3.connect(DB_PATH)
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


def validate_receptionist(username, password):
    """
    Receptionist username: 'FirstName LastName'
    """
    if " " not in username:
        return False
    first_name, last_name = username.strip().split(" ", 1)

    conn = sqlite3.connect(DB_PATH)
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
