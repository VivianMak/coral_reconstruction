# IMG_0274
# IMG_0276

import re
import numpy as np
import matplotlib.pyplot as plt



def read_pfm(file_path):
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


def main():
    disparity_file = "data/LFRDatasetExtracted/IMG_0277/depth.pfm"

    import os
    print(os.path.exists(disparity_file))

    disparity_map = read_pfm(disparity_file)

    disparity_map = np.asarray(disparity_map, dtype=float)
    # depth_map = np.zeros_like(disparity_map)
    # unique_vals = np.unique(disparity_map)


    fig, ax_depth = plt.subplots(figsize=(8, 6))
    vmin, vmax = np.nanpercentile(disparity_map, [2, 98])
    im = ax_depth.imshow(disparity_map, cmap="viridis", vmin=vmin, vmax=vmax)
    cbar = fig.colorbar(im, ax=ax_depth)
    cbar.set_label("Disparity (px)")
    ax_depth.set_title("Disparity Map")
    ax_depth.axis("off")

    # docs_dir = os.path.join(EXTRACTED_DIR, self.lfr, "docs")
    # os.makedirs(docs_dir, exist_ok=True)
    # fig.savefig(os.path.join(docs_dir, "disparity_map.png"), dpi=150, bbox_inches="tight")

    plt.show()
    # plt.close(fig)

if __name__=="__main__":
    main()


