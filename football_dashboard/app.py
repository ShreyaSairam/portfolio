"""
France 2018 World Cup Analytics Dashboard

A Streamlit app built on real StatsBomb open event data covering all seven
of France's matches at the 2018 World Cup (won). It has four tabs:
team comparison, shot maps with expected goals (xG), a player explorer,
and pass-location heatmaps.

Data source: StatsBomb Open Data (github.com/statsbomb/open-data), used
under their open data license for non-commercial research/education.
Run prepare_data.py once first to generate the CSVs this app reads.
"""

import os

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

PITCH_LENGTH = 120
PITCH_WIDTH = 80


@st.cache_data
def load_data():
    matches = pd.read_csv(os.path.join(DATA_DIR, "matches.csv"))
    shots = pd.read_csv(os.path.join(DATA_DIR, "shots.csv"))
    passes = pd.read_csv(os.path.join(DATA_DIR, "passes.csv"))
    stats = pd.read_csv(os.path.join(DATA_DIR, "player_match_stats.csv"))
    return matches, shots, passes, stats


def draw_pitch(fig):
    """Add StatsBomb-coordinate pitch markings (120x80) to a plotly figure."""
    lines = [
        # outer boundary
        dict(x0=0, y0=0, x1=PITCH_LENGTH, y1=PITCH_WIDTH),
        # halfway line
        dict(x0=60, y0=0, x1=60, y1=PITCH_WIDTH),
        # left penalty box
        dict(x0=0, y0=18, x1=18, y1=62),
        # right penalty box
        dict(x0=102, y0=18, x1=120, y1=62),
        # left six-yard box
        dict(x0=0, y0=30, x1=6, y1=50),
        # right six-yard box
        dict(x0=114, y0=30, x1=120, y1=50),
    ]
    for l in lines:
        fig.add_shape(
            type="rect",
            x0=l["x0"], y0=l["y0"], x1=l["x1"], y1=l["y1"],
            line=dict(color="rgba(255,255,255,0.5)", width=1.5),
            layer="below",
        )
    fig.add_shape(
        type="circle",
        x0=60 - 9.15, y0=40 - 9.15, x1=60 + 9.15, y1=40 + 9.15,
        line=dict(color="rgba(255,255,255,0.5)", width=1.5),
        layer="below",
    )
    fig.update_xaxes(range=[-2, PITCH_LENGTH + 2], visible=False)
    fig.update_yaxes(range=[-2, PITCH_WIDTH + 2], visible=False, scaleanchor="x")
    fig.update_layout(
        plot_bgcolor="#1b4332",
        paper_bgcolor="#1b4332",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def tab_team_comparison(matches, shots, stats):
    st.subheader("France's road to the trophy")
    st.dataframe(
        matches[
            ["date", "stage", "home_team", "home_score", "away_score", "away_team"]
        ],
        hide_index=True,
        use_container_width=True,
    )

    match_xg = shots.groupby(["match_id", "team"])["xg"].sum().reset_index()
    match_xg = match_xg.merge(
        matches[["match_id", "date", "home_team", "away_team", "stage"]],
        on="match_id",
    )
    match_xg["opponent_stage"] = match_xg["stage"] + " (" + match_xg["date"] + ")"

    fig = px.bar(
        match_xg,
        x="opponent_stage",
        y="xg",
        color="team",
        barmode="group",
        title="Expected goals (xG) per match",
        labels={"opponent_stage": "Match", "xg": "xG"},
    )
    fig.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "xG is StatsBomb's own model output from the open data — the "
        "probability a given shot results in a goal, based on shot location, "
        "angle, technique and other context."
    )


def tab_shot_map(matches, shots):
    st.subheader("Shot map")
    match_label = matches.apply(
        lambda r: f"{r['home_team']} {r['home_score']}-{r['away_score']} {r['away_team']} ({r['stage']})",
        axis=1,
    )
    match_choice = st.selectbox("Match", options=match_label, index=len(match_label) - 1)
    match_id = matches.loc[match_label == match_choice, "match_id"].iloc[0]

    m_shots = shots[shots["match_id"] == match_id].copy()
    if m_shots.empty:
        st.info("No shot data for this match.")
        return

    teams = m_shots["team"].unique().tolist()
    colors = {teams[0]: "#0055A4", teams[1]: "#EF4135"} if len(teams) == 2 else {}

    fig = go.Figure()
    for team in teams:
        t = m_shots[m_shots["team"] == team]
        fig.add_trace(
            go.Scatter(
                x=t["x"],
                y=t["y"],
                mode="markers",
                name=team,
                marker=dict(
                    size=(t["xg"].fillna(0.02) * 60 + 8),
                    color=colors.get(team, None),
                    line=dict(width=1.5, color="white"),
                    symbol=["star" if g else "circle" for g in t["is_goal"]],
                ),
                text=t.apply(
                    lambda r: f"{r['player']}<br>xG: {r['xg']:.2f}<br>{r['outcome']}",
                    axis=1,
                ),
                hoverinfo="text",
            )
        )
    fig = draw_pitch(fig)
    fig.update_layout(title=f"Shots — {match_choice}", legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Marker size scales with xG. Stars are goals.")

    st.dataframe(
        m_shots[["player", "team", "minute", "body_part", "outcome", "xg"]]
        .sort_values("xg", ascending=False)
        .round({"xg": 3}),
        hide_index=True,
        use_container_width=True,
    )


def tab_player_explorer(stats):
    st.subheader("Player explorer")
    players = sorted(stats["player"].unique())
    player = st.selectbox("Player", players, index=players.index("Kylian Mbappé Lottin") if "Kylian Mbappé Lottin" in players else 0)

    p = stats[stats["player"] == player]
    totals = p.agg(
        {
            "goals": "sum",
            "xg": "sum",
            "shots": "sum",
            "passes": "sum",
            "passes_complete": "sum",
        }
    )
    pass_acc = (
        round(totals["passes_complete"] / totals["passes"] * 100, 1)
        if totals["passes"]
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Goals", int(totals["goals"]))
    c2.metric("xG", round(totals["xg"], 2))
    c3.metric("Shots", int(totals["shots"]))
    c4.metric("Pass accuracy", f"{pass_acc}%")

    fig = px.bar(
        p.sort_values("match_id"),
        x="match_id",
        y=["goals", "xg"],
        barmode="group",
        title=f"{player} — goals vs xG by match",
    )
    st.plotly_chart(fig, use_container_width=True)


def tab_heatmap(matches, passes):
    st.subheader("Player heatmap (pass locations)")
    match_label = matches.apply(
        lambda r: f"{r['home_team']} {r['home_score']}-{r['away_score']} {r['away_team']} ({r['stage']})",
        axis=1,
    )
    match_choice = st.selectbox(
        "Match", options=match_label, index=len(match_label) - 1, key="heatmap_match"
    )
    match_id = matches.loc[match_label == match_choice, "match_id"].iloc[0]

    m_passes = passes[passes["match_id"] == match_id]
    players = sorted(m_passes["player"].dropna().unique())
    if not players:
        st.info("No pass data for this match.")
        return
    player = st.selectbox("Player", players)

    p_passes = m_passes[m_passes["player"] == player]

    fig = go.Figure()
    fig.add_trace(
        go.Histogram2d(
            x=p_passes["x"],
            y=p_passes["y"],
            colorscale="YlOrRd",
            nbinsx=24,
            nbinsy=16,
            opacity=0.85,
        )
    )
    fig = draw_pitch(fig)
    fig.update_layout(title=f"{player} — pass origin heatmap")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{len(p_passes)} passes plotted for this match.")


def main():
    st.set_page_config(page_title="France 2018 World Cup Analytics", layout="wide")
    st.title("France 2018 World Cup — Analytics Dashboard")
    st.caption(
        "Built on real StatsBomb open event data for all seven of France's "
        "matches at the 2018 World Cup."
    )

    matches, shots, passes, stats = load_data()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Team comparison", "Shot map", "Player explorer", "Heatmaps"]
    )
    with tab1:
        tab_team_comparison(matches, shots, stats)
    with tab2:
        tab_shot_map(matches, shots)
    with tab3:
        tab_player_explorer(stats)
    with tab4:
        tab_heatmap(matches, passes)


if __name__ == "__main__":
    main()
