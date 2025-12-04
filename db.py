# db.py
import sqlite3
from datetime import date
from typing import List, Optional
from config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pill_name TEXT NOT NULL,
            time_str TEXT NOT NULL,   -- 'HH:MM'
            days TEXT NOT NULL,       -- 'daily' or '0,2,4'
            last_sent_date TEXT       -- 'YYYY-MM-DD' or NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_id INTEGER NOT NULL,
            sent_at TEXT NOT NULL,        -- ISO datetime
            action TEXT NOT NULL,         -- 'sent', 'taken', 'snooze_15', etc.
            FOREIGN KEY(reminder_id) REFERENCES reminders(id)
        )
    """)

    conn.commit()
    conn.close()


# --- CRUD helpers ---

def create_reminder(user_id: int, pill_name: str, time_str: str, days: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (user_id, pill_name, time_str, days, last_sent_date) "
        "VALUES (?, ?, ?, ?, NULL)",
        (user_id, pill_name, time_str, days),
    )
    conn.commit()
    reminder_id = cur.lastrowid
    conn.close()
    return reminder_id


def get_user_reminders(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, pill_name, time_str, days FROM reminders "
        "WHERE user_id = ? ORDER BY time_str",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_reminder(user_id: int, reminder_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM reminders WHERE id = ? AND user_id = ?",
        (reminder_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_reminder_by_id(reminder_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_reminder(user_id: int, reminder_id: int) -> Optional[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT pill_name FROM reminders WHERE id = ? AND user_id = ?",
        (reminder_id, user_id),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    cur.execute(
        "DELETE FROM reminders WHERE id = ? AND user_id = ?",
        (reminder_id, user_id),
    )
    conn.commit()
    conn.close()
    return row["pill_name"]


def update_reminder(reminder_id: int, time_str: str, days: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reminders SET time_str = ?, days = ?, last_sent_date = NULL "
        "WHERE id = ?",
        (time_str, days, reminder_id),
    )
    conn.commit()
    conn.close()


def get_reminders_for_time(time_str: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, pill_name, days, last_sent_date "
        "FROM reminders WHERE time_str = ?",
        (time_str,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def set_last_sent_today(reminder_id: int) -> None:
    today_str = date.today().isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reminders SET last_sent_date = ? WHERE id = ?",
        (today_str, reminder_id),
    )
    conn.commit()
    conn.close()


def insert_history(reminder_id: int, sent_at: str, action: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (reminder_id, sent_at, action) VALUES (?, ?, ?)",
        (reminder_id, sent_at, action),
    )
    conn.commit()
    conn.close()


def get_recent_history(user_id: int, limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT h.sent_at, h.action, r.pill_name
        FROM history h
        JOIN reminders r ON r.id = h.reminder_id
        WHERE r.user_id = ?
        ORDER BY h.sent_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
