from __future__ import annotations

from .models import PlanResult, Scenario


def build_result(
    scenario: Scenario,
    algorithm: str,
    route: list[int] | tuple[int, ...],
    runtime_ms: float,
) -> PlanResult:
    route_tuple = tuple(route)
    if len(route_tuple) != len(set(route_tuple)):
        raise ValueError("a route cannot visit a task more than once")
    by_id = {task.task_id: task for task in scenario.tasks}
    if any(task_id not in by_id for task_id in route_tuple):
        raise ValueError("route contains an unknown task")
    route_cost = scenario.route_cost(route_tuple)
    if route_cost > scenario.budget + 1e-9:
        raise ValueError(f"infeasible route cost {route_cost:.6f} exceeds budget {scenario.budget:.6f}")
    selected = [by_id[task_id] for task_id in route_tuple]
    value = sum(task.value for task in selected)
    risk = sum(task.risk for task in selected)
    total_risk = sum(task.risk for task in scenario.tasks)
    return PlanResult(
        algorithm=algorithm,
        route=route_tuple,
        route_cost=route_cost,
        captured_value=value,
        captured_risk=risk,
        objective=value + scenario.risk_weight * risk,
        task_coverage=len(selected) / len(scenario.tasks) if scenario.tasks else 1.0,
        risk_coverage=risk / total_risk if total_risk else 1.0,
        runtime_ms=runtime_ms,
    )

