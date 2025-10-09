"""Extracts all .LFP files (jpg, depthmap, metadata) from ../data_raw to ../data_extracted"""

# notes: the get directors(), extract metadata(), and load_depth() works and is tested wiht one image

import os
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image   # To view jpg

def main():
    """Process all files in /data_raw."""

    folder_list = get_directories()
    print(folder_list)

    depth_maps = []
    titles = []

    # Loop through the different images
    for f in folder_list:
        print(f"IMAGE PROCESSING: {f}")
        data = extract_metadata(f)
        print(data)
        # (w, h, focal_len, lambda_inf, DEPTH_HASH, FILENAME):
        depth_norm = load_depth(data[0], data[1], data[6], data[7], data[2], f, data[3], data[4])
        depth_maps.append(depth_norm)
        titles.append(f)
    
    show_depths(depth_maps, titles)


def get_directories():
    '''Get folders from data_extracted'''

    folder_list = []
    files = os.listdir("../data_raw/")
    for f in files:
        # only get the image name
        folder_list.append(os.path.splitext(f)[0])
    
    return folder_list


def extract_metadata(FILENAME):
    """Get useful camera metadata from extracted .json file"""

    data_list = []

    # Load metadata json file
    with open('../data_extracted/' + FILENAME + '/' + 
              FILENAME + '.LFP__lfp_meta.json', 'r') as f:
        data = json.load(f)

    # Extract depth map data
    depthMap = data["views"][0]["accelerations"][0]["depthMap"]
    data_list.extend([depthMap["width"], 
                     depthMap["height"],
                     depthMap["imageRef"].removeprefix("sha1-"),
                     depthMap["minLambda"], 
                     depthMap["maxLambda"]])

    # Extract raw jpg
    raw_img = data["views"][0]["accelerations"][0]["perImage"][0]["imageRef"].removeprefix("sha1-")


    # Extract calibration metrics
    focal_len = data["frames"][0]["frame"]["metadata"]["devices"]["lens"]["focalLength"]
    lambda_inf = data["frames"][0]["frame"]["metadata"]["devices"]["lens"]["infinityLambda"]

    data_list.extend([raw_img, focal_len, lambda_inf])

    return data_list

def load_depth(w, h, focal_len, lambda_inf, DEPTH_HASH, FILENAME, minLambda, maxLambda):
    """Show the adjusted real world depth map in metric units."""

    # Load binary floats
    depth = np.fromfile(
        "../data_extracted/" + FILENAME + "/" + 
        FILENAME + '.LFP__' + DEPTH_HASH + ".data",
        dtype=np.float32
    ).reshape((h, w))


    # Normalize depth
    # depth_norm = (depth - minLambda) / (maxLambda - minLambda)
    # return depth_norm

    # Metric depth
    normalizing_const = 0.1524/depth[100, 211]
    print(f"UNNORMALIZED DEPTH IS: {depth[100, 211]}")
    depth_real = (float(focal_len) * depth * normalizing_const) / (depth - lambda_inf)
    return depth_real


    # Showing a singular depth map
    # plt.figure()
    # plt.imshow(depth_norm, cmap="inferno")
    # plt.title(f"{FILENAME} Metric Depth Map")
    # plt.colorbar()
    # plt.show()
    # time.sleep(1)
    # plt.close()

def show_depths(depth_maps, titles):
    '''Showing all the depth maps as a subgraph'''
    # --- Plot all at once ---
    num_images = len(depth_maps)
    cols = min(3, num_images)
    rows = (num_images + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten() if num_images > 1 else [axes]

    marker_x = 211
    marker_y = 100

    for i, depth_norm in enumerate(depth_maps):
        im = axes[i].imshow(depth_norm, cmap="inferno", aspect='auto')
        axes[i].set_title(titles[i] + " Depth Map")

        depth_val = depth_norm[marker_y, marker_x]
        # --- Add a red cross marker ---
        axes[i].plot(marker_x, marker_y, 'ro', markersize=6, markeredgecolor='white', markeredgewidth=1.5)

        # --- Add text annotation with depth value ---
        axes[i].text(marker_x + 5, marker_y - 5,
                f"{depth_val:.3f}",
                color='white', fontsize=8,
                bbox=dict(facecolor='black', alpha=0.5, pad=1, edgecolor='none'))

    # Hide any extra empty subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    fig.colorbar(im)
    plt.tight_layout()
    plt.show()

    
def load_jpg(JPG_HASH):
    """Shows the raw jpg image after extraction"""

    img = Image.open("../data_extracted/" + JPG_HASH)
    plt.figure()
    plt.imshow(img)
    plt.show()


def generate_point_cloud(depth_real):
    """"""
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


if __name__ == "__main__":
    main()