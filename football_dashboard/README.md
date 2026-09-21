# Football Analytics Dashboard

Streamlit dashboard on real [StatsBomb open event data](https://github.com/statsbomb/open-data)
covering all seven of France's matches at the 2018 World Cup (which they
won), inspired by that run.

## Tabs

- **Team comparison** — France's results by stage, expected goals (xG) per match
- **Shot map** — every shot in a selected match, plotted on a pitch, sized by xG, goals starred
- **Player explorer** — goals, xG, shots and pass accuracy per player across the tournament
- **Heatmaps** — pass-location density for a chosen player in a chosen match

## Setup

```bash
# from the repo root, if not already done:
bash scripts/fetch_raw_data.sh
python prepare_data.py   # builds data/*.csv from the raw event JSON
streamlit run app.py
```

## How it's built

`prepare_data.py` reads the raw per-match StatsBomb event JSON
(`../data/raw_events/*.json`, ~20MB total, not committed — see
`scripts/fetch_raw_data.sh`) and condenses it into four small CSVs in
`data/`: `matches.csv`, `shots.csv`, `passes.csv`, `player_match_stats.csv`.
`app.py` only ever reads those CSVs, so the dashboard itself starts
instantly and never re-parses the raw JSON.

xG (expected goals) values are StatsBomb's own model output, included in
the open data — not computed here.
