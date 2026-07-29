import argparse
import json
import re
import os
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from plenoptisign.mainclass import MainClass
from plenoptisign.constants import ABBS, VALS

DEFAULTS = dict(zip(ABBS, VALS))

SHOW_VALS = False
SHOW_DEPTHS = True

EXTRACTED_DIR = "LFRDatasetExtracted/"


class PlenoptisignLFR:

    def __init__(self, lfr):
       self.params = {}
       self.sources = {}
       self.results = {}

       self.lfr = lfr

       # Same calibration across all images
       self.calibrate_json = EXTRACTED_DIR + "Calibration/mod_0008.json"

       # Per LFR
       self.capture_json = os.path.join(EXTRACTED_DIR, lfr, f"{lfr}.json")
       self.disparity_file = os.path.join(EXTRACTED_DIR, lfr, "depth.pfm")
       self.thumbnail_file = os.path.join(EXTRACTED_DIR, lfr, "thumbnail.png")

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

        self.depth_map = depth_map

        if SHOW_DEPTHS:

            # Get original image for comparison
            if os.path.isfile(self.thumbnail_file):
                fig, (ax_orig, ax_depth) = plt.subplots(1, 2, figsize=(14, 6))
                ax_orig.imshow(plt.imread(self.thumbnail_file))
                ax_orig.set_title("Original")
                ax_orig.axis("off")
            else:
                print(f"Thumbnail not found at {self.thumbnail_file}; showing depth map only")
                fig, ax_depth = plt.subplots(figsize=(8, 6))

            vmin, vmax = np.percentile(depth_map, [2, 98])
            # vmin, vmax = 43, 44
            im = ax_depth.imshow(depth_map, cmap="viridis", vmin=vmin, vmax=vmax)
            cbar = fig.colorbar(im, ax=ax_depth)
            cbar.set_label("Metric depth (mm)")
            ax_depth.set_title("Metric Depth Map")
            ax_depth.axis("off")

            docs_dir = os.path.join(EXTRACTED_DIR, self.lfr, "docs")
            os.makedirs(docs_dir, exist_ok=True)
            fig.savefig(os.path.join(docs_dir, "metric_depth.png"), dpi=150, bbox_inches="tight")

            self.depth_pc()

            plt.show()

    def depth_pc(self):
        """Display a 3D point cloud of the METRIC depth map. Sensor-plane
        pixel coords are back-projected to object space via similar
        triangles (pinhole approximation, using the sourced pixel pitch
        and main-lens focal length), then colored from the thumbnail when
        its resolution matches depth.pfm (true for the PlenoptiCam output
        used here)."""

        if not hasattr(self, "depth_map"):
            raise RuntimeError("depth_pc() requires depth_map_from_disparity() to run first")

        depth_map = self.depth_map
        height_px, width_px = depth_map.shape

        pixel_pitch_mm = self.params.get("pp", DEFAULTS["pp"])
        f_mm = self.params.get("fU", DEFAULTS["fU"])

        ys, xs = np.mgrid[0:height_px, 0:width_px]
        z_mm = depth_map

        # sensor-plane coords (mm, centered on optical axis), back-projected
        # to object-space X/Y using the metric depth at each pixel
        x_sensor_mm = (xs - width_px / 2) * pixel_pitch_mm
        y_sensor_mm = (ys - height_px / 2) * pixel_pitch_mm
        scale = z_mm / f_mm
        x_mm = x_sensor_mm * scale
        y_mm = y_sensor_mm * scale

        colors = None
        if os.path.isfile(self.thumbnail_file):
            thumb = np.asarray(plt.imread(self.thumbnail_file))[..., :3].astype(float)
            if thumb.shape[:2] == depth_map.shape:
                colors = thumb / thumb.max() if thumb.max() > 1 else thumb

        # subsample so the scatter stays responsive
        max_points = 60000
        step = max(1, int(np.sqrt((height_px * width_px) / max_points)))

        x_mm = x_mm[::step, ::step].ravel()
        y_mm = y_mm[::step, ::step].ravel()
        z_sub = z_mm[::step, ::step].ravel()
        c = colors[::step, ::step].reshape(-1, 3) if colors is not None else z_sub

        fig = plt.figure(figsize=(8, 7))
        ax = fig.add_subplot(111, projection="3d")
        sc = ax.scatter(x_mm, y_mm, z_sub, c=c, cmap=None if colors is not None else "viridis",
                         s=2, marker=".")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Depth Z (mm)")
        ax.set_title("Metric Depth Point Cloud")
        if colors is None:
            fig.colorbar(sc, ax=ax, label="Metric depth (mm)")

        docs_dir = os.path.join(EXTRACTED_DIR, self.lfr, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        fig.savefig(os.path.join(docs_dir, "point_cloud.png"), dpi=150, bbox_inches="tight")

        return fig

    def update(self, lfr, virtual_cam_gap=None, disparity_val=None):
        """Main loop, run per frame. Re-derives the capture/disparity paths
        for `lfr` (every extracted LFR follows the same directory layout as
        __init__); the calibration json is shared across all LFRs."""

        self.lfr = lfr
        self.capture_json = os.path.join(EXTRACTED_DIR, lfr, f"{lfr}.json")
        self.disparity_file = os.path.join(EXTRACTED_DIR, lfr, "depth.pfm")
        self.thumbnail_file = os.path.join(EXTRACTED_DIR, lfr, "thumbnail.png")

        # Edit the per frame metadata
        self.add_params(virtual_cam_gap, disparity_val)

        # Calculate with plenoptisign
        self.run_plenopticam()

        if SHOW_VALS: self.report()
        print(self.results)

        # Save the depth map
        self.depth_map_from_disparity()



def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lfr", help="decoded .LFR folder")
    parser.add_argument("--gap", type=float, default=None,
                         help="virtual camera gap G, in px (from PlenoptiCam per-frame output)")
    parser.add_argument("--disparity", type=float, default=None,
                         help=".pfm, measured disparity dx, in px (from PlenoptiCam per-frame output)")
    args = parser.parse_args()
    
    try:
        ps = PlenoptisignLFR(args.lfr)
        ps.update(args.lfr, virtual_cam_gap=args.gap, disparity_val=args.disparity)
    except KeyboardInterrupt:
        print("Ctrl C recieved. Stopping processes")


if __name__=="__main__":
    main()