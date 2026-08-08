"""Correctness tests parameterized over the algorithm registry."""

from __future__ import annotations

import pytest

from sortlab.datasets import generate
from sortlab.registry import all_algorithms, discover, get
from sortlab.types import Distribution

discover()

ALGORITHMS = [spec.name for spec in all_algorithms()]
DISTRIBUTIONS: tuple[Distribution, ...] = (
    "random",
    "sorted",
    "reversed",
    "nearly_sorted",
    "few_unique",
    "sawtooth",
    "zipf",
)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_sorts_all_distributions(algorithm: str, distribution: Distribution) -> None:
    data = generate(distribution, 50, seed=42)
    working = list(data)
    assert get(algorithm).func(working) is None
    assert working == sorted(data)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize(
    "data",
    [
        [],
        [1],
        [2, 1],
        [1, 1, 1, 1],
        [-3, 0, -1, 5, 2],
        [0, -1, -1, 0, 2],
    ],
    ids=["empty", "one", "two", "all_equal", "negatives", "mixed_signs"],
)
def test_edge_cases(algorithm: str, data: list[int]) -> None:
    working = list(data)
    assert get(algorithm).func(working) is None
    assert working == sorted(data)


def test_registry_has_all_spec_algorithms() -> None:
    # Table in spec §6 lists 14 named registrations across 10 catalogs.
    assert len(ALGORITHMS) == 14
    expected = {
        "bubble_sort",
        "bubble_sort_early_exit",
        "insertion_sort",
        "selection_sort",
        "shell_sort_shell",
        "shell_sort_ciura",
        "merge_sort",
        "quick_sort_last",
        "quick_sort_random",
        "quick_sort_median3",
        "heap_sort",
        "counting_sort",
        "radix_sort",
        "builtin_timsort",
    }
    assert set(ALGORITHMS) == expected
