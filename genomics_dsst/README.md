# Genetic Testing Decision-Support Tool

A GP-facing prototype: match a patient's symptoms (HPO-coded) against
real disease phenotype profiles, then suggest a genetic testing strategy
based on how many genes are implicated — the same specification as the
university group project this is modelled on (ISYS90069, Digital
Transformation of eHealth): *"HPO for phenotype matching + a
disease-symptom-gene knowledge graph sourced from OMIM/Orphanet/HPOA."*

**This is a teaching/demo decision-support tool, not a diagnostic device**
— it doesn't replace clinical genetics referral or expert interpretation,
and the app says so.

## What the GP sees

- A **recommended test** for the whole case (single gene, targeted panel, or exome/genome sequencing) with the reason and the genes to include.
- **Candidate conditions**, each with the symptoms it explains, its genes, a score and a High / Moderate / Low confidence.
- **Example cases** (Noonan, NF1, Prader-Willi presentations) to try in one click, and a log of **recent cases** in SQLite.

## Ranking

Common symptoms (seizures, headache) appear across hundreds of conditions and say little; rare ones narrow things down. Each symptom is weighted by its information content, log(conditions / conditions with that symptom). A condition's score is 70% weighted recall (how much of the patient's symptom information it explains) plus 30% coverage (how much of its own profile the patient shows).

## Setup

```bash
# from the repo root, if not already done:
bash scripts/fetch_raw_data.sh
python prepare_data.py
streamlit run app.py
```

## Data

All from the [Human Phenotype Ontology](https://github.com/obophenotype/human-phenotype-ontology)
project:

- `hp.obo` — the HPO term hierarchy (term IDs → names)
- `phenotype.hpoa` — which HPO-coded symptoms are associated with which
  OMIM/Orphanet diseases (286,651 annotations across 12,880 diseases)
- `genes_to_phenotype.txt` — gene ↔ phenotype ↔ disease associations,
  used to link diseases back to the gene(s) a test would target

`prepare_data.py` filters this down to the ~600 best-characterised
diseases (≥3 matched symptoms, with a known gene) and the 400 most
commonly annotated symptom terms, so the app's symptom picker stays a
manageable clinical vocabulary instead of ~20,000 raw HPO terms.

## How the matching works

1. **Symptom scoring** (`engine.match_diseases()`) — each disease scores
   on how much of the patient's selected symptoms it explains (*recall*)
   blended with how much of the disease's typical profile is covered
   (*coverage*), 40/60.
2. **Gene lookup** — for each top-ranked disease, the causative gene(s)
   are pulled from the HPO gene annotations.
3. **Test strategy** (`engine.suggest_test_strategy()`) — 1 gene suggests
   single-gene sequencing, 2-5 suggests a targeted panel, 6+ suggests
   exome/genome sequencing would likely be more efficient.
4. **Knowledge graph** — `app.py` draws the disease-gene graph for the
   top matches with NetworkX + Plotly.
