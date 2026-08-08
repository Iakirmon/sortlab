"""Bubble sort — the baseline for how slow a correct sort can be."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


@register(
    name="bubble_sort",
    complexity="O(n^2)",
    expected_exponent=2.0,
    stable=True,
    in_place=True,
    comparison_based=True,
    max_n=20_000,
    notes="Naive variant without early exit.",
)
def bubble_sort(a: MutableSequence[Any]) -> None:
    """Sort `a` in place by repeatedly swapping adjacent out-of-order pairs."""
    n = len(a)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]


@register(
    name="bubble_sort_early_exit",
    complexity="O(n^2)",
    expected_exponent=2.0,
    stable=True,
    in_place=True,
    comparison_based=True,
    max_n=20_000,
    notes="Stops early when a pass makes no swaps.",
)
def bubble_sort_early_exit(a: MutableSequence[Any]) -> None:
    """Bubble sort that stops when a full pass performs no swaps."""
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            return
