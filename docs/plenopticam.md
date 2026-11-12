# Decoding Light Fields with Plenopticam CLI

### Plenopticam
- https://libraries.io/pypi/plenopticam
- https://github.com/hahnec/plenopticam

```bash
# Setting up plenopticam/workspace
python --version    # Python 3.10
sudo apt install python3-tk
pip install -r requirements.txt
plenopticam -h      # Check package 
```
```bash
python -m utils.decode_lfr
```


### Output folder contents

Results are saved in the folder (`LFRDataExtracted/source_name`), with the following contents:

- **`viewpoints_xxx/`** — sub-aperture (angular view) images, one per virtual viewpoint, plus a view animation GIF
- **Depth data** — the depth map written by `Write depth data`. *(Check the actual output folder for the exact filename/format — likely a `.png`/`.tiff`/`.pgm` in a `depth_xxx` or similarly named folder or file; confirm and fill in here once you've inspected `Bee_1/`.)*
- **`refo_xxx/`** — refocused image stack (focal stack) at different focus planes, plus a refocus animation GIF
- Calibration data derived from the microlens grid analysis (from `Save calibration data`)


## Datasets
- http://clim.inria.fr/IllumDatasetLF/index.html
- http://lightfield.stanford.edu/lfs.html
- https://plenodb.jpeg.org/
- https://lightfields.stanford.edu/mvlf/
- https://plenodb.jpeg.org/lf/epfl/
- https://marine.acfr.usyd.edu.au/research/plenoptic-imaging/
    - Researcher - https://scholar.google.com.au/citations?user=MVfxch0AAAAJ&hl=en