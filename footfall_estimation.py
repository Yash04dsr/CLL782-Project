"""
Footfall Estimation for IIT Delhi ROI (287 Grid Cells)
======================================================
Generates per-cell footfall density and waste generation estimates
using a spatial gravity model centered on key campus venues.

Output: grid_data/footfall_density.csv
"""

import numpy as np
import pandas as pd
from math import radians, cos, sin, asin, sqrt

# ---------------------------------------------------------------------------
# Key venue locations (lat, lon) and their relative attractiveness weights
# Weights reflect expected crowd pull during Rendezvous peak hours.
# ---------------------------------------------------------------------------
VENUES = {
    "OAT":              {"lat": 28.5460, "lon": 77.1920, "weight": 1.00},
    "Nalanda_Ground":   {"lat": 28.5470, "lon": 77.1880, "weight": 0.85},
    "SAC":              {"lat": 28.5455, "lon": 77.1905, "weight": 0.70},
    "LHC":              {"lat": 28.5445, "lon": 77.1935, "weight": 0.60},
    "Main_Building":    {"lat": 28.5450, "lon": 77.1950, "weight": 0.40},
    "Amul_Food_Court":  {"lat": 28.5468, "lon": 77.1910, "weight": 0.80},
    "Red_Square":       {"lat": 28.5462, "lon": 77.1895, "weight": 0.55},
    "Sports_Complex":   {"lat": 28.5490, "lon": 77.1860, "weight": 0.35},
    "Biotech_Lawn":     {"lat": 28.5440, "lon": 77.1870, "weight": 0.45},
    "Rose_Garden":      {"lat": 28.5435, "lon": 77.1940, "weight": 0.30},
}

TOTAL_PEAK_FOOTFALL = 40_000  # persons at peak hour
WASTE_RATE_KG_PER_PERSON = 0.15  # kg/person/visit

# CPCB waste composition fractions
FRAC_COMPOSTABLE = 0.40
FRAC_RECYCLABLE = 0.40
FRAC_GENERAL = 0.20

SIGMA_M = 350  # Gaussian decay length-scale in metres


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres between two (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(a))


def main():
    cells = pd.read_csv("grid_data/candidate_locations.csv")
    n_cells = len(cells)

    raw_attraction = np.zeros(n_cells)
    for _, venue in VENUES.items():
        for idx, row in cells.iterrows():
            d = haversine_m(row["lat"], row["lon"], venue["lat"], venue["lon"])
            raw_attraction[idx] += venue["weight"] * np.exp(-0.5 * (d / SIGMA_M) ** 2)

    # Area-weighted: larger cells collect more people
    area_weight = cells["area_m2"].values / cells["area_m2"].max()
    weighted = raw_attraction * area_weight

    # Normalize so total = TOTAL_PEAK_FOOTFALL
    footfall = weighted / weighted.sum() * TOTAL_PEAK_FOOTFALL

    # Waste generation per cell
    waste_total = footfall * WASTE_RATE_KG_PER_PERSON
    waste_compostable = waste_total * FRAC_COMPOSTABLE
    waste_recyclable = waste_total * FRAC_RECYCLABLE
    waste_general = waste_total * FRAC_GENERAL

    out = pd.DataFrame({
        "cell_id": cells["cell_id"],
        "lat": cells["lat"],
        "lon": cells["lon"],
        "area_m2": cells["area_m2"],
        "footfall_persons": np.round(footfall, 2),
        "waste_kg_total": np.round(waste_total, 4),
        "waste_compostable_kg": np.round(waste_compostable, 4),
        "waste_recyclable_kg": np.round(waste_recyclable, 4),
        "waste_general_kg": np.round(waste_general, 4),
    })

    out.to_csv("grid_data/footfall_density.csv", index=False)

    print(f"Footfall estimation complete — {n_cells} cells")
    print(f"  Total footfall : {footfall.sum():.0f} persons")
    print(f"  Total waste    : {waste_total.sum():.1f} kg")
    print(f"  Compostable    : {waste_compostable.sum():.1f} kg")
    print(f"  Recyclable     : {waste_recyclable.sum():.1f} kg")
    print(f"  General/Inert  : {waste_general.sum():.1f} kg")
    print(f"  Min cell footfall : {footfall.min():.1f}")
    print(f"  Max cell footfall : {footfall.max():.1f}")
    print(f"  Mean cell footfall: {footfall.mean():.1f}")
    print(f"Saved to grid_data/footfall_density.csv")


if __name__ == "__main__":
    main()
