#!/usr/bin/env bash
# Downloads the large raw source datasets that .gitignore keeps out of the
# repo. Run this once after cloning, before running any project's own
# prepare_data.py / preprocess.py / train_model.py.
#
# Usage:
#   bash scripts/fetch_raw_data.sh
#
# Needs: curl, git, and network access to github.com / raw.githubusercontent.com

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/data"
mkdir -p "$DATA_DIR"

echo "== Football Analytics: StatsBomb open data (France's 2018 World Cup matches) =="
mkdir -p "$DATA_DIR/raw_events"
if [ ! -f "$DATA_DIR/wc2018_matches.json" ]; then
    curl -sL "https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/43/3.json" \
        -o "$DATA_DIR/wc2018_matches.json"
fi
for id in 7546 7580 7530 8649 8658 8655 7563; do
    out="$DATA_DIR/raw_events/${id}.json"
    if [ ! -f "$out" ]; then
        echo "  fetching match $id"
        curl -sL "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/${id}.json" -o "$out"
    fi
done

echo "== SignSpeak: Sign Language Digits Dataset (Apache 2.0) =="
if [ ! -d "$DATA_DIR/sign_language_digits" ]; then
    tmp_dir=$(mktemp -d)
    git clone --depth 1 https://github.com/ardamavi/Sign-Language-Digits-Dataset.git "$tmp_dir/sld"
    mkdir -p "$DATA_DIR/sign_language_digits"
    cp -r "$tmp_dir/sld/Dataset/"* "$DATA_DIR/sign_language_digits/"
    rm -rf "$tmp_dir"
fi

echo "== Attendance System: AT&T/ORL Database of Faces =="
if [ ! -d "$DATA_DIR/att_faces" ] || [ -z "$(ls -A "$DATA_DIR/att_faces" 2>/dev/null)" ]; then
    tmp_dir=$(mktemp -d)
    git clone --depth 1 https://github.com/wihoho/FaceRecognition.git "$tmp_dir/fr"
    mkdir -p "$DATA_DIR/att_faces"
    cp -r "$tmp_dir/fr/src/test/resources/faces/"* "$DATA_DIR/att_faces/"
    rm -rf "$tmp_dir"
fi

echo "== Genetic Testing DSST: Human Phenotype Ontology data =="
mkdir -p "$DATA_DIR/hpo"
if [ ! -f "$DATA_DIR/hpo/hp.obo" ]; then
    curl -sL "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo" \
        -o "$DATA_DIR/hpo/hp.obo"
fi
if [ ! -f "$DATA_DIR/hpo/phenotype.hpoa" ]; then
    curl -sL "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/phenotype.hpoa" \
        -o "$DATA_DIR/hpo/phenotype.hpoa"
fi
if [ ! -f "$DATA_DIR/hpo/genes_to_phenotype.txt" ]; then
    curl -sL "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/genes_to_phenotype.txt" \
        -o "$DATA_DIR/hpo/genes_to_phenotype.txt"
fi

echo ""
echo "Done. Raw data is in $DATA_DIR"
echo "Next: run scripts/build_all.sh to process it and train the models."
