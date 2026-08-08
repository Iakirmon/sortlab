"""LSD radix sort, base 10 — breaks the comparison-sort lower bound."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


def _counting_by_digit(
    values: list[int],
    originals: list[Any],
    exp: int,
) -> tuple[list[int], list[Any]]:
    n = len(values)
    counts = [0] * 10
    for value in values:
        digit = (value // exp) % 10
        counts[digit] += 1
    for i in range(1, 10):
        counts[i] += counts[i - 1]
    out_values = [0] * n
    out_items: list[Any] = [None] * n
    for i in range(n - 1, -1, -1):
        digit = (values[i] // exp) % 10
        counts[digit] -= 1
        idx = counts[digit]
        out_values[idx] = values[i]
        out_items[idx] = originals[i]
    return out_values, out_items


def _radix_nonnegative(values: list[int], originals: list[Any]) -> list[Any]:
    if not values:
        return []
    max_value = max(values)
    exp = 1
    items = originals
    while max_value // exp > 0:
        values, items = _counting_by_digit(values, items, exp)
        exp *= 10
    return items


@register(
    name="radix_sort",
    complexity="O(n · k)",
    expected_exponent=1.0,
    stable=True,
    in_place=False,
    comparison_based=False,
    max_n=1_000_000,
    notes="LSD radix sort, base 10; supports negatives via sign split.",
)
def radix_sort(a: MutableSequence[Any]) -> None:
    """Sort integer sequence `a` in place using LSD radix sort (base 10)."""
    n = len(a)
    if n <= 1:
        return
    keys = [int(x) for x in a]
    items = [a[i] for i in range(n)]
    negatives = [(-k, item) for k, item in zip(keys, items, strict=True) if k < 0]
    nonneg = [(k, item) for k, item in zip(keys, items, strict=True) if k >= 0]

    neg_values = [v for v, _ in negatives]
    neg_items = [item for _, item in negatives]
    pos_values = [v for v, _ in nonneg]
    pos_items = [item for _, item in nonneg]

    # Ascending negatives: radix on absolute values, then reverse.
    sorted_neg_items = _radix_nonnegative(neg_values, neg_items)
    sorted_neg_items.reverse()
    sorted_pos_items = _radix_nonnegative(pos_values, pos_items)

    result = sorted_neg_items + sorted_pos_items
    for i in range(n):
        a[i] = result[i]
