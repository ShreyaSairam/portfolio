"""SQLite log of every SignSpeak prediction (source, letter, confidence, time)."""

import os
import sqlite3
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "signspeak.db")


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS predictions (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               created_at TEXT NOT NULL,
               source TEXT NOT NULL,
               letter TEXT NOT NULL,
               confidence REAL NOT NULL
           )"""
    )
    return conn


def log_prediction(source, letter, confidence):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO predictions (created_at, source, letter, confidence) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), source, letter, round(confidence, 3)),
        )


def recent(limit=10):
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT created_at AS time, source, letter, confidence "
            "FROM predictions ORDER BY id DESC LIMIT ?",
            conn,
            params=(limit,),
        )


def counts():
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT letter, COUNT(*) AS times FROM predictions GROUP BY letter ORDER BY times DESC",
            conn,
        )
