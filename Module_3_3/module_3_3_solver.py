"""
Module 3.3 — Waste Collection & Processing Logistics with Vehicle Type Segregation
====================================================================================
Each waste type has its own vehicle fleet and designated processing facility (sink).

Waste type -> Facility mapping:
  compostable -> On-campus Biogas/Compost  (1 km avg, cap 500 kg/day)
  recyclable  -> Okhla Recycling Aggregator (11 km, revenue -₹8/kg)
  general     -> Okhla Landfill/WTE         (12 km, cost ₹2/kg)

Vehicle types (segregated by waste type):
  Green Tipper  — compostable only, 750 kg, ₹600/day, ₹15/km
  Blue Tipper   — recyclable only,  750 kg, ₹600/day, ₹15/km
  Grey Tipper   — general only,     500 kg, ₹500/day, ₹18/km

Decision variables:
  x[i,j,t] >= 0  — kg of waste type t from zone i to facility j
  N_t integer     — number of vehicles of type t deployed
"""

import os, time, json
import numpy as np
import pandas as pd
import pulp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(OUT_DIR), "grid_data")

WASTE_TYPES = ["compostable", "recyclable", "general"]
WASTE_COL = {
    "compostable": "waste_compostable_kg",
    "recyclable":  "waste_recyclable_kg",
    "general":     "waste_general_kg",
}

# Facilities (sinks)
FACILITIES = {
    "biogas":    {"name": "On-campus Biogas/Compost", "dist_km": 1.0,
                  "proc_cost_per_kg": 0.5,  "capacity_kg": 500},
    "recycler":  {"name": "Okhla Recycling Aggregator", "dist_km": 11.0,
                  "proc_cost_per_kg": -8.0, "capacity_kg": 1e9},  # revenue
    "landfill":  {"name": "Okhla Landfill/WTE", "dist_km": 12.0,
                  "proc_cost_per_kg": 2.0,  "capacity_kg": 1e9},
}

# Which facilities accept which waste types (primary + overflow)
TYPE_FACILITY_MAP = {
    "compostable": ["biogas", "landfill"],       # primary: biogas; overflow: landfill
    "recyclable":  ["recycler", "landfill"],      # primary: recycler; overflow: landfill
    "general":     ["landfill"],                   # only landfill
}

# Vehicle types (one per waste type)
VEHICLES = {
    "compostable": {"name": "Green Tipper", "capacity_kg": 750,
                    "fixed_cost": 600, "var_cost_per_km": 15},
    "recyclable":  {"name": "Blue Tipper",  "capacity_kg": 750,
                    "fixed_cost": 600, "var_cost_per_km": 15},
    "general":     {"name": "Grey Tipper",  "capacity_kg": 500,
                    "fixed_cost": 500, "var_cost_per_km": 18},
}

HANDLING_COST_PER_KG = 1.0  # ₹/kg loading/unloading


def load_data():
    footfall = pd.read_csv(os.path.join(DATA_DIR, "footfall_density.csv"))
    return footfall


def solve_logistics(footfall, waste_multiplier=1.0, label="Base"):
    cells = footfall["cell_id"].tolist()
    facilities = list(FACILITIES.keys())
    types = WASTE_TYPES

    prob = pulp.LpProblem(f"WasteLogistics_{label}", pulp.LpMinimize)

    # x[i, j, t]: kg of waste type t from zone i to facility j
    x = {}
    for t in types:
        for i in cells:
            for j in TYPE_FACILITY_MAP[t]:
                x[(i, j, t)] = pulp.LpVariable(f"x_{i}_{j}_{t}", lowBound=0)

    # N_t: number of vehicles of type t (integer)
    N = {}
    for t in types:
        N[t] = pulp.LpVariable(f"N_{t}", lowBound=0, cat=pulp.LpInteger)

    F = footfall.set_index("cell_id")

    # Objective: total logistics cost
    obj_terms = []

    # Transport + handling + processing costs
    for t in types:
        v = VEHICLES[t]
        for i in cells:
            for j in TYPE_FACILITY_MAP[t]:
                fac = FACILITIES[j]
                # Distance from zone i to facility j:
                # For simplicity, use facility average distance (all zones roughly equidistant
                # to off-campus facilities; on-campus varies but we use avg)
                dist = fac["dist_km"]
                unit_cost = v["var_cost_per_km"] * dist + HANDLING_COST_PER_KG + fac["proc_cost_per_kg"]
                obj_terms.append(unit_cost * x[(i, j, t)])

    # Fixed vehicle costs
    for t in types:
        obj_terms.append(VEHICLES[t]["fixed_cost"] * N[t])

    prob += pulp.lpSum(obj_terms), "TotalLogisticsCost"

    # C1: Waste clearance — all waste of type t from zone i must be shipped
    for t in types:
        for i in cells:
            w_it = F.loc[i, WASTE_COL[t]] * waste_multiplier
            prob += (
                pulp.lpSum(x[(i, j, t)] for j in TYPE_FACILITY_MAP[t]) == w_it,
                f"Clear_{i}_{t}"
            )

    # C2: Facility capacity (only biogas is constrained)
    for j in facilities:
        cap = FACILITIES[j]["capacity_kg"]
        if cap < 1e8:
            for t in types:
                if j in TYPE_FACILITY_MAP[t]:
                    prob += (
                        pulp.lpSum(x[(i, j, t)] for i in cells) <= cap,
                        f"FacCap_{j}_{t}"
                    )

    # C3: Fleet capacity — total waste carried by type t <= vehicle capacity * N_t
    # Each vehicle makes multiple trips per day; assume 3 trips/day for on-campus, 2 for off-campus
    for t in types:
        daily_cap_per_vehicle = VEHICLES[t]["capacity_kg"] * 2  # conservative 2 trips/day
        prob += (
            pulp.lpSum(x[(i, j, t)] for i in cells for j in TYPE_FACILITY_MAP[t])
            <= daily_cap_per_vehicle * N[t],
            f"Fleet_{t}"
        )

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=120)
    t0 = time.time()
    prob.solve(solver)
    elapsed = time.time() - t0

    status = pulp.LpStatus[prob.status]
    obj_val = pulp.value(prob.objective)
    print(f"\n[{label}] Status: {status} | Total Cost: ₹{obj_val:,.0f} | Time: {elapsed:.1f}s")

    if status != "Optimal":
        print("WARNING: not optimal!")
        return None

    # Extract results
    flows = {}
    for t in types:
        flows[t] = {}
        for j in TYPE_FACILITY_MAP[t]:
            total_flow = sum(x[(i, j, t)].varValue or 0 for i in cells)
            flows[t][j] = round(total_flow, 1)

    vehicles_used = {t: int(round(N[t].varValue or 0)) for t in types}

    # Cost breakdown
    transport_cost = 0
    processing_cost = 0
    for t in types:
        v = VEHICLES[t]
        for i in cells:
            for j in TYPE_FACILITY_MAP[t]:
                val = x[(i, j, t)].varValue or 0
                fac = FACILITIES[j]
                transport_cost += (v["var_cost_per_km"] * fac["dist_km"] + HANDLING_COST_PER_KG) * val
                processing_cost += fac["proc_cost_per_kg"] * val

    fleet_cost = sum(VEHICLES[t]["fixed_cost"] * vehicles_used[t] for t in types)

    return {
        "label": label,
        "status": status,
        "total_cost": obj_val,
        "flows": flows,
        "vehicles": vehicles_used,
        "transport_cost": transport_cost,
        "processing_cost": processing_cost,
        "fleet_cost": fleet_cost,
        "waste_multiplier": waste_multiplier,
    }


def print_results(r):
    if r is None:
        return
    print(f"\n{'='*60}")
    print(f"  Scenario: {r['label']} (waste × {r['waste_multiplier']})")
    print(f"{'='*60}")
    print(f"  Waste Flows (kg/day):")
    for t in WASTE_TYPES:
        for j, flow in r["flows"][t].items():
            fac_name = FACILITIES[j]["name"]
            print(f"    {t:14s} → {fac_name:35s}: {flow:8.1f} kg")

    print(f"\n  Vehicle Deployment:")
    for t in WASTE_TYPES:
        v = VEHICLES[t]
        print(f"    {v['name']:14s} ({t}): {r['vehicles'][t]} vehicles")

    print(f"\n  Cost Breakdown:")
    print(f"    Transport + Handling: ₹{r['transport_cost']:,.0f}")
    print(f"    Processing          : ₹{r['processing_cost']:,.0f}")
    print(f"    Fleet Fixed         : ₹{r['fleet_cost']:,.0f}")
    print(f"    TOTAL               : ₹{r['total_cost']:,.0f}")

    if r["processing_cost"] < 0:
        print(f"    (Recycling revenue offsets ₹{abs(r['processing_cost']):,.0f})")


def make_sankey_data(r):
    """Create a Sankey-like flow summary chart."""
    if r is None:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    labels = []
    values = []
    colors = []
    type_colors = {"compostable": "#2ca02c", "recyclable": "#1f77b4", "general": "#7f7f7f"}

    for t in WASTE_TYPES:
        for j, flow in r["flows"][t].items():
            if flow > 0:
                fac_name = FACILITIES[j]["name"].split("(")[0].strip()
                labels.append(f"{t.title()}\n→ {fac_name}")
                values.append(flow)
                colors.append(type_colors[t])

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=colors, edgecolor="black", height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Waste Flow (kg/day)")
    ax.set_title(f"Waste Flow Allocation — {r['label']}", fontweight="bold")

    for i, v in enumerate(values):
        ax.text(v + 20, i, f"{v:,.0f} kg", va="center", fontsize=9)

    fig.tight_layout()
    path = os.path.join(OUT_DIR, f"waste_flow_{r['label'].lower().replace(' ','_')}.png")
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Saved {os.path.basename(path)}")


def make_comparison_chart(r_base, r_sens):
    if r_base is None or r_sens is None:
        return

    categories = ["Transport+\nHandling", "Processing", "Fleet Fixed", "TOTAL"]
    base_vals = [r_base["transport_cost"], r_base["processing_cost"],
                 r_base["fleet_cost"], r_base["total_cost"]]
    sens_vals = [r_sens["transport_cost"], r_sens["processing_cost"],
                 r_sens["fleet_cost"], r_sens["total_cost"]]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, base_vals, width, label="Base (1.0×)", color="#4e79a7")
    ax.bar(x + width/2, sens_vals, width, label="Sensitivity (1.2×)", color="#e15759")
    ax.set_ylabel("Cost (₹)")
    ax.set_title("Module 3.3: Sensitivity Analysis — Base vs +20% Waste", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "sensitivity_comparison.png"), dpi=200)
    plt.close(fig)
    print("Saved sensitivity_comparison.png")


def make_vehicle_chart(r_base, r_sens):
    if r_base is None or r_sens is None:
        return
    types = WASTE_TYPES
    names = [VEHICLES[t]["name"] for t in types]
    base_v = [r_base["vehicles"][t] for t in types]
    sens_v = [r_sens["vehicles"][t] for t in types]

    x = np.arange(len(types))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width/2, base_v, width, label="Base", color=["#2ca02c", "#1f77b4", "#7f7f7f"])
    bars2 = ax.bar(x + width/2, sens_v, width, label="+20% Waste",
                   color=["#2ca02c", "#1f77b4", "#7f7f7f"], alpha=0.6, edgecolor="red", linewidth=2)
    ax.set_ylabel("Vehicles Deployed")
    ax.set_title("Vehicle Type Segregation: Fleet Deployment", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.legend()

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                str(int(bar.get_height())), ha="center", fontweight="bold")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                str(int(bar.get_height())), ha="center", fontweight="bold")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "vehicle_deployment.png"), dpi=200)
    plt.close(fig)
    print("Saved vehicle_deployment.png")


def main():
    footfall = load_data()
    print(f"Loaded {len(footfall)} zones")
    print(f"Total waste: {footfall['waste_kg_total'].sum():.0f} kg/day")

    # Base scenario
    r_base = solve_logistics(footfall, waste_multiplier=1.0, label="Base")
    print_results(r_base)
    make_sankey_data(r_base)

    # Sensitivity: +20% waste
    r_sens = solve_logistics(footfall, waste_multiplier=1.2, label="+20% Waste")
    print_results(r_sens)
    make_sankey_data(r_sens)

    if r_base and r_sens:
        delta = r_sens["total_cost"] - r_base["total_cost"]
        pct = delta / r_base["total_cost"] * 100
        print(f"\nSensitivity Impact: Δ cost = ₹{delta:,.0f} ({pct:+.1f}%)")

        extra_vehicles = sum(r_sens["vehicles"][t] - r_base["vehicles"][t] for t in WASTE_TYPES)
        print(f"Additional vehicles needed: {extra_vehicles}")

    make_comparison_chart(r_base, r_sens)
    make_vehicle_chart(r_base, r_sens)

    # Save results
    if r_base:
        with open(os.path.join(OUT_DIR, "logistics_results.json"), "w") as f:
            json.dump({"base": r_base, "sensitivity": r_sens}, f, indent=2, default=str)
        print("Saved logistics_results.json")

    print("\nModule 3.3 complete.")


if __name__ == "__main__":
    main()
