## SHOWING PFM FILES -----------------------------
import re
import numpy as np
import matplotlib.pyplot as plt

def read_pfm(file_path):
    with open(file_path, 'rb') as f:
        # 1. Read header
        header = f.readline().decode('latin-1').rstrip()
        if header == 'PF':
            channels = 3 # Color
        elif header == 'Pf':
            channels = 1 # Grayscale
        else:
            raise Exception('Not a valid PFM file.')
        
        # 2. Read dimensions
        dimensions = f.readline().decode('latin-1').rstrip()
        width, height = map(int, dimensions.split())
        
        # 3. Read scale and endianness
        scale = float(f.readline().decode('latin-1').rstrip())
        if scale < 0: # Little endian
            endian = '<'
            scale = -scale
        else: # Big endian
            endian = '>'
            
        # 4. Read raw binary data
        data = np.fromfile(f, endian + 'f')
        
        # 5. Reshape to image dimensions and handle PFM bottom-up storage
        shape = (height, width, channels) if channels == 3 else (height, width)
        data = np.reshape(data, shape)
        data = np.flipud(data) # PFM stores images from bottom to top
        
        return data, scale

# Show the image
img, scale = read_pfm("LFRDatasetExtracted/Bee_1/depth.pfm")
row, col = 100, 200
pixel_value = img[row, col]

print(f"Value at pixel ({row}, {col}): {pixel_value}")
plt.imshow(img, cmap='gray')
plt.plot(col, row, 'r+', markersize=12, markeredgewidth=2)
plt.annotate(
    f"({col}, {row})\n{pixel_value:.3f}",
    xy=(col, row),
    xytext=(col + 15, row - 15),
    color='red',
    fontsize=9,
    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor='red'),
)
plt.axis('off')
plt.show()

## SHOWING PLY FILES -----------------------------

import open3d as o3d
ply_data = o3d.io.read_point_cloud("LFRDatasetExtracted/Bee_1/depth.ply")
o3d.visualization.draw_geometries([ply_data])

