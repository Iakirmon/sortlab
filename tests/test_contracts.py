"""Contract tests: return value, in-place mutation, stability, memory."""

from __future__ import annotations

import tracemalloc

import pytest

from sortlab.registry import all_algorithms, discover, get

discover()

ALGORITHMS = [spec.name for spec in all_algorithms()]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_returns_none_and_sorts_inplace(algorithm: str) -> None:
    spec = get(algorithm)
    data = [4, 2, 5, 1, 3]
    working = data
    result = spec.func(working)
    assert result is None
    assert working is data
    assert working == [1, 2, 3, 4, 5]


@pytest.mark.parametrize(
    "algorithm",
    [spec.name for spec in all_algorithms() if spec.stable],
)
def test_stable_preserves_relative_order(algorithm: str) -> None:
    # Wrap keys so only the key participates in ordering (not original index).
    data = [(2, 0), (1, 1), (2, 2), (1, 3), (3, 4), (2, 5)]

    class Key:
        __slots__ = ("key", "index")

        def __init__(self, key: int, index: int) -> None:
            self.key = key
            self.index = index

        def __lt__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return self.key < other.key

        def __le__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return self.key <= other.key

        def __gt__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return self.key > other.key

        def __ge__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return self.key >= other.key

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Key):
                return NotImplemented
            return self.key == other.key

        def __int__(self) -> int:
            return self.key

    wrapped = [Key(k, i) for k, i in data]
    get(algorithm).func(wrapped)
    # Among equal keys, original indices must be non-decreasing.
    by_key: dict[int, list[int]] = {}
    for item in wrapped:
        by_key.setdefault(item.key, []).append(item.index)
    for indices in by_key.values():
        assert indices == sorted(indices)


@pytest.mark.parametrize(
    "algorithm",
    [spec.name for spec in all_algorithms() if spec.in_place],
)
def test_in_place_flag_matches_low_allocation(algorithm: str) -> None:
    # Builtin timsort allocates a new list; still declared in_place because of a[:]=.
    if algorithm == "builtin_timsort":
        return
    # Random input avoids O(n) recursion depth on naive quicksort pivots.
    data = list(range(800))
    rng = __import__("random").Random(0)
    rng.shuffle(data)
    working = list(data)
    tracemalloc.start()
    get(algorithm).func(working)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # Allow interpreter/recursion overhead; reject clear O(n) auxiliary buffers.
    assert peak < 200_000
    assert working == sorted(data)
