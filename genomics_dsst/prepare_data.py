"""
Genetic Testing Decision-Support Tool — data preparation.

Builds a symptom -> disease -> gene knowledge base from real Human
Phenotype Ontology (HPO) data:

  - hp.obo: the HPO term hierarchy (term IDs, names) — from
    obophenotype/human-phenotype-ontology.
  - phenotype.hpoa: disease-to-phenotype annotations (which HPO-coded
    symptoms are associated with which OMIM/Orphanet diseases).
  - genes_to_phenotype.txt: gene-to-phenotype-to-disease associations,
    used here to link diseases back to the gene(s) a genetic test would
    target.

This mirrors the specification from the ISYS90069 group project this
tool is modelled on: HPO for phenotype matching, a disease-symptom-gene
knowledge graph sourced from OMIM/HPOA, used to support a GP-facing
recommendation of which genetic test to consider.

To keep the demo responsive, this script filters down to diseases that
have BOTH phenotype annotations and at least one linked gene, and caps
the symptom vocabulary to the ~400 most commonly annotated HPO terms
(so the symptom picker in the app stays usable), then writes compact
CSVs:
    hpo_terms.csv          - hpo_id, name (only terms used below)
    disease_symptoms.csv   - disease_id, disease_name, hpo_id
    disease_genes.csv      - disease_id, disease_name, gene_symbol

Run once:
    python prepare_data.py
"""

import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
HPO_DIR = os.path.join(HERE, "..", "data", "hpo")
OUT_DIR = os.path.join(HERE, "data")
os.makedirs(OUT_DIR, exist_ok=True)

TOP_N_SYMPTOMS = 400
MAX_DISEASES = 600


def parse_obo(path):
    """Minimal .obo parser: returns {hpo_id: name}."""
    terms = {}
    current_id, current_name = None, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "[Term]":
                current_id, current_name = None, None
            elif line.startswith("id: HP:"):
                current_id = line.split("id: ")[1]
            elif line.startswith("name: ") and current_id and current_name is None:
                current_name = line.split("name: ", 1)[1]
                terms[current_id] = current_name
    return terms


def main():
    print("Parsing hp.obo ...")
    hpo_names = parse_obo(os.path.join(HPO_DIR, "hp.obo"))
    print(f"  {len(hpo_names)} HPO terms")

    print("Loading phenotype.hpoa ...")
    hpoa = pd.read_csv(
        os.path.join(HPO_DIR, "phenotype.hpoa"),
        sep="\t",
        comment="#",
        dtype=str,
        low_memory=False,
    )
    hpoa = hpoa[["database_id", "disease_name", "hpo_id"]].dropna()
    # drop "excluded" qualifier rows aren't separated here; hpoa already
    # only lists positive associations in the 'aspect' column P (phenotype)
    hpoa = hpoa.drop_duplicates()

    print("Loading genes_to_phenotype.txt ...")
    g2p = pd.read_csv(
        os.path.join(HPO_DIR, "genes_to_phenotype.txt"), sep="\t", dtype=str
    )
    disease_genes = g2p[["disease_id", "gene_symbol"]].dropna().drop_duplicates()
    disease_genes = disease_genes.rename(columns={"disease_id": "database_id"})

    # Only keep diseases that have both symptoms and a known gene
    diseases_with_genes = set(disease_genes["database_id"].unique())
    hpoa = hpoa[hpoa["database_id"].isin(diseases_with_genes)]

    # Most common symptom terms across this filtered set (keeps the
    # symptom picker to a manageable, clinically-relevant vocabulary)
    top_symptoms = (
        hpoa["hpo_id"].value_counts().head(TOP_N_SYMPTOMS).index.tolist()
    )
    hpoa_top = hpoa[hpoa["hpo_id"].isin(top_symptoms)]

    # Cap number of diseases by how many of the top symptoms they cover
    # (keeps well-characterised diseases, drops long-tail ultra-rare ones
    # with only one annotation, which make for a weak demo)
    disease_symptom_counts = hpoa_top.groupby("database_id").size()
    keep_diseases = (
        disease_symptom_counts[disease_symptom_counts >= 3]
        .sort_values(ascending=False)
        .head(MAX_DISEASES)
        .index
    )

    hpoa_final = hpoa_top[hpoa_top["database_id"].isin(keep_diseases)]
    genes_final = disease_genes[disease_genes["database_id"].isin(keep_diseases)]

    # HPO term reference table, only for terms actually used
    used_terms = sorted(hpoa_final["hpo_id"].unique())
    terms_df = pd.DataFrame(
        {"hpo_id": used_terms, "name": [hpo_names.get(t, t) for t in used_terms]}
    )

    hpoa_final = hpoa_final.rename(columns={"database_id": "disease_id"})
    genes_final = genes_final.rename(columns={"database_id": "disease_id"})
    disease_names = hpoa_final[["disease_id", "disease_name"]].drop_duplicates()
    genes_final = genes_final.merge(disease_names, on="disease_id", how="left")

    terms_df.to_csv(os.path.join(OUT_DIR, "hpo_terms.csv"), index=False)
    hpoa_final[["disease_id", "disease_name", "hpo_id"]].to_csv(
        os.path.join(OUT_DIR, "disease_symptoms.csv"), index=False
    )
    genes_final[["disease_id", "disease_name", "gene_symbol"]].to_csv(
        os.path.join(OUT_DIR, "disease_genes.csv"), index=False
    )

    print(f"\nKept {len(keep_diseases)} diseases, {len(used_terms)} symptom terms")
    print(f"disease_symptoms.csv: {len(hpoa_final)} rows")
    print(f"disease_genes.csv: {len(genes_final)} rows")
    print("Done.")


if __name__ == "__main__":
    main()
