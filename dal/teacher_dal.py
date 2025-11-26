# SMS/dal/teacher_dal.py
import sqlite3
import re
from dal.db_init import connect_db

def dal_add_teacher_transaction(person_data, fullname_data, contacts, teacher_data, 
                                subjects=None, qualifications=None, experiences=None, class_sections=None):
    """
    Adds a new teacher with person, fullname, contacts, and teacher records.
    Returns the new teacher_id on success.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # 1. Insert into person
        cursor.execute('''
            INSERT INTO person (fathername, mothername, dob, address, gender)
            VALUES (?, ?, ?, ?, ?)
        ''', person_data)
        person_id = cursor.lastrowid

        # 2. Insert into fullname
        cursor.execute('''
            INSERT INTO fullname (person_id, first_name, middle_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (person_id,) + fullname_data)

        # 3. Insert contacts
        for contact in contacts:
            cursor.execute('''
                INSERT INTO contact (person_id, type, value, label)
                VALUES (?, ?, ?, ?)
            ''', (person_id, contact['type'], contact['value'], contact['label']))

        # 4. Insert into teacher
        cursor.execute('''
            INSERT INTO teacher (
                person_id, joining_date, salary, rating, security_deposit,
                role, is_active, date_of_leaving
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            person_id,
            teacher_data['joining_date'],
            teacher_data['salary'],
            teacher_data['rating'],
            teacher_data.get('security_deposit', 0),
            teacher_data.get('role', 'Helper Teacher'),
            teacher_data.get('is_active', 1),
            teacher_data.get('date_of_leaving')
        ))
        
        new_teacher_id = cursor.lastrowid
        
        # 5. Insert subjects
        if subjects:
            for subject_name in subjects:
                if subject_name and subject_name.strip():
                    cursor.execute('''
                        INSERT INTO subject (teacher_id, subject_name)
                        VALUES (?, ?)
                    ''', (new_teacher_id, subject_name.strip()))
        
        # 6. Insert qualifications
        if qualifications:
            for qual in qualifications:
                if qual.get('degree'):
                    cursor.execute('''
                        INSERT INTO qualification (teacher_id, degree, institution, year)
                        VALUES (?, ?, ?, ?)
                    ''', (new_teacher_id, qual.get('degree'), qual.get('institution'), qual.get('year')))
        
        # 7. Insert experiences
        if experiences:
            for exp in experiences:
                if exp.get('institution'):
                    cursor.execute('''
                        INSERT INTO experience (teacher_id, institution, position, start_date, end_date, years_of_experience)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (new_teacher_id, exp.get('institution'), exp.get('position'), 
                          exp.get('start_date'), exp.get('end_date'), exp.get('years_of_experience')))
        
        # 8. Insert class_sections
        if class_sections:
            for cs in class_sections:
                if cs.get('class_name'):
                    cursor.execute('''
                        INSERT INTO class_section (teacher_id, class_name, section)
                        VALUES (?, ?, ?)
                    ''', (new_teacher_id, cs.get('class_name'), cs.get('section')))
        
        conn.commit()
        return new_teacher_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def dal_update_teacher_transaction(
    teacher_id,
    person_id,
    teacher_payload,
    form_data,
    contacts,
    subjects,
    qualifications,
    experiences,
    class_sections,
):
    """
    Updates teacher core data along with contacts and related collections.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")

        cursor.execute(
            """
            UPDATE person
            SET fathername = ?, dob = ?, address = ?, gender = ?
            WHERE id = ?
            """,
            (
                form_data["father_name"],
                form_data["dob"],
                form_data["address"],
                form_data["gender"],
                person_id,
            ),
        )

        cursor.execute(
            """
            UPDATE fullname
            SET first_name = ?, middle_name = ?, last_name = ?
            WHERE person_id = ?
            """,
            (
                form_data["first_name"],
                form_data.get("middle_name"),
                form_data["last_name"],
                person_id,
            ),
        )

        cursor.execute(
            """
            UPDATE teacher
            SET joining_date = ?, salary = ?, rating = ?, security_deposit = ?, role = ?
            WHERE id = ?
            """,
            (
                teacher_payload["joining_date"],
                teacher_payload["salary"],
                teacher_payload["rating"],
                teacher_payload["security_deposit"],
                teacher_payload["role"],
                teacher_id,
            ),
        )

        cursor.execute("DELETE FROM contact WHERE person_id = ?", (person_id,))
        for contact in contacts:
            cursor.execute(
                """
                INSERT INTO contact (person_id, type, value, label)
                VALUES (?, ?, ?, ?)
                """,
                (person_id, contact["type"], contact["value"], contact["label"]),
            )

        cursor.execute("DELETE FROM subject WHERE teacher_id = ?", (teacher_id,))
        for subject in subjects or []:
            cursor.execute(
                "INSERT INTO subject (teacher_id, subject_name) VALUES (?, ?)",
                (teacher_id, subject),
            )

        cursor.execute("DELETE FROM qualification WHERE teacher_id = ?", (teacher_id,))
        for qual in qualifications or []:
            cursor.execute(
                """
                INSERT INTO qualification (teacher_id, degree, institution, year)
                VALUES (?, ?, ?, ?)
                """,
                (teacher_id, qual.get("degree"), qual.get("institution"), qual.get("year")),
            )

        cursor.execute("DELETE FROM experience WHERE teacher_id = ?", (teacher_id,))
        for exp in experiences or []:
            cursor.execute(
                """
                INSERT INTO experience (
                    teacher_id, institution, position, start_date, end_date, years_of_experience
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    teacher_id,
                    exp.get("institution"),
                    exp.get("position"),
                    exp.get("start_date"),
                    exp.get("end_date"),
                    exp.get("years_of_experience"),
                ),
            )

        cursor.execute("DELETE FROM class_section WHERE teacher_id = ?", (teacher_id,))
        for cs in class_sections or []:
            cursor.execute(
                "INSERT INTO class_section (teacher_id, class_name, section) VALUES (?, ?, ?)",
                (teacher_id, cs.get("class_name"), cs.get("section")),
            )

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_search_teachers(query, params):
    """
    Generic search function for teachers.
    Returns list of dictionaries with teacher data.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_teacher_details_by_id(teacher_id):
    """
    Fetches complete teacher details by teacher_id.
    Returns (teacher_details_dict, person_id) or (None, None) if not found.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                t.id as teacher_id, t.person_id, t.joining_date, t.salary, 
                t.rating, t.security_deposit,
                t.role, t.is_active, t.date_of_leaving,
                p.fathername, p.dob, p.address, p.gender,
                f.first_name, f.middle_name, f.last_name
            FROM teacher t
            JOIN person p ON t.person_id = p.id
            JOIN fullname f ON f.person_id = p.id
            WHERE t.id = ?
        """, (teacher_id,))
        main_data = cursor.fetchone()
        
        if not main_data:
            return None, None
            
        return dict(main_data), main_data['person_id']
    finally:
        conn.close()

def dal_get_teacher_contacts(teacher_id):
    """
    Fetches all contacts for a teacher.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT c.type, c.value, c.label
        FROM contact c
        JOIN teacher t ON c.person_id = t.person_id
        WHERE t.id = ?
    """
    try:
        cursor.execute(query, (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_check_teacher_exists(teacher_id):
    """
    Checks if a teacher exists by teacher_id.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM teacher WHERE id = ? LIMIT 1", (teacher_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()

def dal_update_teacher_security_deposit(teacher_id, security_deposit):
    """
    Updates the security deposit for a teacher.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE teacher
            SET security_deposit = ?
            WHERE id = ?
        """, (security_deposit, teacher_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_check_teacher_uniqueness(first_name, middle_name, last_name, dob):
    """
    Checks if a teacher with the same full name and DOB already exists.
    Returns True if duplicate exists, False otherwise.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 1 
            FROM teacher t
            JOIN fullname f ON t.person_id = f.person_id
            JOIN person p ON t.person_id = p.id
            WHERE 
                f.first_name = ? AND
                f.last_name = ? AND
                p.dob = ? AND
                (f.middle_name = ? OR (f.middle_name IS NULL AND ? IS NULL))
            LIMIT 1
        """, (first_name, last_name, dob, middle_name, middle_name))
        
        return cursor.fetchone() is not None
    finally:
        conn.close()

def dal_get_teacher_subjects(teacher_id):
    """Fetches all subjects for a teacher."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT subject_name FROM subject WHERE teacher_id = ?", (teacher_id,))
        return [dict(row)['subject_name'] for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_teacher_qualifications(teacher_id):
    """Fetches all qualifications for a teacher."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT degree, institution, year FROM qualification WHERE teacher_id = ?", (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_teacher_experiences(teacher_id):
    """Fetches all experiences for a teacher."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT institution, position, start_date, end_date, years_of_experience 
            FROM experience 
            WHERE teacher_id = ?
            ORDER BY start_date DESC
        """, (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_teacher_class_sections(teacher_id):
    """Fetches all class sections for a teacher."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT class_name, section FROM class_section WHERE teacher_id = ?", (teacher_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_teacher_security_funds(teacher_id):
    """
    Gets teacher's security funds information including joining date, current deposit,
    and calculates time elapsed from joining date to today.
    Returns dict with: joining_date, security_deposit, months_elapsed, years_elapsed, days_elapsed
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT joining_date, security_deposit
            FROM teacher
            WHERE id = ?
        """, (teacher_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        
        # Calculate time elapsed if joining_date exists
        if result.get('joining_date'):
            from datetime import datetime, date
            try:
                joining_date = datetime.strptime(result['joining_date'], '%Y-%m-%d').date()
                today = date.today()
                
                # Calculate days, months, and years
                days_elapsed = (today - joining_date).days
                
                # Calculate months (approximate)
                years_elapsed = days_elapsed / 365.25
                months_elapsed = days_elapsed / 30.44  # Average days per month
                
                result['days_elapsed'] = days_elapsed
                result['months_elapsed'] = round(months_elapsed, 2)
                result['years_elapsed'] = round(years_elapsed, 2)
            except (ValueError, TypeError):
                result['days_elapsed'] = 0
                result['months_elapsed'] = 0
                result['years_elapsed'] = 0
        else:
            result['days_elapsed'] = 0
            result['months_elapsed'] = 0
            result['years_elapsed'] = 0
        
        return result
    finally:
        conn.close()

def dal_get_teacher_compensation(teacher_id):
    """
    Returns salary and current security deposit for validation purposes.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT salary, security_deposit
            FROM teacher
            WHERE id = ?
        """, (teacher_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def dal_mark_teacher_left(teacher_id, date_of_leaving):
    """
    Marks a teacher as inactive and stores the date of leaving.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE teacher
            SET is_active = 0,
                date_of_leaving = ?
            WHERE id = ?
        """, (date_of_leaving, teacher_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
