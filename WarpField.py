
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

    
    def find_affected(self, pcd_tree, center):
        """Return indices and Euclidean distances of points within RADIUS of a center."""

        # search_radius_vector_3d takes a real radius and returns SQUARED distances
        [k, idx, dist2] = pcd_tree.search_radius_vector_3d(center, RADIUS)
        idx = np.asarray(idx, dtype=int)
        dists = np.sqrt(np.asarray(dist2))
        return idx, dists

    def apply_transform(self, sphere_centers, strength=RADIUS, sigma=RADIUS / 2.0):
        """Push affected points radially outward from each deformation node.

        For a node center c and an affected point p:
            v = p - c ;  r = ||v|| ;  n = v / r
            p' = p + strength * w(r) * n
        where w is a Gaussian falloff w(r) = exp(-r^2 / (2*sigma^2)), so the
        bulge is strongest at the node and fades with distance from it.
        """

        sphere_centers = np.asarray(sphere_centers)

        for pcd in self.pcd_files:
            rest = np.asarray(pcd.points).copy()   # canonical positions (unchanged)
            points = rest.copy()                   # deformed positions (accumulated)
            pcd_tree = o3d.geometry.KDTreeFlann(pcd)

            for center in sphere_centers:
                idx, r = self.find_affected(pcd_tree, center)
                if idx.size == 0:
                    continue

                # Outward direction from the center to each affected point
                v = rest[idx] - center
                safe = r > 1e-9                    # a point on the center has no direction
                n_hat = np.zeros_like(v)
                n_hat[safe] = v[safe] / r[safe, None]

                # Gaussian falloff on the distance to the node
                w = np.exp(-r**2 / (2 * sigma**2))

                points[idx] += strength * w[:, None] * n_hat

            pcd.points = o3d.utility.Vector3dVector(points)




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
                self.apply_transform(selected_points)
        
        for i, pcd in enumerate(self.pcd_files):
            self.geometries_to_visualize.append({"name": f"pcd_{i}", "geometry": pcd})
        
        o3d.visualization.draw(self.geometries_to_visualize, bg_color=(1.0, 1.0, 1.0, 1.0))


    def run(self):
        self.view(interactive=True)


def main():
    pcd0 = "PCDDataset/coral_frame_000.pcd"
    pcd1 = "PCDDataset/coral_frame_001.pcd"
    files = [pcd0]

    wf = WarpField(files)
    wf.run()


if __name__=="__main__":
    main()