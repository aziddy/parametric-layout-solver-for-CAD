import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

def plot_packing_result(rectangles, result, padding_inner=0.0, padding_outer=0.0, identifiers=None):
    """
    Plots the packing result using Matplotlib.
    
    Args:
        rectangles: List of (width, height) tuples.
        result: Dictionary returned by the solver.
        padding_inner: Inner padding used.
        padding_outer: Outer padding used.
        identifiers: Optional list of labels for the rectangles.
    """
    R = result['radius']
    positions = result['positions']
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Draw Bounding Circle
    # The solver finds R such that all corners are within R - padding_outer.
    # So the effective boundary for rectangles is R - padding_outer.
    # However, the physical container is Radius R.
    
    # Draw physical outer circle
    circle = Circle((0, 0), R, fill=False, color='blue', linestyle='--', linewidth=2, label=f'Container R={R:.2f}')
    ax.add_patch(circle)
    
    # Optional: Draw the effective containment boundary if padding_outer > 0
    if padding_outer > 0:
        eff_circle = Circle((0, 0), R - padding_outer, fill=False, color='gray', linestyle=':', alpha=0.5, label='Constraint Boundary')
        ax.add_patch(eff_circle)
    
    colors = ['#FF9999', '#99FF99', '#9999FF', '#FFCC99', '#FF99CC', '#99CCFF']
    
    for i, (w, h) in enumerate(rectangles):
        x_c, y_c = positions[i]
        # x, y for Rectangle object is bottom-left corner
        x = x_c - w/2
        y = y_c - h/2
        
        color = colors[i % len(colors)]
        label = identifiers[i] if identifiers and i < len(identifiers) else f'R{i+1}'
        
        # Draw the rectangle
        rect = Rectangle((x, y), w, h, fill=True, alpha=0.7, edgecolor='black', facecolor=color, label=label)
        ax.add_patch(rect)
        
        # Draw padding around rectangle if padding_inner > 0 (visual aid only, half-distance)
        if padding_inner > 0:
            p = padding_inner / 2
            pad_rect = Rectangle((x - p, y - p), w + 2*p, h + 2*p, fill=False, edgecolor='red', linestyle=':', alpha=0.3)
            ax.add_patch(pad_rect)

        # Label content
        ax.text(x_c, y_c, label, ha='center', va='center', fontsize=9, fontweight='bold', color='black')

    # Configure axes
    limit = R * 1.2
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_title(f"Packing Solution (R={R:.4f}mm)\nInner Pad={padding_inner}, Outer Pad={padding_outer}")
    
    plt.tight_layout()
    plt.show()
