import argparse
import glob
import os
import re

import numpy as np
from PIL import Image

FNAME_RE = re.compile(r"^(\d+)_(\d+)\.\w+$")


class SubapertureGrid:
    """Tile PlenoptiCam viewpoint images (row_col.png) into one mosaic laid
    out on the same row/col grid PlenoptiCam used when it sampled each
    viewpoint from a position within the microlens -- i.e. the grid mirrors
    the angular sampling positions across the Lytro's sensor/lenslet array,
    so slight parallax between neighboring tiles is the actual angle shift.
    """

    def __init__(self, viewpoints_dir, thumb_size=120, gap=4, highlight_center=True):
        self.viewpoints_dir = viewpoints_dir
        self.thumb_size = thumb_size
        self.gap = gap
        self.highlight_center = highlight_center

    def _find_views(self):
        paths = glob.glob(os.path.join(self.viewpoints_dir, "*.png"))
        if not paths:
            paths = glob.glob(os.path.join(self.viewpoints_dir, "*.tiff"))
        views = {}
        for p in paths:
            m = FNAME_RE.match(os.path.basename(p))
            if not m:
                continue
            row, col = int(m.group(1)), int(m.group(2))
            views[(row, col)] = p
        if not views:
            raise FileNotFoundError(f"no row_col viewpoint images found in {self.viewpoints_dir}")
        return views

    def build(self):
        views = self._find_views()
        n_rows = max(r for r, _ in views) + 1
        n_cols = max(c for _, c in views) + 1
        center = ((n_rows - 1) / 2, (n_cols - 1) / 2)

        cell = self.thumb_size + self.gap
        mosaic_h = n_rows * cell + self.gap
        mosaic_w = n_cols * cell + self.gap
        mosaic = Image.new("RGB", (mosaic_w, mosaic_h), (30, 30, 30))

        for (row, col), path in views.items():
            img = Image.open(path).convert("RGB")
            img.thumbnail((self.thumb_size, self.thumb_size), Image.LANCZOS)

            if self.highlight_center and (row, col) == (round(center[0]), round(center[1])):
                arr = np.array(img)
                border = 3
                arr[:border, :] = arr[-border:, :] = [255, 60, 60]
                arr[:, :border] = arr[:, -border:] = [255, 60, 60]
                img = Image.fromarray(arr)

            x = self.gap + col * cell
            y = self.gap + row * cell
            mosaic.paste(img, (x, y))

        return mosaic, n_rows, n_cols

    def save(self, out_path="subaperture_grid.png"):
        mosaic, n_rows, n_cols = self.build()
        mosaic.save(out_path)
        print(f"{n_rows}x{n_cols} subaperture grid -> {out_path}")
        return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("viewpoints_dir", help="e.g. LFRDatasetExtracted/IMG_0151/viewpoints_7px")
    parser.add_argument("--out", default=None, help="output mosaic path")
    parser.add_argument("--thumb-size", type=int, default=120, help="pixel size of each tile")
    parser.add_argument("--gap", type=int, default=4, help="pixel gap between tiles")
    parser.add_argument("--no-highlight", action="store_true", help="don't highlight the center view")
    args = parser.parse_args()

    out = args.out or os.path.join(args.viewpoints_dir, "..", "subaperture_grid.png")
    grid = SubapertureGrid(
        args.viewpoints_dir,
        thumb_size=args.thumb_size,
        gap=args.gap,
        highlight_center=not args.no_highlight,
    )
    grid.save(out)


if __name__ == "__main__":
    main()
