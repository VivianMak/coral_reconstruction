# Lytro Illum → Depth Map: Python Pipeline (no Lytro Desktop)

## The shape of the pipeline

```
LFR/XRAW file ──▶ [decode + 4D align] ──▶ sub-aperture image grid ──▶ [depth est.] ──▶ depth map
   (camera)         PlenoptiCam              N×N viewpoint array       you write this    (float, metres-ish)
                    + calibration
```

Two tools do the front half:
- **PlenoptiCam** — does the hard part (calibration, microlens-grid alignment, 4D
  rearrangement) and outputs usable sub-aperture (viewpoint) images.
- **lfptools / LF Toolbox** — only unpacks the container to a raw Bayer frame. Use
  *only* if you want to write your own alignment. Not recommended for getting to
  depth quickly.

The back half (depth) is standard light-field computer vision that you write
yourself — PlenoptiCam does **not** export a finished depth map.

---

## Step 0 — Decide your calibration strategy (do this first, it gates everything)

PlenoptiCam needs the camera's white-image / calibration data to align an Illum
capture correctly. Three ways to get it, easiest first:

1. **Shoot XRAW on the camera (recommended).** XRAW bundles the per-camera
   calibration data *inside each file*, so no separate calibration archive is
   needed. Set it on the camera under `Settings → File Format → LYTRO XRAW`.
   Trade-off: files are ~2× the size and post-capture write is slower, so frame
   rate drops. Fine for offline capture, less so for rapid bursts.

2. **Extract a `caldata-Bxxxx.tar` archive once per camera body.** This is the
   factory calibration. Normally the first Desktop sync backs it up; without
   Desktop you're relying on pulling it off the camera/SD directly, which is the
   fiddly path. If you already have this tar from a prior sync, reuse it forever.

3. **Use a public white-image / calibration dataset** as an approximation for
   testing (e.g. the IEEE DataPort "Lytro Illum Calibration Dataset", or the
   Stanford Lytro Light Field Archive which ships already-decoded data + depth
   maps). Calibration is *per-body*, so a generic white image is only an
   approximation — good enough to prototype, not for final accuracy.

> Shortcut for prototyping: the Stanford Lytro Light Field Archive provides
> decoded Illum captures **with depth maps and metadata already included**. If you
> just need data to build the tracking side against, start there and skip Steps
> 1–3 until your own captures are ready.

---

## Step 1 — Install

```bash
python -m venv lf && source lf/bin/activate
pip install plenopticam numpy opencv-python scipy
# optional, for nicer depth viz / filtering:
pip install matplotlib scikit-image
```

PlenoptiCam ships a CLI and a small GUI. The CLI is the reliable, scriptable
entry point — use it for the decode, then move to Python for depth.

---

## Step 2 — Decode the light field → sub-aperture images

### Via CLI (most robust)

```bash
# single file
plenopticam -f '/path/IMG_0001.lfr' -c '/path/caldata-B5144000XXX.tar'

# whole folder, auto-matching calibration by serial:
plenopticam -f '/path/captures/' -c '/path/caldata_dir/' -p
plenopticam -h   # see all options (refocus refinement, Scheimpflug, etc.)
```

If you shot XRAW, point `-c` at the same file (the calibration travels with it),
or use the folder mode and let it auto-find the white image.

### What lands on disk

Results go in a folder named after the input file. Relevant outputs:

| Folder            | Contents                                              |
|-------------------|-------------------------------------------------------|
| `viewpoints_xxx/` | **The sub-aperture image grid** — this is your input to depth. An N×N set of slightly-shifted views of the same scene. |
| `refo_xxx/`       | Refocused image stack (a focal stack) + a refocus GIF. Only needed if you use the depth-from-focus route. |
| (reader stage)    | A TIFF in Bayer representation + a JSON of metadata used for gamma correction. |

The viewpoint grid is the key product. Each image is one "virtual camera"
position behind the main lens; the shift of a scene point between viewpoints is
your depth cue.

> Resolution warning: light-field cameras trade spatial resolution hard. Each
> sub-aperture view is low-res (the Illum's 2D export peaks around 4MP, and a
> single viewpoint is a fraction of that). This caps how fine a feature you can
> localise — plan tracking features accordingly.

---

## Step 3 — Load the viewpoint grid in Python

```python
import os, glob, cv2, numpy as np

VP_DIR = "/path/IMG_0001/viewpoints_15px"   # whatever the folder is named

# Files are typically named by grid coordinate, e.g. 0000_0000.png ... load into a
# 4D array: LF[s, t, y, x, c]  (s,t = angular/view axes; y,x = spatial; c = colour)
def load_lightfield(vp_dir):
    paths = sorted(glob.glob(os.path.join(vp_dir, "*.png")))
    # infer grid size from filenames; adjust the parser to your actual naming
    coords = []
    for p in paths:
        s, t = os.path.splitext(os.path.basename(p))[0].split("_")
        coords.append((int(s), int(t), p))
    S = max(c[0] for c in coords) + 1
    T = max(c[1] for c in coords) + 1
    sample = cv2.imread(coords[0][2])
    H, W, C = sample.shape
    LF = np.zeros((S, T, H, W, C), np.uint8)
    for s, t, p in coords:
        LF[s, t] = cv2.imread(p)
    return LF  # shape (S, T, H, W, 3)

LF = load_lightfield(VP_DIR)
S, T = LF.shape[:2]
cy, cx = S // 2, T // 2          # central view = your "main" RGB image
center = LF[cy, cx]
```

---

## Step 4 — Estimate depth (pick a route)

### Route A — Disparity between sub-aperture pairs (quickest to working result)

Treat two horizontally-adjacent views as a stereo pair. Disparity ∝ 1/depth.

```python
left  = cv2.cvtColor(LF[cy, cx - 1], cv2.COLOR_BGR2GRAY)
right = cv2.cvtColor(LF[cy, cx + 1], cv2.COLOR_BGR2GRAY)

# baselines between adjacent Lytro views are tiny → disparities are small &
# sub-pixel. Keep numDisparities low and rely on SGBM's sub-pixel output.
sgbm = cv2.StereoSGBM_create(
    minDisparity=0, numDisparities=16, blockSize=5,
    P1=8*5**2, P2=32*5**2, uniquenessRatio=10,
    speckleWindowSize=50, speckleRange=2, mode=cv2.STEREO_SGBM_MODE_HH)
disp = sgbm.compute(left, right).astype(np.float32) / 16.0   # 1/16-px units
```

- Pros: fast, uses tools you know.
- Cons: tiny baseline → noisy, low dynamic range in depth. Averaging disparity
  over *several* view pairs (left/right and up/down, and 2-step baselines)
  improves it a lot.

### Route B — Epipolar Plane Image (EPI) slope (more light-field-native, robust)

Stack a row of views and read the slope of feature streaks; slope encodes depth.
This is what most LF depth papers use and handles the small-baseline regime
better than naive stereo.

```python
# Build a horizontal EPI for image row y0: vary t (view), keep s = cy
y0 = center.shape[0] // 2
epi = LF[cy, :, y0, :, :]          # shape (T, W, 3)  -> a "t vs x" slice
# Depth ∝ 1 / slope of lines in this t-x image. Estimate slope per x via the
# structure tensor (orientation of local gradients):
gray = cv2.cvtColor(epi, cv2.COLOR_BGR2GRAY).astype(np.float32)
gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
gt = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
Jxx = cv2.GaussianBlur(gx*gx, (0,0), 1.5)
Jtt = cv2.GaussianBlur(gt*gt, (0,0), 1.5)
Jxt = cv2.GaussianBlur(gx*gt, (0,0), 1.5)
# local orientation -> slope -> disparity
theta = 0.5*np.arctan2(2*Jxt, (Jxx - Jtt))
slope = np.tan(theta)              # relate to disparity/depth per your geometry
```

Do this for every row to fill a full disparity map; repeat on vertical EPIs
(`LF[:, cx, :, x0, :]`) and fuse for noise reduction.

- Pros: best signal from a dense small-baseline LF; gives confident depth on
  textured edges.
- Cons: more code; weak in textureless regions (true of all these methods).

### Route C — Depth from focus (uses the `refo_xxx` stack)

For each pixel, find which refocus plane is sharpest → that index maps to depth.

```python
import glob
stack = [cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY).astype(np.float32)
         for p in sorted(glob.glob("/path/IMG_0001/refo_15px/*.png"))]
stack = np.stack(stack, 0)                       # (D, H, W)
# sharpness = local variance of Laplacian per slice
sharp = np.stack([cv2.Laplacian(s, cv2.CV_32F)**2 for s in stack], 0)
sharp = np.stack([cv2.GaussianBlur(s, (0,0), 2) for s in sharp], 0)
depth_idx = np.argmax(sharp, 0).astype(np.float32)   # focus-plane index per pixel
```

- Pros: trivially simple, no view-matching.
- Cons: coarse (depth resolution = number of refocus planes), fails on
  low-texture pixels, and the index→metric-depth mapping needs calibration.

**Recommendation for tracking work:** Route B (EPI), fused horizontal+vertical,
with Route A as a fast sanity check while you build. Route C only if you need a
quick rough depth and already have the refocus stack.

---

## Step 5 — Clean up the depth map

```python
# normalise, fill holes, edge-preserving smooth
d = disp.copy()
d[d <= 0] = np.nan
# fill small gaps
mask = np.isnan(d).astype(np.uint8)
d_filled = cv2.inpaint(np.nan_to_num(d).astype(np.float32), mask, 3, cv2.INPAINT_TELEA)
# edge-aware smoothing guided by the central RGB view
d_smooth = cv2.ximgproc.guidedFilter(center, d_filled, radius=8, eps=1e-2) \
           if hasattr(cv2, "ximgproc") else cv2.bilateralFilter(d_filled, 9, 50, 50)
```

If you need **metric** depth (real distances) rather than relative disparity, you
need the camera geometry. PlenoptiCam pairs with the companion tool
**PlenoptiSign** to pinpoint metric object positions in the captured light field
— use that to calibrate the disparity→distance mapping rather than guessing it.

---

## Quick reference: file formats you'll touch

| Format | Where it comes from | Contains |
|--------|--------------------|----------|
| `.lfr` / `.raw` | straight off camera (RAW) | light-field data, **no** calibration |
| XRAW | camera, if selected | light-field data **+** calibration (≈110 MB) |
| `caldata-Bxxxx.tar` | factory calibration / Desktop backup | white images + per-body calibration |
| `viewpoints_*/` PNGs | PlenoptiCam output | sub-aperture grid — **depth input** |
| `refo_*/` PNGs | PlenoptiCam output | refocus / focal stack |
| ESLF | LF Toolbox convention | decoded sub-aperture light field (alt. format) |

---

## Gotchas worth knowing before you start

- **Calibration quality gates everything.** A wrong/approximate white image makes
  every downstream depth value wrong. Verify the central view looks clean and
  artifact-free before trusting depth.
- **Small baselines = small disparities.** Lytro views are very close together;
  keep `numDisparities` small and lean on sub-pixel / EPI methods.
- **Textureless regions have no depth.** All three routes fail on flat colour;
  expect to inpaint/interpolate, or fuse with the central RGB for guidance.
- **Per-frame decode is heavy.** Benchmark one full file end-to-end before
  assuming a batch or stream will keep up; the alignment step is the bottleneck.
- **Lytro's own pipeline is closed and unmaintained** (company shut down 2018),
  so PlenoptiCam is the maintained path — pin your version and dataset.

---

*Note: PlenoptiCam CLI flags and output folder names are stable per its docs; the
Python depth code above is standard OpenCV/numpy and is meant as a starting
scaffold — adjust the viewpoint-filename parser and the disparity→depth geometry
to your actual decoded output and camera settings.*
