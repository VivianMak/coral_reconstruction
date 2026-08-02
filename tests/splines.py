import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.utils import Point

CURVE_DENSITY = 15


def show_spline(points):
    """List of x y z points"""

    x_coords = []
    y_coords = []
    z_coords = []

    for p in points:
        for i in range(len(p.pos_history)):    
            x_coords.append(p.pos_history[i][0])
            y_coords.append(p.pos_history[i][1])
            z_coords.append(p.pos_history[i][2])

    print(x_coords)

    print(f"Generating B-spline of {CURVE_DENSITY} curve density")
    
    tck, u_param = interpolate.splprep([x_coords, y_coords, z_coords], k=3, s=0)

    # 3. Generate a fine grid of parameter values to evaluate the curve
    u_fine = np.linspace(0, 1, num=CURVE_DENSITY)

    # 4. Evaluate the B-spline curve at the fine parameters
    evaluated_points = interpolate.splev(u_fine, tck)
    x_fine, y_fine, z_fine = evaluated_points

    # 5. Plot the 3D results using Matplotlib
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Plot original sparse control points
    ax.scatter(x_coords, y_coords, z_coords, color='red', label='Control Points')

    # Plot the smooth interpolated B-spline curve
    ax.plot(x_fine, y_fine, z_fine, color='blue', linewidth=2, label='3D B-Spline Curve')

    # Configure labels and layout
    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_zlabel('Z Axis')
    ax.set_title('3D B-Spline Interpolation via SciPy')
    ax.legend()

    plt.show()


def main():
    x_coords = [0.0, 1.0, 2.5, 3.0, 4.5, 6.0]
    y_coords = [0.0, 2.5, 1.0, 4.0, 2.0, 5.0]
    z_coords = [0.0, 1.0, 3.0, 2.5, 4.5, 6.0]

    viewed_points: list[Point] = []

    counter = 0
    for x, y , z in zip (x_coords, y_coords, z_coords):
        p = Point(
            idx=counter, 
            x=x, 
            y=y, 
            z=z, 
            pos_history=[(x,y,z)]
        )
        counter += 1

        viewed_points.append(p)

    show_spline(viewed_points)




if __name__=="__main__":
    main()