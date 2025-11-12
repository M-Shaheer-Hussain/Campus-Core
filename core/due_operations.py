# SMS/core/due_operations.py
import sqlite3
import os
from core.db_init import connect_db
from datetime import datetime

def add_manual_due(student_id, due_type, amount, due_date):
    """
    Manually adds a new pending due to a specific student.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO pending_due (student_id, due_type, amount_due, due_date, status)
            VALUES (?, ?, ?, ?, 'unpaid')
        """, (student_id, due_type, amount, due_date))
        conn.commit()
        return True
    except Exception as e:
        print(f"[ERROR] add_manual_due: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- NEW FUNCTION ---
def check_if_monthly_fee_was_run():
    """
    Checks if the monthly fee script has been run for the current month.
    Returns (True, "Monthly Fee - [Month] [Year]") if it has.
    Returns (False, None) if it has not.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    today = datetime.now()
    current_month_year = today.strftime("%B %Y")
    specific_due_type = f"Monthly Fee - {current_month_year}"
    
    try:
        cursor.execute("""
            SELECT 1 
            FROM pending_due 
            WHERE due_type = ?
            LIMIT 1
        """, (specific_due_type,))
        
        if cursor.fetchone():
            return True, specific_due_type
        else:
            return False, None
            
    except Exception as e:
        print(f"[ERROR] check_if_monthly_fee_was_run: {e}")
        return False, None
    finally:
        conn.close()

# --- NEW FUNCTION ---
def add_specific_monthly_fee(student_id, fee_amount, due_type_name):
    """
    Directly adds a specific monthly fee to a new student.
    Used when the receptionist confirms adding a fee after the script has run.
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    today = datetime.now()
    due_date = today.strftime('%Y-%m-10') # Standard due date
    
    try:
        cursor.execute("""
            INSERT INTO pending_due (student_id, due_type, amount_due, due_date, status)
            VALUES (?, ?, ?, ?, 'unpaid')
        """, (student_id, due_type_name, fee_amount, due_date))
        conn.commit()
        print(f"Successfully added fee '{due_type_name}' for new student ID: {student_id}")
    except Exception as e:
        print(f"[ERROR] add_specific_monthly_fee: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_student_pending_dues(student_id):
    """Fetches all unpaid dues for a given student ID."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT due_type, amount_due, due_date, status
        FROM pending_due
        WHERE student_id = ? AND status != 'paid'
        ORDER BY due_date ASC
    """
    try:
        cursor.execute(query, (student_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[ERROR] get_student_pending_dues: {e}")
        return []
    finally:
        conn.close()

def get_unpaid_dues_for_student(student_id):
    """
    Fetches all dues for a student that are not fully paid.
    Calculates what has already been paid.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT
            pd.id as pending_due_id,
            pd.due_type,
            pd.amount_due,
            pd.due_date,
            pd.status,
            COALESCE(SUM(pr.amount_paid), 0) as total_paid,
            (pd.amount_due - COALESCE(SUM(pr.amount_paid), 0)) as amount_remaining
        FROM pending_due pd
        LEFT JOIN payment_record pr ON pd.id = pr.pending_due_id
        WHERE pd.student_id = ?
        GROUP BY pd.id, pd.due_type, pd.amount_due, pd.due_date, pd.status
        HAVING pd.status != 'paid' AND amount_remaining > 0
        ORDER BY pd.due_date ASC
    """
    try:
        cursor.execute(query, (student_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[ERROR] get_unpaid_dues_for_student: {e}")
        return []
    finally:
        conn.close()

def make_payment(pending_due_id, amount_paid, payment_mode, payment_timestamp, received_by_user):
    """
    Records a payment for a pending due in a transaction.
    Updates the due's status if fully paid.
    Returns (True, new_status, new_payment_id) on success.
    Returns (False, error_message, None) on failure.
    """
    conn = connect_db()
    cursor = conn.cursor()
    new_payment_id = None
    
    try:
        cursor.execute("BEGIN")
        
        cursor.execute("""
            INSERT INTO payment_record (pending_due_id, amount_paid, payment_timestamp, payment_mode, received_by_user)
            VALUES (?, ?, ?, ?, ?)
        """, (pending_due_id, amount_paid, payment_timestamp, payment_mode, received_by_user))
        
        new_payment_id = cursor.lastrowid
        
        cursor.execute("SELECT amount_due FROM pending_due WHERE id = ?", (pending_due_id,))
        row = cursor.fetchone()
        if not row:
            raise Exception("Pending due not found")
        amount_due = row[0]
        
        cursor.execute("""
            SELECT SUM(amount_paid) 
            FROM payment_record 
            WHERE pending_due_id = ?
        """, (pending_due_id,))
        total_paid = cursor.fetchone()[0]
        
        new_status = 'partially paid'
        if total_paid >= amount_due:
            new_status = 'paid'
            
        cursor.execute("""
            UPDATE pending_due 
            SET status = ? 
            WHERE id = ?
        """, (new_status, pending_due_id))
        
        conn.commit()
        return True, new_status, new_payment_id
        
    except Exception as e:
        print(f"[ERROR] make_payment transaction failed: {e}")
        conn.rollback()
        return False, str(e), None
    finally:
        conn.close()

def get_all_student_dues_with_summary(student_id):
    """
    Fetches ALL dues for a student (paid, unpaid, etc.) and
    calculates their payment summary.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT
            pd.id as pending_due_id,
            pd.due_type,
            pd.amount_due,
            pd.due_date,
            pd.status,
            COALESCE(SUM(pr.amount_paid), 0) as total_paid,
            (pd.amount_due - COALESCE(SUM(pr.amount_paid), 0)) as amount_remaining
        FROM pending_due pd
        LEFT JOIN payment_record pr ON pd.id = pr.pending_due_id
        WHERE pd.student_id = ?
        GROUP BY pd.id, pd.due_type, pd.amount_due, pd.due_date, pd.status
        ORDER BY pd.due_date DESC
    """
    try:
        cursor.execute(query, (student_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[ERROR] get_all_student_dues_with_summary: {e}")
        return []
    finally:
        conn.close()

def get_payments_for_due(pending_due_id):
    """
    Fetches all individual payment records (installments) for a
    single pending due, ordered by date.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT payment_timestamp, amount_paid, payment_mode, received_by_user
        FROM payment_record
        WHERE pending_due_id = ?
        ORDER BY payment_timestamp ASC
    """
    try:
        cursor.execute(query, (pending_due_id,))
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[ERROR] get_payments_for_due: {e}")
        return []
    finally:
        conn.close()