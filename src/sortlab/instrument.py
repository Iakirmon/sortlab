"""Transparent operation counting for sorting algorithms."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, MutableSequence, Sequence
from dataclasses import dataclass
from typing import Any, overload

from sortlab.types import SortFn


@dataclass(slots=True)
class Counters:
    """Mutable tallies of comparisons, writes, and reads."""

    comparisons: int = 0
    writes: int = 0
    reads: int = 0


class Tracked:
    """Value wrapper that increments ``counters.comparisons`` on ordered compares."""

    __slots__ = ("value", "_c")

    def __init__(self, value: Any, counters: Counters) -> None:
        self.value = value
        self._c = counters

    def __lt__(self, other: object) -> bool:
        self._c.comparisons += 1
        if isinstance(other, Tracked):
            return bool(self.value < other.value)
        return bool(self.value < other)

    def __le__(self, other: object) -> bool:
        self._c.comparisons += 1
        if isinstance(other, Tracked):
            return bool(self.value <= other.value)
        return bool(self.value <= other)

    def __gt__(self, other: object) -> bool:
        self._c.comparisons += 1
        if isinstance(other, Tracked):
            return bool(self.value > other.value)
        return bool(self.value > other)

    def __ge__(self, other: object) -> bool:
        self._c.comparisons += 1
        if isinstance(other, Tracked):
            return bool(self.value >= other.value)
        return bool(self.value >= other)

    def __eq__(self, other: object) -> bool:
        self._c.comparisons += 1
        if isinstance(other, Tracked):
            return bool(self.value == other.value)
        return bool(self.value == other)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __int__(self) -> int:
        return int(self.value)

    def __index__(self) -> int:
        return int(self.value)

    def __repr__(self) -> str:
        return f"Tracked({self.value!r})"


class TrackedList(MutableSequence[Any]):
    """List-like container that counts reads/writes and optionally snapshots writes."""

    def __init__(
        self,
        data: Iterable[Any],
        counters: Counters,
        *,
        on_write: Callable[[list[Any]], None] | None = None,
        wrap_values: bool = True,
    ) -> None:
        self._c = counters
        self._on_write = on_write
        if wrap_values:
            self._data: list[Any] = [
                x if isinstance(x, Tracked) else Tracked(x, counters) for x in data
            ]
        else:
            self._data = list(data)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[Any]:
        for i in range(len(self._data)):
            yield self[i]

    @overload
    def __getitem__(self, index: int) -> Any: ...

    @overload
    def __getitem__(self, index: slice) -> list[Any]: ...

    def __getitem__(self, index: int | slice) -> Any:
        if isinstance(index, slice):
            indices = range(*index.indices(len(self._data)))
            self._c.reads += len(indices)
            return [self._data[i] for i in indices]
        self._c.reads += 1
        return self._data[index]

    @overload
    def __setitem__(self, index: int, value: Any) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Any]) -> None: ...

    def __setitem__(self, index: int | slice, value: Any) -> None:
        if isinstance(index, slice):
            values = [self._ensure_tracked(v) for v in value]
            self._c.writes += len(values)
            self._data[index] = values
        else:
            self._c.writes += 1
            self._data[index] = self._ensure_tracked(value)
        if self._on_write is not None:
            self._on_write(self.snapshot())

    def __delitem__(self, index: int | slice) -> None:
        del self._data[index]

    def insert(self, index: int, value: Any) -> None:
        self._c.writes += 1
        self._data.insert(index, self._ensure_tracked(value))
        if self._on_write is not None:
            self._on_write(self.snapshot())

    def snapshot(self) -> list[Any]:
        """Return plain values currently stored in the list."""
        out: list[Any] = []
        for item in self._data:
            out.append(item.value if isinstance(item, Tracked) else item)
        return out

    def _ensure_tracked(self, value: Any) -> Any:
        if isinstance(value, Tracked):
            return value
        return Tracked(value, self._c)


def count_run(func: SortFn, data: Sequence[Any]) -> Counters:
    """Run ``func`` on a tracked copy of ``data`` and return operation counters."""
    counters = Counters()
    tracked = TrackedList(data, counters, wrap_values=True)
    func(tracked)
    return counters
