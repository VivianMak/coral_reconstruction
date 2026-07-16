"""Voxel grid experiments with PyntCloud + Open3D.

Converted from voxel.ipynb. Point clouds are loaded/sampled with PyntCloud,
then voxelized and displayed in a native Open3D window (same viewer used in
WarpField.py) instead of PyntCloud's notebook-only plot() backends.
"""

import numpy as np
import open3d as o3d
from pyntcloud import PyntCloud


def to_open3d_point_cloud(cloud):
    """Convert a PyntCloud's points dataframe into an Open3D PointCloud."""

    df = cloud.points
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(df[["x", "y", "z"]].to_numpy())

    if {"red", "green", "blue"}.issubset(df.columns):
        colors = df[["red", "green", "blue"]].to_numpy() / 255.0
        pcd.colors = o3d.utility.Vector3dVector(colors)

    return pcd


def voxelize_and_view(pcd, n_voxels):
    """Voxelize a point cloud and pop up a window to view the result."""

    voxel_size = pcd.get_axis_aligned_bounding_box().get_extent().max() / n_voxels
    voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=voxel_size)
    print(f"Voxel grid: {len(voxel_grid.get_voxels())} occupied voxels "
          f"(voxel_size={voxel_size:.6f})")

    o3d.visualization.draw_geometries([voxel_grid])
    return voxel_grid


def ankylosaurus_example():
    """PyntCloud library example: ankylosaurus mesh -> voxel grid."""

    anky = PyntCloud.from_file("ARCHIVED/ankylosaurus_mesh.ply")

    # Convert ply file to pcd with random samples from the surface
    anky_cloud = anky.get_sample(
        "mesh_random", n=200000, rgb=True, normals=True, as_PyntCloud=True
    )
    print(anky_cloud)

    pcd = to_open3d_point_cloud(anky_cloud)
    voxelize_and_view(pcd, n_voxels=64)


def bunny_example():
    """Bunny point cloud -> voxel grid."""

    file = "ARCHIVED/bunny_pcds/bun00.pcd"
    print(f"Looking at: {file}")

    bunny_cloud = PyntCloud.from_file(file)
    print(bunny_cloud)

    pcd = to_open3d_point_cloud(bunny_cloud)
    voxelize_and_view(pcd, n_voxels=32)


def main():
    print("np version:", np.__version__)  # downgrade to 1.26.4 if needed

    ankylosaurus_example()
    # bunny_example()


if __name__ == "__main__":
    main()
