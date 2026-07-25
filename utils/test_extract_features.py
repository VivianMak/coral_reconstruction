import numpy as np
import cv2
import os
from matplotlib import pyplot as plt

def orb_extract(img):

    # Initiate STAR detector
    orb = cv2.ORB_create(nfeatures=2000,
                        fastThreshold=10)

    # find the keypoints with ORB
    kp, des = orb.detectAndCompute(img, None)

    print(len(kp))

    # draw only keypoints location,not size and orientation
    output_image = cv2.drawKeypoints(img, kp, None, color=(0,255,0))


    plt.figure(figsize=(10, 6))
    plt.imshow(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.show()



def main():
    img = cv2.imread("LFRDatasetExtracted/IMG_0162/thumbnail.png")

    orb_extract(img)
