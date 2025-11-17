# SMS/dal/receptionist_dal.py
from dal.db_init import connect_db

def dal_add_receptionist_transaction(person_data, fullname_data, contacts, password):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # 1. Insert into person
        cursor.execute("""
            INSERT INTO person (fathername, mothername, dob, address, gender)
            VALUES (?, ?, ?, ?, ?)
        """, person_data)
        person_id = cursor.lastrowid

        # 2. Insert into fullname
        cursor.execute("""
            INSERT INTO fullname (person_id, first_name, middle_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (person_id,) + fullname_data)

        # 3. Insert all contacts
        for contact in contacts:
            ctype = contact.get('type')
            value = contact.get('value')
            label = contact.get('label', 'primary')
            cursor.execute("""
                INSERT INTO contact (person_id, type, value, label)
                VALUES (?, ?, ?, ?)
            """, (person_id, ctype, value, label))

        # 4. Insert into receptionist with plain text password
        cursor.execute("""
            INSERT INTO receptionist (person_id, password)
            VALUES (?, ?)
        """, (person_id, password))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()