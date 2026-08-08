"""Insertion sort — efficient on nearly sorted input."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


@register(
    name="insertion_sort",
    complexity="O(n^2)",
    expected_exponent=2.0,
    stable=True,
    in_place=True,
    comparison_based=True,
    max_n=20_000,
    notes="Baseline adaptive quadratic sort.",
)
def insertion_sort(a: MutableSequence[Any]) -> None:
    """Sort `a` in place by inserting each element into the sorted prefix."""
    n = len(a)
    for i in range(1, n):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
