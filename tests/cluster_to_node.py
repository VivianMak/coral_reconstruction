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

1. DBSCAN: not a good fit bc, it finds dense blobs separated by sparse gaps and discards sparse points as noise, 
so on a single continuous point cloud it'll either lump everything into one giant cluster or fragment based on 
local density variation, not give you evenly-spaced control points

2. Voxel downsample: radius based greedy spampling, rough uniform coverage
Overlays a 3D grid of fixed-size cubes (voxels) on the point cloud, then keeps one representative point per occupied voxel (usually the centroid of points inside it). Density-adaptive: dense regions collapse to one point per voxel, sparse regions stay sparse. O(N) — just a hash-bucket pass, no distance comparisons.

"""

import numpy as np
import matplotlib.pyplot as plt
import open3d as o3d


# 1. Configuration
k = 500  # Number of random points
np.random.seed(42)  # Ensures reproducible results
VOXEL_SIZE = 10


def voxel_downsample(points, voxel_size=VOXEL_SIZE, show=False):
    """Keep one centroid per occupied voxel of size voxel_size."""
    voxel_indices = np.floor(points / voxel_size).astype(int)

    buckets = {}
    for point, voxel_idx in zip(points, voxel_indices):
        key = tuple(voxel_idx)
        buckets.setdefault(key, []).append(point)

    nodes = np.array([np.mean(bucket, axis=0) for bucket in buckets.values()])

    print(f"Downsampled {len(points)} points -> {len(nodes)} voxel nodes (voxel_size={VOXEL_SIZE})")
    # return nodes

    if show:
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




def voxel_wireframe(voxel_grid):
    """Build a LineSet outlining every occupied voxel cube."""

    CUBE_CORNER_OFFSETS = np.array([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
        [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1],
    ])
    CUBE_EDGES = np.array([
        [0, 1], [1, 3], [3, 2], [2, 0],  # bottom face
        [4, 5], [5, 7], [7, 6], [6, 4],  # top face
        [0, 4], [1, 5], [2, 6], [3, 7],  # verticals
    ])
    
    voxel_size = voxel_grid.voxel_size
    origin = voxel_grid.origin

    all_points = []
    all_lines = []
    for voxel in voxel_grid.get_voxels():
        corner = origin + np.array(voxel.grid_index) * voxel_size
        cube_corners = corner + CUBE_CORNER_OFFSETS * voxel_size

        base = len(all_points)
        all_points.extend(cube_corners)
        all_lines.extend(CUBE_EDGES + base)

    wireframe = o3d.geometry.LineSet()
    wireframe.points = o3d.utility.Vector3dVector(np.array(all_points))
    wireframe.lines = o3d.utility.Vector2iVector(np.array(all_lines))
    wireframe.paint_uniform_color((0.0, 0.0, 0.0))

    return wireframe



def main():
    points = np.random.uniform(0, 100, size=(k, 3))

    # Separate coordinates for clean plotting syntax
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]

    voxel_downsample(points, VOXEL_SIZE)

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.paint_uniform_color([0.6, 0.6, 0.6])

    voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=VOXEL_SIZE)

    o3d.visualization.draw_geometries(
        [pcd, voxel_grid, voxel_wireframe(voxel_grid)],
        window_name=f'Voxel Grid (voxel_size={VOXEL_SIZE})',
    )


if __name__=="__main__":
    main()