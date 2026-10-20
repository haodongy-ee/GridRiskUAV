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
class HazardZone:
    x: float
    y: float
    radius: float
    severity: float


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
    weather_travel_factor: float = 1.0
    max_flight_distance: float = math.inf
    battery_capacity: float = math.inf
    battery_reserve: float = 0.0
    battery_per_distance: float = 1.0
    max_flight_exposure: float = math.inf
    hazard_zones: tuple[HazardZone, ...] = ()

    def __post_init__(self) -> None:
        if self.budget < 0 or self.speed <= 0 or self.risk_weight < 0:
            raise ValueError("budget and risk_weight must be nonnegative; speed must be positive")
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task_id values must be unique")
        if any(min(t.value, t.risk, t.service_time) < 0 for t in self.tasks):
            raise ValueError("task value, risk, and service time must be nonnegative")
        if self.weather_travel_factor < 1 or self.max_flight_distance < 0 or self.battery_capacity < 0:
            raise ValueError("invalid weather, distance or battery capacity")
        if self.battery_reserve < 0 or self.battery_per_distance <= 0 or self.max_flight_exposure < 0:
            raise ValueError("invalid battery reserve, consumption or exposure limit")
        if self.battery_reserve > self.battery_capacity:
            raise ValueError("battery reserve exceeds capacity")
        if any(z.radius <= 0 or z.severity < 0 for z in self.hazard_zones):
            raise ValueError("hazard radius must be positive and severity nonnegative")

    def distance_points(self, ax: float, ay: float, bx: float, by: float) -> float:
        return math.hypot(ax - bx, ay - by)

    def travel_time(self, a: Task | None, b: Task | None) -> float:
        ax, ay = (self.depot_x, self.depot_y) if a is None else (a.x, a.y)
        bx, by = (self.depot_x, self.depot_y) if b is None else (b.x, b.y)
        return self.weather_travel_factor * self.distance_points(ax, ay, bx, by) / self.speed

    def route_distance(self, route: Iterable[int]) -> float:
        by_id = {task.task_id: task for task in self.tasks}
        ordered = [by_id[task_id] for task_id in route]
        nodes: list[Task | None] = [None, *ordered, None] if ordered else []
        return sum(self._edge_distance(a, b) for a, b in zip(nodes, nodes[1:]))

    def _edge_distance(self, a: Task | None, b: Task | None) -> float:
        ax, ay = (self.depot_x, self.depot_y) if a is None else (a.x, a.y)
        bx, by = (self.depot_x, self.depot_y) if b is None else (b.x, b.y)
        return math.hypot(ax - bx, ay - by)

    def route_exposure(self, route: Iterable[int]) -> float:
        by_id = {task.task_id: task for task in self.tasks}
        ordered = [by_id[task_id] for task_id in route]
        nodes: list[Task | None] = [None, *ordered, None] if ordered else []
        return sum(self.edge_exposure(a, b) for a, b in zip(nodes, nodes[1:]))

    def edge_exposure(self, a: Task | None, b: Task | None) -> float:
        ax, ay = (self.depot_x, self.depot_y) if a is None else (a.x, a.y)
        bx, by = (self.depot_x, self.depot_y) if b is None else (b.x, b.y)
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length == 0:
            return 0.0
        exposure = 0.0
        for zone in self.hazard_zones:
            # Length of the segment inside a circular hazard zone.
            fx, fy = ax - zone.x, ay - zone.y
            aa = dx * dx + dy * dy
            bb = 2 * (fx * dx + fy * dy)
            cc = fx * fx + fy * fy - zone.radius * zone.radius
            discriminant = bb * bb - 4 * aa * cc
            if discriminant <= 0:
                if cc < 0:
                    exposure += length * zone.severity
                continue
            root = math.sqrt(discriminant)
            lo = max(0.0, (-bb - root) / (2 * aa))
            hi = min(1.0, (-bb + root) / (2 * aa))
            exposure += max(0.0, hi - lo) * length * zone.severity
        return exposure

    def is_feasible(self, route: Iterable[int]) -> bool:
        route_tuple = tuple(route)
        distance = self.route_distance(route_tuple)
        return (
            self.route_cost(route_tuple) <= self.budget + 1e-9
            and distance <= self.max_flight_distance + 1e-9
            and distance * self.battery_per_distance <= self.battery_capacity - self.battery_reserve + 1e-9
            and self.route_exposure(route_tuple) <= self.max_flight_exposure + 1e-9
        )

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
        for name in ("max_flight_distance", "battery_capacity", "max_flight_exposure"):
            if math.isinf(payload[name]):
                payload.pop(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")

    @classmethod
    def from_json(cls, path: Path) -> Scenario:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["tasks"] = tuple(Task(**row) for row in payload["tasks"])
        payload["hazard_zones"] = tuple(HazardZone(**row) for row in payload.get("hazard_zones", []))
        return cls(**payload)


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
    route_distance: float = 0.0
    flight_exposure: float = 0.0

