
# Process Optimization Project Report
## Module 3.3: Waste Collection and Processing Logistics

**Your Name**  
**Entry Number:** 202XXXXX  
**Department of Chemical Engineering, IIT Delhi**  
**February 17, 2026**

### Declaration of Tool Usage
I declare that in completing this assignment:
* I used an LLM-based tool (Gemini) for assistance in:
    - Formulating the Vehicle Routing Problem (VRP) variants.
    - Structuring the optimization model for logistics.
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
    - 4.1 Objective Function Construction
    - 4.2 Constraints Integration
5. **Optimization Analysis**
    - 5.1 Complexity and Convexity
    - 5.2 Sensitivity Analysis Strategy
6. **Preliminary Insights and Discussion**
7. **References**

---

### 1. Introduction
Efficient waste management for the "Rendezvous" festival requires a robust logistics network to transport waste from generation zones to processing facilities (recycling units, compost pits, landfills). Module 3.3 addresses this challenge by modeling a waste collection and processing system. The objective is to minimize total operational costs, including transportation and processing, while respecting vehicle capacities, facility throughput limits, and waste supply constraints.

### 2. Nomenclature
The variables and parameters used in the mathematical model are defined in Table 1.

**Table 1: Nomenclature Table**

| Symbol | Description | Units | Type |
| :--- | :--- | :--- | :--- |
| $i$ | Index for waste generation zones, $i \in \{1, \dots, m\}$ | - | Index |
| $j$ | Index for processing facilities, $j \in \{1, \dots, p\}$ | - | Index |
| $k$ | Index for vehicles, $k \in \{1, \dots, K\}$ | - | Index |
| $W_i$ | Total waste generated in zone $i$ | kg | Parameter |
| $Cap_j$ | Throughput capacity of facility $j$ | kg | Parameter |
| $V_{cap}$ | Capacity of a single waste collection vehicle | kg | Parameter |
| $C_{proc,j}$ | Unit processing cost at facility $j$ | INR/kg | Parameter |
| $D_{ij}$ | Distance from zone $i$ to facility $j$ | km | Parameter |
| $C_{dist}$ | Transport cost per km | INR/km | Parameter |
| $C_{handling}$ | Handling cost per kg | INR/kg | Parameter |
| $C_{fixed}$ | Fixed cost per vehicle used | INR | Parameter |
| $x_{i,j}$ | Waste quantity transported from zone $i$ to facility $j$ | kg | Decision Var |
| $v_k$ | Binary: 1 if vehicle $k$ is deployed, 0 otherwise | - | Decision Var |
| $Z_{total}$ | Total Cost (Transport + Processing + Fixed) | INR | Objective Fn |

### 3. Assumptions and Justifications
1.  **A1: Direct Transport Model.**
    *   **Justification:** For simplicity in this module, we model direct transport from zones to facilities (Star network) rather than a complex multi-stop vehicle routing problem (VRP). The "route" variable mentioned in the problem statement is approximated by aggregate flow $x_{i,j}$.
    *   *Note:* A full VRP formulation would require variables $x_{i,j,k}$ indicating if vehicle $k$ travels from node $i$ to $j$, which scales exponentially. The direct flow approximation provides a lower bound on cost and is tractable.
2.  **A2: Homogeneous Fleet.**
    *   **Justification:** All vehicles are assumed to have identical capacity $V_{cap}$ and costs.
3.  **A3: Linear Costs.**
    *   **Justification:** Transportation and processing costs scale linearly with distance and mass, respectively.

### 4. Mathematical Model Formulation

The problem is modeled as a **Minimum Cost Flow Problem** with fixed costs for vehicle deployment.

#### 4.1 Objective Function Construction
We minimize the Total Cost ($Z_{total}$), comprising:
1.  **Transportation Cost:** Function of distance and weight.
    $$ C_{trans} = \sum_{i=1}^m \sum_{j=1}^p x_{i,j} \cdot (C_{dist} \cdot D_{ij} + C_{handling}) $$
2.  **Processing Cost:** At facilities.
    $$ C_{proc} = \sum_{i=1}^m \sum_{j=1}^p x_{i,j} \cdot C_{proc,j} $$
3.  **Vehicle Fixed Cost:** Based on the number of vehicles required.
    $$ C_{veh} = N_{vehicles} \cdot C_{fixed} $$
    Where $N_{vehicles}$ is determined by the total waste volume divided by vehicle capacity (approximate).

**Combined Objective:**
$$ Z = \sum_{i,j} x_{i,j} (C_{dist} D_{ij} + C_{handling} + C_{proc,j}) + C_{fixed} \cdot \lceil \frac{\sum_{i,j} x_{i,j}}{V_{cap}} \rceil $$

To linearize the vehicle count for optimization:
$$ Z = \sum_{i,j} C_{ij}^{total} \cdot x_{i,j} + C_{fixed} \cdot \sum_{k} v_k $$

#### 4.2 Constraints Integration

**1. Waste Clearance (Supply Constraint):**
All waste from zone $i$ must be removed.
$$ \sum_{j=1}^p x_{i,j} = W_i, \quad \forall i $$

**2. Facility Capacity:**
Total waste sent to facility $j$ cannot exceed its throughput.
$$ \sum_{i=1}^m x_{i,j} \le Cap_j, \quad \forall j $$

**3. Vehicle Capacity (Fleet Sizing):**
The total waste transported must be covered by the deployed fleet.
$$ \sum_{i=1}^m \sum_{j=1}^p x_{i,j} \le \sum_{k=1}^K v_k \cdot V_{cap} $$
Or simply, defining $N$ as integer variable for number of vehicles:
$$ \sum_{i,j} x_{i,j} \le N \cdot V_{cap} $$

**4. Non-negativity:**
$$ x_{i,j} \ge 0, \quad N \in \mathbb{Z}_{\ge 0} $$

### 5. Optimization Analysis

#### 5.1 Complexity
The core transport problem is a **Linear Programming (LP)** transportation problem, which is totally unimodular and solvable in polynomial time. The integer constraint on the number of vehicles ($N$) makes it a **Mixed-Integer Linear Program (MILP)**, but since $N$ is a single scalar variable linked to the total sum, the complexity remains very low compared to VRP.

#### 5.2 Sensitivity Analysis Strategy (Part e)
To analyze the impact of a 20% increase in waste generation:
1.  Update parameter: $W_i' = 1.2 \times W_i$.
2.  Check Feasibility:
    $$ \sum W_i' \le \sum Cap_j $$
    If total waste exceeds total facility capacity, the problem becomes infeasible, indicating a need for simpler disposal methods (landfill expansion).
3.  Cost Impact:
    Calculate $\Delta Z = Z_{new} - Z_{old}$.
    Since variable costs are linear, we expect a roughly linear increase in operational costs, but the "step function" of vehicle fixed costs ($C_{fixed}$) might trigger the need for an additional vehicle, causing a discontinuous jump in total cost.

### 6. Preliminary Insights and Discussion
*   **Facility Selection:** The solver will instinctively route waste to the nearest facility with the lowest processing cost. If recycling usually has lower $C_{proc}$ (or even revenue) but is further away, a trade-off radius exists.
*   **Bottlenecks:** The most constrained resource is likely the processing capacity of "green" facilities (compost/recycling). Once these fill up, the model will be forced to route excess waste to landfills, increasing the environmental penalty (if modeled).
*   **Fleet Utilization:** The fixed cost of vehicles encourages maximizing the load per vehicle. A 20% increase in waste might be absorbed by existing fleet slack or might require a strictly new vehicle purchase.

### 7. References
1.  Toth, P., & Vigo, D. (2014). *Vehicle Routing: Problems, Methods, and Applications*. SIAM.
2.  Golden, B. L., Raghavan, S., & Wasil, E. A. (2008). *The Vehicle Routing Problem: Latest Advances and New Challenges*. Springer.
