
import numpy as np

import open3d as o3d

def view():
    pcd1 = o3d.io.read_point_cloud("PCDDataset/coral_frame_000.pcd")
    pcd2 = o3d.io.read_point_cloud("PCDDataset/coral_frame_001.pcd")


    pcd1.paint_uniform_color([1.0, 0.0, 0.0])  # Red
    pcd2.paint_uniform_color([0.0, 0.0, 1.0])  # Blue

    show = [pcd1, pcd2]
    o3d.visualization.draw_geometries([pcd1], window_name="Overlayed PCD Comparison")

def view_interactive():
    # 1. Load your point cloud
    pcd = o3d.io.read_point_cloud("PCDDataset/coral_frame_000.pcd")

    # 2. Open the interactive editing window
    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window()
    vis.add_geometry(pcd)
    vis.run()  # The window will pop up. Press Shift+Left Click to select points.
    vis.destroy_window()

    # 3. Retrieve the indices of the selected points
    picked_indices = vis.get_picked_points()
    print("Selected point indices:", picked_indices)

    # 4. Extract the actual points if needed
    selected_pcd = pcd.select_by_index(picked_indices)


def draw_sphere():
    # [Open3D INFO] Picked point #22018 (-0.045, 0.006, 0.11) to add in queue.
    # [Open3D INFO] Picked point #3565 (-0.0013, -0.046, 0.096) to add in queue
    p1 = np.array([-0.045, 0.006, 0.11])
    p2 = np.array([-0.0013, -0.046, 0.096])
    picked_points = [p1, p2]

    # 2. Set up a list to hold the sphere geometries
    geometries_to_visualize = []

    # 3. Create a sphere for each point
    sphere_radius = 0.005  # Adjust this depending on your point cloud scale
    sphere_color = [1.0, 0.0, 0.0, 0.4]  # Bright red, alpha < 1.0 = translucent

    # Material with a transparency-capable shader; alpha comes from base_color
    sphere_material = o3d.visualization.rendering.MaterialRecord()
    sphere_material.shader = "defaultLitTransparency"
    sphere_material.base_color = sphere_color

    for i, pt in enumerate(picked_points):
        # Create a primitive sphere centered at [0, 0, 0]
        sphere = o3d.geometry.TriangleMesh.create_sphere(radius=sphere_radius)
        sphere.compute_vertex_normals()

        # Translate it to the picked point's coordinates
        sphere.translate(pt)

        # Add to our visualization list (name must be unique, material carries the alpha)
        geometries_to_visualize.append({
            "name": f"sphere_{i}",
            "geometry": sphere,
            "material": sphere_material,
        })

    # 4. Optional: Load and add your main point cloud if you want to see them together
    pcd = o3d.io.read_point_cloud("PCDDataset/coral_frame_000.pcd")
    geometries_to_visualize.append({"name": "pcd", "geometry": pcd})

    # 5. Visualize everything (new-style draw() is required for transparency)
    o3d.visualization.draw(geometries_to_visualize)


def main():
    draw_sphere()

if __name__=="__main__":
    main()