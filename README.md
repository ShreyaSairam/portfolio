# Shreya Sairam — Project Portfolio

Five working projects from my resume, each a real, runnable implementation
(not a mockup), plus a Streamlit dashboard that ties them together.

| Project | What it does | Real data used |
|---|---|---|
| [Football Analytics](football_dashboard/) | Team comparison, shot maps (xG), player explorer, heatmaps for France's 2018 World Cup run | [StatsBomb open data](https://github.com/statsbomb/open-data) |
| [SignSpeak](signspeak/) | Sign-language digit recognition (HOG + SVM), 86% accuracy | [Sign Language Digits Dataset](https://github.com/ardamavi/Sign-Language-Digits-Dataset) |
| [WanderWise](wanderwise/) | Hybrid (content + collaborative) travel recommender over 51 destinations | Hand-curated destination data + simulated ratings (see project README) |
| [Facial Recognition Attendance System](attendance_system/) | Face detection + recognition (Haar + LBPH), 93.8% accuracy, attendance logging | [AT&T/ORL Database of Faces](https://github.com/wihoho/FaceRecognition) |
| [Genetic Testing Decision-Support Tool](genomics_dsst/) | Symptom → disease → gene matching and test-strategy suggestion | [Human Phenotype Ontology](https://github.com/obophenotype/human-phenotype-ontology) |

Each project also has its own README with more detail on how it works and
its own `streamlit run app.py`.

## Setup

```bash
git clone <this-repo-url>
cd <repo>
pip install -r requirements.txt
```

**Important:** `opencv-contrib-python` (used by the attendance system for
face recognition) conflicts with plain `opencv-python` /
`opencv-python-headless` if more than one is installed — they all provide
a `cv2` module and only one wins. If you already have `opencv-python`
installed, remove it first:

```bash
pip uninstall -y opencv-python opencv-python-headless
```

Some large source datasets are downloaded on demand rather than committed
to the repo (see `.gitignore`). Two scripts handle setup:

```bash
bash scripts/fetch_raw_data.sh   # downloads raw StatsBomb/HPO/dataset files
bash scripts/build_all.sh        # processes data + trains all models
```

Both are idempotent — safe to re-run, they skip anything already present.
`build_all.sh` takes under a minute total (the slowest step is HPO parsing).

## Running the dashboard

```bash
cd dashboard
streamlit run Home.py
```

This opens a hub with all five projects as pages in the sidebar. Each
project also runs standalone:

```bash
cd football_dashboard && streamlit run app.py
cd signspeak && streamlit run app.py
cd wanderwise && streamlit run app.py
cd attendance_system && streamlit run app.py
cd genomics_dsst && streamlit run app.py
```

## Tests

```bash
cd tests
python -m pytest test_projects.py -v
```

Smoke tests that each project's core logic (data loading, prediction,
recommendation ranking) runs correctly against the built data/models.

## Repo layout

```
portfolio/
├── dashboard/              # hub Streamlit app (all 5 projects as pages)
├── football_dashboard/     # project 1 (standalone Streamlit app)
├── signspeak/               # project 2
├── wanderwise/               # project 3
├── attendance_system/       # project 4
├── genomics_dsst/            # project 5
├── data/                    # shared raw source data (mostly gitignored)
├── scripts/                 # fetch_raw_data.sh, build_all.sh
├── tests/                   # cross-project smoke tests
└── requirements.txt
```

## Notes on scope and honesty

A couple of these are demo-scale versions of the real idea, and each
project's own README says exactly where:

- **SignSpeak** classifies still images (upload or sample), not a live
  webcam feed — this environment has no camera. The same feature-extraction
  and prediction functions drop straight into a `cv2.VideoCapture` loop for
  real-time use on a machine with a webcam.
- **Attendance System** likewise works from an uploaded photo rather than
  a live camera feed, for the same reason.
- **WanderWise**'s collaborative-filtering half runs on *simulated* user
  ratings (there's no public dataset of real travellers rating these 51
  destinations) — the content-based half runs on real, hand-curated
  destination attributes. `wanderwise/data/build_ratings.py` explains why
  and how.
- **Genetic Testing DSST** is a teaching/demo decision-support tool built
  on real HPO/OMIM data, not a diagnostic device — the app says so.

Everything else (StatsBomb match data, the Sign Language Digits Dataset,
the AT&T faces dataset, the HPO ontology and annotations) is real, openly
licensed data, not synthetic filler.
