"""Power-law complexity fit tests."""

from __future__ import annotations

import pytest

from sortlab.complexity import classify, fit_power_law, is_close_exponent


def test_fit_quadratic() -> None:
    ns = [100, 200, 400, 800, 1600]
    times = [float(n**2) for n in ns]
    fit = fit_power_law(ns, times)
    assert fit.exponent == pytest.approx(2.0, abs=0.05)
    assert fit.r_squared > 0.999


def test_fit_n_log_like_and_linear() -> None:
    ns = [100, 200, 400, 800, 1600]
    t_n15 = [float(n**1.5) for n in ns]
    t_n = [float(n) for n in ns]
    assert fit_power_law(ns, t_n15).exponent == pytest.approx(1.5, abs=0.05)
    assert fit_power_law(ns, t_n).exponent == pytest.approx(1.0, abs=0.05)


def test_classify_undetermined_on_few_points_or_low_r2() -> None:
    fit_few = fit_power_law([10, 20, 40], [100.0, 400.0, 1600.0])
    assert classify(fit_few) == "nierozstrzygnięte"
    # Construct a poor fit by mixing unrelated times.
    fit_bad = fit_power_law(
        [10, 20, 40, 80],
        [5.0, 500.0, 6.0, 400.0],
    )
    assert fit_bad.r_squared < 0.95
    assert classify(fit_bad) == "nierozstrzygnięte"


def test_classify_labels() -> None:
    from sortlab.complexity import FitResult

    assert classify(FitResult(2.0, 0.0, 0.99, 5)) == "≈O(n²)"
    assert classify(FitResult(1.2, 0.0, 0.99, 5)) == "≈O(n log n)"
    assert classify(FitResult(1.0, 0.0, 0.99, 5)) == "≈O(n)"
    assert classify(FitResult(1.08, 0.0, 0.99, 5)) == "≈O(n)"
    assert classify(FitResult(1.14, 0.0, 0.99, 5)) == "≈O(n log n)"


def test_is_close_exponent_helper() -> None:
    assert is_close_exponent(1.98, 2.0)
    assert not is_close_exponent(1.0, 2.0)


def test_measured_exponents_on_small_bench() -> None:
    """Integration: measured exponents stay near metadata expectations."""
    from sortlab.bench import run_matrix
    from sortlab.complexity import fit_power_law, is_close_exponent
    from sortlab.registry import get

    report = run_matrix(
        algorithms=[
            "bubble_sort",
            "merge_sort",
            "radix_sort",
            "insertion_sort",
            "heap_sort",
        ],
        distributions=["random"],
        sizes=[80, 160, 320, 640],
        repeats=1,
        warmup=0,
        timeout_s=60.0,
    )
    for name in [
        "bubble_sort",
        "merge_sort",
        "radix_sort",
        "insertion_sort",
        "heap_sort",
    ]:
        rows = [
            r
            for r in report.results
            if r.algorithm == name and r.status == "ok" and r.timing is not None
        ]
        rows = sorted(rows, key=lambda r: r.n)
        assert len(rows) >= 4
        fit = fit_power_law(
            [r.n for r in rows],
            [r.timing.median_s for r in rows if r.timing is not None],
        )
        expected = get(name).expected_exponent
        assert is_close_exponent(fit.exponent, expected), (
            f"{name}: measured {fit.exponent:.3f} vs expected {expected}"
        )
