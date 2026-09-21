"""
SignSpeak — data preparation.

Source data: Sign Language Digits Dataset by Turkey Ankara Ayranci Anadolu
High School students (github.com/ardamavi/Sign-Language-Digits-Dataset),
Apache 2.0 licensed. 2,062 images, digits 0-9, 100x100 RGB.

This script:
  1. Reads the raw dataset (expected at ../data/sign_language_digits/<digit>/*.JPG,
     one folder per class — clone the dataset repo and copy its Dataset/
     folder there, or point RAW_DIR at wherever you kept it).
  2. Extracts HOG (Histogram of Oriented Gradients) features from each
     hand image after grayscale + resize + contrast normalisation.
  3. Saves the feature matrix to features.csv, and copies a small sample
     of images per class into sample_images/ for the demo page (keeps
     the repo light instead of shipping the full 2000+ image dataset).

Run once before train.py:
    python preprocess.py
"""

import os
import shutil

import cv2
import numpy as np
import pandas as pd
from skimage.feature import hog

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "data", "sign_language_digits")
SAMPLE_DIR = os.path.join(HERE, "sample_images")
FEATURES_PATH = os.path.join(HERE, "features.csv")

IMG_SIZE = 64
SAMPLES_PER_CLASS = 8


def extract_hog_features(gray_img):
    """gray_img: single-channel uint8 image, IMG_SIZE x IMG_SIZE."""
    features = hog(
        gray_img,
        orientations=9,
        pixels_per_cell=(8, 8),
        cells_per_block=(2, 2),
        block_norm="L2-Hys",
        feature_vector=True,
    )
    return features


def load_and_process_image(path):
    img = cv2.imread(path)
    if img is None:
        return None
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return gray


def main():
    if not os.path.isdir(RAW_DIR):
        raise SystemExit(
            f"Raw dataset not found at {RAW_DIR}.\n"
            "Clone https://github.com/ardamavi/Sign-Language-Digits-Dataset "
            "and copy its Dataset/ folder contents there (one subfolder per "
            "digit, 0-9)."
        )

    if os.path.isdir(SAMPLE_DIR):
        shutil.rmtree(SAMPLE_DIR)
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    rows = []
    classes = sorted(os.listdir(RAW_DIR))
    for label in classes:
        class_dir = os.path.join(RAW_DIR, label)
        if not os.path.isdir(class_dir):
            continue
        files = sorted(os.listdir(class_dir))
        os.makedirs(os.path.join(SAMPLE_DIR, label), exist_ok=True)

        for i, fname in enumerate(files):
            path = os.path.join(class_dir, fname)
            gray = load_and_process_image(path)
            if gray is None:
                continue
            feats = extract_hog_features(gray)
            row = {"label": label}
            row.update({f"f{j}": v for j, v in enumerate(feats)})
            rows.append(row)

            if i < SAMPLES_PER_CLASS:
                shutil.copy(path, os.path.join(SAMPLE_DIR, label, fname))

        print(f"Class {label}: {len(files)} images processed")

    df = pd.DataFrame(rows)
    df.to_csv(FEATURES_PATH, index=False)
    print(f"\nSaved {len(df)} feature rows ({df.shape[1] - 1} features) to {FEATURES_PATH}")
    print(f"Sample images copied to {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
