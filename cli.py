import argparse
import sys
from solver import rect_circle_packing_solver
from input_loader import InputLoader

def main():
    parser = argparse.ArgumentParser(description="Pack 4 rectangles into a minimal circle.")
    
    # Mutually exclusive group: either direct arguments or JSON file
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('rects', metavar='W,H', type=str, nargs='*',
                        help='Dimensions of a rectangle in format Width,Height (e.g. 10,20)')
    group.add_argument('--json', '-f', type=str, metavar='FILE',
                        help='Path to JSON input file (e.g. input/exampleInput.json)')

    args = parser.parse_args()
    
    rectangles = []
    identifiers = []
    padding_inner = 0.0
    padding_outer = 0.0
    
    if args.json:
        try:
            data = InputLoader.load_json(args.json)
            rects_data, constraints = InputLoader.extract_solver_params(data)
            
            for w, h, ident in rects_data:
                rectangles.append((w, h))
                identifiers.append(ident)
            
            padding_inner = constraints["padding_inner"]
            padding_outer = constraints["padding_outer"]
            
            print(f"Loaded from JSON: {len(rectangles)} rectangles.")
            print(f"Padding: Inner={padding_inner}, Outer={padding_outer}")
            
        except Exception as e:
            print(f"Error loading JSON: {e}")
            sys.exit(1)
            
    else:
        # CLI direct input mode
        if not args.rects:
             parser.print_help()
             sys.exit(1)
             
        try:
            for i, r_str in enumerate(args.rects):
                w, h = map(float, r_str.split(','))
                rectangles.append((w, h))
                identifiers.append(f"Rect_{i+1}")
        except ValueError:
            print("Error: Rectangles must be in format Width,Height using numbers.")
            sys.exit(1)
            
    if len(rectangles) != 4:
        print(f"Warning: Expected 4 rectangles, but got {len(rectangles)}. Solver is optimized for 4 but will try.")

    print(f"Packing Rectangles: {rectangles}")
    result = rect_circle_packing_solver(rectangles, padding_inner, padding_outer)
    
    if result['success']:
        print(f"\nOptimization Successful!")
        print(f"Minimum Circle Radius: {result['radius']:.4f}")
        print("\nPositions (Center x, y):")
        for i, pos in enumerate(result['positions']):
            ident = identifiers[i] if i < len(identifiers) else f"Rect {i+1}"
            print(f"  {ident}: ({pos[0]:.4f}, {pos[1]:.4f})")
            
        # Check output format
        output_format = "CLI"
        if args.json:
            try:
                # Reload minimal data to get metadata or stick to what we have
                data = InputLoader.load_json(args.json)
                output_format = InputLoader.extract_output_format(data)
            except:
                pass
        
        if output_format == "GUI":
            print("\nOpening result visualization window...")
            from visualizer import plot_packing_result
            plot_packing_result(rectangles, result, padding_inner, padding_outer, identifiers)
            
    else:
        print("\nOptimization Failed.")
        print(f"Message: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()