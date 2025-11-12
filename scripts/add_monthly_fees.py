# scripts/add_monthly_fees.py
import sqlite3
import os
from datetime import datetime

# Adjust path to go up one level (from scripts to SMS) and then to data
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'campuscore.db')

def connect_db():
    return sqlite3.connect(DB_PATH)

def add_monthly_fees_for_all_students():
    """
    Adds the default monthly fee to all students' pending dues.
    
    This is "idempotent" (safe to run multiple times):
    It only adds fees once for the current calendar month using a specific name
    (e.g., "Monthly Fee - November 2025").
    """
    print(f"[{datetime.now()}] Running monthly fee check...")
    
    today = datetime.now()
    conn = connect_db()
    cursor = conn.cursor()
    
    # --- FIX: Create a specific name for this month's fee ---
    # e.g., "Monthly Fee - November 2025"
    current_month_year = today.strftime("%B %Y")
    specific_due_type = f"Monthly Fee - {current_month_year}"
    
    try:
        # --- FIX: Check if this *specific* due type already exists for any student ---
        cursor.execute("""
            SELECT 1 
            FROM pending_due 
            WHERE due_type = ?
            LIMIT 1
        """, (specific_due_type,))
        
        if cursor.fetchone():
            print(f"Fees for {current_month_year} (as '{specific_due_type}') have already been added. No action taken.")
            return

        # --- If no fees found for this month, proceed to add them ---
        print(f"No fees found for {current_month_year}. Proceeding to add them as '{specific_due_type}'...")
        
        # Get all students and their fees
        cursor.execute("SELECT id, monthly_fee FROM student")
        students = cursor.fetchall()
        
        if not students:
            print("No students found.")
            return
            
        # Prepare due date (e.g., the 10th of the current month)
        due_date = today.strftime('%Y-%m-10')
        dues_to_add = []
        
        for student in students:
            student_id, monthly_fee = student
            if monthly_fee > 0:
                dues_to_add.append(
                    # --- FIX: Use the new specific due type ---
                    (student_id, specific_due_type, monthly_fee, due_date, 'unpaid')
                )
        
        # Insert all new dues in a single transaction
        cursor.executemany("""
            INSERT INTO pending_due (student_id, due_type, amount_due, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, dues_to_add)
        
        conn.commit()
        print(f"Successfully added monthly fees for {len(dues_to_add)} students.")

    except Exception as e:
        print(f"[ERROR] Failed to add monthly fees: {e}")
        conn.rollback()
    finally:
        conn.close()

# This allows you to run the file directly
if __name__ == "__main__":
    add_monthly_fees_for_all_students()