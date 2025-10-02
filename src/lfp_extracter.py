"""Extracts all .LFP files (jpg, depthmap, metadata) from ../data_raw to ../data_extracted"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image   # To view jpg

def main():
    """Process all files in /data_raw."""

    file_list = os.listdir("../data_raw/")

    for f in file_list:
        data = extract_metadata(file)
        load_depth(data[1], data[2], focal_len, lambda_inf)



def extract_metadata(FILENAME):
    """Get useful camera metadata from extracted .json file"""

    data_list = []

    # Load metadata json file
    with open('../data_extracted/' + FILENAME, 'r') as f:
        data = json.load(f)

    # Extract depth map data
    depthMap = data["views"][0]["accelerations"][0]["depthMap"]
    data_list.append(depthMap["width"], 
                     depthMap["height"],
                     depthMap["imageRef"], #need to filter out "sha1"
                     depthMap["minLambda"], 
                     depthMap["maxLambda"])

    # Extract jpg

    # Extract calibration metrics


    return data_list

def load_depth(h, w, focal_len, lambda_inf, DEPTH_HASH):
    """Show the adjusted real world depth map in metric units."""

    # Load binary floats
    depth = np.fromfile(
        "../data_extracted" + DEPTH_HASH,
        dtype=np.float32
    ).reshape((h, w))

    # # Normalize for viewing
    # depth_norm = (depth - minLambda) / (maxLambda - minLambda)

    depth_real = (focal_len * (depth * (6/0.0019))) / (depth- lambda_inf)

    plt.figure()
    plt.imshow(depth_real, cmap="inferno")
    plt.title("Metric Depth Map")
    plt.colorbar()
    plt.show()
    
    return depth_real

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