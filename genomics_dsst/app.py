"""
Genetic Testing Decision-Support Tool, for GPs.

The GP enters the patient's symptoms (coded with the Human Phenotype
Ontology). The tool ranks candidate genetic conditions, shows the genes
behind each one with a confidence level, and recommends one test for the
case: single gene, targeted panel, or exome/genome sequencing.

Data: real HPO disease and gene annotations, served from SQLite (gx_db.py).
This is a teaching prototype, not a diagnostic device.
"""

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

import gx_db
from engine import get_recommendation, overall_recommendation, symptom_weights

EXAMPLES = {
    "Noonan": ["Hypertrophic cardiomyopathy", "Hypogonadism", "Bruising susceptibility",
                                 "Male infertility", "Dry skin"],
    "NF1": ["Headache", "Hyperlordosis", "Mitral valve prolapse",
                               "Hypertrophic cardiomyopathy", "Mitral regurgitation"],
    "Prader-Willi": ["Hypertriglyceridemia", "Edema", "Delayed puberty", "Carious teeth", "Short palm"],
}
CONF_COLOUR = {"High": "#1b7f4b", "Moderate": "#b26a00", "Low": "#8a8f98"}


@st.cache_data
def load():
    terms, ds, dg = gx_db.load_tables()
    return terms, ds, dg, symptom_weights(ds)


def chip(text, colour="#2f4a8a"):
    return (f"<span style='display:inline-block;padding:2px 9px;margin:2px 4px 2px 0;border-radius:999px;"
            f"border:1px solid {colour};color:{colour};font-size:12.5px'>{text}</span>")


def graph_figure(ranked, max_diseases=6):
    G = nx.Graph()
    for _, row in ranked.head(max_diseases).iterrows():
        G.add_node(row["disease_name"], kind="disease")
        for g in [g for g in row["genes"].split(", ") if g][:5]:
            G.add_node(g, kind="gene")
            G.add_edge(row["disease_name"], g)
    if G.number_of_nodes() == 0:
        return None
    pos = nx.spring_layout(G, seed=42, k=0.9)
    ex, ey = [], []
    for u, v in G.edges():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    nodes = list(G.nodes(data=True))
    fig = go.Figure([
        go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=1, color="rgba(140,140,140,.5)"), hoverinfo="none"),
        go.Scatter(x=[pos[n][0] for n, _ in nodes], y=[pos[n][1] for n, _ in nodes], mode="markers+text",
                   text=[n if a["kind"] == "gene" else n[:28] for n, a in nodes], textposition="top center",
                   hovertext=[n for n, _ in nodes], hoverinfo="text",
                   marker=dict(size=[18 if a["kind"] == "disease" else 12 for _, a in nodes],
                               color=["#3b5bab" if a["kind"] == "disease" else "#c4473a" for _, a in nodes])),
    ])
    fig.update_layout(showlegend=False, height=420, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def main():
    st.set_page_config(page_title="Genetic Testing Decision Support", layout="wide")
    st.title("Genetic Testing Decision Support")
    st.caption("For GPs deciding which genetic test to order. Built on real Human Phenotype Ontology "
               "disease and gene annotations, stored in SQLite.")
    st.warning("Teaching prototype, not a diagnostic device. It does not replace referral to clinical genetics.",
               icon="⚕️")

    terms, ds, dg, weights = load()
    names = sorted(terms["name"].tolist())
    name_to_id = dict(zip(terms["name"], terms["hpo_id"]))

    if "gx_symptoms" not in st.session_state:
        st.session_state.gx_symptoms = EXAMPLES["Noonan"]

    case_col, result_col = st.columns([2, 3])
    with case_col:
        with st.container(border=True):
            st.subheader("Patient case")
            a1, a2 = st.columns(2)
            age = a1.selectbox("Age group", ["Infant", "Child", "Adolescent", "Adult"], index=1, key="gx_age")
            sex = a2.selectbox("Sex", ["Female", "Male", "Not stated"], index=1, key="gx_sex")
            st.caption("Try an example case:")
            ex_cols = st.columns(len(EXAMPLES))
            for col, (label, syms) in zip(ex_cols, EXAMPLES.items()):
                if col.button(label, key=f"gx_ex_{label}", help=f"A {label}-like presentation", width="stretch"):
                    st.session_state.gx_symptoms = syms
                    st.rerun()
            selected = st.multiselect("Observed symptoms (HPO terms)", names, key="gx_symptoms")
            top_n = st.slider("Candidates to show", 3, 10, 5, key="gx_topn")
            if selected:
                info = sorted(((weights.get(name_to_id[n], 0), n) for n in selected), reverse=True)
                st.caption("Most informative symptom: **" + info[0][1] + "** (rarest across conditions, so it "
                           "narrows the search most).")

        with st.container(border=True):
            st.subheader("Recent cases")
            st.caption("Each case you run is saved to SQLite.")
            recent = gx_db.recent_searches(6)
            if recent.empty:
                st.write("No cases yet.")
            else:
                st.dataframe(recent, hide_index=True, width="stretch")

    with result_col:
        if not selected:
            st.info("Add at least one symptom to see candidate conditions.")
            return
        ids = [name_to_id[n] for n in selected]
        ranked, _ = get_recommendation(ids, ds, dg, top_n=top_n, weights=weights)
        if ranked.empty:
            st.error("No condition in the dataset matches these symptoms.")
            return
        test, reason, genes = overall_recommendation(ranked)

        case_key = (tuple(sorted(selected)), top_n)
        if st.session_state.get("gx_last_logged") != case_key:
            gx_db.log_search(selected, ranked.iloc[0]["disease_name"], test)
            st.session_state.gx_last_logged = case_key

        with st.container(border=True):
            st.markdown(f"<div style='font-size:12px;letter-spacing:.08em;opacity:.7'>RECOMMENDED TEST</div>"
                        f"<div style='font-size:26px;font-weight:700;margin:2px 0 6px'>{test}</div>",
                        unsafe_allow_html=True)
            st.write(reason)
            st.markdown("Genes to include: " + "".join(chip(g, "#c4473a") for g in genes), unsafe_allow_html=True)
            st.caption(f"Case: {sex.lower()} {age.lower()}, {len(selected)} symptoms.")

        st.subheader("Candidate conditions")
        for rank, row in ranked.iterrows():
            colour = CONF_COLOUR[row["confidence"]]
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{rank + 1}. {row['disease_name']}**")
                    matched = terms.set_index("hpo_id").loc[row["matched_ids"], "name"].tolist()
                    st.markdown("Explains: " + "".join(chip(m) for m in matched), unsafe_allow_html=True)
                    st.caption(f"Genes: {row['genes'] or 'none recorded'} · usual test: {row['suggested_test']}")
                with c2:
                    st.markdown(f"<div style='text-align:right'><div style='color:{colour};font-weight:700'>"
                                f"{row['confidence']}</div><div style='font-size:12px;opacity:.7'>score "
                                f"{row['score']:.2f}</div></div>", unsafe_allow_html=True)
                    st.progress(min(1.0, float(row["score"])))

        with st.expander("Disease and gene network"):
            fig = graph_figure(ranked)
            if fig:
                st.plotly_chart(fig, width="stretch")
                st.caption("Blue: candidate conditions. Red: genes linked to them.")

    with st.expander("How the ranking works"):
        st.markdown(
            """
1. **Weight each symptom**: common symptoms (like seizures) appear in hundreds of conditions, rare ones in a few.
   Each symptom gets an information weight, log(conditions / conditions with that symptom).
2. **Score each condition**: 70% is how much of the patient's symptom information it explains (weighted recall),
   30% is how much of the condition's known profile the patient shows (coverage).
3. **Confidence**: High needs a strong score and several matching symptoms, Moderate a fair score, otherwise Low.
4. **Recommend one test**: a clear leader linked to one gene means single-gene sequencing; a small set of genes
   across the top three means a targeted panel; anything broader means exome or genome sequencing.
"""
        )


if __name__ == "__main__":
    main()
