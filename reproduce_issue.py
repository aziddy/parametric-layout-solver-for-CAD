from solver import solve_multistage

# Rectangles mimicking the user input
rects = [
    (38.1, 17.35),
    (53.85, 14.84),
    (42.1, 14.1),
    (39, 10.85)
]

# Case where target is impossible or very hard
# This should trigger "Solution Valid but Exceeds Target"
target_radius = 37.2
padding_inner = 1.0
padding_outer = 1.0

print(f"Target Radius: {target_radius}")
solve_multistage(rects, padding_inner=padding_inner, padding_outer=padding_outer, target_radius=target_radius)
