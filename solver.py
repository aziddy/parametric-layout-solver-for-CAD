import numpy as np
from scipy.optimize import minimize, differential_evolution

def rect_circle_packing_solver(rectangles, padding_inner=0.0, padding_outer=0.0):
    """
    Solves for the minimum radius circle that contains 4 rectangles without overlap.
    
    Args:
        rectangles: List of tuples (width, height) for 4 rectangles.
        padding_inner: Minimum distance between rectangles.
        padding_outer: Minimum distance between rectangles and the circle boundary.
        
    Returns:
        result: Dictionary containing:
            'radius': Minimum radius found
            'positions': List of (x, y) center positions for each rectangle
            'success': Boolean indicating solver success
    """
    n_rects = len(rectangles)
    rects = np.array(rectangles)
    
    # Decision variables: [R, x1, y1, x2, y2, x3, y3, x4, y4]
    # R is radius, (xi, yi) are centers of rectangles
    
    # We will use Differential Evolution because the non-overlap constraint is non-convex.
    
    # Bounds
    # R: 0 to sum of max dimensions (upper bound)
    max_dim = np.sum([max(w, h) for w, h in rectangles]) + n_rects * padding_inner + padding_outer
    bounds = [(0, max_dim)] + [(-max_dim, max_dim)] * (2 * n_rects)
    
    def objective(vars):
        """Minimize Radius + Penalty for constraints."""
        R = vars[0]
        centers = vars[1:].reshape((n_rects, 2))
        
        penalty = 0
        
        # 1. Containment Constraint
        # All corners must be within R - padding_outer
        effective_R = R - padding_outer
        
        for i in range(n_rects):
            w, h = rects[i]
            x, y = centers[i]
            
            # Check all 4 corners
            corners = [
                (x + w/2, y + h/2),
                (x + w/2, y - h/2),
                (x - w/2, y + h/2),
                (x - w/2, y - h/2)
            ]
            
            for cx, cy in corners:
                dist = np.sqrt(cx**2 + cy**2)
                # If dist > effective_R, we violate the containment
                if dist > effective_R:
                    penalty += (dist - effective_R)**2 * 1000  # Strong penalty
        
        # 2. Non-overlap Constraint
        # For every pair, must be separated in X or Y by at least padding_inner
        for i in range(n_rects):
            for j in range(i + 1, n_rects):
                w1, h1 = rects[i]
                x1, y1 = centers[i]
                
                w2, h2 = rects[j]
                x2, y2 = centers[j]
                
                # Check overlap
                dx = abs(x1 - x2)
                dy = abs(y1 - y2)
                
                # Minimum required center distance including padding
                min_dx = (w1 + w2) / 2 + padding_inner
                min_dy = (h1 + h2) / 2 + padding_inner
                
                # If overlap in BOTH X and Y, we have a problem.
                x_overlap_amount = max(0, min_dx - dx)
                y_overlap_amount = max(0, min_dy - dy)
                
                if x_overlap_amount > 0 and y_overlap_amount > 0:
                    # Overlap exists
                    penalty += (x_overlap_amount * y_overlap_amount) * 10000 

        return R + penalty

    # Run Differential Evolution
    result = differential_evolution(
        objective, 
        bounds, 
        strategy='best1bin', 
        maxiter=1000, 
        popsize=15, 
        tol=0.01, 
        mutation=(0.5, 1), 
        recombination=0.7,
        seed=None
    )

    # Extract results
    best_vars = result.x
    min_radius = best_vars[0]
    positions = best_vars[1:].reshape((n_rects, 2))
    
    return {
        'radius': min_radius,
        'positions': positions.tolist(),
        'success': result.success,
        'message': result.message
    }

if __name__ == "__main__":
    # Test case
    test_rects = [(10, 10), (20, 10), (10, 20), (15, 15)]
    print(f"Testing with rects: {test_rects}")
    res = rect_circle_packing_solver(test_rects, padding_inner=1.0, padding_outer=1.0)
    print(f"Result Radius: {res['radius']:.4f}")
    for i, pos in enumerate(res['positions']):
        print(f"Rect {i}: Center {pos}")
