# Third-party data sources and licenses

This repo's code is original. The datasets it trains/runs on are:

| Data | Source | License | Used by |
|---|---|---|---|
| 2018 FIFA World Cup event data | [StatsBomb Open Data](https://github.com/statsbomb/open-data) | [StatsBomb's open data license](https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf) — non-commercial research/education use, with attribution | `football_dashboard/` |
| Sign Language Digits Dataset | [ardamavi/Sign-Language-Digits-Dataset](https://github.com/ardamavi/Sign-Language-Digits-Dataset) | Apache License 2.0 | `signspeak/` |
| AT&T/ORL Database of Faces | Originally AT&T Laboratories Cambridge; mirrored (as used here) via [wihoho/FaceRecognition](https://github.com/wihoho/FaceRecognition) | Free for research/educational use (AT&T's original terms) | `attendance_system/` |
| Human Phenotype Ontology, `phenotype.hpoa`, `genes_to_phenotype.txt` | [obophenotype/human-phenotype-ontology](https://github.com/obophenotype/human-phenotype-ontology) | [HPO license](https://hpo.jax.org/app/license) (open, attribution required) | `genomics_dsst/` |
| WanderWise destination attributes | Hand-curated by me from general travel knowledge (no open dataset fit the need) | — | `wanderwise/` |
| WanderWise traveller ratings | Synthetically generated for this project (see `wanderwise/data/build_ratings.py`) | — | `wanderwise/` |

If you reuse this repo, keep this file and give the same attribution to
StatsBomb, the HPO project, and the dataset authors above.
