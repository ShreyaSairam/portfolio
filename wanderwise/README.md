# WanderWise: AI Travel Recommender

Tell it what you like doing, the climate and your budget. It ranks 51 destinations and adds live context.

- **Hybrid recommender** (`recommender.py`): content-based matching (cosine similarity between your preferences and each destination's activities, climate and budget) blended with item-item collaborative filtering from traveller ratings.
- **Live weather** (`ww_services.py`): current conditions and a 3-day outlook for where you are and for every match, from Open-Meteo. No key needed; cached for 15 minutes.
- **Your location**: the browser's GPS (with permission) or a city you pick, for distance and rough flying time (haversine distance at 800 km/h plus 45 minutes).
- **Chat assistant**: ask about any match. Answers come from Google Gemini when a `GOOGLE_API_KEY` is set (Streamlit secrets or environment). Without one, it answers from the trip facts and labels the answer as offline.
- **Accounts and favourites** (`ww_db.py`): SQLite, with salted PBKDF2-SHA256 password hashes (200,000 iterations), never plain passwords.

## Data

- `data/destinations.csv`: 51 hand-curated destinations with coordinates (`data/build_destinations.py`).
- `data/ratings.csv`: simulated traveller ratings (`data/build_ratings.py`), since real ratings aren't openly available. The collaborative signal is a demonstration of the technique.

## Run

```bash
streamlit run app.py
```

For Gemini answers: `export GOOGLE_API_KEY=...` or add it to `.streamlit/secrets.toml`.
