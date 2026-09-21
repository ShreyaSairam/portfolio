"""
Lightweight smoke tests across all five projects. These check that each
project's core logic runs and produces sane output — not full ML
evaluation (that's train.py / train_model.py's job), just "does the
pipeline work end to end without crashing, on real generated artifacts."

Run after scripts/build_all.sh (needs each project's data/model files
to exist):
    cd tests && python -m pytest test_projects.py -v
or just:
    python test_projects.py
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestFootballDashboard(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "football_dashboard"))

    def test_data_loads(self):
        import importlib
        import app as football_app
        importlib.reload(football_app)
        matches, shots, passes, stats = football_app.load_data.__wrapped__()
        self.assertEqual(len(matches), 7)
        self.assertGreater(len(shots), 0)
        self.assertGreater(len(passes), 0)
        self.assertIn("France", matches["home_team"].tolist() + matches["away_team"].tolist())


class TestSignSpeak(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "signspeak"))

    def test_prediction_matches_true_label_on_a_sample(self):
        import importlib
        import app as signspeak_app
        importlib.reload(signspeak_app)
        from PIL import Image

        bundle = signspeak_app.load_model.__wrapped__()
        sample_dir = os.path.join(ROOT, "signspeak", "sample_images", "3")
        fname = sorted(os.listdir(sample_dir))[0]
        img = Image.open(os.path.join(sample_dir, fname))
        label, probs = signspeak_app.predict_digit(img, bundle)
        self.assertEqual(label, "3")
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=3)


class TestWanderWise(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "wanderwise"))

    def test_recommendations_respect_activity_filter(self):
        import importlib
        import recommender
        importlib.reload(recommender)

        recs = recommender.get_recommendations(
            activities=["beach", "relaxation"], climate="Tropical", budget_level=1, top_n=5
        )
        self.assertEqual(len(recs), 5)
        self.assertTrue((recs["match_score"] > 0).all())

    def test_collaborative_boost_excludes_liked_destination(self):
        import importlib
        import recommender
        importlib.reload(recommender)

        recs = recommender.get_recommendations(
            activities=["beach"], climate="Tropical", budget_level=1,
            liked_destinations=["Bali"], top_n=5,
        )
        self.assertNotIn("Bali", recs["name"].tolist())


class TestAttendanceSystem(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "attendance_system"))

    def test_recognizes_known_subject_from_detected_crop(self):
        import importlib
        import cv2
        import recognizer
        importlib.reload(recognizer)

        rec, labels = recognizer.load_recognizer()
        det = recognizer.load_detector()
        img_path = os.path.join(ROOT, "data", "att_faces", "s7", "1.pgm")
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces = recognizer.detect_faces(img, det)
        self.assertGreater(len(faces), 0)
        x, y, w, h = faces[0]
        crop = img[y : y + h, x : x + w]
        label_id, confidence, is_known = recognizer.recognize_face(crop, rec)
        self.assertEqual(label_id, 7)
        self.assertTrue(is_known)


class TestGenomicsDSST(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "genomics_dsst"))

    def test_recommendation_returns_ranked_diseases_with_genes(self):
        import importlib
        import engine
        importlib.reload(engine)

        terms, disease_symptoms, disease_genes = engine.load_data()
        seizure_id = terms.loc[terms["name"] == "Seizure", "hpo_id"]
        self.assertFalse(seizure_id.empty, "expected 'Seizure' in the top symptom vocabulary")

        ranked, gene_summary = engine.get_recommendation(
            [seizure_id.iloc[0]], disease_symptoms, disease_genes, top_n=5
        )
        self.assertFalse(ranked.empty)
        self.assertIn("suggested_test", ranked.columns)
        self.assertTrue(ranked["n_genes"].ge(1).all())


if __name__ == "__main__":
    unittest.main()
