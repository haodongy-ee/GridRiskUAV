from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Task:
    task_id: int
    x: float
    y: float
    value: float
    risk: float
    service_time: float = 1.0


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    tasks: tuple[Task, ...]
    budget: float
    speed: float = 1.0
    risk_weight: float = 1.0
    depot_x: float = 0.0
    depot_y: float = 0.0
    seed: int | None = None
    risk_distribution: str = "custom"

    def __post_init__(self) -> None:
        if self.budget < 0 or self.speed <= 0 or self.risk_weight < 0:
            raise ValueError("budget and risk_weight must be nonnegative; speed must be positive")
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task_id values must be unique")
        if any(min(t.value, t.risk, t.service_time) < 0 for t in self.tasks):
            raise ValueError("task value, risk, and service time must be nonnegative")

    def distance_points(self, ax: float, ay: float, bx: float, by: float) -> float:
        return math.hypot(ax - bx, ay - by)

    def travel_time(self, a: Task | None, b: Task | None) -> float:
        ax, ay = (self.depot_x, self.depot_y) if a is None else (a.x, a.y)
        bx, by = (self.depot_x, self.depot_y) if b is None else (b.x, b.y)
        return self.distance_points(ax, ay, bx, by) / self.speed

    def route_cost(self, route: Iterable[int]) -> float:
        by_id = {task.task_id: task for task in self.tasks}
        ordered = [by_id[task_id] for task_id in route]
        if not ordered:
            return 0.0
        cost = self.travel_time(None, ordered[0])
        cost += sum(task.service_time for task in ordered)
        cost += sum(self.travel_time(a, b) for a, b in zip(ordered, ordered[1:]))
        cost += self.travel_time(ordered[-1], None)
        return cost

    def to_json(self, path: Path) -> None:
        payload = asdict(self)
        payload["tasks"] = [asdict(task) for task in self.tasks]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@dataclass(frozen=True)
class PlanResult:
    algorithm: str
    route: tuple[int, ...]
    route_cost: float
    captured_value: float
    captured_risk: float
    objective: float
    task_coverage: float
    risk_coverage: float
    runtime_ms: float
    status: str = "ok"

