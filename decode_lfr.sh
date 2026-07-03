#!/usr/bin/env bash
#
# Decode every .LFR file in LFRDataset/ with PlenoptiCam and collect the
# results into LFRDatasetExtracted/.
#
#   LFRDataset/Coral_1.LFR  ->  LFRDatasetExtracted/Coral_1/
#   LFRDataset/Coral_2.LFR  ->  LFRDatasetExtracted/Coral_2/
#   LFRDataset/Calibration/caldata-*.tar (extracted json)
#                           ->  LFRDatasetExtracted/Calibration/
#
# Usage:   ./decode_lfr.sh
#          FORCE=1 ./decode_lfr.sh      # re-decode files already extracted
#
set -euo pipefail

# --- Run from the repo root (this script's location) ---------------------
cd "$(dirname "${BASH_SOURCE[0]}")"

# --- Configuration -------------------------------------------------------
INPUT_DIR="LFRDataset"
CALIB_DIR="${INPUT_DIR}/Calibration"
OUTPUT_DIR="LFRDatasetExtracted"

# Prefer the project venv's plenopticam, fall back to one on PATH.
if [[ -x ".venv/bin/plenopticam" ]]; then
    PLENOPTICAM=".venv/bin/plenopticam"
else
    PLENOPTICAM="plenopticam"
fi

# --- Locate the calibration .tar -----------------------------------------
CALIB_TAR="$(find "$CALIB_DIR" -maxdepth 1 -type f -name '*.tar' | head -n1)"
if [[ -z "$CALIB_TAR" ]]; then
    echo "ERROR: no calibration .tar found in $CALIB_DIR" >&2
    exit 1
fi
echo "Calibration: $CALIB_TAR"

mkdir -p "$OUTPUT_DIR"

# --- Decode each .LFR file -----------------------------------------------
shopt -s nullglob
lfr_files=("$INPUT_DIR"/*.LFR)
if [[ ${#lfr_files[@]} -eq 0 ]]; then
    echo "ERROR: no .LFR files found in $INPUT_DIR" >&2
    exit 1
fi

for lfr in "${lfr_files[@]}"; do
    name="$(basename "$lfr" .LFR)"     # e.g. Coral_1
    src_out="${INPUT_DIR}/${name}"     # where plenopticam writes its output
    dst_out="${OUTPUT_DIR}/${name}"    # where we want it

    if [[ -d "$dst_out" && "${FORCE:-0}" != "1" ]]; then
        echo "=== Skipping ${name} (already in ${dst_out}; set FORCE=1 to redo) ==="
        continue
    fi

    echo "=== Decoding ${name} ==="
    "$PLENOPTICAM" -f "$lfr" -c "$CALIB_TAR"

    if [[ -d "$src_out" ]]; then
        rm -rf "$dst_out"
        mv "$src_out" "$dst_out"
        echo "Saved -> ${dst_out}"
    else
        echo "WARNING: expected output folder ${src_out} not found" >&2
    fi
done

# --- Collect the extracted calibration json ------------------------------
# PlenoptiCam extracts calibration into LFRDataset/Calibration/<serial>/mod_*.json
# and caches it there for reuse, so we copy (not move) the first one found.
mkdir -p "${OUTPUT_DIR}/Calibration"
calib_json="$(find "$CALIB_DIR" -type f -name 'mod_*.json' | head -n1)"
if [[ -n "$calib_json" ]]; then
    cp "$calib_json" "${OUTPUT_DIR}/Calibration/"
    echo "Saved calibration -> ${OUTPUT_DIR}/Calibration/$(basename "$calib_json")"
else
    echo "WARNING: no calibration mod_*.json found under ${CALIB_DIR}" >&2
fi

echo "Done."
