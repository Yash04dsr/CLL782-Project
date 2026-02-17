# Process Optimization Project Report
## Module 3.2: Dustbin Placement and Accessibility for Sustainable "Rendezvous"

**Your Name**  
**Entry Number:** 202XXXXX  
**Department of Chemical Engineering, IIT Delhi**  
**February 17, 2026**

### Declaration of Tool Usage
I declare that in completing this assignment:
* I used an LLM-based tool (Gemini) for assistance in:
    - Structuring the mathematical formulation for the facility location problem.
    - Drafting the report in LaTeX/Markdown format.
    - Analyzing relaxation strategies for mixed-integer programming.
* I understand the submitted solution fully.
* I can explain and justify every part of my code and reasoning.
* I have verified all results independently.

---

### Contents
1. **Introduction**
2. **Nomenclature**
3. **Assumptions and Justifications**
4. **Mathematical Model Formulation**
    - 4.1 Objective Function Construction
    - 4.2 Constraints Integration
5. **Optimization Analysis**
    - 5.1 Complexity and Convexity
    - 5.2 Relaxation Strategy
6. **Preliminary Insights and Discussion**
7. **References**

---

### 1. Introduction
The "Rendezvous" festival attracts thousands of footfalls, leading to significant waste generation. Inefficient dustbin placement results in littering, overflowing bins, and poor user experience. As part of the Sustainability Task Force, Module 3.2 aims to optimize the placement of waste bins across the IIT Delhi campus. The goal is to minimize the total walking distance for attendees while strictly adhering to budget constraints, service radii, and capacity limits, thereby ensuring a cleaner and more sustainable festival.

### 2. Nomenclature
The variables and parameters used in the mathematical model are defined in Table 1.

**Table 1: Nomenclature Table**

| Symbol | Description | Units | Type |
| :--- | :--- | :--- | :--- |
| $i$ | Index for zones (demand points), $i \in \{1, \dots, m\}$ | - | Index |
| $j$ | Index for candidate bin locations, $j \in \{1, \dots, p\}$ | - | Index |
| $t$ | Index for bin type (recyclable, compostable, general) | - | Index |
| $F_i$ | Footfall density in zone $i$ | persons/hr | Parameter |
| $D_{ij}$ | Distance between zone center $i$ and candidate location $j$ | meters | Parameter |
| $C_t$ | Cost of installing bin type $t$ | INR | Parameter |
| $R_t$ | Service radius of bin type $t$ | meters | Parameter |
| $K_t$ | Capacity of bin type $t$ | kg | Parameter |
| $w$ | Average waste generation per person | kg/person | Parameter |
| $B$ | Total Budget | INR | Parameter |
| $y_{j,t}$ | Binary decision: 1 if bin $t$ is placed at $j$, 0 otherwise | - | Decision Var |
| $a_{i,j,t}$ | Fraction of footfall from zone $i$ assigned to bin $j$ of type $t$ | - | Decision Var |
| $Z$ | Total Weighted Walking Distance | person-meters | Objective Fn |

### 3. Assumptions and Justifications
To formulate a tractable optimization model, the following assumptions are made:

1.  **A1: Centroid Approximation.**
    *   **Justification:** Zones are treated as point sources of waste generation located at their geometric centroids. This simplifies distance calculations ($D_{ij}$) without significant loss of accuracy for small zones.
2.  **A2: Uniform Waste Generation.**
    *   **Justification:** Waste generation is assumed proportional to footfall density ($F_i$). While food stalls may generate more waste, we assume the zoning grid ($i$) is fine enough to capture these high-density areas as distinct zones with higher $F_i$.
3.  **A3: Single Assignment Preference.**
    *   **Justification:** Attendees will generally walk to the single nearest available bin. However, for the mathematical formulation, we allow fractional assignment ($a_{i,j,t}$) to model aggregate crowd behavior and to allow for convex relaxation, which can be interpreted as the probability of a person from zone $i$ using bin $j$.
4.  **A4: Fixed Service Radius.**
    *   **Justification:** Users are unlikely to walk beyond a certain distance to throw away trash. If no bin is within radius $R_t$, littering occurs. We enforce coverage within $R_t$ as a hard constraint to prevent littering.

### 4. Mathematical Model Formulation

The problem is modeled as a **Capacitated Facility Location Problem (CFLP)** with service radius constraints.

#### 4.1 Objective Function Construction
We seek to minimize the total inconvenience to the attendees, quantified as the total walking distance weighted by the number of people.

$$ Z = \sum_{i=1}^{m} \sum_{j=1}^{p} \sum_{t} \left( F_i \cdot a_{i,j,t} \cdot D_{ij} \right) $$

Where $F_i \cdot a_{i,j,t}$ represents the number of people from zone $i$ served by bin $j$ of type $t$.

#### 4.2 Constraints Integration

**1. Demand Satisfaction (Coverage):**
All waste from every zone must be assigned to some bin.
$$ \sum_{j=1}^{p} \sum_{t} a_{i,j,t} = 1, \quad \forall i $$

**2. Logical Link Constraints:**
Waste can only be assigned to location $j$ if a bin is actually placed there.
$$ a_{i,j,t} \le y_{j,t}, \quad \forall i, j, t $$
*(Note: Stronger formulations like $a_{i,j,t} \le y_{j,t}$ are preferred over $\sum_i a_{i,j,t} \le M y_{j,t}$ for tighter relaxation).*

**3. Capacity Constraints:**
The total waste assigned to a bin cannot exceed its capacity.
$$ \sum_{i=1}^{m} (F_i \cdot w \cdot a_{i,j,t}) \le K_t \cdot y_{j,t}, \quad \forall j, t $$

**4. Service Radius / Accessibility:**
Assignments are only valid if the bin is within the service radius.
$$ a_{i,j,t} \cdot D_{ij} \le R_t \cdot a_{i,j,t} $$
Or more simply, restrict the domain of valid $(i,j)$ pairs:
$$ a_{i,j,t} = 0 \quad \text{if } D_{ij} > R_t $$

**5. Budget Constraint:**
Total cost of installed bins must be within budget.
$$ \sum_{j=1}^{p} \sum_{t} C_t \cdot y_{j,t} \le B $$

**6. Domain Restrictions:**
$$ y_{j,t} \in \{0, 1\} $$
$$ 0 \le a_{i,j,t} \le 1 $$

### 5. Optimization Analysis

#### 5.1 Complexity and Convexity
This formulation is a **Mixed-Integer Linear Programming (MILP)** problem.
*   **Linearity:** The objective function and all constraints are linear in terms of decision variables $y$ and $a$.
*   **Non-Convexity:** The binary constraint on $y_{j,t}$ makes the feasible set non-convex (a set of discrete points).
*   **Complexity:** The problem is NP-hard, as it generalizes the Knapsack problem and Facility Location Problem. However, for typical campus sizes ($m \approx 50-100$, $p \approx 200$), modern solvers (Gurobi, CPLEX, CBC) can solve this efficiently.

#### 5.2 Relaxation Strategy
To solve this efficiently or to gain insights into the "ideal" distribution, we can relax the integrality constraint:
$$ 0 \le y_{j,t} \le 1 $$
This transforms the problem into a strictly **Linear Programming (LP)** problem, which is convex and can be solved in polynomial time.
*   **Interpretation:** A fractional $y_{j,t} = 0.5$ physically implies "half a bin" is needed, or a bin is needed 50% of the time.
*   **Rounding:** We can use randomized rounding or establishing a threshold (e.g., if $y_{j,t} > 0.5$, set $y_{j,t} = 1$) to recover a feasible integer solution from the relaxed LP solution.

### 6. Preliminary Insights and Discussion
*   **Trade-off - Cost vs. Convenience:** Tighter budgets ($B$) force fewer bins, increasing average walking distance ($D_{ij}$). The relationship is likely asymptotic: initial investments significantly reduce walking distance, but marginal gains diminish as saturation is reached.
*   **Impact of Service Radius ($R_t$):** A small strict service radius forces a minimum number of bins regardless of capacity. If $R_t$ is too small, the problem may become infeasible for a given budget.
*   **Type Segregation:** If specific waste types (e.g., food waste) are localized to specific zones (food courts), the optimal solution should naturally cluster compostable bins ($t=\text{compostable}$) in those zones, while general bins might be more distributed.
*   **Active Constraints:** In high-density zones, the **Capacity Constraint** will likely be active (binding), requiring multiple bins at the same location. In low-density peripheral zones, the **Service Radius Constraint** will likely dictate placement, leading to under-utilized bins just to satisfy coverage.

### 7. References
1.  Current, J., Daskin, M., & Schilling, D. (2002). *Discrete Network Location Models*. Facility Location: Applications and Theory.
2.  Taha, H. A. (2017). *Operations Research: An Introduction*. Pearson.
3.  Letterman, R.D. (1980). *Economic analysis of granular-bed filtration*. (Cited for general economic optimization context).
