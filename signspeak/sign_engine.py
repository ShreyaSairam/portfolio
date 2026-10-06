"""
SignSpeak recognition engine.

Shared by the live webcam path, the demo mode and the photo upload path,
so every input goes through exactly the same steps:

    image -> grayscale -> 28x28 -> HOG features -> scaler -> PCA -> SVM -> letter

Training data is Sign Language MNIST (24 static ASL letters, 28x28
grayscale). J and Z are not included because they are signed with
movement, so a single frame cannot capture them.
"""

import os

import cv2
import joblib
import numpy as np
from skimage.feature import hog

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model.joblib")

IMG_SIZE = 28

# Sign Language MNIST labels are 0-25 for A-Z, with 9 (J) and 25 (Z) unused.
LETTERS = {i: chr(ord("A") + i) for i in range(26) if i not in (9, 25)}


def hog_features(gray28):
    """gray28: 28x28 float image in [0, 1]. Returns a 1,296-dim HOG vector."""
    return hog(
        gray28,
        orientations=9,
        pixels_per_cell=(4, 4),
        cells_per_block=(2, 2),
    )


def to_gray28(image):
    """Accepts a BGR/RGB uint8 array or a 2D grayscale array of any size."""
    img = np.asarray(image)
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    return img.astype(np.float32) / 255.0


def center_square(image, fraction=0.6):
    """The guide box used on the live camera: a centred square crop."""
    h, w = image.shape[:2]
    side = int(min(h, w) * fraction)
    y0, x0 = (h - side) // 2, (w - side) // 2
    return image[y0:y0 + side, x0:x0 + side], (x0, y0, side)


def load_model(path=MODEL_PATH):
    return joblib.load(path)


def predict(model, image):
    """Returns (letter, confidence, top3) for one image."""
    feats = hog_features(to_gray28(image)).reshape(1, -1)
    proba = model.predict_proba(feats)[0]
    order = np.argsort(proba)[::-1]
    classes = model.classes_
    top3 = [(LETTERS[int(classes[i])], float(proba[i])) for i in order[:3]]
    letter, conf = top3[0]
    return letter, conf, top3
