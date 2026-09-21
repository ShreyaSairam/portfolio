# WanderWise — Travel Recommendation System

A hybrid recommender: content-based matching on your stated preferences,
blended with a collaborative-filtering signal from simulated traveller
ratings.

## Setup

```bash
cd data && python build_destinations.py && python build_ratings.py && cd ..
streamlit run app.py
```

## How it's built

- **Destinations** (`data/destinations.csv`, via `data/build_destinations.py`)
  — 51 real, well-known destinations, hand-curated with genuine attributes
  (climate, typical daily cost, best season, activity mix) from general
  travel knowledge. No open dataset with this kind of attribute mix exists
  publicly, so this is curated reference data rather than fetched from a
  source.
- **Content-based scoring** (`recommender.py`) — destinations are
  vectorised (activities as multi-hot tags, climate one-hot, budget
  scaled) and compared to your stated preferences via cosine similarity.
- **Collaborative-filtering signal** (`data/ratings.csv`, via
  `data/build_ratings.py`) — there's no public dataset of real travellers
  rating these 51 destinations, so this generates *synthetic* ratings from
  300 simulated users, each assigned a "traveller persona" (e.g.
  beach-relaxer, budget-backpacker) that biases their ratings toward
  matching destinations, with noise added. An item-item similarity matrix
  built from this data powers "travellers like you also liked..." —
  clearly a demonstration of the mechanism, not a claim about real travel
  behaviour.
- **Hybrid blend** (`recommender.get_recommendations()`) — final score is
  `(1 - w) * content_score + w * collaborative_score`, where `w` is
  adjustable in the app sidebar, and the collaborative half only kicks in
  once you've told it a destination you've enjoyed before.
