import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            state TEXT,
            score INTEGER,
            updated_at TEXT,
            is_premium INTEGER DEFAULT 0,
            premium_until TEXT,
            morning_hour INTEGER DEFAULT 6,
            evening_hour INTEGER DEFAULT 18
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_story (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            answer TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            entry TEXT,
            response TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            state TEXT,
            score INTEGER,
            analysis TEXT,
            story TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnosis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            state TEXT,
            score INTEGER,
            timestamp TEXT
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
    cursor.execute('INSERT INTO diagnosis_log (user_id, state, score, timestamp) VALUES (?, ?, ?, ?)',
                   (user_id, state, score, now))
    conn.commit()
    conn.close()


def get_user_state(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT state, score, updated_at, is_premium, morning_hour, evening_hour FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_user_answer(user_id: int, question: str, answer: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_story (user_id, question, answer, timestamp) VALUES (?, ?, ?, ?)',
                   (user_id, question, answer, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_user_story(user_id: int) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT question, answer FROM user_story WHERE user_id = ? ORDER BY id', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"q": row["question"], "a": row["answer"]} for row in rows]


def clear_user_story(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_story WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def activate_premium(user_id: int, days: int = 365):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    until = (datetime.now() + timedelta(days=days)).isoformat()
    cursor.execute('UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?', (until, user_id))
    conn.commit()
    conn.close()
    return True


def is_premium(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_premium, premium_until FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["is_premium"]:
        try:
            if datetime.fromisoformat(row["premium_until"]) > datetime.now():
                return True
        except (ValueError, TypeError):
            return False
    return False


def set_user_time(user_id: int, morning: int, evening: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, morning_hour, evening_hour)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            morning_hour = excluded.morning_hour,
            evening_hour = excluded.evening_hour
    ''', (user_id, morning, evening))
    conn.commit()
    conn.close()


def get_all_users_with_times():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, state, morning_hour, evening_hour FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_diary_entry(user_id: int, entry: str, response: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO diary (user_id, entry, response, timestamp) VALUES (?, ?, ?, ?)',
                   (user_id, entry, response, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_last_entries(user_id: int, limit: int = 3):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, entry, response, timestamp FROM diary WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_entry_by_id(entry_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT entry, response, timestamp FROM diary WHERE id = ? AND user_id = ?', (entry_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_analysis(user_id: int, state: str, score: int, analysis: str, story: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_analysis (user_id, state, score, analysis, story, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                   (user_id, state, score, analysis, story, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_last_analysis(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT state, score, analysis, story, timestamp FROM user_analysis WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_analysis_count(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM user_analysis WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_diagnosis_log(user_id: int, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT state, score, timestamp FROM diagnosis_log WHERE user_id = ? ORDER BY id DESC LIMIT ?', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_diary_count(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as cnt FROM diary WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["cnt"] if row else 0
