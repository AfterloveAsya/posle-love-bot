import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            state TEXT,
            score INTEGER,
            updated_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            analysis TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            morning_hour INTEGER DEFAULT 6,
            evening_hour INTEGER DEFAULT 18
        )
    ''')
    conn.commit()
    conn.close()

def save_diagnosis(user_id: int, state: str, score: int):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO users (user_id, state, score, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            state = excluded.state,
            score = excluded.score,
            updated_at = excluded.updated_at
    ''', (user_id, state, score, now))
    conn.commit()
    conn.close()

def get_user_state(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT state, score, updated_at FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_diary_entry(user_id: int, text: str, analysis: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO diary (user_id, text, analysis, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, text, analysis, now))
    conn.commit()
    conn.close()

def get_diary_entries(user_id: int, limit: int = 5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT text, analysis, created_at FROM diary
        WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_diagnosis_history(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT state, score, updated_at FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_settings(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT morning_hour, evening_hour FROM settings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"morning_hour": 6, "evening_hour": 18}

def save_settings(user_id: int, morning_hour: int, evening_hour: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO settings (user_id, morning_hour, evening_hour)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            morning_hour = excluded.morning_hour,
            evening_hour = excluded.evening_hour
    ''', (user_id, morning_hour, evening_hour))
    conn.commit()
    conn.close()
