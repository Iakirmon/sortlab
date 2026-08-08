"""Selection sort — minimizes writes at the cost of comparisons."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


@register(
    name="selection_sort",
    complexity="O(n^2)",
    expected_exponent=2.0,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=20_000,
    notes="Exactly n-1 writes of selected minima into place.",
)
def selection_sort(a: MutableSequence[Any]) -> None:
    """Sort `a` in place by selecting the minimum of each unsorted suffix."""
    n = len(a)
    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
