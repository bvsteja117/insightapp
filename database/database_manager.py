# database/database_manager.py
import sqlite3
import os
import time
from contextlib import contextmanager
from config import DATABASE_PATH

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()

def create_tables():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS contractors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        contractor_id TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        address TEXT NOT NULL,
                        aadhaar TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        aadhaar TEXT NOT NULL,
                        address TEXT NOT NULL,
                        contractor_id TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS checkin_checkout (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_name TEXT NOT NULL,
                        checkin_time TEXT,
                        checkout_time TEXT)''')
        conn.commit()

def add_contractor(contractor_details):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO contractors (name, contractor_id, phone, address, aadhaar) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (contractor_details['name'], contractor_details['id'], contractor_details['phone'],
                   contractor_details['address'], contractor_details['aadhaar']))
        conn.commit()

def add_employee(employee_details):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO employees (employee_id, name, phone, aadhaar, address, contractor_id) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (employee_details['employee_id'], employee_details['name'], employee_details['phone'],
                   employee_details['aadhaar'], employee_details['address'], employee_details['contractor_id']))
        conn.commit()

def check_id_exists(table, id_column, id_value):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(f"SELECT 1 FROM {table} WHERE {id_column} = ?", (id_value,))
        return c.fetchone() is not None

def get_all_employees():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM employees")
        return c.fetchall()

def get_all_contractors():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM contractors")
        return c.fetchall()




