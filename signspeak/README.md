# SignSpeak — Sign Language Digit Recognition

A hand-sign digit classifier (0-9): HOG (Histogram of Oriented Gradients)
features + an RBF-kernel SVM, trained on the
[Sign Language Digits Dataset](https://github.com/ardamavi/Sign-Language-Digits-Dataset)
(2,062 images, Apache 2.0 licensed). **86% held-out test accuracy.**

## Setup

```bash
# from the repo root, if not already done:
bash scripts/fetch_raw_data.sh
python preprocess.py   # extracts HOG features -> features.csv, copies sample images
python train.py        # trains the SVM -> model.pkl
streamlit run app.py
```

## How it's built

1. **Preprocess** (`preprocess.py`) — each image is resized to 64x64,
   converted to grayscale, and contrast-normalised with histogram
   equalisation, then a 1,764-dimension HOG feature vector is extracted.
2. **Train** (`train.py`) — an 80/20 train/test split with 5-fold
   cross-validation, an RBF SVM (`C=10`) fit on standardised features.
3. **App** (`app.py`) — loads the trained model and lets you try a sample
   image or upload your own hand-sign photo for a live prediction with
   per-class confidence.

## Scope note

This classifies **still images**, not a live webcam feed — the app runs
headlessly with no camera access here. `predict_digit()` in `app.py` (which
wraps `extract_hog_features()` from `preprocess.py`) is exactly the
function you'd call inside a `cv2.VideoCapture` loop for real-time
recognition on a machine with a webcam:

```python
import cv2
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    # crop to the hand region (e.g. via a bounding box or hand detector),
    # then feed the PIL/np crop through predict_digit(crop, bundle)
```
