import argparse
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path


class PlenopticamLFR:
    """Decode every .LFR file in `input_dir` with PlenoptiCam and collect
    the results into `output_dir`.

        LFRDataset/Coral_1.LFR  ->  LFRDatasetExtracted/Coral_1/
        LFRDataset/Coral_2.LFR  ->  LFRDatasetExtracted/Coral_2/
        LFRDataset/Calibration/caldata-*.tar (extracted json)
                                ->  LFRDatasetExtracted/Calibration/
    """

    def __init__(self, input_dir="LFRDataset", output_dir=None, force=False):
        self.input_dir = input_dir
        self.calib_dir = os.path.join(input_dir, "Calibration")
        self.output_dir = output_dir or f"{input_dir}Extracted"
        self.force = force
        self.plenopticam = self._find_plenopticam()

    def _find_plenopticam(self):
        venv_bin = os.path.join(".venv", "bin", "plenopticam")
        if os.path.isfile(venv_bin) and os.access(venv_bin, os.X_OK):
            return venv_bin
        return "plenopticam"

    def _find_calibration_tar(self):
        tars = sorted(glob.glob(os.path.join(self.calib_dir, "*.tar")))
        if not tars:
            raise FileNotFoundError(f"no calibration .tar found in {self.calib_dir}")
        return tars[0]

    def _lfr_files(self):
        return sorted(glob.glob(os.path.join(self.input_dir, "*.LFR")))

    def _subdirs(self):
        return {d for d in glob.glob(os.path.join(self.input_dir, "*")) if os.path.isdir(d)}

    def _decode_one(self, lfr_path, calib_tar):
        name = Path(lfr_path).stem
        dst_out = os.path.join(self.output_dir, name)

        if os.path.isdir(dst_out) and not self.force:
            print(f"=== Skipping {name} (already in {dst_out}; set force=True to redo) ===")
            return

        before_dirs = self._subdirs()

        print(f"=== Decoding {name} ===")
        subprocess.run([self.plenopticam, "-f", lfr_path, "-c", calib_tar], check=True)

        new_dirs = self._subdirs() - before_dirs
        if len(new_dirs) == 1:
            src_out = new_dirs.pop()
            if os.path.isdir(dst_out):
                shutil.rmtree(dst_out)
            shutil.move(src_out, dst_out)
            print(f"Saved -> {dst_out}")
        elif not new_dirs:
            print(f"WARNING: no new output folder appeared in {self.input_dir} for {name}", file=sys.stderr)
        else:
            print(f"WARNING: multiple new folders appeared for {name}, not moving: {sorted(new_dirs)}", file=sys.stderr)

    def _collect_calibration_json(self):
        calib_out_dir = os.path.join(self.output_dir, "Calibration")
        os.makedirs(calib_out_dir, exist_ok=True)

        matches = sorted(glob.glob(os.path.join(self.calib_dir, "**", "mod_*.json"), recursive=True))
        if matches:
            shutil.copy2(matches[0], calib_out_dir)
            print(f"Saved calibration -> {os.path.join(calib_out_dir, os.path.basename(matches[0]))}")
        else:
            print(f"WARNING: no calibration mod_*.json found under {self.calib_dir}", file=sys.stderr)

    def run(self):
        calib_tar = self._find_calibration_tar()
        print(f"Calibration: {calib_tar}")

        os.makedirs(self.output_dir, exist_ok=True)

        lfr_files = self._lfr_files()
        if not lfr_files:
            raise FileNotFoundError(f"no .LFR files found in {self.input_dir}")

        for lfr in lfr_files:
            self._decode_one(lfr, calib_tar)

        self._collect_calibration_json()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="LFRDataset")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--force", default=False, action="store_true", help="re-decode files already extracted")
    args = parser.parse_args()

    pc = PlenopticamLFR(input_dir=args.input_dir, output_dir=args.output_dir, force=args.force)
    pc.run()


if __name__ == "__main__":
    main()
