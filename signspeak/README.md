# SignSpeak: Real-Time Sign Recognition

Reads American Sign Language letters from a webcam and spells them out.

- **Live camera**: your browser webcam through streamlit-webrtc. Hold a sign in the green box; the letter is drawn on the video, and holding it for about a second adds it to the text.
- **Demo mode**: type a word and watch it spelled from test images the model never trained on. Works without a camera.
- **Upload a photo**: one still image.
- Every prediction is logged to SQLite (`sign_db.py`) and shown as recent activity.

## Model

| Step | Detail |
|---|---|
| Data | Sign Language MNIST: 27,455 training and 7,172 test images, 28x28 grayscale, 24 letters (CC0) |
| Features | Histogram of Oriented Gradients, 1,296 numbers per image |
| Classifier | StandardScaler, PCA to 160 components, RBF-kernel SVM with probabilities |
| Accuracy | **95.2%** on the separate test file (per-letter scores in `metrics.json`) |
| Speed | about 3 ms per frame on a laptop CPU |

J and Z are signed with movement, so a single frame can't capture them; they are left out.

**Honest limit:** the training images are tightly cropped hands on plain backgrounds. On a real webcam it works best with good light and a plain wall behind your hand.

## Files

- `sign_engine.py`: the shared pipeline (crop, grayscale, 28x28, HOG, predict)
- `train.py`: trains the model and writes `model.joblib`, `metrics.json` and `sample_frames/`
- `sign_db.py`: SQLite prediction log
- `app.py`: the Streamlit page

Retrain with `bash ../scripts/fetch_raw_data.sh && python train.py`.
