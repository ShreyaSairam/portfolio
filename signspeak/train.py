"""
SignSpeak — train the letter classifier.

Data: Sign Language MNIST (CC0), downloaded by scripts/fetch_raw_data.sh to
../data/sign_mnist/. 27,455 training and 7,172 test images, 24 letters.

Pipeline: HOG features -> StandardScaler -> PCA (160 components) -> RBF SVM.
Accuracy is reported on the dataset's own separate test file, so the model
never sees those images during training.

Outputs (committed to the repo so the app works without retraining):
    model.joblib      the trained pipeline
    metrics.json      test accuracy and per-letter accuracy
    sample_frames/    a few test images per letter for demo mode

Run:
    python train.py
"""

import json
import os
import time

import cv2
import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from sign_engine import LETTERS, MODEL_PATH, hog_features

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "sign_mnist")
SAMPLE_DIR = os.path.join(HERE, "sample_frames")
SAMPLES_PER_LETTER = 4


def load(name):
    df = pd.read_csv(os.path.join(DATA_DIR, name))
    images = df.drop(columns="label").values.reshape(-1, 28, 28).astype(np.uint8)
    return images, df["label"].values


def featurise(images):
    return np.array([hog_features(img.astype(np.float32) / 255.0) for img in images])


def main():
    X_train_img, y_train = load("sign_mnist_train.csv")
    X_test_img, y_test = load("sign_mnist_test.csv")
    print(f"Train {len(y_train)} images, test {len(y_test)} images")

    t0 = time.time()
    X_train, X_test = featurise(X_train_img), featurise(X_test_img)
    print(f"HOG features {X_train.shape[1]} dims ({time.time() - t0:.0f}s)")

    model = make_pipeline(
        StandardScaler(),
        PCA(n_components=160, random_state=0),
        SVC(C=5, gamma="scale", probability=True, random_state=0),
    )
    t0 = time.time()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print(f"Test accuracy {acc:.3f} ({time.time() - t0:.0f}s to train)")

    per_letter = {
        LETTERS[int(c)]: round(float((pred[y_test == c] == c).mean()), 3)
        for c in np.unique(y_test)
    }
    joblib.dump(model, MODEL_PATH, compress=3)
    with open(os.path.join(HERE, "metrics.json"), "w") as f:
        json.dump(
            {
                "test_accuracy": round(float(acc), 4),
                "train_images": int(len(y_train)),
                "test_images": int(len(y_test)),
                "per_letter_accuracy": per_letter,
            },
            f,
            indent=2,
        )

    # A few held-out test images per letter, upscaled for display in demo mode.
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    for label, letter in LETTERS.items():
        idx = np.where(y_test == label)[0][:SAMPLES_PER_LETTER]
        for k, i in enumerate(idx):
            big = cv2.resize(X_test_img[i], (224, 224), interpolation=cv2.INTER_NEAREST)
            cv2.imwrite(os.path.join(SAMPLE_DIR, f"{letter}_{k}.png"), big)
    print(f"Saved model to {MODEL_PATH} and sample frames to {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
