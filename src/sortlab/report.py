"""Chart and markdown report generation."""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from sortlab.bench import BenchmarkReport, RunResult
from sortlab.complexity import classify, fit_power_law

_TABLE_START = "<!-- sortlab:tables:start -->"
_TABLE_END = "<!-- sortlab:tables:end -->"

_STYLE: dict[str, object] = {
    "figure.facecolor": "white",
    "axes.facecolor": "#fafafa",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 10,
}


def _meta_caption(report: BenchmarkReport) -> str:
    m = report.meta
    return f"{m.cpu_model} · Python {m.python_version} · {m.system}"


def _ok_times(
    report: BenchmarkReport,
    *,
    algorithm: str | None = None,
    distribution: str | None = None,
) -> list[RunResult]:
    out: list[RunResult] = []
    for result in report.results:
        if result.status != "ok" or result.timing is None:
            continue
        if algorithm is not None and result.algorithm != algorithm:
            continue
        if distribution is not None and result.distribution != distribution:
            continue
        out.append(result)
    return out


def chart_time_vs_n(report: BenchmarkReport, distribution: str, out: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        algorithms = sorted({r.algorithm for r in report.results})
        for name in algorithms:
            rows = _ok_times(report, algorithm=name, distribution=distribution)
            if not rows:
                continue
            rows = sorted(rows, key=lambda r: r.n)
            ns = [r.n for r in rows]
            ts = [r.timing.median_s for r in rows if r.timing is not None]
            style = {"linewidth": 2.5, "color": "black"} if name == "builtin_timsort" else {}
            ax.plot(ns, ts, marker="o", label=name, **style)
        skipped = [
            r
            for r in report.results
            if r.distribution == distribution and r.status == "skipped_max_n"
        ]
        if skipped:
            ax.text(
                0.02,
                0.02,
                "skipped: n > max_n present",
                transform=ax.transAxes,
                fontsize=8,
                color="#666666",
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("n")
        ax.set_ylabel("median time (s)")
        ax.set_title(f"Time vs n · {distribution}")
        ax.legend(fontsize=7, loc="upper left", ncol=2)
        fig.text(0.5, 0.01, _meta_caption(report), ha="center", fontsize=8, color="#444444")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        plt.close(fig)


def chart_distribution_comparison(report: BenchmarkReport, n: int, out: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(10, 5.5))
        algorithms = sorted({r.algorithm for r in report.results})
        distributions = sorted({r.distribution for r in report.results})
        x = np.arange(len(algorithms))
        width = 0.8 / max(len(distributions), 1)
        for i, dist in enumerate(distributions):
            heights: list[float] = []
            for algo in algorithms:
                match = [
                    r
                    for r in report.results
                    if r.algorithm == algo
                    and r.distribution == dist
                    and r.n == n
                    and r.status == "ok"
                    and r.timing is not None
                ]
                heights.append(match[0].timing.median_s if match else 0.0)
            ax.bar(x + i * width, heights, width=width, label=dist)
        ax.set_xticks(x + width * len(distributions) / 2)
        ax.set_xticklabels(algorithms, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("median time (s)")
        ax.set_title(f"Distribution comparison · n={n}")
        ax.legend(fontsize=7, ncol=2)
        fig.text(0.5, 0.01, _meta_caption(report), ha="center", fontsize=8, color="#444444")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        plt.close(fig)


def chart_operation_counts(report: BenchmarkReport, out: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        # Prefer random / largest shared n with counters.
        rows = [r for r in report.results if r.status == "ok" and r.counters is not None]
        if not rows:
            fig.savefig(out)
            plt.close(fig)
            return
        target_n = max(r.n for r in rows)
        dist = "random"
        points = [
            r for r in rows if r.n == target_n and r.distribution == dist and r.counters is not None
        ]
        if not points:
            points = [r for r in rows if r.n == target_n and r.counters is not None]
        names = [r.algorithm for r in points]
        comps = [r.counters.comparisons if r.counters else 0 for r in points]
        writes = [r.counters.writes if r.counters else 0 for r in points]
        x = np.arange(len(names))
        ax.bar(x - 0.2, comps, 0.4, label="comparisons")
        ax.bar(x + 0.2, writes, 0.4, label="writes")
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("count")
        ax.set_title(f"Operation counts · n={target_n}")
        ax.legend()
        fig.text(0.5, 0.01, _meta_caption(report), ha="center", fontsize=8, color="#444444")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        plt.close(fig)


def chart_memory(report: BenchmarkReport, out: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        plotted = False
        for name in ("merge_sort", "heap_sort", "quick_sort_median3"):
            rows = [
                r
                for r in report.results
                if r.algorithm == name
                and r.status == "ok"
                and r.resources is not None
                and r.distribution == "random"
            ]
            if not rows:
                continue
            rows = sorted(rows, key=lambda r: r.n)
            ns = [r.n for r in rows]
            mem = [
                float(r.resources["tracemalloc_peak_bytes"])
                for r in rows
                if r.resources is not None
            ]
            ax.plot(ns, mem, marker="o", label=name)
            plotted = True
        if not plotted:
            ax.text(0.5, 0.5, "no profile data", ha="center", va="center")
        ax.set_xlabel("n")
        ax.set_ylabel("tracemalloc peak (bytes)")
        ax.set_title("Memory vs n (random)")
        ax.legend()
        fig.text(0.5, 0.01, _meta_caption(report), ha="center", fontsize=8, color="#444444")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        plt.close(fig)


def chart_complexity_fit(report: BenchmarkReport, out: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        for name in sorted({r.algorithm for r in report.results}):
            rows = _ok_times(report, algorithm=name, distribution="random")
            if len(rows) < 2:
                continue
            rows = sorted(rows, key=lambda r: r.n)
            ns = [r.n for r in rows]
            ts = [r.timing.median_s for r in rows if r.timing is not None]
            ax.scatter(ns, ts, s=18, label=name)
            if len(ns) >= 4:
                fit = fit_power_law(ns, ts)
                if fit.r_squared >= 0.95:
                    grid = np.array(ns, dtype=float)
                    pred = np.exp(fit.intercept) * grid**fit.exponent
                    ax.plot(grid, pred, linewidth=1, alpha=0.7)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("n")
        ax.set_ylabel("median time (s)")
        ax.set_title("Complexity fit · random")
        ax.legend(fontsize=7, ncol=2)
        fig.text(0.5, 0.01, _meta_caption(report), ha="center", fontsize=8, color="#444444")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        plt.close(fig)


def heatmap_algorithm_x_distribution(report: BenchmarkReport, n: int, out: Path) -> None:
    with plt.rc_context(_STYLE):
        algorithms = sorted({r.algorithm for r in report.results})
        distributions = sorted({r.distribution for r in report.results})
        data = np.full((len(algorithms), len(distributions)), np.nan)
        for i, algo in enumerate(algorithms):
            for j, dist in enumerate(distributions):
                match = [
                    r
                    for r in report.results
                    if r.algorithm == algo and r.distribution == dist and r.n == n
                ]
                if not match:
                    continue
                row = match[0]
                if row.status == "ok" and row.timing is not None:
                    data[i, j] = row.timing.median_s
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(np.log10(data + 1e-12), aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(distributions)))
        ax.set_xticklabels(distributions, rotation=45, ha="right")
        ax.set_yticks(range(len(algorithms)))
        ax.set_yticklabels(algorithms, fontsize=8)
        ax.set_title(f"Heatmap log10(time) · n={n}")
        fig.colorbar(im, ax=ax, fraction=0.03)
        fig.text(0.5, 0.01, _meta_caption(report), ha="center", fontsize=8, color="#444444")
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=120)
        plt.close(fig)


def markdown_tables(report: BenchmarkReport) -> str:
    lines: list[str] = []
    lines.append("### Measured exponents (random)")
    lines.append("")
    lines.append("| Algorithm | Theory | Measured exponent | R² | Classification |")
    lines.append("|---|---|---:|---:|---|")
    for name in sorted({r.algorithm for r in report.results}):
        rows = _ok_times(report, algorithm=name, distribution="random")
        rows = sorted(rows, key=lambda r: r.n)
        if len(rows) < 4:
            lines.append(f"| `{name}` | — | — | — | nierozstrzygnięte |")
            continue
        from sortlab.registry import get

        spec = get(name)
        ns = [r.n for r in rows]
        ts = [r.timing.median_s for r in rows if r.timing is not None]
        fit = fit_power_law(ns, ts)
        label = classify(fit)
        lines.append(
            f"| `{name}` | {spec.complexity} | {fit.exponent:.2f} | {fit.r_squared:.3f} | {label} |"
        )
    lines.append("")
    skipped = sum(1 for r in report.results if r.status != "ok")
    lines.append(f"_Skipped/timeout rows in matrix: {skipped}_")
    lines.append("")
    return "\n".join(lines)


def inject_tables(readme_path: Path, tables: str) -> None:
    text = readme_path.read_text(encoding="utf-8")
    if _TABLE_START not in text or _TABLE_END not in text:
        raise ValueError("README missing sortlab table markers")
    pattern = re.compile(
        re.escape(_TABLE_START) + r".*?" + re.escape(_TABLE_END),
        flags=re.DOTALL,
    )
    replacement = f"{_TABLE_START}\n{tables}{_TABLE_END}"
    new_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError("failed to inject tables")
    readme_path.write_text(new_text, encoding="utf-8")


def write_all(report: BenchmarkReport, charts_dir: Path, readme_path: Path) -> None:
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_time_vs_n(report, "random", charts_dir / "time_vs_n_random.png")
    chart_time_vs_n(report, "sorted", charts_dir / "time_vs_n_sorted.png")
    # Pick a representative n present in results.
    ns = sorted({r.n for r in report.results if r.status == "ok"})
    n_bar = ns[len(ns) // 2] if ns else 100
    chart_distribution_comparison(report, n_bar, charts_dir / "distribution_comparison.png")
    chart_operation_counts(report, charts_dir / "operation_counts.png")
    chart_memory(report, charts_dir / "memory.png")
    chart_complexity_fit(report, charts_dir / "complexity_fit.png")
    heatmap_algorithm_x_distribution(report, n_bar, charts_dir / "heatmap.png")
    inject_tables(readme_path, markdown_tables(report))
