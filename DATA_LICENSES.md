# Third-party data sources and licenses

This repo's code is my own. The datasets it trains/runs on are:

| Data | Source | License | Used by |
|---|---|---|---|
| 2018 FIFA World Cup event data | [StatsBomb Open Data](https://github.com/statsbomb/open-data) | [StatsBomb's open data license](https://github.com/statsbomb/open-data/blob/master/LICENSE.pdf) — non-commercial research/education use, with attribution | `football_dashboard/` |
| Sign Language MNIST (24 static ASL letters) | [Kaggle: datamunge/sign-language-mnist](https://www.kaggle.com/datasets/datamunge/sign-language-mnist), downloaded from a GitHub mirror | CC0 1.0 (public domain) | `signspeak/` |
| Live weather | [Open-Meteo API](https://open-meteo.com/) | CC BY 4.0, free for non-commercial use, no key needed | `wanderwise/` |
| Chat answers (optional) | [Google Gemini API](https://ai.google.dev/) | Gemini API terms, with your own key | `wanderwise/` |
| AT&T/ORL Database of Faces | Originally AT&T Laboratories Cambridge; mirrored (as used here) via [wihoho/FaceRecognition](https://github.com/wihoho/FaceRecognition) | Free for research/educational use (AT&T's original terms) | `attendance_system/` |
| Human Phenotype Ontology, `phenotype.hpoa`, `genes_to_phenotype.txt` | [obophenotype/human-phenotype-ontology](https://github.com/obophenotype/human-phenotype-ontology) | [HPO license](https://hpo.jax.org/app/license) (open, attribution required) | `genomics_dsst/` |
| WanderWise destination attributes | Hand-curated by me from general travel knowledge (no open dataset fit the need) | — | `wanderwise/` |
| WanderWise traveller ratings | Synthetically generated for this project (see `wanderwise/data/build_ratings.py`) | — | `wanderwise/` |

If you reuse this repo, keep this file and give the same attribution to
StatsBomb, the HPO project, and the dataset authors above.
