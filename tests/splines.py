import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate

CURVE_DENSITY = 15


def show_spline(x_coords, y_coords, z_coords):
    """List of x y z points"""

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
    x_coords = np.array([0.0, 1.0, 2.5, 3.0, 4.5, 6.0])
    y_coords = np.array([0.0, 2.5, 1.0, 4.0, 2.0, 5.0])
    z_coords = np.array([0.0, 1.0, 3.0, 2.5, 4.5, 6.0])


    show_spline(x_coords, y_coords, z_coords)




if __name__=="__main__":
    main()