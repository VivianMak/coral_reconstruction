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



def main():

    # Files to look at
    pcd_files = [4,5]
    cloud_pts = {}

    # Saving points (x,y,z) to dictionary
    for n in pcd_files:
        file = f"data/bun0{n}.pcd"

        # Add points to dictionary as cloud objects
        cloud = o3d.io.read_point_cloud(file)
        cloud_pts[n] = cloud #.points

        print(f"Looking at: {file} has {len(cloud.points)} points.")

    source = cloud_pts[4]
    target = cloud_pts[5]

    print("---- PERFORMING ICP -------")
    new = icp(source, target)

    print("----VISUALIZING-----")
    visualize(cloud_pts, new)


def icp(source, target):
    source.paint_uniform_color([0.5, 0.5, 0.5])
    target.paint_uniform_color([0, 0, 1])

    target_points = np.asarray(target.points)

    # 1. Find nearest neighbor
    new_source_points = find_nearest_neighbors(source, target, 1)

    print(f"There are {len(new_source_points)} nearest neighbor points")
    print(f"They are of type {new_source_points.dtype}")
    print(new_source_points[4])

    # 2. Find point cloud centroids and their repositions
    target_points = np.asarray(target.points)
    source_centroid = np.mean(new_source_points, axis=0)
    target_centroid = np.mean(target_points, axis=0)
    source_repos = np.zeros_like(new_source_points)
    target_repos = np.zeros_like(target_points)
    source_repos = np.asarray([new_source_points[ind] - source_centroid for ind in range(len(new_source_points))])
    target_repos = np.asarray([target_points[ind] - target_centroid for ind in range(len(target_points))])

    # 3. Find correspondence between source and target point clouds
    cov_mat = target_repos.transpose() @ source_repos

    print("The covariance matrix is:")
    print(cov_mat)

    U, X, Vt = np.linalg.svd(cov_mat)
    R = U @ Vt
    t = target_centroid - R @ source_centroid
    t = np.reshape(t, (1,3))
    curr_cost = np.linalg.norm(target_repos - (R @ source_repos.T).T)
    print("Curr_cost=", curr_cost)

    return new_source_points

def visualize(cloud_pts, new_pts):

    visuals = []
    
    for cloud in cloud_pts.values():
        visuals.append(cloud)

    # For new points, turn into a point cloud object
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.asarray(new_pts))

    visuals.append(pcd)

    o3d.visualization.draw_geometries(visuals,
                                  window_name="PCD 4,5 with nearest neighbor new points",
                                  width=800, height=600)


if __name__ == "__main__":
    main()

