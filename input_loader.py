import json
import os

class InputLoader:
    @staticmethod
    def load_json(filepath):
        """
        Loads and validates the JSON input file.
        
        Args:
            filepath: Path to the JSON file.
            
        Returns:
            data: Parsed and validated dictionary.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
            
        InputLoader._validate(data)
        return data

    @staticmethod
    def _validate(data):
        """Validates the structure of the input data."""
        # 1. Validate Inner Shapes
        if "innerShape" not in data:
            raise ValueError("Missing required field: 'innerShape'")
        
        if not isinstance(data["innerShape"], list):
            raise ValueError("'innerShape' must be a list")
            
        for idx, item in enumerate(data["innerShape"]):
            if "shape" not in item or item["shape"] != "rectangle":
                raise ValueError(f"Item {idx} in 'innerShape' must be a shape of type 'rectangle'")
            if "width" not in item or "height" not in item:
                raise ValueError(f"Item {idx} missing 'width' or 'height'")
            if not isinstance(item["width"], (int, float)) or not isinstance(item["height"], (int, float)):
                 raise ValueError(f"Dimensions for item {idx} must be numbers")
                 
        # 2. Validate Outer Shape
        if "outerShape" in data:
            outer = data["outerShape"]
            if "shape" in outer and outer["shape"] != "circle":
                 raise ValueError("Only 'circle' outerShape is currently supported")
            
            # Check dimensions if present
            if "radius" not in outer and "diameter" not in outer:
                pass # Optional info
            elif "radius" in outer and "diameter" in outer:
                raise ValueError("Cannot specify both 'radius' and 'diameter' in outerShape")
            
        # 3. Validate Constraints (Optional)
        if "additionalConstraints" in data:
            constraints = data["additionalConstraints"]
            # Check known keys if strict, or just let them pass.
            # We look for padding.
            pass

    @staticmethod
    def extract_solver_params(data):
        """
        Extracts parameters formatted for the solver.
        
        Returns:
            rectangles: List of (width, height, identifier) tuples
            constraints: Dictionary of solver constraints (paddings)
        """
        rectangles = []
        for item in data["innerShape"]:
            rect = (
                item["width"],
                item["height"],
                item.get("identifier", f"Rect_{len(rectangles)+1}")
            )
            rectangles.append(rect)
            
        constraints = {
            "padding_inner": 0.0,
            "padding_outer": 0.0
        }
        
        if "additionalConstraints" in data:
            ac = data["additionalConstraints"]
            if "paddingBetweenInnerShapes" in ac:
                constraints["padding_inner"] = float(ac["paddingBetweenInnerShapes"].get("amount", 0))
            if "paddingBetweenInnerShapesAndOuter" in ac:
                constraints["padding_outer"] = float(ac["paddingBetweenInnerShapesAndOuter"].get("amount", 0))
                
        return rectangles, constraints

    @staticmethod
    def extract_output_format(data):
        """
        Extracts the preferred output format.
        Returns 'CLI' (default) or 'GUI'.
        """
        if "resultOutput" in data:
            return data["resultOutput"].get("outputFormat", "CLI")
        return "CLI"
