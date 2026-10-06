"""
Smoke tests for the core logic of all five projects (no browser needed).

Run from the repo root:
    python -m pytest tests -q
"""

import importlib
import os
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def use(project):
    path = os.path.join(ROOT, project)
    if path not in sys.path:
        sys.path.insert(0, path)


# ---------------------------------------------------------------- football
def test_football_sql_tables_and_read_only_guard():
    use("football_dashboard")
    fb_db = importlib.import_module("fb_db")
    matches, shots, passes, stats = fb_db.load_all()
    assert len(matches) == 7
    assert shots["is_goal"].dtype == bool and shots["is_goal"].sum() > 0
    assert len(passes) > 1000 and len(stats) > 100
    top = fb_db.read_only(fb_db.SAMPLE_QUERIES["Top scorers by xG"])
    assert top.iloc[0]["player"] == "Antoine Griezmann"
    for bad in ("DELETE FROM matches", "SELECT 1; DROP TABLE matches"):
        try:
            fb_db.read_only(bad)
            raise AssertionError("write query was allowed")
        except ValueError:
            pass


# ---------------------------------------------------------------- signspeak
def test_signspeak_reads_held_out_samples():
    use("signspeak")
    se = importlib.import_module("sign_engine")
    import cv2

    model = se.load_model()
    sample_dir = os.path.join(ROOT, "signspeak", "sample_frames")
    correct = total = 0
    for letter in ("A", "B", "C", "L", "Y"):
        img = cv2.imread(os.path.join(sample_dir, f"{letter}_0.png"), cv2.IMREAD_GRAYSCALE)
        pred, conf, top3 = se.predict(model, img)
        total += 1
        correct += pred == letter
        assert 0 <= conf <= 1 and len(top3) == 3
    assert correct >= 4


def test_signspeak_handles_a_webcam_sized_colour_frame():
    use("signspeak")
    se = importlib.import_module("sign_engine")
    roi, (x0, y0, side) = se.center_square(np.zeros((480, 640, 3), np.uint8))
    assert roi.shape[:2] == (side, side)
    letter, conf, _ = se.predict(se.load_model(), roi)
    assert letter in se.LETTERS.values()


# ---------------------------------------------------------------- wanderwise
def test_wanderwise_recommendations_and_coordinates():
    use("wanderwise")
    rec = importlib.import_module("recommender")
    out = rec.get_recommendations(["beach"], "Tropical", 2, top_n=5)
    assert len(out) == 5 and out["activities"].str.contains("beach").all()
    assert out[["lat", "lon"]].notna().all().all()
    liked = rec.get_recommendations(["culture"], "Temperate", 2, liked_destinations=["Paris"], top_n=5)
    assert "Paris" not in liked["name"].tolist()


def test_wanderwise_accounts_and_offline_chat():
    use("wanderwise")
    db = importlib.import_module("ww_db")
    svc = importlib.import_module("ww_services")
    db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
    assert db.create_user("tester", "secret12")[0]
    assert not db.create_user("tester", "secret12")[0]
    uid = db.check_login("Tester", "secret12")
    assert uid and db.check_login("tester", "wrong") is None
    assert db.toggle_favourite(uid, "Bali") is True
    assert db.favourites(uid)["destination"].tolist() == ["Bali"]
    assert db.toggle_favourite(uid, "Bali") is False
    assert 4000 < svc.distance_km((-37.81, 144.96), (-8.65, 115.22)) < 5000
    dest = {"name": "Bali", "country": "Indonesia", "region": "Southeast Asia", "climate": "Tropical",
            "best_season": "Apr-Oct", "activities": "beach|nature", "avg_daily_cost_usd": 45}
    ctx = svc.trip_context(dest, None, "Melbourne", 4500)
    assert "Apr-Oct" in svc.offline_answer("when is the best weather?", ctx)
    assert "45" in svc.offline_answer("how much does it cost?", ctx)


# ---------------------------------------------------------------- attendance
def test_attendance_recognises_and_tracks_status():
    use("attendance_system")
    R = importlib.import_module("recognizer")
    att_db = importlib.import_module("att_db")
    import cv2

    rec, _ = R.load_recognizer()
    img = cv2.imread(os.path.join(ROOT, "data", "att_faces", "s1", "10.pgm"), cv2.IMREAD_GRAYSCALE)
    faces = R.detect_faces(img, R.load_detector())
    x, y, w, h = faces[0] if len(faces) else (0, 0, img.shape[1], img.shape[0])
    label, distance, known = R.recognize_face(img[y:y + h, x:x + w], rec)
    assert label == 1 and known

    att_db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
    assert att_db.check_in(1, "2026-01-01", "08:55", "present") is None
    assert att_db.check_in(1, "2026-01-01", "09:30", "late") == ("08:55", "present")
    att_db.check_in(2, "2026-01-01", "09:12", "late")
    report = att_db.day_report("2026-01-01")
    counts = report["status"].value_counts()
    assert counts["present"] == 1 and counts["late"] == 1 and counts["absent"] == att_db.CLASS_SIZE - 2


# ---------------------------------------------------------------- genomics
def test_genomics_ranks_noonan_case_first():
    use("genomics_dsst")
    sys.modules.pop("engine", None)
    gx_db = importlib.import_module("gx_db")
    engine = importlib.import_module("engine")
    gx_db.DB_PATH = os.path.join(tempfile.mkdtemp(), "t.db")
    terms, ds, dg = gx_db.load_tables()
    names = ["Hypertrophic cardiomyopathy", "Hypogonadism", "Bruising susceptibility", "Male infertility", "Dry skin"]
    ids = terms[terms["name"].isin(names)]["hpo_id"].tolist()
    ranked, _ = engine.get_recommendation(ids, ds, dg, top_n=5, weights=engine.symptom_weights(ds))
    assert ranked.iloc[0]["disease_name"] == "Noonan syndrome 1"
    assert ranked.iloc[0]["confidence"] == "High"
    test, reason, genes = engine.overall_recommendation(ranked)
    assert test in {"Single-gene sequencing", "Targeted multi-gene panel", "Exome or genome sequencing"}
    assert "PTPN11" in genes
