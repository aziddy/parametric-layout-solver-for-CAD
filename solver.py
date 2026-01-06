import numpy as np
from scipy.optimize import differential_evolution
import itertools
import sys

def make_progress_callback(max_iter):
    iteration = 0
    def callback(xk, convergence=None):
        nonlocal iteration
        iteration += 1
        sys.stdout.write(f"\rIteration {iteration}/{max_iter}")
        sys.stdout.flush()
    return callback

def get_corners(cx, cy, w, h, theta):
    """
    Returns the 4 corners of a rotated rectangle.
    theta is in radians.
    """
    c, s = np.cos(theta), np.sin(theta)
    
    # Half dimensions
    hw, hh = w / 2, h / 2
    
    # Local corners relative to center [(hw, hh), (-hw, hh), (-hw, -hh), (hw, -hh)]
    # Rotated: x' = x*c - y*s, y' = x*s + y*c
    
    corners = []
    # Standard order: Top-Right, Top-Left, Bottom-Left, Bottom-Right (relative to unrotated)
    # Actually order doesn't matter for SAT as long as it's sequential for edges
    for dx, dy in [(hw, hh), (-hw, hh), (-hw, -hh), (hw, -hh)]:
        rx = dx * c - dy * s
        ry = dx * s + dy * c
        corners.append((cx + rx, cy + ry))
        
    return corners

def get_axes(corners):
    """Get the normal axes for a polygon defined by corners."""
    axes = []
    for i in range(len(corners)):
        p1 = corners[i]
        p2 = corners[(i + 1) % len(corners)]
        edge = (p2[0] - p1[0], p2[1] - p1[1])
        # Normal is (-dy, dx)
        normal = (-edge[1], edge[0])
        length = np.sqrt(normal[0]**2 + normal[1]**2)
        if length > 1e-9:
             axes.append((normal[0]/length, normal[1]/length))
    return axes

def project(corners, axis):
    """Project corners onto an axis and return min/max."""
    min_proj = float('inf')
    max_proj = float('-inf')
    for x, y in corners:
        p = x * axis[0] + y * axis[1]
        if p < min_proj: min_proj = p
        if p > max_proj: max_proj = p
    return min_proj, max_proj

def get_sat_overlap(corners1, corners2, padding=0.0):
    """
    Check if two convex polygons overlap using SAT.
    Returns: approximate penalty value (squared penetration depth) if overlap, else 0.
    """
    # For rectangles, we only need axes from both.
    axes = get_axes(corners1) + get_axes(corners2)
    
    # We want to find the MINIMUM penetration.
    # If any axis has separation >= padding, then overlap is 0.
    
    min_penetration = float('inf')
    
    for axis in axes:
        min1, max1 = project(corners1, axis)
        min2, max2 = project(corners2, axis)
        
        # We need distance between intervals [min1, max1] and [min2, max2]
        # Distance = max(min2 - max1, min1 - max2)
        
        d = max(min2 - max1, min1 - max2)
        
        if d >= padding:
            # Separated by at least padding
            return 0.0
            
        # Penetration (negative distance) + padding requirement
        # We need d >= padding. 
        # Violation = padding - d.
        # Since d < padding, violation is positive.
        
        violation = padding - d
        if violation < min_penetration:
            min_penetration = violation
            
    # If we get here, constraints are violated on ALL axes.
    # Return squared penetration
    return min_penetration**2 if min_penetration != float('inf') else 0.0

def rect_circle_packing_solver(rectangles, padding_inner=0.0, padding_outer=0.0, rotation_mode='FIXED_0', target_radius=None):
    """
    Solves for the minimum radius circle that contains rectangles without overlap.
    
    Args:
        rectangles: List of tuples (width, height)
        padding_inner: Minimum distance between rectangles.
        padding_outer: Minimum distance between rectangles and the circle boundary.
        rotation_mode: 'FIXED_0', 'DISCRETE_90', 'DISCRETE_45', 'FREE'
        target_radius: Optional target radius for strict checking.
        
    Returns:
        result: Dictionary containing radius, positions, success status.
    """
    print(f"Solver running in mode: {rotation_mode}")
    
    res = {}
    if rotation_mode == 'FREE':
        res = _solve_free(rectangles, padding_inner, padding_outer, target_radius=target_radius)
    elif rotation_mode == 'FIXED_0':
        angles = [0.0] * len(rectangles)
        # Use more robustness for the first mode as requested
        res = _solve_fixed_angles(rectangles, angles, padding_inner, padding_outer, robust=True, target_radius=target_radius)
    elif rotation_mode == 'DISCRETE_90':
        res = _solve_discrete_permutations(rectangles, [0, 90], padding_inner, padding_outer, target_radius=target_radius)
    elif rotation_mode == 'DISCRETE_45':
        # 0, 45, 90, and 135 (which is -45 for a rectangle)
        res = _solve_discrete_permutations(rectangles, [0, 45, 90, 135], padding_inner, padding_outer, target_radius=target_radius)
    else:
        raise ValueError(f"Unknown rotation mode: {rotation_mode}")
    
    # Ensure new line after progress bar
    print()
    return res

def _solve_discrete_permutations(rectangles, allowed_degrees, padding_inner, padding_outer, target_radius=None):
    n = len(rectangles)
    
    # Generate all combinations of angles
    angle_options = [np.radians(d) for d in allowed_degrees]
    # Cartesian product of angles for all rects
    permutations = list(itertools.product(angle_options, repeat=n))
    
    best_result = None
    best_radius = float('inf')
    
    # print(f"DEBUG: Testing {len(permutations)} permutations for {allowed_degrees}...")
    
    for angles in permutations:
        res = _solve_fixed_angles(rectangles, angles, padding_inner, padding_outer, robust=False, target_radius=target_radius)
        if res.get('valid') and res['radius'] < best_radius:
            best_radius = res['radius']
            best_result = res
        elif best_result is None and res['success']:
             # Keep fallback if no valid found yet?
             pass
            
    if best_result is None:
        # Fallback if everything failed
        return {'radius': float('inf'), 'success': False, 'positions': [], 'message': "All permutations failed", 'valid': False}
        
    return best_result

def _solve_fixed_angles(rectangles, angles, padding_inner, padding_outer, robust=False, target_radius=None):
    n_rects = len(rectangles)
    width_heights = np.array(rectangles) 
    
    max_dim = np.sum([max(w, h) for w, h in rectangles]) * 1.5 + n_rects * padding_inner + padding_outer
    bounds = [(0, max_dim)] + [(-max_dim, max_dim)] * (2 * n_rects)
    
    def objective(vars):
        R = vars[0]
        centers = vars[1:].reshape((n_rects, 2))
        penalty = 0
        
        effective_R = R - padding_outer
        
        # Precompute corners
        all_corners = []
        for i in range(n_rects):
            w, h = width_heights[i]
            x, y = centers[i]
            theta = angles[i]
            corners = get_corners(x, y, w, h, theta)
            all_corners.append(corners)
            
            # 1. Containment (check all corners distance to origin)
            for cx, cy in corners:
                dist = np.sqrt(cx**2 + cy**2)
                if dist > effective_R:
                    penalty += (dist - effective_R)**2 * 1000

        # 2. Overlap
        for i in range(n_rects):
            for j in range(i + 1, n_rects):
                overlap = get_sat_overlap(all_corners[i], all_corners[j], padding_inner)
                if overlap > 0:
                    penalty += overlap * 10000
                    
        return R + penalty

    
    # Config based on robustness
    maxiter = 2000 if robust else 600
    popsize = 20 if robust else 10
    
    if target_radius is not None:
        # If target provided, use tol=0 to disable standard convergence
        # Use callback to stop ONLY if valid and within target
        tol = 0
    else:
        tol = 0.01

    iteration = 0
    def callback_wrapper(xk, convergence=None):
        nonlocal iteration
        iteration += 1
        sys.stdout.write(f"\rIteration {iteration}/{maxiter}")
        sys.stdout.flush()
        
        if target_radius is not None:
            # Check validity
            R = xk[0]
            if R > target_radius:
                return False # Keep going
            
            # Check physical validity (overlap)
            val = objective(xk)
            penalty = val - R
            if penalty < 1e-4:
                return True # Stop! Valid and Fits Target
                
        return False

    result = differential_evolution(
        objective, 
        bounds, 
        strategy='best1bin', 
        maxiter=maxiter, 
        popsize=popsize, 
        tol=tol, 
        seed=None,
        callback=callback_wrapper
    )

    best_vars = result.x
    R = best_vars[0]
    positions = best_vars[1:].reshape((n_rects, 2))
    
    # Calculate final penalty to determine validity
    final_penalty = objective(best_vars) - R
    is_valid = final_penalty < 1e-4
    
    final_positions = []
    for i in range(n_rects):
        final_positions.append({
            'x': positions[i][0], 
            'y': positions[i][1], 
            'rotation': float(np.degrees(angles[i]))
        })
        
    return {
        'radius': R,
        'positions': final_positions,
        'success': result.success, # DE success (converged)
        'valid': is_valid,         # Physical validity (no overlap)
        'message': result.message
    }

def _solve_free(rectangles, padding_inner, padding_outer, target_radius=None):
    n_rects = len(rectangles)
    width_heights = np.array(rectangles)
    
    max_dim = np.sum([max(w, h) for w, h in rectangles]) * 1.5 + n_rects * padding_inner
    
    # Vars: [R, x1, y1, t1, x2, y2, t2, ...]
    bounds = [(0, max_dim)]
    for _ in range(n_rects):
        bounds.append((-max_dim, max_dim)) # x
        bounds.append((-max_dim, max_dim)) # y
        bounds.append((0, np.pi))          # theta (0 to 180)
        
    def objective(vars):
        R = vars[0]
        penalty = 0
        effective_R = R - padding_outer
        
        all_corners = []
        
        for i in range(n_rects):
            base = 1 + i * 3
            x = vars[base]
            y = vars[base + 1]
            t = vars[base + 2]
            w, h = width_heights[i]
            
            corners = get_corners(x, y, w, h, t)
            all_corners.append(corners)
            
            for cx, cy in corners:
                dist = np.sqrt(cx**2 + cy**2)
                if dist > effective_R:
                    penalty += (dist - effective_R)**2 * 1000
                    
        for i in range(n_rects):
            for j in range(i + 1, n_rects):
                overlap = get_sat_overlap(all_corners[i], all_corners[j], padding_inner)
                if overlap > 0:
                    penalty += overlap * 10000
                    
        return R + penalty
    
    maxiter = 1000
    
    if target_radius is not None:
        tol = 0
    else:
        tol = 0.05
        
    iteration = 0
    def callback_wrapper(xk, convergence=None):
        nonlocal iteration
        iteration += 1
        sys.stdout.write(f"\rIteration {iteration}/{maxiter}")
        sys.stdout.flush()
        
        if target_radius is not None:
            R = xk[0]
            if R > target_radius: return False
            val = objective(xk)
            if val - R < 1e-4: return True
        return False
    
    result = differential_evolution(
        objective, 
        bounds, 
        strategy='best1bin', 
        maxiter=maxiter,
        popsize=15, 
        tol=tol,
        seed=None,
        callback=callback_wrapper
    )
    
    best_vars = result.x
    R = best_vars[0]
    
    final_penalty = objective(best_vars) - R
    is_valid = final_penalty < 1e-4
    
    final_positions = []
    
    for i in range(n_rects):
        base = 1 + i * 3
        final_positions.append({
            'x': best_vars[base],
            'y': best_vars[base+1],
            'rotation': float(np.degrees(best_vars[base+2]))
        })

    return {
        'radius': R,
        'positions': final_positions,
        'success': result.success,
        'valid': is_valid,
        'message': result.message
    }

def solve_multistage(rectangles, padding_inner=0.0, padding_outer=0.0, target_radius=None):
    """
    Runs various modes sequentially.
    Stops early if a VALID solution is found.
    Optimization robustness is higher for earlier modes.
    
    Args:
        target_radius: Optional float. If provided, early stopping only occurs if radius <= target_radius.
    """
    # Order: FIXED_0 -> DISCRETE_90 -> DISCRETE_45 -> FREE
    modes = ['FIXED_0', 'DISCRETE_90', 'DISCRETE_45', 'FREE']
    best_res = None
    best_mode = None
    
    print("Starting Multi-stage Solver...")
    
    for mode in modes:
        print(f"--- Running Mode: {mode} ---")
        try:
            res = rect_circle_packing_solver(rectangles, padding_inner, padding_outer, rotation_mode=mode, target_radius=target_radius)
            is_no_overlap = res.get('valid', False)
            print(f"  > Radius: {res['radius']:.4f}, No Overlap: {is_no_overlap}")
            
            # Check if fits target (if target is provided)
            fits_target = True
            if target_radius is not None:
                fits_target = res['radius'] <= target_radius + 1e-4

            if is_no_overlap and fits_target:
                print(f"  > VALID Solution found in {mode} (Fits Target). Stopping early.")
                return res
            elif is_no_overlap and not fits_target:
                 print(f"  > Solution Radius {res['radius']:.4f} > Target {target_radius:.4f}. Continuing search...")
            
            # Keep track of best attempt
            if best_res is None:
                best_res = res
                best_mode = mode
            else:
                # Prioritize Validity (No Overlap AND Fits Target)
                # If neither fits target, prioritize No Overlap
                # If both No Overlap, prioritize smallest radius
                
                current_fits = is_no_overlap and fits_target
                best_fits = best_res.get('valid', False) and (best_res['radius'] <= target_radius + 1e-4 if target_radius else True)
                
                if current_fits and not best_fits:
                    best_res = res
                    best_mode = mode
                elif current_fits == best_fits:
                     # Tie-breaker: Check Overlap status if strictly required (though current_fits implies overlap=False)
                     current_no_overlap = is_no_overlap
                     best_no_overlap = best_res.get('valid', False)
                     
                     if current_no_overlap and not best_no_overlap:
                         best_res = res
                         best_mode = mode
                     elif current_no_overlap == best_no_overlap:
                         if res['radius'] < best_res['radius']:
                             best_res = res
                             best_mode = mode
                
        except Exception as e:
            print(f"  > Mode {mode} failed with error: {e}")
            
    if best_res:
        print(f"=== Best (approx) Result from Mode: {best_mode}, Radius: {best_res['radius']:.4f} ===")
    else:
        print("=== All modes failed ===")
        
    return best_res

if __name__ == "__main__":
    # Test case
    # 2 rects, 20x10. 
    rects = [(20, 10), (20, 10)]
    print(f"Testing with rects: {rects}")
    
    res = solve_multistage(rects, padding_inner=1.0, padding_outer=1.0)
    
    if res:
        print(f"Final Radius: {res['radius']:.4f}")
        for i, pos in enumerate(res['positions']):
            print(f"Rect {i}: {pos}")
