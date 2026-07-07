
import numpy as np
import open3d as o3d

RADIUS = 0.005

class WarpField():

    def __init__(self, pcd_files):
        
        self.pcd_files = []
        self.read_pcds(pcd_files)

        self.geometries_to_visualize = []


    def read_pcds(self, pcd_files):
        """Convert pcds into readable format"""
        for item in pcd_files:
            print(item)
            self.pcd_files.append(o3d.io.read_point_cloud(item))


    def draw_sphere(self, selected_points):
        """Draw transparent spheres to visualize deformation node."""

        # Create a sphere for each point
        sphere_radius = RADIUS  # Adjust this depending on your point cloud scale
        sphere_color = [1.0, 0.0, 0.0, 0.4]  # Bright red, alpha < 1.0 = translucent

        # Material with a transparency-capable shader; alpha comes from base_color
        sphere_material = o3d.visualization.rendering.MaterialRecord()
        sphere_material.shader = "defaultLitTransparency"
        sphere_material.base_color = sphere_color

        for i, pt in enumerate(selected_points):
            # Create a primitive sphere centered at [0, 0, 0]
            sphere = o3d.geometry.TriangleMesh.create_sphere(radius=sphere_radius)
            sphere.compute_vertex_normals()

            # Translate it to the picked point's coordinates
            sphere.translate(pt)

            # Add to our visualization list (name must be unique, material carries the alpha)
            self.geometries_to_visualize.append({
                "name": f"sphere_{i}",
                "geometry": sphere,
                "material": sphere_material,
            })

    
    def find_affected(self, sphere_centers):
        """Within sphere centers (deformation nodes) return the affected points"""

        for pcd in self.pcd_files:
            pcd_tree = o3d.geometry.KDTreeFlann(pcd)
            all_points = np.asarray(pcd.points)

            for center in sphere_centers:
                # Finds all indices inside the radius around this center
                [k, idx, _] = pcd_tree.search_radius_vector_3d(center, RADIUS)
                points_inside = all_points[idx]

                print(points_inside)




    def view(self, interactive=False):
        """
        Open window to visualize. 
        Args:
            intneractive (bool)
            
        """
        
        # Different color per pcd for vis
        # pcd1.paint_uniform_color([1.0, 0.0, 0.0]) 
        # pcd2.paint_uniform_color([0.0, 0.0, 1.0])


        if interactive:
            vis = o3d.visualization.VisualizerWithEditing()
            vis.create_window()
            for pcd in self.pcd_files:
                vis.add_geometry(pcd)
            vis.run()  # The window will pop up. Press Shift+Left Click to select points.
            vis.destroy_window()

            # Convert picked indices into actual xyz coordinates
            idx = vis.get_picked_points()
            selected_points = np.asarray(self.pcd_files[0].points)[idx]
            print("Selected point indices:", idx)

            # overwrite for now
            p1 = np.array([-0.045, 0.006, 0.11])        #22018 (-0.045, 0.006, 0.11)
            p2 = np.array([-0.0013, -0.046, 0.096])     #3565 (-0.0013, -0.046, 0.096)
            selected_points = [p1, p2]

            if len(selected_points) > 0:
                self.draw_sphere(selected_points)
                self.find_affected(selected_points)
        
        for i, pcd in enumerate(self.pcd_files):
            self.geometries_to_visualize.append({"name": f"pcd_{i}", "geometry": pcd})
        
        o3d.visualization.draw(self.geometries_to_visualize, bg_color=(1.0, 1.0, 1.0, 1.0))


    def run(self):
        self.view(interactive=True)


def main():
    pcd0 = ["PCDDataset/coral_frame_000.pcd"]
    pcd1 = ["PCDDataset/coral_frame_001.pcd"]
    files = [pcd0, pcd1]

    wf = WarpField(pcd0)
    wf.run()


if __name__=="__main__":
    main()