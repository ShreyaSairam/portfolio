"""
Facial Recognition Attendance System.

Take a photo with your webcam, upload one, or use the sample gallery.
The app finds each face (Haar cascade), identifies it (LBPH recognizer),
and records the check-in in SQLite as present or late against the class
start time. Anyone on the roster who hasn't checked in shows as absent.
"""

import os
from datetime import date, datetime, time, timedelta

import cv2
import numpy as np
import streamlit as st
from PIL import Image

import att_db
import recognizer as R
from roster import ROSTER

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "..", "data", "att_faces")
STATUS_ICON = {"present": "🟢 present", "late": "🟠 late", "absent": "🔴 absent"}


@st.cache_resource
def load_pipeline():
    rec, _ = R.load_recognizer()
    return rec, R.load_detector()


def find_faces(pil_image, rec, det):
    img = np.array(pil_image.convert("RGB"))[:, :, ::-1].copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = R.detect_faces(gray, det)
    if len(faces) == 0 and gray.shape[0] <= 120:
        # The sample gallery images are already tight face crops.
        faces = [(0, 0, gray.shape[1], gray.shape[0])]
    results = []
    for (x, y, w, h) in faces:
        label_id, distance, known = R.recognize_face(gray[y:y + h, x:x + w], rec)
        colour = (0, 190, 0) if known else (0, 0, 230)
        cv2.rectangle(img, (x, y), (x + w, y + h), colour, 2)
        name = ROSTER.get(label_id, {}).get("name", "Unknown") if known else "Unrecognised"
        cv2.putText(img, name.split(" (")[0], (x + 3, max(14, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)
        results.append({"id": int(label_id), "distance": round(float(distance), 1), "known": known})
    return Image.fromarray(img[:, :, ::-1]), results


def main():
    st.set_page_config(page_title="Attendance System", layout="wide")
    st.title("Facial Recognition Attendance System")
    st.caption(
        "Haar cascade face detection and an LBPH face recognizer trained on the AT&T/ORL "
        "Database of Faces (40 people), **93.8% accuracy** on held-out photos. Check-ins are "
        "stored in SQLite and sorted into present, late and absent."
    )
    rec, det = load_pipeline()

    with st.container(border=True):
        s1, s2, s3, s4 = st.columns(4)
        class_date = s1.date_input("Class date", value=date.today(), key="att_date")
        start = s2.time_input("Class starts", value=time(9, 0), step=300, key="att_start")
        grace = s3.number_input("Grace period (minutes)", 0, 30, 5, key="att_grace")
        use_clock = s4.toggle("Use the real clock", value=False, key="att_clock",
                              help="Off: pick the check-in time yourself, handy for trying late arrivals.")
        if use_clock:
            arrival = datetime.now().time().replace(microsecond=0)
            st.caption(f"Check-in time: now ({arrival.strftime('%H:%M')})")
        else:
            arrival = st.time_input("Check-in time", value=time(8, 55), step=60, key="att_arrival")
    cutoff = (datetime.combine(class_date, start) + timedelta(minutes=grace)).time()
    day = class_date.isoformat()

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Check in")
        source = st.radio("Photo from", ["Sample gallery", "Webcam", "Upload"], horizontal=True, key="att_src")
        pil_image = None
        if source == "Webcam":
            snap = st.camera_input("Look at the camera", key="att_cam")
            if snap:
                pil_image = Image.open(snap)
            st.caption("The model only knows the 40 AT&T faces, so a new face shows as unrecognised. "
                       "That's the system correctly refusing a stranger.")
        elif source == "Upload":
            up = st.file_uploader("Photo with a face", type=["jpg", "jpeg", "png", "pgm"], key="att_up")
            if up:
                pil_image = Image.open(up)
        else:
            subject = st.selectbox("Student", list(range(1, 41)), key="att_subject",
                                   format_func=lambda i: ROSTER[i]["name"]
                                   + ("" if i <= att_db.CLASS_SIZE else "  (not in this class)"))
            photo = st.select_slider("Photo", options=list(range(1, 11)), value=1, key="att_photo")
            pil_image = Image.open(os.path.join(SAMPLE_DIR, f"s{subject}", f"{photo}.pgm"))
            st.image(pil_image, width=150)

        if pil_image is not None and st.button("Detect and check in", type="primary", key="att_go"):
            annotated, results = find_faces(pil_image, rec, det)
            st.image(annotated, width=320)
            if not results:
                st.warning("No face found. Try a clearer, front-on photo.")
            for r in results:
                if not r["known"]:
                    st.error(f"Face not recognised (distance {r['distance']}, needs {R.CONFIDENCE_THRESHOLD} or less).")
                    continue
                name = ROSTER[r["id"]]["name"]
                if not att_db.is_enrolled(r["id"]):
                    st.warning(f"Recognised {name}, but they aren't enrolled in this class.")
                    continue
                status = "present" if arrival <= cutoff else "late"
                before = att_db.check_in(r["id"], day, arrival.strftime("%H:%M"), status)
                if before:
                    st.info(f"{name} already checked in at {before[0]} ({before[1]}).")
                elif status == "present":
                    st.success(f"{name} checked in at {arrival.strftime('%H:%M')}: present.")
                else:
                    mins = int((datetime.combine(class_date, arrival)
                                - datetime.combine(class_date, start)).total_seconds() // 60)
                    st.warning(f"{name} checked in at {arrival.strftime('%H:%M')}: late by {mins} minutes.")

    with right:
        report = att_db.day_report(day)
        counts = report["status"].value_counts()
        st.subheader(f"Class register, {class_date.strftime('%d %b %Y')}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Present", int(counts.get("present", 0)))
        m2.metric("Late", int(counts.get("late", 0)))
        m3.metric("Absent", int(counts.get("absent", 0)))
        st.caption(f"Late means after {cutoff.strftime('%H:%M')} (start time plus grace period).")
        shown = report.assign(status=report["status"].map(STATUS_ICON))
        st.dataframe(shown, hide_index=True, width="stretch", height=460)
        absent = report.loc[report["status"] == "absent", "name"].tolist()
        with st.expander(f"Absentee list ({len(absent)})"):
            st.write(", ".join(absent) if absent else "Everyone is here.")
        if st.button("Clear this day's check-ins", key="att_reset"):
            att_db.reset_day(day)
            st.rerun()

    with st.expander("How it works"):
        st.markdown(
            """
1. **Detect**: a Haar cascade scans the photo for face-shaped patterns and returns a box per face.
2. **Recognise**: each face is resized to 100x100 and compared with the trained LBPH model, which
   describes faces by local texture patterns. It returns the closest person and a distance.
3. **Decide**: a distance of 75 or less counts as a match. Anything higher is treated as a stranger,
   so the system doesn't guess.
4. **Record**: the check-in goes into SQLite as present or late against the class start time plus
   grace period. One check-in per person per day.
5. **Report**: absent students are everyone on the roster with no check-in, found with a SQL LEFT JOIN.
"""
        )


if __name__ == "__main__":
    main()
