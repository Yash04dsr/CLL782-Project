"""
Module 3.1 — Environmental Load Model: Numerical Optimization
=============================================================
Defines E = f(N, S, A) and finds optimal event configuration
that minimizes total ecological footprint.

Uses the 287-cell grid data for spatially-resolved analysis.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Model constants (from ppt.tex and literature) ──
ALPHA1 = 2.5      # per-capita base impact (kg CO2e / person)
ALPHA2 = 18.0     # per-stall embodied energy (kg CO2e / stall)
ALPHA3 = 12.0     # per-activity base impact (kg CO2e / activity-hr)
BETA_N = 0.002    # crowding nonlinearity coefficient
BETA_S = 0.5      # stall scaling coefficient
BETA_A = 5.0      # activity scaling coefficient
GAMMA_NS = 0.0005 # congestion penalty coefficient
EXP_N = 1.3
EXP_S = 1.2
EXP_A = 0.8


def env_load(N, S, A):
    """Compute total environmental load E(N, S, A)."""
    base = ALPHA1 * N + ALPHA2 * S + ALPHA3 * A
    nonlinear = BETA_N * N**EXP_N + BETA_S * S**EXP_S + BETA_A * A**EXP_A
    congestion = GAMMA_NS * N**2 / max(S, 1)
    return base + nonlinear + congestion


def env_load_vec(x):
    return env_load(x[0], x[1], x[2])


def optimal_S_fixed_N(N):
    """Analytical S* for given N: from dE/dS = 0 approximation."""
    return N * np.sqrt(GAMMA_NS / ALPHA2)


def main():
    footfall = pd.read_csv("grid_data/footfall_density.csv")
    N_peak = 40_000

    # ── 1. Optimal S* at fixed N = 40,000 ──
    S_star_analytical = optimal_S_fixed_N(N_peak)
    print(f"Analytical S* (N={N_peak}): {S_star_analytical:.0f} stalls")

    # Numerical verification: minimise E w.r.t. S only
    res_S = minimize_scalar(lambda s: env_load(N_peak, s, 50),
                            bounds=(10, 1000), method="bounded")
    print(f"Numerical  S* (N={N_peak}): {res_S.x:.0f} stalls, E = {res_S.fun:.0f} kg CO2e")

    # ── 2. Full unconstrained minimization of E(N, S, A) ──
    x0 = [20000, 150, 50]
    bounds = [(1000, 60000), (10, 1000), (5, 200)]
    res = minimize(env_load_vec, x0, method="L-BFGS-B", bounds=bounds)
    N_opt, S_opt, A_opt = res.x
    E_opt = res.fun
    print(f"\nUnconstrained Optimum (bounded search):")
    print(f"  N* = {N_opt:.0f} persons")
    print(f"  S* = {S_opt:.0f} stalls")
    print(f"  A* = {A_opt:.1f} activity-hrs")
    print(f"  E* = {E_opt:.0f} kg CO2e")

    # ── 3. Plot: E vs S at fixed N ──
    S_range = np.linspace(20, 600, 500)
    E_vs_S = [env_load(N_peak, s, 50) for s in S_range]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(S_range, E_vs_S, "b-", lw=2)
    ax.axvline(res_S.x, color="r", ls="--", label=f"S* = {res_S.x:.0f}")
    ax.set_xlabel("Number of Food Stalls (S)")
    ax.set_ylabel("Environmental Load E (kg CO₂-eq)")
    ax.set_title(f"E vs S  (N = {N_peak:,}, A = 50 activity-hrs)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "E_vs_S.png"), dpi=200)
    plt.close(fig)
    print("Saved E_vs_S.png")

    # ── 4. Plot: E vs N at optimal S(N) ──
    N_range = np.linspace(5000, 60000, 500)
    E_vs_N = [env_load(n, optimal_S_fixed_N(n), 50) for n in N_range]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(N_range, E_vs_N, "g-", lw=2)
    ax.axvline(N_peak, color="r", ls="--", label=f"N = {N_peak:,} (design)")
    ax.set_xlabel("Number of Attendees (N)")
    ax.set_ylabel("Environmental Load E (kg CO₂-eq)")
    ax.set_title("E vs N  (S = S*(N), A = 50 activity-hrs)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "E_vs_N.png"), dpi=200)
    plt.close(fig)
    print("Saved E_vs_N.png")

    # ── 5. 3D Surface: E(N, S) at fixed A ──
    N_grid = np.linspace(5000, 50000, 80)
    S_grid = np.linspace(20, 500, 80)
    NN, SS = np.meshgrid(N_grid, S_grid)
    EE = np.vectorize(lambda n, s: env_load(n, s, 50))(NN, SS)

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(NN, SS, EE, cmap="viridis", alpha=0.85, edgecolor="none")
    ax.set_xlabel("Attendees N")
    ax.set_ylabel("Stalls S")
    ax.set_zlabel("E (kg CO₂-eq)")
    ax.set_title("Environmental Load Surface E(N, S) at A=50")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "E_surface_NS.png"), dpi=200)
    plt.close(fig)
    print("Saved E_surface_NS.png")

    # ── 6. Component breakdown at design point ──
    N, S, A = N_peak, round(res_S.x), 50
    base = ALPHA1 * N + ALPHA2 * S + ALPHA3 * A
    nl_crowd = BETA_N * N**EXP_N
    nl_stall = BETA_S * S**EXP_S
    nl_act = BETA_A * A**EXP_A
    congestion = GAMMA_NS * N**2 / S
    total = base + nl_crowd + nl_stall + nl_act + congestion

    labels = ["Base Load", "Crowding (N^1.3)", "Stall Scaling (S^1.2)",
              "Activity (A^0.8)", "Congestion (N²/S)"]
    values = [base, nl_crowd, nl_stall, nl_act, congestion]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"]
    ax.barh(labels, values, color=colors)
    ax.set_xlabel("kg CO₂-eq")
    ax.set_title(f"E Component Breakdown (N={N:,}, S={S}, A={A})")
    for i, v in enumerate(values):
        ax.text(v + total * 0.01, i, f"{v:,.0f} ({v/total:.1%})", va="center")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "E_breakdown.png"), dpi=200)
    plt.close(fig)
    print("Saved E_breakdown.png")

    # ── 7. Spatial load distribution across 287 cells ──
    per_capita_load = total / N_peak
    footfall["env_load_kg"] = footfall["footfall_persons"] * per_capita_load

    print(f"\nSpatial Environmental Load (287 cells):")
    print(f"  Per-capita load: {per_capita_load:.2f} kg CO2e/person")
    print(f"  Max cell load  : {footfall['env_load_kg'].max():.1f} kg CO2e")
    print(f"  Total load     : {footfall['env_load_kg'].sum():.0f} kg CO2e")
    print(f"\n{'='*50}")
    print("Module 3.1 complete.")


if __name__ == "__main__":
    main()
