import open3d as o3d


pcd1 = o3d.io.read_point_cloud("PCDDataset/coral_frame_000.pcd")
pcd2 = o3d.io.read_point_cloud("PCDDataset/coral_frame_001.pcd")


pcd1.paint_uniform_color([1.0, 0.0, 0.0])  # Red
pcd2.paint_uniform_color([0.0, 0.0, 1.0])  # Blue


o3d.visualization.draw_geometries([pcd1, pcd2], window_name="Overlayed PCD Comparison")
