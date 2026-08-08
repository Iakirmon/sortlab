"""Quick sort — three pivot strategies sharing one partition routine."""

from __future__ import annotations

import random
from collections.abc import Callable, MutableSequence
from typing import Any

from sortlab.registry import register

PivotChooser = Callable[[MutableSequence[Any], int, int], int]


def _partition(a: MutableSequence[Any], lo: int, hi: int, pivot_index: int) -> int:
    pivot = a[pivot_index]
    a[pivot_index], a[hi] = a[hi], a[pivot_index]
    store = lo
    for i in range(lo, hi):
        if a[i] < pivot:
            a[store], a[i] = a[i], a[store]
            store += 1
    a[store], a[hi] = a[hi], a[store]
    return store


def _quicksort(
    a: MutableSequence[Any],
    lo: int,
    hi: int,
    choose_pivot: PivotChooser,
) -> None:
    # Iterative stack avoids RecursionError on degenerate pivot choices.
    stack: list[tuple[int, int]] = [(lo, hi)]
    while stack:
        lo_i, hi_i = stack.pop()
        if lo_i >= hi_i:
            continue
        pivot_index = choose_pivot(a, lo_i, hi_i)
        p = _partition(a, lo_i, hi_i, pivot_index)
        stack.append((lo_i, p - 1))
        stack.append((p + 1, hi_i))


def _pivot_last(_a: MutableSequence[Any], _lo: int, hi: int) -> int:
    return hi


def _pivot_random(_a: MutableSequence[Any], lo: int, hi: int) -> int:
    return random.randint(lo, hi)


def _pivot_median3(a: MutableSequence[Any], lo: int, hi: int) -> int:
    mid = (lo + hi) // 2
    x, y, z = a[lo], a[mid], a[hi]
    if y <= x <= z or z <= x <= y:
        return lo
    if x <= y <= z or z <= y <= x:
        return mid
    return hi


@register(
    name="quick_sort_last",
    complexity="O(n log n)",
    expected_exponent=1.15,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=1_000_000,
    notes="Pivot = last element; degenerates on sorted input.",
)
def quick_sort_last(a: MutableSequence[Any]) -> None:
    """Quicksort with last-element pivot."""
    if len(a) > 1:
        _quicksort(a, 0, len(a) - 1, _pivot_last)


@register(
    name="quick_sort_random",
    complexity="O(n log n)",
    expected_exponent=1.15,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=1_000_000,
    notes="Random pivot.",
)
def quick_sort_random(a: MutableSequence[Any]) -> None:
    """Quicksort with a uniformly random pivot."""
    if len(a) > 1:
        _quicksort(a, 0, len(a) - 1, _pivot_random)


@register(
    name="quick_sort_median3",
    complexity="O(n log n)",
    expected_exponent=1.15,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=1_000_000,
    notes="Median-of-three pivot.",
)
def quick_sort_median3(a: MutableSequence[Any]) -> None:
    """Quicksort with median-of-three pivot selection."""
    if len(a) > 1:
        _quicksort(a, 0, len(a) - 1, _pivot_median3)
