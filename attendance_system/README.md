# Facial Recognition Attendance System

Face detection (Haar cascade) + face recognition (LBPH — Local Binary
Patterns Histograms), both from OpenCV's contrib module, trained on the
[AT&T/ORL Database of Faces](https://github.com/wihoho/FaceRecognition)
(40 subjects, 10 images each). **93.8% held-out test accuracy.**

## Setup

```bash
# from the repo root, if not already done (AT&T faces are ~5MB, committed by default):
bash scripts/fetch_raw_data.sh
python train_model.py   # trains the LBPH recognizer -> lbph_model.yml
streamlit run app.py
```

**Note:** this needs `opencv-contrib-python`, not plain `opencv-python` —
see the top-level README for why (they conflict if both are installed;
only `opencv-contrib-python` has the `cv2.face` module LBPH lives in).

## How it's built

- **Detection** — `cv2.CascadeClassifier` with the bundled
  `haarcascade_frontalface_default.xml` (copied into `cascades/` so the
  app doesn't depend on wherever OpenCV happens to be installed).
- **Recognition** — `cv2.face.LBPHFaceRecognizer_create()`, trained in
  `train_model.py`. Training runs each AT&T image through the *same*
  Haar-detect-and-crop step the app uses at inference time before
  resizing to 100x100 — matching training and inference framing this way
  measurably improves accuracy (93.8% vs. 86% when the model is trained
  on un-cropped source images instead).
- **Attendance log** — `recognizer.mark_attendance()` appends a
  timestamped row to `attendance.csv`, and won't mark the same person
  twice on the same day.
- **Roster** — `roster.py` maps the 40 anonymous AT&T subject IDs to
  placeholder employee names/departments for the demo UI. Edit it to
  rename people, or replace the training data with your own enrolled
  faces (one folder per person, same layout as `data/att_faces/s1/`,
  `s2/`, etc.) and re-run `train_model.py`.

## Scope note

This works from an **uploaded photo**, not a live camera feed — the app
runs headlessly with no camera access here. `recognizer.detect_faces()`
and `recognizer.recognize_face()` are the same functions you'd call
inside a `cv2.VideoCapture` loop for real-time use on a machine with a
webcam:

```python
import cv2, recognizer as R
rec, labels = R.load_recognizer()
det = R.load_detector()
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    for (x, y, w, h) in R.detect_faces(gray, det):
        label_id, confidence, is_known = R.recognize_face(gray[y:y+h, x:x+w], rec)
        # draw box, mark attendance, etc.
```
