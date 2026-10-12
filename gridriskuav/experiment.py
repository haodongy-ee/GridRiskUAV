from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean

from .baselines import ALGORITHMS
from .scenarios import RISK_DISTRIBUTIONS, generate_scenario


FIELDS = [
    "scenario_id", "n_tasks", "risk_distribution", "seed", "budget",
    "algorithm", "status", "selected_tasks", "task_coverage", "captured_value",
    "captured_risk", "risk_coverage", "route_cost", "objective", "runtime_ms", "route",
]


def run_experiment(
    output_dir: Path,
    sizes: list[int],
    distributions: list[str],
    replicates: int,
    base_seed: int,
    risk_weight: float,
) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = output_dir / "scenarios"
    rows: list[dict[str, object]] = []
    for n_tasks in sizes:
        for distribution_index, distribution in enumerate(distributions):
            for replicate in range(replicates):
                seed = base_seed + n_tasks * 10_000 + distribution_index * 1_000 + replicate
                scenario = generate_scenario(n_tasks, distribution, seed, risk_weight=risk_weight)
                scenario.to_json(scenario_dir / f"{scenario.scenario_id}.json")
                for algorithm_name, algorithm in ALGORITHMS.items():
                    result = algorithm(scenario)
                    rows.append({
                        "scenario_id": scenario.scenario_id,
                        "n_tasks": n_tasks,
                        "risk_distribution": distribution,
                        "seed": seed,
                        "budget": scenario.budget,
                        "algorithm": algorithm_name,
                        "status": result.status,
                        "selected_tasks": len(result.route) if result.status == "ok" else "",
                        "task_coverage": result.task_coverage if result.status == "ok" else "",
                        "captured_value": result.captured_value if result.status == "ok" else "",
                        "captured_risk": result.captured_risk if result.status == "ok" else "",
                        "risk_coverage": result.risk_coverage if result.status == "ok" else "",
                        "route_cost": result.route_cost if result.status == "ok" else "",
                        "objective": result.objective if result.status == "ok" else "",
                        "runtime_ms": result.runtime_ms,
                        "route": " ".join(map(str, result.route)),
                    })
    _write_csv(output_dir / "runs.csv", rows, FIELDS)
    _write_summary(output_dir / "summary.csv", rows)
    _write_report(output_dir / "REPORT.md", rows, sizes, distributions, replicates, base_seed, risk_weight)
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    metrics = ["task_coverage", "captured_risk", "risk_coverage", "route_cost", "objective", "runtime_ms"]
    groups: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        key = (row["n_tasks"], row["risk_distribution"], row["algorithm"])
        groups.setdefault(key, []).append(row)
    output = []
    for (n_tasks, distribution, algorithm), group in sorted(groups.items(), key=lambda item: item[0]):
        successful = [row for row in group if row["status"] == "ok"]
        record: dict[str, object] = {
            "n_tasks": n_tasks,
            "risk_distribution": distribution,
            "algorithm": algorithm,
            "successful_runs": len(successful),
            "total_runs": len(group),
        }
        for metric in metrics:
            values = [float(row[metric]) for row in successful if row[metric] != ""]
            record[f"mean_{metric}"] = mean(values) if values else ""
        output.append(record)
    fields = ["n_tasks", "risk_distribution", "algorithm", "successful_runs", "total_runs"] + [f"mean_{m}" for m in metrics]
    _write_csv(path, output, fields)


def _write_report(
    path: Path,
    rows: list[dict[str, object]],
    sizes: list[int],
    distributions: list[str],
    replicates: int,
    base_seed: int,
    risk_weight: float,
) -> None:
    successful = [row for row in rows if row["status"] == "ok"]
    groups: dict[tuple[int, str], list[dict[str, object]]] = {}
    for row in successful:
        groups.setdefault((int(row["n_tasks"]), str(row["algorithm"])), []).append(row)

    lines = [
        "# GridRiskUAV batch experiment report",
        "",
        "## Configuration",
        "",
        f"- Task counts: {', '.join(map(str, sizes))}",
        f"- Risk distributions: {', '.join(distributions)}",
        f"- Replicates per setting: {replicates}",
        f"- Base random seed: {base_seed}",
        f"- Risk weight: {risk_weight:g}",
        f"- Generated scenarios: {len(sizes) * len(distributions) * replicates}",
        "- Exact baseline limit: 18 tasks",
        "",
        "## Aggregate results",
        "",
        "Values below are means across all requested risk distributions and replicates.",
        "",
        "| tasks | algorithm | runs | task coverage | risk coverage | captured risk | route cost | objective | runtime (ms) |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for n_tasks in sizes:
        for algorithm in ALGORITHMS:
            group = groups.get((n_tasks, algorithm), [])
            if not group:
                lines.append(f"| {n_tasks} | {algorithm} | 0 | — | — | — | — | — | — |")
                continue
            avg = lambda metric: mean(float(row[metric]) for row in group)
            lines.append(
                f"| {n_tasks} | {algorithm} | {len(group)} | {avg('task_coverage'):.1%} | "
                f"{avg('risk_coverage'):.1%} | {avg('captured_risk'):.2f} | {avg('route_cost'):.2f} | "
                f"{avg('objective'):.2f} | {avg('runtime_ms'):.3f} |"
            )

    lines.extend([
        "",
        "## Interpretation notes",
        "",
        "- Task coverage and risk coverage are deliberately separate. A planner may inspect fewer tasks while capturing more total risk.",
        "- `optimal_dp` is an exact reference for scenarios with at most 18 tasks; skipped cells are not treated as zero performance.",
        "- Runtime measures planning only and excludes scenario generation and file writing.",
        "- The current synthetic benchmark is a baseline, not evidence of field performance. Real coordinates, no-fly constraints, battery reserve, and weather should be introduced as separate model terms.",
        "",
        "## Files",
        "",
        "- `runs.csv`: per-run metrics and routes.",
        "- `summary.csv`: means for each task-count / distribution / algorithm combination.",
        "- `scenarios/`: serialized inputs for exact replay.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reproducible GridRiskUAV baseline experiments")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--sizes", type=int, nargs="+", default=[10, 15, 20])
    parser.add_argument("--distributions", nargs="+", choices=RISK_DISTRIBUTIONS, default=list(RISK_DISTRIBUTIONS))
    parser.add_argument("--replicates", type=int, default=5)
    parser.add_argument("--base-seed", type=int, default=20261013)
    parser.add_argument("--risk-weight", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    rows = run_experiment(args.output_dir, args.sizes, args.distributions, args.replicates, args.base_seed, args.risk_weight)
    print(f"Wrote {len(rows)} algorithm runs to {args.output_dir}")


if __name__ == "__main__":
    main()

