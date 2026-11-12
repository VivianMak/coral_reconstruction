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

from lib import paths


# Images im working with
IMG = "IMG_0277"
SUBAPERATURE_DIR = os.path.join(paths.DATA_RAW_DIR, IMG, "viewpoints_13px")
paths = sorted(glob.glob(os.path.join(SUBAPERATURE_DIR, "*.png")))

H = 431, W = 620


"""
Given two images, return a disparity map via rgb channel
"""
def compare_imgs(img1, img2):
    pass
    

    # create empty image


    # for each rgb channel, subtract img2 from img1


    # sum up all the changes


def main():

    print("Total Viewpoints:", len(paths))

    # img = cv2.imread(paths[1])

    # if img is None:
    #     print("Error: Could not load image.")
    # else:
    #     cv2.imshow("Image Window", img)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()

    

    # in BGR
    img1 = cv2.imread(paths[0]) 
    img2 = cv2.imread(paths[-1])

    # get height and witdth
    h, w = img1.shape[:2]

    # print("channels", len(img1[1][1]))
    # print(h) #431
    # print(w) #620

    # Compare difference in two images
    # build a heatmap
    compare_imgs(img1, img2)


if __name__=="__main__":
    main()
