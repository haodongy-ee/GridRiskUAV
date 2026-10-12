# GridRiskUAV v0.2

Risk-aware route planning baselines for power-grid UAV inspection.

## Problem

A UAV starts and ends at one depot. Each candidate inspection task has a
location, inspection value, risk score, and service time. Under a total time
budget, the planner chooses and orders a subset of tasks. The main objective is
to maximize

```text
sum(value_i + risk_weight * risk_i)
```

while respecting travel time, service time, visit-once, and return-to-depot
constraints. See `docs/problem_definition.md` for the formal model.

## Baselines

- `nearest`: chooses the nearest feasible unvisited task.
- `reward_per_cost`: chooses the largest inspection-value / marginal-cost ratio.
- `risk_aware_greedy`: chooses the largest (value + weighted risk) / marginal-cost ratio.
- `optimal_dp`: exact orienteering baseline using Held-Karp subset dynamic programming.
  It is intentionally limited to at most 18 tasks.

Every constructive baseline checks the cost of returning to the depot before
accepting a task.

## Quick start

Python 3.10+ is sufficient; there are no third-party runtime dependencies.

```powershell
python -m gridriskuav.demo
python -m gridriskuav.experiment --output-dir results
python -m unittest discover -s tests -v
```

The experiment command writes:

- `runs.csv`: one row per scenario/algorithm pair;
- `summary.csv`: aggregated means by task count, risk distribution, and algorithm;
- `scenarios/*.json`: exact inputs, including random seed and budget.

## Reproducibility

Scenario IDs encode task count, risk distribution, replicate, and seed. Results
record both `task_coverage` and `risk_coverage`; neither is overloaded as the
other. A skipped exact run has status `skipped_size_limit` and blank metrics.


