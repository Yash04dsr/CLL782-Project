Project 3.

Sustainable “Rendezvous” - A Festival Systems Challenge

Context.WhenSanskruti, a third-year chemical engineering student from West Champaran district
in Bihar, was elected as the General Secretary (Cultural Affairs) at IIT Delhi, she was thrilled by the
opportunity. Growing up on the fringes of one of India’s richest biodiversity hotspots - where rivers,
forests, and wildlife coexist in delicate balance, Sanskruti had developed a strong respect for nature and
an instinctive understanding of how fragile ecosystems can be.

Upon arriving in Delhi, however, she was struck by the chaos and the enormous environmental footprint
of human-led activities in metro-cities. She realized that the shine, dazzling lights, convenience, and
spectacle that defined urban life, came at a cost, one that the environment silently but heavily paid. When
she witnessed the scale of waste generated during IIT Delhi’s renowned cultural festival,Rendezvous-
advertised as Asia’s largest student-run cultural festival - she decided to take an audacious step.

Rather than viewing the festival merely as a logistical challenge, Sanskruti began to see it as a powerful
opportunity. With thousands of visitors, including many school students, she felt the festival could go
beyond entertainment and serve as a platform for awareness and learning. She envisioned Rendezvous
as an event that demonstrates how enjoyment, creativity, and responsibility can coexist - showing young
minds that thoughtful choices can lead to meaningful impact.

As a member of the conscious younger generation, Sanskruti believed that meaningful change would not
come from slogans or social media campaigns alone; one had to be the change to truly see the change. For
her,sustainability was not about restriction, but about acting responsibly, making informed
decisions, and leading by example.

She therefore took on the bold challenge of reimagining Rendezvous as a truly sustainable festival, one
that minimizes waste, optimizes resource use, and paints a loud, unmistakable example for others to
see. With the support of the Dean (Student Affairs), Sanskruti assembled a Sustainability Task Force, a
diverse team of students from engineering, research, management, and design disciplines - charged with
reimagining how a large-scale cultural event could be planned, executed, and experienced sustainably.

Your team is part of this task force. You have been entrusted with the responsibility tomodel, ana-
lyze, and optimize key components of the festival- from waste collection and transportation to
infrastructure planning and procurement decisions - using the tools of optimization and systems thinking.

Module 3.1 Modeling the Problem: Quantifying Environmental Load

```
(a) Define an environmental impact function. E.g.,E=f(N, S, A), whereN: number of attendees,
S: number of food stalls,A: total event activities (e.g., concerts, performances).
```
```
(b) Do literature review and formulate an expressive model, which could include nonlinear terms (di-
minishing returns, crowding effects).
```
```
(c) Incorporate sub-components withinE, like energy use, waste generation, and emissions.
```
```
(d) Find the unconstrained minimum ofE, i.e., the ideal event scale that minimizes total ecological
footprint.
```
```
(e) Does the objective function need to be modified to better capture the sustainable festival design?
If yes, propose appropriately. Keep it to the unconstrained formulation in this module.
```
```
(f) Discuss results and draw your insights such as trade-offs, diminishing returns, sub-optimal and
optimal solutions, etc.
```
```
[22 points]
```

Module 3.2 Dustbin Placement and Accessibility

Optimize waste-bin placement to minimize average walking distance while meeting accessibility and
budget constraints.

```
(a) Formulate real-world bin location and allocation problems using nonlinear constrained optimiza-
tion.
```
- Objective: Minimize total walking distance weighted by footfall density.
- Constraints: Budget limit, bin capacity, coverage requirement.

```
(b) Divide the IIT Delhi campus map into several zonesi∈{ 1 ,... , m}with estimated footfall densities
(e.g., people/hr). Each zoneican have candidate bin locationsj ∈ { 1 ,... , p}(grid points or
predefined region)
```
```
(c) There are 3 bin types:t∈ {recyclable, compostable, general}. Each has a cost (c), service radius
(each bin serves people within a radiusr), and capacity constraint (say in kg).
```
```
(d) Your decision variables can be:
```
- yi,j,t∈{ 0 , 1 }: if bin of typetis placed at candidate locationjwithin zonei
- ai,j,t∈[0,1]: fraction of zoneifootfall assigned to binjof typet(Assignment/coverage
    fraction).

```
(e) Solve the constrained optimization problem and report the optimal number and type of bins per
zone.
```
- You can relax the binary variable to solve the continuous problem first and then you can solve
    the original problem, i.e., MINLP.

```
[24 points]
```
Module 3.3 Waste Collection and Processing Logistics

Design an efficient waste collection and processing logistics system. Waste generated in different zones
must be transported to recycling/processing centers. Each vehicle and vendor has fixed and variable
costs.

```
(a) Model the transportation of waste from zonesi={ 1 ,... , m}to processing centersj∈ {recycling
units, compost pits, landfill}.
```
- Objective: Minimize total transportation and processing cost.
- Constraints: Capacity of vehicles, facilities capacity, waste supply constraint at zonei.

```
(b) Facilitiesjhave throughput capacitiesCapjand unit processing cost in INR/kg. Transport cost
per kg from zoneito facilityjcan be modeled asti,j=cvehicledisti,j+ per-kg handling. Feel free
to modify the model.
```
```
(c) Your decision variables can be:
```
- xi,j≥0: kg of waste from zoneisent to facilityj.
- Number of vehicles for transportation∈Z≥ 0
- vehicle route used∈{ 0 , 1 }. e.g., vehicle 1 starting point→zone 1→zone 3 ...→facilityj

```
(d) Solve for optimal vehicle deployment and facility utilization.
```
```
(e) Perform sensitivity analysis to check how results change if waste generation increases by 20%.
```
```
[22 points]
```

Module 3.4 Water Refill Station Planning

The festival adopts a reusable water bottle policy for all participants. To promote reusable bottles,
each festival participant may be given a metallic water bottle, with cost partially recovered through the
festival pass.

```
(a) Pickkrefill station locations to serve attendees (minimize walking distance + installation cost)
subject to capacities (you can look for capacity p-median problem).
```
- Objective: Minimize walking distance + installation cost
- Constraints: capacity of refill station

```
(b) Candidate location for refill stationj∈{ 1 ,... , p}. Demand point comes from zonesi∈{ 1 ,... , m}
with footfalld(people/hr). Station installation cost can be considered asfj. service capacity can
be considered ascapj(people served per hour). walking cost can be considered to be proportional
to distance from zone to refill station.
```
```
(c) Your decision variables can be:
```
- yj∈{ 0 , 1 }: refill station atj
- xi,j∈[0,1]: fraction of zoneifootfall assigned to stationj(Assignment/coverage fraction).
    You can make this variable strict binary too{ 0 , 1 }.

```
(d) Solve for optimal number and placement of refill stations.
```
```
[22 points]
```
Module 3.5 Integrated System-Level Model

```
(a) Combine the previous modules into a system-level optimization
```
- Minimize total cost, environmental cost, and user inconvenience (average walking distance involved
    in using the dustbin and the refill station)
- Constraints: Combine all constraints from above modules: budget, capacities, coverage, ser-
    vice radii, logistic feasibility.

```
(b) Solve the multi-objective optimization problem and analyze the trade-offs across different objectives.
```
```
[10 points]
```

References

Letterman, R.D., 1980. Economic analysis of granular-bed filtration. Journal of the Environmental
Engineering Division 106, 279–291.

```
Optimization is in our DNA –
a “near-perfect” design shaped by millions of years of evolution, and still an ongoing process
```
```
Just like Mother Nature, we can optimize continuously – learning, adapting, and improving.
Happy Optimizing
```
