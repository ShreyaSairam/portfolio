"""
Genetic Testing Decision-Support Tool — matching engine.

Given a set of patient symptoms (as HPO terms), ranks candidate diseases
by phenotype overlap against the real HPO disease-annotation data
(prepare_data.py), then surfaces the gene(s) linked to each candidate
disease and a suggested test strategy based on how many genes are
implicated:

  - 1 gene implicated  -> single-gene sequencing test
  - 2-5 genes          -> a targeted multi-gene panel
  - 6+ genes           -> broader panel or exome/genome sequencing,
                           since single-gene testing would be inefficient

This mirrors the "matches symptoms against HPO terms, outputs genetic
testing recommendations" specification from the source project. It is a
teaching/demo decision-support tool, not a diagnostic device, and the
app says so.
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")


def load_data():
    terms = pd.read_csv(os.path.join(DATA_DIR, "hpo_terms.csv"))
    disease_symptoms = pd.read_csv(os.path.join(DATA_DIR, "disease_symptoms.csv"))
    disease_genes = pd.read_csv(os.path.join(DATA_DIR, "disease_genes.csv"))
    return terms, disease_symptoms, disease_genes


def suggest_test_strategy(n_genes):
    if n_genes == 1:
        return "Single-gene sequencing"
    elif n_genes <= 5:
        return "Targeted multi-gene panel"
    else:
        return "Broad panel or exome sequencing"


def match_diseases(selected_hpo_ids, disease_symptoms, top_n=10):
    """
    Ranks diseases by the fraction of the disease's known symptom set that
    the patient's selected symptoms cover, weighted slightly by how many
    of the patient's symptoms are explained (to avoid over-favouring
    diseases with very few annotated symptoms).
    """
    if not selected_hpo_ids:
        return pd.DataFrame(
            columns=["disease_id", "disease_name", "matched_symptoms",
                     "disease_symptom_count", "coverage", "score"]
        )

    selected = set(selected_hpo_ids)

    grouped = disease_symptoms.groupby(["disease_id", "disease_name"])["hpo_id"].apply(set)

    rows = []
    for (disease_id, disease_name), disease_hpo_set in grouped.items():
        matched = selected & disease_hpo_set
        if not matched:
            continue
        coverage = len(matched) / len(disease_hpo_set)  # how much of disease profile is explained
        recall = len(matched) / len(selected)  # how much of patient's symptoms fit this disease
        score = 0.6 * coverage + 0.4 * recall
        rows.append(
            {
                "disease_id": disease_id,
                "disease_name": disease_name,
                "matched_symptoms": len(matched),
                "disease_symptom_count": len(disease_hpo_set),
                "coverage": round(coverage, 3),
                "recall": round(recall, 3),
                "score": round(score, 3),
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)


def get_recommendation(selected_hpo_ids, disease_symptoms, disease_genes, top_n=10):
    ranked = match_diseases(selected_hpo_ids, disease_symptoms, top_n=top_n)
    if ranked.empty:
        return ranked, pd.DataFrame()

    genes_for_ranked = disease_genes[
        disease_genes["disease_id"].isin(ranked["disease_id"])
    ]
    gene_summary = (
        genes_for_ranked.groupby(["disease_id", "disease_name"])["gene_symbol"]
        .apply(lambda s: sorted(set(s)))
        .reset_index()
    )
    gene_summary["n_genes"] = gene_summary["gene_symbol"].apply(len)
    gene_summary["suggested_test"] = gene_summary["n_genes"].apply(suggest_test_strategy)
    gene_summary["genes"] = gene_summary["gene_symbol"].apply(lambda g: ", ".join(g))

    merged = ranked.merge(
        gene_summary[["disease_id", "genes", "n_genes", "suggested_test"]],
        on="disease_id",
        how="left",
    )
    return merged, gene_summary
