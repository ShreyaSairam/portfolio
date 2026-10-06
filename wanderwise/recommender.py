"""
WanderWise — hybrid recommendation engine.

Two components, blended:

1. Content-based: destinations are vectorised from their real attributes
   (activities as multi-hot tags, climate as one-hot, budget level, and
   cost scaled) and compared to a user's stated preferences via cosine
   similarity.

2. Collaborative: an item-item similarity matrix built from the synthetic
   ratings in data/ratings.csv (see data/build_ratings.py for how and why
   that data is synthetic) using cosine similarity over each
   destination's rating vector across users. Given a destination the user
   likes, this surfaces others that similar travellers also rated highly.

get_recommendations() blends both: content score from stated preferences,
plus a collaborative boost from any destinations the user says they've
enjoyed before.
"""

import os

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer, MinMaxScaler

HERE = os.path.dirname(os.path.abspath(__file__))
DEST_PATH = os.path.join(HERE, "data", "destinations.csv")
RATINGS_PATH = os.path.join(HERE, "data", "ratings.csv")

ALL_ACTIVITIES = [
    "beach", "adventure", "culture", "nightlife", "nature",
    "food", "relaxation", "history", "shopping", "wildlife",
]
ALL_CLIMATES = ["Tropical", "Temperate", "Cold", "Mediterranean", "Arid"]


def load_destinations():
    df = pd.read_csv(DEST_PATH)
    df["activity_list"] = df["activities"].apply(lambda s: s.split("|"))
    return df


def load_ratings():
    return pd.read_csv(RATINGS_PATH)


def build_content_matrix(dest_df):
    mlb = MultiLabelBinarizer(classes=ALL_ACTIVITIES)
    activity_matrix = mlb.fit_transform(dest_df["activity_list"])

    climate_dummies = pd.get_dummies(dest_df["climate"]).reindex(
        columns=ALL_CLIMATES, fill_value=0
    ).values

    budget_scaled = MinMaxScaler().fit_transform(dest_df[["budget_level"]])

    feature_matrix = np.hstack([activity_matrix, climate_dummies, budget_scaled])
    return feature_matrix, mlb


def build_item_item_similarity(ratings_df, dest_names):
    pivot = ratings_df.pivot_table(
        index="destination", columns="user_id", values="rating", fill_value=0
    )
    pivot = pivot.reindex(dest_names, fill_value=0)
    sim = cosine_similarity(pivot.values)
    return pd.DataFrame(sim, index=dest_names, columns=dest_names)


def build_user_vector(activities, climate, budget_level):
    activity_vec = [1 if a in activities else 0 for a in ALL_ACTIVITIES]
    climate_vec = [1 if c == climate else 0 for c in ALL_CLIMATES]
    budget_vec = [(budget_level - 1) / 2]  # scale 1-3 to 0-1
    return np.array(activity_vec + climate_vec + budget_vec).reshape(1, -1)


def get_recommendations(
    activities,
    climate,
    budget_level,
    liked_destinations=None,
    top_n=8,
    collab_weight=0.35,
):
    """
    activities: list of tag strings the user wants (subset of ALL_ACTIVITIES)
    climate: one of ALL_CLIMATES
    budget_level: 1 (budget), 2 (mid-range), 3 (luxury)
    liked_destinations: optional list of destination names the user has
        enjoyed before, used for the collaborative-filtering boost
    """
    dest_df = load_destinations()
    ratings_df = load_ratings()

    feature_matrix, _ = build_content_matrix(dest_df)
    user_vec = build_user_vector(activities, climate, budget_level)
    content_scores = cosine_similarity(user_vec, feature_matrix)[0]

    collab_scores = np.zeros(len(dest_df))
    if liked_destinations:
        sim_df = build_item_item_similarity(ratings_df, dest_df["name"].tolist())
        valid_liked = [d for d in liked_destinations if d in sim_df.index]
        if valid_liked:
            collab_scores = sim_df.loc[valid_liked].mean(axis=0).reindex(
                dest_df["name"]
            ).fillna(0).values

    if collab_scores.max() > 0:
        collab_scores = collab_scores / collab_scores.max()

    final_scores = (1 - collab_weight) * content_scores + collab_weight * collab_scores

    result = dest_df.copy()
    result["content_score"] = content_scores
    result["collab_score"] = collab_scores
    result["match_score"] = final_scores

    if liked_destinations:
        result = result[~result["name"].isin(liked_destinations)]

    result = result.sort_values("match_score", ascending=False).head(top_n)
    return result[
        [
            "name", "country", "region", "climate", "budget_level",
            "avg_daily_cost_usd", "best_season", "activities", "lat", "lon",
            "match_score", "content_score", "collab_score",
        ]
    ].reset_index(drop=True)
