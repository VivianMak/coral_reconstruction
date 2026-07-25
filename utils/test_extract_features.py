import numpy as np
import cv2
import os
from matplotlib import pyplot as plt


def preprocess(img, use_clahe=True):
    """
    Require grayscale for local contrast boost.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

    if use_clahe:
        # clipLimit higher than the 2.0 default = more aggressive boost.
        # tileGridSize=(8,8) keeps the equalization local to tentacle-scale regions.
        gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)

    return gray

def show_keypoints(img, kp, alg):
    """Draw the extracted keypoints on each image"""
    output_image = cv2.drawKeypoints(img, kp, None, color=(0, 255, 0))

    plt.figure(figsize=(10, 6))
    plt.imshow(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
    plt.title(f"{alg} - {len(kp)} keypoints, w/o CLAHE")
    plt.axis('off')
    plt.show()


def orb_extract(img):
    """Use orb algorithm"""
    gray = preprocess(img)

    # Initiate STAR detector
    orb = cv2.ORB_create(
        nfeatures=500,
        fastThreshold=10
    )

    kp, des = orb.detectAndCompute(gray, None)
    print(f"[Feature Extracting] ORB: {len(kp)} keypoints")

    return kp, des


def sift_extract(img):
    """Use sift algorithm"""
    gray = preprocess(img)

    sift = cv2.SIFT_create(
        nfeatures=500,          # 0 = keep all kps found
        nOctaveLayers=4,        # more scale samples per octave -> catches tentacles at more thicknesses
        contrastThreshold=0.01,     # lower accepts lower contrast blobs at the cost of noise
        edgeThreshold=20,           # larger = FEWER features filtered out
        sigma=1.2,                  # lower to preserve fine structure
    )

    kp, des = sift.detectAndCompute(gray, None)
    print(f"[Feature Extracting] SIFT: {len(kp)} keypoints")

    return kp, des


def extract_features(img, alg="SIFT", show=False):
    """Takes in image and extracts features with selected algorithm"""

    if alg=="SIFT":
        kp, des = sift_extract(img)
    else:
        kp, des = orb_extract(img)

    if show:
        show_keypoints(img, kp, alg)

    return kp, des

def show_matches(img1, kp1, img2, kp2, good_matches, i):
    """Draw matches on two consecutive frames"""

    output_img = cv2.drawMatches(
        img1, kp1, img2, kp2, good_matches, None, 
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )

    print(f"[Feature Matching] - {len(good_matches)} good matches between images {i} and {i+1} ")

    cv2.imshow('FLANN Feature Matching', output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def match_features(des1, des2):
    # 3. Configure FLANN Matcher parameters
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50) # More checks = higher accuracy, slower speed

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des1, des2, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.1 * n.distance:
            good_matches.append(m)

    return good_matches


def main():
    img_names = ["IMG_0151", "IMG_0152"]
    img_list = []
    kp_list = []
    des_list = []


    for name in img_names:
        img = cv2.imread(f"LFRDatasetExtracted/{name}/thumbnail.png")
        kp, des = extract_features(img, alg="SIFT", show=False)

        img_list.append(img)
        kp_list.append(kp)
        des_list.append(des)

    for i in range(len(img_list) - 1):
        good_matches = match_features(des_list[i], des_list[i + 1])

        show_matches(img_list[i], kp_list[i], img_list[i + 1], kp_list[i + 1], good_matches, i)




if __name__=="__main__":
    main()