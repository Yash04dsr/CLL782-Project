"""
Module 3.2 — Dustbin Placement with 3-Type Waste Segregation (MILP)
====================================================================
Facility Location Problem with bin types t in {compostable, recyclable, general}.

Decision variables:
  y[j,t] >= 0 integer — number of bins of type t at candidate site j
  a[i,j,t] in [0,1]   — fraction of zone i's type-t waste assigned to site j

Uses PuLP with CBC solver on the 287-cell grid.
"""

import os, time, json
import numpy as np
import pandas as pd
import pulp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import folium

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(OUT_DIR), "grid_data")

# ── Bin type parameters ──
BIN_TYPES = {
    "compostable": {"capacity_kg": 20, "cost_inr": 10_000, "radius_m": 200, "color": "green"},
    "recyclable":  {"capacity_kg": 15, "cost_inr":  8_000, "radius_m": 200, "color": "blue"},
    "general":     {"capacity_kg": 10, "cost_inr":  6_000, "radius_m": 250, "color": "gray"},
}
WASTE_COL = {
    "compostable": "waste_compostable_kg",
    "recyclable":  "waste_recyclable_kg",
    "general":     "waste_general_kg",
}
BUDGET = 35_00_000  # INR 35 Lakhs


def load_data():
    footfall = pd.read_csv(os.path.join(DATA_DIR, "footfall_density.csv"))
    dist_df = pd.read_csv(os.path.join(DATA_DIR, "walking_distance_matrix.csv"), index_col="from_cell")
    dist_df.columns = dist_df.columns.astype(int)
    return footfall, dist_df


def solve_milp(footfall, dist_matrix, relax_binary=False):
    """
    Solve the bin placement FLP.  We allow multiple bins per site (y[j,t] integer)
    because high-footfall zones need multiple bins to satisfy capacity.
    """
    m = len(footfall)
    cells = footfall["cell_id"].tolist()
    types = list(BIN_TYPES.keys())

    prob = pulp.LpProblem("DustbinPlacement_3Type", pulp.LpMinimize)

    # y[j,t] = number of bins of type t at site j (integer, or continuous for LP relax)
    cat_y = pulp.LpContinuous if relax_binary else pulp.LpInteger
    max_bins_per_site = 10
    y = {}
    for j in cells:
        for t in types:
            y[(j, t)] = pulp.LpVariable(f"y_{j}_{t}", lowBound=0,
                                         upBound=max_bins_per_site, cat=cat_y)

    # Pre-compute reachable pairs per type
    reachable = {}
    reachable_from = {}
    for t in types:
        R = BIN_TYPES[t]["radius_m"]
        reach_t = {}
        reach_from_t = {i: [] for i in cells}
        for i in cells:
            reach_t[i] = []
            for j in cells:
                if dist_matrix.loc[i, j] <= R:
                    reach_t[i].append(j)
                    reach_from_t[j].append(i)  # zones served by site j
        reachable[t] = reach_t
        reachable_from[t] = reach_from_t

    # Check coverage feasibility
    for t in types:
        for i in cells:
            if len(reachable[t][i]) == 0:
                # Force self-assignment by extending radius for this cell
                reachable[t][i] = [i]
                reachable_from[t][i].append(i)

    # a[i,j,t] — assignment fractions (only for reachable pairs)
    a = {}
    for t in types:
        for i in cells:
            for j in reachable[t][i]:
                a[(i, j, t)] = pulp.LpVariable(f"a_{i}_{j}_{t}", lowBound=0, upBound=1)

    F = footfall.set_index("cell_id")

    # Objective: minimise total waste-weighted walking distance
    obj_terms = []
    for t in types:
        for i in cells:
            w_it = F.loc[i, WASTE_COL[t]]
            for j in reachable[t][i]:
                obj_terms.append(w_it * a[(i, j, t)] * dist_matrix.loc[i, j])
    prob += pulp.lpSum(obj_terms), "TotalWeightedDistance"

    # C1: Coverage — each zone's waste type fully assigned
    for t in types:
        for i in cells:
            prob += (
                pulp.lpSum(a[(i, j, t)] for j in reachable[t][i]) == 1,
                f"Cover_{i}_{t}"
            )

    # C2: Capacity — total waste assigned to site j, type t <= capacity * y[j,t]
    for t in types:
        K = BIN_TYPES[t]["capacity_kg"]
        for j in cells:
            serving_zones = [i for i in cells if j in reachable[t][i]]
            if serving_zones:
                prob += (
                    pulp.lpSum(F.loc[i, WASTE_COL[t]] * a[(i, j, t)]
                               for i in serving_zones) <= K * y[(j, t)],
                    f"Cap_{j}_{t}"
                )

    # C3: Budget
    prob += (
        pulp.lpSum(BIN_TYPES[t]["cost_inr"] * y[(j, t)] for j in cells for t in types) <= BUDGET,
        "Budget"
    )

    n_vars = len(prob.variables())
    n_cons = len(prob.constraints)
    print(f"Solving {'LP relaxation' if relax_binary else 'MILP'}...")
    print(f"  Variables: {n_vars}, Constraints: {n_cons}")

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=300)
    t0 = time.time()
    prob.solve(solver)
    elapsed = time.time() - t0

    status = pulp.LpStatus[prob.status]
    obj_val = pulp.value(prob.objective)
    print(f"  Status: {status}  |  Objective: {obj_val:,.0f}  |  Time: {elapsed:.1f}s")

    if status != "Optimal":
        print("WARNING: solver did not find optimal solution!")
        return None

    # Extract placements
    placements = {}
    total_bins_by_type = {}
    for t in types:
        site_counts = {}
        for j in cells:
            val = y[(j, t)].varValue
            if val is not None and val > 0.01:
                site_counts[j] = int(round(val)) if not relax_binary else round(val, 2)
        placements[t] = site_counts
        total_bins_by_type[t] = sum(site_counts.values())

    return {
        "status": status,
        "objective": obj_val,
        "placements": placements,
        "total_bins": total_bins_by_type,
        "solve_time": elapsed,
        "relax": relax_binary,
    }


def summarise(result):
    if result is None:
        return
    print(f"\n{'='*60}")
    label = "LP Relaxation" if result["relax"] else "MILP (Integer)"
    print(f"{label} Results")
    print(f"{'='*60}")
    total_cost = 0
    total_bins = 0
    for t in BIN_TYPES:
        n = result["total_bins"].get(t, 0)
        cost = n * BIN_TYPES[t]["cost_inr"]
        total_cost += cost
        total_bins += n
        n_sites = len(result["placements"].get(t, {}))
        print(f"  {t:14s}: {n:7.1f} bins at {n_sites} sites, cost ≈ ₹{cost:,.0f}")
    print(f"  {'TOTAL':14s}: {total_bins:7.1f} bins, cost = ₹{total_cost:,.0f}")
    print(f"  Budget usage: {total_cost/BUDGET:.1%}")
    print(f"  Objective (waste-m): {result['objective']:,.0f}")


def make_map(result, footfall):
    if result is None or result["relax"]:
        return
    placements = result["placements"]
    center_lat = footfall["lat"].mean()
    center_lon = footfall["lon"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles="OpenStreetMap")

    type_colors = {"compostable": "green", "recyclable": "blue", "general": "gray"}
    ff = footfall.set_index("cell_id")

    for t, site_counts in placements.items():
        fg = folium.FeatureGroup(name=f"{t.title()} bins ({sum(site_counts.values())})")
        for j, count in site_counts.items():
            folium.CircleMarker(
                location=[ff.loc[j, "lat"], ff.loc[j, "lon"]],
                radius=3 + count * 1.5,
                color=type_colors[t],
                fill=True, fill_opacity=0.7,
                popup=f"Cell {j} | {t} × {count}",
            ).add_to(fg)
        fg.add_to(m)

    folium.LayerControl().add_to(m)
    path = os.path.join(OUT_DIR, "bin_placement_map.html")
    m.save(path)
    print(f"Saved interactive map: {path}")


def make_charts(result):
    if result is None or result["relax"]:
        return
    types = list(BIN_TYPES.keys())
    counts = [result["total_bins"].get(t, 0) for t in types]
    costs = [result["total_bins"].get(t, 0) * BIN_TYPES[t]["cost_inr"] for t in types]
    colors = [BIN_TYPES[t]["color"] for t in types]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.bar(types, counts, color=colors, edgecolor="black")
    ax1.set_ylabel("Number of Bins")
    ax1.set_title("Bin Count by Waste Type")
    for i, v in enumerate(counts):
        ax1.text(i, v + 1, str(int(v)), ha="center", fontweight="bold")

    ax2.bar(types, [c / 1e5 for c in costs], color=colors, edgecolor="black")
    ax2.set_ylabel("Cost (₹ Lakhs)")
    ax2.set_title("Investment by Bin Type")
    for i, v in enumerate(costs):
        ax2.text(i, v / 1e5 + 0.1, f"₹{v/1e5:.1f}L", ha="center", fontweight="bold")

    fig.suptitle("Module 3.2: 3-Type Waste-Segregated Bin Placement", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "bin_placement_summary.png"), dpi=200)
    plt.close(fig)
    print("Saved bin_placement_summary.png")


def main():
    footfall, dist_matrix = load_data()
    print(f"Loaded {len(footfall)} demand zones, distance matrix {dist_matrix.shape}")
    print(f"Total waste: {footfall['waste_kg_total'].sum():.0f} kg")
    print(f"  Compostable: {footfall['waste_compostable_kg'].sum():.0f} kg")
    print(f"  Recyclable : {footfall['waste_recyclable_kg'].sum():.0f} kg")
    print(f"  General    : {footfall['waste_general_kg'].sum():.0f} kg")
    print(f"Budget: ₹{BUDGET:,}\n")

    # LP relaxation (lower bound)
    result_lp = solve_milp(footfall, dist_matrix, relax_binary=True)
    summarise(result_lp)

    # Integer MILP
    result_milp = solve_milp(footfall, dist_matrix, relax_binary=False)
    summarise(result_milp)

    if result_lp and result_milp:
        gap = abs(result_milp["objective"] - result_lp["objective"]) / max(abs(result_lp["objective"]), 1) * 100
        print(f"\nIntegrality gap: {gap:.2f}%")

    make_map(result_milp, footfall)
    make_charts(result_milp)

    if result_milp:
        save_data = {}
        for t, sc in result_milp["placements"].items():
            save_data[t] = {str(k): v for k, v in sc.items()}
        with open(os.path.join(OUT_DIR, "bin_placements.json"), "w") as f:
            json.dump(save_data, f, indent=2)
        print("Saved bin_placements.json")

    print("\nModule 3.2 complete.")


if __name__ == "__main__":
    main()
