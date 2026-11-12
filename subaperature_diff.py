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
import seaborn as sns

from lib import paths


# Images im working with
IMG = "IMG_0277"
SUBAPERATURE_DIR = os.path.join(paths.DATA_RAW_DIR, IMG, "viewpoints_13px")
view_paths = sorted(glob.glob(os.path.join(SUBAPERATURE_DIR, "*.png")))

H = 431
W = 620

VIEWS = 13


"""
Given two images, return a disparity map via rgb channel
"""
def compare_imgs(img1, img2, threshold=None):
    
    # Get grayscale image difference (0-255)
    diff = cv2.absdiff(img1, img2)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)

    # Find intersection of pixels that aren't black
    valid = (img1.max(axis=2) > 0) & (img2.max(axis=2) > 0) #431×620

    # Apply pixel dif to valid pixels - Ignore vignetting
    pixel_diff = gray_diff[valid]

    # Plot valid pixels
    # plt.figure()
    # plt.hist(pixel_diff, bins=256, range=(0, 255))
    # plt.yscale('log')
    # plt.xlabel('Pixel value (0-255)')
    # plt.ylabel('Pixel count (log)')
    # plt.title('Pixel Dif histogram')
    # plt.show()

   
    # Quantify the results  
    mean_diff = pixel_diff.mean()   # Average pixel change

    if threshold is not None:
        percent_change = 100 * (pixel_diff > threshold).mean() / 255
    else:
        percent_change = 100 * pixel_diff.mean() / 255  # use every pixel

    results = [
        percent_change,
        mean_diff
    ]

    print(f"Percent Change: {percent_change:.3f} %")
    print(f"Mean Change: {mean_diff:.3f} px")

    return gray_diff, results


"""
Given a 13 by 13 view, create a heatmap of the pixel disparity between images
"""
def create_heatmap():

    # Create 2d array of percentage dif for 13 by 13
    percentages = np.zeros((13, 13), dtype=float)

    for i in range(VIEWS):
        for j in range(VIEWS):

            # Convert paths to rgb images
            img1 = cv2.imread(view_paths[i])
            img2 = cv2.imread(view_paths[j])
            
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

            # Compare images
            _, results = compare_imgs(img1, img2)

            percentages[i, j] = results[0]


    # plt.imshow(percentages, cmap="inferno")
    # plt.colorbar(label="Value")

    sns.heatmap(percentages, annot=True, fmt=".2f", cmap="coolwarm")
   
    plt.title("Heatmap of Pixel Change Across 13 by 13")
    plt.show()

    return None



def main():

    # print("Total Viewpoints:", len(view_paths))

    # create_heatmap()
    

    n = 3

    # Load images in rgb
    img1 = cv2.imread(view_paths[n])
    img2 = cv2.imread(view_paths[n+1])

    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    # Compare difference in two images
    dif, results = compare_imgs(img1, img2)


    # Make subplot for comparison
    images = [img1, img2, dif]

    fig, axes = plt.subplots(1,3)

    titles = ['Image 1', 'Image 2', 'Image Dif', 'Overlapped']

    for ax, im, title in zip(axes.flat, images, titles):
        ax.imshow(im, cmap='gray' if im.ndim == 2 else None)
        ax.set_title(title)
        # ax.axis('off')  # Hide axis ticks and labels

    
    plt.tight_layout()

    subplot_title = ""
    cv2.imwrite(os.path.join(paths.IMG_DOC, f"{subplot_title}.png"), ax)
    
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
