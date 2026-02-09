# Module 3.1: Quantifying Environmental Load

## Mathematical Model for Sustainable "Rendezvous" Festival

**Course:** CLL782 / CHL7204 - Process Optimization  
**Project:** Sustainable Rendezvous - A Festival Systems Challenge  
**Prepared for:** Prof. Om Prakash, Department of Chemical Engineering, IIT Delhi

---

## 1. Nomenclature Table

| Symbol | Description | Units | Type |
|--------|-------------|-------|------|
| $N$ | Number of attendees | persons | Decision Variable |
| $S$ | Number of food stalls/vendors | count | Decision Variable |
| $A$ | Total event activities (concerts, performances, etc.) | activity-hours | Decision Variable |
| $E$ | Total environmental impact/load | kg CO₂-eq | Objective Function |
| $E_{\text{energy}}$ | Energy consumption impact | kg CO₂-eq | Sub-function |
| $W_{\text{total}}$ | Total waste generation | kg | Sub-function |
| $CO_2e$ | Greenhouse gas emissions | kg CO₂-eq | Sub-function |
| $\alpha_1, \alpha_2, \alpha_3$ | Linear impact coefficients for $N$, $S$, $A$ | kg CO₂-eq/unit | Parameter |
| $\beta_1, \beta_2, \beta_3$ | Nonlinear crowding effect coefficients | kg CO₂-eq/unit² | Parameter |
| $\gamma_{NS}, \gamma_{NA}, \gamma_{SA}$ | Cross-interaction coefficients | kg CO₂-eq/unit² | Parameter |
| $\epsilon$ | Grid emission factor | kg CO₂-eq/kWh | Parameter |
| $\eta$ | Diminishing returns exponent | dimensionless | Parameter |
| $\phi$ | Waste generation rate per attendee | kg/person | Parameter |
| $\psi$ | Waste generation rate per stall | kg/stall | Parameter |
| $\tau$ | Duration of event | hours | Parameter |
| $\xi$ | Sustainability efficiency metric | kg CO₂-eq/(person·hour) | Derived Variable |

---

## 2. Assumptions and Justifications

### A2.1 Attendee-Related Assumptions

| ID | Assumption | Justification |
|----|------------|---------------|
| A1 | Per-capita environmental impact follows a base linear relationship plus nonlinear crowding effects | Life Cycle Assessment (LCA) principles indicate that individual contributions aggregate linearly at low densities, but congestion and resource competition introduce nonlinear effects at high densities (ISO 14040:2006) |
| A2 | Attendee density affects waste generation rate nonlinearly | Higher crowd density reduces per-capita access to waste bins, increasing littering and contamination of recyclables—a well-documented crowding effect in event management literature |
| A3 | Average event duration per attendee is $\tau = 8$ hours | Typical large-scale cultural festival attendance pattern based on event scheduling from 10 AM to 10 PM |

### A2.2 Food Stall Assumptions

| ID | Assumption | Justification |
|----|------------|---------------|
| A4 | Each food stall has an average capacity of 200 servings/day | Based on typical vendor capacity at large festivals |
| A5 | Food waste follows a sigmoid relationship with stall count | Initially increases linearly, then saturates due to improved logistics at scale (diminishing returns in waste per additional stall) |
| A6 | Energy consumption per stall includes cooking, refrigeration, and lighting | Standard LCA scope for food service operations |

### A2.3 Activity-Related Assumptions

| ID | Assumption | Justification |
|----|------------|---------------|
| A7 | Sound and lighting equipment power consumption scales with $A^{0.8}$ | Letterman (1980) and engineering economy principles suggest economies of scale with exponent 0.6-0.8 for equipment operations |
| A8 | Each activity-hour requires approximately 15 kW of power | Based on typical stage lighting (5 kW) + sound systems (8 kW) + auxiliary equipment (2 kW) |

### A2.4 Interaction Assumptions

| ID | Assumption | Justification |
|----|------------|---------------|
| A9 | Cross-term $N \cdot S$ captures attendee-stall congestion effects | Higher attendee counts with limited stalls create queuing, longer wait times, and inefficient food preparation leading to increased waste |
| A10 | Cross-term $N \cdot A$ reflects audience-activity synergy impacts | More activities spread attendees, potentially reducing congestion but increasing total energy footprint |
| A11 | Cross-term $S \cdot A$ models resource sharing inefficiencies | Stalls operating during high-activity periods face supply chain stress |

---

## 3. Mathematical Model Development

### 3.1 Part (a) & (b): Primary Objective Function Formulation

Following LCA principles and incorporating nonlinear effects consistent with environmental impact modeling literature, we propose a multi-variable objective function that captures the total environmental load $E$ as a function of attendees ($N$), food stalls ($S$), and activities ($A$):

$$E(N, S, A) = E_{\text{base}} + E_{\text{nonlinear}} + E_{\text{interaction}}$$

#### 3.1.1 Base Linear Impact Component

The base environmental footprint scales linearly with each primary variable:

$$E_{\text{base}} = \alpha_1 N + \alpha_2 S + \alpha_3 A$$

Where:
- $\alpha_1 = 2.5$ kg CO₂-eq/person (per-capita carbon footprint including transport, food consumption, water use)
- $\alpha_2 = 150$ kg CO₂-eq/stall (stall operation carbon footprint per day)
- $\alpha_3 = 50$ kg CO₂-eq/activity-hour (stage operations, equipment, crowd management)

#### 3.1.2 Nonlinear Crowding Effects

**Physical Interpretation**: As the scale of any variable increases beyond a threshold, environmental efficiency degrades due to:
- **Congestion effects**: Higher densities lead to resource competition
- **Diseconomies of scale**: Infrastructure strain, logistical bottlenecks
- **Diminishing returns in waste management**: Collection systems become overwhelmed

The nonlinear component is modeled as:

$$E_{\text{nonlinear}} = \beta_1 N^{1.3} + \beta_2 S^{1.2} + \beta_3 A^{1.15}$$

Where:
- $\beta_1 = 0.0003$ kg CO₂-eq/person¹·³ (crowding-induced inefficiency in waste collection, sanitation)
- $\beta_2 = 0.5$ kg CO₂-eq/stall¹·² (supply chain stress, refrigeration inefficiency at high stall counts)
- $\beta_3 = 0.8$ kg CO₂-eq/(activity-hour)¹·¹⁵ (staging conflicts, equipment redundancy)

**Justification for Exponents**:
- The exponent $1.3$ for $N$ reflects that crowd density impacts grow superlinearly, consistent with queuing theory where wait times scale as $O(N^2/(N-\lambda))$ near capacity
- The exponent $1.2$ for $S$ captures logistics network complexity that grows faster than linear
- The exponent $1.15$ for $A$ is lower, reflecting better economies of scale in shared infrastructure

#### 3.1.3 Cross-Interaction Terms

**Physical Interpretation**: Real systems exhibit synergistic effects where combinations of variables create emergent environmental pressures:

$$E_{\text{interaction}} = \gamma_{NS} \frac{N \cdot S}{S + S_0} + \gamma_{NA} \frac{N \cdot A}{N + N_0} + \gamma_{SA} \cdot S \cdot A$$

Where:
- $\gamma_{NS} = 0.002$ captures the crowding effect at food stalls (congestion-induced waste)
- $\gamma_{NA} = 0.001$ captures activity-audience impact scaling
- $\gamma_{SA} = 0.5$ captures resource competition between stalls and activities
- $S_0 = 50$, $N_0 = 5000$ are saturation constants (Michaelis-Menten type formulation)

The Michaelis-Menten formulation for the first two terms ensures:
- At low $S$ or $N$: Impact grows nearly linearly
- At high $S$ or $N$: Impact saturates (bounded crowding effect)

#### 3.1.4 Complete Objective Function

$$\boxed{E(N, S, A) = \alpha_1 N + \alpha_2 S + \alpha_3 A + \beta_1 N^{1.3} + \beta_2 S^{1.2} + \beta_3 A^{1.15} + \gamma_{NS} \frac{NS}{S + S_0} + \gamma_{NA} \frac{NA}{N + N_0} + \gamma_{SA} SA}$$

---

### 3.2 Part (c): Sub-component Integration

The total environmental load $E$ is decomposed into three primary sub-functions following LCA methodology:

$$E = E_{\text{energy}} + W_{\text{CO}_2\text{-eq}} + E_{\text{emissions}}$$

#### 3.2.1 Energy Use Sub-function ($E_{\text{energy}}$)

Energy consumption and its carbon equivalent:

$$E_{\text{energy}} = \epsilon \cdot \left[ P_{\text{lighting}}(N, A) + P_{\text{stalls}}(S) + P_{\text{audio}}(A) + P_{\text{infrastructure}}(N) \right] \cdot \tau$$

Where:
- $P_{\text{lighting}}(N, A) = 0.005 \cdot N + 5 \cdot A^{0.8}$ kW (venue lighting scales with area, stage lighting with activities)
- $P_{\text{stalls}}(S) = 3.5 \cdot S$ kW (average power per stall: cooking + refrigeration)
- $P_{\text{audio}}(A) = 8 \cdot A$ kW (sound systems)
- $P_{\text{infrastructure}}(N) = 0.002 \cdot N^{1.1}$ kW (HVAC, charging stations, information kiosks)
- $\epsilon = 0.82$ kg CO₂/kWh (Indian grid emission factor, CEA 2023)
- $\tau = 8$ hours (event duration)

Aggregated form:

$$E_{\text{energy}} = \epsilon \tau \left[ 0.005N + 0.002N^{1.1} + 3.5S + 5A^{0.8} + 8A \right]$$

$$E_{\text{energy}} = 6.56 \left[ 0.005N + 0.002N^{1.1} + 3.5S + 13A^{0.8} + 8A \right]$$

#### 3.2.2 Waste Generation Sub-function ($W_{\text{total}}$)

Total waste generation in kg, converted to CO₂-equivalent for aggregation:

$$W_{\text{total}} = W_{\text{food}} + W_{\text{packaging}} + W_{\text{organic}} + W_{\text{other}}$$

Component models:

$$W_{\text{food}} = \phi_1 \cdot N + \phi_2 \cdot S \cdot \left(1 - e^{-N/(200S)}\right)$$

This formulation captures:
- Direct attendee food waste ($\phi_1 = 0.15$ kg/person)
- Stall-dependent waste that saturates based on stall utilization

$$W_{\text{packaging}} = 0.25 \cdot N + 2 \cdot S$$

$$W_{\text{organic}} = 0.5 \cdot S \cdot \left(\frac{N}{N + 2000}\right)$$

Total waste conversion to CO₂-eq (using decomposition emission factors):

$$W_{\text{CO}_2\text{-eq}} = 0.48 \cdot W_{\text{food}} + 2.5 \cdot W_{\text{packaging}} + 0.2 \cdot W_{\text{organic}}$$

#### 3.2.3 Direct Emissions Sub-function ($CO_2e$)

Direct emissions from transportation, generators, and activities:

$$E_{\text{emissions}} = E_{\text{transport}} + E_{\text{generators}} + E_{\text{materials}}$$

Where:
$$E_{\text{transport}} = 1.5 \cdot N \quad \text{(average travel emissions per attendee)}$$

$$E_{\text{generators}} = 2.7 \cdot A \cdot \tau_{\text{backup}} \quad \text{(backup power during activities)}$$

$$E_{\text{materials}} = 0.3 \cdot S + 2 \cdot A \quad \text{(construction, staging materials)}$$

#### 3.2.4 Aggregated Primary Function

$$\boxed{E = E_{\text{energy}} + W_{\text{CO}_2\text{-eq}} + E_{\text{emissions}}}$$

Substituting the sub-components and simplifying (with $\tau = 8$ hrs, $\epsilon = 0.82$ kg CO₂/kWh):

$$E(N, S, A) \approx 2.53N + 0.013N^{1.1} + 23S + 42.7A^{0.8} + 52.5A + \text{interaction terms}$$

---

### 3.3 Part (d) & (f): Unconstrained Optimization Analysis

#### 3.3.1 First-Order Necessary Conditions

For an unconstrained minimum, we require:

$$\nabla E = \mathbf{0} \implies \frac{\partial E}{\partial N} = 0, \quad \frac{\partial E}{\partial S} = 0, \quad \frac{\partial E}{\partial A} = 0$$

**Partial Derivatives**:

$$\frac{\partial E}{\partial N} = \alpha_1 + 1.3\beta_1 N^{0.3} + \gamma_{NS} \frac{S}{S + S_0} + \gamma_{NA} \frac{A \cdot N_0}{(N + N_0)^2}$$

$$\frac{\partial E}{\partial S} = \alpha_2 + 1.2\beta_2 S^{0.2} + \gamma_{NS} \frac{N \cdot S_0}{(S + S_0)^2} + \gamma_{SA} A$$

$$\frac{\partial E}{\partial A} = \alpha_3 + 1.15\beta_3 A^{0.15} + \gamma_{NA} \frac{N}{N + N_0} + \gamma_{SA} S$$

#### 3.3.2 Critical Analysis

**Observation 1: No Internal Minimum Exists**

Setting the partial derivatives to zero reveals that:
- All coefficients $\alpha_i, \beta_i, \gamma_{ij} > 0$
- All terms in each partial derivative are strictly positive for $N, S, A > 0$

Therefore: $\nabla E > 0$ for all $(N, S, A) > 0$

**Conclusion**: The unconstrained minimum occurs at the trivial solution:

$$\boxed{(N^*, S^*, A^*) = (0, 0, 0)}$$

**Physical Interpretation**: From a pure environmental impact minimization perspective, the "ideal" event is no event at all. This is mathematically correct but practically infeasible—it fails to capture the festival's purpose.

#### 3.3.3 Trade-off Analysis

Despite no internal optimum, the model reveals important trade-offs:

**Trade-off 1: Attendee-Stall Balance**

$$\frac{\partial^2 E}{\partial N \partial S} = \gamma_{NS} \frac{S_0}{(S + S_0)^2} > 0$$

Increasing both $N$ and $S$ creates synergistic environmental load. The optimal stall-to-attendee ratio can be derived from marginal impact equality:

$$\frac{\partial E/\partial S}{\partial E/\partial N} = \frac{\text{Marginal impact of stall}}{\text{Marginal impact of attendee}}$$

For efficient resource allocation: $S \approx N/150$ provides balanced service capacity.

**Trade-off 2: Diminishing Returns**

The second derivatives show:

$$\frac{\partial^2 E}{\partial N^2} = 0.39\beta_1 N^{-0.7} - 2\gamma_{NA} \frac{A \cdot N_0}{(N + N_0)^3}$$

At high $N$, the crowding effect diminishes (decreasing marginal damage per additional attendee), while interaction effects fade. This suggests:

> **Insight**: Very large festivals are more environmentally efficient *per capita* than medium-scale events.

**Trade-off 3: Activity-Scale Tension**

The exponent $0.8$ in $A^{0.8}$ terms indicates economies of scale:
- Doubling activities increases energy impact by factor $2^{0.8} \approx 1.74$
- Many small activities are worse than fewer large activities

---

### 3.4 Part (e): Model Refinement - Sustainability Efficiency

The pure minimization objective is inadequate because it ignores the festival's social value. We propose a **sustainability efficiency** metric:

#### 3.4.1 Efficiency-Based Objective (Per-Capita-Hour Impact)

$$\xi = \frac{E}{N \cdot \tau_{\text{avg}}}$$

Where $\tau_{\text{avg}}$ is average attendee engagement time.

Modified objective:

$$\boxed{\min_{N, S, A} \xi(N, S, A) = \frac{E(N, S, A)}{N \cdot \tau_{\text{avg}}}}$$

**Substituting the primary function**:

$$\xi = \frac{\alpha_1 N + \alpha_2 S + \alpha_3 A + \beta_1 N^{1.3} + \beta_2 S^{1.2} + \beta_3 A^{1.15} + \text{interactions}}{N \cdot \tau_{\text{avg}}}$$

$$\xi = \frac{\alpha_1}{\tau_{\text{avg}}} + \frac{\alpha_2 S}{N \tau_{\text{avg}}} + \frac{\alpha_3 A}{N \tau_{\text{avg}}} + \frac{\beta_1 N^{0.3}}{\tau_{\text{avg}}} + \frac{\beta_2 S^{1.2}}{N \tau_{\text{avg}}} + \ldots$$

#### 3.4.2 Analysis of Modified Objective

**First-order conditions**:

$$\frac{\partial \xi}{\partial N} = -\frac{\alpha_2 S + \alpha_3 A + \beta_2 S^{1.2} + \ldots}{N^2 \tau} + \frac{0.3 \beta_1 N^{-0.7}}{\tau} = 0$$

This yields a non-trivial optimal $N^*$ that depends on $S$ and $A$.

**Key Result**: Unlike the original formulation, the efficiency metric has an interior optimum where increasing $N$ initially *improves* per-capita efficiency (by spreading fixed costs) until crowding effects dominate.

#### 3.4.3 Alternative Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Impact per attendee | $E/N$ | Environmental burden per person |
| Impact per activity-hour | $E/(A \cdot \tau)$ | Efficiency of entertainment value |
| Impact per utility-weighted attendance | $E/(N \cdot U(S, A))$ | Where $U$ is utility/satisfaction function |
| Pareto-optimal frontier | Multi-objective $(E, N, U)$ | Trade-off surface visualization |

---

## 4. Preliminary Insights

### 4.1 Key Findings

1. **No Interior Optimum for Pure Minimization**: The unconstrained environmental load function is strictly increasing in all decision variables. Practical optimization requires either:
   - Introducing constraints (minimum attendance, required activities)
   - Reformulating as efficiency maximization

2. **Nonlinear Crowding Effects are Critical**: The superlinear exponents ($N^{1.3}$, $S^{1.2}$) indicate that environmental damage accelerates with scale. This justifies:
   - Crowd management strategies
   - Distributed event layouts
   - Capacity planning based on infrastructure limits

3. **Cross-Interactions Drive Strategic Decisions**:
   - The $N \cdot S$ interaction suggests optimal stall density planning
   - The $S \cdot A$ term implies coordinating vendor operations with activity schedules

4. **Economies of Scale in Activities**: The sublinear energy scaling ($A^{0.8}$) favors consolidated programming over fragmented small events.

### 4.2 Trade-off Matrix

| Increase | Effect on $E_{\text{energy}}$ | Effect on $W_{\text{total}}$ | Effect on $CO_2e$ |
|----------|------------------------------|------------------------------|-------------------|
| $N$ | ↑ (lighting, infrastructure) | ↑↑ (food waste, packaging) | ↑ (transport) |
| $S$ | ↑↑ (cooking, refrigeration) | ↑ (vendor waste) | ↑ (slight) |
| $A$ | ↑↑ (audio, staging) | ↑ (slight) | ↑ (generators) |

### 4.3 Recommendations for Module 3.2+

1. **Constrained Optimization**: Introduce minimum service requirements and capacity constraints
2. **Multi-Objective Formulation**: Balance $E$ against attendee satisfaction utility
3. **Stochastic Elements**: Model uncertainty in attendance, weather impacts
4. **Spatial Components**: Integrate with dustbin placement (Module 3.2) for waste logistics

---

## 5. References

1. **Edgar, T.F., Himmelblau, D.M., & Lasdon, L.S. (2001)**. *Optimization of Chemical Processes*, 2nd ed. McGraw-Hill. — Foundational framework for process optimization and objective function formulation.

2. **Letterman, R.D. (1980)**. Economic analysis of granular-bed filtration. *Journal of the Environmental Engineering Division*, 106, 279-291. — Referenced for diminishing returns and scale effects in environmental systems.

3. **ISO 14040:2006**. Environmental management — Life cycle assessment — Principles and framework. — LCA methodology for environmental impact quantification.

4. **Central Electricity Authority of India (2023)**. CO₂ Baseline Database for the Indian Power Sector. — Grid emission factor reference.

5. **Course Lecture Notes**, CLL782/CHL7204, IIT Delhi, Prof. Om Prakash. — Optimization framework and problem formulation methodology.

---

*This model provides a theoretical foundation for Module 3.1. Numerical calibration requires site-specific data from previous Rendezvous events.*
