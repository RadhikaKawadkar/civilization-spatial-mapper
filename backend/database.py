import sqlite3
import os
from pathlib import Path
import hashlib

DB_PATH = Path(__file__).parent / "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS custom_civilizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            start_year INTEGER,
            end_year INTEGER,
            region TEXT,
            resource_density REAL,
            knowledge_density REAL,
            military_strength REAL,
            added_by_id INTEGER,
            FOREIGN KEY (added_by_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(name: str, email: str, password: str):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password))
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_custom_civilization(name, lat, lon, region, resource, knowledge, military, added_by_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO custom_civilizations 
            (name, lat, lon, start_year, end_year, region, resource_density, knowledge_density, military_strength, added_by_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, lat, lon, 0, 0, region, resource, knowledge, military, added_by_id)
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_custom_civilizations():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT c.*, u.name as added_by_name 
        FROM custom_civilizations c
        LEFT JOIN users u ON c.added_by_id = u.id
    """)
    rows = c.fetchall()
    conn.close()
    return rows
