"""
Genetic testing tool SQLite store.

On first run the processed HPO CSVs (built by prepare_data.py) are loaded
into genomics.db, with indexes on the lookup columns. The app then reads
from SQL, and every case a GP runs is logged to the searches table.
"""

import json
import os
import sqlite3
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
DB_PATH = os.path.join(HERE, "genomics.db")
TABLES = ["hpo_terms", "disease_symptoms", "disease_genes"]


def _connect():
    conn = sqlite3.connect(DB_PATH)
    have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not set(TABLES) <= have:
        for t in TABLES:
            pd.read_csv(os.path.join(DATA_DIR, f"{t}.csv")).to_sql(t, conn, if_exists="replace", index=False)
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS ix_ds_hpo ON disease_symptoms(hpo_id);
            CREATE INDEX IF NOT EXISTS ix_ds_disease ON disease_symptoms(disease_id);
            CREATE INDEX IF NOT EXISTS ix_dg_disease ON disease_genes(disease_id);
            """
        )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS searches (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               created_at TEXT NOT NULL,
               symptoms TEXT NOT NULL,
               top_disease TEXT,
               recommendation TEXT
           )"""
    )
    return conn


def load_tables():
    with _connect() as conn:
        return tuple(pd.read_sql_query(f"SELECT * FROM {t}", conn) for t in TABLES)


def log_search(symptom_names, top_disease, recommendation):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO searches (created_at, symptoms, top_disease, recommendation) VALUES (?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(symptom_names), top_disease, recommendation),
        )


def recent_searches(limit=8):
    with _connect() as conn:
        df = pd.read_sql_query(
            "SELECT created_at AS time, symptoms, top_disease, recommendation "
            "FROM searches ORDER BY id DESC LIMIT ?",
            conn,
            params=(limit,),
        )
    df["symptoms"] = df["symptoms"].apply(lambda s: ", ".join(json.loads(s)))
    return df
