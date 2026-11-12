"""
Find the difference in subaperature across 13 by 13 grid
"""

import argparse
import glob
import os
import re

import numpy as np
from PIL import Image

import cv2
import matplotlib.pyplot as plt

from lib import paths


# Images im working with
IMG = "IMG_0277"
SUBAPERATURE_DIR = os.path.join(paths.DATA_RAW_DIR, IMG, "viewpoints_13px")
view_paths = sorted(glob.glob(os.path.join(SUBAPERATURE_DIR, "*.png")))

H = 431
W = 620


"""
Given two images, return a disparity map via rgb channel
"""
def compare_imgs(img1, img2):

    diff = cv2.absdiff(img1, img2)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

    # gray_diff = (gray_diff > 30).astype('uint8') * 255

    return gray_diff

    image_dif = np.zeros((H, W, 3), dtype=np.uint8)

    # for each bgr channel, subtract img2 from img1
    for i in range(3):
        image_dif[:, :, i] = np.abs((img1[:, :, i].astype(np.int16) - img1[:, :, i].astype(np.int16)))

    return image_dif


def main():

    print("Total Viewpoints:", len(view_paths))

    n = 3

    # Load images in rgb
    img1 = cv2.imread(view_paths[n])
    img2 = cv2.imread(view_paths[n+1])

    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    # get height and witdth
    # h, w, d = img1.shape[:3]

    # Compare difference in two images
    # build a heatmap
    img = compare_imgs(img1, img2)

    binary_diff = (img > 30).astype(np.int16) * 255

    # Make subplot for comparison

    fig, axes = plt.subplots(2, 2, figsize=(15, 5))

    images = [img1, img2, img, binary_diff]
    titles = ['Image 1', 'Image 2', 'Image Dif', 'Binary Dif']

    for ax, img, title in zip(axes, images, titles):
        print(title)
        ax.imshow(img, cmap='gray' if img.ndim == 2 else None)
        ax.set_title(title)
        ax.axis('off')  # Hide axis ticks and labels

    plt.tight_layout()
    plt.show()

    return None

    if img is None:
        print("Error: Could not load image.")
    else:
        cv2.imshow("Image Window", img)
        # cv2.imwrite(os.path.join(paths.IMG_DOC, "BGR_diff.png"), img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__=="__main__":
    main()
