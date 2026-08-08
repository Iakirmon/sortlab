"""Merge sort — stable divide-and-conquer with linear extra memory."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


def _merge(
    a: MutableSequence[Any],
    lo: int,
    mid: int,
    hi: int,
    temp: list[Any],
) -> None:
    i = lo
    j = mid
    k = lo
    while i < mid and j < hi:
        if a[i] <= a[j]:
            temp[k] = a[i]
            i += 1
        else:
            temp[k] = a[j]
            j += 1
        k += 1
    while i < mid:
        temp[k] = a[i]
        i += 1
        k += 1
    while j < hi:
        temp[k] = a[j]
        j += 1
        k += 1
    for idx in range(lo, hi):
        a[idx] = temp[idx]


def _mergesort(a: MutableSequence[Any], lo: int, hi: int, temp: list[Any]) -> None:
    if hi - lo <= 1:
        return
    mid = (lo + hi) // 2
    _mergesort(a, lo, mid, temp)
    _mergesort(a, mid, hi, temp)
    _merge(a, lo, mid, hi, temp)


@register(
    name="merge_sort",
    complexity="O(n log n)",
    expected_exponent=1.15,
    stable=True,
    in_place=False,
    comparison_based=True,
    max_n=1_000_000,
    notes="Top-down merge sort with an auxiliary buffer.",
)
def merge_sort(a: MutableSequence[Any]) -> None:
    """Sort `a` in place (via buffer copy-back) using merge sort."""
    n = len(a)
    if n <= 1:
        return
    temp: list[Any] = [None] * n
    _mergesort(a, 0, n, temp)
