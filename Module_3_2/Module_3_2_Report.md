
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
    - Researching IIT Delhi campus data and standard waste generation norms.
* I understand the submitted solution fully.
* I can explain and justify every part of my code and reasoning.
* I have verified all results independently.

---

### Contents
1. **Introduction**
2. **Nomenclature**
3. **Assumptions and Justifications**
4. **Data Estimation and Context**
5. **Mathematical Model Formulation**
    - 5.1 Objective Function Construction
    - 5.2 Constraints Integration
6. **Optimization Analysis**
7. **References**

---

### 1. Introduction
The "Rendezvous" festival sees a massive influx of visitors, generating significant waste. Module 3.2 focuses on the optimal placement of dustbins to minimize littering and user inconvenience. The problem is modeled as a Facility Location Problem (FLP), balancing the cost of walking (inconvenience) against the budget and capacity constraints of the waste management system.

### 2. Nomenclature
The variables and parameters used in the mathematical model are defined in Table 1.

**Table 1: Nomenclature Table**

| Symbol | Description | Units | Type |
| :--- | :--- | :--- | :--- |
| $i$ | Index for demand zones (footfall locations), $i \in \{1, \dots, m\}$ | - | Index |
| $j$ | Index for candidate bin locations, $j \in \{1, \dots, p\}$ | - | Index |
| $F_i$ | Peak footfall / Demand at zone $i$ | persons/hr | Parameter |
| $D_{ij}$ | Walking distance from zone $i$ to candidate location $j$ | meters | Parameter |
| $C$ | Cost of procuring and installing a dual-bin unit | INR | Parameter |
| $K$ | Capacity of a dual-bin unit (both compartments combined) | kg | Parameter |
| $R$ | Service radius of a bin | meters | Parameter |
| $w$ | Average waste generation rate per person during event | kg/person | Parameter |
| $B$ | Total Budget for dustbins | INR | Parameter |
| $y_{j}$ | Binary decision: 1 if dual-bin is placed at $j$, 0 otherwise | - | Decision Var |
| $a_{i,j}$ | Fraction of footfall in $i$ assigned to bin $j$ | - | Decision Var |
| $Z$ | Total Weighted Walking Distance (User Inconvenience) | person-m | Objective Fn |

### 3. Assumptions and Justifications
1.  **A1: Active Festival Zone (82 Acres).**
    *   **Justification:** While the IIT Delhi campus is ~320 acres [1], the festival activities are concentrated in a specific HIGH-INTENSITY zone of approx. **82 acres** (~26% of campus). This includes the Open Air Theatre (OAT), Nalanda Ground, Main Road axis, Lecture Hall Complex (LHC), Biotech Lawn, Amul area, and Red Square [User Specified]. We model only this dense subset to optimize resources where they are needed most.
2.  **A2: Dual-Compartment Bins (Wet + Dry).**
    *   **Justification:** Per India's Solid Waste Management Rules 2016, waste must be segregated at source into at least two categories: **Wet** (compostable/organic) and **Dry** (recyclable). Each physical bin unit is a dual-compartment FRP/Metal unit with a Green (Wet) and Blue (Dry) compartment. General/reject waste (<5% of total) is handled via periodic collection rounds, not dedicated bins.
3.  **A3: Greenery Protection.**
    *   **Justification:** Significant portions of this 82-acre zone (Biotech Lawn, area in front of LHC) are softscapes. Bins must be placed on **hardscape edges** (roads, paved paths) to prevent trampling of green cover.
4.  **A4: Peak Surge Demand.**
    *   **Justification:** The system is designed for *peak* footfall (Rendezvous attendance ~160,000 over 4 days [2]). We assume a safe design factor where peak hourly load determines capacity, ensuring no overflow during concerts or events.

### 4. Data Estimation and Context (IIT Delhi Specifics)
To ensure the model is grounded in reality, the following well-supported approximations are used for coefficients:

*   **Campus Area Scope:**
    *   **Total Campus:** ~320 Acres [1].
    *   **Modeled Zone:** **82 Acres** (~0.33 km²).
    *   **Key Locations:** OAT, Nalanda Ground, LHC Complex, Red Square, Amul Area.
*   **Footfall ($F_i$):**
    *   **Total Attendees:** ~160,000 over 4 days [2].
    *   **Daily Peak:** ~40,000 visitors/day.
    *   **Zone Concentration:** **100%** of the crowd is assumed to be within the 82-acre hub at peak times (e.g., Star Night), resulting in a peak density of **40,000 people**.
*   **Waste Generation Rate ($w$):**
    *   **Definition:** Average mass of solid waste generated per attendee per visit.
    *   **Justification:** While the national urban average is 0.45 kg/capita/day [3], festival attendees consume significantly more disposables (plates, cups, bottles) in a shorter window.
    *   **Calculation:** Assuming an average stay of 6 hours, 2 meals (0.05 kg food waste each), and 2 beverages (0.025 kg bottles/cups each) = **0.15 kg/person**. This aligns with event management norms for high-traffic food festivals.
    *   **Total Peak Waste:** $40,000 \text{ people} \times 0.15 \text{ kg} = 6,000 \text{ kg/day}$.
*   **Service Radius ($R$):**
    *   **Definition:** The maximum distance a user is willing to walk to find a bin before littering becomes likely.
    *   **Justification:** Disney theme park research suggests a "convenience threshold" of ~30 feet (9m) for zero littering, but for a university campus, a broader range is acceptable. Industry norms suggest 30--50 m spacing [5]. We use a midpoint of **$R = 40$ m**.
    *   **Constraint:** Users must find a bin within this radius; otherwise, the location model is penalized.
*   **Bin Specifications:**
    *   **Type:** Dual-compartment outdoor FRP/Metal bins (Green: Wet, Blue: Dry) per SWM Rules 2016.
    *   **Capacity ($K$):** Standard dual-compartment bins hold approx **30 kg** total (~15 kg per compartment) [4].
    *   **Cost ($C$):** Durable outdoor dual-compartment FRP/Metal bins cost approx **₹12,000** per unit [4].

### 5. Mathematical Model Formulation

The problem is formulated as a mixed-integer linear programming (MILP) model.

#### 5.1 Objective Function Construction
We minimize the Total User Inconvenience ($Z$), defined as the weighted sum of walking distances.
$$ Z = \sum_{i=1}^{m} \sum_{j=1}^{p} \left( F_i \cdot a_{i,j} \cdot D_{ij} \right) $$

#### 5.2 Constraints Integration

**1. Coverage Constraint:**
Every demand zone fraction must be fully assigned to some bin(s).
$$ \sum_{j=1}^{p} a_{i,j} = 1, \quad \forall i $$

**2. Logical Link Constraint:**
Demand can only be assigned to a location if a bin is actually installed there.
$$ a_{i,j} \le y_{j}, \quad \forall i, j $$

**3. Capacity Constraint:**
The total waste assigned to a bin cannot exceed its capacity ($K$).
$$ \sum_{i=1}^{m} (F_i \cdot w \cdot a_{i,j}) \le K \cdot y_{j}, \quad \forall j $$

**4. Accessibility (Service Radius) Constraint:**
Users should not have to walk more than the service radius ($R = 40\text{m}$). If distance $D_{ij} > R$, assignment is forbidden.
$$ a_{i,j} = 0 \quad \text{if } D_{ij} > R $$

**5. Budget Constraint:**
The total spending on bins must be within budget ($B$).
$$ \sum_{j=1}^{p} C \cdot y_{j} \le B $$

**6. Variable Domains:**
$$ y_{j} \in \{0, 1\} $$
$$ 0 \le a_{i,j} \le 1 $$

### 6. Optimization Analysis
*   **Complexity:** This is an NP-hard FLP. With the reduced scope of 82 acres, we can discretize the area into a grid (e.g., $50m \times 50m$, yielding 137 candidate locations consistent with Module 3.1), resulting in feasible computation times.
*   **Trade-offs:** We expect a high density of bins around OAT and Amul (food zones) due to high $F_i$ and $w$, while the Main Road will have spaced-out bins primarily satisfying the $R$ constraint.

### 7. References
1.  IIT Delhi Campus Master Plan (2024). *Institute Infrastructure Details*. (Approx 320 acres).
2.  Rendezvous Festival Official Statistics (2024-25). *Expected Footfall*. ~160,000 attendees.
3.  CPCB (2023). *Annual Report on Solid Waste Management*. Central Pollution Control Board, India. (Avg 0.45 kg/capita/day).
4.  Market Review (2025). *Outdoor Dustbin Pricing in India*. Approx ₹10k-15k for dual FRP bins.
5.  Glasdon/Trash-Cans.com (2025). *Recommended Bin Spacing for Parks and Campuses*. 100-150 feet (30-50m).
