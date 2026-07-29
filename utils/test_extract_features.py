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

def show_matches(img1, kp1, img2, kp2, good_matches, img_name1, img_name2):
    """Draw matches on two consecutive frames"""

    output_img = cv2.drawMatches(
        img1, kp1, img2, kp2, good_matches, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )

    # label with image name
    RED = (0, 0, 255)   # BGR
    for text, x in [(img_name1, 10), (img_name2, img1.shape[1] + 10)]:
        cv2.putText(output_img, text, (x, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, RED, 2, cv2.LINE_AA)

    print(f"[Feature Matching] - {len(good_matches)} good matches between images {img_name1} and {img_name2} ")

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
        if m.distance < 0.8 * n.distance:
            good_matches.append(m)

    return good_matches


def ransac_filter(matches, kp1, kp2, reproj_thresh=2.0, confidence=0.99):
    """Keep only the matches consistent with a single epipolar geometry.

    The ratio test compares descriptors only, so it passes matches that look
    alike but are geometrically impossible (e.g. coral in one frame -> wall in
    the other). Fitting a fundamental matrix with RANSAC rejects those.
    """
    # the 8-point algorithm needs at least 8 correspondences
    if len(matches) < 8:
        print(f"[RANSAC] only {len(matches)} matches, need 8+ -- skipping filter")
        return matches

    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

    _, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC,
                                     reproj_thresh, confidence)

    # RANSAC can fail to reach consensus, in which case there is nothing to trust
    if mask is None:
        print("[RANSAC] no consensus found -- keeping all matches")
        return matches

    inliers = [m for m, keep in zip(matches, mask.ravel()) if keep]
    print(f"[RANSAC] {len(inliers)}/{len(matches)} matches are geometrically consistent")

    return inliers


def depth_at(depth_map, pt):
    """Sample a depth map at a keypoint's (subpixel) location.

    Keypoint coords are floats, depth maps are indexed [row, col] = [y, x],
    so round and clamp to stay inside the array.
    """
    x, y = int(round(pt[0])), int(round(pt[1]))
    y = min(max(y, 0), depth_map.shape[0] - 1)
    x = min(max(x, 0), depth_map.shape[1] - 1)

    return depth_map[y, x]


def filter_kp_by_depth(kp, des, depth_map, dmin, dmax):
    """Keep only the keypoints whose depth falls inside [dmin, dmax].

    Run before matching, to throw away background (wall, table) keypoints so
    they never get the chance to form a false match in the first place.
    """
    keep = [i for i, k in enumerate(kp) if dmin <= depth_at(depth_map, k.pt) <= dmax]

    kp_filtered = [kp[i] for i in keep]
    # descriptor rows must be re-indexed with the SAME indices, otherwise each
    # descriptor no longer corresponds to its keypoint
    des_filtered = des[keep] if des is not None else None

    print(f"[Depth] kept {len(kp_filtered)}/{len(kp)} keypoints within depth [{dmin}, {dmax}]")

    return kp_filtered, des_filtered


def filter_matches_by_depth(matches, kp1, kp2, depth1, depth2, tol=0.01):
    """Drop matches whose two endpoints disagree on depth.

    The same physical point should sit at a similar depth in both frames, so a
    large disagreement suggests a false match.
    """
    if not matches:
        return matches

    d1 = np.array([depth_at(depth1, kp1[m.queryIdx].pt) for m in matches])
    d2 = np.array([depth_at(depth2, kp2[m.trainIdx].pt) for m in matches])

    # PlenoptiCam normalizes each frame's depth.pfm to [0,1] independently, so a
    # constant per-frame offset survives even for correct matches. Measured ~0.03
    # between IMG_0152/IMG_0162, which is larger than tol -- subtract it first or
    # the filter rejects everything.
    offset = np.median(d1 - d2)
    resid = np.abs((d1 - d2) - offset)

    inliers = [m for m, r in zip(matches, resid) if r <= tol]
    print(f"[Depth] {len(inliers)}/{len(matches)} matches agree on depth "
          f"(tol={tol}, offset={offset:+.4f})")

    return inliers


def main():
    # IMG_0152"
    img_names = ["IMG_0159", "IMG_0162"]
    img_list = []
    kp_list = []
    des_list = []


    # depth_list = []

    for name in img_names:
        img = cv2.imread(f"LFRDatasetExtracted/{name}/thumbnail.png")
        kp, des = extract_features(img, alg="SIFT", show=False)

        # depth map, a 2d array the same HxW as img, one depth per pixel
        # depth = load_depth(name)
        # kp, des = filter_kp_by_depth(kp, des, depth, dmin=0.45, dmax=0.52)
        # depth_list.append(depth)

        img_list.append(img)
        kp_list.append(kp)
        des_list.append(des)

    for i in range(len(img_list) - 1):
        good_matches = match_features(des_list[i], des_list[i + 1])
        good_matches = ransac_filter(good_matches, kp_list[i], kp_list[i + 1])
        # good_matches = filter_matches_by_depth(good_matches, kp_list[i], kp_list[i + 1],
        #                                        depth_list[i], depth_list[i + 1], tol=0.01)

        show_matches(img_list[i], kp_list[i], img_list[i + 1], kp_list[i + 1], good_matches, img_names[i], img_names[i+1])




if __name__=="__main__":
    main()