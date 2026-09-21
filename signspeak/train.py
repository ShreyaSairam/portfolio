"""
SignSpeak — model training.

Trains an SVM classifier on the HOG features extracted by preprocess.py
to recognise hand-sign digits (0-9). Reports accuracy on a held-out test
split and saves the fitted model + label encoder for the dashboard page
and for real-time webcam use in app.py.

Run after preprocess.py:
    python train.py
"""

import os
import pickle

import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = os.path.join(HERE, "features.csv")
MODEL_PATH = os.path.join(HERE, "model.pkl")


def main():
    df = pd.read_csv(FEATURES_PATH)
    X = df.drop(columns=["label"]).values
    y = df["label"].astype(str).values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clf = SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=42)
    clf.fit(X_train_s, y_train)

    cv_scores = cross_val_score(clf, scaler.transform(X), y_enc, cv=5)
    print(f"5-fold CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    y_pred = clf.predict(X_test_s)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nHeld-out test accuracy: {acc:.3f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "scaler": scaler, "label_encoder": le}, f)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
