# SMS/business/complaint_service.py
from dal.complaint_dal import (
    dal_add_complaint,
    dal_get_complaints_by_teacher,
    dal_get_complaint_count_by_teacher,
    dal_get_teacher_leaderboard
)
from common.utils import validate_is_not_future_date, validate_date_format
import logging

logging.basicConfig(level=logging.INFO)


def add_complaint(teacher_id, complaint_text, complaint_date, registered_by=None):
    """
    Service method to add a complaint against a teacher.
    Returns (success: bool, message: str)
    """
    if not complaint_text or not complaint_text.strip():
        return False, "Complaint text cannot be empty."

    is_valid_format, error_msg = validate_date_format(complaint_date)
    if not is_valid_format:
        return False, error_msg

    is_valid, error_msg = validate_is_not_future_date(complaint_date)
    if not is_valid:
        return False, error_msg

    try:
        dal_add_complaint(teacher_id, complaint_text.strip(), complaint_date, registered_by)
        return True, "Complaint registered successfully."
    except Exception as e:
        logging.error(f"[ERROR] add_complaint: {e}")
        return False, str(e)


def get_complaints_by_teacher(teacher_id):
    """
    Service method to get all complaints for a teacher.
    Returns list of complaint dictionaries.
    """
    try:
        return dal_get_complaints_by_teacher(teacher_id)
    except Exception as e:
        logging.error(f"[ERROR] get_complaints_by_teacher: {e}")
        return []


def get_complaint_count_by_teacher(teacher_id):
    """
    Service method to get complaint count for a teacher.
    Returns integer count.
    """
    try:
        return dal_get_complaint_count_by_teacher(teacher_id)
    except Exception as e:
        logging.error(f"[ERROR] get_complaint_count_by_teacher: {e}")
        return 0


def get_teacher_leaderboard():
    """
    Service method to get teacher leaderboard ranked by complaint count.
    Returns list of teacher dictionaries with complaint counts.
    Teachers with no complaints get rank 5, others ranked by complaint count.
    """
    try:
        teachers = dal_get_teacher_leaderboard()
        # Calculate rank: 5 for no complaints, decreasing as complaints increase
        for teacher in teachers:
            complaint_count = teacher.get('complaint_count', 0)
            if complaint_count == 0:
                teacher['rank'] = 5
            elif complaint_count == 1:
                teacher['rank'] = 4
            elif complaint_count == 2:
                teacher['rank'] = 3
            elif complaint_count == 3:
                teacher['rank'] = 2
            else:
                teacher['rank'] = 1
        return teachers
    except Exception as e:
        logging.error(f"[ERROR] get_teacher_leaderboard: {e}")
        return []

