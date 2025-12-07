from pyntcloud import PyntCloud
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import open3d as o3d


# Files to look at
pcd_files = [3,4]
cloud_pts = {}

# Saving points (x,y,z) to dictionary
for n in pcd_files:
    file = f"data/bun0{n}.pcd"
    print(f"Looking at: {file}")
    # Add points to dictionary
    cloud = PyntCloud.from_file(file)

    # cloud_pts[n]["x"] = cloud.points.x
    # cloud_pts[n]["y"] = cloud.points.y
    # cloud_pts[n]["z"] = cloud.points.z

    cloud_pts[n] = {
        "x": cloud.points.x.to_numpy(),
        "y": cloud.points.y.to_numpy(),
        "z": cloud.points.z.to_numpy(),
    }

print(f"Point cloud 3 has {len(cloud_pts[3]['x'])} x values")

# Plot points in the dictionary
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

for i in cloud_pts:

    x = cloud_pts[i]['x']
    y = cloud_pts[i]['y']
    z = cloud_pts[i]['z']
    
    ax.scatter(x, y, z, s=1)

ax.set_xlabel("X") 
ax.set_ylabel("Y") 
ax.set_zlabel("Z")
ax.set_title("Point Cloud Scatter Plot")

plt.show()


# print(points.head())
# print(points.dtypes)        # x,y,z



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