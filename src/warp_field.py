"""Warp Field"""



class WarpField:
    """Compare a point cloud to canon model to calculate warp/deformation, represent motion as a continous function."""

    def __init__(self, point_cloud):
        """
        Initalize attributes.
        
        Args:
            point_cloud: a structured point cloud representing depth
            
        """

        self.point_cloud = point_cloud

        self.neighbors = []

        self.canon_model = None

    def intialize_model(self):
        """Initalize canon voxel grid size."""

        if self.canon_model is None:
            size = len(self.point_cloud)
            

        
