import argparse
import json
import re
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from plenoptisign.mainclass import MainClass
from plenoptisign.constants import ABBS, VALS

DEFAULTS = dict(zip(ABBS, VALS))

SHOW_VALS = False
SHOW_DEPTHS = True


class PlenoptisignLFR:

    def __init__(self, capture_json, calibration_json):
       self.params = {}
       self.sources = {}
       self.results = {}

       self.capture_json = str(capture_json)
       self.calibrate_json = str(calibration_json)

       self.build_params()

    def _set(self, key, value, source):
        self.params[key] = value
        self.sources[key] = source

    def read_pfm(self, file_path):
        """
        Reads PFM file, handles header parsing, endianness, and flips image.
        
        Return:
            disparity_map: 2d numpy array
        """

        with open(file_path, 'rb') as f:
            header = f.readline().decode('latin-1').rstrip()
            dim_match = re.match(r'^(\d+)\s+(\d+)\s$', f.readline().decode('latin-1'))
            width, height = map(int, dim_match.groups())
            scale = float(f.readline().decode('latin-1').rstrip())
            endian = '<' if scale < 0 else '>'
            data = np.fromfile(f, endian + 'f').reshape((height, width))
        return np.flipud(data)


    def build_params(self):
        """Get the params that are fixed for the whole camera (sensor/MLA
        hardware constants). Runs once -- subsequent calls are no-ops, since
        these values don't change frame to frame even when zoom/focus do."""

        with open(self.capture_json) as f:
            cap_json = json.load(f)

        frame_meta = cap_json["master"]["picture"]["frameArray"][0]["frame"]["metadata"]

        devices = frame_meta["devices"]
        pixel_pitch_mm = devices["sensor"]["pixelPitch"] * 1e3
        lens_pitch_mm = devices["mla"]["lensPitch"] * 1e3
        mla_sensor_gap_mm = devices["mla"]["sensorOffset"]["z"] * 1e3

        height_px = cap_json["image"]["height"]
        width_px = cap_json["image"]["width"]
        sensor_dims_mm = (height_px * pixel_pitch_mm, width_px * pixel_pitch_mm)

        self._set("pp", pixel_pitch_mm,
                   "capture.master.picture.frameArray[0].frame.metadata.devices.sensor.pixelPitch")
        self._set("pm", lens_pitch_mm,
                   "capture.master.picture.frameArray[0].frame.metadata.devices.mla.lensPitch")
        self._set("hh", mla_sensor_gap_mm,
                   "capture...devices.mla.sensorOffset.z (MLA-to-sensor gap)")
        self._set("sd", sensor_dims_mm,
                   "computed: image.height/width (capture json) x pixelPitch")

        # not available anywhere in either JSON -- lens-design constants
        self.sources["fs"] = f"not in JSON -- using PlenoptiSign default ({DEFAULTS['fs']} mm)"
        self.sources["HH"] = f"not in JSON -- using PlenoptiSign default ({DEFAULTS['HH']} mm)"

        self._built = True


    def add_params(self, virtual_cam_gap=None, disparity_val=None):
        """Add the params that vary per frame. Use defualt value if none."""

        with open(self.capture_json) as f:
            cap_json = json.load(f)
        with open(self.calibrate_json) as f:
            cal_json = json.load(f)

        devices = cap_json["master"]["picture"]["frameArray"][0]["frame"]["metadata"]["devices"]
        pixel_pitch_mm = devices["sensor"]["pixelPitch"] * 1e3
        lens_pitch_mm = devices["mla"]["lensPitch"] * 1e3
        exit_pupil_mm = devices["lens"]["exitPupilOffset"]["z"] * 1e3
        f_u_mm = devices["lens"]["focalLength"] * 1e3
        f_number = devices["lens"]["fNumber"]

        self._set("dA", exit_pupil_mm,
                   "capture...devices.lens.exitPupilOffset.z")
        self._set("fU", f_u_mm,
                   "capture...devices.lens.focalLength")
        self._set("f_num", f_number,
                   "capture...devices.lens.fNumber")

        # object distance: parsed from the matched calibration frame's filename,
        # e.g. "FL6564ObjDist843ZS-883FS-337.png" -> 843 mm. This is the BENCH
        # distance the calibration white image was captured at, used here only
        # as a rough stand-in -- it is NOT the true object distance of this shot.
        image_file = cap_json.get("imageFile", "")
        match = re.search(r"ObjDist(\d+)", image_file)
        if match:
            self._set("df", float(match.group(1)),
                       f"parsed from capture.imageFile ('{image_file}') -- "
                       f"calibration bench distance, NOT the true shot distance")
        else:
            self.sources["df"] = "not found in capture.imageFile -- using library default"

        # micro image resolution: prefer the *measured* calibration grid pitch
        # over the nominal lensPitch/pixelPitch ratio.
        ptc_mean = cal_json.get("ptc_mean")
        if ptc_mean:
            m_val = sum(ptc_mean) / len(ptc_mean)
            self._set("M", m_val,
                       "computed: mean(calibration.ptc_mean) -- measured MLA grid pitch in px")
        else:
            m_nominal = lens_pitch_mm / pixel_pitch_mm
            self._set("M", m_nominal,
                       "computed: capture lensPitch / pixelPitch (nominal, no calibration ptc_mean found)")

        # per-frame values supplied by caller (from PlenoptiCam's actual disparity output)
        if virtual_cam_gap is not None:
            self._set("G", virtual_cam_gap, "provided by caller (per-frame PlenoptiCam output)")
        else:
            self.sources["G"] = f"None -> using PlenoptiSign default ({DEFAULTS['G']} px)"

        if disparity_val is not None:
            self._set("dx", disparity_val, "provided by caller (per-frame PlenoptiCam output)")
        else:
            self.sources["dx"] = f"None -> using PlenoptiSign default ({DEFAULTS['dx']} px)"

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

    def run_plenopticam(self):
        """Run the Pletopisign package."""

        obj = MainClass(self.params)
        ret_refo = obj.refo()
        ret_tria = obj.tria()
        self.results = {
            "refocusing_distance_mm": obj.d,
            "dof_far_border_mm": obj.d_p,
            "dof_near_border_mm": obj.d_m,
            "depth_of_field_mm": obj.dof,
            "baseline_mm": obj.B,
            "tilt_angle_deg": obj.phi,
            "triangulation_distance_mm": obj.Z,
        }
    
    def triangulation_distance_for_disparity(self, disparity_val, virtual_cam_gap=None):
        """ Recompute Z for a single disparity value, reusing all other sourced params. """
        params = dict(self.params)
        params["dx"] = float(disparity_val)
        params["G"] = float(virtual_cam_gap) if virtual_cam_gap is not None else params.get("G", DEFAULTS["G"])
        obj = MainClass(params)
        obj.tria()
        return obj.Z
    
    def depth_map_from_disparity(self, virtual_cam_gap=None, disparity_val=None):
        """ Convert a full PlenoptiCam disparity map (numpy array, px) to metric
        depth (mm) using this geometry's sourced parameters.
        """
        print("Calculating depth...")

        disparity_map = self.read_pfm(self.disparity_file)

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

    def update(self, capture_json, calibration_json, disparity_file=None, virtual_cam_gap=None, disparity_val=None):
        """Main loop, run per frame."""

        # Update the metadata files
        self.capture_json = capture_json
        self.calibrate_json = calibration_json

        # self.disparity_file = disparity_file
        self.disparity_file = 'LFRDatasetExtracted/Bee_1/depth.pfm'

        # Edit the per frame metadata
        self.add_params(virtual_cam_gap, disparity_val)
        
        # Calculate with plenoptisign
        self.run_plenopticam()

        if SHOW_VALS: self.report()
        print(self.results)

        depth_map = self.depth_map_from_disparity()

        if SHOW_DEPTHS:
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(depth_map, cmap="viridis")
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label("Metric depth (mm)")
            ax.set_title("Metric Depth Map")
            ax.axis("off")

            plt.show()



def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_json", help="decoded .LFR metadata json file")
    parser.add_argument("calibration_json", help="PlenoptiCam calibrated MLA json file")
    parser.add_argument("--gap", type=float, default=None,
                         help="virtual camera gap G, in px (from PlenoptiCam per-frame output)")
    parser.add_argument("--disparity", type=float, default=None,
                         help=".pfm, measured disparity dx, in px (from PlenoptiCam per-frame output)")
    args = parser.parse_args()
    
    try:
        ps = PlenoptisignLFR(args.capture_json, args.calibration_json)
        ps.update(args.capture_json, args.calibration_json, virtual_cam_gap=args.gap, disparity_val=args.disparity)
    except KeyboardInterrupt:
        print("Ctrl C recieved. Stopping processes")


if __name__=="__main__":
    main()