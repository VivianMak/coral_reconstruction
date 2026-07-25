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


def show_keypoints(img, kp, title):
    output_image = cv2.drawKeypoints(img, kp, None, color=(0, 255, 0))

    plt.figure(figsize=(10, 6))
    plt.imshow(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
    plt.title(f"{title} - {len(kp)} keypoints, w/o CLAHE")
    plt.axis('off')
    plt.show()

def orb_extract(img):

    # gray = preprocess(img)

    # Initiate STAR detector
    orb = cv2.ORB_create(nfeatures=500,
                        fastThreshold=10)

    # find the keypoints with ORB
    kp, des = orb.detectAndCompute(img, None)
    print(f"ORB: {len(kp)} keypoints")

    show_keypoints(img, kp, "ORB")
    return kp, des


def sift_extract(img):
    # gray = preprocess(img)

    sift = cv2.SIFT_create(
        # 0 = keep every keypoint found, don't rank-and-truncate
        nfeatures=500,
        # more scale samples per octave -> catches tentacles at more thicknesses
        nOctaveLayers=4,
        # THE main lever. Default 0.04 rejects low-contrast blobs, which is
        # exactly what coral tentacles are. 0.01 -> ~4.5x more keypoints.
        # Drop to 0.005 if you still need more, at the cost of noise.
        contrastThreshold=0.01,
        # larger = FEWER features filtered out (inverted vs contrastThreshold).
        # Tentacles are ridge/edge-like, so raising this keeps them.
        edgeThreshold=20,
        # assumed blur already in the image. The LFR thumbnail is soft/decimated,
        # so pre-blurring less (1.2 < 1.6 default) preserves fine structure.
        sigma=1.2,
    )

    kp, des = sift.detectAndCompute(img, None)
    print(f"SIFT: {len(kp)} keypoints")

    show_keypoints(img, kp, "SIFT")
    return kp, des


def akaze_extract(img):
    gray = preprocess(img)

    # NOTE: AKAZE lives in OpenCV 4.x main modules. It was moved out in 5.x,
    # so the plain opencv-python 5.0 wheel does not ship it at all.
    akaze = cv2.AKAZE_create(
        # MLDB = binary descriptor. Use *_UPRIGHT variants if the views are
        # rotation-aligned, which is cheaper and slightly more discriminative.
        descriptor_type=cv2.AKAZE_DESCRIPTOR_MLDB,
        descriptor_size=0,        # 0 = full 486-bit descriptor
        descriptor_channels=3,
        # THE main lever, same story as SIFT's contrastThreshold.
        # Default 0.001 -> 0.0001 gives ~3x more keypoints.
        threshold=0.002,
        nOctaves=4,
        nOctaveLayers=5,
        # WEICKERT diffusion enhances elongated/ridge-like structures, which is
        # the right bias for tentacles. Only ~4% more kp than PM_G2 though.
        diffusivity=cv2.KAZE_DIFF_WEICKERT,
    )

    kp, des = akaze.detectAndCompute(img, None)
    print(f"AKAZE: {len(kp)} keypoints")

    show_keypoints(img, kp, "AKAZE")
    return kp, des


def main():
    img = cv2.imread("LFRDatasetExtracted/IMG_0162/thumbnail.png")

    # img = preprocess(img)
    # plt.imshow(img)
    # plt.show()


    # orb_extract(img)
    # sift_extract(img)
    akaze_extract(img)


if __name__=="__main__":
    main()