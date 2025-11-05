"""Extracts all .LFP files (jpg, depthmap, metadata) from ../data_raw to ../data_extracted"""

# notes: the get directors(), extract metadata(), and load_depth() works and is tested wiht one image

import os
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image   # To view jpg



def get_directories():
    '''Get folders names from data_extracted'''

    folder_list = []
    files = os.listdir("data_raw/")
    for f in files:
        # remove the '.lfp' part 
        folder_list.append(os.path.splitext(f)[0])
    
    return folder_list


def extract_metadata(FILENAME):
    """Extract relevant metadata from .json file"""

    json_path = os.path.join("data_extracted/", FILENAME, f"{FILENAME}.LFP__lfp_meta.json")
    print(json_path)

    # Load metadata json file
    with open(json_path) as f:
        data = json.load(f)

    # Paths to relevant metadata
    depth_info = data["views"][0]["accelerations"][0]["depthMap"]
    per_image = data["views"][0]["accelerations"][0]["perImage"][0]
    lens_meta = data["frames"][0]["frame"]["metadata"]["devices"]["lens"]

    metadata = {
        "width": depth_info["width"],
        "height": depth_info["height"],
        "depth_hash": depth_info["imageRef"].removeprefix("sha1-"),
        "min_lambda": depth_info["minLambda"],
        "max_lambda": depth_info["maxLambda"],
        "jpg_hash": per_image["imageRef"].removeprefix("sha1-"),
        "focal_length": lens_meta["focalLength"],
        "lambda_inf": lens_meta["infinityLambda"],
    }

    return metadata

def load_depth(metadata, FILENAME):
    """Convert unitless lambda map to metric depth map."""

    depth_path = os.path.join("data_extracted/", FILENAME, f"{FILENAME}.LFP__{metadata['depth_hash']}.data")
    
    # Load binary floats - lambda map
    depth = np.fromfile(depth_path, dtype=np.float32).reshape((metadata["height"], metadata["width"]))


    # Normalize depth
    # depth_norm = (depth - metadata["min_lambda"]) / (metadata["max_lambda"] - metadata["min_lambda"])
    # return depth_norm

    # # Metric depth
    depth_real = (float(metadata["focal_length"]) * depth) / (metadata["lambda_inf"] - depth)
    return depth_real


def show_depths(depth_maps, titles, marker=(211,100)):
    '''Visualize all the depth maps as a subgraph with marker and colorbar.'''

    num_images = len(depth_maps)
    cols = min(3, num_images)
    rows = (num_images + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten() 

    for i, (depth, title) in enumerate(zip(depth_maps, titles)):
        im = axes[i].imshow(depth, cmap="inferno", aspect="auto")
        axes[i].set_title(f"{title} Depth Map (Log100)")

        mx, my = marker
        depth_val = depth[my, mx]
        axes[i].plot(mx, my, "ro", markersize=6, markeredgecolor="white", markeredgewidth=1.5)
        axes[i].text(mx + 5, my - 5, f"{depth_val:.3f}",
                     color="white", fontsize=8,
                     bbox=dict(facecolor="black", alpha=0.5, pad=1, edgecolor="none"))

    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    fig.colorbar(im) #, ax=axes.tolist())
    # plt.title("Normalized Depth Maps")
    plt.tight_layout()
    plt.show()

    
def show_jpg(metadata, FILENAME):
    '''Displays the raw jpg image'''

    raw_path = os.path.join("data_extracted/", FILENAME, f"{FILENAME}.LFP__{metadata['jpg_hash']}.data")

    img = Image.open(raw_path)
    plt.figure()
    plt.imshow(img)
    plt.show()


def generate_point_cloud(depth_real):
    '''NOT TESTED:
    Generate a simple scatter plot of dpeth map'''

    depths = []
    x = []
    y = []

    for i, depth_w in enumerate(depth_real):
        for j, depth2 in enumerate(depth_w):
            x.append(i)
            y.append(j)
            depths.append(depth2)

    fig = plt.figure()
    ax = plt.axes(projection='3d')

    start = 0
    end = 50000

    sc = ax.scatter(x[start:end], y[start:end], 
            depths[start:end], c=depths[start:end], cmap='inferno', # color
            marker='.')
    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_zlabel('Depth')
    ax.set_title('Depth Naive Point Cloud')
    ax.legend()

    # Color bar visualization
    fig.colorbar(sc, ax=ax, label="Depth")

    ax.set_box_aspect(None, zoom=0.80)
    plt.show()

def main():
    """Process all files"""

    folders = get_directories()
    # print(folder_list)

    depth_maps = []
    titles = []

    # Loop through the different images
    for f in folders:
        print(f"PROCESSING IMAGES IN FOLDER: {f}")
        metadata = extract_metadata(f)
        print(metadata)

        depth_norm = load_depth(metadata, f)

        depth_maps.append(np.log(depth_norm)/np.log(100))
        titles.append(f)
    
    show_depths(depth_maps, titles)

if __name__ == "__main__":
    main()