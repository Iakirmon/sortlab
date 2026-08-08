"""Benchmark runner protocol and serialization tests."""

from __future__ import annotations

import time
from collections.abc import MutableSequence
from pathlib import Path
from typing import Any

import pytest

from sortlab.bench import (
    BenchmarkTimeoutError,
    load,
    parse_sizes,
    run_matrix,
    save,
    time_run,
)
from sortlab.types import AlgorithmSpec


def test_parse_sizes_list_and_geometric() -> None:
    assert parse_sizes("100,200,400") == [100, 200, 400]
    assert parse_sizes("500:16000:x2") == [500, 1000, 2000, 4000, 8000, 16000]


def test_roundtrip_serialization(tmp_path: Path) -> None:
    report = run_matrix(
        algorithms=["insertion_sort", "builtin_timsort"],
        distributions=["random"],
        sizes=[50, 100],
        repeats=2,
        warmup=1,
        timeout_s=30.0,
    )
    path = tmp_path / "r.json"
    save(report, path)
    loaded = load(path)
    assert loaded.meta.python_version == report.meta.python_version
    assert len(loaded.results) == len(report.results)
    assert loaded.results[0].algorithm == report.results[0].algorithm
    assert loaded.results[0].status == "ok"
    assert loaded.results[0].timing is not None


def test_skipped_max_n_does_not_run_function() -> None:
    calls = 0

    def spy(a: MutableSequence[Any]) -> None:
        nonlocal calls
        calls += 1

    # Temporarily replace bubble_sort func via a dedicated matrix path:
    # use an algorithm with tiny max_n by constructing a one-off matrix entry.
    from sortlab import bench as bench_mod
    from sortlab.types import AlgorithmSpec

    original_get = bench_mod.get

    tiny = AlgorithmSpec(
        name="tiny_probe",
        func=spy,
        complexity="O(1)",
        expected_exponent=1.0,
        stable=True,
        in_place=True,
        comparison_based=True,
        max_n=10,
    )

    def fake_get(name: str) -> AlgorithmSpec:
        if name == "tiny_probe":
            return tiny
        return original_get(name)

    bench_mod.get = fake_get  # type: ignore[assignment]
    try:
        report = run_matrix(
            algorithms=["tiny_probe"],
            distributions=["random"],
            sizes=[5, 100],
            repeats=1,
            warmup=0,
        )
    finally:
        bench_mod.get = original_get  # type: ignore[assignment]

    statuses = {(r.n, r.status) for r in report.results}
    assert (5, "ok") in statuses
    assert (100, "skipped_max_n") in statuses
    # n=5: one timed repeat + one count_run; n=100 must not invoke spy.
    assert calls == 2


def test_timeout_status(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(a: MutableSequence[Any]) -> None:
        time.sleep(1.0)

    spec = AlgorithmSpec(
        name="slow",
        func=slow,
        complexity="O(1)",
        expected_exponent=1.0,
        stable=True,
        in_place=True,
        comparison_based=True,
        max_n=100,
    )
    with pytest.raises(BenchmarkTimeoutError):
        time_run(spec, [1, 2, 3], repeats=1, warmup=0, timeout_s=0.05)


def test_fresh_copy_each_repeat() -> None:
    seen: list[list[int]] = []

    def recorder(a: MutableSequence[Any]) -> None:
        seen.append(list(a))
        # Sort in place so a missing fresh copy would feed sorted data next time.
        for i in range(len(a)):
            for j in range(len(a) - 1 - i):
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]

    spec = AlgorithmSpec(
        name="recorder",
        func=recorder,
        complexity="O(n^2)",
        expected_exponent=2.0,
        stable=True,
        in_place=True,
        comparison_based=True,
        max_n=100,
    )
    data = [3, 1, 2]
    time_run(spec, data, repeats=3, warmup=0, timeout_s=5.0)
    assert len(seen) == 3
    assert all(sample == [3, 1, 2] for sample in seen)
