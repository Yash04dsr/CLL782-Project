"""
Module 3.5 — Integrated System-Level Multi-Objective Optimization
=================================================================
Combines Modules 3.2 (bins), 3.3 (logistics), and 3.4 (water stations).

Formulation:
  Decision variables:
    B_bin   — budget allocated to bins (INR)
    B_stn   — budget allocated to water stations (INR)
    (logistics cost is operationally fixed, not a capital decision)

  Shared constraint:
    B_bin + B_stn <= B_total   (global sustainability fund)

  Three objectives (weighted-sum scalarisation):
    C_sys = B_bin + B_stn + C_logistics    (economic cost)
    E_sys = f(bins, logistics, stations)    (kg CO2e)
    I_sys = g(bins, stations)              (user inconvenience)

  For each weight vector (w1, w2, w3):
    min  w1 * C_norm + w2 * E_norm + w3 * I_norm
    s.t. B_bin + B_stn <= B_total

Uses scipy.optimize.minimize over the budget-partition space.
"""

import os, json, time
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(OUT_DIR), "grid_data")

# ── Constants from individual modules ──
BIN_COSTS = {"compostable": 10_000, "recyclable": 8_000, "general": 6_000}
WEIGHTED_AVG_BIN_COST = (10_000 * 0.4 + 8_000 * 0.4 + 6_000 * 0.2)  # ₹8,800
STATION_COST = 100_000
LOGISTICS_COST_FIXED = 1_001_350  # from Module 3.3 base optimal

B_TOTAL = 85_00_000  # ₹85 Lakhs total sustainability fund

# Bin parameters (from Module 3.2)
WASTE_TOTAL_KG = 6_000
BIN_AVG_CAPACITY_KG = (20 * 0.4 + 15 * 0.4 + 10 * 0.2) / 1  # weighted: 16 kg
MIN_BINS_CAPACITY = int(np.ceil(WASTE_TOTAL_KG / BIN_AVG_CAPACITY_KG))  # ~375

# Station parameters (from Module 3.4)
TOTAL_WATER_DEMAND_LPH = 10_000
STATION_CAPACITY_LPH = 250
MIN_STATIONS_CAPACITY = int(np.ceil(TOTAL_WATER_DEMAND_LPH / STATION_CAPACITY_LPH))  # 40

# Environmental impact factors (kg CO2e)
CO2_PER_BIN = 5.0
CO2_PER_STATION = 50.0
CO2_LANDFILL_PER_KG = 1.2
CO2_COMPOST_PER_KG = 0.3
CO2_RECYCLE_PER_KG = -0.5
# Waste routing: 500kg compost, 2400kg recycle, 3100kg landfill (from corrected 3.3)
CO2_LOGISTICS_BASE = (500 * CO2_COMPOST_PER_KG +
                      2400 * CO2_RECYCLE_PER_KG +
                      3100 * CO2_LANDFILL_PER_KG)  # base logistics CO2

# Walking inconvenience reference (from Module 3.2 MILP at full budget)
INCONV_BIN_REF = 93_209      # obj value at 436 bins (full Module 3.2 solution)
N_BINS_REF = 436
INCONV_STN_REF = 60_065      # walk cost at 40 stations (Module 3.4)
N_STATIONS_REF = 40


def compute_objectives(B_bin, B_stn):
    """
    Given budget allocation, compute the three system objectives.
    This is the sub-problem evaluation: for a given budget split,
    determine how many bins/stations can be procured and their impact.
    """
    n_bins = max(MIN_BINS_CAPACITY, int(B_bin / WEIGHTED_AVG_BIN_COST))
    n_stations = max(MIN_STATIONS_CAPACITY, int(B_stn / STATION_COST))

    # C_sys: total economic cost (actual spending)
    actual_bin_spend = n_bins * WEIGHTED_AVG_BIN_COST
    actual_stn_spend = n_stations * STATION_COST
    C_sys = actual_bin_spend + actual_stn_spend + LOGISTICS_COST_FIXED

    # E_sys: environmental cost
    # More bins = better source segregation = more recycling, less landfill
    segregation_efficiency = min(1.0, n_bins / MIN_BINS_CAPACITY)
    compost_flow = 500  # biogas cap is fixed at 500 kg
    recycle_flow = 2400 * segregation_efficiency
    landfill_flow = WASTE_TOTAL_KG - compost_flow - recycle_flow

    E_sys = (n_bins * CO2_PER_BIN +
             n_stations * CO2_PER_STATION +
             compost_flow * CO2_COMPOST_PER_KG +
             recycle_flow * CO2_RECYCLE_PER_KG +
             landfill_flow * CO2_LANDFILL_PER_KG)

    # I_sys: user inconvenience (walking distance to bins + to stations)
    # Scales inversely with number of facilities (more bins/stations = less walking)
    bin_inconv = INCONV_BIN_REF * (N_BINS_REF / max(n_bins, 1))
    stn_inconv = INCONV_STN_REF * (N_STATIONS_REF / max(n_stations, 1))
    I_sys = bin_inconv + stn_inconv

    return C_sys, E_sys, I_sys


def solve_weighted_sum(w1, w2, w3, C_range, E_range, I_range):
    """
    Solve: min w1*C_norm + w2*E_norm + w3*I_norm
    s.t.   B_bin + B_stn <= B_total, B_bin >= 0, B_stn >= 0
    """
    def objective(x):
        B_bin, B_stn = x
        C, E, I = compute_objectives(B_bin, B_stn)
        C_norm = (C - C_range[0]) / max(C_range[1] - C_range[0], 1)
        E_norm = (E - E_range[0]) / max(E_range[1] - E_range[0], 1)
        I_norm = (I - I_range[0]) / max(I_range[1] - I_range[0], 1)
        return w1 * C_norm + w2 * E_norm + w3 * I_norm

    min_bin_budget = MIN_BINS_CAPACITY * WEIGHTED_AVG_BIN_COST
    min_stn_budget = MIN_STATIONS_CAPACITY * STATION_COST
    constraints = [{"type": "ineq", "fun": lambda x: B_TOTAL - x[0] - x[1]}]
    bounds = [(min_bin_budget, B_TOTAL - min_stn_budget),
              (min_stn_budget, B_TOTAL - min_bin_budget)]

    best_result = None
    best_obj = np.inf
    # Multi-start to avoid local minima
    for b_frac in [0.2, 0.4, 0.5, 0.6, 0.8]:
        x0 = [B_TOTAL * b_frac, B_TOTAL * (1 - b_frac) * 0.8]
        res = minimize(objective, x0, method="SLSQP", bounds=bounds,
                       constraints=constraints)
        if res.success and res.fun < best_obj:
            best_obj = res.fun
            best_result = res

    return best_result


def main():
    print("Module 3.5: Integrated System-Level Optimization")
    print("=" * 60)
    print(f"Global Budget: Rs. {B_TOTAL/1e5:.0f} Lakhs")
    print(f"Logistics cost (fixed from Mod 3.3): Rs. {LOGISTICS_COST_FIXED:,}")
    print(f"Available for bins + stations: Rs. {(B_TOTAL - LOGISTICS_COST_FIXED)/1e5:.1f} Lakhs\n")

    # Compute normalization ranges by sampling the feasible space
    min_bin_budget = MIN_BINS_CAPACITY * WEIGHTED_AVG_BIN_COST
    min_stn_budget = MIN_STATIONS_CAPACITY * STATION_COST
    available = B_TOTAL - min_bin_budget - min_stn_budget

    all_C, all_E, all_I = [], [], []
    configs = []
    for b_frac in np.linspace(0.0, 1.0, 50):
        B_bin = min_bin_budget + available * b_frac
        B_stn = min_stn_budget + available * (1 - b_frac)
        C, E, I = compute_objectives(B_bin, B_stn)
        all_C.append(C)
        all_E.append(E)
        all_I.append(I)
        n_bins = max(1, int(B_bin / WEIGHTED_AVG_BIN_COST))
        n_stns = max(1, int(B_stn / STATION_COST))
        configs.append({
            "b_frac": round(b_frac, 3),
            "B_bin": B_bin, "B_stn": B_stn,
            "n_bins": n_bins, "n_stations": n_stns,
            "C_sys": C, "E_sys": E, "I_sys": I,
        })

    C_range = (min(all_C), max(all_C))
    E_range = (min(all_E), max(all_E))
    I_range = (min(all_I), max(all_I))

    configs_df = pd.DataFrame(configs)
    print("Feasible Space Extremes:")
    print(f"  C_sys: Rs. {C_range[0]/1e5:.1f}L — Rs. {C_range[1]/1e5:.1f}L")
    print(f"  E_sys: {E_range[0]:,.0f} — {E_range[1]:,.0f} kg CO₂e")
    print(f"  I_sys: {I_range[0]:,.0f} — {I_range[1]:,.0f}\n")

    # Pareto frontier: filter non-dominated configs
    pareto = []
    for idx, row in configs_df.iterrows():
        dominated = False
        for _, other in configs_df.iterrows():
            if (other["C_sys"] <= row["C_sys"] and
                other["E_sys"] <= row["E_sys"] and
                other["I_sys"] <= row["I_sys"] and
                (other["C_sys"] < row["C_sys"] or
                 other["E_sys"] < row["E_sys"] or
                 other["I_sys"] < row["I_sys"])):
                dominated = True
                break
        if not dominated:
            pareto.append(row)
    pareto_df = pd.DataFrame(pareto)
    print(f"Pareto-optimal points: {len(pareto_df)} out of {len(configs_df)}")

    # Weighted-sum sweep
    print("\nWeighted-sum optimisation sweep:")
    sweep_results = []
    weight_sets = []
    n_w = 8
    for w1 in np.linspace(0, 1, n_w):
        for w2 in np.linspace(0, 1 - w1, max(2, n_w)):
            w3 = 1 - w1 - w2
            if w3 >= -0.001:
                weight_sets.append((round(w1, 3), round(w2, 3), round(max(w3, 0), 3)))

    for w1, w2, w3 in weight_sets:
        res = solve_weighted_sum(w1, w2, w3, C_range, E_range, I_range)
        if res and res.success:
            B_bin_opt, B_stn_opt = res.x
            C, E, I = compute_objectives(B_bin_opt, B_stn_opt)
            n_bins = max(1, int(B_bin_opt / WEIGHTED_AVG_BIN_COST))
            n_stns = max(1, int(B_stn_opt / STATION_COST))
            sweep_results.append({
                "w_cost": w1, "w_env": w2, "w_inconv": w3,
                "B_bin": B_bin_opt, "B_stn": B_stn_opt,
                "n_bins": n_bins, "n_stations": n_stns,
                "C_sys": C, "E_sys": E, "I_sys": I,
                "Z": res.fun,
            })

    sweep_df = pd.DataFrame(sweep_results)
    print(f"  Sweep points computed: {len(sweep_df)}")

    # Print key operating points
    print(f"\n{'='*70}")
    print("KEY OPERATING POINTS")
    print(f"{'='*70}")

    # Minimum cost
    mc = sweep_df.loc[sweep_df["C_sys"].idxmin()]
    print(f"\n  [Min Cost]  w=(1,0,0)")
    print(f"    Bins: {mc['n_bins']:.0f}, Stations: {mc['n_stations']:.0f}")
    print(f"    C=Rs.{mc['C_sys']/1e5:.1f}L, E={mc['E_sys']:.0f} kgCO2e, I={mc['I_sys']:.0f}")

    # Minimum environmental
    me = sweep_df.loc[sweep_df["E_sys"].idxmin()]
    print(f"\n  [Min Environment]  w=(0,1,0)")
    print(f"    Bins: {me['n_bins']:.0f}, Stations: {me['n_stations']:.0f}")
    print(f"    C=Rs.{me['C_sys']/1e5:.1f}L, E={me['E_sys']:.0f} kgCO2e, I={me['I_sys']:.0f}")

    # Minimum inconvenience
    mi = sweep_df.loc[sweep_df["I_sys"].idxmin()]
    print(f"\n  [Min Inconvenience]  w=(0,0,1)")
    print(f"    Bins: {mi['n_bins']:.0f}, Stations: {mi['n_stations']:.0f}")
    print(f"    C=Rs.{mi['C_sys']/1e5:.1f}L, E={mi['E_sys']:.0f} kgCO2e, I={mi['I_sys']:.0f}")

    # Balanced (w ≈ 1/3 each)
    # Find the point closest to equal weights (1/3, 1/3, 1/3)
    sweep_df["dist_to_equal"] = ((sweep_df["w_cost"] - 1/3)**2 +
                                  (sweep_df["w_env"] - 1/3)**2 +
                                  (sweep_df["w_inconv"] - 1/3)**2)
    rec = sweep_df.loc[sweep_df["dist_to_equal"].idxmin()]
    print(f"\n  [RECOMMENDED — Balanced]  w=({rec['w_cost']:.2f},{rec['w_env']:.2f},{rec['w_inconv']:.2f})")
    print(f"    Bins: {rec['n_bins']:.0f}, Stations: {rec['n_stations']:.0f}")
    print(f"    Budget: bins Rs.{rec['B_bin']/1e5:.1f}L + stations Rs.{rec['B_stn']/1e5:.1f}L")
    print(f"    C=Rs.{rec['C_sys']/1e5:.1f}L, E={rec['E_sys']:.0f} kgCO2e, I={rec['I_sys']:.0f}")

    # ── Plots ──
    # 1. Pareto frontier (2D: Cost vs Environment, Cost vs Inconvenience)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    ax = axes[0]
    ax.scatter(configs_df["C_sys"] / 1e5, configs_df["E_sys"],
               c="lightgray", s=20, label="Feasible")
    ax.scatter(pareto_df["C_sys"] / 1e5, pareto_df["E_sys"],
               c="red", s=40, zorder=5, label="Pareto front")
    ax.set_xlabel("Economic Cost (Rs. Lakhs)")
    ax.set_ylabel("Environmental Cost (kg CO₂e)")
    ax.set_title("Cost vs Environment")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.scatter(configs_df["C_sys"] / 1e5, configs_df["I_sys"] / 1e3,
               c="lightgray", s=20, label="Feasible")
    ax.scatter(pareto_df["C_sys"] / 1e5, pareto_df["I_sys"] / 1e3,
               c="red", s=40, zorder=5, label="Pareto front")
    ax.set_xlabel("Economic Cost (Rs. Lakhs)")
    ax.set_ylabel("User Inconvenience (×10³)")
    ax.set_title("Cost vs Inconvenience")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    ax.scatter(configs_df["E_sys"], configs_df["I_sys"] / 1e3,
               c="lightgray", s=20, label="Feasible")
    ax.scatter(pareto_df["E_sys"], pareto_df["I_sys"] / 1e3,
               c="red", s=40, zorder=5, label="Pareto front")
    ax.set_xlabel("Environmental Cost (kg CO₂e)")
    ax.set_ylabel("User Inconvenience (×10³)")
    ax.set_title("Environment vs Inconvenience")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.suptitle("Module 3.5: Pareto Frontier — Budget-Constrained Trade-offs",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "pareto_frontier_3d.png"), dpi=200)
    plt.close(fig)
    print("\nSaved pareto_frontier_3d.png")

    # 2. Budget allocation vs objectives
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    fracs = configs_df["b_frac"]
    ax1.plot(fracs, configs_df["E_sys"], "g-o", ms=3, label="E_sys (CO₂e)")
    ax1.set_xlabel("Fraction of Budget → Bins")
    ax1.set_ylabel("Environmental Cost (kg CO₂e)", color="green")
    ax1.tick_params(axis="y", labelcolor="green")
    ax1b = ax1.twinx()
    ax1b.plot(fracs, configs_df["I_sys"] / 1e3, "b-s", ms=3, label="I_sys")
    ax1b.set_ylabel("User Inconvenience (×10³)", color="blue")
    ax1b.tick_params(axis="y", labelcolor="blue")
    ax1.set_title("Budget Partition Effect on Objectives")
    ax1.grid(True, alpha=0.3)

    # Stacked budget allocation for the recommended point
    labels = ["Bins", "Stations", "Logistics"]
    values = [rec["B_bin"], rec["B_stn"], LOGISTICS_COST_FIXED]
    colors = ["#2ca02c", "#1f77b4", "#ff7f0e"]
    ax2.pie(values, labels=[f"{l}\nRs.{v/1e5:.1f}L" for l, v in zip(labels, values)],
            autopct="%1.0f%%", colors=colors, startangle=90)
    ax2.set_title(f"Recommended Budget Allocation\n(Total: Rs. {sum(values)/1e5:.1f}L)")

    fig.suptitle("Module 3.5: Budget Allocation Analysis", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "tradeoff_2d.png"), dpi=200)
    plt.close(fig)
    print("Saved tradeoff_2d.png")

    # Save results
    summary = {
        "formulation": {
            "decision_variables": ["B_bin (budget for bins)", "B_stn (budget for stations)"],
            "constraint": f"B_bin + B_stn <= Rs. {B_TOTAL:,} (shared budget)",
            "objectives": ["C_sys (economic cost)", "E_sys (CO2e)", "I_sys (inconvenience)"],
            "method": "Weighted-sum scalarisation with scipy SLSQP",
        },
        "pareto_points": len(pareto_df),
        "recommended": {
            "weights": {"cost": float(rec["w_cost"]), "env": float(rec["w_env"]),
                        "inconv": float(rec["w_inconv"])},
            "B_bin": float(rec["B_bin"]), "B_stn": float(rec["B_stn"]),
            "n_bins": int(rec["n_bins"]), "n_stations": int(rec["n_stations"]),
            "C_sys": float(rec["C_sys"]),
            "E_sys": float(rec["E_sys"]),
            "I_sys": float(rec["I_sys"]),
        },
    }
    with open(os.path.join(OUT_DIR, "integrated_results.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved integrated_results.json")

    print(f"\n{'='*60}")
    print("Module 3.5 complete.")


if __name__ == "__main__":
    main()
