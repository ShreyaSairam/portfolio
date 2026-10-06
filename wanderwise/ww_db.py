"""
WanderWise SQLite store: user accounts and saved destinations.

Passwords are never stored. Each user gets a random salt and a
PBKDF2-SHA256 hash (200,000 iterations), checked in constant time.
"""

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "wanderwise.db")
ITERATIONS = 200_000


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS favourites (
            user_id INTEGER NOT NULL REFERENCES users(id),
            destination TEXT NOT NULL,
            saved_at TEXT NOT NULL,
            PRIMARY KEY (user_id, destination)
        );
        """
    )
    return conn


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)


def create_user(username, password):
    """Returns (ok, message)."""
    username = username.strip().lower()
    if len(username) < 3:
        return False, "Usernames need at least 3 characters."
    if len(password) < 6:
        return False, "Passwords need at least 6 characters."
    salt = os.urandom(16)
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, salt, _hash(password, salt), datetime.now().isoformat(timespec="seconds")),
            )
    except sqlite3.IntegrityError:
        return False, "That username is taken."
    return True, "Account created."


def check_login(username, password):
    """Returns the user id, or None if the details are wrong."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, salt, password_hash FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
    if row and hmac.compare_digest(row[2], _hash(password, row[1])):
        return row[0]
    return None


def toggle_favourite(user_id, destination):
    with _connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM favourites WHERE user_id = ? AND destination = ?", (user_id, destination)
        ).fetchone()
        if exists:
            conn.execute("DELETE FROM favourites WHERE user_id = ? AND destination = ?", (user_id, destination))
            return False
        conn.execute(
            "INSERT INTO favourites (user_id, destination, saved_at) VALUES (?, ?, ?)",
            (user_id, destination, datetime.now().isoformat(timespec="seconds")),
        )
        return True


def favourites(user_id):
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT destination, saved_at FROM favourites WHERE user_id = ? ORDER BY saved_at DESC",
            conn,
            params=(user_id,),
        )
