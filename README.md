# 3D Dynamic Coral Reconstruction with a Light Field Approach

This project is part of CREST Lab advised by Dr. Victoria Preston.

### Motivation
Coral reef systems, especially soft corals, are a very vulnerable ecosystem that changes frequently with each pass of ocean wave movement. Unlike hard corals, soft corals lack a calcium carbonate skeleton, making them particularly sensitive to external environmental factors. Being able to model these ecosystems over multiple expeditions provides a valuable opportunity to compare changes and enhance our understanding of overall ecosystem dynamics and the effects of climate change.

This research project aims to answer the question: <u>__“Through scientific experiments and design, can a single light field camera (Lytro Illum) be used for accurate 3D dynamic reconstruction of soft corals?”__</u>

# Datasets
- http://clim.inria.fr/IllumDatasetLF/index.html
- http://lightfield.stanford.edu/lfs.html
- https://plenodb.jpeg.org/
- https://lightfields.stanford.edu/mvlf/
- https://plenodb.jpeg.org/lf/epfl/
- https://marine.acfr.usyd.edu.au/research/plenoptic-imaging/
    - Researcher - https://scholar.google.com.au/citations?user=MVfxch0AAAAJ&hl=en

# Decoding Light Fields (LFR)

### Plenopticam
- https://libraries.io/pypi/plenopticam
- https://github.com/hahnec/plenopticam

```sh
pip3 install plenopticam
plenopticam -h
./decode_lfr.sh
```
```
plenopticam -f LFRDataset/Bee_1.LFR -c LFRDataset/Calibration/caldata-B5144000580.ta
```

### Output folder contents

Results are saved in the folder (`LFRDataExtracted/source_name`), with the following contents:

- **`viewpoints_xxx/`** — sub-aperture (angular view) images, one per virtual viewpoint, plus a view animation GIF
- **Depth data** — the depth map written by `Write depth data`. *(Check the actual output folder for the exact filename/format — likely a `.png`/`.tiff`/`.pgm` in a `depth_xxx` or similarly named folder or file; confirm and fill in here once you've inspected `Bee_1/`.)*
- **`refo_xxx/`** — refocused image stack (focal stack) at different focus planes, plus a refocus animation GIF
- Calibration data derived from the microlens grid analysis (from `Save calibration data`)

> Note: "Potential data loss as directory already exists" appeared twice — PlenoptiCam is warning it's overwriting a prior `Bee_1/` output folder from an earlier run. Back up prior results before re-running if you need to keep them.



# Dynamic Fusion