"""
Workflow:

LFR/XRAW file ──▶ [decode + 4D align] ──▶ sub-aperture image grid ──▶ [depth est.] ──▶ depth map
   (camera)         PlenoptiCam              NxN viewpoint array       you write this    (float, metres-ish)
                    + calibration
"""

import cv2
import numpy as np

class LytroDepth:

    def __init__(self):
        
        self.img_list = {
            "LEFT": [],
            "RIGHT": []
        }


    def calibration(self):
        """Calibrate"""
        pass

    def decode_imgs(self):
        """Run a bash script to decode images."""
        pass

    def find_depth(self, left, right):
        """
        Given disparity between sub-aperature pairs, estimate the depth.
        Output a depth map."""

        left  = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)

        # baselines between adjacent Lytro views are tiny → disparities are small &
        # sub-pixel. Keep numDisparities low and rely on SGBM's sub-pixel output.
        sgbm = cv2.StereoSGBM_create(
            minDisparity=0, numDisparities=16, blockSize=5,
            P1=8*5**2, P2=32*5**2, uniquenessRatio=10,
            speckleWindowSize=50, speckleRange=2, mode=cv2.STEREO_SGBM_MODE_HH)
        disp = sgbm.compute(left, right).astype(np.float32) / 16.0   # 1/16-px units


        # # Clean up depth map
        # # normalise, fill holes, edge-preserving smooth
        # d = disp.copy()
        # d[d <= 0] = np.nan
        # # fill small gaps
        # mask = np.isnan(d).astype(np.uint8)
        # d_filled = cv2.inpaint(np.nan_to_num(d).astype(np.float32), mask, 3, cv2.INPAINT_TELEA)
        # # edge-aware smoothing guided by the central RGB view
        # d_smooth = cv2.ximgproc.guidedFilter(center, d_filled, radius=8, eps=1e-2) \
        #         if hasattr(cv2, "ximgproc") else cv2.bilateralFilter(d_filled, 9, 50, 50)



    def run(self):

        self.decode_imgs()

        for subaperature_1, subaperature_2 in zip(self.img_list[LEFT], self.img_list[RIGHT]):
            self.find_depth(subaperature_1, subaperature_2)




def main():

    ld = LytroDepth()
    ld.calibration()
    ld.run()


if __name__=="__main__":
    main()