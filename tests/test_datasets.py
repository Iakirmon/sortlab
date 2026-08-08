"""Tests for deterministic dataset generators."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from sortlab.datasets import generate, load_csv_keys
from sortlab.types import Distribution

DISTRIBUTIONS: tuple[Distribution, ...] = (
    "random",
    "sorted",
    "reversed",
    "nearly_sorted",
    "few_unique",
    "sawtooth",
    "zipf",
)


def _count_inversions(data: list[int]) -> int:
    count = 0
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] > data[j]:
                count += 1
    return count


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_length_equals_n(distribution: Distribution) -> None:
    n = 200
    assert len(generate(distribution, n, seed=42)) == n


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_deterministic_same_seed(distribution: Distribution) -> None:
    a = generate(distribution, 100, seed=7)
    b = generate(distribution, 100, seed=7)
    assert a == b


@pytest.mark.parametrize("distribution", ["random", "nearly_sorted", "few_unique", "zipf"])
def test_different_seed_different_result(distribution: Distribution) -> None:
    a = generate(distribution, 100, seed=1)
    b = generate(distribution, 100, seed=2)
    assert a != b


def test_sorted_is_identity_range() -> None:
    assert generate("sorted", 10, seed=42) == list(range(10))


def test_reversed_is_descending() -> None:
    assert generate("reversed", 10, seed=42) == list(range(9, -1, -1))


def test_nearly_sorted_has_about_one_percent_inversions() -> None:
    n = 1000
    data = generate("nearly_sorted", n, seed=42)
    inversions = _count_inversions(data)
    # 1% random swaps → roughly O(n) inversions; allow a wide but meaningful band.
    assert 1 <= inversions <= n * 0.05


def test_few_unique_has_exactly_ten_distinct_values() -> None:
    data = generate("few_unique", 500, seed=42)
    assert len(set(data)) == 10


def test_sawtooth_repeats_rising_segments() -> None:
    n = 25
    data = generate("sawtooth", n, seed=42)
    # Documented shape: repeating ascending runs of length 5: 0,1,2,3,4,0,1,...
    assert data == [i % 5 for i in range(n)]


def test_zipf_is_skewed_toward_small_ranks() -> None:
    data = generate("zipf", 5000, seed=42)
    # Most frequent value should appear much more often than the median unique value.
    counts: dict[int, int] = {}
    for value in data:
        counts[value] = counts.get(value, 0) + 1
    frequencies = sorted(counts.values(), reverse=True)
    assert frequencies[0] > 3 * frequencies[len(frequencies) // 2]


def test_load_csv_keys(tmp_path: Path) -> None:
    path = tmp_path / "rows.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "surname"])
        writer.writeheader()
        writer.writerow({"id": "1", "surname": "Kowalski"})
        writer.writerow({"id": "2", "surname": "Nowak"})
    assert load_csv_keys(path, "surname") == ["Kowalski", "Nowak"]


def test_generate_rejects_unknown_distribution() -> None:
    with pytest.raises(ValueError):
        generate("nope", 10, seed=1)  # type: ignore[arg-type]
