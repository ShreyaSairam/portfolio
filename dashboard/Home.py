"""
Portfolio hub — entry point.

Run with:
    streamlit run Home.py
from inside the dashboard/ folder (after each project's own
prepare_data.py / preprocess.py / train_model.py has been run once —
see the top-level README).
"""

import streamlit as st

st.set_page_config(page_title="Shreya Sairam — Project Portfolio", page_icon="📁", layout="wide")


def home_page():
    st.title("Project Portfolio")
    st.caption("Five working projects, one dashboard. Pick one from the sidebar.")

    projects = [
        {
            "title": "France 2018 World Cup — Football Analytics",
            "desc": (
                "Streamlit dashboard on real StatsBomb open event data "
                "covering all seven of France's matches at the 2018 World "
                "Cup: team xG comparison, shot maps, a player explorer, "
                "and pass-location heatmaps."
            ),
            "stack": "pandas, plotly, StatsBomb open data",
        },
        {
            "title": "SignSpeak — Sign Language Digit Recognition",
            "desc": (
                "HOG features + SVM classifier trained on the Sign "
                "Language Digits Dataset (2,062 images, digits 0-9). "
                "86% held-out test accuracy. Upload a photo or try a "
                "sample image."
            ),
            "stack": "OpenCV, scikit-image, scikit-learn",
        },
        {
            "title": "WanderWise — Travel Recommendation System",
            "desc": (
                "Hybrid recommender over 51 hand-curated destinations: "
                "content-based matching on your stated activity/climate/"
                "budget preferences, blended with a collaborative-"
                "filtering signal from simulated traveller ratings."
            ),
            "stack": "scikit-learn (cosine similarity), pandas",
        },
        {
            "title": "Facial Recognition Attendance System",
            "desc": (
                "OpenCV Haar cascade face detection + LBPH face "
                "recognizer, trained on the AT&T/ORL Database of Faces "
                "(40 subjects). 93.8% held-out accuracy. Detects faces in "
                "an uploaded photo and logs attendance per person, once "
                "per day."
            ),
            "stack": "OpenCV (opencv-contrib)",
        },
        {
            "title": "Genetic Testing Decision-Support Tool",
            "desc": (
                "GP-facing prototype: match patient symptoms (HPO-coded) "
                "against real disease phenotype profiles from the Human "
                "Phenotype Ontology, then suggest a genetic testing "
                "strategy based on how many genes are implicated, with a "
                "disease-gene knowledge graph."
            ),
            "stack": "NetworkX, pandas, real HPO/OMIM data",
        },
    ]

    cols = st.columns(2)
    for i, p in enumerate(projects):
        with cols[i % 2]:
            with st.container(border=True):
                st.subheader(p["title"])
                st.write(p["desc"])
                st.caption(f"**Stack:** {p['stack']}")

    st.divider()
    st.markdown(
        "Each project also runs standalone — see its own folder's README "
        "for `streamlit run app.py` instructions and the one-time data/"
        "model preparation steps."
    )


home = st.Page(home_page, title="Home", icon="🏠", default=True)
football = st.Page("views/football.py", title="Football Analytics", icon="⚽")
signspeak = st.Page("views/signspeak.py", title="SignSpeak", icon="🤟")
wanderwise = st.Page("views/wanderwise.py", title="WanderWise", icon="🧭")
attendance = st.Page("views/attendance.py", title="Attendance System", icon="🧑‍💼")
genomics = st.Page("views/genomics.py", title="Genetic Testing DSST", icon="🧬")

nav = st.navigation([home, football, signspeak, wanderwise, attendance, genomics])
nav.run()
