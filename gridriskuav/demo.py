from __future__ import annotations

from .baselines import ALGORITHMS
from .scenarios import reference_scenario


def main() -> None:
    scenario = reference_scenario()
    print(f"Scenario: {scenario.scenario_id}")
    print(f"Tasks: {len(scenario.tasks)}, total risk: {sum(t.risk for t in scenario.tasks):.1f}, budget: {scenario.budget:.1f}")
    print("algorithm             tasks  coverage  captured_risk  risk_cov  cost    objective  runtime_ms")
    for name, algorithm in ALGORITHMS.items():
        result = algorithm(scenario)
        print(
            f"{name:21} {len(result.route):5d}  {result.task_coverage:7.1%}"
            f"  {result.captured_risk:13.1f}  {result.risk_coverage:8.1%}"
            f"  {result.route_cost:6.2f}  {result.objective:9.2f}  {result.runtime_ms:10.3f}"
        )


if __name__ == "__main__":
    main()

