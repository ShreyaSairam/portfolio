"""
WanderWise — synthetic user ratings for the collaborative-filtering half
of the recommender.

There's no public dataset of real travellers rating these 51 destinations,
so this generates a plausible synthetic ratings matrix: 300 simulated
users, each with a randomly assigned "traveller persona" (a preference
over climate/activities/budget), rating a random subset of destinations
higher when the destination matches their persona and lower otherwise,
with noise added. This is clearly synthetic data used only to demonstrate
the collaborative-filtering component (item-item similarity from
co-rated patterns) alongside the content-based component, which runs on
the real, hand-curated destination attributes in destinations.csv.

Run once:
    python build_ratings.py
"""

import os
import random

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DEST_PATH = os.path.join(HERE, "destinations.csv")
OUT_PATH = os.path.join(HERE, "ratings.csv")

N_USERS = 300
RATINGS_PER_USER = (8, 20)

PERSONAS = [
    {"name": "beach_relaxer", "activities": {"beach", "relaxation"}, "budget_pref": {1, 2}},
    {"name": "culture_history", "activities": {"culture", "history"}, "budget_pref": {2, 3}},
    {"name": "adventure_nature", "activities": {"adventure", "nature", "wildlife"}, "budget_pref": {1, 2, 3}},
    {"name": "foodie_nightlife", "activities": {"food", "nightlife"}, "budget_pref": {2, 3}},
    {"name": "budget_backpacker", "activities": {"culture", "food", "adventure"}, "budget_pref": {1}},
    {"name": "luxury_shopper", "activities": {"shopping", "nightlife", "relaxation"}, "budget_pref": {3}},
]


def score_for_persona(persona, dest_activities, dest_budget):
    overlap = len(persona["activities"] & dest_activities)
    budget_match = dest_budget in persona["budget_pref"]
    base = 2.0 + overlap * 1.1 + (1.0 if budget_match else 0)
    return base


def main():
    random.seed(42)
    dest_df = pd.read_csv(DEST_PATH)
    dest_df["activity_set"] = dest_df["activities"].apply(lambda s: set(s.split("|")))

    rows = []
    for user_id in range(1, N_USERS + 1):
        persona = random.choice(PERSONAS)
        n_ratings = random.randint(*RATINGS_PER_USER)
        sampled = dest_df.sample(n=n_ratings, random_state=user_id)
        for _, dest in sampled.iterrows():
            base = score_for_persona(persona, dest["activity_set"], dest["budget_level"])
            noise = random.gauss(0, 0.7)
            rating = max(1, min(5, round(base + noise)))
            rows.append(
                {
                    "user_id": user_id,
                    "persona": persona["name"],
                    "destination": dest["name"],
                    "rating": rating,
                }
            )

    ratings_df = pd.DataFrame(rows)
    ratings_df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(ratings_df)} synthetic ratings from {N_USERS} users to {OUT_PATH}")


if __name__ == "__main__":
    main()
