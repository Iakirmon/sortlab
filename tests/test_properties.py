"""Property-based tests shared by every registered algorithm."""

from __future__ import annotations

from collections import Counter

from hypothesis import given, settings
from hypothesis import strategies as st

from sortlab.registry import all_algorithms, discover

discover()


@settings(max_examples=50, deadline=None)
@given(data=st.lists(st.integers(min_value=-1000, max_value=1000), max_size=80))
def test_result_is_sorted_permutation(data: list[int]) -> None:
    for spec in all_algorithms():
        working = list(data)
        before = Counter(working)
        assert spec.func(working) is None
        assert Counter(working) == before
        assert working == sorted(data)
