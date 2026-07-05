"""
Build PlenoptiSign input parameters directly from Lytro Illum .LFR / PlenoptiCam
JSON metadata, then run PlenoptiSign non-interactively (no CLI prompts).

Sources:
  - capture_json:     the decoded .LFR metadata (e.g. Bee_1.json)
  - calibration_json: PlenoptiCam's calibrated MLA geometry (e.g. mod_0008.json)

Two parameters PlenoptiSign needs are not camera constants but per-frame
measurements from the actual light-field decode/disparity step:
  - virtual_cam_gap (G): which pair of virtual sub-aperture views was compared
  - disparity_val (dx):  measured pixel disparity between those views
If either is left as None, PlenoptiSign's own library defaults are used
(G=-6, dx=4.0 -- the same defaults the interactive CLI shows).

Two lens-design constants have no source in either JSON at all:
  - fs (micro lens focal length)
  - HH (main lens principal plane spacing)
These fall back to PlenoptiSign's built-in defaults and are flagged in the
report -- they are the two parameters worth calibrating empirically if you
need better accuracy than the analytic in-air model gives.
"""

import argparse
import json
import re
import numpy as np
from pathlib import Path

from plenoptisign.mainclass import MainClass
from plenoptisign.constants import ABBS, VALS

DEFAULTS = dict(zip(ABBS, VALS))


class LFRGeometry:
    def __init__(self, capture_json, calibration_json,
                 virtual_cam_gap=None, disparity_val=None):
        self.virtual_cam_gap = virtual_cam_gap
        self.disparity_val = disparity_val
        self.params = {}
        self.sources = {}
        self._load_capture(Path(capture_json))
        self._load_calibration(Path(calibration_json))
        self._build_params()

    def _load_capture(self, path):
        print("WHAT IS THE BEE FILE", path)
        with open(path) as f:
            self.capture = json.load(f)

    def _load_calibration(self, path):
        with open(path) as f:
            self.calibration = json.load(f)

    def _set(self, key, value, source):
        self.params[key] = value
        self.sources[key] = source

    def _build_params(self):
        cap = self.capture
        frame_meta = cap["master"]["picture"]["frameArray"][0]["frame"]["metadata"]
        devices = frame_meta["devices"]

        pixel_pitch_mm = devices["sensor"]["pixelPitch"] * 1e3
        lens_pitch_mm = devices["mla"]["lensPitch"] * 1e3
        mla_sensor_gap_mm = devices["mla"]["sensorOffset"]["z"] * 1e3
        exit_pupil_mm = devices["lens"]["exitPupilOffset"]["z"] * 1e3
        f_u_mm = devices["lens"]["focalLength"] * 1e3
        f_number = devices["lens"]["fNumber"]

        height_px = cap["image"]["height"]
        width_px = cap["image"]["width"]
        sensor_dims_mm = (height_px * pixel_pitch_mm, width_px * pixel_pitch_mm)

        self._set("pp", pixel_pitch_mm,
                   "capture.master.picture.frameArray[0].frame.metadata.devices.sensor.pixelPitch")
        self._set("pm", lens_pitch_mm,
                   "capture.master.picture.frameArray[0].frame.metadata.devices.mla.lensPitch")
        self._set("hh", mla_sensor_gap_mm,
                   "capture...devices.mla.sensorOffset.z (MLA-to-sensor gap)")
        self._set("dA", exit_pupil_mm,
                   "capture...devices.lens.exitPupilOffset.z")
        self._set("fU", f_u_mm,
                   "capture...devices.lens.focalLength")
        self._set("f_num", f_number,
                   "capture...devices.lens.fNumber")
        self._set("sd", sensor_dims_mm,
                   "computed: image.height/width (capture json) x pixelPitch")

        # object distance: parsed from the matched calibration frame's filename,
        # e.g. "FL6564ObjDist843ZS-883FS-337.png" -> 843 mm. This is the BENCH
        # distance the calibration white image was captured at, used here only
        # as a rough stand-in -- it is NOT the true object distance of this shot.
        image_file = cap.get("imageFile", "")
        match = re.search(r"ObjDist(\d+)", image_file)
        if match:
            self._set("df", float(match.group(1)),
                       f"parsed from capture.imageFile ('{image_file}') -- "
                       f"calibration bench distance, NOT the true shot distance")
        else:
            self.sources["df"] = "not found in capture.imageFile -- using library default"

        # micro image resolution: prefer the *measured* calibration grid pitch
        # over the nominal lensPitch/pixelPitch ratio.
        ptc_mean = self.calibration.get("ptc_mean")
        if ptc_mean:
            m_val = sum(ptc_mean) / len(ptc_mean)
            self._set("M", m_val,
                       "computed: mean(calibration.ptc_mean) -- measured MLA grid pitch in px")
        else:
            m_nominal = lens_pitch_mm / pixel_pitch_mm
            self._set("M", m_nominal,
                       "computed: capture lensPitch / pixelPitch (nominal, no calibration ptc_mean found)")

        # not available anywhere in either JSON -- lens-design constants
        self.sources["fs"] = f"not in JSON -- using PlenoptiSign default ({DEFAULTS['fs']} mm)"
        self.sources["HH"] = f"not in JSON -- using PlenoptiSign default ({DEFAULTS['HH']} mm)"

        # per-frame values supplied by caller (from PlenoptiCam's actual disparity output)
        if self.virtual_cam_gap is not None:
            self._set("G", self.virtual_cam_gap, "provided by caller (per-frame PlenoptiCam output)")
        else:
            self.sources["G"] = f"None -> using PlenoptiSign default ({DEFAULTS['G']} px)"

        if self.disparity_val is not None:
            self._set("dx", self.disparity_val, "provided by caller (per-frame PlenoptiCam output)")
        else:
            self.sources["dx"] = f"None -> using PlenoptiSign default ({DEFAULTS['dx']} px)"

        self._set("a", DEFAULTS["a"], "PlenoptiSign default (algorithmic shift parameter)")

    def report(self):
        label_map = dict(zip(ABBS, [
            "Sensor Dimensions (Y,X) [mm]", "Pixel Pitch [mm]", "Micro Lens Focal Length [mm]",
            "Micro Lens Principal Plane Spacing [mm]", "Micro Lens Pitch [mm]", "Exit Pupil Distance [mm]",
            "Main Lens Focal Length [mm]", "Main Lens Principal Plane Spacing [mm]",
            "Main Lens Focusing Distance [mm]", "F-number", "Shift Parameter",
            "Micro Image Resolution [px]", "Virtual Camera Gap [px]", "Disparity [px]",
        ]))
        print(f"{'Parameter':38} {'Value':>22}   Source")
        print("-" * 100)
        for key in ABBS:
            value = self.params.get(key, DEFAULTS[key])
            source = self.sources.get(key, "PlenoptiSign default")
            val_str = str(value) if not isinstance(value, float) else f"{value:.4f}"
            print(f"{label_map[key]:38} {val_str:>22}   {source}")

    def run(self):
        obj = MainClass(self.params)
        ret_refo = obj.refo()
        ret_tria = obj.tria()
        results = {
            "refocusing_distance_mm": obj.d,
            "dof_far_border_mm": obj.d_p,
            "dof_near_border_mm": obj.d_m,
            "depth_of_field_mm": obj.dof,
            "baseline_mm": obj.B,
            "tilt_angle_deg": obj.phi,
            "triangulation_distance_mm": obj.Z,
        }
        return results

    def triangulation_distance_for_disparity(self, disparity_val, virtual_cam_gap=None):
        """ Recompute Z for a single disparity value, reusing all other sourced params. """
        params = dict(self.params)
        params["dx"] = float(disparity_val)
        params["G"] = float(virtual_cam_gap) if virtual_cam_gap is not None else params.get("G", DEFAULTS["G"])
        obj = MainClass(params)
        obj.tria()
        return obj.Z

    def depth_map_from_disparity(self, disparity_map, virtual_cam_gap=None):
        """ Convert a full PlenoptiCam disparity map (numpy array, px) to metric
        depth (mm) using this geometry's sourced parameters.

        Disparity is quantized in practice, so unique values are triangulated
        once and broadcast back over the map rather than looping per pixel.

        :param disparity_map: 2D numpy array of per-pixel disparity, in px
        :param virtual_cam_gap: optional override for G; defaults to whatever
            this instance was constructed with (or the PlenoptiSign default)
        :return: 2D numpy array of metric depth, in mm, same shape as input
        """

        disparity_map = np.asarray(disparity_map, dtype=float)
        depth_map = np.zeros_like(disparity_map)

        unique_vals = np.unique(disparity_map)
        z_lookup = {
            d: self.triangulation_distance_for_disparity(d, virtual_cam_gap)
            for d in unique_vals
        }
        for d, z in z_lookup.items():
            depth_map[disparity_map == d] = z

        return depth_map
    

    def read_pfm(self, file_path):
        # Reads PFM file, handles header parsing, endianness, and flips image
        with open(file_path, 'rb') as f:
            header = f.readline().decode('latin-1').rstrip()
            dim_match = re.match(r'^(\d+)\s+(\d+)\s$', f.readline().decode('latin-1'))
            width, height = map(int, dim_match.groups())
            scale = float(f.readline().decode('latin-1').rstrip())
            endian = '<' if scale < 0 else '>'
            data = np.fromfile(f, endian + 'f').reshape((height, width))
            return np.flipud(data) # Disparity map as 2D numpy array
    

    def show_depth(self):
        """ Convert a PlenoptiCam disparity .pfm to metric depth (mm) using
        this geometry's sourced parameters, and display it with a colorbar
        in real units (plain normalized grayscale would hide the metric
        conversion that's the whole point of this pipeline).

        :param pfm_path: path to PlenoptiCam's depth.pfm (disparity map, px)
        :param save_path: optional path to also save the figure as png
        """
        import matplotlib.pyplot as plt

        disparity_map = self.read_pfm("LFRDatasetExtracted/Bee_1/depth.pfm")
        depth_map = self.depth_map_from_disparity(disparity_map)

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(depth_map, cmap="viridis")
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("Metric depth (mm)")
        ax.set_title("Metric Depth Map")
        ax.axis("off")

        plt.show()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_json", help="decoded .LFR metadata json (e.g. Bee_1.json)")
    parser.add_argument("calibration_json", help="PlenoptiCam calibrated MLA json (e.g. mod_0008.json)")
    parser.add_argument("--gap", type=float, default=None,
                         help="virtual camera gap G, in px (from PlenoptiCam per-frame output)")
    parser.add_argument("--disparity", type=float, default=None,
                         help="measured disparity dx, in px (from PlenoptiCam per-frame output)")
    args = parser.parse_args()

    geo = LFRGeometry(args.capture_json, args.calibration_json,
                       virtual_cam_gap=args.gap, disparity_val=args.disparity)
    geo.report()

    results = geo.run()
    print()
    print(f"refoc. distance d: {results['refocusing_distance_mm']:.4f} mm")
    print(f"depth of field DoF: {results['depth_of_field_mm']:.4f} mm")
    print(f"narrow DoF border: {results['dof_near_border_mm']:.4f} mm")
    print(f"far DoF border: {results['dof_far_border_mm']:.4f} mm")
    print()
    print(f"baseline B: {results['baseline_mm']:.4f} mm")
    print(f"tilt angle Phi: {results['tilt_angle_deg']:.4f} deg")
    print(f"tria. distance Z: {results['triangulation_distance_mm']:.4f} mm")

    geo.show_depth()



if __name__ == "__main__":
    main()
