"""Dependency-free, editable SVG figures for the sensitivity report."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from html import escape
from pathlib import Path
from statistics import mean

from .baselines import local_search
from .models import HazardZone
from .scenarios import reference_scenario


COLORS = {
    "nearest": "#64748b",
    "reward_per_cost": "#d97706",
    "risk_aware_greedy": "#0d9488",
    "local_search": "#2563eb",
    "optimal_dp": "#7c3aed",
}
LABELS = {
    "nearest": "Nearest",
    "reward_per_cost": "Value / cost",
    "risk_aware_greedy": "Risk-aware greedy",
    "local_search": "Local search",
    "optimal_dp": "Exact DP",
}


def _svg(parts: list[str], width: int = 1000, height: int = 600) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">\n'
            '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172033} '
            '.title{font-size:25px;font-weight:700}.label{font-size:15px}.small{font-size:12px} '
            '.grid{stroke:#dbe3ed;stroke-width:1}.axis{stroke:#52657a;stroke-width:1.5}</style>\n'
            + "\n".join(parts) + "\n</svg>\n")


def _text(x: float, y: float, value: str, css: str = "label", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{css}" text-anchor="{anchor}">{escape(value)}</text>'


def _line(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 1.5) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"/>'


def _circle(x: float, y: float, radius: float, color: str, opacity: float = 1) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}" fill-opacity="{opacity}"/>'


def _legend(parts: list[str], algorithms: list[str], x: int = 750, y: int = 92) -> None:
    for index, algorithm in enumerate(algorithms):
        yy = y + index * 26
        parts.append(f'<rect x="{x}" y="{yy-11}" width="17" height="17" fill="{COLORS[algorithm]}"/>')
        parts.append(_text(x + 25, yy + 2, LABELS[algorithm], "small"))


def _read_runs(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def performance(rows: list[dict]) -> str:
    parts = [_text(75, 55, "Risk coverage by task count", "title"),
             _text(75, 79, "Medium budget · risk weight 1 · mean across all distributions", "small")]
    algorithms = list(COLORS)
    sizes = sorted({int(r["n_tasks"]) for r in rows})
    x0, y0, plot_w, plot_h = 85, 130, 610, 390
    for tick in range(0, 101, 20):
        y = y0 + plot_h * (1 - tick / 100)
        parts.extend([_line(x0, y, x0 + plot_w, y, "#dbe3ed", 1), _text(x0 - 12, y + 5, f"{tick}%", "small", "end")])
    group_w = plot_w / len(sizes)
    bar_w = group_w / (len(algorithms) + 1)
    for index, size in enumerate(sizes):
        for alg_index, algorithm in enumerate(algorithms):
            values = [float(r["risk_coverage"]) for r in rows if r["status"] == "ok"
                      and int(r["n_tasks"]) == size and r["algorithm"] == algorithm
                      and float(r["risk_weight"]) == 1.0 and r["budget_level"] == "medium"]
            if not values:
                continue
            value = mean(values)
            h = plot_h * value
            x = x0 + index * group_w + 7 + alg_index * bar_w
            parts.append(f'<rect x="{x:.1f}" y="{y0+plot_h-h:.1f}" width="{bar_w-3:.1f}" height="{h:.1f}" fill="{COLORS[algorithm]}"/>')
        parts.append(_text(x0 + (index + 0.5) * group_w, y0 + plot_h + 27, str(size), "label", "middle"))
    parts.extend([_line(x0, y0, x0, y0 + plot_h, "#52657a"),
                  _text(x0 + plot_w / 2, 570, "Number of tasks", "label", "middle")])
    _legend(parts, algorithms)
    return _svg(parts)


def pareto(rows: list[dict]) -> str:
    parts = [_text(75, 55, "Risk coverage versus route cost", "title"),
             _text(75, 79, "50 tasks · risk weight 1 · each marker is a budget-level mean", "small")]
    subset = [r for r in rows if r["status"] == "ok" and int(r["n_tasks"]) == 50
              and float(r["risk_weight"]) == 1.0]
    x0, y0, w, h = 85, 130, 610, 390
    points = []
    for algorithm in COLORS:
        for budget in ("tight", "medium", "loose"):
            group = [r for r in subset if r["algorithm"] == algorithm and r["budget_level"] == budget]
            if group:
                points.append((algorithm, budget, mean(float(r["route_cost"]) for r in group),
                               mean(float(r["risk_coverage"]) for r in group)))
    max_cost = max((p[2] for p in points), default=1) * 1.12
    max_risk = max((p[3] for p in points), default=1) * 1.15
    for tick in range(6):
        x = x0 + w * tick / 5
        y = y0 + h * (1 - tick / 5)
        parts.extend([_line(x, y0, x, y0 + h, "#dbe3ed", 1),
                      _line(x0, y, x0 + w, y, "#dbe3ed", 1),
                      _text(x, y0 + h + 22, f"{max_cost*tick/5:.0f}", "small", "middle"),
                      _text(x0 - 12, y + 4, f"{max_risk*tick/5:.0%}", "small", "end")])
    for algorithm in COLORS:
        series = [p for p in points if p[0] == algorithm]
        for a, b in zip(series, series[1:]):
            parts.append(_line(x0 + w*a[2]/max_cost, y0 + h*(1-a[3]/max_risk),
                               x0 + w*b[2]/max_cost, y0 + h*(1-b[3]/max_risk), COLORS[algorithm], 2))
        for _, budget, cost, risk in series:
            x, y = x0 + w*cost/max_cost, y0 + h*(1-risk/max_risk)
            parts.append(_circle(x, y, 6 if budget == "medium" else 4, COLORS[algorithm]))
    frontier = []
    best_risk = -1.0
    for point in sorted(points, key=lambda item: (item[2], -item[3])):
        if point[3] > best_risk + 1e-9:
            frontier.append(point)
            best_risk = point[3]
    for a, b in zip(frontier, frontier[1:]):
        x1, y1 = x0+w*a[2]/max_cost, y0+h*(1-a[3]/max_risk)
        x2, y2 = x0+w*b[2]/max_cost, y0+h*(1-b[3]/max_risk)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#172033" stroke-width="2" stroke-dasharray="6 4"/>')
    parts.extend([_text(x0+w/2, 570, "Route cost (time units)", "label", "middle")])
    _legend(parts, [name for name in COLORS if name != "optimal_dp"])
    parts.append(_text(750, 224, "Small = tight/loose; large = medium", "small"))
    parts.append(_text(750, 246, "Dashed = Pareto frontier of means", "small"))
    return _svg(parts)


def lambda_curve(rows: list[dict]) -> str:
    parts = [_text(75, 55, "Risk coverage versus risk weight", "title"),
             _text(75, 79, "50 tasks · medium budget · mean across all distributions", "small")]
    weights = sorted({float(r["risk_weight"]) for r in rows})
    x0, y0, w, h = 85, 130, 610, 390
    for tick in range(0, 101, 20):
        y = y0 + h*(1-tick/100)
        parts.extend([_line(x0, y, x0+w, y, "#dbe3ed", 1), _text(x0-12, y+4, f"{tick}%", "small", "end")])
    for weight in weights:
        parts.append(_text(x0 + w*weight/max(weights), y0+h+25, f"{weight:g}", "small", "middle"))
    for algorithm in COLORS:
        series = []
        for weight in weights:
            values = [float(r["risk_coverage"]) for r in rows if r["status"] == "ok"
                      and int(r["n_tasks"]) == 50 and r["algorithm"] == algorithm
                      and float(r["risk_weight"]) == weight and r["budget_level"] == "medium"]
            if values:
                series.append((x0+w*weight/max(weights), y0+h*(1-mean(values))))
        for a, b in zip(series, series[1:]):
            parts.append(_line(*a, *b, COLORS[algorithm], 2.5))
        for x, y in series:
            parts.append(_circle(x, y, 4.5, COLORS[algorithm]))
    parts.append(_text(x0+w/2, 570, "Risk weight λ", "label", "middle"))
    _legend(parts, [name for name in COLORS if name != "optimal_dp"])
    return _svg(parts)


def route_map() -> str:
    base = reference_scenario()
    scenario = replace(base, hazard_zones=(HazardZone(3, 1, 2, 1.5),),
                       max_flight_distance=30, battery_capacity=36, battery_reserve=6,
                       max_flight_exposure=8)
    result = local_search(scenario)
    width, height = 900, 600
    x0, y0, scale = 420, 310, 27
    xy = lambda x, y: (x0 + x*scale, y0 - y*scale)
    parts = [_text(50, 52, "Inspection route and asset risk", "title"),
             _text(50, 77, "Reference 13-task scenario · local search · circular flight hazard", "small")]
    for gx in range(-8, 9, 2):
        a, b = xy(gx, -7), xy(gx, 7)
        parts.append(_line(*a, *b, "#e5edf5", 1))
    for gy in range(-6, 7, 2):
        a, b = xy(-8, gy), xy(8, gy)
        parts.append(_line(*a, *b, "#e5edf5", 1))
    for zone in scenario.hazard_zones:
        x, y = xy(zone.x, zone.y)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{zone.radius*scale}" fill="#dc2626" fill-opacity="0.12" stroke="#dc2626" stroke-dasharray="6 4"/>')
    by_id = {t.task_id: t for t in scenario.tasks}
    nodes = [None] + [by_id[i] for i in result.route] + [None]
    for a, b in zip(nodes, nodes[1:]):
        ax, ay = xy(0, 0) if a is None else xy(a.x, a.y)
        bx, by = xy(0, 0) if b is None else xy(b.x, b.y)
        parts.append(_line(ax, ay, bx, by, "#2563eb", 3))
    for task in scenario.tasks:
        x, y = xy(task.x, task.y)
        selected = task.task_id in result.route
        color = "#b91c1c" if task.risk >= 7 else "#f59e0b" if task.risk >= 5 else "#64748b"
        parts.append(_circle(x, y, 8 if selected else 5, color, 1 if selected else 0.65))
        parts.append(_text(x+10, y-9, f"{task.task_id} ({task.risk:g})", "small"))
    parts.append(_circle(*xy(0, 0), 10, "#172033"))
    parts.append(_text(*xy(0.5, -0.5), "Depot", "small"))
    parts.extend([_text(690, 155, f"Tasks inspected: {len(result.route)}/13", "label"),
                  _text(690, 184, f"Captured risk: {result.captured_risk:.1f}/74", "label"),
                  _text(690, 213, f"Route time: {result.route_cost:.1f}/26", "label"),
                  _text(690, 242, f"Flight distance: {result.route_distance:.1f}/30", "label"),
                  _text(690, 271, f"Exposure: {result.flight_exposure:.1f}/8", "label")])
    return _svg(parts, width, height)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw editable SVG benchmark figures")
    parser.add_argument("--runs", type=Path, default=Path("results/v0.3/runs.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/v0.3/figures"))
    args = parser.parse_args()
    rows = _read_runs(args.runs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, graphic in {
        "risk_coverage_by_size.svg": performance(rows),
        "risk_coverage_vs_cost.svg": pareto(rows),
        "risk_weight_sensitivity.svg": lambda_curve(rows),
        "reference_route.svg": route_map(),
    }.items():
        (args.output_dir / filename).write_text(graphic, encoding="utf-8")
    print(f"Wrote 4 SVG figures to {args.output_dir}")


if __name__ == "__main__":
    main()
