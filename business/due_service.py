# SMS/business/due_service.py
from dal.due_dal import (
    dal_add_manual_due, dal_check_for_due_type, dal_add_specific_monthly_fee,
    dal_get_unpaid_dues_for_student, dal_make_payment_transaction,
    dal_get_all_student_dues_with_summary, dal_get_payments_for_due, dal_get_all_students_for_fees,
    dal_insert_monthly_dues_batch
)
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

def add_manual_due(student_id, due_type, amount, due_date):
    """
    Service method to manually add a new pending due.
    """
    try:
        return dal_add_manual_due(student_id, due_type, amount, due_date)
    except Exception as e:
        logging.error(f"[ERROR] add_manual_due: {e}")
        return False

def check_if_monthly_fee_was_run():
    """
    Service method to check if the monthly fee script has been run for the current month.
    """
    today = datetime.now()
    current_month_year = today.strftime("%B %Y")
    specific_due_type = f"Monthly Fee - {current_month_year}"
    
    try:
        if dal_check_for_due_type(specific_due_type):
            return True, specific_due_type
        else:
            return False, None
    except Exception as e:
        logging.error(f"[ERROR] check_if_monthly_fee_was_run: {e}")
        return False, None

def add_specific_monthly_fee(student_id, fee_amount, due_type_name):
    """
    Service method to directly add a specific monthly fee to a new student.
    """
    today = datetime.now()
    due_date = today.strftime('%Y-%m-10') # Standard due date
    
    try:
        dal_add_specific_monthly_fee(student_id, due_type_name, fee_amount, due_date)
        logging.info(f"Successfully added fee '{due_type_name}' for new student ID: {student_id}")
    except Exception as e:
        logging.error(f"[ERROR] add_specific_monthly_fee: {e}")

def get_unpaid_dues_for_student(student_id):
    """
    Service method to fetch unpaid dues by delegating to DAL.
    """
    try:
        return dal_get_unpaid_dues_for_student(student_id)
    except Exception as e:
        logging.error(f"[ERROR] get_unpaid_dues_for_student: {e}")
        return []

def make_payment(pending_due_id, amount_paid, payment_mode, payment_timestamp, received_by_user):
    """
    Service method to record a payment in a transaction.
    """
    try:
        new_status, new_payment_id = dal_make_payment_transaction(
            pending_due_id, amount_paid, payment_timestamp, payment_mode, received_by_user
        )
        return True, new_status, new_payment_id
    except Exception as e:
        logging.error(f"[ERROR] make_payment transaction failed: {e}")
        return False, str(e), None

def get_all_student_dues_with_summary(student_id):
    """
    Service method to fetch ALL dues with summary.
    """
    try:
        return dal_get_all_student_dues_with_summary(student_id)
    except Exception as e:
        logging.error(f"[ERROR] get_all_student_dues_with_summary: {e}")
        return []

def get_payments_for_due(pending_due_id):
    """
    Service method to fetch all individual payment records.
    """
    try:
        return dal_get_payments_for_due(pending_due_id)
    except Exception as e:
        logging.error(f"[ERROR] get_payments_for_due: {e}")
        return []
        
# --- New Service Function from scripts/add_monthly_fees.py ---
def add_monthly_fees_for_all_students():
    """
    Adds the default monthly fee to all students' pending dues.
    This is "idempotent" (safe to run multiple times).
    """
    print(f"[{datetime.now()}] Running monthly fee check...")
    
    today = datetime.now()
    current_month_year = today.strftime("%B %Y")
    specific_due_type = f"Monthly Fee - {current_month_year}"
    
    try:
        # Check if this *specific* due type already exists
        if dal_check_for_due_type(specific_due_type):
            print(f"Fees for {current_month_year} (as '{specific_due_type}') have already been added. No action taken.")
            return

        # If no fees found for this month, proceed to add them
        print(f"No fees found for {current_month_year}. Proceeding to add them as '{specific_due_type}'...")
        
        # Get all students and their fees from DAL
        students = dal_get_all_students_for_fees()
        
        if not students:
            print("No students found.")
            return
            
        # Prepare due date (e.g., the 10th of the current month)
        due_date = today.strftime('%Y-%m-10')
        dues_to_add = []
        
        for student_id, monthly_fee in students:
            if monthly_fee > 0:
                dues_to_add.append(
                    (student_id, specific_due_type, monthly_fee, due_date, 'unpaid')
                )
        
        # Insert all new dues in a single transaction via DAL
        if dal_insert_monthly_dues_batch(dues_to_add):
            print(f"Successfully added monthly fees for {len(dues_to_add)} students.")

    except Exception as e:
        print(f"[ERROR] Failed to add monthly fees: {e}")