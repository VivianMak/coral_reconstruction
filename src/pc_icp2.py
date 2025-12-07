from pyntcloud import PyntCloud
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import open3d as o3d


# https://github.com/casychow/Iterative-Closest-Point/blob/main/icp.py
def find_nearest_neighbors(source_pc, target_pc, nearest_neigh_num):
    # Find the closest neighbor for each anchor point through KDTree
    point_cloud_tree = o3d.geometry.KDTreeFlann(source_pc)
    # Find nearest target_point neighbor index
    points_arr = []
    for point in target_pc.points:
        [_, idx, _] = point_cloud_tree.search_knn_vector_3d(point, nearest_neigh_num)
        points_arr.append(source_pc.points[idx[0]])
    return np.asarray(points_arr)




# Files to look at
pcd_files = [3,4]
cloud_pts = {}

# Saving points (x,y,z) to dictionary
for n in pcd_files:
    file = f"data/bun0{n}.pcd"
    print(f"Looking at: {file}")

    # Add points to dictionary as cloud objects
    cloud = PyntCloud.from_file(file)
    cloud_pts[n] = cloud #.points

find_nearest_neighbors(cloud_pts[3], cloud_pts[4], 2)


