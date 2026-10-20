# GridRiskUAV v0.3 experiment

Generated 22500 planner records from 4500 scenario settings.
Each task count/distribution/weight/budget cell uses 20 independent seeds.
95% intervals use mean ± 1.96 × sample standard deviation / √n.
Runtime measures planning only, on the machine that produced these files.

## Medium budget, risk weight 1

| Tasks | Algorithm | Runs | Task coverage | Risk coverage | Captured risk | Route cost | Objective | Gap | Runtime (ms) |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | nearest | 60 | 30.5% | 28.1% | 12.03 | 20.42 | 30.49 | 18.1% | 0.15 |
| 10 | reward_per_cost | 60 | 28.7% | 24.6% | 10.47 | 20.53 | 30.40 | 18.0% | 0.13 |
| 10 | risk_aware_greedy | 60 | 28.8% | 32.0% | 13.37 | 20.50 | 32.66 | 12.0% | 0.13 |
| 10 | local_search | 60 | 32.2% | 36.8% | 15.29 | 21.90 | 36.09 | 2.5% | 1.07 |
| 10 | optimal_dp | 60 | 32.7% | 37.3% | 15.64 | 22.04 | 37.03 | 0.0% | 0.73 |
| 15 | nearest | 60 | 26.8% | 26.8% | 15.85 | 22.33 | 39.73 | 19.5% | 0.34 |
| 15 | reward_per_cost | 60 | 25.4% | 24.2% | 14.45 | 22.44 | 40.14 | 17.8% | 0.29 |
| 15 | risk_aware_greedy | 60 | 25.4% | 29.6% | 17.57 | 22.18 | 42.16 | 14.2% | 0.30 |
| 15 | local_search | 60 | 28.6% | 32.8% | 19.28 | 23.69 | 46.84 | 5.0% | 2.50 |
| 15 | optimal_dp | 60 | 28.9% | 36.2% | 21.33 | 24.53 | 49.24 | 0.0% | 21.53 |
| 20 | nearest | 60 | 25.2% | 23.5% | 19.61 | 24.77 | 50.54 | — | 0.59 |
| 20 | reward_per_cost | 60 | 24.2% | 22.8% | 19.15 | 24.45 | 52.47 | — | 0.54 |
| 20 | risk_aware_greedy | 60 | 24.6% | 26.1% | 21.52 | 24.19 | 54.09 | — | 0.55 |
| 20 | local_search | 60 | 27.5% | 30.2% | 24.68 | 25.51 | 61.49 | — | 5.15 |
| 20 | optimal_dp | 0 | — | — | — | — | — | — | — |
| 50 | nearest | 60 | 18.1% | 17.0% | 34.45 | 31.58 | 87.41 | — | 3.78 |
| 50 | reward_per_cost | 60 | 16.2% | 14.3% | 30.33 | 30.68 | 85.84 | — | 3.38 |
| 50 | risk_aware_greedy | 60 | 16.6% | 19.3% | 38.77 | 31.01 | 93.51 | — | 3.37 |
| 50 | local_search | 60 | 19.5% | 22.7% | 45.42 | 31.94 | 109.20 | — | 38.82 |
| 50 | optimal_dp | 0 | — | — | — | — | — | — | — |
| 100 | nearest | 60 | 14.1% | 13.1% | 55.33 | 38.29 | 141.04 | — | 17.93 |
| 100 | reward_per_cost | 60 | 12.8% | 11.3% | 47.67 | 37.46 | 133.81 | — | 15.51 |
| 100 | risk_aware_greedy | 60 | 12.9% | 13.6% | 56.79 | 37.48 | 140.35 | — | 15.78 |
| 100 | local_search | 60 | 15.2% | 16.1% | 66.62 | 38.33 | 167.84 | — | 203.71 |
| 100 | optimal_dp | 0 | — | — | — | — | — | — | — |

## Interpretation

- Task coverage and risk coverage answer different questions.
- Exact DP runs only for task counts up to 18 and without additional flight-resource constraints; skipped runs are blank, not zero.
- The objective changes with risk weight, so compare objectives only within the same weight and scenario.
- Scenario JSON files contain base task sets. `runs.csv` records the applied risk weight and budget factor for replay.
- Synthetic results do not establish field performance.
