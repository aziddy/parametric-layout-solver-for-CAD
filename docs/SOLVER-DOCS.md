# Solver Documentation

## Overview

The Parametric Layout Solver uses a differential evolution algorithm to minimize the radius of a bounding circle containing a set of rectangular inner shapes.

## Rotation Support

The solver supports four modes of operation regarding rotation:

1.  **No Rotation (0°)**: Standard axis-aligned packing.
2.  **Discrete 90°**: Tries 0° and 90° orientations.
3.  **Discrete 45°**: Tries 0°, 45°, and 90° orientations.
4.  **Free Rotation**: Allows any angle [0, 180].

### Implementation Details

To support rotation, collision detection is performed using the **Separating Axis Theorem (SAT)**.

- **Constraints**: Constraints like "non-overlap" are modeled as penalty functions added to the objective.
- **SAT**: Two convex polygons do not overlap if and only if there exists a line (axis) onto which their projections do not overlap. For rectangles, we check the axes parallel to their edges.

### Performance Considerations & Limitations

> [!WARNING] > **Complexity Scaling in Discrete Modes**
> The "Discrete 90°" and "Discrete 45°" modes currently use a **brute-force permutation strategy**.
>
> - For $N$ shapes in 90° mode, the solver runs $2^N$ times.
> - For $N$ shapes in 45° mode, the solver runs $3^N$ times.
>
> This is efficient for small $N$ (e.g., $N \le 6$). However, this complexity scales exponentially:
>
> - $N=10$ (90° mode) = 1024 runs.
> - $N=10$ (45° mode) = 59,049 runs.
>
> **Recommendation**: If $N$ grows larger than ~8, the discrete modes should be replaced or augmented with a probabilistic approach (e.g., treating discrete angles as integer decision variables or using a genetic algorithm that includes orientation as a gene), rather than iterating all permutations.
