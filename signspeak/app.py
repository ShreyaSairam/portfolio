"""
SignSpeak — Sign Language Digit Recognition dashboard page.

Loads the trained SVM model (see preprocess.py / train.py) and lets the
user either pick a sample image or upload their own hand-sign photo to
get a live prediction with per-class confidence.

Note on scope: this recognises the 10 digit signs (0-9) from the Sign
Language Digits Dataset, as a still-image classifier (HOG features + SVM)
rather than a live webcam feed, since this app runs in a headless server
environment with no camera access. The same model + feature pipeline
(predict_digit below) drops straight into a cv2.VideoCapture loop for
real-time use on a machine with a webcam — see the "Run it live" note
in the README.
"""

import os
import pickle

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from preprocess import extract_hog_features, IMG_SIZE

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model.pkl")
SAMPLE_DIR = os.path.join(HERE, "sample_images")


@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def predict_digit(pil_image, bundle):
    img = np.array(pil_image.convert("RGB"))[:, :, ::-1]  # RGB -> BGR
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    feats = extract_hog_features(gray).reshape(1, -1)
    feats_scaled = bundle["scaler"].transform(feats)
    pred = bundle["model"].predict(feats_scaled)[0]
    proba = bundle["model"].predict_proba(feats_scaled)[0]
    label = bundle["label_encoder"].inverse_transform([pred])[0]
    class_probs = dict(zip(bundle["label_encoder"].classes_, proba))
    return label, class_probs


def main():
    st.set_page_config(page_title="SignSpeak", layout="wide")
    st.title("SignSpeak — Sign Language Digit Recognition")
    st.caption(
        "HOG features + SVM, trained on the Sign Language Digits Dataset "
        "(2,062 images, digits 0-9). 86% held-out test accuracy."
    )

    if not os.path.exists(MODEL_PATH):
        st.error(
            "Model not found. Run `python preprocess.py` then `python train.py` "
            "inside signspeak/ first."
        )
        return

    bundle = load_model()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Try a sample")
        digits = sorted(os.listdir(SAMPLE_DIR))
        digit = st.selectbox("Digit class", digits)
        class_dir = os.path.join(SAMPLE_DIR, digit)
        files = sorted(os.listdir(class_dir))
        fname = st.selectbox("Sample image", files)
        sample_img = Image.open(os.path.join(class_dir, fname))
        st.image(sample_img, caption=f"Sample — true label {digit}", width=250)
        if st.button("Predict sample"):
            label, probs = predict_digit(sample_img, bundle)
            st.success(f"Predicted digit: **{label}**")
            st.bar_chart(probs)

    with col2:
        st.subheader("Upload your own")
        uploaded = st.file_uploader("Hand sign image", type=["jpg", "jpeg", "png"])
        if uploaded:
            user_img = Image.open(uploaded)
            st.image(user_img, caption="Uploaded image", width=250)
            label, probs = predict_digit(user_img, bundle)
            st.success(f"Predicted digit: **{label}**")
            st.bar_chart(probs)
        else:
            st.info("Upload a clear photo of a single hand showing a digit 0-9.")

    with st.expander("How this works"):
        st.markdown(
            """
            1. **Preprocess** — image resized to 64x64, converted to grayscale,
               contrast-normalised with histogram equalisation.
            2. **Feature extraction** — Histogram of Oriented Gradients (HOG)
               captures the hand's shape and finger edges as a 1,764-dim vector.
            3. **Classification** — an RBF-kernel SVM (scikit-learn), trained
               on an 80/20 split with 5-fold cross-validation, predicts the
               digit and a confidence score per class.
            """
        )


if __name__ == "__main__":
    main()
