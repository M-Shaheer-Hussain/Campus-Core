# SMS/business/teacher_service.py
from dal.teacher_dal import (
    dal_add_teacher_transaction,
    dal_search_teachers,
    dal_get_teacher_details_by_id,
    dal_get_teacher_contacts,
    dal_check_teacher_exists,
    dal_update_teacher_security_deposit,
    dal_check_teacher_uniqueness,
    dal_get_teacher_subjects,
    dal_get_teacher_qualifications,
    dal_get_teacher_experiences,
    dal_get_teacher_class_sections,
    dal_get_teacher_security_funds,
    dal_get_teacher_compensation,
    dal_mark_teacher_left,
    dal_update_teacher_transaction,
)
import logging
import re

logging.basicConfig(level=logging.INFO)

TEACHER_ROLES = [
    "Principal",
    "Coordinator",
    "Head Teacher",
    "Helper Teacher"
]

def add_teacher(first_name, middle_name, last_name, father_name,
                dob, address, gender, contacts, joining_date, salary, rating,
                security_deposit=0, role="Helper Teacher",
                subjects=None, qualifications=None, experiences=None, class_sections=None):
    """
    Service method to handle teacher addition with validation.
    Returns (success: bool, message: str, teacher_id: int or None)
    """
    from common.utils import validate_min_age_at_event, validate_is_not_future_date, validate_dob_not_current_year
    
    # 1. Apply Business Rule: Uniqueness (Full Name + DOB)
    if dal_check_teacher_uniqueness(first_name, middle_name, last_name, dob):
        error_msg = "A teacher with this Full Name and Date of Birth already exists."
        logging.error(f"[ERROR] add_teacher: {error_msg}")
        return False, error_msg, None

    # 1.5. Validate DOB is not in current year
    is_valid_dob, dob_msg = validate_dob_not_current_year(dob)
    if not is_valid_dob:
        logging.error(f"[ERROR] add_teacher: {dob_msg}")
        return False, dob_msg, None

    # 2. Validate salary is positive
    try:
        salary_amount = float(salary)
        if salary_amount <= 0:
            return False, "Salary must be greater than zero.", None
    except ValueError:
        return False, "Salary must be a valid number.", None

    # 3. Validate rating (1-5)
    try:
        rating_value = int(rating)
        if rating_value < 1 or rating_value > 5:
            return False, "Rating must be between 1 and 5.", None
    except ValueError:
        return False, "Rating must be a valid integer between 1 and 5.", None

    # 3.5 Validate role
    if role not in TEACHER_ROLES:
        return False, "Invalid teacher role provided.", None

    # 4. Validate security deposit (if provided)
    try:
        security_amount = float(security_deposit) if security_deposit else 0
        if security_amount < 0:
            return False, "Security deposit cannot be negative.", None
        if security_amount > salary_amount:
            return False, "Security deposit cannot exceed salary.", None
    except ValueError:
        return False, "Security deposit must be a valid number.", None

    # 5. Validate joining date is not in future
    is_valid_date, date_msg = validate_is_not_future_date(joining_date)
    if not is_valid_date:
        logging.error(f"[ERROR] add_teacher: {date_msg}")
        return False, date_msg, None

    # 6. Validate minimum age (assuming 18 years for teachers)
    is_valid_age, age_msg = validate_min_age_at_event(dob, joining_date, 18)
    if not is_valid_age:
        logging.error(f"[ERROR] add_teacher: {age_msg}")
        return False, age_msg, None
        
    try:
        # Prepare DAL data structures (mothername set to empty string for compatibility with existing schema)
        person_data = (father_name, "", dob, address, gender)
        fullname_data = (first_name, middle_name, last_name)
        teacher_data = {
            'joining_date': joining_date,
            'salary': salary_amount,
            'rating': rating_value,
            'security_deposit': security_amount,
            'role': role,
            'is_active': 1,
            'date_of_leaving': None
        }
        
        new_teacher_id = dal_add_teacher_transaction(
            person_data, fullname_data, contacts, teacher_data,
            subjects=subjects, qualifications=qualifications, 
            experiences=experiences, class_sections=class_sections
        )
        
        return True, "SUCCESS", new_teacher_id
            
    except Exception as e:
        logging.error(f"[ERROR] add_teacher: {e}")
        return False, str(e), None

def search_teachers(search_term, status_filter="Active"):
    """
    Search for teachers by ID or name.
    Builds the query in the service layer, passes to DAL.
    """
    query = """
        SELECT 
            t.id as teacher_id,
            f.first_name || ' ' || COALESCE(f.middle_name || ' ', '') || f.last_name as full_name,
            p.fathername as father_name,
            t.joining_date,
            t.salary,
            t.rating,
            t.security_deposit,
            t.role,
            t.is_active,
            t.date_of_leaving,
            CASE WHEN t.is_active = 1 THEN 'Active' ELSE 'Left' END as status_label
        FROM teacher t
        JOIN person p ON t.person_id = p.id
        JOIN fullname f ON f.person_id = p.id
    """
    params = []
    conditions = []

    cleaned_term = re.sub(r'\D', '', search_term)
    
    if cleaned_term.isdigit():
        conditions.append("t.id = ?")
        params.append(int(cleaned_term))
    else:
        terms = search_term.split()
        name_conditions = []
        for term in terms:
            name_conditions.append("(f.first_name LIKE ? OR f.middle_name LIKE ? OR f.last_name LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        if name_conditions:
            conditions.append("(" + " AND ".join(name_conditions) + ")")

    normalized_status = (status_filter or "Active").strip().lower()
    if normalized_status in ("active", "active teachers"):
        conditions.append("t.is_active = 1")
    elif normalized_status in ("left", "left teachers", "inactive"):
        conditions.append("t.is_active = 0")
    elif normalized_status in ("all", "all teachers"):
        pass
    else:
        conditions.append("t.is_active = 1")
            
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY t.id DESC"
            
    try:
        return dal_search_teachers(query, params)
    except Exception as e:
        logging.error(f"[ERROR] search_teachers: {e}")
        return []

def get_teacher_details_by_id(teacher_id):
    """
    Service method: Fetches main data from DAL, then fetches contacts and related data.
    """
    try:
        # 1. Fetch main data and person_id from DAL
        details, person_id = dal_get_teacher_details_by_id(teacher_id)
        if not details:
            return None
        
        # 2. Fetch contacts
        contacts = dal_get_teacher_contacts(teacher_id)
        details["contacts"] = contacts
        
        # 3. Fetch subjects, qualifications, experiences, and class sections
        details["subjects"] = dal_get_teacher_subjects(teacher_id)
        details["qualifications"] = dal_get_teacher_qualifications(teacher_id)
        details["experiences"] = dal_get_teacher_experiences(teacher_id)
        details["class_sections"] = dal_get_teacher_class_sections(teacher_id)
        details["person_id"] = person_id
        
        return details
        
    except Exception as e:
        logging.error(f"[ERROR] get_teacher_details_by_id: {e}")
        return None

def check_teacher_exists(teacher_id):
    """
    Service method to check teacher existence by delegating to DAL.
    """
    try:
        return dal_check_teacher_exists(teacher_id)
    except Exception as e:
        logging.error(f"[ERROR] check_teacher_exists: {e}")
        return False

def update_teacher_security_deposit(teacher_id, additional_amount):
    """
    Service method to add to a teacher's security deposit.
    Returns (success: bool, message: str)
    """
    from common.utils import validate_is_positive_float

    is_valid, error_msg = validate_is_positive_float(str(additional_amount))
    if not is_valid:
        return False, error_msg

    additional_amount = float(additional_amount)
    if additional_amount == 0:
        return False, "Additional amount must be greater than zero."

    compensation = dal_get_teacher_compensation(teacher_id)
    if not compensation:
        return False, "Teacher not found."

    salary = float(compensation.get('salary') or 0)
    current_deposit = float(compensation.get('security_deposit') or 0)
    new_total = current_deposit + additional_amount

    if salary <= 0:
        return False, "Teacher salary is missing. Cannot update security deposit."

    if new_total > salary:
        remaining_capacity = max(salary - current_deposit, 0)
        return False, f"Security deposit cannot exceed salary. You can add up to {remaining_capacity:.2f}."

    try:
        dal_update_teacher_security_deposit(teacher_id, new_total)
        return True, f"Security deposit updated successfully. New total: {new_total:.2f}"
    except Exception as e:
        logging.error(f"[ERROR] update_teacher_security_deposit: {e}")
        return False, str(e)


def update_teacher(
    teacher_id,
    person_id,
    data,
    contacts,
    subjects,
    qualifications,
    experiences,
    class_sections,
):
    """
    Service method to update an existing teacher's profile.
    """
    from common.utils import (
        validate_is_not_future_date,
        validate_min_age_at_event,
    )

    try:
        salary_amount = float(data["salary"])
    except (ValueError, TypeError):
        return False, "Salary must be a valid number."

    try:
        rating_value = int(data["rating"])
        if rating_value < 1 or rating_value > 5:
            return False, "Rating must be between 1 and 5."
    except (ValueError, TypeError):
        return False, "Rating must be a valid integer between 1 and 5."

    if data["role"] not in TEACHER_ROLES:
        return False, "Invalid teacher role provided."

    try:
        security_amount = float(data.get("security_deposit") or 0)
        if security_amount < 0:
            return False, "Security deposit cannot be negative."
        if security_amount > salary_amount:
            return False, "Security deposit cannot exceed salary."
    except (ValueError, TypeError):
        return False, "Security deposit must be a valid number."

    is_valid_date, date_msg = validate_is_not_future_date(data["joining_date"])
    if not is_valid_date:
        logging.error(f"[ERROR] update_teacher: {date_msg}")
        return False, date_msg

    is_valid_age, age_msg = validate_min_age_at_event(data["dob"], data["joining_date"], 18)
    if not is_valid_age:
        logging.error(f"[ERROR] update_teacher: {age_msg}")
        return False, age_msg

    teacher_payload = {
        "joining_date": data["joining_date"],
        "salary": salary_amount,
        "rating": rating_value,
        "security_deposit": security_amount,
        "role": data["role"],
    }

    try:
        dal_update_teacher_transaction(
            teacher_id,
            person_id,
            teacher_payload,
            data,
            contacts,
            subjects,
            qualifications,
            experiences,
            class_sections,
        )
        return True, "Teacher record updated successfully."
    except Exception as e:
        logging.error(f"[ERROR] update_teacher: {e}")
        return False, str(e)

def remove_teacher(teacher_id, date_of_leaving):
    """
    Marks a teacher as inactive and stores their leaving date.
    """
    from common.utils import validate_is_not_future_date, validate_date_format
    details = get_teacher_details_by_id(teacher_id)
    if not details:
        return False, "Teacher not found."

    if details.get('is_active') == 0:
        return False, "Teacher is already marked as left."

    is_valid_format, error_msg = validate_date_format(date_of_leaving)
    if not is_valid_format:
        return False, error_msg

    is_valid, error_msg = validate_is_not_future_date(date_of_leaving)
    if not is_valid:
        return False, error_msg

    joining_date = details.get('joining_date')
    if joining_date:
        from datetime import datetime
        try:
            join_dt = datetime.strptime(joining_date, "%Y-%m-%d").date()
            leave_dt = datetime.strptime(date_of_leaving, "%Y-%m-%d").date()
            if leave_dt < join_dt:
                return False, "Date of leaving cannot be earlier than the joining date."
        except ValueError:
            pass

    try:
        if dal_mark_teacher_left(teacher_id, date_of_leaving):
            return True, "Teacher marked as left successfully."
        return False, "Unable to update teacher status."
    except Exception as e:
        logging.error(f"[ERROR] remove_teacher: {e}")
        return False, str(e)

def get_teacher_security_funds(teacher_id):
    """
    Service method to get teacher's security funds information.
    Calculates security deposit accumulated from joining date to current date.
    Returns dict with security information or None if teacher not found.
    """
    try:
        security_info = dal_get_teacher_security_funds(teacher_id)
        if not security_info:
            return None
        
        return security_info
    except Exception as e:
        logging.error(f"[ERROR] get_teacher_security_funds: {e}")
        return None
