import numpy as np
import matplotlib.pyplot as plt

# Voxel grid
N = 150
r = g = b = np.linspace(-1, 1, N)
R, G, B = np.meshgrid(r, g, b, indexing='ij')

# 3D cosine wave parameters
amp_y = 0.6       # amplitude in y
amp_z = 0.3       # amplitude in z
freq_y = 3        # frequency for y
freq_z = 5        # frequency for z
thickness = 0.05  # voxel thickness around the curve

# Define cosine-shaped line (parametric style)
# y = amp_y * cos(freq_y * πx)
# z = amp_z * sin(freq_z * πx)
line_mask = (np.abs(G - amp_y * np.cos(freq_y * np.pi * R)) < thickness)
line_mask &= (np.abs(B - amp_z * np.sin(freq_z * np.pi * R)) < thickness)

# Plot
fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.voxels(line_mask,
          facecolors='blue',
          edgecolor='k')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_aspect('equal')
plt.show()