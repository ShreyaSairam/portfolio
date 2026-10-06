"""
Attendance SQLite store.

Tables:
  students    the class roster (enrolled subjects)
  check_ins   one row per student per day: time and present/late status

Absent students are not stored. They are everyone on the roster with no
check-in for that date, worked out with a LEFT JOIN.
"""

import os
import sqlite3

import pandas as pd

from roster import ROSTER

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "attendance.db")
CLASS_SIZE = 12  # subjects 1-12 are enrolled in the demo class


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            subject_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS check_ins (
            subject_id INTEGER NOT NULL REFERENCES students(subject_id),
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('present', 'late')),
            PRIMARY KEY (subject_id, date)
        );
        """
    )
    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO students VALUES (?, ?, ?)",
            [(i, ROSTER[i]["name"], ROSTER[i]["department"]) for i in range(1, CLASS_SIZE + 1)],
        )
    return conn


def is_enrolled(subject_id):
    with _connect() as conn:
        return conn.execute("SELECT 1 FROM students WHERE subject_id = ?", (subject_id,)).fetchone() is not None


def check_in(subject_id, date, time, status):
    """Returns the existing row if already checked in that day, else None after inserting."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT time, status FROM check_ins WHERE subject_id = ? AND date = ?", (subject_id, date)
        ).fetchone()
        if row:
            return row
        conn.execute("INSERT INTO check_ins VALUES (?, ?, ?, ?)", (subject_id, date, time, status))
    return None


def day_report(date):
    """Every enrolled student with their status for one date: present, late or absent."""
    with _connect() as conn:
        return pd.read_sql_query(
            """SELECT s.subject_id AS id, s.name, s.department,
                      COALESCE(c.status, 'absent') AS status, COALESCE(c.time, '') AS checked_in
               FROM students s
               LEFT JOIN check_ins c ON c.subject_id = s.subject_id AND c.date = ?
               ORDER BY CASE COALESCE(c.status, 'absent')
                            WHEN 'present' THEN 0 WHEN 'late' THEN 1 ELSE 2 END,
                        c.time, s.subject_id""",
            conn,
            params=(date,),
        )


def history():
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT date, status, COUNT(*) AS students FROM check_ins GROUP BY date, status ORDER BY date",
            conn,
        )


def reset_day(date):
    with _connect() as conn:
        conn.execute("DELETE FROM check_ins WHERE date = ?", (date,))
