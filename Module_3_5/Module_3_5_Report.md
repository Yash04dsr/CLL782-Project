
# Process Optimization Project Report
## Module 3.5: Integrated System-Level Model for Sustainable "Rendezvous"

**Your Name**  
**Entry Number:** 202XXXXX  
**Department of Chemical Engineering, IIT Delhi**  
**February 17, 2026**

### Declaration of Tool Usage
I declare that in completing this assignment:
* I used an LLM-based tool (Gemini) for assistance in:
    - Integrating sub-models from Modules 3.2, 3.3, and 3.4.
    - Formulating the multi-objective optimization problem (Weighted Sum Method).
    - Formatting the report in LaTeX/Markdown.
* I understand the submitted solution fully.
* I can explain and justify every part of my code and reasoning.
* I have verified all results independently.

---

### Contents
1. **Introduction**
2. **Nomenclature**
3. **Assumptions and Justifications**
4. **Mathematical Model Formulation**
    - 4.1 Unified Objective Function
    - 4.2 Integrated Constraints
5. **Optimization Analysis**
    - 5.1 Trade-off Analysis (Pareto Optimality)
    - 5.2 Computational Complexity
6. **Preliminary Insights and Discussion**
7. **References**

---

### 1. Introduction
The previous modules addressed individual components of the festival's sustainability infrastructure: dustbin placement (3.2), waste logistics (3.3), and water refill stations (3.4). Module 3.5 integrates these into a unified system-level optimization model. The goal is to simultaneously minimize economic costs, environmental impact, and user inconvenience. This holistic approach captures the interdependencies between subsystems—for example, optimal bin placement affects collection logistics, and budget constraints link all infrastructure investments.

### 2. Nomenclature
The model aggregates nomenclature from previous modules. Key system-level variables are defined in Table 1.

**Table 1: Integrated Nomenclature Table**

| Symbol | Description | Units | Type |
| :--- | :--- | :--- | :--- |
| $i$ | Index for demand zones, $i \in \{1, \dots, m\}$ | - | Index |
| $j_{bin}$ | Index for candidate bin locations | - | Index |
| $j_{refill}$ | Index for candidate refill station locations | - | Index |
| $j_{proc}$ | Index for waste processing facilities | - | Index |
| $t$ | Waste stream (Wet, Dry) | - | Index |
| $C_{sys}$ | Total Economic Cost of System | INR | Obj Component |
| $E_{sys}$ | Total Environmental Impact | kg CO2e | Obj Component |
| $I_{sys}$ | Total User Inconvenience (Walking Distance) | person-m | Obj Component |
| $w_1, w_2, w_3$ | Weights for multi-objective scalarization | - | Parameter |
| $y^{bin}_{j}$ | Binary: Install dual-bin at $j$ | - | Decision Var |
| $y^{refill}_j$ | Binary: Install refill station at $j$ | - | Decision Var |
| $x^{waste}_{i,j}$ | Waste flow from zone $i$ to facility $j$ | kg | Decision Var |
| $B_{total}$ | Global Budget for all sustainability initiatives | INR | Parameter |

### 3. Assumptions and Justifications
1.  **A1: Additive Objectives.**
    *   **Justification:** We assume the global objective can be represented as a weighted sum of normalized individual objectives. This allows us to convert the multi-objective problem into a single-objective problem solvable by standard MILP solvers.
2.  **A2: Independent Demand.**
    *   **Justification:** We assume the demand for water ($d_i$) and waste generation ($F_i$) are spatially correlated but functionally independent (i.e., placing a bin does not change water demand).
3.  **A3: Shared Budget.**
    *   **Justification:** Funds for bins, refill stations, and logistics come from a single "Green Fund". This creates a hard trade-off: spending more on expensive compost bins implies fewer water stations or cheaper waste disposal methods.

### 4. Mathematical Model Formulation

The problem is a **Multi-Objective Mixed-Integer Linear Program (MO-MILP)**.

#### 4.1 Unified Objective Function
We minimize a weighted sum of three competing goals:

1.  **Economic Cost ($C_{sys}$):**
    $$ C_{sys} = \sum C \cdot y^{bin} + \sum C_{install} \cdot y^{refill} + \sum C_{trans} \cdot x^{waste} + C_{fixed} \cdot N_{veh} $$
    *(Terms represent: Bins + Refill Stations + Logistics + Fleet)*

2.  **Environmental Cost ($E_{sys}$):**
    $$ E_{sys} = \sum E_{material} \cdot y^{bin} + \sum E_{process} \cdot x^{waste} + E_{transport} \cdot \sum \text{dist} \cdot x^{waste} $$
    *Note: Recycling reduces $E_{process}$ (negative cost), while landfilling increases it.*

3.  **User Inconvenience ($I_{sys}$):**
    $$ I_{sys} = \sum d_i \cdot \text{dist} \cdot x^{assign}_{bin} + \sum d_i \cdot \text{dist} \cdot x^{assign}_{refill} $$
    *(Terms represent: Walking to Bins + Walking to Water)*

**Global Objective:**
$$ \text{Minimize } Z = w_1 \cdot \frac{C_{sys}}{C_{scale}} + w_2 \cdot \frac{E_{sys}}{E_{scale}} + w_3 \cdot \frac{I_{sys}}{I_{scale}} $$
Where $C_{scale}, E_{scale}, I_{scale}$ are normalization factors to make objectives comparable.

#### 4.2 Integrated Constraints

**1. Global Budget Constraint:**
$$ C_{sys} \le B_{total} $$
This single constraint couples all three subsystems. A valid solution must optimize infrastructure within this limit.

**2. Physical Constraints (From Modules 3.2, 3.3, 3.4):**
*   **Coverage:** Every zone must be served by a bin and a water station.
*   **Capacity:** Waste flows $\le$ Bin Capacity; Water demand $\le$ Station Capacity.
*   **Flow Conservation:** Waste collected = Waste transported = Waste processed.
    $$ \sum_{j_{bin}} \text{Collected}_{i,j} = W_i = \sum_{j_{proc}} x^{waste}_{i,j} $$

### 5. Optimization Analysis

#### 5.1 Trade-off Analysis (Pareto Optimality)
Since the objectives conflict, no single "optimal" solution exists.
*   **Cost vs. Convenience:** Increasing $w_3$ (valuing convenience) drives the installation of more bins and stations, increasing $C_{sys}$ until the Budget constraint is hit.
*   **Cost vs. Environment:** Increasing $w_2$ shifts waste processing from cheap landfills to expensive recycling/composting, and favors electric vehicles if modeled.

#### 5.2 Computational Complexity
The problem combines two Facility Location Problems (Bins, Refill Stations) with a Network Flow Problem (Logistics).
*   **Variables:** The number of binary variables is the sum of candidate sites for bins and stations.
*   **Coupling:** The main coupling assumes a shared budget. If the budget is partitioned beforehand, the problems decouple and can be solved separately. The shared budget makes it a Knapsack-like resource allocation problem on top of the facility location structure.

### 6. Preliminary Insights and Discussion
*   **Synergy:** Placing bins and water stations at the same location (e.g., "Sustainability Hubs") could reduce installation fixed costs if infrastructure (clearing land, electricity) is shared.
*   **Critical Path:** The budget is the primary bottleneck. If the budget is tight, the system will sacrifice User Convenience first (fewer stations, longer walks) to satisfy the hard constraints of Waste Removal (sanitation cannot be compromised).
*   **Sustainability Premium:** Achieving minimal environmental impact ($E_{sys}$) requires significant investment (high $C_{sys}$). The "Green Premium" is the extra cost required to move from the cheapest solution (Landfill + Min Bins) to the greenest solution (Recycling + Max Coverage).

### 7. References
1.  Deb, K. (2001). *Multi-Objective Optimization using Evolutionary Algorithms*. Wiley.
2.  Ehrgott, M. (2005). *Multicriteria Optimization*. Springer.
