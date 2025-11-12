# SMS/core/student_operations.py
import sqlite3
import os
import re
from core.db_init import connect_db
from core.due_operations import check_if_monthly_fee_was_run, add_specific_monthly_fee

def get_or_create_family(family_ssn, family_name):
    """
    Finds a family by SSN. If not found, creates one.
    Returns the family_id.
    """
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
        print(f"[ERROR] get_or_create_family: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_next_family_ssn():
    """
    Calculates the next available family SSN.
    Starts at 10001.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(CAST(family_SSN AS INTEGER)) FROM family")
        row = cursor.fetchone()
        if row and row[0] is not None:
            next_ssn = row[0] + 1
            return str(next_ssn)
        else:
            return "10001"
    except Exception as e:
        print(f"[ERROR] get_next_family_ssn: {e}")
        return "10001"
    finally:
        conn.close()

def search_families(search_term):
    """
    Searches the family table by SSN or name.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT id, family_SSN, family_name FROM family"
    params = []
    if search_term.isdigit():
        query += " WHERE family_SSN LIKE ?"
        params.append(f"%{search_term}%")
    else:
        query += " WHERE family_name LIKE ?"
        params.append(f"%{search_term}%")
    try:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[ERROR] search_families: {e}")
        return []
    finally:
        conn.close()


def add_student(first_name, middle_name, last_name, father_name, mother_name,
                dob, address, gender, contacts, date_of_admission, monthly_fee,
                annual_fund, student_class, family_id): 
    """
    Add a new student to the database using a family_id.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        fee_amount = float(monthly_fee)
        fund_amount = float(annual_fund)
        
        cursor.execute('''
            INSERT INTO person (fathername, mothername, dob, address, gender)
            VALUES (?, ?, ?, ?, ?)
        ''', (father_name, mother_name, dob, address, gender))
        person_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO fullname (person_id, first_name, middle_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (person_id, first_name, middle_name, last_name))

        for contact in contacts:
            cursor.execute('''
                INSERT INTO contact (person_id, type, value, label)
                VALUES (?, ?, ?, ?)
            ''', (person_id, contact.get('type'), contact.get('value'), contact.get('label')))

        cursor.execute('''
            INSERT INTO student (person_id, family_id, date_of_admission, monthly_fee, annual_fund, class)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (person_id, family_id, date_of_admission, fee_amount, fund_amount, student_class))
        
        new_student_id = cursor.lastrowid
        conn.commit()
        
        if fee_amount > 0:
            script_has_run, due_type_name = check_if_monthly_fee_was_run()
            if script_has_run:
                return True, "NEEDS_FEE_CONFIRMATION", new_student_id, fee_amount, due_type_name
        
        return True, "SUCCESS", new_student_id, None, None
            
    except Exception as e:
        print(f"[ERROR] add_student: {e}")
        conn.rollback()
        return False, str(e), None, None, None
    finally:
        conn.close()

def search_students(search_term):
    """
    Search for students by ID, 5-digit Family SSN, or name.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    query = """
        SELECT 
            s.id as student_id,
            f.first_name || ' ' || COALESCE(f.middle_name || ' ', '') || f.last_name as full_name,
            p.fathername as father_name,
            p.mothername as mother_name,
            s.class,
            s.monthly_fee,
            s.annual_fund,
            fam.family_SSN,
            fam.family_name
        FROM student s
        JOIN person p ON s.person_id = p.id
        JOIN fullname f ON f.person_id = p.id
        LEFT JOIN family fam ON s.family_id = fam.id
    """
    params = []
    cleaned_term = re.sub(r'\D', '', search_term)
    
    if cleaned_term.isdigit() and len(cleaned_term) == 5:
        query += " WHERE fam.family_SSN = ?"
        params.append(cleaned_term)
    elif cleaned_term.isdigit():
        query += " WHERE s.id = ?"
        params.append(int(cleaned_term))
    else:
        terms = search_term.split()
        conditions = []
        for term in terms:
            conditions.append("(f.first_name LIKE ? OR f.middle_name LIKE ? OR f.last_name LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
    try:
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[ERROR] search_students: {e}")
        return []
    finally:
        conn.close()

def get_student_contacts(student_id):
    """Fetches all contacts for a given student ID."""
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
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[ERROR] get_student_contacts: {e}")
        return []
    finally:
        conn.close()

def check_student_exists(student_id):
    """
    Checks if a student with the given ID exists in the database.
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM student WHERE id = ? LIMIT 1", (student_id,))
        if cursor.fetchone():
            return True
        else:
            return False
    except Exception as e:
        print(f"[ERROR] check_student_exists: {e}")
        return False
    finally:
        conn.close()

# --- UPDATED FUNCTION ---
def get_student_details_by_id(student_id):
    """
    Fetches a complete record for a student for populating the update form.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    details = {}
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
            -- --- FIX: Corrected JOIN from p.person_id = f.id to f.person_id = p.id ---
            JOIN fullname f ON f.person_id = p.id
            LEFT JOIN family fam ON s.family_id = fam.id
            WHERE s.id = ?
        """, (student_id,))
        
        main_data = cursor.fetchone()
        if not main_data:
            return None
        
        details = dict(main_data)
        
        # 2. Get contacts (uses person_id)
        person_id = details['person_id']
        cursor.execute("""
            SELECT type, value, label
            FROM contact
            WHERE person_id = ?
        """, (person_id,))
        
        contacts = [dict(row) for row in cursor.fetchall()]
        details['contacts'] = contacts
        
        return details
        
    except Exception as e:
        print(f"[ERROR] get_student_details_by_id: {e}")
        return None
    finally:
        conn.close()

# --- NEW FUNCTION ---
def update_student(student_id, person_id, data, contacts, family_id):
    """
    Updates an existing student record in a transaction.
    """
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
            """, (person_id, contact.get('type'), contact.get('value'), contact.get('label')))
            
        # 6. Commit
        conn.commit()
        return True, "Success"
        
    except Exception as e:
        print(f"[ERROR] update_student: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()