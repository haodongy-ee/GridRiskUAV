# GridRiskUAV batch experiment report

## Configuration

- Task counts: 10, 15, 20
- Risk distributions: uniform, hotspot, bimodal
- Replicates per setting: 3
- Base random seed: 20261013
- Risk weight: 1
- Generated scenarios: 27
- Exact baseline limit: 18 tasks

## Aggregate results

Values below are means across all requested risk distributions and replicates.

| tasks | algorithm | runs | task coverage | risk coverage | captured risk | route cost | objective | runtime (ms) |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 10 | nearest | 9 | 30.0% | 28.9% | 12.46 | 22.24 | 30.65 | 0.042 |
| 10 | reward_per_cost | 9 | 25.6% | 29.8% | 11.06 | 19.83 | 28.41 | 0.029 |
| 10 | risk_aware_greedy | 9 | 25.6% | 37.8% | 14.66 | 21.13 | 31.62 | 0.029 |
| 10 | optimal_dp | 9 | 28.9% | 42.5% | 16.33 | 22.98 | 36.12 | 0.906 |
| 15 | nearest | 9 | 29.6% | 22.4% | 13.34 | 23.99 | 41.22 | 0.078 |
| 15 | reward_per_cost | 9 | 26.7% | 25.3% | 14.64 | 23.25 | 45.23 | 0.059 |
| 15 | risk_aware_greedy | 9 | 27.4% | 30.5% | 18.04 | 22.47 | 47.12 | 0.061 |
| 15 | optimal_dp | 9 | 32.6% | 36.2% | 22.26 | 24.67 | 55.80 | 28.831 |
| 20 | nearest | 9 | 25.6% | 27.6% | 22.71 | 24.53 | 53.51 | 0.113 |
| 20 | reward_per_cost | 9 | 23.3% | 24.3% | 20.33 | 23.79 | 51.89 | 0.089 |
| 20 | risk_aware_greedy | 9 | 23.9% | 26.1% | 21.76 | 23.42 | 52.59 | 0.092 |
| 20 | optimal_dp | 0 | — | — | — | — | — | — |

## Interpretation notes

- Task coverage and risk coverage are deliberately separate. A planner may inspect fewer tasks while capturing more total risk.
- `optimal_dp` is an exact reference for scenarios with at most 18 tasks; skipped cells are not treated as zero performance.
- Runtime measures planning only and excludes scenario generation and file writing.
- The current synthetic benchmark is a baseline, not evidence of field performance. Real coordinates, no-fly constraints, battery reserve, and weather should be introduced as separate model terms.

## Files

- `runs.csv`: per-run metrics and routes.
- `summary.csv`: means for each task-count / distribution / algorithm combination.
- `scenarios/`: serialized inputs for exact replay.
