"""
SignSpeak — real-time sign language letter recognition.

Three ways in, one engine (sign_engine.predict):
  * Live camera: your browser webcam via streamlit-webrtc. Hold one hand
    sign inside the guide box and the letter is drawn on the video.
  * Demo mode: spells a word from held-out test images, for when there is
    no camera (or a recruiter just wants to see it work).
  * Upload a photo: one still image.

Every prediction is logged to a SQLite database (sign_db.py).
"""

import json
import os
import threading
import time

import cv2
import numpy as np
import streamlit as st
from PIL import Image

import sign_db
from sign_engine import LETTERS, MODEL_PATH, center_square, load_model, predict

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "sample_frames")
VALID = set(LETTERS.values())


@st.cache_resource
def get_model():
    return load_model()


@st.cache_data
def get_metrics():
    with open(os.path.join(HERE, "metrics.json")) as f:
        return json.load(f)


def sample_frame(letter, k):
    path = os.path.join(SAMPLE_DIR, f"{letter}_{k % 4}.png")
    return cv2.imread(path, cv2.IMREAD_GRAYSCALE)


def letter_card(letter, conf):
    st.markdown(
        f"""<div style="border:1px solid rgba(128,128,128,.3);border-radius:12px;
        padding:14px 18px;text-align:center">
        <div style="font-size:13px;opacity:.7">Predicted letter</div>
        <div style="font-size:64px;font-weight:700;line-height:1.1">{letter}</div>
        <div style="font-size:13px;opacity:.7">{conf:.0%} confidence</div></div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- live camera
class LiveState:
    """Shared between the video thread and the page."""

    def __init__(self):
        self.lock = threading.Lock()
        self.letter, self.conf, self.text = "", 0.0, ""
        self._streak_letter, self._streak = "", 0


def live_camera(model):
    try:
        from streamlit_webrtc import WebRtcMode, webrtc_streamer
        import av
    except ImportError:
        st.warning("Live camera needs the streamlit-webrtc package (see requirements.txt).")
        return

    st.markdown(
        "Allow camera access, then hold **one hand sign inside the green box** "
        "against a plain background. Hold a letter steady for about a second "
        "to add it to the text."
    )
    if "live_state" not in st.session_state:
        st.session_state.live_state = LiveState()
    state = st.session_state.live_state
    hold_frames = 12

    def callback(frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)  # mirror, so it feels like a mirror to the signer
        roi, (x0, y0, side) = center_square(img)
        letter, conf, _ = predict(model, roi)
        with state.lock:
            state.letter, state.conf = letter, conf
            if conf >= 0.6 and letter == state._streak_letter:
                state._streak += 1
                if state._streak == hold_frames:
                    state.text = (state.text + letter)[-24:]
                    sign_db.log_prediction("live camera", letter, conf)
            else:
                state._streak_letter, state._streak = letter, 1
            text = state.text
        cv2.rectangle(img, (x0, y0), (x0 + side, y0 + side), (60, 200, 90), 3)
        cv2.rectangle(img, (0, 0), (img.shape[1], 64), (20, 24, 60), -1)
        cv2.putText(img, f"{letter}  {conf:.0%}", (16, 46), cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                    (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(img, text, (230, 46), cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                    (120, 220, 255), 2, cv2.LINE_AA)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    webrtc_streamer(
        key="signspeak-live",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
        video_frame_callback=callback,
        async_processing=True,
    )
    if st.button("Clear text", key="live_clear"):
        with state.lock:
            state.text = ""
    st.caption(
        "Works best with good lighting and a plain wall behind your hand. "
        "The model was trained on 28x28 grayscale hand crops, so busy backgrounds "
        "lower its confidence."
    )


# ---------------------------------------------------------------- demo mode
def demo_mode(model):
    st.markdown(
        "No camera? Type a word and SignSpeak spells it out frame by frame, using "
        "test images the model never saw during training."
    )
    c1, c2 = st.columns([3, 1])
    word = c1.text_input("Word to sign", value="HELLO", max_chars=12, key="demo_word")
    speed = c2.select_slider("Speed", options=["Slow", "Normal", "Fast"], value="Normal")
    delay = {"Slow": 1.4, "Normal": 0.9, "Fast": 0.5}[speed]
    clean = "".join(ch for ch in word.upper() if ch in VALID)
    skipped = sorted(set(ch for ch in word.upper() if ch.isalpha() and ch not in VALID))
    if skipped:
        st.caption(f"Skipping {', '.join(skipped)}: J and Z are signed with movement, so a single frame can't show them.")

    if st.button("Play", type="primary", key="demo_play", disabled=not clean):
        frame_col, info_col = st.columns([2, 3])
        frame_slot, card_slot = frame_col.empty(), info_col.empty()
        text_slot, prog = info_col.empty(), info_col.progress(0.0)
        spelled = ""
        for i, ch in enumerate(clean):
            gray = sample_frame(ch, i)
            letter, conf, top3 = predict(model, gray)
            spelled += letter
            sign_db.log_prediction("demo mode", letter, conf)
            shown = cv2.cvtColor(cv2.resize(gray, (360, 360), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2RGB)
            cv2.rectangle(shown, (0, 0), (360, 44), (20, 24, 60), -1)
            cv2.putText(shown, f"frame {i + 1}/{len(clean)}   true sign: {ch}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            frame_slot.image(shown, width=340)
            with card_slot.container():
                letter_card(letter, conf)
                st.caption("Runner-up guesses: " + ", ".join(f"{l} {p:.0%}" for l, p in top3[1:]))
            text_slot.markdown(f"#### Text so far: `{spelled}`")
            prog.progress((i + 1) / len(clean))
            time.sleep(delay)
        if spelled == clean:
            st.success(f"Spelled **{spelled}** correctly.")
        else:
            st.warning(f"Read **{spelled}** for **{clean}**. Look at which letters it confused.")


# ---------------------------------------------------------------- upload
def upload_photo(model):
    up = st.file_uploader("A photo of one hand sign", type=["jpg", "jpeg", "png"], key="sign_upload")
    if not up:
        st.info("Crop the photo close to the hand for the best result.")
        return
    img = np.array(Image.open(up).convert("RGB"))[:, :, ::-1]
    letter, conf, top3 = predict(model, img)
    sign_db.log_prediction("upload", letter, conf)
    c1, c2 = st.columns([3, 2])
    c1.image(img[:, :, ::-1], width="stretch")
    with c2:
        letter_card(letter, conf)
        st.caption("Runner-up guesses: " + ", ".join(f"{l} {p:.0%}" for l, p in top3[1:]))


def main():
    st.set_page_config(page_title="SignSpeak", layout="wide")
    st.title("SignSpeak: Real-Time Sign Recognition")
    if not os.path.exists(MODEL_PATH):
        st.error("Model not found. Run `python train.py` inside signspeak/ first.")
        return
    model, metrics = get_model(), get_metrics()
    st.caption(
        f"Reads American Sign Language letters A to Y from a webcam. HOG features, PCA and an "
        f"SVM trained on {metrics['train_images']:,} images (Sign Language MNIST), "
        f"**{metrics['test_accuracy']:.1%} accuracy** on {metrics['test_images']:,} separate test images."
    )

    main_col, side_col = st.columns([3, 1])
    with main_col:
        t_demo, t_live, t_up = st.tabs(["Demo mode", "Live camera", "Upload a photo"])
        with t_demo:
            demo_mode(model)
        with t_live:
            live_camera(model)
        with t_up:
            upload_photo(model)

    with side_col:
        st.subheader("Recent activity")
        st.caption("Every prediction is saved to a SQLite database.")
        log = sign_db.recent(8)
        if log.empty:
            st.write("Nothing yet. Press Play in demo mode.")
        else:
            st.dataframe(log, hide_index=True, width="stretch")
        with st.expander("Accuracy per letter"):
            st.bar_chart(metrics["per_letter_accuracy"])

    with st.expander("How it works"):
        st.markdown(
            """
1. **Frame**: the webcam frame is mirrored and the guide box is cropped out.
2. **Normalise**: converted to grayscale and shrunk to 28x28 pixels, the format of the training data.
3. **Features**: Histogram of Oriented Gradients (HOG) turns finger edges and hand shape into 1,296 numbers.
4. **Classify**: a scaler, PCA (down to 160 components) and an RBF-kernel SVM pick the most likely of 24 letters, with a probability for each.
5. **Spell**: on the live camera, a letter is added to the text once it stays the top guess for about a second.

J and Z are left out because they are signed with movement.
"""
        )


if __name__ == "__main__":
    main()
