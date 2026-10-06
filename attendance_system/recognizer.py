"""
Facial Recognition Attendance System — recognition + attendance logging.

Wraps the trained LBPH recognizer (train_model.py) and Haar cascade face
detector into a simple API:

- detect_faces(image): find face bounding boxes in a BGR image
- recognize_face(face_crop): return (subject_id, confidence) for a
  cropped, grayscale face
- mark_attendance(subject_id): append a timestamped row to attendance.csv
    if this subject hasn't already been marked today

LBPH confidence is a *distance* (lower = more confident match); a
threshold decides whether to treat a prediction as "recognised" versus
"unknown".
"""

import csv
import os
import pickle
from datetime import datetime

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "lbph_model.yml")
LABELS_PATH = os.path.join(HERE, "labels.pkl")
CASCADE_PATH = os.path.join(HERE, "cascades", "haarcascade_frontalface_default.xml")
ATTENDANCE_LOG = os.path.join(HERE, "attendance.csv")

FACE_SIZE = (100, 100)
CONFIDENCE_THRESHOLD = 75.0  # LBPH distance; lower = better match


def load_recognizer():
    if not (os.path.exists(MODEL_PATH) and os.path.exists(LABELS_PATH)):
        # The trained model isn't committed (it's 35 MB); training takes a few seconds.
        import train_model

        train_model.main()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    with open(LABELS_PATH, "rb") as f:
        labels = pickle.load(f)
    return recognizer, labels


def load_detector():
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    return detector


def detect_faces(gray_image, detector):
    faces = detector.detectMultiScale(
        gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    return faces  # list of (x, y, w, h)


def recognize_face(face_gray, recognizer):
    face_gray = cv2.resize(face_gray, FACE_SIZE)
    label_id, confidence = recognizer.predict(face_gray)
    is_known = confidence <= CONFIDENCE_THRESHOLD
    return label_id, confidence, is_known


def mark_attendance(subject_id, name, department):
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")

    already_marked = False
    if os.path.exists(ATTENDANCE_LOG):
        with open(ATTENDANCE_LOG, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["subject_id"] == str(subject_id) and row["date"] == today:
                    already_marked = True
                    break

    if already_marked:
        return False

    file_exists = os.path.exists(ATTENDANCE_LOG)
    with open(ATTENDANCE_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["subject_id", "name", "department", "date", "time"])
        writer.writerow([subject_id, name, department, today, now])
    return True


def read_attendance_log():
    import pandas as pd

    if not os.path.exists(ATTENDANCE_LOG):
        return pd.DataFrame(
            columns=["subject_id", "name", "department", "date", "time"]
        )
    return pd.read_csv(ATTENDANCE_LOG)
