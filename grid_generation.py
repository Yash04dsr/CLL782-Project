"""
Geospatial Grid Generation for IIT Delhi ROI — Rendezvous Festival
===================================================================
Pulls the IIT Delhi campus boundary and road network from OpenStreetMap,
creates a 50m x 50m grid clipped to the 82-acre festival ROI, computes
walking-distance matrices over the actual path network, and exports
everything for use in the MILP solvers (Modules 3.2–3.5).

Outputs:
  - grid_cells.geojson          : GeoJSON of all valid grid cells with IDs
  - grid_centroids.geojson      : GeoJSON of cell centroids (demand points)
  - walking_distance_matrix.csv : D_ij matrix (metres) between all centroids
  - candidate_bin_locations.csv : Candidate facility locations (cell centroids)
  - iitd_roi_grid_map.html      : Interactive Folium map for visual check
  - iitd_roi_grid_map.png       : Static matplotlib figure
"""

import os
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import folium
from shapely.geometry import box, Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from scipy.spatial import cKDTree

warnings.filterwarnings("ignore", category=FutureWarning)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "grid_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====================================================================
# 1. IIT Delhi Campus Boundary & ROI Definition
# ====================================================================
# IIT Delhi campus boundary (approximate polygon from OSM relation)
# We query OSM for the campus, then define the 82-acre festival ROI
# as a sub-polygon covering the High-Intensity Zone.

PLACE_QUERY = "Indian Institute of Technology Delhi, New Delhi, India"
GRID_SIZE_M = 50  # 50m x 50m cells ≈ 0.6 acres each

# ROI polygon from Google Earth KML export — coordinates in (lat, lon).
ROI_POLYGON_COORDS = [
    (28.54593460564416, 77.19698696848262),
    (28.54609699593413, 77.19629414749039),
    (28.54500711054681, 77.18973756145169),
    (28.54620660679139, 77.18674089604193),
    (28.54775090825118, 77.19084005716148),
    (28.55057715515920, 77.18381246179051),
    (28.54618005102303, 77.18164866568537),
    (28.54663683268151, 77.18059945360173),
    (28.54393219187904, 77.17943741492736),
    (28.54276424163600, 77.18138263077708),
    (28.54475318783015, 77.18224693363388),
    (28.54486386282180, 77.18375290152068),
    (28.54405574048120, 77.18565145174203),
    (28.54456282719475, 77.18592657792534),
    (28.54189880841331, 77.19232799098667),
    (28.54291377874060, 77.19476036152102),
    (28.54429329691116, 77.19552068091009),
    (28.54593460564416, 77.19698696848262),
]


def get_campus_boundary():
    """Fetch IIT Delhi campus boundary from OSM."""
    print("[1/6] Fetching IIT Delhi campus boundary from OpenStreetMap...")
    try:
        gdf = ox.geocode_to_gdf(PLACE_QUERY)
        campus_geom = gdf.geometry.iloc[0]
        print(f"       Campus area from OSM: {campus_geom.area * 1e10:.0f} (arbitrary units)")
        return campus_geom, gdf
    except Exception as e:
        print(f"       WARNING: OSM geocode failed ({e}). Using ROI polygon as fallback.")
        return None, None


def build_roi_polygon():
    """Build the 82-acre festival ROI polygon."""
    roi = Polygon([(lon, lat) for lat, lon in ROI_POLYGON_COORDS])
    roi_gdf = gpd.GeoDataFrame(geometry=[roi], crs="EPSG:4326")
    roi_utm = roi_gdf.to_crs(roi_gdf.estimate_utm_crs())
    area_m2 = roi_utm.geometry.iloc[0].area
    area_acres = area_m2 / 4046.86
    print(f"       ROI area: {area_acres:.1f} acres ({area_m2:.0f} m²)")
    return roi, roi_gdf, roi_utm


# ====================================================================
# 2. Grid Generation — clipped to ROI
# ====================================================================
def generate_grid(roi_utm_gdf, grid_size=GRID_SIZE_M):
    """Create a grid of square cells clipped to the ROI polygon."""
    print(f"[2/6] Generating {grid_size}m × {grid_size}m grid over ROI...")
    roi_geom = roi_utm_gdf.geometry.iloc[0]
    minx, miny, maxx, maxy = roi_geom.bounds

    cells = []
    cell_id = 0
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            cell = box(x, y, x + grid_size, y + grid_size)
            clipped = cell.intersection(roi_geom)
            # Keep cells that overlap at least 25% with the ROI
            if not clipped.is_empty and clipped.area >= 0.25 * (grid_size ** 2):
                cells.append({
                    "cell_id": cell_id,
                    "geometry": clipped,
                    "area_m2": clipped.area,
                    "centroid_x": clipped.centroid.x,
                    "centroid_y": clipped.centroid.y,
                })
                cell_id += 1
            y += grid_size
        x += grid_size

    grid_gdf = gpd.GeoDataFrame(cells, crs=roi_utm_gdf.crs)
    print(f"       Generated {len(grid_gdf)} valid grid cells")
    print(f"       Average cell area: {grid_gdf['area_m2'].mean():.0f} m² "
          f"({grid_gdf['area_m2'].mean() / 4046.86:.2f} acres)")
    return grid_gdf


# ====================================================================
# 3. Walking Network & Distance Matrix
# ====================================================================
def get_walking_network(roi_polygon_wgs84):
    """Download the walking network from OSM for the ROI area."""
    print("[3/6] Downloading walking network from OpenStreetMap...")
    # Buffer slightly to capture paths at the ROI boundary
    buffered = roi_polygon_wgs84.buffer(0.002)  # ~200m buffer in degrees
    G = ox.graph_from_polygon(buffered, network_type="walk")
    print(f"       Network: {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G


def compute_walking_distances(G, grid_gdf, roi_utm_gdf):
    """Compute walking distance matrix between all cell centroids."""
    print("[4/6] Computing walking distance matrix (this may take a moment)...")

    # Convert centroids back to WGS84 for network snapping
    centroids_utm = grid_gdf[["cell_id", "centroid_x", "centroid_y"]].copy()
    centroid_points = gpd.GeoDataFrame(
        centroids_utm,
        geometry=gpd.points_from_xy(centroids_utm.centroid_x, centroids_utm.centroid_y),
        crs=roi_utm_gdf.crs,
    )
    centroid_points_wgs = centroid_points.to_crs("EPSG:4326")

    lats = centroid_points_wgs.geometry.y.values
    lons = centroid_points_wgs.geometry.x.values
    cell_ids = centroids_utm["cell_id"].values

    # Snap each centroid to nearest network node
    nearest_nodes = ox.distance.nearest_nodes(G, lons, lats)

    n = len(cell_ids)
    dist_matrix = np.full((n, n), np.inf)

    # Compute shortest paths from each unique node
    unique_nodes = list(set(nearest_nodes))
    print(f"       Computing shortest paths from {len(unique_nodes)} unique network nodes...")

    all_lengths = {}
    for i, source in enumerate(unique_nodes):
        try:
            lengths = nx.single_source_dijkstra_path_length(G, source, weight="length")
            all_lengths[source] = lengths
        except nx.NetworkXError:
            all_lengths[source] = {}
        if (i + 1) % 20 == 0:
            print(f"       ... processed {i + 1}/{len(unique_nodes)} source nodes")

    for i in range(n):
        for j in range(n):
            if i == j:
                dist_matrix[i, j] = 0.0
                continue
            src = nearest_nodes[i]
            tgt = nearest_nodes[j]
            if src in all_lengths and tgt in all_lengths[src]:
                dist_matrix[i, j] = all_lengths[src][tgt]

    # Replace any remaining inf with Euclidean fallback * 1.3 (detour factor)
    inf_mask = np.isinf(dist_matrix)
    if inf_mask.any():
        print(f"       WARNING: {inf_mask.sum()} pairs unreachable via network, using Euclidean × 1.3")
        xs = centroids_utm["centroid_x"].values
        ys = centroids_utm["centroid_y"].values
        for i in range(n):
            for j in range(n):
                if inf_mask[i, j]:
                    eucl = np.sqrt((xs[i] - xs[j]) ** 2 + (ys[i] - ys[j]) ** 2)
                    dist_matrix[i, j] = eucl * 1.3

    df = pd.DataFrame(dist_matrix, index=cell_ids, columns=cell_ids)
    df.index.name = "from_cell"
    df.columns.name = "to_cell"

    avg_dist = dist_matrix[dist_matrix > 0].mean()
    max_dist = dist_matrix.max()
    print(f"       Distance matrix: {n}×{n}")
    print(f"       Average walking distance: {avg_dist:.1f} m")
    print(f"       Maximum walking distance: {max_dist:.1f} m")
    return df


# ====================================================================
# 4. Export Everything
# ====================================================================
def export_data(grid_gdf, roi_utm_gdf, dist_df):
    """Export grid cells, centroids, distance matrix, and candidate locations."""
    print("[5/6] Exporting data files...")

    # Grid cells as GeoJSON (WGS84)
    grid_wgs = grid_gdf.to_crs("EPSG:4326")
    grid_wgs.to_file(os.path.join(OUTPUT_DIR, "grid_cells.geojson"), driver="GeoJSON")

    # Centroids — compute in UTM then convert to WGS84
    centroids_utm = grid_gdf.copy()
    centroids_utm["geometry"] = centroids_utm.geometry.centroid
    centroids = centroids_utm.to_crs("EPSG:4326")
    centroids["lat"] = centroids.geometry.y
    centroids["lon"] = centroids.geometry.x
    centroids.to_file(os.path.join(OUTPUT_DIR, "grid_centroids.geojson"), driver="GeoJSON")

    # Distance matrix
    dist_df.to_csv(os.path.join(OUTPUT_DIR, "walking_distance_matrix.csv"))

    # Candidate bin/station locations (cell centroids with IDs)
    candidates = centroids[["cell_id", "lat", "lon", "area_m2"]].copy()
    candidates.to_csv(os.path.join(OUTPUT_DIR, "candidate_locations.csv"), index=False)

    print(f"       Saved to: {OUTPUT_DIR}/")
    for f in os.listdir(OUTPUT_DIR):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"         {f:40s} ({size:,} bytes)")


# ====================================================================
# 5. Visualization
# ====================================================================
def create_visualizations(grid_gdf, roi_utm_gdf, roi_polygon_wgs84, G):
    """Create both an interactive Folium map and a static matplotlib figure."""
    print("[6/6] Creating visualizations...")

    grid_wgs = grid_gdf.to_crs("EPSG:4326")
    roi_wgs = gpd.GeoDataFrame(geometry=[roi_polygon_wgs84], crs="EPSG:4326")

    # --- Interactive Folium Map ---
    center_lat = np.mean([c[0] for c in ROI_POLYGON_COORDS])
    center_lon = np.mean([c[1] for c in ROI_POLYGON_COORDS])
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16,
                   tiles="OpenStreetMap")

    # ROI boundary
    folium.GeoJson(
        roi_wgs,
        style_function=lambda x: {
            "fillColor": "#ff000020",
            "color": "#cc0000",
            "weight": 3,
            "fillOpacity": 0.1,
        },
        name="ROI Boundary",
    ).add_to(m)

    # Grid cells with popups
    for _, row in grid_wgs.iterrows():
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda x: {
                "fillColor": "#3388ff",
                "color": "#003399",
                "weight": 1,
                "fillOpacity": 0.15,
            },
            tooltip=f"Cell {row['cell_id']} | {row['area_m2']:.0f} m²",
        ).add_to(m)

    # Cell centroids
    for _, row in grid_wgs.iterrows():
        c = row.geometry.centroid
        folium.CircleMarker(
            location=[c.y, c.x],
            radius=3,
            color="#cc0000",
            fill=True,
            fill_opacity=0.8,
            tooltip=f"Centroid {row['cell_id']}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    folium_path = os.path.join(OUTPUT_DIR, "iitd_roi_grid_map.html")
    m.save(folium_path)
    print(f"       Interactive map: {folium_path}")

    # --- Static Matplotlib Figure ---
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    roi_wgs.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2, label="ROI Boundary")
    grid_wgs.plot(ax=ax, facecolor="#3388ff22", edgecolor="#003399", linewidth=0.5)

    # Plot centroids (compute in UTM, then project to WGS84)
    centroids_for_plot = grid_gdf.geometry.centroid
    centroids_for_plot = gpd.GeoSeries(centroids_for_plot, crs=grid_gdf.crs).to_crs("EPSG:4326")
    centroids = centroids_for_plot
    ax.scatter(centroids.x, centroids.y, s=8, c="red", zorder=5, label="Cell Centroids")

    # Label every 5th cell to avoid clutter
    for _, row in grid_wgs.iterrows():
        if row["cell_id"] % 5 == 0:
            c = row.geometry.centroid
            ax.annotate(str(row["cell_id"]), (c.x, c.y), fontsize=5,
                        ha="center", va="center", color="#333")

    # Plot the walking network
    try:
        edges = ox.graph_to_gdfs(G, nodes=False)
        edges.plot(ax=ax, linewidth=0.3, color="gray", alpha=0.5)
    except Exception:
        pass

    ax.set_title(f"IIT Delhi ROI — {len(grid_gdf)} Grid Cells ({GRID_SIZE_M}m × {GRID_SIZE_M}m)", fontsize=14)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()

    png_path = os.path.join(OUTPUT_DIR, "iitd_roi_grid_map.png")
    fig.savefig(png_path, dpi=200)
    plt.close(fig)
    print(f"       Static map: {png_path}")


# ====================================================================
# MAIN
# ====================================================================
def main():
    print("=" * 70)
    print("IIT DELHI ROI — GEOSPATIAL GRID GENERATION")
    print("For Modules 3.2–3.5 Optimization (CLL782 Project)")
    print("=" * 70)

    campus_geom, campus_gdf = get_campus_boundary()
    roi_polygon, roi_gdf, roi_utm = build_roi_polygon()

    grid_gdf = generate_grid(roi_utm)

    G = get_walking_network(roi_polygon)

    dist_df = compute_walking_distances(G, grid_gdf, roi_utm)

    export_data(grid_gdf, roi_utm, dist_df)

    create_visualizations(grid_gdf, roi_utm, roi_polygon, G)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Grid cells (demand zones m):  {len(grid_gdf)}")
    print(f"  Cell size:                    {GRID_SIZE_M}m × {GRID_SIZE_M}m")
    print(f"  Candidate locations (p):      {len(grid_gdf)} (centroid of each cell)")
    print(f"  Distance matrix:              {len(grid_gdf)} × {len(grid_gdf)}")
    print(f"  Output directory:             {OUTPUT_DIR}/")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Use grid_centroids.geojson as demand zones (i = 1..m)")
    print("  2. Use candidate_locations.csv as potential facility sites (j = 1..p)")
    print("  3. Use walking_distance_matrix.csv as D_ij in your MILP formulations")
    print("  4. Open iitd_roi_grid_map.html in a browser for interactive exploration")


if __name__ == "__main__":
    main()
