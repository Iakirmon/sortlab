"""Shared types and exception hierarchy for sortlab."""

from __future__ import annotations

from collections.abc import Callable, MutableSequence
from dataclasses import dataclass
from typing import Any, Literal

SortFn = Callable[[MutableSequence[Any]], None]

Distribution = Literal[
    "random",
    "sorted",
    "reversed",
    "nearly_sorted",
    "few_unique",
    "sawtooth",
    "zipf",
]


@dataclass(frozen=True, slots=True)
class AlgorithmSpec:
    """Metadata and entry point for a registered sorting algorithm."""

    name: str
    func: SortFn
    complexity: str
    expected_exponent: float
    stable: bool
    in_place: bool
    comparison_based: bool
    max_n: int
    notes: str = ""


class SortlabError(Exception):
    """Base error for the sortlab package."""


class DuplicateAlgorithmError(SortlabError):
    """Raised when registering an algorithm name that already exists."""


class UnknownAlgorithmError(SortlabError):
    """Raised when looking up an algorithm that is not registered."""
