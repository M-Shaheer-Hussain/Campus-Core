# SMS/business/student_service.py
import sqlite3
import re
from dal.student_dal import (
    dal_get_or_create_family, dal_get_next_family_ssn, dal_search_families,
    dal_add_student_transaction, dal_search_students, dal_get_student_contacts,
    dal_check_student_exists, dal_get_student_details_by_id, dal_update_student_transaction,
    dal_check_student_uniqueness, dal_remove_student
)
from business.due_service import check_if_monthly_fee_was_run
import logging

logging.basicConfig(level=logging.INFO)

def get_or_create_family(family_ssn, family_name):
    """
    Service method for family creation/retrieval.
    """
    try:
        return dal_get_or_create_family(family_ssn, family_name)
    except Exception as e:
        logging.error(f"[ERROR] get_or_create_family: {e}")
        return None

def get_next_family_ssn():
    """
    Calculates the next available family SSN.
    Starts at 10001.
    """
    try:
        next_ssn = dal_get_next_family_ssn()
        if next_ssn is not None:
            return str(next_ssn + 1)
        else:
            return "10001"
    except Exception as e:
        logging.error(f"[ERROR] get_next_family_ssn: {e}")
        return "10001"

def search_families(search_term):
    """
    Searches the family table by SSN or name.
    Builds the query in the service layer, passes to DAL.
    """
    query = "SELECT id, family_SSN, family_name FROM family"
    params = []
    if search_term.isdigit():
        query += " WHERE family_SSN LIKE ?"
        params.append(f"%{search_term}%")
    else:
        query += " WHERE family_name LIKE ?"
        params.append(f"%{search_term}%")
    try:
        return dal_search_families(query, params)
    except Exception as e:
        logging.error(f"[ERROR] search_families: {e}")
        return []

def add_student(first_name, middle_name, last_name, father_name, mother_name,
                dob, address, gender, contacts, date_of_admission, monthly_fee,
                annual_fund, student_class, family_id): 
    """
    Service method to handle student addition, validation (including new business rules), and fee confirmation logic.
    """
    # Import validation utilities here to avoid circular dependency issues
    from common.utils import validate_min_age_at_event

    # 1. Apply Business Rule: Uniqueness (Full Name + DOB) - Now checks only active students in DAL
    if dal_check_student_uniqueness(first_name, middle_name, last_name, dob):
        error_msg = "A student with this Full Name and Date of Birth already exists."
        logging.error(f"[ERROR] add_student: {error_msg}")
        return False, error_msg, None, None, None

    # 2. Convert and validate floats
    try:
        fee_amount = float(monthly_fee)
        fund_amount = float(annual_fund)
    except ValueError:
        # Note: UI should prevent this, but BLL acts as final defense
        return False, "Fee amounts must be valid numbers.", None, None, None

    # 3. Apply Business Rule: Age at Admission (Min 3 years)
    is_valid_age, age_msg = validate_min_age_at_event(dob, date_of_admission, 3)
    if not is_valid_age:
        logging.error(f"[ERROR] add_student: {age_msg}")
        return False, age_msg, None, None, None
        
    try:
        # Prepare DAL data structures
        person_data = (father_name, mother_name, dob, address, gender)
        fullname_data = (first_name, middle_name, last_name)
        student_data = {
            'date_of_admission': date_of_admission,
            'monthly_fee': fee_amount,
            'annual_fund': fund_amount,
            'student_class': student_class
        }
        
        new_student_id = dal_add_student_transaction(person_data, fullname_data, contacts, student_data, family_id)
        
        # Post-DAL Business Logic: Check for monthly fee confirmation need
        if fee_amount > 0:
            script_has_run, due_type_name = check_if_monthly_fee_was_run()
            if script_has_run:
                return True, "NEEDS_FEE_CONFIRMATION", new_student_id, fee_amount, due_type_name
        
        return True, "SUCCESS", new_student_id, None, None
            
    except Exception as e:
        logging.error(f"[ERROR] add_student: {e}")
        return False, str(e), None, None, None

def search_students(search_term, include_inactive=False):
    """
    Search for students by ID, 5-digit Family SSN, or name.
    Builds the query in the service layer, passes to DAL.
    By default, searches only active students (is_active = 1).
    """
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
            fam.family_name,
            s.is_active, 
            s.date_of_leaving 
        FROM student s
        JOIN person p ON s.person_id = p.id
        JOIN fullname f ON f.person_id = p.id
        LEFT JOIN family fam ON s.family_id = fam.id
    """
    params = []
    
    # Base filter: Only include active students unless explicitly requested otherwise
    where_clauses = []
    if not include_inactive:
        where_clauses.append("s.is_active = 1")
    
    cleaned_term = re.sub(r'\D', '', search_term)
    
    if cleaned_term.isdigit() and len(cleaned_term) == 5:
        where_clauses.append("fam.family_SSN = ?")
        params.append(cleaned_term)
    elif cleaned_term.isdigit():
        where_clauses.append("s.id = ?")
        params.append(int(cleaned_term))
    else:
        terms = search_term.split()
        name_conditions = []
        for term in terms:
            name_conditions.append("(f.first_name LIKE ? OR f.middle_name LIKE ? OR f.last_name LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        if name_conditions:
            where_clauses.append("(" + " AND ".join(name_conditions) + ")")
            
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
            
    try:
        return dal_search_students(query, params)
    except Exception as e:
        logging.error(f"[ERROR] search_students: {e}")
        return []

def get_student_contacts(student_id):
    """Service method to fetch contacts by delegating to DAL."""
    try:
        return dal_get_student_contacts(student_id)
    except Exception as e:
        logging.error(f"[ERROR] get_student_contacts: {e}")
        return []

def check_student_exists(student_id):
    """
    Service method to check student existence by delegating to DAL.
    NOTE: DAL now checks for ACTIVE student existence.
    """
    try:
        return dal_check_student_exists(student_id)
    except Exception as e:
        logging.error(f"[ERROR] check_student_exists: {e}")
        return False

def get_student_details_by_id(student_id):
    """
    Service method: Fetches main data from DAL, then fetches contacts.
    """
    try:
        # 1. Fetch main data and person_id from DAL
        details, person_id = dal_get_student_details_by_id(student_id)
        if not details:
            return None
        
        # 2. Fetch contacts (reusing the search contacts for convenience)
        contacts = get_student_contacts(student_id)
        details['contacts'] = contacts
        
        return details
        
    except Exception as e:
        logging.error(f"[ERROR] get_student_details_by_id: {e}")
        return None

def update_student(student_id, person_id, data, contacts, family_id):
    """
    Service method: Orchestrates the update transaction, including age validation.
    """
    from common.utils import validate_min_age_at_event
    
    # Apply Business Rule: Age at Admission (Min 3 years)
    is_valid_age, age_msg = validate_min_age_at_event(data['dob'], data['date_of_admission'], 3)
    if not is_valid_age:
        logging.error(f"[ERROR] update_student: {age_msg}")
        return False, age_msg

    try:
        dal_update_student_transaction(student_id, person_id, data, contacts, family_id)
        return True, "Success"
        
    except Exception as e:
        logging.error(f"[ERROR] update_student: {e}")
        return False, str(e)

# --- NEW SERVICE FUNCTION ---
def remove_student(student_id, date_of_leaving):
    """
    Service method to mark a student as inactive (removed) and set the leaving date.
    """
    # Import validation utilities here to avoid circular dependency issues
    from common.utils import validate_is_not_future_date
    
    # 1. Basic validation
    if not dal_check_student_exists(student_id):
        return False, "Student not found or already marked as inactive."
        
    # 2. Apply Business Rule: Date of Leaving Must Not Be Future
    is_valid, error_msg = validate_is_not_future_date(date_of_leaving)
    if not is_valid:
        logging.error(f"[ERROR] remove_student: Date of leaving is in the future: {date_of_leaving}")
        return False, error_msg
        
    try:
        if dal_remove_student(student_id, date_of_leaving):
            return True, "Student marked as inactive successfully."
        else:
            return False, "Database operation failed."
    except Exception as e:
        logging.error(f"[ERROR] remove_student: {e}")
        return False, str(e)
# --- END NEW SERVICE FUNCTION ---