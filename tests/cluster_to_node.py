"""
Testing the auto selecting of deformation nodes.

Approach:
- generate a random set of points in 3d
- find clusters
- use euclidean distance to find the center of the cluster
- make the center the deformation node

- give the deformation node some transformation
- test the deformation field functions

Looking into:
- DBSCAN: not a good fit bc, it finds dense blobs separated by sparse gaps and discards sparse points as noise, 
so on a single continuous point cloud it'll either lump everything into one giant cluster or fragment based on 
local density variation, not give you evenly-spaced control points

"""


import matplotlib
import numpy as np
import matplotlib.pyplot as plt

print(matplotlib.__version__)

# 1. Configuration
k = 500  # Number of random points
np.random.seed(42)  # Ensures reproducible results

# 2. Generate k points in 3D space (X, Y, Z ranges between 0 and 100)
points = np.random.uniform(0, 100, size=(k, 3))

# Separate coordinates for clean plotting syntax
x = points[:, 0]
y = points[:, 1]
z = points[:, 2]


def voxel_downsample(points, voxel_size):
    """Keep one centroid per occupied voxel of size voxel_size."""
    voxel_indices = np.floor(points / voxel_size).astype(int)

    buckets = {}
    for point, voxel_idx in zip(points, voxel_indices):
        key = tuple(voxel_idx)
        buckets.setdefault(key, []).append(point)

    return np.array([np.mean(bucket, axis=0) for bucket in buckets.values()])


VOXEL_SIZE = 15
nodes = voxel_downsample(points, VOXEL_SIZE)
print(f"Downsampled {len(points)} points -> {len(nodes)} voxel nodes (voxel_size={VOXEL_SIZE})")

# 3. Create the 3D plot
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(projection='3d') # Modern alternative to Axes3D

# Original point cloud, small and faded so the downsampled nodes stand out
ax.scatter(x, y, z, c='gray', marker='o', s=10, alpha=0.3, label=f'Point Cloud (k={k})')

# Voxel-downsampled deformation nodes
ax.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2],
           c='red', marker='o', s=60, edgecolors='black', label=f'Voxel Nodes (n={len(nodes)})')

# Labels and styling
ax.set_title(f'Voxel Downsampling (voxel_size={VOXEL_SIZE})', pad=20, fontsize=14, fontweight='bold')
ax.set_xlabel('X Axis Space', labelpad=10)
ax.set_ylabel('Y Axis Space', labelpad=10)
ax.set_zlabel('Z Axis Space', labelpad=10)
ax.legend()

# Tight layout fixes cropped labels
plt.tight_layout()
plt.show()


