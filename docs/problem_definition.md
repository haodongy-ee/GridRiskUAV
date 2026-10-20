# GridRiskUAV v0.3 mathematical model

The UAV departs from depot 0, visits an ordered subset of tasks \(V=\{1,\dots,n\}\), and returns to 0. Task \(i\) has inspection value \(v_i\ge0\), asset risk \(r_i\ge0\), and service time \(s_i\ge0\). Asset risk is the risk captured by inspection. The decision weight \(\lambda\ge0\) controls its importance.

For a route \(P=(0,i_1,\dots,i_k,0)\), the objective is

\[
\max_P U(P)=\sum_{i\in P\setminus\{0\}}(v_i+\lambda r_i).
\]

Each task appears at most once. The empty route is feasible. A full trip, including the final return, must satisfy all active limits below.

## Flight resources

Let \(d_{ij}\) be Euclidean edge length, \(q>0\) UAV speed, and \(w\ge1\) the weather travel multiplier. Let \(B\) be the sortie time budget, \(D_{\max}\) the maximum flight distance, \(C\) battery capacity, \(C_{\mathrm{reserve}}\) the required landing reserve, and \(e_d>0\) battery consumption per distance unit.

\[
T(P)=\sum_{(i,j)\in P}w d_{ij}/q+\sum_{i\in P\setminus\{0\}}s_i\le B,
\]

\[
D(P)=\sum_{(i,j)\in P}d_{ij}\le D_{\max},\qquad
e_d D(P)\le C-C_{\mathrm{reserve}}.
\]

The battery model is deliberately simple and transparent. Future calibration can replace distance-based consumption with a measured energy model.

## Flight-path hazard

Flight hazard is separate from asset risk. Each circular hazard zone \(z\) has a center, radius, and nonnegative severity \(h_z\). For a straight edge \((i,j)\), \(\ell_{ij,z}\) is the exact length of its intersection with zone \(z\). Exposure is

\[
E(P)=\sum_{(i,j)\in P}\sum_z h_z\ell_{ij,z}\le E_{\max}.
\]

Intersecting zones add exposure. This is a screening model, not a certified collision or no-fly-zone planner. Wind and weather currently affect travel time through \(w\); actual weather constraints need field data.

## Algorithms and reported metrics

`nearest`, `reward_per_cost`, `risk_aware_greedy`, and `local_search` enforce all active resource limits before accepting a route. `local_search` starts from the three constructive routes, shortens each with 2-opt, then tries feasible insertions and one-for-one exchanges. Its result cannot be worse in objective than the best of those three starts.

`optimal_dp` is exact for the single time-budget model with at most 18 tasks. It is explicitly skipped when additional flight-resource limits are active. This avoids presenting a single-resource dynamic program as exact under multiple resources.

Reported metrics are task coverage \(k/n\), captured asset risk \(\sum r_i\), risk coverage \(\sum_{i\in P}r_i/\sum_{i\in V}r_i\), route time \(T(P)\), route distance \(D(P)\), flight exposure \(E(P)\), utility \(U(P)\), and wall-clock planning runtime. When an exact solution exists, relative gap is \(\max(0,(U^*-U)/U^*)\). Gap is blank when no exact reference exists or \(U^*=0\).

Confidence intervals in the batch report use \(\bar x\pm1.96s/\sqrt n\), where \(s\) is the sample standard deviation across independent scenario seeds. These are normal-approximation intervals, not bootstrap or field uncertainty bounds.
