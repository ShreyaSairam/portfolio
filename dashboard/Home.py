"""
Portfolio hub — entry point.

Run with:
    streamlit run Home.py
from inside the dashboard/ folder (after each project's own
prepare_data.py / preprocess.py / train_model.py has been run once —
see the top-level README).
"""

import streamlit as st

st.set_page_config(page_title="Shreya Sairam: Project Demos", page_icon="📁", layout="wide")


def home_page():
    st.title("Shreya Sairam: Project Demos")
    st.caption("Five working projects, each a live app. Pick one from the sidebar. "
               "Code: github.com/ShreyaSairam/portfolio")

    projects = [
        {
            "title": "Football Analytics: France at the 2018 World Cup",
            "desc": "Shot maps with expected goals (xG), team comparison, a player explorer and pass "
                    "heatmaps from real StatsBomb event data, stored in SQLite with a live SQL explorer.",
            "stack": "pandas, Plotly, SQLite, StatsBomb open data",
        },
        {
            "title": "SignSpeak: Real-Time Sign Recognition",
            "desc": "Reads ASL letters A to Y from your webcam. HOG features, PCA and an SVM, 95.2% accuracy "
                    "on 7,172 separate test images. Demo mode spells words without a camera.",
            "stack": "OpenCV, scikit-learn, streamlit-webrtc, SQLite",
        },
        {
            "title": "WanderWise: AI Travel Recommender",
            "desc": "Hybrid recommender (content plus collaborative filtering) over 51 destinations, with live "
                    "weather, your location, a Gemini chat assistant and accounts with saved favourites.",
            "stack": "scikit-learn, Open-Meteo, Gemini API, SQLite",
        },
        {
            "title": "Facial Recognition Attendance",
            "desc": "Check in by webcam or photo. Haar cascade detection and LBPH recognition (93.8% accuracy), "
                    "with present, late and absent tracking against the class start time.",
            "stack": "OpenCV, SQLite",
        },
        {
            "title": "Genetic Testing Decision Support",
            "desc": "A GP enters symptoms and gets ranked genetic conditions, the genes behind them, a "
                    "confidence level and one recommended test. Built on real HPO data.",
            "stack": "pandas, NetworkX, SQLite, Human Phenotype Ontology",
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
    st.caption("Everything here runs on open data. Databases reset when the app restarts.")


home = st.Page(home_page, title="Home", icon="🏠", default=True)
football = st.Page("views/football.py", title="Football Analytics", icon="⚽")
signspeak = st.Page("views/signspeak.py", title="SignSpeak", icon="🤟")
wanderwise = st.Page("views/wanderwise.py", title="WanderWise", icon="🧭")
attendance = st.Page("views/attendance.py", title="Attendance System", icon="🧑‍💼")
genomics = st.Page("views/genomics.py", title="Genetic Testing", icon="🧬")

nav = st.navigation([home, football, signspeak, wanderwise, attendance, genomics])
nav.run()
