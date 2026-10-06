# Shreya Sairam: Project Demos

Five working projects in one Streamlit app. Each one runs on real or openly licensed data and keeps its records in SQLite.

**Live app:** https://shreyasairam-projects.streamlit.app
**Portfolio:** https://shreyasairam.github.io

| Project | What it does | Key techniques |
|---|---|---|
| [Football Analytics](football_dashboard/) | France's 2018 World Cup: shot maps with expected goals (xG), team comparison, player explorer, pass heatmaps and a read-only SQL explorer | pandas, Plotly, SQLite, StatsBomb open data |
| [SignSpeak](signspeak/) | Reads ASL letters A to Y from a webcam, 95.2% accuracy on 7,172 separate test images; demo mode spells words without a camera | HOG features, PCA, SVM, streamlit-webrtc |
| [WanderWise](wanderwise/) | Hybrid travel recommender with live weather, your location, a Gemini chat assistant, accounts and saved favourites | content plus collaborative filtering, Open-Meteo, Gemini API, PBKDF2 password hashing |
| [Attendance System](attendance_system/) | Check in by webcam or photo; present, late and absent against the class start time | Haar cascade, LBPH face recognition (93.8% held-out accuracy), SQL LEFT JOIN for absentees |
| [Genetic Testing Decision Support](genomics_dsst/) | A GP enters symptoms and gets ranked genetic conditions, the genes behind them, a confidence level and one recommended test | information-weighted symptom matching, Human Phenotype Ontology |

## Run it locally

```bash
git clone https://github.com/ShreyaSairam/portfolio
cd portfolio
pip install -r requirements.txt
streamlit run dashboard/Home.py
```

Everything the app needs is in the repo: processed data, the SignSpeak model, and the face images. The face model trains itself in a few seconds on first run, and the SQLite databases are created automatically.

**Optional, for real AI chat answers in WanderWise:** get a free key at https://aistudio.google.com/apikey, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste it in. Without a key, WanderWise answers from the trip facts and says so.

## Rebuild the data and models from scratch

```bash
bash scripts/fetch_raw_data.sh   # downloads StatsBomb, Sign Language MNIST, AT&T faces, HPO
bash scripts/build_all.sh        # processes the data and retrains every model
```

## Tests

```bash
python -m pytest tests -q
```

Checks the core logic of all five projects: SQL queries and the read-only guard, letter predictions on held-out images, recommendations, account security, face recognition, present/late/absent logic, and disease ranking.

## Deploy (Streamlit Community Cloud)

1. Sign in at https://share.streamlit.io with GitHub.
2. Create app → this repo, branch `main`, main file `dashboard/Home.py`, Python 3.12.
3. Optional: in Advanced settings → Secrets, add `GOOGLE_API_KEY = "..."`.

Each project has a direct link: `/football`, `/signspeak`, `/wanderwise`, `/attendance`, `/genomics`.

## Layout

```
dashboard/            hub app: Home.py plus one page per project
football_dashboard/   app.py, fb_db.py (SQLite), prepare_data.py
signspeak/            app.py, sign_engine.py, sign_db.py, train.py, model.joblib
wanderwise/           app.py, recommender.py, ww_services.py, ww_db.py, data/
attendance_system/    app.py, recognizer.py, att_db.py, train_model.py
genomics_dsst/        app.py, engine.py, gx_db.py, prepare_data.py, data/
data/                 AT&T faces (committed); raw downloads (ignored)
tests/                pytest smoke tests
```

Data sources and licences are listed in [DATA_LICENSES.md](DATA_LICENSES.md).
