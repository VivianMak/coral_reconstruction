"""
Paths to important folders
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_RAW_DIR = os.path.join(ROOT, "data", "LFRDataset")
DATA_EXTRACTED_DIR = os.path.join(ROOT, "data", "LFRDatasetExtracted")
