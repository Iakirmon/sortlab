"""Command-line interface for sortlab."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from rich.console import Console
from rich.table import Table

from sortlab.bench import load, parse_sizes, run_matrix, save
from sortlab.registry import all_algorithms, discover
from sortlab.types import Distribution

console = Console()

_ALL_DISTRIBUTIONS: tuple[Distribution, ...] = (
    "random",
    "sorted",
    "reversed",
    "nearly_sorted",
    "few_unique",
    "sawtooth",
    "zipf",
)


def _cmd_list(_: argparse.Namespace) -> int:
    discover()
    table = Table(title="Registered algorithms")
    table.add_column("name")
    table.add_column("complexity")
    table.add_column("stable")
    table.add_column("in_place")
    table.add_column("max_n", justify="right")
    for spec in all_algorithms():
        table.add_row(
            spec.name,
            spec.complexity,
            str(spec.stable),
            str(spec.in_place),
            f"{spec.max_n:,}",
        )
    console.print(table)
    return 0


def _cmd_bench(args: argparse.Namespace) -> int:
    algorithms = args.algorithms.split(",") if args.algorithms else None
    distributions: list[Distribution] | None = None
    if args.distributions:
        parsed: list[Distribution] = []
        for item in args.distributions.split(","):
            name = item.strip()
            if name not in _ALL_DISTRIBUTIONS:
                raise SystemExit(f"unknown distribution: {name}")
            parsed.append(cast(Distribution, name))
        distributions = parsed
    sizes = parse_sizes(args.sizes)
    report = run_matrix(
        algorithms=algorithms,
        distributions=distributions,
        sizes=sizes,
        repeats=args.repeats,
        timeout_s=args.timeout,
        profile=args.profile,
    )
    out = Path(args.output)
    save(report, out)
    ok = sum(1 for r in report.results if r.status == "ok")
    skipped = sum(1 for r in report.results if r.status != "ok")
    console.print(f"Wrote {out} ({ok} ok, {skipped} skipped/timeout)")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from sortlab.report import write_all

    report = load(Path(args.results))
    write_all(report, Path(args.charts_dir), Path(args.readme))
    console.print(f"Charts → {args.charts_dir}; tables injected into {args.readme}")
    return 0


def _cmd_animate(args: argparse.Namespace) -> int:
    from sortlab.animate import animate

    out = Path(args.output) if args.output else Path(f"docs/animations/{args.algorithm}.gif")
    animate(args.algorithm, out, n=args.n, distribution=args.distribution)
    console.print(f"Wrote {out}")
    return 0


def _cmd_dataset(args: argparse.Namespace) -> int:
    from sortlab.datasets import write_records_csv

    path = Path(args.output)
    write_records_csv(path, rows=args.rows, seed=args.seed)
    console.print(f"Wrote {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sortlab", description="Sorting algorithm lab")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Show registered algorithms")
    p_list.set_defaults(func=_cmd_list)

    p_bench = sub.add_parser("bench", help="Run benchmark matrix")
    p_bench.add_argument("--algorithms", default=None, help="Comma-separated names")
    p_bench.add_argument("--distributions", default=None, help="Comma-separated distributions")
    p_bench.add_argument("--sizes", default="100,200,400,800,1600", help="Sizes or start:end:xF")
    p_bench.add_argument("--repeats", type=int, default=5)
    p_bench.add_argument("--timeout", type=float, default=30.0)
    p_bench.add_argument("--profile", action="store_true")
    p_bench.add_argument("-o", "--output", default="benchmarks/results/latest.json")
    p_bench.set_defaults(func=_cmd_bench)

    p_report = sub.add_parser("report", help="Generate charts and README tables")
    p_report.add_argument("--results", default="benchmarks/results/latest.json")
    p_report.add_argument("--charts-dir", default="docs/charts")
    p_report.add_argument("--readme", default="README.md")
    p_report.set_defaults(func=_cmd_report)

    p_anim = sub.add_parser("animate", help="Render algorithm animation GIF")
    p_anim.add_argument("--algorithm", required=True)
    p_anim.add_argument("--n", type=int, default=60)
    p_anim.add_argument("--distribution", default="random")
    p_anim.add_argument("--output", default=None)
    p_anim.set_defaults(func=_cmd_animate)

    p_data = sub.add_parser("dataset", help="Generate deterministic CSV dataset")
    p_data.add_argument("--rows", type=int, default=200_000)
    p_data.add_argument("-o", "--output", default="data/records.csv")
    p_data.add_argument("--seed", type=int, default=42)
    p_data.set_defaults(func=_cmd_dataset)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
