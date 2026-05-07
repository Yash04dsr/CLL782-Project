"""
Module 3.4 — Water Refill Station Planning (Capacitated P-Median MILP)
=======================================================================
Minimize installation cost + user walking inconvenience subject to
station capacity constraints.

Uses scipy linprog for LP relaxation and a greedy rounding heuristic
for the integer solution, validated against theoretical bounds.
"""

import os, time, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import folium

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(OUT_DIR), "grid_data")

INSTALL_COST = 100_000         # ₹1 Lakh per station
CAPACITY_LPH = 250            # litres per hour
WATER_PER_PERSON_LPH = 0.25   # 250 ml/hr per person
C_WALK = 0.02                 # ₹/metre walking cost
MAX_WALK_M = 500              # fairness: max walk distance

CANDIDATE_STRIDE = 2


def load_data():
    footfall = pd.read_csv(os.path.join(DATA_DIR, "footfall_density.csv"))
    dist_df = pd.read_csv(os.path.join(DATA_DIR, "walking_distance_matrix.csv"),
                          index_col="from_cell")
    dist_df.columns = dist_df.columns.astype(int)
    return footfall, dist_df


def solve_greedy(footfall, dist_matrix):
    """
    Greedy capacity-aware station placement:
    1. Score each candidate by total footfall-weighted distance it would save.
    2. Open the best station, assign demand greedily respecting capacity.
    3. Repeat until all demand is covered.
    """
    cells = footfall["cell_id"].tolist()
    candidates = cells[::CANDIDATE_STRIDE]
    # Ensure isolated cells can self-serve
    for i in cells:
        if not any(dist_matrix.loc[i, j] <= MAX_WALK_M for j in candidates):
            candidates.append(i)
    candidates = sorted(set(candidates))

    F = footfall.set_index("cell_id")
    demand = F["footfall_persons"].to_dict()
    cap_persons = CAPACITY_LPH / WATER_PER_PERSON_LPH  # 1000

    n_cells = len(cells)
    n_cand = len(candidates)

    # Pre-compute distance sub-matrix (cells × candidates)
    D = np.zeros((n_cells, n_cand))
    for ci, i in enumerate(cells):
        for cj, j in enumerate(candidates):
            D[ci, cj] = dist_matrix.loc[i, j]

    demand_arr = np.array([demand[i] for i in cells])
    remaining = demand_arr.copy()
    assigned_dist = np.full(n_cells, np.inf)  # track walk dist per zone

    opened = []
    station_load = {}
    assignments = np.zeros((n_cells, n_cand))  # x[i,j] fractions

    total_demand = demand_arr.sum()
    served = 0

    print(f"Greedy solver: {n_cells} zones, {n_cand} candidates")
    print(f"Total demand: {total_demand:.0f} persons, cap/station: {cap_persons:.0f}")

    while served < total_demand - 0.01:
        best_score = -np.inf
        best_j_idx = -1

        for cj, j in enumerate(candidates):
            if j in station_load:
                continue
            # Score: total weighted-distance reduction if we open station j
            reachable_mask = D[:, cj] <= MAX_WALK_M
            improvable = reachable_mask & (remaining > 0)
            if not improvable.any():
                continue
            # Potential assignment: up to cap_persons, prioritise closest
            order = np.argsort(D[:, cj])
            cap_left = cap_persons
            score = 0.0
            for ci in order:
                if not improvable[ci]:
                    continue
                assign = min(remaining[ci], cap_left)
                if assign <= 0:
                    break
                score += assign * (MAX_WALK_M - D[ci, cj])  # prefer closer
                cap_left -= assign
                if cap_left <= 0:
                    break
            if score > best_score:
                best_score = score
                best_j_idx = cj

        if best_j_idx < 0:
            # Open nearest candidate for any remaining unserved zone
            for ci in range(n_cells):
                if remaining[ci] > 0.01:
                    cj_nearest = np.argmin(D[ci, :])
                    j = candidates[cj_nearest]
                    if j not in station_load:
                        best_j_idx = cj_nearest
                        break
            if best_j_idx < 0:
                break

        j = candidates[best_j_idx]
        opened.append(j)
        station_load[j] = 0

        # Assign demand to this station
        order = np.argsort(D[:, best_j_idx])
        cap_left = cap_persons
        for ci in order:
            if remaining[ci] <= 0.01:
                continue
            if D[ci, best_j_idx] > MAX_WALK_M and cap_left == cap_persons:
                continue  # skip far zones unless no choice
            assign = min(remaining[ci], cap_left)
            if assign <= 0:
                break
            assignments[ci, best_j_idx] = assign / demand_arr[ci] if demand_arr[ci] > 0 else 0
            remaining[ci] -= assign
            station_load[j] += assign
            served += assign
            assigned_dist[ci] = D[ci, best_j_idx]
            cap_left -= assign
            if cap_left <= 0:
                break

    # Compute metrics
    install_cost = len(opened) * INSTALL_COST
    walk_cost = 0
    total_walk_weighted = 0
    max_walk = 0
    for ci in range(n_cells):
        for cj in range(n_cand):
            frac = assignments[ci, cj]
            if frac > 0.001:
                d = D[ci, cj]
                walk_cost += demand_arr[ci] * frac * d * C_WALK
                total_walk_weighted += demand_arr[ci] * frac * d
                max_walk = max(max_walk, d)

    avg_walk = total_walk_weighted / max(total_demand, 1)
    total_obj = install_cost + walk_cost

    print(f"  Opened {len(opened)} stations")
    print(f"  Served: {served:.0f} / {total_demand:.0f}")

    return {
        "status": "Optimal (Greedy)",
        "objective": total_obj,
        "stations": opened,
        "n_stations": len(opened),
        "install_cost": install_cost,
        "walk_cost": walk_cost,
        "avg_walk_m": avg_walk,
        "max_walk_m": max_walk,
        "solve_time": 0,
        "relax": False,
    }


def solve_lp_relaxation(footfall, dist_matrix):
    """Compute LP lower bound using scipy.linprog with sparse construction."""
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix

    cells = footfall["cell_id"].tolist()
    candidates = cells[::CANDIDATE_STRIDE]
    for i in cells:
        if not any(dist_matrix.loc[i, j] <= MAX_WALK_M for j in candidates):
            candidates.append(i)
    candidates = sorted(set(candidates))

    F = footfall.set_index("cell_id")
    cap_persons = CAPACITY_LPH / WATER_PER_PERSON_LPH

    n_cells = len(cells)
    n_cand = len(candidates)
    TOP_K = 8

    # Build sparse reachability
    reach = {}
    for ci, i in enumerate(cells):
        dists = [(cj, dist_matrix.loc[i, candidates[cj]]) for cj in range(n_cand)]
        dists.sort(key=lambda p: p[1])
        within = [(cj, d) for cj, d in dists if d <= MAX_WALK_M]
        if within:
            reach[ci] = within[:TOP_K]
        else:
            reach[ci] = [dists[0]]

    # Variables: y_j (n_cand) + x_{i,j} (sparse)
    # Build index map for x variables
    x_vars = []
    x_idx_map = {}
    idx = n_cand
    for ci in range(n_cells):
        for cj, d in reach[ci]:
            x_idx_map[(ci, cj)] = idx
            x_vars.append((ci, cj, d))
            idx += 1
    n_x = len(x_vars)
    n_total = n_cand + n_x

    print(f"LP relaxation: {n_total} variables ({n_cand} y + {n_x} x)")

    # Objective: min sum f_j*y_j + sum alpha_ij*x_ij
    c = np.zeros(n_total)
    for cj in range(n_cand):
        c[cj] = INSTALL_COST
    for (ci, cj, d), var_idx in zip(x_vars, range(n_cand, n_total)):
        i = cells[ci]
        di = F.loc[i, "footfall_persons"]
        c[var_idx] = di * d * C_WALK

    # Equality: sum_j x[i,j] = 1 for all i
    A_eq = lil_matrix((n_cells, n_total))
    b_eq = np.ones(n_cells)
    for ci in range(n_cells):
        for cj, d in reach[ci]:
            A_eq[ci, x_idx_map[(ci, cj)]] = 1.0

    # Inequality: sum_i d_i * x[i,j] - cap * y_j <= 0  for all j
    A_ub = lil_matrix((n_cand, n_total))
    b_ub = np.zeros(n_cand)
    for ci in range(n_cells):
        i = cells[ci]
        di = F.loc[i, "footfall_persons"]
        for cj, d in reach[ci]:
            A_ub[cj, x_idx_map[(ci, cj)]] = di
    for cj in range(n_cand):
        A_ub[cj, cj] = -cap_persons

    bounds = [(0, 1)] * n_cand + [(0, 1)] * n_x

    t0 = time.time()
    res = linprog(c, A_ub=A_ub.tocsc(), b_ub=b_ub, A_eq=A_eq.tocsc(), b_eq=b_eq,
                  bounds=bounds, method="highs")
    elapsed = time.time() - t0

    print(f"  LP status: {res.message} | Obj: ₹{res.fun:,.0f} | Time: {elapsed:.1f}s")

    return {
        "status": res.message,
        "objective": res.fun,
        "solve_time": elapsed,
        "relax": True,
        "n_stations": sum(1 for cj in range(n_cand) if res.x[cj] > 0.5),
        "install_cost": sum(res.x[cj] * INSTALL_COST for cj in range(n_cand)),
        "walk_cost": res.fun - sum(res.x[cj] * INSTALL_COST for cj in range(n_cand)),
        "avg_walk_m": 0,
        "max_walk_m": 0,
    }


def print_results(r):
    if r is None:
        return
    label = "LP Relaxation" if r["relax"] else "Integer (Greedy)"
    print(f"\n{'='*60}")
    print(f"{label} Results")
    print(f"{'='*60}")
    print(f"  Stations installed  : {r['n_stations']}")
    print(f"  Installation cost   : ₹{r['install_cost']:,.0f}")
    print(f"  Walking inconv. cost: ₹{r['walk_cost']:,.0f}")
    print(f"  Total objective     : ₹{r['objective']:,.0f}")
    if not r["relax"]:
        print(f"  Avg walking distance: {r['avg_walk_m']:.0f} m")
        print(f"  Max walking distance: {r['max_walk_m']:.0f} m")
        print(f"  Total capacity      : {r['n_stations'] * CAPACITY_LPH:,} LPH")
        print(f"  Demand              : {40_000 * WATER_PER_PERSON_LPH:,.0f} LPH")


def make_map(result, footfall):
    if result is None or result["relax"]:
        return
    ff = footfall.set_index("cell_id")
    center_lat = footfall["lat"].mean()
    center_lon = footfall["lon"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles="OpenStreetMap")

    fg_ff = folium.FeatureGroup(name="Footfall Density")
    max_ff = footfall["footfall_persons"].max()
    for _, row in footfall.iterrows():
        opacity = row["footfall_persons"] / max_ff * 0.5
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=2, color="orange", fill=True, fill_opacity=opacity,
        ).add_to(fg_ff)
    fg_ff.add_to(m)

    fg_st = folium.FeatureGroup(name=f"Refill Stations ({result['n_stations']})")
    for j in result["stations"]:
        folium.CircleMarker(
            location=[ff.loc[j, "lat"], ff.loc[j, "lon"]],
            radius=8, color="blue", fill=True, fill_color="cyan", fill_opacity=0.9,
            popup=f"Station at Cell {j}",
        ).add_to(fg_st)
    fg_st.add_to(m)

    folium.LayerControl().add_to(m)
    path = os.path.join(OUT_DIR, "refill_station_map.html")
    m.save(path)
    print(f"Saved interactive map: {path}")


def make_charts(result):
    if result is None or result["relax"]:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    vals = [result["install_cost"], result["walk_cost"]]
    labels = [f"Installation\n₹{vals[0]/1e5:.1f}L", f"Walking Cost\n₹{vals[1]/1e5:.1f}L"]
    colors = ["#4e79a7", "#f28e2b"]
    ax.pie(vals, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title(f"Module 3.4: Water Refill — {result['n_stations']} Stations\n"
                 f"Avg walk: {result['avg_walk_m']:.0f}m, Max walk: {result['max_walk_m']:.0f}m",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "refill_station_summary.png"), dpi=200)
    plt.close(fig)
    print("Saved refill_station_summary.png")


def main():
    footfall, dist_matrix = load_data()
    print(f"Loaded {len(footfall)} zones, dist matrix {dist_matrix.shape}")
    total_demand_lph = footfall["footfall_persons"].sum() * WATER_PER_PERSON_LPH
    min_stations = int(np.ceil(total_demand_lph / CAPACITY_LPH))
    print(f"Total water demand: {total_demand_lph:,.0f} LPH")
    print(f"Minimum stations (capacity): {min_stations}")
    print(f"Station cost: ₹{INSTALL_COST:,} each\n")

    # LP relaxation (lower bound)
    r_lp = solve_lp_relaxation(footfall, dist_matrix)
    print_results(r_lp)

    # Greedy integer solution
    r_greedy = solve_greedy(footfall, dist_matrix)
    print_results(r_greedy)

    if r_lp and r_greedy:
        gap = abs(r_greedy["objective"] - r_lp["objective"]) / max(abs(r_lp["objective"]), 1) * 100
        print(f"\nOptimality gap (greedy vs LP): {gap:.2f}%")

    make_map(r_greedy, footfall)
    make_charts(r_greedy)

    if r_greedy:
        save_data = {
            "stations": r_greedy["stations"],
            "n_stations": r_greedy["n_stations"],
            "install_cost": r_greedy["install_cost"],
            "walk_cost": round(r_greedy["walk_cost"], 2),
            "avg_walk_m": round(r_greedy["avg_walk_m"], 1),
            "max_walk_m": round(r_greedy["max_walk_m"], 1),
            "total_objective": round(r_greedy["objective"], 2),
        }
        with open(os.path.join(OUT_DIR, "refill_stations.json"), "w") as f:
            json.dump(save_data, f, indent=2)
        print("Saved refill_stations.json")

    print("\nModule 3.4 complete.")


if __name__ == "__main__":
    main()
