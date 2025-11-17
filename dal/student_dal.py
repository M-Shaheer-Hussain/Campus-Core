# SMS/dal/student_dal.py
import sqlite3
import re
from dal.db_init import connect_db

def dal_get_or_create_family(family_ssn, family_name):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM family WHERE family_SSN = ?", (family_ssn,))
        row = cursor.fetchone()
        
        if row:
            family_id = row[0]
            if family_name:
                cursor.execute("UPDATE family SET family_name = ? WHERE id = ?", (family_name, family_id))
            conn.commit()
            return family_id
        else:
            cursor.execute("""
                INSERT INTO family (family_SSN, family_name)
                VALUES (?, ?)
            """, (family_ssn, family_name))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_get_next_family_ssn():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(CAST(family_SSN AS INTEGER)) FROM family")
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    finally:
        conn.close()

def dal_search_families(query, params):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
        
# --- NEW DAL FUNCTION: Uniqueness Check ---
def dal_check_student_uniqueness(first_name, middle_name, last_name, dob):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Check for any existing student with the same full name and DOB
        cursor.execute("""
            SELECT 1 
            FROM student s
            JOIN fullname f ON s.person_id = f.person_id
            JOIN person p ON s.person_id = p.id
            WHERE 
                f.first_name = ? AND
                f.last_name = ? AND
                p.dob = ? AND
                (f.middle_name = ? OR (f.middle_name IS NULL AND ? IS NULL))
            LIMIT 1
        """, (first_name, last_name, dob, middle_name, middle_name))
        
        return cursor.fetchone() is not None # True if a match is found
    finally:
        conn.close()
# --- END NEW DAL FUNCTION ---

def dal_add_student_transaction(person_data, fullname_data, contacts, student_data, family_id):
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

        # 4. Insert into student
        cursor.execute('''
            INSERT INTO student (person_id, family_id, date_of_admission, monthly_fee, annual_fund, class)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (person_id, family_id, student_data['date_of_admission'], student_data['monthly_fee'], student_data['annual_fund'], student_data['student_class']))
        
        new_student_id = cursor.lastrowid
        conn.commit()
        return new_student_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_search_students(query, params):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_student_contacts(student_id):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT c.type, c.value, c.label
        FROM contact c
        JOIN student s ON c.person_id = s.person_id
        WHERE s.id = ?
    """
    try:
        cursor.execute(query, (student_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_check_student_exists(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM student WHERE id = ? LIMIT 1", (student_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()

def dal_get_student_details_by_id(student_id):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # 1. Get main data
        cursor.execute("""
            SELECT 
                s.id as student_id, s.person_id, s.family_id,
                s.date_of_admission, s.monthly_fee, s.annual_fund, s.class,
                p.fathername, p.mothername, p.dob, p.address, p.gender,
                f.first_name, f.middle_name, f.last_name,
                fam.family_SSN, fam.family_name
            FROM student s
            JOIN person p ON s.person_id = p.id
            JOIN fullname f ON f.person_id = p.id
            LEFT JOIN family fam ON s.family_id = fam.id
            WHERE s.id = ?
        """, (student_id,))
        main_data = cursor.fetchone()
        
        if not main_data:
            return None, None
            
        return dict(main_data), main_data['person_id']
        
    finally:
        conn.close()

def dal_update_student_transaction(student_id, person_id, data, contacts, family_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        
        # 1. Update person table
        cursor.execute("""
            UPDATE person
            SET fathername = ?, mothername = ?, dob = ?, address = ?, gender = ?
            WHERE id = ?
        """, (data['father_name'], data['mother_name'], data['dob'], 
              data['address'], data['gender'], person_id))
              
        # 2. Update fullname table
        cursor.execute("""
            UPDATE fullname
            SET first_name = ?, middle_name = ?, last_name = ?
            WHERE person_id = ?
        """, (data['first_name'], data['middle_name'], data['last_name'], person_id))
        
        # 3. Update student table
        cursor.execute("""
            UPDATE student
            SET family_id = ?, date_of_admission = ?, monthly_fee = ?, 
                annual_fund = ?, class = ?
            WHERE id = ?
        """, (family_id, data['date_of_admission'], float(data['monthly_fee']),
              float(data['annual_fund']), data['student_class'], student_id))
              
        # 4. Delete old contacts
        cursor.execute("DELETE FROM contact WHERE person_id = ?", (person_id,))
        
        # 5. Insert new contacts
        for contact in contacts:
            cursor.execute("""
                INSERT INTO contact (person_id, type, value, label)
                VALUES (?, ?, ?, ?)
            """, (person_id, contact['type'], contact['value'], contact['label']))
            
        # 6. Commit
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()