# SMS/business/login_service.py
from dal.login_dal import dal_validate_admin, dal_validate_receptionist
import logging

logging.basicConfig(level=logging.INFO)

def validate_admin(username, password):
    """
    Admin username: 'FirstName LastName'
    """
    if " " not in username:
        return False
    first_name, last_name = username.strip().split(" ", 1)
    
    try:
        # Delegation to DAL
        return dal_validate_admin(first_name, last_name, password)
    except Exception as e:
        logging.error(f"Error in validate_admin service: {e}")
        return False


def validate_receptionist(username, password):
    """
    Receptionist username: 'FirstName LastName'
    """
    if " " not in username:
        return False
    first_name, last_name = username.strip().split(" ", 1)

    try:
        # Delegation to DAL
        return dal_validate_receptionist(first_name, last_name, password)
    except Exception as e:
        logging.error(f"Error in validate_receptionist service: {e}")
        return False