"""Built-in Timsort baseline exposed through the common in-place contract."""

from collections.abc import MutableSequence
from typing import Any

from sortlab.registry import register


@register(
    name="builtin_timsort",
    complexity="O(n log n)",
    expected_exponent=1.15,
    stable=True,
    in_place=True,
    comparison_based=True,
    max_n=5_000_000,
    notes="Reference line: a[:] = sorted(a). Comparisons are not countable in Python.",
)
def builtin_timsort(a: MutableSequence[Any]) -> None:
    """Sort `a` in place by assigning ``sorted(a)`` back into ``a``."""
    a[:] = sorted(a)
