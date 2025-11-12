from core.db_init import connect_db

def add_receptionist(fathername, mothername, dob, address, gender,
                      first_name, middle_name, last_name,
                      password, contacts):
    """
    Add a new receptionist.

    contacts: list of dicts with keys: type ('email' or 'phone'), value, label
    """
    if not contacts or all(c.get('type') != 'phone' for c in contacts):
        raise ValueError("At least one phone number must be provided.")

    conn = connect_db()
    cursor = conn.cursor()

    # Insert into person
    cursor.execute("""
        INSERT INTO person (fathername, mothername, dob, address, gender)
        VALUES (?, ?, ?, ?, ?)
    """, (fathername, mothername, dob, address, gender))
    person_id = cursor.lastrowid

    # Insert into fullname
    cursor.execute("""
        INSERT INTO fullname (person_id, first_name, middle_name, last_name)
        VALUES (?, ?, ?, ?)
    """, (person_id, first_name, middle_name, last_name))

    # Insert all contacts
    for contact in contacts:
        ctype = contact.get('type')
        value = contact.get('value')
        label = contact.get('label', 'primary')
        cursor.execute("""
            INSERT INTO contact (person_id, type, value, label)
            VALUES (?, ?, ?, ?)
        """, (person_id, ctype, value, label))

    # Insert into receptionist with plain text password
    cursor.execute("""
        INSERT INTO receptionist (person_id, password)
        VALUES (?, ?)
    """, (person_id, password))

    conn.commit()
    conn.close()
