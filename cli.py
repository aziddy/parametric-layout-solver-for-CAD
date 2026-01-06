import argparse
import sys
from solver import solve_multistage
from input_loader import InputLoader

def main():
    parser = argparse.ArgumentParser(description="Pack rectangles into a minimal circle with rotation support.")
    
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
    
    # Context specific defaults
    show_output = False
    output_format = None
    target_radius = None
    
    if args.json:
        try:
            data = InputLoader.load_json(args.json)
            rects_data, constraints = InputLoader.extract_solver_params(data)
            
            for w, h, ident in rects_data:
                rectangles.append((w, h))
                identifiers.append(ident)
            
            padding_inner = constraints["padding_inner"]
            padding_outer = constraints["padding_outer"]
            
            # Extract config
            config = InputLoader.extract_output_config(data)
            show_output = config["show_output"]
            output_format = config["output_format"]
            
            # Extract target radius
            target_radius = InputLoader.extract_target_radius(data)
            
            print(f"Loaded from JSON: {len(rectangles)} rectangles.")
            
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
            
        # Defaults for CLI mode
        show_output = False 
        output_format = None
        target_radius = None
            
    if len(rectangles) != 4:
        print(f"Warning: Expected 4 rectangles, but got {len(rectangles)}. Solver will proceed.")
 
    print(f"Packing {len(rectangles)} Rectangles: {rectangles}")
    
    # Call the multistage solver
    result = solve_multistage(rectangles, padding_inner, padding_outer, target_radius=target_radius)
    
    if result and result.get('valid', False):
        # Strict Validation against Target
        fits_target = True
        if target_radius is not None and result['radius'] > target_radius + 1e-4:
            fits_target = False
            
        if fits_target:
            print(f"\nOptimization Successful!")
        else:
             print(f"\nOptimization Failed: Result exceeds Target Radius.")
             
        print(f"Minimum Circle Radius: {result['radius']:.4f}")
        print("\nPositions:")
        for i, pos_data in enumerate(result['positions']):
            ident = identifiers[i] if i < len(identifiers) else f"Rect {i+1}"
            x = pos_data['x']
            y = pos_data['y']
            rot = pos_data.get('rotation', 0.0)
            print(f"  {ident}: Center({x:.4f}, {y:.4f}), Rotation: {rot:.2f}°")
            
        # Validation
        if target_radius is not None:
            print("\n--- Validation ---")
            print(f"Target Radius: {target_radius:.4f} (Diameter: {target_radius*2:.4f})")
            print(f"Result Radius: {result['radius']:.4f} (Diameter: {result['radius']*2:.4f})")
            
            # Check fit
            # Solver returns R which includes the padding offset (constraints are valid if Rects are within R - padding_outer)
            # So we just compare Result R vs Target R
            if result['radius'] <= target_radius + 1e-4: # Tolerance
                print("STATUS: FITS")
            else:
                diff = result['radius'] - target_radius
                print(f"STATUS: DOES NOT FIT (Exceeds by Radius: {diff:.4f}, Diameter: {diff*2:.4f})")
                print(f"NOTE: Inner shapes need to fit within Diameter {target_radius*2 - padding_outer*2:.4f} (Target - 2*Padding)")

            
        # Handle Output
        if output_format:
            print(f"Exporting result as {output_format}...")
            try:
                from file_exporter import export_result
                filename = "output" 
                # If json input, maybe use that base name? sticking to 'output' for now as simpler
                export_result(rectangles, result, padding_inner, padding_outer, output_format, filename, identifiers)
            except ImportError:
                 print("Error importing file_exporter. Check dependencies.")
            except Exception as e:
                print(f"Export error: {e}")
                
        if show_output:
            print("\nOpening result visualization window...")
            try:
                from visualizer import plot_packing_result
                plot_packing_result(rectangles, result, padding_inner, padding_outer, identifiers, target_radius=target_radius)
            except ImportError:
                print("Visualization module not available or failed to import.")
            except Exception as e:
                print(f"Visualization error: {e}")
            
    else:
        print("\nOptimization Failed or no valid solution found.")
        if result:
            print(f"Message: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()