# SMS/dal/db_init.py
import sqlite3
import os

DB_PATH = "data/campuscore.db"

def connect_db():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_db():
    """Create all tables according to the original schema."""
    conn = connect_db()
    cursor = conn.cursor()

    # --- NEW: Family Table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS family (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_SSN TEXT NOT NULL UNIQUE,
            family_name TEXT
        )
    ''')

    # Person table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS person (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fathername TEXT NOT NULL,
            mothername TEXT,
            dob DATE NOT NULL,
            address TEXT NOT NULL,
            gender TEXT NOT NULL
        )
    ''')
    
    # Make mothername nullable for existing tables (if it exists and is NOT NULL)
    try:
        cursor.execute("SELECT mothername FROM person LIMIT 1")
        # If we get here, table exists - check if we need to alter it
        # SQLite doesn't support ALTER COLUMN, so we'll handle it gracefully
    except sqlite3.OperationalError:
        pass  # Table doesn't exist yet, will be created with nullable mothername

    # Fullname table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fullname (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            FOREIGN KEY(person_id) REFERENCES person(id) ON DELETE CASCADE
        )
    ''')

    # Contact table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            label TEXT,
            FOREIGN KEY(person_id) REFERENCES person(id) ON DELETE CASCADE
        )
    ''')

    # --- UPDATED: Student Table (Added date_of_leaving and is_active) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            family_id INTEGER,
            date_of_admission DATE,
            date_of_leaving DATE, -- NEW
            monthly_fee DOUBLE,
            annual_fund DOUBLE,
            class TEXT NOT NULL,
            is_active INTEGER DEFAULT 1, -- NEW: 1 for active, 0 for removed
            FOREIGN KEY(person_id) REFERENCES person(id) ON DELETE CASCADE,
            FOREIGN KEY(family_id) REFERENCES family(id) ON DELETE SET NULL
        )
    ''')

    # Add missing columns to existing table if they don't exist
    try:
        cursor.execute("SELECT date_of_leaving FROM student LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE student ADD COLUMN date_of_leaving DATE")
    
    try:
        cursor.execute("SELECT is_active FROM student LIMIT 1")
    except sqlite3.OperationalError:
        # Default existing students to active
        cursor.execute("ALTER TABLE student ADD COLUMN is_active INTEGER DEFAULT 1")


    # Teacher table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            joining_date DATE,
            salary DOUBLE NOT NULL,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            security_deposit DOUBLE DEFAULT 0,
            FOREIGN KEY(person_id) REFERENCES person(id) ON DELETE CASCADE
        )
    ''')
    
    # Add security_deposit column if it doesn't exist
    try:
        cursor.execute("SELECT security_deposit FROM teacher LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE teacher ADD COLUMN security_deposit DOUBLE DEFAULT 0")

    # Subject table (for teacher subjects)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            FOREIGN KEY(teacher_id) REFERENCES teacher(id) ON DELETE CASCADE
        )
    ''')

    # Qualification table (for teacher qualifications)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qualification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            degree TEXT NOT NULL,
            institution TEXT,
            year INTEGER,
            FOREIGN KEY(teacher_id) REFERENCES teacher(id) ON DELETE CASCADE
        )
    ''')

    # Experience table (for teacher experience)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            institution TEXT NOT NULL,
            position TEXT,
            start_date DATE,
            end_date DATE,
            years_of_experience INTEGER,
            FOREIGN KEY(teacher_id) REFERENCES teacher(id) ON DELETE CASCADE
        )
    ''')

    # Class_Section table (for teacher class assignments)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_section (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            section TEXT,
            FOREIGN KEY(teacher_id) REFERENCES teacher(id) ON DELETE CASCADE
        )
    ''')

    # Admin Table with password
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY(person_id) REFERENCES person(id) ON DELETE CASCADE
        )
    ''')

    # Receptionist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receptionist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY(person_id) REFERENCES person(id) ON DELETE CASCADE
        )
    ''')

    # Pending Due table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_due (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            due_type TEXT NOT NULL,
            amount_due DOUBLE NOT NULL,
            due_date DATE NOT NULL,
            status TEXT DEFAULT 'unpaid',
            FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
        )
    ''')

    # --- UPDATED: Payment Record table ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pending_due_id INTEGER NOT NULL,
            amount_paid DOUBLE NOT NULL,
            payment_timestamp DATETIME NOT NULL,
            payment_mode TEXT,
            received_by_user TEXT NOT NULL,
            FOREIGN KEY(pending_due_id) REFERENCES pending_due(id) ON DELETE CASCADE
        )
    ''')

    # Check if admin exists
    cursor.execute("SELECT id FROM admin LIMIT 1")
    if cursor.fetchone() is None:
        # Insert default admin
        cursor.execute("""
            INSERT INTO person (fathername, mothername, dob, address, gender)
            VALUES (?, ?, ?, ?, ?)
        """, ("AdminFather", "AdminMother", "1970-01-01", "Admin Address", "Male"))
        person_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO fullname (person_id, first_name, middle_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (person_id, "Admin", None, "User"))

        cursor.execute("""
            INSERT INTO admin (person_id, password)
            VALUES (?, ?)
        """, (person_id, "admin123"))


    conn.commit()
    conn.close()