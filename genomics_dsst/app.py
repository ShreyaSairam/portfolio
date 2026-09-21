"""
Genetic Testing Decision-Support Tool — dashboard page.

GP-facing prototype: a clinician (or in this demo, you) selects the
patient's symptoms from an HPO-coded picklist, and the tool ranks
candidate diseases by phenotype overlap, surfaces the gene(s)
implicated, and suggests a testing strategy — single-gene, panel, or
broader sequencing — depending on how many genes are in play. It also
draws the underlying disease-symptom-gene knowledge graph for the
top matches.

Data: real HPO ontology + disease/gene annotations (see prepare_data.py).
This is a teaching/demo decision-support tool, not a diagnostic device —
it doesn't replace clinical genetics referral or expert interpretation.
"""

import os

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine import load_data, get_recommendation

HERE = os.path.dirname(os.path.abspath(__file__))


@st.cache_data
def cached_load():
    return load_data()


def build_knowledge_graph(ranked, gene_summary, max_diseases=6):
    G = nx.Graph()
    top = ranked.head(max_diseases)
    for _, row in top.iterrows():
        G.add_node(row["disease_name"], kind="disease")
        genes = gene_summary.loc[
            gene_summary["disease_id"] == row["disease_id"], "gene_symbol"
        ]
        if len(genes):
            for gene in genes.iloc[0][:4]:  # cap genes shown per disease for readability
                G.add_node(gene, kind="gene")
                G.add_edge(row["disease_name"], gene)
    return G


def plot_graph(G):
    if G.number_of_nodes() == 0:
        return None
    pos = nx.spring_layout(G, seed=42, k=0.8)

    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="rgba(150,150,150,0.5)"), hoverinfo="none",
    )

    node_x, node_y, node_text, node_color = [], [], [], []
    for node, attrs in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_color.append("#4C78A8" if attrs["kind"] == "disease" else "#E45756")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=node_text,
        textposition="top center", hoverinfo="text",
        marker=dict(size=16, color=node_color, line=dict(width=1, color="white")),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=30, b=10),
        title="Disease-gene knowledge graph (top matches)",
    )
    return fig


def main():
    st.set_page_config(page_title="Genetic Testing Decision Support", layout="wide")
    st.title("Genetic Testing Decision-Support Tool")
    st.caption(
        "GP-facing prototype: match patient symptoms (HPO-coded) against "
        "known disease phenotype profiles, then suggest a genetic testing "
        "strategy based on how many genes are implicated. Built on real "
        "HPO ontology and disease/gene annotation data."
    )
    st.info(
        "This is a teaching/demo decision-support tool, not a diagnostic "
        "device. It does not replace clinical genetics referral or expert "
        "interpretation.",
        icon="⚠️",
    )

    terms, disease_symptoms, disease_genes = cached_load()

    st.subheader("Patient symptoms")
    term_options = terms.sort_values("name")
    label_to_id = dict(zip(term_options["name"], term_options["hpo_id"]))
    selected_names = st.multiselect(
        "Select observed symptoms (HPO-coded terms)",
        options=term_options["name"].tolist(),
        default=["Seizure", "Intellectual disability"]
        if {"Seizure", "Intellectual disability"}.issubset(set(term_options["name"]))
        else [],
    )
    selected_ids = [label_to_id[n] for n in selected_names]

    top_n = st.slider("Number of candidate diseases to show", 3, 20, 10)

    if not selected_ids:
        st.warning("Select at least one symptom to get recommendations.")
        return

    ranked, gene_summary = get_recommendation(
        selected_ids, disease_symptoms, disease_genes, top_n=top_n
    )

    if ranked.empty:
        st.error("No matching diseases found for this symptom combination in the dataset.")
        return

    st.subheader(f"Top {len(ranked)} candidate diseases")
    display_df = ranked[
        ["disease_name", "matched_symptoms", "disease_symptom_count",
         "score", "genes", "n_genes", "suggested_test"]
    ].rename(
        columns={
            "disease_name": "Disease",
            "matched_symptoms": "Symptoms matched",
            "disease_symptom_count": "Disease's known symptoms",
            "score": "Match score",
            "genes": "Implicated gene(s)",
            "n_genes": "# genes",
            "suggested_test": "Suggested test strategy",
        }
    )
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    st.subheader("Knowledge graph — top matches")
    G = build_knowledge_graph(ranked, gene_summary)
    fig = plot_graph(G)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Blue = disease, red = gene. Edges show gene-disease association.")

    with st.expander("How this works"):
        st.markdown(
            """
            1. **Symptom matching** — each disease in the HPO annotation
               data has a known set of associated symptoms (HPO terms).
               The tool scores each disease by how much of the patient's
               selected symptoms it explains (*recall*) and how much of
               the disease's typical profile is covered (*coverage*),
               blended 40/60.
            2. **Gene lookup** — for each top-ranked disease, the genes
               known to cause it are pulled from HPO's gene-to-phenotype
               annotations.
            3. **Test strategy** — a simple heuristic: 1 gene implicated
               suggests single-gene sequencing; 2-5 genes suggests a
               targeted panel; 6+ suggests exome/genome sequencing would
               likely be more efficient than testing genes one at a time.
            """
        )


if __name__ == "__main__":
    main()
