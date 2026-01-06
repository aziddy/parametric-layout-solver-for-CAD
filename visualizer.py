import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

def plot_packing_result(rectangles, result, padding_inner=0.0, padding_outer=0.0, identifiers=None, save_path=None, show=True, target_radius=None):
    """
    Plots the packing result using Matplotlib.
    
    Args:
        rectangles: List of (width, height) tuples.
        result: Dictionary returned by the solver.
        padding_inner: Inner padding used.
        padding_outer: Outer padding used.
        identifiers: Optional list of labels.
        save_path: Optional path to save the plot (e.g. 'out.png')
        show: Whether to display the plot GUI.
        target_radius: Optional float. If provided, draws the target circle in green.
    """
    R = result['radius']
    positions = result['positions']
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Draw physical outer circle (Result)
    circle = Circle((0, 0), R, fill=False, color='blue', linestyle='--', linewidth=2, label=f'Result R={R:.2f}')
    ax.add_patch(circle)
    
    # Draw Target Circle if provided
    if target_radius is not None:
         target_c = Circle((0, 0), target_radius, fill=False, color='green', linestyle='-', linewidth=2, label=f'Target R={target_radius:.2f} (D={target_radius*2:.1f})')
         ax.add_patch(target_c)
    
    # Optional: Draw the effective containment boundary
    if padding_outer > 0:
        eff_circle = Circle((0, 0), R - padding_outer, fill=False, color='gray', linestyle=':', alpha=0.5, label='Constraint Boundary')
        ax.add_patch(eff_circle)
    
    colors = ['#FF9999', '#99FF99', '#9999FF', '#FFCC99', '#FF99CC', '#99CCFF']
    
    for i, (w, h) in enumerate(rectangles):
        pos_data = positions[i]
        if isinstance(pos_data, dict):
            x_c = pos_data['x']
            y_c = pos_data['y']
            angle_deg = pos_data.get('rotation', 0.0)
        else:
            x_c, y_c = pos_data
            angle_deg = 0.0
        
        theta = np.radians(angle_deg)
        c, s = np.cos(theta), np.sin(theta)
        
        dx_center = w / 2
        dy_center = h / 2
        
        # Original corners: (dx, dy)
        # Rotated: rx = dx*c - dy*s
        rx = dx_center * c - dy_center * s
        ry = dx_center * s + dy_center * c
        
        # Bottom-left corner for matplotlib Rectangle
        x = x_c - rx
        y = y_c - ry
        
        color = colors[i % len(colors)]
        label = identifiers[i] if identifiers and i < len(identifiers) else f'R{i+1}'
        
        rect = Rectangle((x, y), w, h, angle=angle_deg, fill=True, alpha=0.7, edgecolor='black', facecolor=color, label=label)
        ax.add_patch(rect)
        
        # Draw Center
        # ax.plot(x_c, y_c, 'k.', markersize=5)
    
    # Auto Scale
    limit = max(R * 1.2, target_radius * 1.2 if target_radius else 0)
    limit = max(limit, 50) # Minimum view
    
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')
    
    plt.title(f"Packing Result (R={R:.4f})")
    
    if save_path:
        plt.savefig(save_path)
        
    if show:
        plt.show()
    else:
        plt.close(fig)
