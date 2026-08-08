"""Hand-checked counter tests — the measurement tool must not lie."""

from __future__ import annotations

from sortlab.algorithms.counting_sort.algorithm import counting_sort
from sortlab.algorithms.insertion_sort.algorithm import insertion_sort
from sortlab.algorithms.radix_sort.algorithm import radix_sort
from sortlab.algorithms.selection_sort.algorithm import selection_sort
from sortlab.instrument import Counters, TrackedList, count_run


def test_insertion_sort_comparisons_on_3_1_2() -> None:
    # Manual trace of insertion_sort on [3, 1, 2]:
    # i=1,key=1: 3>1 → shift; i=2,key=2: 3>2 → shift; 1>2 → stop. 3 comparisons.
    counters = count_run(insertion_sort, [3, 1, 2])
    assert counters.comparisons == 3


def test_selection_sort_comparisons_on_3_1_2() -> None:
    # Manual trace of selection_sort on [3, 1, 2]:
    # i=0: 1<3, 2<1; i=1: 2<3. 3 comparisons.
    counters = count_run(selection_sort, [3, 1, 2])
    assert counters.comparisons == 3


def test_comparisons_are_machine_independent() -> None:
    first = count_run(insertion_sort, [3, 1, 2])
    second = count_run(insertion_sort, [3, 1, 2])
    assert first.comparisons == second.comparisons == 3


def test_count_run_does_not_mutate_caller_list() -> None:
    original = [3, 1, 2]
    snapshot = list(original)
    count_run(insertion_sort, original)
    assert original == snapshot


def test_on_write_called_once_per_write() -> None:
    frames: list[list[int]] = []
    counters = Counters()
    tracked = TrackedList([3, 1, 2], counters, on_write=lambda snap: frames.append(snap))
    insertion_sort(tracked)
    assert len(frames) == counters.writes
    assert counters.writes > 0


def test_counting_sort_has_zero_comparisons() -> None:
    counters = count_run(counting_sort, [3, 1, 2, 1, 0])
    assert counters.comparisons == 0
    assert counters.writes > 0


def test_radix_sort_has_zero_comparisons() -> None:
    counters = count_run(radix_sort, [30, 1, 22, 15, 0])
    assert counters.comparisons == 0
    assert counters.writes > 0
