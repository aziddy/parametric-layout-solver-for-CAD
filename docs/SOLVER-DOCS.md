# Parametric Layout Solver Documentation

This document details the inner workings of the Parametric Layout Solver used in this project. The solver is designed to pack multiple rectangular shapes into the smallest possible circular boundary, respecting defined padding and rotation constraints.

## 1. Overview

The solver uses a **Global Optimization** approach, specifically **Differential Evolution**, to find the optimal arrangement of rectangles. The problem is modeled as a minimization problem where we try to minimize the radius $R$ of the bounding circle subject to two main types of constraints:

1.  **Containment**: All rectangles must be fully inside the circle of radius $R$.
2.  **Non-Overlap**: No two rectangles can overlap each other.

To handle these geometric constraints within a continuous optimization framework, we use **Penalty Functions**. Instead of strict "hard" constraints that would instantly invalidate a potential solution, we add large "penalties" to the objective function when constraints are violated. This guides the solver towards valid regions of the search space.

## 2. Mathematical Formulation

### 2.1 Variables

The state of the system is defined by a vector of variables $\mathbf{x}$.
For $N$ rectangles, the variables depend on the rotation mode:

- **Fixed/Discrete Rotation**: $\mathbf{x} = [R, x_1, y_1, x_2, y_2, \dots, x_N, y_N]$
  - Dimension: $1 + 2N$
- **Free Rotation**: $\mathbf{x} = [R, x_1, y_1, \theta_1, x_2, y_2, \theta_2, \dots, x_N, y_N, \theta_N]$
  - Dimension: $1 + 3N$

Where:

- $R$: Radius of the bounding circle.
- $(x_i, y_i)$: Center coordinates of the $i$-th rectangle.
- $\theta_i$: Rotation angle of the $i$-th rectangle (in radians).

### 2.2 Objective Function

The solver attempts to minimize the following objective function:

$$
f(\mathbf{x}) = R + \sum P_{\text{containment}} + \sum P_{\text{overlap}}
$$

Where $P$ represents penalty terms that are zero when valid and large positive values when invalid.

### 2.3 Containment Constraint

For a rectangle to be inside the circle, all 4 of its corners must be within $(R - P_{\text{outer}})$, where $P_{\text{outer}}$ is the outer padding.

Let $C_{i,k}$ be the $k$-th corner of the $i$-th rectangle. The distance from the origin is $d_{i,k} = \|C_{i,k}\|$.
The penalty is applied if $d_{i,k} > (R - P_{\text{outer}})$:

$$
P_{\text{containment}}(i, k) =
\begin{cases}
    1000 \cdot (d_{i,k} - (R - P_{\text{outer}}))^2 & \text{if } d_{i,k} > (R - P_{\text{outer}}) \\
    0 & \text{otherwise}
\end{cases}
$$

### 2.4 Overlap Constraint (Separating Axis Theorem)

To check if two rotated rectangles overlap, we use the **Separating Axis Theorem (SAT)**.
Two convex polygons do **not** overlap if there exists an axis onto which their projections do not overlap.

For two rectangles $A$ and $B$, we check the axes formed by the normals of their edges (up to 4 axes).
Let $[min_A, max_A]$ and $[min_B, max_B]$ be the projections of the rectangles onto an axis.
The overlap distance $d$ on this axis is:

$$
d = \max(0, \min(max_A, max_B) - \max(min_A, min_B))
$$

We require a separation of at least $P_{\text{inner}}$ (inner padding).
The violation on a specific axis is:

$$
v = P_{\text{inner}} - d_{\text{separation}}
$$

If $v > 0$ on **ALL** testing axes, the rectangles are overlapping (or too close).
The penalty is based on the _minimum_ penetration depth squared:

$$
P_{\text{overlap}}(i, j) = 10000 \cdot (\min \text{penetration})^2
$$

### 2.5 Update Mechanism (Generational Steps)

The solver does not "move" shapes based on physics updates (like velocity or gradients). Instead, it evolves a population of random layouts using **Differential Evolution**.

1.  **Mutation**: For each candidate layout $\mathbf{x}_i$ in the population (target vector), a new trial vector $\mathbf{v}_i$ is created by combining three other random vectors ($\mathbf{x}_{r1}, \mathbf{x}_{r2}, \mathbf{x}_{r3}$):

    $$
    \mathbf{v}_i = \mathbf{x}_{r1} + F \cdot (\mathbf{x}_{r2} - \mathbf{x}_{r3})
    $$

    Where $F$ is a mutation factor. This "jumps" the positions ($x, y$) and angles ($\theta$) to new values based on the difference between other population members.

2.  **Crossover**: A trial vector $\mathbf{u}_i$ is formed by mixing parameters from $\mathbf{x}_i$ and $\mathbf{v}_i$.

3.  **Selection**: We compare the objective scores:
    $$
    \begin{cases}
    \mathbf{x}_{i, \text{new}} = \mathbf{u}_i & \text{if } f(\mathbf{u}_i) \le f(\mathbf{x}_i) \\
    \mathbf{x}_{i, \text{new}} = \mathbf{x}_i & \text{otherwise}
    \end{cases}
    $$

**When an iteration doesn't have a valid solution:**
If a candidate solution has overlaps or is out of bounds, the objective function returns a **high penalty value**.

- This high score makes it unlikely to beat the existing population member $\mathbf{x}_i$ (unless $\mathbf{x}_i$ is even worse).
- Therefore, the **invalid update is typically discarded**, and the solver keeps the previous "better" state for that slot in the population, trying a different random mutation in the next generation.

## 3. Algorithm Stages

The solver runs in multiple stages to balance speed and flexibility. It stops as soon as a valid solution is found that fits within the optional `target_radius`.

### Stage 1: Fixed Orientation (`FIXED_0`)

- **Constraint**: All $\theta_i = 0$.
- **Complexity**: Lowest.
- **Use case**: Best for simple layouts where rotation isn't needed.

### Stage 2: Discrete Permutations (`DISCRETE_90`)

- **Constraint**: $\theta_i \in \{0, 90^\circ\}$.
- **Method**: Brute-force checks all $2^N$ rotation combinations in parallel.
- **Complexity**: Medium.
- **Use case**: Very common for packing rectangular items efficiently.

### Stage 3: Discrete Permutations (`DISCRETE_45`)

- **Constraint**: $\theta_i \in \{0, 45^\circ, 90^\circ, 135^\circ\}$.
- **Method**: Brute-force checks all $4^N$ combinations.
- **Complexity**: High (exponential with $N$).

### Stage 4: Free Rotation (`FREE`)

- **Constraint**: $0 \le \theta_i \le 180^\circ$.
- **Method**: Single optimization run where $\theta$ is a continuous variable.
- **Complexity**: Highest. Constant dimension $1+3N$, but the search space is much more complex (many local minima).

## 4. Step-by-Step Example

Let's trace the solver with a simple input: **2 Rectangles (20x10)** and **Padding = 1.0**.

### Step 1: Initialization

- The solver reads the input and calculates `max_dim` to set bounds for the coordinate search space.
- It starts **Stage 1 (`FIXED_0`)**.

### Step 2: Optimization Loop (Stage 1)

Differential Evolution generates a population of candidate vectors.
**Candidate Vector**: `[R=15, x1=2, y1=2, x2=-2, y2=-2]`

- **Calculate Corners**:
  - Rect 1 (at 2,2): Corners approx at (12, 7), (-8, -3)...
  - Rect 2 (at -2,-2): Corners...
- **Check Overlap**:
  - Compute axes for Rect 1 (0, 1) & (1, 0) (since $\theta=0$).
  - Project Rect 1 and Rect 2.
  - If they occupy the same space (distance < padding), add huge penalty.
- **Check Bounds**:
  - Furthest corner of Rect 1 is at distance $\sqrt{12^2 + 7^2} \approx 13.89$.
  - If $R=15$ and padding is 1, effective limit is 14.
  - $13.89 \le 14$, so Containment Penalty is 0.
- **Score**: $15 + 0 \text{ (overlap)} + 0 \text{ (containment)} = 15$.

**Candidate Vector**: `[R=5, x1=0, y1=0, x2=0, y2=0]`

- **Overlap**: Massive overlap (rects on top of each other). Penalty = 1,000,000.
- **Containment**: Corners are way outside R=5. Penalty = 5,000.
- **Score**: $1,005,005$ (Very bad solution).

### Step 3: Convergence

- The solver evolves simple populations toward lower scores.
- It finds a valid solution, e.g., Rects side-by-side or stacked.
- Minimum Radius found: $\approx 15.5$ (Hypothetical).

### Step 4: Multi-stage Check

- If Stage 1 returns a valid solution and we don't need to try harder (or if it fits `target_radius`), we return it.
- Otherwise, we might try **Stage 2 (`DISCRETE_90`)**.
  - It spins up parallel tasks:
    1.  (0, 0)
    2.  (0, 90)
    3.  (90, 0)
    4.  (90, 90)
  - Each task runs the same optimization logic as above but with fixed different angles.

### Step 5: Final Output

- The solver returns the configuration from the stage that produced the **smallest valid radius**.
- Output includes `radius`, `success` flag, and list of `positions` (x, y, rotation).
