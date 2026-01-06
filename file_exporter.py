import os
try:
    import ezdxf
    from ezdxf import units
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    ezdxf = None

import matplotlib.pyplot as plt
from visualizer import plot_packing_result

def export_result(rectangles, result, padding_inner, padding_outer, format_type, filename_base="output", identifiers=None):
    if format_type == "DXF":
        if ezdxf is None:
            print("Error: ezdxf library is not installed. Cannot export to DXF.")
            return False
        return _export_dxf(rectangles, result, padding_inner, padding_outer, filename_base + ".dxf", identifiers)
    elif format_type == "PNG":
        return _export_png(rectangles, result, padding_inner, padding_outer, filename_base + ".png", identifiers)
    else:
        print(f"Unknown export format: {format_type}")
        return False

def _export_dxf(rectangles, result, padding_inner, padding_outer, filename, identifiers):
    try:
        # Use R12 (AC1009) for ABSOLUTE MAXIMUM compatibility
        doc = ezdxf.new(dxfversion='R12')
        
        msp = doc.modelspace()
        
        R = result['radius']
        positions = result['positions']
        
        # Draw Outer Circle
        msp.add_circle((0, 0), R, dxfattribs={'layer': 'CONTAINER', 'color': 1}) # Red
        
        if padding_outer > 0:
             msp.add_circle((0, 0), R - padding_outer, dxfattribs={'layer': 'CONSTRAINT', 'color': 7, 'linetype': 'DASHED'})
        
        # Draw Rectangles
        for i, (w, h) in enumerate(rectangles):
            pos_data = positions[i]
            x_c = pos_data['x']
            y_c = pos_data['y']
            rotation = pos_data.get('rotation', 0.0)
            
            # Create corners
            hw, hh = w/2, h/2
            corners_local = [(hw, hh), (-hw, hh), (-hw, -hh), (hw, -hh)]
            
            # Transform to global
            corners_global = []
            import math
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            
            for lx, ly in corners_local:
                rx = lx * c - ly * s
                ry = lx * s + ly * c
                gx = x_c + rx
                gy = y_c + ry
                corners_global.append((gx, gy))
                
            # Close the loop
            corners_global.append(corners_global[0])
            
            ident = identifiers[i] if identifiers and i < len(identifiers) else f"R{i+1}"
            
            # R12 requires POLYLINE (2D), not LWPOLYLINE
            msp.add_polyline2d(corners_global, dxfattribs={'layer': 'SHAPES', 'color': 3})
            
            # Text in R12: use set_placement (works in ezdxf abstract layer)
            txt = msp.add_text(ident, dxfattribs={'layer': 'TEXT', 'height': min(w,h)/4})
            try:
                txt.set_placement((x_c, y_c), align=TextEntityAlignment.MIDDLE_CENTER)
            except:
                txt.dxf.insert = (x_c, y_c)

        doc.saveas(filename)
        print(f"Exported DXF (R12) to {filename}")
        return True
    except Exception as e:
        print(f"Failed to export DXF: {e}")
        import traceback
        traceback.print_exc()
        return False

def _export_png(rectangles, result, padding_inner, padding_outer, filename, identifiers):
    try:
        from visualizer import plot_packing_result
        plot_packing_result(rectangles, result, padding_inner, padding_outer, identifiers, save_path=filename, show=False)
        print(f"Exported PNG to {filename}")
        return True
    except Exception as e:
        print(f"Failed to export PNG: {e}")
        return False
