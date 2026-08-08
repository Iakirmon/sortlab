"""Counting sort — integer keys, zero element comparisons."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


@register(
    name="counting_sort",
    complexity="O(n + k)",
    expected_exponent=1.0,
    stable=True,
    in_place=False,
    comparison_based=False,
    max_n=1_000_000,
    notes="Stable counting sort over integer key range.",
)
def counting_sort(a: MutableSequence[Any]) -> None:
    """Sort integer sequence `a` in place via counting sort (copy-back)."""
    n = len(a)
    if n <= 1:
        return
    keys = [int(x) for x in a]
    lo = min(keys)
    hi = max(keys)
    size = hi - lo + 1
    counts = [0] * size
    for key in keys:
        counts[key - lo] += 1
    for i in range(1, size):
        counts[i] += counts[i - 1]
    out: list[Any] = [None] * n
    for i in range(n - 1, -1, -1):
        key = keys[i]
        counts[key - lo] -= 1
        out[counts[key - lo]] = a[i]
    for i in range(n):
        a[i] = out[i]
