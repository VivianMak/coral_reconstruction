"""2D sandbox for the WarpField Gaussian deformation.

This is a small, reproducible test of the exact equations used by
``WarpField.apply_transform`` (see ../WarpField.py), but in 2D so the
behaviour is easy to eyeball.

Workflow (the terminal blocks while the window is open):
    1. A fixed grid of points is drawn (no randomness -> reproducible).
    2. Click grid points to toggle them as deformation *nodes*. Each node is
       drawn green with a translucent circle showing its RADIUS of influence.
       Points that fall inside any node's radius immediately turn red.
    3. Press Enter to apply the deformation. Affected points are pushed
       radially outward from each node with a Gaussian falloff; arrows show
       the displacement.
    4. Press 'r' to reset, Esc/'q' to quit.

The deformation, for a node center c and an affected point p:
    v = p - c ;  r = ||v|| ;  n = v / r
    p' = p + strength * exp(-r^2 / (2*sigma^2)) * n
which is identical to WarpField, just in two dimensions.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# Window spans a 1x1 area, so these are chosen to be clearly visible. They keep
# the same relationships WarpField uses by default (strength=RADIUS, sigma=RADIUS/2).
RADIUS = 0.3           # radius of influence around each node
STRENGTH = RADIUS       # peak outward push (matches WarpField default)
SIGMA = RADIUS / 2.0    # Gaussian falloff width (matches WarpField default)

# RGBA colors for the point states.
GRAY = (0.65, 0.65, 0.65, 1.0)   # untouched grid point
RED = (0.90, 0.10, 0.10, 1.0)    # affected (within a node's radius)
GREEN = (0.10, 0.70, 0.20, 1.0)  # selected deformation node


def find_affected(points, center, radius):
    """Indices of points within ``radius`` of ``center``, plus their distances.

    2D analog of ``WarpField.find_affected`` (which queries an Open3D KD-tree
    in 3D). Brute force is plenty here since the grid is tiny.
    """
    v = points - center
    r = np.linalg.norm(v, axis=1)
    idx = np.nonzero(r <= radius)[0]
    return idx, r[idx]


def apply_transform(points, centers, strength=STRENGTH, sigma=SIGMA, radius=RADIUS):
    """Push affected points radially outward from each node (Gaussian falloff).

    Same math as ``WarpField.apply_transform`` in 2D. Displacement is computed
    from the canonical ``points`` and accumulated, so overlapping nodes stack.

    Returns:
        (deformed, affected) where ``deformed`` is the new (N, 2) positions and
        ``affected`` is a boolean mask of which points moved.
    """
    rest = np.asarray(points, dtype=float)   # canonical positions (unchanged)
    deformed = rest.copy()                   # accumulated deformed positions
    affected = np.zeros(len(rest), dtype=bool)

    for node_i, center in enumerate(centers):
        center = np.asarray(center, dtype=float)
        idx, r = find_affected(rest, center, radius)
        print(f"[apply_transform] node={node_i} center=({center[0]:.3f}, {center[1]:.3f}): "
              f"{idx.size} points within RADIUS={radius}")
        if idx.size == 0:
            continue

        # Outward direction from the center to each affected point.
        v = rest[idx] - center
        safe = r > 1e-9                      # a point on the center has no direction
        n_hat = np.zeros_like(v)
        n_hat[safe] = v[safe] / r[safe, None]

        # Gaussian falloff on the distance to the node.
        w = np.exp(-r**2 / (2 * sigma**2))

        displacement = strength * w[:, None] * n_hat
        deformed[idx] += displacement

        disp_mag = np.linalg.norm(displacement, axis=1)
        print(f"    displacement magnitude: min={disp_mag.min():.4f} "
              f"max={disp_mag.max():.4f} mean={disp_mag.mean():.4f}")
        affected[idx] = True

    total_moved = np.linalg.norm(deformed - rest, axis=1)
    print(f"[apply_transform] {affected.sum()} unique points affected (of {len(rest)}), "
          f"max total displacement={total_moved.max():.4f}")
    return deformed, affected


class Warp2DTest:
    """Interactive 2D grid for picking nodes and previewing the deformation."""

    def __init__(self, grid_n=21, extent=(0.0, 1.0),
                 radius=RADIUS, strength=STRENGTH, sigma=SIGMA):
        self.radius = radius
        self.strength = strength
        self.sigma = sigma

        # Reproducible grid of points (no randomness).
        lo, hi = extent
        xs = np.linspace(lo, hi, grid_n)
        ys = np.linspace(lo, hi, grid_n)
        gx, gy = np.meshgrid(xs, ys)
        self.points = np.column_stack([gx.ravel(), gy.ravel()])

        # State reset on every (re)build.
        self.node_idx = []       # indices into self.points that are nodes
        self.circles = {}        # node index -> Circle patch
        self.transformed = False

        margin = 0.5 * self.radius + 0.05
        self.fig, self.ax = plt.subplots(figsize=(7.5, 7.5))
        self.ax.set_xlim(lo - margin, hi + margin)
        self.ax.set_ylim(lo - margin, hi + margin)
        self.ax.set_aspect("equal")

        # Grid point scatter — colors/sizes are mutated in place as nodes change.
        self.scatter = self.ax.scatter(
            self.points[:, 0], self.points[:, 1],
            s=25, facecolor=[GRAY] * len(self.points), edgecolor="none", zorder=2,
        )

        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

        self._set_pick_title()

    # ---- drawing helpers -------------------------------------------------

    def _set_pick_title(self):
        self.ax.set_title(
            "Click grid points to toggle deformation nodes (green).  "
            "Affected points turn red.\n"
            "Enter = deform    r = reset    Esc = quit",
            fontsize=10,
        )

    def refresh_affected(self):
        """Recolor points: gray, red if inside any node's radius, green if a node."""
        affected = np.zeros(len(self.points), dtype=bool)
        for i in self.node_idx:
            idx, _ = find_affected(self.points, self.points[i], self.radius)
            affected[idx] = True

        colors = np.array([GRAY] * len(self.points), dtype=float)
        sizes = np.full(len(self.points), 25.0)
        colors[affected] = RED
        if self.node_idx:
            colors[self.node_idx] = GREEN   # nodes override affected coloring
            sizes[self.node_idx] = 90.0

        self.scatter.set_facecolors(colors)
        self.scatter.set_sizes(sizes)
        self.fig.canvas.draw_idle()

    def toggle_node(self, i):
        """Add or remove grid point ``i`` as a deformation node."""
        if i in self.node_idx:
            self.node_idx.remove(i)
            self.circles.pop(i).remove()
            print(f"[node] removed grid point {i} -> {len(self.node_idx)} node(s)")
        else:
            self.node_idx.append(i)
            x, y = self.points[i]
            circle = Circle((x, y), self.radius, facecolor=(0.10, 0.70, 0.20, 0.12),
                            edgecolor=(0.10, 0.55, 0.20, 0.9), lw=1.5, zorder=1)
            self.ax.add_patch(circle)
            self.circles[i] = circle
            print(f"[node] added grid point {i} at ({x:.3f}, {y:.3f}) "
                  f"-> {len(self.node_idx)} node(s)")
        self.refresh_affected()

    # ---- event handlers --------------------------------------------------

    def on_click(self, event):
        if self.transformed:
            return                                  # locked until reset
        if event.inaxes != self.ax or event.button != 1:
            return
        toolbar = self.fig.canvas.toolbar
        if toolbar is not None and getattr(toolbar, "mode", ""):
            return                                  # ignore clicks while panning/zooming

        d = np.linalg.norm(self.points - np.array([event.xdata, event.ydata]), axis=1)
        self.toggle_node(int(np.argmin(d)))

    def on_key(self, event):
        if event.key == "enter":
            self.do_transform()
        elif event.key == "r":
            self.reset()
        elif event.key in ("escape", "q"):
            plt.close(self.fig)

    # ---- actions ---------------------------------------------------------

    def do_transform(self):
        if not self.node_idx:
            print("No deformation nodes selected — click grid points, then press Enter.")
            return
        if self.transformed:
            return

        centers = self.points[self.node_idx]
        deformed, affected = apply_transform(
            self.points, centers, self.strength, self.sigma, self.radius)

        # Show where affected points came from and the displacement they took.
        orig = self.points[affected]
        delta = deformed[affected] - orig
        self.ax.scatter(orig[:, 0], orig[:, 1], s=20, facecolor="none",
                        edgecolor=(0.5, 0.5, 0.5, 0.6), zorder=1)
        self.ax.quiver(orig[:, 0], orig[:, 1], delta[:, 0], delta[:, 1],
                       angles="xy", scale_units="xy", scale=1,
                       color=(0, 0, 0, 0.45), width=0.003, zorder=3)

        # Move the points to their deformed positions (nodes stay put, r=0).
        self.scatter.set_offsets(deformed)
        self.transformed = True
        self.ax.set_title(
            "Transformed — red = affected, arrows = displacement.\n"
            "r = reset    Esc = quit",
            fontsize=10,
        )
        self.fig.canvas.draw_idle()

    def reset(self):
        """Clear nodes and the deformation, back to the untouched grid."""
        self.ax.cla()

        lo_x, hi_x = self.points[:, 0].min(), self.points[:, 0].max()
        lo_y, hi_y = self.points[:, 1].min(), self.points[:, 1].max()
        margin = 0.5 * self.radius + 0.05
        self.ax.set_xlim(lo_x - margin, hi_x + margin)
        self.ax.set_ylim(lo_y - margin, hi_y + margin)
        self.ax.set_aspect("equal")

        self.node_idx = []
        self.circles = {}
        self.transformed = False
        self.scatter = self.ax.scatter(
            self.points[:, 0], self.points[:, 1],
            s=25, facecolor=[GRAY] * len(self.points), edgecolor="none", zorder=2,
        )
        self._set_pick_title()
        self.fig.canvas.draw_idle()
        print("[reset] cleared all nodes")

    def run(self):
        print(__doc__)
        print(f"Grid: {len(self.points)} points | RADIUS={self.radius} "
              f"STRENGTH={self.strength} SIGMA={self.sigma}\n")
        plt.show()


def main():
    Warp2DTest().run()


if __name__ == "__main__":
    main()
