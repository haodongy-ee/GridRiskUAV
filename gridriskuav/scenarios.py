from __future__ import annotations

import random

from .models import Scenario, Task


RISK_DISTRIBUTIONS = ("uniform", "hotspot", "bimodal")


def _risk(rng: random.Random, distribution: str, x: float, y: float) -> float:
    if distribution == "uniform":
        return rng.uniform(1.0, 10.0)
    if distribution == "hotspot":
        # A high-risk cluster around (7, 7), plus a small background risk.
        proximity = max(0.0, 1.0 - ((x - 7.0) ** 2 + (y - 7.0) ** 2) ** 0.5 / 8.0)
        return min(10.0, 1.0 + 9.0 * proximity + rng.uniform(-0.5, 0.5))
    if distribution == "bimodal":
        return rng.uniform(1.0, 3.0) if rng.random() < 0.65 else rng.uniform(8.0, 10.0)
    raise ValueError(f"unknown risk distribution: {distribution}")


def generate_scenario(
    n_tasks: int,
    risk_distribution: str,
    seed: int,
    budget: float | None = None,
    risk_weight: float = 1.0,
) -> Scenario:
    if n_tasks < 0:
        raise ValueError("n_tasks must be nonnegative")
    rng = random.Random(seed)
    tasks = []
    for task_id in range(1, n_tasks + 1):
        x, y = rng.uniform(-10.0, 10.0), rng.uniform(-10.0, 10.0)
        risk = round(_risk(rng, risk_distribution, x, y), 3)
        value = round(rng.uniform(2.0, 10.0), 3)
        service = round(rng.uniform(0.4, 1.4), 3)
        tasks.append(Task(task_id, x, y, value, risk, service))
    # Budget grows sublinearly to keep selection nontrivial as task count increases.
    resolved_budget = budget if budget is not None else 17.0 + 2.2 * n_tasks ** 0.5
    scenario_id = f"n{n_tasks}_{risk_distribution}_rep{seed % 1000:03d}_seed{seed}"
    return Scenario(
        scenario_id=scenario_id,
        tasks=tuple(tasks),
        budget=resolved_budget,
        risk_weight=risk_weight,
        seed=seed,
        risk_distribution=risk_distribution,
    )


def reference_scenario() -> Scenario:
    """A deterministic 13-task example whose total risk is exactly 74."""
    risks = [9, 8, 7, 7, 6, 6, 6, 5, 5, 4, 4, 4, 3]
    points = [
        (2, 1), (4, 1), (5, 3), (3, 4), (1, 5), (-2, 4), (-4, 2),
        (-5, -1), (-3, -3), (-1, -5), (2, -4), (5, -3), (7, 0),
    ]
    tasks = tuple(
        Task(i + 1, x, y, value=4 + (i % 5), risk=risks[i], service_time=0.8)
        for i, (x, y) in enumerate(points)
    )
    return Scenario(
        scenario_id="reference_13_total_risk_74",
        tasks=tasks,
        budget=26.0,
        risk_weight=1.0,
        risk_distribution="reference",
        seed=0,
    )

