"""
Decode all light-field images (.LFR) with PlenoptiCam.

    data/LFRDataset/IMG_0274.LFR  ->  data/LFRDatasetExtracted/IMG_0274/

Run from the repo root:  python -m utils.decode_lfr
"""

import argparse as arg
import glob
import os
import shutil
import subprocess
import sys

from lib import paths


PATCH_SIZE = 7  # views per axis (7 -> 7x7 sub-aperture grid)

PLENOPTICAM = os.path.join(os.path.dirname(sys.executable), "plenopticam")

# Files PlenoptiCam writes that nothing here reads. Removed unless --all.
UNUSED = [
    "lfp_img_align.pkl",    # ~300 MB, only a cache to skip re-alignment
    "*.tiff",               # ~80 MB, raw Bayer image; the .LFR is the source
    "depth.png",            # 8-bit render of depth.pfm
    "depth.ply",            # arbitrary units, not metric
    "*_animation_*px.gif",  # view + refocus gifs
    "refo_*px",             # refocus stack
]


def decode_one(lfr, calib_tar, keep_all, force):
    """Decode one .LFR with PlenoptiCam, move the result into the extracted folder, and drop unused files unless keep_all."""
    name = os.path.splitext(os.path.basename(lfr))[0]
    dst = os.path.join(paths.DATA_EXTRACTED_DIR, name)

    if os.path.isdir(dst) and not force:
        print(f"=== Skipping {name} (already in {dst}; use --force to redo) ===")
        return

    print(f"=== Decoding {name} ===")
    # PlenoptiCam v0.9.3 exits with status 1 even on success, so no check=True.
    # Success is judged by whether its output folder appears.
    subprocess.run([PLENOPTICAM, "-f", lfr, "-c", calib_tar, "-p", str(PATCH_SIZE)])

    # PlenoptiCam writes its output next to the .LFR
    out = os.path.splitext(lfr)[0]
    if not os.path.isdir(out):
        print(f"WARNING: expected output folder {out} was not produced for {name}", file=sys.stderr)
        return

    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.move(out, dst)
    os.makedirs(os.path.join(dst, "docs"), exist_ok=True)

    if not keep_all:
        for pattern in UNUSED:
            for path in glob.glob(os.path.join(dst, pattern)):
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    print(f"Saved -> {dst}")


def collect_calibration():
    """Copy the calibration json files PlenoptiCam extracted from the tar, one per zoom/focus setting."""
    dst = os.path.join(paths.DATA_EXTRACTED_DIR, "Calibration")
    os.makedirs(dst, exist_ok=True)

    matches = glob.glob(os.path.join(paths.DATA_RAW_DIR, "Calibration", "**", "mod_*.json"), recursive=True)
    if not matches:
        print("WARNING: no calibration mod_*.json found", file=sys.stderr)
    for match in matches:
        shutil.copy2(match, dst)


def decode(keep_all=False, force=False):
    """Decode every .LFR in the raw data folder, then collect the calibration files."""
    tars = sorted(glob.glob(os.path.join(paths.DATA_RAW_DIR, "Calibration", "*.tar")))
    lfrs = sorted(glob.glob(os.path.join(paths.DATA_RAW_DIR, "*.LFR")))
    if not tars:
        raise FileNotFoundError(f"no calibration .tar found in {paths.DATA_RAW_DIR}/Calibration")
    if not lfrs:
        raise FileNotFoundError(f"no .LFR files found in {paths.DATA_RAW_DIR}")

    os.makedirs(paths.DATA_EXTRACTED_DIR, exist_ok=True)

    for lfr in lfrs:
        decode_one(lfr, tars[0], keep_all, force)

    collect_calibration()


def main():
    """Parse the command-line flags and run decode()."""
    parser = arg.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="keep everything PlenoptiCam writes, not just what is used")
    parser.add_argument("--force", action="store_true", help="re-decode files already extracted")
    args = parser.parse_args()

    decode(keep_all=args.all, force=args.force)


if __name__ == "__main__":
    main()
