import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle, Circle
import numpy as np
from solver import rect_circle_packing_solver

class PackingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("4-Rectangle Circle Packer")
        self.geometry("900x600")
        
        # Left Frame for Inputs
        input_frame = ttk.Frame(self, padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(input_frame, text="Rectangle Dimensions (mm)", font=("Arial", 14)).pack(pady=10)
        
        self.entries = []
        for i in range(4):
            frame = ttk.Frame(input_frame)
            frame.pack(pady=5, fill=tk.X)
            ttk.Label(frame, text=f"Rect {i+1}:").pack(side=tk.LEFT)
            
            w_entry = ttk.Entry(frame, width=8)
            w_entry.pack(side=tk.LEFT, padx=5)
            w_entry.insert(0, "10")
            
            ttk.Label(frame, text="x").pack(side=tk.LEFT)
            
            h_entry = ttk.Entry(frame, width=8)
            h_entry.pack(side=tk.LEFT, padx=5)
            h_entry.insert(0, "10")
            
            self.entries.append((w_entry, h_entry))
            
        solve_btn = ttk.Button(input_frame, text="Solve Packing", command=self.solve)
        solve_btn.pack(pady=20, fill=tk.X)
        
        self.result_label = ttk.Label(input_frame, text="Status: Ready", wraplength=200)
        self.result_label.pack(pady=10)
        
        # Right Frame for Visualization
        viz_frame = ttk.Frame(self)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def solve(self):
        rects = []
        try:
            for w_ent, h_ent in self.entries:
                w = float(w_ent.get())
                h = float(h_ent.get())
                if w <= 0 or h <= 0:
                    raise ValueError
                rects.append((w, h))
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid positive numbers for all dimensions.")
            return
            
        self.result_label.config(text="Solving... Please wait.")
        self.update()
        
        # Run Solver
        res = rect_circle_packing_solver(rects)
        
        if res['success']:
            self.result_label.config(text=f"Solved!\nMin Radius: {res['radius']:.3f} mm")
            self.plot_result(rects, res)
        else:
            self.result_label.config(text=f"Failed: {res.get('message', 'Unknown')}")
            
    def plot_result(self, rects, res):
        self.ax.clear()
        
        R = res['radius']
        positions = res['positions']
        
        # Draw Circle
        circle = Circle((0, 0), R, fill=False, color='blue', linestyle='--', label='Bounding Circle')
        self.ax.add_patch(circle)
        
        # Draw Rectangles
        colors = ['red', 'green', 'orange', 'purple']
        for i, (w, h) in enumerate(rects):
            x_c, y_c = positions[i]
            # Convert center to bottom-left for Rectangle patch
            x = x_c - w/2
            y = y_c - h/2
            
            rect = Rectangle((x, y), w, h, fill=True, alpha=0.5, edgecolor='black', facecolor=colors[i], label=f'R{i+1}')
            self.ax.add_patch(rect)
            self.ax.text(x_c, y_c, f"{i+1}", ha='center', va='center', color='white', fontweight='bold')
            
        # Set limits
        limit = R * 1.2
        self.ax.set_xlim(-limit, limit)
        self.ax.set_ylim(-limit, limit)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.legend(loc='upper right', fontsize='small')
        self.ax.set_title(f"Minimal Radius: {R:.2f}")
        
        self.canvas.draw()

if __name__ == "__main__":
    app = PackingApp()
    app.mainloop()
