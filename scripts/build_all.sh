#!/usr/bin/env bash
# Runs every project's data-prep / training step, in order. Run
# scripts/fetch_raw_data.sh first if data/raw_events, data/sign_language_digits
# or data/hpo/*.obo,*.hpoa,*.txt are missing.
#
# Usage:
#   bash scripts/build_all.sh

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Football Analytics: building match/shot/pass CSVs =="
(cd "$ROOT_DIR/football_dashboard" && python3 prepare_data.py)

echo ""
echo "== SignSpeak: extracting HOG features + training SVM =="
(cd "$ROOT_DIR/signspeak" && python3 preprocess.py && python3 train.py)

echo ""
echo "== WanderWise: building destinations + synthetic ratings =="
(cd "$ROOT_DIR/wanderwise/data" && python3 build_destinations.py && python3 build_ratings.py)

echo ""
echo "== Attendance System: training LBPH face recognizer =="
(cd "$ROOT_DIR/attendance_system" && python3 train_model.py)

echo ""
echo "== Genetic Testing DSST: building HPO knowledge base =="
(cd "$ROOT_DIR/genomics_dsst" && python3 prepare_data.py)

echo ""
echo "All projects built. Run the hub with:"
echo "  cd dashboard && streamlit run Home.py"
