"""Heap sort — in-place, predictable n log n."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


def _sift_down(a: MutableSequence[Any], start: int, end: int) -> None:
    root = start
    while True:
        child = 2 * root + 1
        if child > end:
            return
        if child + 1 <= end and a[child] < a[child + 1]:
            child += 1
        if a[root] < a[child]:
            a[root], a[child] = a[child], a[root]
            root = child
        else:
            return


@register(
    name="heap_sort",
    complexity="O(n log n)",
    expected_exponent=1.15,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=1_000_000,
    notes="Binary heap sort; predictable but rarely the fastest.",
)
def heap_sort(a: MutableSequence[Any]) -> None:
    """Sort `a` in place using a binary max-heap."""
    n = len(a)
    if n <= 1:
        return
    for start in range(n // 2 - 1, -1, -1):
        _sift_down(a, start, n - 1)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        _sift_down(a, 0, end - 1)
