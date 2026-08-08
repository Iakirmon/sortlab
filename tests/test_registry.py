"""Registry discovery, lookup, and metadata contracts."""

from __future__ import annotations

import importlib
from collections.abc import MutableSequence
from typing import Any

import pytest

from sortlab.registry import all_algorithms, get, register
from sortlab.types import AlgorithmSpec, DuplicateAlgorithmError, UnknownAlgorithmError


def test_discover_finds_insertion_sort() -> None:
    names = {spec.name for spec in all_algorithms()}
    assert "insertion_sort" in names


def test_all_algorithms_sorted_by_name() -> None:
    names = [spec.name for spec in all_algorithms()]
    assert names == sorted(names)


def test_get_returns_spec() -> None:
    spec = get("insertion_sort")
    assert isinstance(spec, AlgorithmSpec)
    assert spec.name == "insertion_sort"
    assert callable(spec.func)


def test_get_unknown_raises() -> None:
    with pytest.raises(UnknownAlgorithmError):
        get("no_such_algorithm")


def test_duplicate_name_raises() -> None:
    from sortlab import registry as registry_mod

    probe = "__duplicate_probe__"
    try:

        @register(
            name=probe,
            complexity="O(1)",
            expected_exponent=1.0,
            stable=True,
            in_place=True,
            comparison_based=True,
            max_n=10,
        )
        def _first(a: MutableSequence[Any]) -> None:
            return None

        with pytest.raises(DuplicateAlgorithmError):

            @register(
                name=probe,
                complexity="O(1)",
                expected_exponent=1.0,
                stable=True,
                in_place=True,
                comparison_based=True,
                max_n=10,
            )
            def _second(a: MutableSequence[Any]) -> None:
                return None
    finally:
        registry_mod._REGISTRY.pop(probe, None)


def test_metadata_complete_for_every_algorithm() -> None:
    for spec in all_algorithms():
        assert spec.name
        assert callable(spec.func)
        assert spec.complexity
        assert isinstance(spec.expected_exponent, float)
        assert isinstance(spec.stable, bool)
        assert isinstance(spec.in_place, bool)
        assert isinstance(spec.comparison_based, bool)
        assert spec.max_n > 0


def test_discover_is_idempotent() -> None:
    from sortlab import registry

    before = all_algorithms()
    registry.discover()
    after = all_algorithms()
    assert before == after


def test_algorithms_package_import_triggers_registration() -> None:
    # Re-import path used by discover; insertion_sort must stay registered.
    importlib.import_module("sortlab.algorithms.insertion_sort")
    get("insertion_sort")
