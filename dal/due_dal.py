# SMS/dal/due_dal.py
import sqlite3
from dal.db_init import connect_db

def dal_add_manual_due(student_id, due_type, amount, due_date):
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
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_check_for_due_type(specific_due_type):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 1 
            FROM pending_due 
            WHERE due_type = ?
            LIMIT 1
        """, (specific_due_type,))
        return cursor.fetchone() is not None
    finally:
        conn.close()

def dal_add_specific_monthly_fee(student_id, due_type_name, fee_amount, due_date):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pending_due (student_id, due_type, amount_due, due_date, status)
            VALUES (?, ?, ?, ?, 'unpaid')
        """, (student_id, due_type_name, fee_amount, due_date))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_get_all_students_for_fees():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, monthly_fee FROM student")
        return cursor.fetchall()
    finally:
        conn.close()

def dal_insert_monthly_dues_batch(dues_to_add):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.executemany("""
            INSERT INTO pending_due (student_id, due_type, amount_due, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, dues_to_add)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_get_unpaid_dues_for_student(student_id):
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
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_make_payment_transaction(pending_due_id, amount_paid, payment_timestamp, payment_mode, received_by_user):
    conn = connect_db()
    cursor = conn.cursor()
    new_payment_id = None
    try:
        cursor.execute("BEGIN")
        
        # 1. Insert payment record
        cursor.execute("""
            INSERT INTO payment_record (pending_due_id, amount_paid, payment_timestamp, payment_mode, received_by_user)
            VALUES (?, ?, ?, ?, ?)
        """, (pending_due_id, amount_paid, payment_timestamp, payment_mode, received_by_user))
        new_payment_id = cursor.lastrowid
        
        # 2. Get amount due and total paid
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
        
        # 3. Determine new status
        new_status = 'partially paid'
        if total_paid >= amount_due:
            new_status = 'paid'
            
        # 4. Update pending due status
        cursor.execute("""
            UPDATE pending_due 
            SET status = ? 
            WHERE id = ?
        """, (new_status, pending_due_id))
        
        conn.commit()
        return new_status, new_payment_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def dal_get_all_student_dues_with_summary(student_id):
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
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def dal_get_payments_for_due(pending_due_id):
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
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()