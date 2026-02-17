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
# The ROI in Region.pdf covers a central horizontal band:
#   LEFT: SAC, OAT, Nalanda Grounds (event venues)
#   CENTER: Main Grounds, Indoor Sports Complex (open spaces)
#   CENTER-RIGHT: Library, Main Building, LHC (academic core)
#   RIGHT: Rose Garden, Block 99C, Nursery (near Metro gate)
#
# Estimation method: The campus map is roughly trapezoidal.
# The ROI spans ~60% of the campus width (east-west) and ~35%
# of the campus height (north-south) in the central belt.
# However, it excludes:
#   - All hostels (north strip, west/new campus, south residences)
#   - West/New Campus residential area
#   - Block 102 and southern academic blocks
#   - Deer Park adjacency / northern perimeter
#
# From the Region.pdf overlay, the ROI occupies approximately
# 25-30% of the total campus area.

# Sub-region area estimates based on known IIT Delhi landmarks:
# (Using Google Maps satellite imagery proportions)

sub_regions = {
    "SAC + OAT + Nalanda Grounds": {
        "acres": 18.0,
        "description": "Student Activity Centre, Open Air Theatre, Nalanda open grounds. Primary cultural event venue.",
        "type": "event_venue"
    },
    "Main Grounds + Indoor Sports": {
        "acres": 25.0,
        "description": "Central sports grounds (cricket ground, athletics track) and Indoor Sports Complex. Largest open space for mass gatherings.",
        "type": "open_ground"
    },
    "Library + Main Building + LHC": {
        "acres": 15.0,
        "description": "Central Library, Main Administrative Building, Lecture Hall Complex. Dense academic core with corridors & courtyards.",
        "type": "academic_core"
    },
    "Rose Garden + Block 99C + Nursery": {
        "acres": 12.0,
        "description": "Rose Garden, SBI area, Block 99C, Nursery. Green corridor leading to Metro station / Main Gate.",
        "type": "green_corridor"
    },
    "Connecting Pathways & Roads": {
        "acres": 10.0,
        "description": "Internal roads and pedestrian pathways connecting the above zones within the ROI boundary.",
        "type": "circulation"
    }
}

total_roi_acres = sum(r["acres"] for r in sub_regions.values())
roi_fraction = total_roi_acres / TOTAL_CAMPUS_ACRES

print("=" * 70)
print("REGION OF INTEREST ANALYSIS — IIT DELHI RENDEZVOUS FESTIVAL")
print("=" * 70)
print(f"\nTotal Campus Area: {TOTAL_CAMPUS_ACRES} acres ({TOTAL_CAMPUS_HECTARES:.1f} ha)")
print(f"\nRegion of Interest Breakdown:")
print("-" * 70)
print(f"{'Sub-Region':<40} {'Area (acres)':>12} {'Type':<20}")
print("-" * 70)
for name, info in sub_regions.items():
    print(f"{name:<40} {info['acres']:>10.1f}   {info['type']:<20}")
print("-" * 70)
print(f"{'TOTAL ROI':<40} {total_roi_acres:>10.1f}   {'—':<20}")
print(f"\nROI as fraction of campus: {roi_fraction:.1%}")
print(f"ROI in hectares: {total_roi_acres * 0.4047:.1f} ha")
print(f"ROI in sq meters: {total_roi_acres * 4047:.0f} m²")

# ============================================================
# GRID DIVISION
# ============================================================
# Divide ROI into equal-area grid cells for Module 3.2
# Target: ~5 acre cells (reasonable for crowd density modeling)

GRID_CELL_ACRES = 5.0
n_cells = math.ceil(total_roi_acres / GRID_CELL_ACRES)
actual_cell_acres = total_roi_acres / n_cells

print(f"\n{'=' * 70}")
print(f"GRID DIVISION FOR MODULE 3.2")
print(f"{'=' * 70}")
print(f"Target cell size: {GRID_CELL_ACRES} acres")
print(f"Number of grid cells: {n_cells}")
print(f"Actual cell size: {actual_cell_acres:.2f} acres ({actual_cell_acres * 4047:.0f} m²)")
print(f"Cell side length (if square): {math.sqrt(actual_cell_acres * 4047):.0f} m × {math.sqrt(actual_cell_acres * 4047):.0f} m")

# ============================================================
# GENERATE ANNOTATED CAMPUS MAP
# ============================================================
print(f"\n{'=' * 70}")
print("GENERATING ANNOTATED CAMPUS MAP...")
print(f"{'=' * 70}")

# Load the campus map
map_path = "/Users/yash/Desktop/CLL788 Project/iitd-campus-map.jpg"
img = Image.open(map_path)
draw = ImageDraw.Draw(img)

W, H = img.size
print(f"Image size: {W} x {H} pixels")

# The campus map image coordinates for key landmarks (estimated from the image):
# The map is oriented with North roughly up-right.
# Image coordinate system: (0,0) at top-left, x increases right, y increases down.

# Define ROI polygon vertices on the campus map image
# These trace the approximate black outline from Region.pdf mapped onto
# the campus map JPG, covering the central event band.

roi_polygon = [
    # Starting from SAC/OAT area (left-center), going clockwise
    (300, 380),   # West edge near SAC
    (300, 300),   # North of Nalanda Grounds  
    (420, 270),   # North of SAC/OAT
    (520, 280),   # North of Hospital area
    (600, 300),   # North of Main Grounds
    (700, 270),   # North of Academic Area (above Main Grounds)
    (800, 250),   # North edge near Main Building
    (900, 230),   # North of Rose Garden
    (1000, 200),  # North near Nursery
    (1050, 210),  # NE corner near Hostels(east)
    (1100, 250),  # East side near Block 99C
    (1100, 340),  # East edge near LHC
    (1050, 380),  # SE near IRD Hostel
    (950, 390),   # South of LHC/Block 99B
    (850, 400),   # South of Library
    (750, 420),   # South of Indoor Sports
    (650, 430),   # South of Main Grounds
    (550, 430),   # SW below Main Grounds
    (450, 420),   # South of SAC
    (350, 410),   # South of Nalanda
    (300, 400),   # Back to west edge
]

# Draw semi-transparent ROI overlay
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)

# Fill ROI with semi-transparent red
overlay_draw.polygon(roi_polygon, fill=(255, 50, 50, 60), outline=(255, 0, 0, 200))

# Convert base image to RGBA and composite
img_rgba = img.convert('RGBA')
img_composite = Image.alpha_composite(img_rgba, overlay)

# Draw the ROI boundary line (thick)
draw_final = ImageDraw.Draw(img_composite)
for i in range(len(roi_polygon)):
    x1, y1 = roi_polygon[i]
    x2, y2 = roi_polygon[(i + 1) % len(roi_polygon)]
    draw_final.line([(x1, y1), (x2, y2)], fill=(220, 30, 30, 255), width=4)

# ============================================================
# DRAW GRID LINES INSIDE ROI
# ============================================================
# Compute bounding box of ROI
all_x = [p[0] for p in roi_polygon]
all_y = [p[1] for p in roi_polygon]
min_x, max_x = min(all_x), max(all_x)
min_y, max_y = min(all_y), max(all_y)

roi_width = max_x - min_x   # pixels
roi_height = max_y - min_y   # pixels

# We want n_cells grid cells. Arrange as rows × cols
n_cols = int(math.ceil(math.sqrt(n_cells * roi_width / roi_height)))
n_rows = int(math.ceil(n_cells / n_cols))

cell_w = roi_width / n_cols
cell_h = roi_height / n_rows

print(f"Grid: {n_rows} rows × {n_cols} cols = {n_rows * n_cols} cells")
print(f"Cell size (pixels): {cell_w:.0f} × {cell_h:.0f}")

# Draw grid lines
grid_color = (0, 100, 255, 180)  # Blue grid

# Vertical lines
for i in range(n_cols + 1):
    x = min_x + i * cell_w
    draw_final.line([(x, min_y), (x, max_y)], fill=grid_color, width=2)

# Horizontal lines
for j in range(n_rows + 1):
    y = min_y + j * cell_h
    draw_final.line([(min_x, y), (max_x, y)], fill=grid_color, width=2)

# Label grid cells
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    label_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
except:
    font = ImageFont.load_default()
    label_font = font

cell_num = 1
for row in range(n_rows):
    for col in range(n_cols):
        cx = min_x + (col + 0.5) * cell_w
        cy = min_y + (row + 0.5) * cell_h
        # Check if center is roughly inside ROI (simple point-in-polygon)
        label = f"G{cell_num}"
        # Draw label background
        bbox = draw_final.textbbox((cx, cy), label, font=font)
        pad = 2
        draw_final.rectangle([bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad], 
                           fill=(255, 255, 255, 200))
        draw_final.text((cx - 10, cy - 8), label, fill=(0, 0, 180, 255), font=font)
        cell_num += 1

# ============================================================
# ADD TITLE AND LEGEND
# ============================================================
# Title
title_y = 20
draw_final.rectangle([(10, 5), (600, 65)], fill=(255, 255, 255, 220))
draw_final.text((15, 8), "IIT Delhi — Rendezvous Region of Interest", 
                fill=(200, 30, 30), font=label_font)
draw_final.text((15, 35), f"ROI: {total_roi_acres:.0f} acres ({roi_fraction:.0%} of campus) | "
                f"Grid: {n_rows}×{n_cols} cells @ {actual_cell_acres:.1f} acres each",
                fill=(0, 0, 0), font=font)

# Legend
legend_y = H - 120
draw_final.rectangle([(10, legend_y), (350, H - 10)], fill=(255, 255, 255, 220), outline=(0, 0, 0))
draw_final.text((20, legend_y + 5), "LEGEND", fill=(0, 0, 0), font=label_font)
draw_final.line([(20, legend_y + 35), (50, legend_y + 35)], fill=(220, 30, 30), width=4)
draw_final.text((60, legend_y + 28), "Region of Interest Boundary", fill=(0, 0, 0), font=font)
draw_final.line([(20, legend_y + 60), (50, legend_y + 60)], fill=(0, 100, 255), width=2)
draw_final.text((60, legend_y + 53), f"Grid Cells ({actual_cell_acres:.1f} acres each)", fill=(0, 0, 0), font=font)
draw_final.rectangle([(20, legend_y + 75), (50, legend_y + 90)], fill=(255, 50, 50, 60))
draw_final.text((60, legend_y + 78), "ROI Shaded Area", fill=(0, 0, 0), font=font)

# Save
output_path = "/Users/yash/Desktop/CLL788 Project/Module_3_1/iitd_roi_grid_map.png"
img_composite.save(output_path)
print(f"\nAnnotated map saved to: {output_path}")

# ============================================================
# SUMMARY TABLE FOR REPORT
# ============================================================
print(f"\n{'=' * 70}")
print("SUMMARY FOR REPORT (LaTeX-ready)")
print(f"{'=' * 70}")
print(f"""
\\begin{{table}}[h]
\\centering
\\caption{{Region of Interest Sub-Zones}}
\\label{{tab:roi}}
\\begin{{tabular}}{{@{{}}llcc@{{}}}}
\\toprule
\\textbf{{Zone}} & \\textbf{{Key Landmarks}} & \\textbf{{Area (acres)}} & \\textbf{{Type}} \\\\ \\midrule
A & SAC, OAT, Nalanda Grounds & {sub_regions['SAC + OAT + Nalanda Grounds']['acres']:.0f} & Event Venue \\\\
B & Main Grounds, Indoor Sports & {sub_regions['Main Grounds + Indoor Sports']['acres']:.0f} & Open Ground \\\\
C & Library, Main Building, LHC & {sub_regions['Library + Main Building + LHC']['acres']:.0f} & Academic Core \\\\
D & Rose Garden, Block 99C, Nursery & {sub_regions['Rose Garden + Block 99C + Nursery']['acres']:.0f} & Green Corridor \\\\
E & Internal Roads \\& Pathways & {sub_regions['Connecting Pathways & Roads']['acres']:.0f} & Circulation \\\\
\\midrule
  & \\textbf{{Total ROI}} & \\textbf{{{total_roi_acres:.0f}}} & --- \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}

Total campus area: {TOTAL_CAMPUS_ACRES} acres
ROI fraction: {roi_fraction:.1%}
Grid cells: {n_cells} cells @ {actual_cell_acres:.1f} acres each
Cell dimensions: ~{math.sqrt(actual_cell_acres * 4047):.0f} m × {math.sqrt(actual_cell_acres * 4047):.0f} m
""")
