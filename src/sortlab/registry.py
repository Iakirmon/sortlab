"""Algorithm registry with decorator-based registration and autodiscovery."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

from sortlab.types import (
    AlgorithmSpec,
    DuplicateAlgorithmError,
    SortFn,
    UnknownAlgorithmError,
)

_REGISTRY: dict[str, AlgorithmSpec] = {}
_DISCOVERED = False


def register(
    *,
    name: str,
    complexity: str,
    expected_exponent: float,
    stable: bool,
    in_place: bool,
    comparison_based: bool,
    max_n: int,
    notes: str = "",
) -> Callable[[SortFn], SortFn]:
    """Register a sorting function under ``name`` when the module is imported."""

    def decorator(func: SortFn) -> SortFn:
        if name in _REGISTRY:
            raise DuplicateAlgorithmError(f"algorithm already registered: {name}")
        _REGISTRY[name] = AlgorithmSpec(
            name=name,
            func=func,
            complexity=complexity,
            expected_exponent=expected_exponent,
            stable=stable,
            in_place=in_place,
            comparison_based=comparison_based,
            max_n=max_n,
            notes=notes,
        )
        return func

    return decorator


def discover() -> None:
    """Import every ``sortlab.algorithms`` subpackage to trigger ``@register``."""
    global _DISCOVERED
    if _DISCOVERED:
        return
    import sortlab.algorithms as algorithms_pkg

    prefix = algorithms_pkg.__name__ + "."
    for module_info in pkgutil.iter_modules(algorithms_pkg.__path__, prefix):
        importlib.import_module(module_info.name)
    _DISCOVERED = True


def all_algorithms() -> tuple[AlgorithmSpec, ...]:
    """Return all registered algorithms sorted by name."""
    discover()
    return tuple(sorted(_REGISTRY.values(), key=lambda spec: spec.name))


def get(name: str) -> AlgorithmSpec:
    """Look up a registered algorithm by name."""
    discover()
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise UnknownAlgorithmError(f"unknown algorithm: {name}") from exc
