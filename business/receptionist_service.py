# SMS/business/receptionist_service.py
from dal.receptionist_dal import dal_add_receptionist_transaction
import logging

logging.basicConfig(level=logging.INFO)

def add_receptionist(fathername, mothername, dob, address, gender,
                      first_name, middle_name, last_name,
                      password, contacts):
    """
    Service method: Handles business logic and delegates persistence to DAL.

    contacts: list of dicts with keys: type ('email' or 'phone'), value, label
    """
    # 1. Business Validation (retained from original core)
    if not contacts or all(c.get('type') != 'phone' for c in contacts):
        raise ValueError("At least one phone number must be provided.")

    # 2. Prepare DAL data structures
    person_data = (fathername, mothername, dob, address, gender)
    fullname_data = (first_name, middle_name, last_name)

    # 3. Delegate Transaction to DAL
    try:
        dal_add_receptionist_transaction(person_data, fullname_data, contacts, password)
        return True
    except Exception as e:
        logging.error(f"Error adding receptionist: {e}")
        raise e