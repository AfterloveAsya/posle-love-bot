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
