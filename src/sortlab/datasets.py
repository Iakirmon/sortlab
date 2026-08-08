"""Deterministic input generators for sorting benchmarks."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from sortlab.types import Distribution, SortlabError


class UnknownDistributionError(SortlabError, ValueError):
    """Raised when an unsupported distribution name is requested."""


def generate(distribution: Distribution, n: int, *, seed: int = 42) -> list[int]:
    """Return ``n`` integers drawn from ``distribution`` (deterministic for ``seed``)."""
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    rng = random.Random(seed)
    if distribution == "random":
        data = list(range(n))
        rng.shuffle(data)
        return data
    if distribution == "sorted":
        return list(range(n))
    if distribution == "reversed":
        return list(range(n - 1, -1, -1))
    if distribution == "nearly_sorted":
        data = list(range(n))
        if n >= 2:
            swaps = max(1, n // 100)
            for _ in range(swaps):
                i = rng.randrange(n - 1)
                data[i], data[i + 1] = data[i + 1], data[i]
        return data
    if distribution == "few_unique":
        if n == 0:
            return []
        values = list(range(10))
        if n < 10:
            return [rng.choice(values) for _ in range(n)]
        data = [i % 10 for i in range(n)]
        rng.shuffle(data)
        return data
    if distribution == "sawtooth":
        period = 5
        return [i % period for i in range(n)]
    if distribution == "zipf":
        return _zipf(n, rng)
    raise UnknownDistributionError(f"unknown distribution: {distribution}")


def load_csv_keys(path: Path, column: str) -> list[str]:
    """Load values of ``column`` from a CSV file as strings."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise SortlabError(f"column {column!r} not found in {path}")
        return [row[column] for row in reader]


def write_records_csv(path: Path, *, rows: int = 200_000, seed: int = 42) -> None:
    """Write a deterministic synthetic records CSV (id, surname, city, ...)."""
    rng = random.Random(seed)
    surnames = [
        "Kowalski",
        "Nowak",
        "Wiśniewski",
        "Wójcik",
        "Kamiński",
        "Lewandowski",
        "Zielinski",
        "Szymański",
        "Woźniak",
        "Dąbrowski",
    ]
    cities = ["Warszawa", "Kraków", "Gdańsk", "Wrocław", "Poznań", "Łódź"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["id", "surname", "city", "registered_at", "amount"],
        )
        writer.writeheader()
        for i in range(rows):
            writer.writerow(
                {
                    "id": str(i),
                    "surname": rng.choice(surnames),
                    "city": rng.choice(cities),
                    "registered_at": f"2020-01-01T00:00:{i % 60:02d}Z",
                    "amount": f"{rng.random() * 1000:.2f}",
                }
            )


def _zipf(n: int, rng: random.Random, *, alpha: float = 1.1, vocabulary: int = 100) -> list[int]:
    """Sample integers from a Zipf-like distribution over ``vocabulary`` ranks."""
    if n == 0:
        return []
    ranks = list(range(1, vocabulary + 1))
    weights = [1.0 / (rank**alpha) for rank in ranks]
    total = sum(weights)
    cumulative: list[float] = []
    running = 0.0
    for weight in weights:
        running += weight / total
        cumulative.append(running)

    out: list[int] = []
    for _ in range(n):
        u = rng.random()
        choice = vocabulary - 1
        for index, threshold in enumerate(cumulative):
            if u <= threshold:
                choice = index
                break
        out.append(choice)
    return out
