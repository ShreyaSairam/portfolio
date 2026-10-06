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

import numpy as np
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


def symptom_weights(disease_symptoms):
    """
    Information content of each symptom: log(N / diseases with that symptom).
    A symptom shared by hundreds of diseases (seizure) says little; a rare one
    (lens dislocation) narrows things down a lot, so it counts for more.
    """
    n = disease_symptoms["disease_id"].nunique()
    per_term = disease_symptoms.groupby("hpo_id")["disease_id"].nunique()
    return np.log(n / per_term).to_dict()


def match_diseases(selected_hpo_ids, disease_symptoms, top_n=10, weights=None):
    """
    Ranks diseases by how well they explain the patient's symptoms.

    score = 0.7 * weighted recall + 0.3 * coverage
      weighted recall: share of the patient's symptom information this disease explains
      coverage: share of the disease's known profile that the patient shows
    """
    cols = ["disease_id", "disease_name", "matched_symptoms", "disease_symptom_count",
            "coverage", "recall", "score", "matched_ids"]
    if not selected_hpo_ids:
        return pd.DataFrame(columns=cols)

    weights = weights or symptom_weights(disease_symptoms)
    selected = set(selected_hpo_ids)
    total_info = sum(weights.get(h, 0.0) for h in selected) or 1.0
    grouped = disease_symptoms.groupby(["disease_id", "disease_name"])["hpo_id"].apply(set)

    rows = []
    for (disease_id, disease_name), disease_hpo_set in grouped.items():
        matched = selected & disease_hpo_set
        if not matched:
            continue
        recall = sum(weights.get(h, 0.0) for h in matched) / total_info
        coverage = len(matched) / len(disease_hpo_set)
        rows.append(
            {
                "disease_id": disease_id,
                "disease_name": disease_name,
                "matched_symptoms": len(matched),
                "disease_symptom_count": len(disease_hpo_set),
                "coverage": round(coverage, 3),
                "recall": round(recall, 3),
                "score": round(0.7 * recall + 0.3 * coverage, 3),
                "matched_ids": sorted(matched),
            }
        )

    result = pd.DataFrame(rows, columns=cols)
    if result.empty:
        return result
    return result.sort_values(["score", "matched_symptoms"], ascending=False).head(top_n).reset_index(drop=True)


def confidence_label(score, matched, n_selected):
    """Plain-language confidence for a candidate, shown to the GP."""
    if score >= 0.55 and matched >= min(3, n_selected):
        return "High"
    if score >= 0.3:
        return "Moderate"
    return "Low"


def get_recommendation(selected_hpo_ids, disease_symptoms, disease_genes, top_n=10, weights=None):
    ranked = match_diseases(selected_hpo_ids, disease_symptoms, top_n=top_n, weights=weights)
    if ranked.empty:
        return ranked, pd.DataFrame()

    genes_for_ranked = disease_genes[
        disease_genes["disease_id"].isin(ranked["disease_id"])
        & ~disease_genes["gene_symbol"].isin(["-", ""])
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
    merged["n_genes"] = merged["n_genes"].fillna(0).astype(int)
    merged["genes"] = merged["genes"].fillna("")
    merged["suggested_test"] = merged["suggested_test"].fillna("Refer to clinical genetics")
    merged["confidence"] = [
        confidence_label(s, m, len(selected_hpo_ids)) for s, m in zip(merged["score"], merged["matched_symptoms"])
    ]
    return merged, gene_summary


def overall_recommendation(ranked):
    """
    One recommendation for the case, from the top candidates:
      * a clear leader with high confidence and one gene -> single-gene test
      * a handful of genes across the leading candidates -> targeted panel
      * many genes or no clear leader -> exome or genome sequencing
    Returns (test, reason, genes_to_include).
    """
    top = ranked.head(3)
    lead = top.iloc[0]
    gap = lead["score"] - (top.iloc[1]["score"] if len(top) > 1 else 0)
    genes = sorted({g for gs in top["genes"] for g in gs.split(", ") if g})
    if lead["confidence"] == "High" and lead["n_genes"] == 1 and gap >= 0.1:
        return ("Single-gene sequencing",
                f"{lead['disease_name']} clearly leads and is linked to one gene.", lead["genes"].split(", "))
    if 0 < len(genes) <= 12:
        return ("Targeted multi-gene panel",
                f"The top {len(top)} candidates share {len(genes)} genes between them, small enough for one panel.", genes)
    return ("Exome or genome sequencing",
            "Many genes are in play and no candidate clearly leads, so testing broadly is more efficient.", genes[:12])
