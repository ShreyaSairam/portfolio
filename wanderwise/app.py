"""
WanderWise — Travel Recommendation Dashboard page.

Lets a user set activity preferences, climate, budget and (optionally)
destinations they've enjoyed before, and returns ranked recommendations
from the hybrid content-based + collaborative-filtering engine in
recommender.py.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from recommender import get_recommendations, ALL_ACTIVITIES, ALL_CLIMATES, load_destinations


def main():
    st.set_page_config(page_title="WanderWise", layout="wide")
    st.title("WanderWise — Travel Recommendation System")
    st.caption(
        "Hybrid recommender over 51 hand-curated destinations: content-based "
        "matching on your stated preferences, blended with a collaborative-"
        "filtering signal from simulated traveller ratings."
    )

    dest_df = load_destinations()

    with st.sidebar:
        st.header("Your preferences")
        activities = st.multiselect(
            "What do you want to do?",
            ALL_ACTIVITIES,
            default=["beach", "relaxation"],
        )
        climate = st.selectbox("Preferred climate", ALL_CLIMATES)
        budget_label = st.select_slider(
            "Budget", options=["Budget", "Mid-range", "Luxury"], value="Mid-range"
        )
        budget_level = {"Budget": 1, "Mid-range": 2, "Luxury": 3}[budget_label]

        liked = st.multiselect(
            "Places you've enjoyed before (optional, powers the "
            "collaborative-filtering boost)",
            sorted(dest_df["name"].tolist()),
        )
        collab_weight = st.slider(
            "Weight on 'travellers like you also liked...'", 0.0, 1.0, 0.35, 0.05
        )
        top_n = st.slider("Number of recommendations", 3, 15, 8)

    if not activities:
        st.warning("Pick at least one activity in the sidebar to get recommendations.")
        return

    recs = get_recommendations(
        activities=activities,
        climate=climate,
        budget_level=budget_level,
        liked_destinations=liked,
        top_n=top_n,
        collab_weight=collab_weight,
    )

    st.subheader(f"Top {len(recs)} matches for you")
    for _, row in recs.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"### {row['name']}, {row['country']}")
                st.write(
                    f"**Region:** {row['region']} · **Climate:** {row['climate']} · "
                    f"**Best time:** {row['best_season']}"
                )
                st.write(
                    f"**Activities:** {row['activities'].replace('|', ', ')}"
                )
                st.write(f"**Approx. daily cost:** ${row['avg_daily_cost_usd']}")
            with c2:
                st.metric("Match score", f"{row['match_score']*100:.0f}%")
                st.caption(
                    f"content {row['content_score']:.2f} · "
                    f"collaborative {row['collab_score']:.2f}"
                )

    st.subheader("Match score breakdown")
    fig = px.bar(
        recs.sort_values("match_score"),
        x="match_score",
        y="name",
        orientation="h",
        color="region",
        title="Recommended destinations ranked by match score",
        labels={"match_score": "Match score", "name": "Destination"},
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Browse the full destination catalogue"):
        st.dataframe(
            dest_df[
                ["name", "country", "region", "climate", "budget_level",
                 "avg_daily_cost_usd", "best_season", "activities"]
            ],
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
