# GridRiskUAV

Version 0.3

Risk-aware scheduling for power-grid UAV inspection. The planner selects inspection tasks, visits each at most once, and returns to the depot within the sortie limits. It reports inspection value, captured asset risk, flight distance, flight-path hazard exposure, and planning runtime separately.

## Quick start

Python 3.10+ is required. The project has no third-party runtime dependencies.

```powershell
python -m unittest discover -s tests -v
python -m gridriskuav.demo
python -m gridriskuav.sensitivity --config config/experiment.json --output-dir results/v0.3
python -m gridriskuav.plots --runs results/v0.3/runs.csv --output-dir results/v0.3/figures
```

For a short smoke run, add `--replicates 1` to the sensitivity command. The full configuration has 20 independent seeds for every combination of 5 task counts, 3 risk distributions, 5 risk weights, and 3 budget levels: 4,500 scenario settings and 22,500 planner records.

## Baselines

- `nearest`: closest feasible next task.
- `reward_per_cost`: inspection value divided by marginal route cost.
- `risk_aware_greedy`: inspection value plus weighted asset risk divided by marginal route cost.
- `local_search`: multi-start 2-opt, insertion, and exchange improvement.
- `optimal_dp`: exact single-resource dynamic programming for up to 18 tasks. It reports a skip status outside its supported domain.

The [mathematical model](docs/problem_definition.md) defines the objective and all constraints. The experiment configuration is in [config/experiment.json](config/experiment.json).

## Outputs

- `results/v0.3/REPORT.md`: readable aggregate results and limitations, included in the repository.
- `results/v0.3/figures/`: editable SVG comparisons and route map, included in the repository.
- `GridRiskUAV_v0.3_results.zip` in the GitHub release: full `runs.csv`, `summary.csv`, 300 base scenario JSON files, report, and figures. Run rows specify the applied weight and budget factor.

The repository includes a GitHub Actions test workflow. Re-run the full experiment locally to regenerate runtime numbers on your own machine; runtime is hardware-dependent.
