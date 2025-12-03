from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    z: float

@dataclass
class DeformationNode:
    pose: Pose              # Location in 3D
    transform: np.ndarray   # Local transform as dual quaternion 4x
    radius: float           # Influence weight/radius