"""
Facial Recognition Attendance System — model training.

Uses OpenCV's Haar cascade for face detection and its LBPH
(Local Binary Patterns Histograms) face recognizer for identification,
both from opencv-contrib-python — a lightweight, fully offline pipeline
(no external model downloads needed).

Trained on the AT&T/ORL Database of Faces (40 subjects x 10 images,
92x112 grayscale, released by AT&T Laboratories Cambridge for face
recognition research). Subjects s1..s40 are treated here as 40 enrolled
"employees" for the attendance demo, with editable display names in
roster.py.

Run once before app.py:
    python train_model.py
"""

import os
import pickle

import cv2
import numpy as np
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "data", "att_faces")
MODEL_PATH = os.path.join(HERE, "lbph_model.yml")
LABELS_PATH = os.path.join(HERE, "labels.pkl")
CASCADE_PATH = os.path.join(HERE, "cascades", "haarcascade_frontalface_default.xml")

FACE_SIZE = (100, 100)


def load_dataset():
    """
    Loads AT&T faces and runs them through the SAME Haar-cascade detect
    + crop step app.py uses at inference time, so the recognizer trains
    on the same kind of framing it will see from real detections
    (rather than training on whole, already-tightly-cropped source
    images and then evaluating on a different, Haar-cropped framing —
    which silently hurts accuracy because the two crops don't line up).
    """
    detector = cv2.CascadeClassifier(CASCADE_PATH)

    images, labels = [], []
    subjects = sorted(
        [d for d in os.listdir(RAW_DIR) if d.startswith("s") and d[1:].isdigit()],
        key=lambda s: int(s[1:]),
    )
    n_fallback = 0
    for subject in subjects:
        subject_dir = os.path.join(RAW_DIR, subject)
        label_id = int(subject[1:])
        for fname in sorted(os.listdir(subject_dir)):
            if not fname.endswith(".pgm"):
                continue
            path = os.path.join(subject_dir, fname)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            faces = detector.detectMultiScale(
                img, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
            )
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face_crop = img[y : y + h, x : x + w]
            else:
                face_crop = img  # fallback: use whole (already face-only) image
                n_fallback += 1

            face_crop = cv2.resize(face_crop, FACE_SIZE)
            images.append(face_crop)
            labels.append(label_id)

    print(f"Haar detection fell back to whole-image crop for {n_fallback}/{len(images)} images")
    return images, labels, subjects


def main():
    images, labels, subjects = load_dataset()
    print(f"Loaded {len(images)} images across {len(subjects)} subjects")

    idx_train, idx_test = train_test_split(
        range(len(images)), test_size=0.2, random_state=42, stratify=labels
    )
    train_images = [images[i] for i in idx_train]
    train_labels = [labels[i] for i in idx_train]
    test_images = [images[i] for i in idx_test]
    test_labels = [labels[i] for i in idx_test]

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(train_images, np.array(train_labels))
    recognizer.save(MODEL_PATH)

    correct = 0
    for img, true_label in zip(test_images, test_labels):
        pred_label, confidence = recognizer.predict(img)
        if pred_label == true_label:
            correct += 1
    accuracy = correct / len(test_images)
    print(f"Held-out test accuracy: {accuracy:.3f} ({correct}/{len(test_images)})")

    with open(LABELS_PATH, "wb") as f:
        pickle.dump({"subjects": subjects}, f)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Labels saved to {LABELS_PATH}")


if __name__ == "__main__":
    main()
