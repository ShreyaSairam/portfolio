"""
Football SQLite store.

Builds football.db from the processed StatsBomb CSVs on first run:

  matches(match_id, date, stage, home_team, away_team, home_score, away_score, stadium)
  teams(team)
  players(player, team)
  events(match_id, event_type, player, team, minute, x, y, outcome, xg, is_goal, detail)
  player_match_stats(match_id, player, team, passes, passes_complete, shots, goals, xg, pass_accuracy)

Shots and passes share one events table, which is how event data is
usually stored. The dashboard reads everything back with SQL, and the
SQL tab runs read-only queries against the same file.
"""

import os
import sqlite3

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
DB_PATH = os.path.join(HERE, "football.db")


def build():
    m = pd.read_csv(os.path.join(DATA_DIR, "matches.csv"))
    shots = pd.read_csv(os.path.join(DATA_DIR, "shots.csv"))
    passes = pd.read_csv(os.path.join(DATA_DIR, "passes.csv"))
    stats = pd.read_csv(os.path.join(DATA_DIR, "player_match_stats.csv"))
    events = pd.concat(
        [
            shots.assign(event_type="Shot", detail=shots["body_part"] + " · " + shots["shot_type"])[
                ["match_id", "event_type", "player", "team", "minute", "second", "x", "y", "end_x", "end_y",
                 "outcome", "xg", "is_goal", "detail", "body_part", "technique", "shot_type"]
            ],
            passes.assign(event_type="Pass", detail=passes["pass_type"], xg=None, is_goal=None)[
                ["match_id", "event_type", "player", "team", "minute", "x", "y", "outcome", "xg", "is_goal",
                 "detail", "pass_type"]
            ],
        ],
        ignore_index=True,
    )
    tmp = DB_PATH + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    with sqlite3.connect(tmp) as conn:
        m.to_sql("matches", conn, index=False)
        pd.DataFrame({"team": sorted(set(m["home_team"]) | set(m["away_team"]))}).to_sql("teams", conn, index=False)
        stats[["player", "team"]].drop_duplicates().to_sql("players", conn, index=False)
        events.to_sql("events", conn, index=False)
        stats.to_sql("player_match_stats", conn, index=False)
        conn.executescript(
            """
            CREATE INDEX ix_events_match ON events(match_id, event_type);
            CREATE INDEX ix_events_player ON events(player);
            """
        )
    os.replace(tmp, DB_PATH)


def ensure():
    if not os.path.exists(DB_PATH):
        build()


def query(sql, params=()):
    ensure()
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def load_all():
    """The four frames the dashboard tabs use, read back from SQL."""
    matches = query("SELECT * FROM matches ORDER BY date")
    shots = query(
        """SELECT match_id, player, team, minute, second, x, y, end_x, end_y, body_part, technique,
                  shot_type, outcome, xg, CAST(is_goal AS INTEGER) = 1 AS is_goal
           FROM events WHERE event_type = 'Shot'"""
    )
    shots["is_goal"] = shots["is_goal"].astype(bool)
    passes = query(
        "SELECT match_id, player, team, minute, x, y, outcome, pass_type FROM events WHERE event_type = 'Pass'"
    )
    stats = query("SELECT * FROM player_match_stats")
    return matches, shots, passes, stats


def read_only(sql):
    """Runs one SELECT statement on a read-only connection. Raises ValueError otherwise."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned.lower().startswith(("select", "with")) or ";" in cleaned:
        raise ValueError("Only a single SELECT query is allowed here.")
    ensure()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(cleaned + " LIMIT 500" if "limit" not in cleaned.lower() else cleaned, conn)
    finally:
        conn.close()


SAMPLE_QUERIES = {
    "Top scorers by xG": """SELECT player, team, ROUND(SUM(xg), 2) AS total_xg, SUM(is_goal) AS goals,
       COUNT(*) AS shots
FROM events
WHERE event_type = 'Shot'
GROUP BY player, team
ORDER BY total_xg DESC
LIMIT 10""",
    "France's results": """SELECT date, stage,
       CASE WHEN home_team = 'France' THEN away_team ELSE home_team END AS opponent,
       CASE WHEN home_team = 'France' THEN home_score ELSE away_score END AS france,
       CASE WHEN home_team = 'France' THEN away_score ELSE home_score END AS against
FROM matches
ORDER BY date""",
    "Most accurate passers (100+ passes)": """SELECT player, team, SUM(passes) AS passes,
       ROUND(100.0 * SUM(passes_complete) / SUM(passes), 1) AS accuracy_pct
FROM player_match_stats
GROUP BY player, team
HAVING SUM(passes) >= 100
ORDER BY accuracy_pct DESC
LIMIT 10""",
    "Goals by body part": """SELECT body_part, COUNT(*) AS goals
FROM events
WHERE event_type = 'Shot' AND is_goal = 1
GROUP BY body_part
ORDER BY goals DESC""",
}
