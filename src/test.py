from scipy.spatial.transform import RigidTransform as Tf
import numpy as np

# Create a RigidTransform
t = np.array([2, 3, 4])
r = Tf.random().rotation
tf = Tf.from_components(t, r)

# Get the dual quaternion with default scalar-last ordering
dual_quat_default = tf.as_dual_quat()

# Get the dual quaternion with scalar-first ordering
dual_quat_scalar_first = tf.as_dual_quat(scalar_first=True)

print("Dual Quaternion (scalar-last):", dual_quat_default)
print("Dual Quaternion (scalar-first):", dual_quat_scalar_first)

# For the identity transform, the dual quaternion is [0, 0, 0, 1, 0, 0, 0, 0]
print("Identity dual quaternion (scalar-last):", Tf.identity().as_dual_quat())
print("Identity dual quaternion (scalar-first):", Tf.identity().as_dual_quat(scalar_first=True))
