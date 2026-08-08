"""Shell sort — insertion sort with shrinking gaps."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


def _shell_sort(a: MutableSequence[Any], gaps: list[int]) -> None:
    n = len(a)
    for gap in gaps:
        for i in range(gap, n):
            temp = a[i]
            j = i
            while j >= gap and a[j - gap] > temp:
                a[j] = a[j - gap]
                j -= gap
            a[j] = temp


def _shell_gaps(n: int) -> list[int]:
    gaps: list[int] = []
    gap = n // 2
    while gap > 0:
        gaps.append(gap)
        gap //= 2
    return gaps


# Ciura's sequence, descending, filtered to < n at runtime.
_CIURA = [701, 301, 132, 57, 23, 10, 4, 1]


@register(
    name="shell_sort_shell",
    complexity="O(n^1.5)",
    expected_exponent=1.5,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=1_000_000,
    notes="Original Shell gap sequence n/2, n/4, ..., 1.",
)
def shell_sort_shell(a: MutableSequence[Any]) -> None:
    """Shell sort using Shell's original gap sequence."""
    _shell_sort(a, _shell_gaps(len(a)))


@register(
    name="shell_sort_ciura",
    complexity="O(n^1.25)",
    expected_exponent=1.25,
    stable=False,
    in_place=True,
    comparison_based=True,
    max_n=1_000_000,
    notes="Ciura gap sequence.",
)
def shell_sort_ciura(a: MutableSequence[Any]) -> None:
    """Shell sort using Ciura's gap sequence."""
    n = len(a)
    gaps = [gap for gap in _CIURA if gap < n]
    if not gaps or gaps[-1] != 1:
        gaps.append(1)
    _shell_sort(a, gaps)
