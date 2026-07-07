"""
Workflow:

LFR/XRAW file ──▶ [decode + 4D align] ──▶ sub-aperture image grid ──▶ [depth est.] ──▶ depth map
   (camera)         PlenoptiCam              NxN viewpoint array       you write this    (float, metres-ish)
                    + calibration
"""

import cv2
import numpy as np

from PlenopticamLFR import PlenopticamLFR       # to decode LFRs
from PlenoptisignLFR import PlenoptisignLFR     # to calculate metric depth

class LytroDepth:

    def __init__(self):

        self.pc = PlenopticamLFR()
        self.ps = PlenoptisignLFR()
        
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

    def get_depth_params(self):
        """Get depth parameters from the Lytro metadata."""
        pass

    def find_depth(self, left, right):
        """
        Given disparity between sub-aperature pairs, estimate the depth.
        Output a depth map."""

        pass


    def run(self):

        self.decode_imgs()



def main():

    ld = LytroDepth()
    ld.calibration()
    ld.run()


if __name__=="__main__":
    main()