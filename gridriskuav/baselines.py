from __future__ import annotations

from math import inf
from time import perf_counter
from typing import Callable

from .metrics import build_result
from .models import PlanResult, Scenario, Task


Score = Callable[[Scenario, Task | None, Task, float], tuple[float, ...]]


def _marginal_cost(scenario: Scenario, current: Task | None, candidate: Task) -> float:
    """Extra cost of inserting candidate immediately before the depot return."""
    return (
        scenario.travel_time(current, candidate)
        + candidate.service_time
        + scenario.travel_time(candidate, None)
        - scenario.travel_time(current, None)
    )


def _greedy(scenario: Scenario, name: str, score: Score) -> PlanResult:
    started = perf_counter()
    remaining = list(scenario.tasks)
    route: list[int] = []
    current: Task | None = None
    committed_cost = 0.0
    while remaining:
        feasible: list[tuple[tuple[float, ...], Task, float]] = []
        for task in remaining:
            marginal = _marginal_cost(scenario, current, task)
            if scenario.is_feasible([*route, task.task_id]):
                feasible.append((score(scenario, current, task, marginal), task, marginal))
        if not feasible:
            break
        _, chosen, marginal = max(feasible, key=lambda item: item[0])
        route.append(chosen.task_id)
        remaining.remove(chosen)
        current = chosen
        committed_cost += marginal
    elapsed = (perf_counter() - started) * 1000
    return build_result(scenario, name, route, elapsed)


def nearest(scenario: Scenario) -> PlanResult:
    def score(s: Scenario, current: Task | None, task: Task, marginal: float) -> tuple[float, ...]:
        direct = s.travel_time(current, task)
        return (-direct, task.value, task.risk, -task.task_id)

    return _greedy(scenario, "nearest", score)


def reward_per_cost(scenario: Scenario) -> PlanResult:
    def score(s: Scenario, current: Task | None, task: Task, marginal: float) -> tuple[float, ...]:
        ratio = task.value / marginal if marginal > 0 else inf
        return (ratio, task.value, task.risk, -task.task_id)

    return _greedy(scenario, "reward_per_cost", score)


def risk_aware_greedy(scenario: Scenario) -> PlanResult:
    def score(s: Scenario, current: Task | None, task: Task, marginal: float) -> tuple[float, ...]:
        utility = task.value + s.risk_weight * task.risk
        ratio = utility / marginal if marginal > 0 else inf
        return (ratio, utility, task.risk, -task.task_id)

    return _greedy(scenario, "risk_aware_greedy", score)


def optimal_dp(scenario: Scenario, max_tasks: int = 18) -> PlanResult:
    """Exact resource-constrained orienteering via Held-Karp subset DP."""
    if (
        scenario.max_flight_distance < inf
        or scenario.battery_capacity < inf
        or scenario.max_flight_exposure < inf
    ):
        return PlanResult("optimal_dp", (), float("nan"), float("nan"), float("nan"),
                          float("nan"), float("nan"), float("nan"), 0.0,
                          status="skipped_resource_constraints")
    if len(scenario.tasks) > max_tasks:
        return PlanResult(
            algorithm="optimal_dp",
            route=(),
            route_cost=float("nan"),
            captured_value=float("nan"),
            captured_risk=float("nan"),
            objective=float("nan"),
            task_coverage=float("nan"),
            risk_coverage=float("nan"),
            runtime_ms=0.0,
            status="skipped_size_limit",
        )

    started = perf_counter()
    tasks = scenario.tasks
    n = len(tasks)
    if n == 0:
        return build_result(scenario, "optimal_dp", [], (perf_counter() - started) * 1000)

    # dp[(mask, j)] = minimum one-way cost from depot, visiting mask, ending at j.
    dp: dict[tuple[int, int], float] = {}
    parent: dict[tuple[int, int], int | None] = {}
    for j, task in enumerate(tasks):
        cost = scenario.travel_time(None, task) + task.service_time
        if cost + scenario.travel_time(task, None) <= scenario.budget + 1e-9:
            dp[(1 << j, j)] = cost
            parent[(1 << j, j)] = None

    for mask in range(1, 1 << n):
        for j in range(n):
            state = (mask, j)
            if state not in dp:
                continue
            base = dp[state]
            for k in range(n):
                if mask & (1 << k):
                    continue
                new_mask = mask | (1 << k)
                new_cost = base + scenario.travel_time(tasks[j], tasks[k]) + tasks[k].service_time
                if new_cost + scenario.travel_time(tasks[k], None) > scenario.budget + 1e-9:
                    continue
                key = (new_mask, k)
                if new_cost < dp.get(key, inf) - 1e-12:
                    dp[key] = new_cost
                    parent[key] = j

    utilities = [task.value + scenario.risk_weight * task.risk for task in tasks]
    utility_by_mask = [0.0] * (1 << n)
    for mask in range(1, 1 << n):
        bit = mask & -mask
        idx = bit.bit_length() - 1
        utility_by_mask[mask] = utility_by_mask[mask ^ bit] + utilities[idx]

    best_key: tuple[int, int] | None = None
    best_rank = (0.0, 0, 0.0)
    for (mask, j), one_way_cost in dp.items():
        full_cost = one_way_cost + scenario.travel_time(tasks[j], None)
        rank = (utility_by_mask[mask], mask.bit_count(), -full_cost)
        if rank > best_rank:
            best_rank = rank
            best_key = (mask, j)

    route_indices: list[int] = []
    if best_key is not None:
        mask, current = best_key
        while True:
            route_indices.append(current)
            previous = parent[(mask, current)]
            if previous is None:
                break
            mask ^= 1 << current
            current = previous
        route_indices.reverse()
    route = [tasks[index].task_id for index in route_indices]
    elapsed = (perf_counter() - started) * 1000
    return build_result(scenario, "optimal_dp", route, elapsed)


def _two_opt(scenario: Scenario, route: list[int]) -> list[int]:
    """Shorten the tour without changing its selected tasks."""
    improved = route[:]
    for _ in range(2):
        best_cost = scenario.route_cost(improved)
        best_route = improved
        for i in range(len(improved) - 1):
            for j in range(i + 2, len(improved) + 1):
                candidate = improved[:i] + list(reversed(improved[i:j])) + improved[j:]
                cost = scenario.route_cost(candidate)
                if cost < best_cost - 1e-9 and scenario.is_feasible(candidate):
                    best_cost, best_route = cost, candidate
        if best_route == improved:
            break
        improved = best_route
    return improved


def local_search(scenario: Scenario) -> PlanResult:
    """Multi-start insertion, 2-opt and one-for-one exchanges for larger instances."""
    started = perf_counter()
    utility = {t.task_id: t.value + scenario.risk_weight * t.risk for t in scenario.tasks}
    seeds = [nearest(scenario).route, reward_per_cost(scenario).route, risk_aware_greedy(scenario).route]
    best_route: list[int] = []
    best_rank = (0.0, 0.0)
    for seed in seeds:
        route = _two_opt(scenario, list(seed))
        for _ in range(3):
            changed = False
            remaining = [t.task_id for t in scenario.tasks if t.task_id not in route]
            # Evaluate all insertion positions, prioritizing objective increase.
            best_insert: tuple[float, float, list[int]] | None = None
            for task_id in remaining:
                for position in range(len(route) + 1):
                    candidate = route[:position] + [task_id] + route[position:]
                    if scenario.is_feasible(candidate):
                        rank = (utility[task_id], -scenario.route_cost(candidate))
                        if best_insert is None or rank > best_insert[:2]:
                            best_insert = (*rank, candidate)
            if best_insert is not None:
                route = _two_opt(scenario, best_insert[2])
                changed = True
            else:
                best_swap: tuple[float, float, list[int]] | None = None
                for task_id in remaining:
                    for position, outgoing in enumerate(route):
                        gain = utility[task_id] - utility[outgoing]
                        if gain <= 1e-9:
                            continue
                        candidate = route[:position] + [task_id] + route[position + 1:]
                        if scenario.is_feasible(candidate):
                            rank = (gain, -scenario.route_cost(candidate))
                            if best_swap is None or rank > best_swap[:2]:
                                best_swap = (*rank, candidate)
                if best_swap is not None:
                    route = _two_opt(scenario, best_swap[2])
                    changed = True
            if not changed:
                break
        rank = (sum(utility[task_id] for task_id in route), -scenario.route_cost(route))
        if rank > best_rank:
            best_rank, best_route = rank, route
    return build_result(scenario, "local_search", best_route, (perf_counter() - started) * 1000)


ALGORITHMS = {
    "nearest": nearest,
    "reward_per_cost": reward_per_cost,
    "risk_aware_greedy": risk_aware_greedy,
    "local_search": local_search,
    "optimal_dp": optimal_dp,
}

