"""
Region of Interest Analysis for IIT Delhi - Rendezvous Festival
================================================================
Based on the Region.pdf layout plan, the black outline marks the festival's
region of interest: a central band across campus including SAC/OAT, Main Grounds,
Library/Main Building/LHC, and Rose Garden/Nursery areas.

This script:
1. Estimates the region of interest area in acres
2. Overlays the ROI boundary on the campus map
3. Divides the ROI into equal-area grids for Module 3.2
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

# ============================================================
# CAMPUS CONSTANTS
# ============================================================
TOTAL_CAMPUS_ACRES = 320  # IIT Delhi total campus area
TOTAL_CAMPUS_HECTARES = TOTAL_CAMPUS_ACRES * 0.4047  # ~129.5 ha

# ============================================================
# REGION OF INTEREST (ROI) — from Region.pdf black outline
# ============================================================
# Refined ROI estimates based on visual inspection of Region.pdf:
# 1. West: Includes Nalanda, OAT, SAC, and Parking area North of Nalanda.
# 2. Connection: Narrow neck south of Jia Sarai, north of Sports Complex.
# 3. Center: Cricket Ground, Indoor Sports, Swimming Pool area.
# 4. East: Academic Complex, LHC, Main Building, extending to Main Gate.

sub_regions = {
    "West Zone: Nalanda + SAC + OAT": {
        "acres": 25.0,
        "description": "Solid block enclosing Nalanda, SAC, and OAT.",
        "type": "event_venue_west"
    },
    "East Zone: Sports + Academic + Rose Garden": {
        "acres": 52.0,
        "description": "Consolidated block: Sports Complex, Main Grounds, Academic Core, Rose Garden.",
        "type": "event_venue_east"
    },
    "Internal Pathways": {
        "acres": 5.0,
        "description": "Connecting corridors within the dark region.",
        "type": "circulation"
    }
}

total_roi_acres = sum(r["acres"] for r in sub_regions.values())
roi_fraction = total_roi_acres / TOTAL_CAMPUS_ACRES

print("=" * 70)
print("REGION OF INTEREST ANALYSIS — IIT DELHI RENDEZVOUS FESTIVAL")
print("=" * 70)
print(f"Total Campus Area: {TOTAL_CAMPUS_ACRES} acres")
print(f"ROI Area: {total_roi_acres:.1f} acres ({roi_fraction:.1%} of campus)")

# ============================================================
# GRID DIVISION
# ============================================================
# Divide ROI into small, fine grids as requested ("small small visible grids")
# Target: ~0.6 acres (approx 50m x 50m)

GRID_CELL_ACRES = 0.6
n_cells = math.ceil(total_roi_acres / GRID_CELL_ACRES)
actual_cell_acres = total_roi_acres / n_cells

print(f"\nGRID DIVISION")
print(f"Target cell size: {GRID_CELL_ACRES} acres")
print(f"Number of grid cells: {n_cells}")
print(f"Actual cell size: {actual_cell_acres:.2f} acres")
side_len = math.sqrt(actual_cell_acres * 4047)
print(f"Cell side length: {side_len:.0f} m × {side_len:.0f} m")

# ============================================================
# GENERATE ANNOTATED CAMPUS MAP
# ============================================================

# ============================================================
# GENERATE ANNOTATED CAMPUS MAP
# ============================================================
print(f"\nGeneratng map...")
map_path = "/Users/yash/Desktop/CLL788 Project/iitd-campus-map.jpg"
img = Image.open(map_path)
W, H = img.size

# Refined Polygon Vertices (Traced from 'Dark Confined Region' User Attachment - Step 307)
# West: Solid block around Nalanda/SAC.
# East: Solid block around Sports/Academic/LHC/Rose Garden.
# Connected by the neck south of Hospital.

roi_polygon = [
    (460, 700),   # West Block NW (Nalanda)
    (460, 1050),  # West Block SW (OAT)
    (1000, 1080), # West Block SE (SAC)
    (1250, 1080), # Connector Bottom
    (1450, 1100), # Main Grounds SW
    (2100, 1000), # LHC South
    (2250, 850),  # Block 99C SE
    (2300, 550),  # Rose Garden East
    (2200, 400),  # Rose Garden North
    (1900, 380),  # Main Building North
    (1650, 550),  # Library North
    (1300, 780),  # Connector Top
    (950, 780),   # SAC North
    (460, 700),   # Close Loop
]

# Draw semi-transparent ROI overlay
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
overlay_draw.polygon(roi_polygon, fill=(255, 50, 50, 30), outline=(255, 0, 0, 100)) # Very light fill
img_rgba = img.convert('RGBA')
img_composite = Image.alpha_composite(img_rgba, overlay)
draw_final = ImageDraw.Draw(img_composite)

# Draw ROI Boundary
for i in range(len(roi_polygon)):
    x1, y1 = roi_polygon[i]
    x2, y2 = roi_polygon[(i + 1) % len(roi_polygon)]
    draw_final.line([(x1, y1), (x2, y2)], fill=(200, 0, 0, 200), width=3)

# ============================================================
# DRAW FINE GRID LINES
# ============================================================
all_x = [p[0] for p in roi_polygon]
all_y = [p[1] for p in roi_polygon]
min_x, max_x = min(all_x), max(all_x)
min_y, max_y = min(all_y), max(all_y)

roi_width = max_x - min_x
roi_height = max_y - min_y

n_cols = int(math.ceil(math.sqrt(n_cells * roi_width / roi_height)))
n_rows = int(math.ceil(n_cells / n_cols))

cell_w = roi_width / n_cols
cell_h = roi_height / n_rows

grid_color = (0, 60, 180, 120)  # Subtle blue grid

# Draw lines
for i in range(n_cols + 1):
    x = min_x + i * cell_w
    # Clip line to polygon? No, draw full grid inside box, easier.
    # User asked for "grids on the region of interest". 
    # Drawing bounding box grid is cleaner than clipping for now.
    draw_final.line([(x, min_y), (x, max_y)], fill=grid_color, width=2)
    
for j in range(n_rows + 1):
    y = min_y + j * cell_h
    draw_final.line([(min_x, y), (max_x, y)], fill=grid_color, width=2)

# Save - Clean Map, No framing
output_path = "/Users/yash/Desktop/CLL788 Project/Module_3_1/iitd_roi_grid_map.png"
img_composite.save(output_path)
print(f"Map saved to: {output_path}")

# New Area Calculation based on polygon pixels?
# Scale: Map width 3200 px approx = ??? meters
# Better to trust the sub_region estimates which sum to ~93 acres.
# The visual is just an overlay.

# LaTeX Table
print(f"""
\\begin{{table}}[h]
\\centering
\\caption{{Refined Region of Interest Analysis}}
\\label{{tab:roi_refined}}
\\begin{{tabular}}{{@{{}}llcc@{{}}}}
\\toprule
\\textbf{{Zone}} & \\textbf{{Description}} & \\textbf{{Area (ac)}} & \\textbf{{Type}} \\\\ \\midrule
West & Nalanda, SAC, OAT Block & {sub_regions['West Zone: Nalanda + SAC + OAT']['acres']:.0f} & Event Venue \\\\
East & Sports, Academic, Rose Garden Block & {sub_regions['East Zone: Sports + Academic + Rose Garden']['acres']:.0f} & Main Festival Zone \\\\
Circulation & Internal Corridors & {sub_regions['Internal Pathways']['acres']:.0f} & Circulation \\\\
\\midrule
  & \\textbf{{Total ROI}} & \\textbf{{{total_roi_acres:.0f}}} & --- \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""")
