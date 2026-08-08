"""Log-log power-law fit for empirical complexity classification."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from sortlab.types import SortlabError


class ComplexityFitError(SortlabError):
    """Raised when a power-law fit cannot be computed."""


@dataclass(frozen=True, slots=True)
class FitResult:
    exponent: float
    intercept: float
    r_squared: float
    points: int


def fit_power_law(ns: Sequence[int], times: Sequence[float]) -> FitResult:
    """Least squares fit of ``log(t) = a*log(n) + b``; ``a`` is the exponent."""
    if len(ns) != len(times):
        raise ComplexityFitError("ns and times must have the same length")
    if len(ns) < 2:
        raise ComplexityFitError("need at least 2 points to fit")
    if any(n <= 0 for n in ns) or any(t <= 0 for t in times):
        raise ComplexityFitError("ns and times must be positive")

    log_n = np.log(np.asarray(ns, dtype=float))
    log_t = np.log(np.asarray(times, dtype=float))
    a, b = np.polyfit(log_n, log_t, 1)
    predicted = a * log_n + b
    ss_res = float(np.sum((log_t - predicted) ** 2))
    ss_tot = float(np.sum((log_t - np.mean(log_t)) ** 2))
    r_squared = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return FitResult(
        exponent=float(a),
        intercept=float(b),
        r_squared=float(r_squared),
        points=len(ns),
    )


def classify(fit: FitResult) -> str:
    """Classify a fit, or return ``nierozstrzygnięte`` when evidence is weak."""
    if fit.points < 4 or fit.r_squared < 0.95:
        return "nierozstrzygnięte"
    exp = fit.exponent
    if exp < 1.12:
        return "≈O(n)"
    if exp < 1.6:
        return "≈O(n log n)"
    return "≈O(n²)"


def relative_error(measured: float, expected: float) -> float:
    return abs(measured - expected) / max(abs(expected), 1e-9)


def is_close_exponent(measured: float, expected: float, *, tol: float | None = None) -> bool:
    """Tolerance around expected_exponent from algorithm metadata."""
    if tol is None:
        if expected >= 1.8:
            tol = 0.25
        elif expected <= 1.05:
            tol = 0.25
        else:
            tol = 0.35
    return math.fabs(measured - expected) <= tol
