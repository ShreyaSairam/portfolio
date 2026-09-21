"""
Data preparation for the France 2018 World Cup analytics dashboard.

Source: StatsBomb Open Data (https://github.com/statsbomb/open-data),
used under StatsBomb's open data license for non-commercial research and
educational use. Raw per-match event JSON files live in ../data/raw_events/
and are condensed here into a handful of small CSVs the Streamlit app
actually reads, so the app never has to parse multi-megabyte JSON at
runtime.

Run this once (or whenever the raw data changes):
    python prepare_data.py
"""

import json
import os
import glob

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "data", "raw_events")
MATCHES_PATH = os.path.join(HERE, "..", "data", "wc2018_matches.json")
OUT_DIR = os.path.join(HERE, "data")
os.makedirs(OUT_DIR, exist_ok=True)

FRANCE_MATCH_IDS = [7546, 7580, 7530, 8649, 8658, 8655, 7563]


def load_matches():
    with open(MATCHES_PATH) as f:
        matches = json.load(f)
    rows = []
    for m in matches:
        if m["match_id"] not in FRANCE_MATCH_IDS:
            continue
        rows.append(
            {
                "match_id": m["match_id"],
                "date": m["match_date"],
                "stage": m["competition_stage"]["name"],
                "home_team": m["home_team"]["home_team_name"],
                "away_team": m["away_team"]["away_team_name"],
                "home_score": m["home_score"],
                "away_score": m["away_score"],
                "stadium": m.get("stadium", {}).get("name", ""),
            }
        )
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df.to_csv(os.path.join(OUT_DIR, "matches.csv"), index=False)
    return df


def load_events_for_match(match_id):
    path = os.path.join(RAW_DIR, f"{match_id}.json")
    with open(path) as f:
        return json.load(f)


def build_shots(matches_df):
    rows = []
    for match_id in matches_df["match_id"]:
        events = load_events_for_match(match_id)
        for e in events:
            if e["type"]["name"] != "Shot":
                continue
            shot = e["shot"]
            loc = e.get("location", [None, None])
            end = shot.get("end_location", [None, None, None])
            rows.append(
                {
                    "match_id": match_id,
                    "player": e["player"]["name"],
                    "team": e["team"]["name"],
                    "minute": e["minute"],
                    "second": e["second"],
                    "x": loc[0],
                    "y": loc[1],
                    "end_x": end[0] if len(end) > 0 else None,
                    "end_y": end[1] if len(end) > 1 else None,
                    "body_part": shot.get("body_part", {}).get("name"),
                    "technique": shot.get("technique", {}).get("name"),
                    "shot_type": shot.get("type", {}).get("name"),
                    "outcome": shot.get("outcome", {}).get("name"),
                    "xg": shot.get("statsbomb_xg"),
                    "is_goal": shot.get("outcome", {}).get("name") == "Goal",
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DIR, "shots.csv"), index=False)
    return df


def build_passes(matches_df):
    """Pass locations, used for player heatmaps / touch maps."""
    rows = []
    for match_id in matches_df["match_id"]:
        events = load_events_for_match(match_id)
        for e in events:
            if e["type"]["name"] != "Pass":
                continue
            loc = e.get("location", [None, None])
            passobj = e.get("pass", {}) or {}
            rows.append(
                {
                    "match_id": match_id,
                    "player": e["player"]["name"] if "player" in e else None,
                    "team": e["team"]["name"],
                    "minute": e["minute"],
                    "x": loc[0],
                    "y": loc[1],
                    "outcome": passobj.get("outcome", {}).get("name", "Complete"),
                    "pass_type": passobj.get("height", {}).get("name"),
                }
            )
    df = pd.DataFrame(rows).dropna(subset=["player"])
    df.to_csv(os.path.join(OUT_DIR, "passes.csv"), index=False)
    return df


def build_player_match_stats(shots_df, passes_df):
    shot_agg = (
        shots_df.groupby(["match_id", "player", "team"])
        .agg(shots=("player", "count"), goals=("is_goal", "sum"), xg=("xg", "sum"))
        .reset_index()
    )
    pass_agg = (
        passes_df.groupby(["match_id", "player", "team"])
        .agg(
            passes=("player", "count"),
            passes_complete=("outcome", lambda s: (s == "Complete").sum()),
        )
        .reset_index()
    )
    merged = pd.merge(
        pass_agg, shot_agg, on=["match_id", "player", "team"], how="outer"
    ).fillna(0)
    merged["pass_accuracy"] = (
        merged["passes_complete"] / merged["passes"].replace(0, pd.NA) * 100
    ).round(1)
    merged.to_csv(os.path.join(OUT_DIR, "player_match_stats.csv"), index=False)
    return merged


def main():
    matches_df = load_matches()
    print(f"Matches: {len(matches_df)}")
    shots_df = build_shots(matches_df)
    print(f"Shots: {len(shots_df)}")
    passes_df = build_passes(matches_df)
    print(f"Passes: {len(passes_df)}")
    stats_df = build_player_match_stats(shots_df, passes_df)
    print(f"Player-match rows: {len(stats_df)}")
    print("Done. CSVs written to", OUT_DIR)


if __name__ == "__main__":
    main()
