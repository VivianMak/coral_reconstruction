from pyntcloud import PyntCloud
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

for i in range(3,5):

    file = f"data/bun0{i}.pcd"
    print(f"Looking at: {file}")

    cloud = PyntCloud.from_file(file)
    points = cloud.points

    # print(points.head())
    
    ax.scatter(points.x, points.y, points.z, s=1)

ax.set_xlabel("X") 
ax.set_ylabel("Y") 
ax.set_zlabel("Z")
ax.set_title("Point Cloud Scatter Plot")

plt.show()


########## POINT CLOUD DATA #########
# PointCloud with 397 points.
# Has normals: True
# PointCloud with 200 points.
# Has normals: False
# PointCloud with 217 points.
# Has normals: False
# PointCloud with 197 points.
# Has normals: False
# PointCloud with 361 points.
# Has normals: False
# PointCloud with 397 points.
# Has normals: False


# import open3d as o3d

# for i in range(6):

#     # Load the PCD file
#     pcd = o3d.io.read_point_cloud(f"data/bun0{i}.pcd")

#     # Check what was loaded
#     print(pcd)
#     print("Has normals:", pcd.has_normals())

#     # Visualize
#     o3d.visualization.draw_geometries(
#         [pcd],
#         point_show_normal=True,   # <- show the surface normals
#         window_name="Stanford Bunny"
#     )
