"""Benchmark runner: timing protocol, counting mode, JSON persistence."""

from __future__ import annotations

import gc
import json
import os
import platform
import statistics
import subprocess
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from sortlab import __version__
from sortlab.datasets import generate
from sortlab.instrument import Counters
from sortlab.instrument import count_run as instrument_count_run
from sortlab.registry import all_algorithms, get
from sortlab.types import AlgorithmSpec, Distribution, SortlabError

try:
    import signal
except ImportError:  # pragma: no cover
    signal = None  # type: ignore[assignment]


class BenchmarkTimeoutError(SortlabError):
    """Raised when a single timing run exceeds the hard timeout."""


@dataclass(frozen=True, slots=True)
class TimingResult:
    median_s: float
    min_s: float
    repeats: int


@dataclass(frozen=True, slots=True)
class RunResult:
    algorithm: str
    distribution: str
    n: int
    timing: TimingResult | None
    counters: Counters | None
    resources: dict[str, Any] | None
    status: Literal["ok", "skipped_max_n", "timeout"]


@dataclass(frozen=True, slots=True)
class ReportMeta:
    cpu_model: str
    cpu_count: int
    python_version: str
    system: str
    sortlab_version: str
    created_at_utc: str


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    meta: ReportMeta
    results: tuple[RunResult, ...]


def _cpu_model() -> str:
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
            ).strip()
            if out:
                return out
        except (OSError, subprocess.CalledProcessError):
            pass
    return platform.processor() or platform.machine() or "unknown"


def collect_meta() -> ReportMeta:
    return ReportMeta(
        cpu_model=_cpu_model(),
        cpu_count=os.cpu_count() or 1,
        python_version=platform.python_version(),
        system=f"{platform.system()} {platform.release()}",
        sortlab_version=__version__,
        created_at_utc=datetime.now(UTC).isoformat(),
    )


def count_run(spec: AlgorithmSpec, data: Sequence[Any]) -> Counters:
    """Count comparisons/reads/writes without mutating the caller's list."""
    return instrument_count_run(spec.func, data)


def time_run(
    spec: AlgorithmSpec,
    data: Sequence[Any],
    *,
    repeats: int = 5,
    warmup: int = 1,
    timeout_s: float = 30.0,
) -> TimingResult:
    """Time ``spec.func`` with fresh copies, warmup, GC disabled, median reported."""
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

    def _timed_call() -> float:
        working = list(data)
        start = time.perf_counter()
        spec.func(working)
        return time.perf_counter() - start

    def _with_timeout(callable_fn: Any) -> float:
        if signal is None or not hasattr(signal, "SIGALRM"):
            return float(callable_fn())

        def _handler(_signum: int, _frame: Any) -> None:
            raise BenchmarkTimeoutError(
                f"{spec.name} exceeded timeout of {timeout_s}s",
            )

        previous = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_s)
        try:
            return float(callable_fn())
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, previous)

    gc.disable()
    try:
        for _ in range(warmup):
            _with_timeout(_timed_call)
        samples: list[float] = []
        for _ in range(repeats):
            samples.append(_with_timeout(_timed_call))
    finally:
        gc.enable()

    return TimingResult(
        median_s=statistics.median(samples),
        min_s=min(samples),
        repeats=repeats,
    )


def parse_sizes(spec: str | Sequence[int]) -> list[int]:
    """Parse ``100,200,400`` or geometric ``500:16000:x2`` size specs."""
    if not isinstance(spec, str):
        return [int(x) for x in spec]
    text = spec.strip()
    parts = text.split(":")
    if len(parts) == 3 and parts[2].lower().startswith("x"):
        start = int(parts[0])
        end = int(parts[1])
        factor = float(parts[2][1:])
        if start <= 0 or end < start or factor <= 1.0:
            raise ValueError(f"invalid geometric sizes: {spec}")
        sizes: list[int] = []
        value = float(start)
        while int(value) <= end:
            sizes.append(int(value))
            value *= factor
        return sizes
    return [int(part.strip()) for part in text.split(",") if part.strip()]


def run_matrix(
    algorithms: Sequence[str] | None = None,
    distributions: Sequence[Distribution] | None = None,
    sizes: Sequence[int] | None = None,
    *,
    repeats: int = 5,
    warmup: int = 1,
    timeout_s: float = 30.0,
    profile: bool = False,
    seed: int = 42,
) -> BenchmarkReport:
    """Run the full algorithm × distribution × size matrix."""
    algo_names = list(algorithms) if algorithms is not None else [s.name for s in all_algorithms()]
    dists: list[Distribution] = (
        list(distributions)
        if distributions is not None
        else [
            "random",
            "sorted",
            "reversed",
            "nearly_sorted",
            "few_unique",
            "sawtooth",
            "zipf",
        ]
    )
    ns = list(sizes) if sizes is not None else [100, 200, 400, 800, 1600]

    results: list[RunResult] = []
    for name in algo_names:
        spec = get(name)
        for distribution in dists:
            for n in ns:
                if n > spec.max_n:
                    results.append(
                        RunResult(
                            algorithm=name,
                            distribution=distribution,
                            n=n,
                            timing=None,
                            counters=None,
                            resources=None,
                            status="skipped_max_n",
                        )
                    )
                    continue
                data = generate(distribution, n, seed=seed)
                try:
                    timing = time_run(
                        spec,
                        data,
                        repeats=repeats,
                        warmup=warmup,
                        timeout_s=timeout_s,
                    )
                    counters = count_run(spec, data)
                    resources: dict[str, Any] | None = None
                    if profile:
                        from sortlab.profile import profiled

                        with profiled(min_duration_s=0.0) as sample:
                            working = list(data)
                            spec.func(working)
                        resources = {
                            "peak_rss_bytes": sample.peak_rss_bytes,
                            "tracemalloc_peak_bytes": sample.tracemalloc_peak_bytes,
                            "cpu_percent_samples": sample.cpu_percent_samples,
                            "sample_interval_s": sample.sample_interval_s,
                        }
                    results.append(
                        RunResult(
                            algorithm=name,
                            distribution=distribution,
                            n=n,
                            timing=timing,
                            counters=counters,
                            resources=resources,
                            status="ok",
                        )
                    )
                except (BenchmarkTimeoutError, RecursionError):
                    results.append(
                        RunResult(
                            algorithm=name,
                            distribution=distribution,
                            n=n,
                            timing=None,
                            counters=None,
                            resources=None,
                            status="timeout",
                        )
                    )
    return BenchmarkReport(meta=collect_meta(), results=tuple(results))


def _counters_to_dict(counters: Counters | None) -> dict[str, int] | None:
    if counters is None:
        return None
    return {
        "comparisons": counters.comparisons,
        "writes": counters.writes,
        "reads": counters.reads,
    }


def _result_to_dict(result: RunResult) -> dict[str, Any]:
    return {
        "algorithm": result.algorithm,
        "distribution": result.distribution,
        "n": result.n,
        "timing": asdict(result.timing) if result.timing is not None else None,
        "counters": _counters_to_dict(result.counters),
        "resources": result.resources,
        "status": result.status,
    }


def save(report: BenchmarkReport, path: Path) -> None:
    payload = {
        "meta": asdict(report.meta),
        "results": [_result_to_dict(r) for r in report.results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load(path: Path) -> BenchmarkReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results: list[RunResult] = []
    for raw in payload["results"]:
        timing = None
        if raw["timing"] is not None:
            timing = TimingResult(**raw["timing"])
        counters = None
        if raw["counters"] is not None:
            counters = Counters(**raw["counters"])
        results.append(
            RunResult(
                algorithm=raw["algorithm"],
                distribution=raw["distribution"],
                n=raw["n"],
                timing=timing,
                counters=counters,
                resources=raw.get("resources"),
                status=raw["status"],
            )
        )
    return BenchmarkReport(meta=ReportMeta(**payload["meta"]), results=tuple(results))
