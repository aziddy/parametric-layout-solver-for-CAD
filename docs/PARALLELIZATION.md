# Solver Parallelization Strategy

This document outlines the high-level strategy used to parallelize the `DISCRETE` rotation modes in the parametric layout solver.

## The Problem

When running in `DISCRETE_90` or `DISCRETE_45` modes, the solver must evaluate a specific set of rotation permutations for all rectangles.

- **DISCRETE_90**: Each rectangle can be 0° or 90° ($2^N$ permutations).
- **DISCRETE_45**: Each rectangle can be 0°, 45°, 90°, or 135° ($4^N$ permutations).

Previously, these permutations were evaluated sequentially. For a layout with 4 rectangles, `DISCRETE_90` checks 16 permutations. If each optimization takes ~0.5s, the total time is ~8s. For larger inputs, this scales exponentially.

## The Solution

Since each permutation (a specific set of fixed angles for all rectangles) is completely independent of the others, this is an "embarrassingly parallel" problem. We utilize Python's `concurrent.futures.ProcessPoolExecutor` to distribute these permutations across all available CPU cores.

### Architecture

1.  **Main Process**:

    - Generates all possible angle permutations (Cartesian product).
    - Submits a task for each permutation to the process pool.
    - Monitors completion and updates a unified progress bar (e.g., "Permutations Checked: 5/16").
    - Aggregates results to find the global minimum radius.

2.  **Worker Processes**:
    - Each worker receives a single permutation (e.g., `[0, 90, 0, 90]`).
    - It runs the standard `differential_evolution` optimization for that specific configuration.
    - **Silent Mode**: Workers run with `silent=True` to prevent their internal progress bars from spamming the main console's `stdout`.

### Key Implementation Details

- **`_solve_single_permutation` Wrapper**:
  - Because `multiprocessing` requires picklable objects, we created a top-level wrapper function `_solve_single_permutation` that takes a tuple of arguments. This ensures the function can be correctly serialized and sent to worker processes.
- **Process Pool Management**:
  - We use `ProcessPoolExecutor` which manages a pool of workers (defaults to the number of CPU cores).
  - `as_completed` is used to process results as soon as they finish, allowing for real-time progress updates.

## Benefits

- **Linear Speedup**: The speedup is roughly linear with the number of CPU cores (until the number of permutations < number of cores).
- **Responsiveness**: The user sees progress immediately rather than waiting for long sequential blocks.
