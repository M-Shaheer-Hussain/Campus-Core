# SMS/dal/db_connection.py
import sqlite3
import os

DB_PATH = "data/campuscore.db"

def get_connection():
    """Returns a new SQLite connection using the same DB path as db_init."""
    os.makedirs("data", exist_ok=True)  # Ensure folder exists
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # So you can access columns by name
    return conn
