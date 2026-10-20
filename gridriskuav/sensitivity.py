"""GridRiskUAV v0.3 reproducible sensitivity experiment."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import json
import math
from pathlib import Path
from statistics import mean, stdev

from .baselines import ALGORITHMS
from .models import Scenario
from .scenarios import generate_scenario


RUN_FIELDS = [
    "scenario_id", "base_scenario_id", "n_tasks", "risk_distribution", "replicate", "seed",
    "risk_weight", "budget_level", "budget_factor", "budget", "algorithm", "status",
    "selected_tasks", "task_coverage", "captured_value", "captured_risk", "risk_coverage",
    "route_cost", "route_distance", "flight_exposure", "objective", "optimality_gap",
    "runtime_ms", "route",
]
METRICS = ["task_coverage", "captured_risk", "risk_coverage", "route_cost", "route_distance",
           "flight_exposure", "objective", "optimality_gap", "runtime_ms"]
GROUP_FIELDS = ["n_tasks", "risk_distribution", "risk_weight", "budget_level", "algorithm"]


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not config["task_counts"] or not config["risk_distributions"]:
        raise ValueError("task counts and distributions must be nonempty")
    if config["replicates"] < 1 or any(n < 0 for n in config["task_counts"]):
        raise ValueError("replicates must be positive and task counts nonnegative")
    if any(weight < 0 for weight in config["risk_weights"]):
        raise ValueError("risk weights must be nonnegative")
    if any(factor <= 0 for factor in config["budget_factors"].values()):
        raise ValueError("budget factors must be positive")
    return config


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _stats(values: list[float]) -> tuple[float | str, float | str, float | str, float | str]:
    if not values:
        return "", "", "", ""
    center = mean(values)
    sd = stdev(values) if len(values) > 1 else 0.0
    half = 1.96 * sd / math.sqrt(len(values))
    return center, sd, center - half, center + half


def summarize(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        groups.setdefault(tuple(row[field] for field in GROUP_FIELDS), []).append(row)
    summary = []
    for key, group in sorted(groups.items(), key=lambda item: item[0]):
        successful = [row for row in group if row["status"] == "ok"]
        record = dict(zip(GROUP_FIELDS, key))
        record.update(successful_runs=len(successful), total_runs=len(group))
        for metric in METRICS:
            values = [float(row[metric]) for row in successful if row[metric] != ""]
            center, sd, lower, upper = _stats(values)
            record[f"mean_{metric}"] = center
            record[f"sd_{metric}"] = sd
            record[f"ci95_low_{metric}"] = lower
            record[f"ci95_high_{metric}"] = upper
        summary.append(record)
    return summary


def run(config: dict, output_dir: Path) -> tuple[list[dict], list[dict]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = output_dir / "scenarios"
    scenario_dir.mkdir(exist_ok=True)
    rows: list[dict] = []
    for n in config["task_counts"]:
        for distribution_index, distribution in enumerate(config["risk_distributions"]):
            for replicate in range(config["replicates"]):
                seed = config["base_seed"] + n * 100_000 + distribution_index * 10_000 + replicate
                base = generate_scenario(n, distribution, seed)
                base.to_json(scenario_dir / f"{base.scenario_id}.json")
                for weight in config["risk_weights"]:
                    for budget_level, factor in config["budget_factors"].items():
                        scenario = replace(base, scenario_id=f"{base.scenario_id}_w{weight:g}_b{budget_level}",
                                           budget=base.budget * factor, risk_weight=weight)
                        results = {name: algorithm(scenario) for name, algorithm in ALGORITHMS.items()}
                        optimum = results["optimal_dp"]
                        for name, result in results.items():
                            gap = ""
                            if result.status == "ok" and optimum.status == "ok" and optimum.objective > 1e-12:
                                gap = max(0.0, (optimum.objective - result.objective) / optimum.objective)
                            rows.append({
                                "scenario_id": scenario.scenario_id,
                                "base_scenario_id": base.scenario_id,
                                "n_tasks": n,
                                "risk_distribution": distribution,
                                "replicate": replicate,
                                "seed": seed,
                                "risk_weight": weight,
                                "budget_level": budget_level,
                                "budget_factor": factor,
                                "budget": scenario.budget,
                                "algorithm": name,
                                "status": result.status,
                                "selected_tasks": len(result.route) if result.status == "ok" else "",
                                "task_coverage": result.task_coverage if result.status == "ok" else "",
                                "captured_value": result.captured_value if result.status == "ok" else "",
                                "captured_risk": result.captured_risk if result.status == "ok" else "",
                                "risk_coverage": result.risk_coverage if result.status == "ok" else "",
                                "route_cost": result.route_cost if result.status == "ok" else "",
                                "route_distance": result.route_distance if result.status == "ok" else "",
                                "flight_exposure": result.flight_exposure if result.status == "ok" else "",
                                "objective": result.objective if result.status == "ok" else "",
                                "optimality_gap": gap,
                                "runtime_ms": result.runtime_ms if result.status == "ok" else "",
                                "route": " ".join(map(str, result.route)),
                            })
    summary = summarize(rows)
    _write_csv(output_dir / "runs.csv", rows, RUN_FIELDS)
    metric_fields = [f"{stat}_{metric}" for metric in METRICS
                     for stat in ("mean", "sd", "ci95_low", "ci95_high")]
    _write_csv(output_dir / "summary.csv", summary,
               GROUP_FIELDS + ["successful_runs", "total_runs"] + metric_fields)
    (output_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    _write_report(output_dir / "REPORT.md", config, rows, summary)
    return rows, summary


def _write_report(path: Path, config: dict, rows: list[dict], summary: list[dict]) -> None:
    lines = ["# GridRiskUAV v0.3 experiment", "",
             f"Generated {len(rows)} planner records from {len(rows) // len(ALGORITHMS)} scenario settings.",
             f"Each task count/distribution/weight/budget cell uses {config['replicates']} independent seeds.",
             "95% intervals use mean ± 1.96 × sample standard deviation / √n.",
             "Runtime measures planning only, on the machine that produced these files.", "",
             "## Medium budget, risk weight 1", "",
             "| Tasks | Algorithm | Runs | Task coverage | Risk coverage | Captured risk | Route cost | Objective | Gap | Runtime (ms) |",
             "|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|" ]
    for n in config["task_counts"]:
        for name in ALGORITHMS:
            subset = [row for row in rows if row["n_tasks"] == n and row["algorithm"] == name
                      and row["risk_weight"] == 1.0 and row["budget_level"] == "medium" and row["status"] == "ok"]
            if not subset:
                lines.append(f"| {n} | {name} | 0 | — | — | — | — | — | — | — |")
                continue
            avg = lambda field: mean(float(row[field]) for row in subset if row[field] != "")
            gaps = [float(row["optimality_gap"]) for row in subset if row["optimality_gap"] != ""]
            gap = f"{mean(gaps):.1%}" if gaps else "—"
            lines.append(f"| {n} | {name} | {len(subset)} | {avg('task_coverage'):.1%} | "
                         f"{avg('risk_coverage'):.1%} | {avg('captured_risk'):.2f} | "
                         f"{avg('route_cost'):.2f} | {avg('objective'):.2f} | {gap} | "
                         f"{avg('runtime_ms'):.2f} |")
    lines.extend(["", "## Interpretation", "",
                  "- Task coverage and risk coverage answer different questions.",
                  "- Exact DP runs only for task counts up to 18 and without additional flight-resource constraints; skipped runs are blank, not zero.",
                  "- The objective changes with risk weight, so compare objectives only within the same weight and scenario.",
                  "- Scenario JSON files contain base task sets. `runs.csv` records the applied risk weight and budget factor for replay.",
                  "- Synthetic results do not establish field performance.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GridRiskUAV sensitivity benchmark")
    parser.add_argument("--config", type=Path, default=Path("config/experiment.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/v0.3"))
    parser.add_argument("--replicates", type=int, help="Override replicate count for a smoke test")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.replicates is not None:
        config["replicates"] = args.replicates
    rows, _ = run(config, args.output_dir)
    print(f"Wrote {len(rows)} planner records to {args.output_dir}")


if __name__ == "__main__":
    main()
