"""
Facial Recognition Attendance System — dashboard page.

Upload a photo (a snapshot from a webcam or phone camera works), the app
detects faces with a Haar cascade, identifies each one with the trained
LBPH recognizer, and marks attendance for anyone it recognises with
enough confidence. There's also a gallery of sample AT&T faces to try
without needing your own photo.

Note on scope: this runs on an uploaded still image because this app is
hosted headlessly with no camera access. recognizer.py's detect_faces /
recognize_face functions are the same ones you'd call inside a
cv2.VideoCapture loop for a real-time desktop version — see the README.
"""

import os

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

import recognizer as R
from roster import ROSTER

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "..", "data", "att_faces")


@st.cache_resource
def load_pipeline():
    rec, labels = R.load_recognizer()
    det = R.load_detector()
    return rec, det


def process_image(pil_image, rec, det):
    img = np.array(pil_image.convert("RGB"))[:, :, ::-1].copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = R.detect_faces(gray, det)

    results = []
    for (x, y, w, h) in faces:
        face_crop = gray[y : y + h, x : x + w]
        label_id, confidence, is_known = R.recognize_face(face_crop, rec)
        info = ROSTER.get(label_id, {"name": "Unknown", "department": "-"})
        color = (0, 200, 0) if is_known else (0, 0, 255)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        label_text = info["name"] if is_known else "Unrecognised"
        cv2.putText(
            img, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )
        results.append(
            {
                "subject_id": label_id,
                "name": info["name"],
                "department": info["department"],
                "confidence": round(confidence, 1),
                "recognised": is_known,
            }
        )

    annotated = Image.fromarray(img[:, :, ::-1])
    return annotated, results


def main():
    st.set_page_config(page_title="Attendance System", layout="wide")
    st.title("Facial Recognition Attendance System")
    st.caption(
        "OpenCV Haar cascade face detection + LBPH face recognizer, trained "
        "on the AT&T/ORL Database of Faces (40 subjects). 93.8% held-out "
        "recognition accuracy."
    )

    rec, det = load_pipeline()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Check in")
        source = st.radio("Image source", ["Sample gallery", "Upload a photo"], horizontal=True)

        pil_image = None
        if source == "Upload a photo":
            uploaded = st.file_uploader("Photo with a face", type=["jpg", "jpeg", "png"])
            if uploaded:
                pil_image = Image.open(uploaded)
        else:
            subject_dirs = sorted(
                d for d in os.listdir(SAMPLE_DIR)
                if d.startswith("s") and d[1:].isdigit()
                and os.path.isdir(os.path.join(SAMPLE_DIR, d))
            )
            subject = st.selectbox(
                "Sample subject",
                subject_dirs,
                format_func=lambda s: ROSTER.get(int(s[1:]), {}).get("name", s),
            )
            if subject.startswith("s"):
                sample_files = sorted(
                    f for f in os.listdir(os.path.join(SAMPLE_DIR, subject)) if f.endswith(".pgm")
                )
                fname = st.selectbox("Sample image", sample_files)
                pil_image = Image.open(os.path.join(SAMPLE_DIR, subject, fname))

        if pil_image:
            st.image(pil_image, caption="Input", width=250)

        if pil_image and st.button("Detect & check in"):
            annotated, results = process_image(pil_image, rec, det)
            st.image(annotated, caption="Detected faces", use_container_width=True)

            if not results:
                st.warning("No faces detected in this image.")
            for r in results:
                if r["recognised"]:
                    marked = R.mark_attendance(r["subject_id"], r["name"], r["department"])
                    if marked:
                        st.success(
                            f"Checked in: {r['name']} ({r['department']}) — "
                            f"confidence distance {r['confidence']}"
                        )
                    else:
                        st.info(f"{r['name']} already checked in today.")
                else:
                    st.error(
                        f"Face detected but not recognised confidently "
                        f"(distance {r['confidence']}, threshold "
                        f"{R.CONFIDENCE_THRESHOLD})."
                    )

    with col2:
        st.subheader("Today's attendance log")
        log_df = R.read_attendance_log()
        today = pd.Timestamp.now().strftime("%Y-%m-%d")
        today_log = log_df[log_df["date"] == today] if not log_df.empty else log_df
        st.dataframe(today_log, hide_index=True, use_container_width=True)
        st.caption(f"{len(today_log)} check-ins today · {len(log_df)} total logged")

        if not log_df.empty:
            by_dept = log_df.groupby("department").size().reset_index(name="check_ins")
            st.bar_chart(by_dept.set_index("department"))


if __name__ == "__main__":
    main()
