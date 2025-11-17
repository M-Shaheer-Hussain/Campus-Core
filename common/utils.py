# SMS/common/utils.py
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime
import re

def show_warning(parent, title, message):
    """A reusable wrapper for QMessageBox.warning."""
    QMessageBox.warning(parent, title, message)

def validate_required_fields(data_dict, required_keys, display_names=None):
    """
    Validates that all specified keys in data_dict have non-empty string values.
    """
    missing_fields = []
    for key in required_keys:
        value = data_dict.get(key)
        if not value or (isinstance(value, str) and not value.strip()):
            display_name = display_names.get(key) if display_names else key.replace('_', ' ').title()
            missing_fields.append(display_name)

    if missing_fields:
        message = f"Please fill the following required fields: {', '.join(missing_fields)}."
        return False, message
    return True, None

def validate_date_format(date_str, format_str="%Y-%m-%d"):
    """
    Validates that a date string is in the specified format.
    """
    if not date_str:
        return False, "Date field cannot be empty."
    if format_str == "%Y-%m-%d" and not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False, "Date must be in YYYY-MM-DD format."
    try:
        datetime.strptime(date_str, format_str)
        return True, None
    except ValueError:
        return False, "Date must be a valid date in YYYY-MM-DD format."


def validate_dob_not_current_year(dob_str, format_str="%Y-%m-%d"):
    """
    Validates that the Date of Birth is not in the current year.
    """
    is_valid, error_msg = validate_date_format(dob_str, format_str)
    if not is_valid:
        return False, error_msg
    try:
        dob_dt = datetime.strptime(dob_str, format_str)
        current_year = datetime.now().year
        if dob_dt.year == current_year:
            return False, "Date of Birth cannot be in the current year."
        return True, None
    except ValueError:
        return False, "An unexpected date error occurred."

def validate_password_length(password, min_length=8):
    """
    Validates that the password meets the minimum length requirement.
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters."
    return True, None
    
def validate_phone_length(phone_number, required_length=11):
    """
    Validates that the phone number is exactly the required length (11 digits).
    """
    digits_only = re.sub(r'\D', '', phone_number)
    if len(digits_only) != required_length:
        return False, f"Phone number must be exactly {required_length} digits long."
    return True, None

def validate_is_float(value_str):
    """
    Validates that a string can be converted to a positive float.
    """
    try:
        value = float(value_str)
        if value < 0:
            return False, "Value cannot be negative."
        return True, None
    except ValueError:
        return False, "Value must be a valid number (e.g., 1500.0)."

def validate_ssn(ssn_str, required_length=9):
    """
    Validates that the SSN is a specific number of digits.
    """
    digits_only = re.sub(r'\D', '', ssn_str)
    if len(digits_only) != required_length:
        return False, f"Family SSN must be exactly {required_length} digits."
    return True, digits_only