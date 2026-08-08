"""CPU / RSS sampling around a timed region."""

from __future__ import annotations

import threading
import time
import tracemalloc
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psutil


@dataclass(frozen=True, slots=True)
class ResourceSample:
    peak_rss_bytes: int
    tracemalloc_peak_bytes: int
    cpu_percent_samples: list[float]
    sample_interval_s: float


@dataclass(slots=True)
class _SampleDraft:
    peak_rss_bytes: int = 0
    tracemalloc_peak_bytes: int = 0
    cpu_percent_samples: list[float] | None = None
    sample_interval_s: float = 0.05

    def freeze(self) -> ResourceSample:
        return ResourceSample(
            peak_rss_bytes=self.peak_rss_bytes,
            tracemalloc_peak_bytes=self.tracemalloc_peak_bytes,
            cpu_percent_samples=list(self.cpu_percent_samples or []),
            sample_interval_s=self.sample_interval_s,
        )


@contextmanager
def profiled(min_duration_s: float = 0.5) -> Iterator[ResourceSample]:
    """Sample process CPU/RSS while the context body runs.

    Yields a ``ResourceSample`` that is filled when the context exits. The worker
    thread is a daemon and is always joined, even if the body raises.
    """
    process = psutil.Process()
    samples: list[float] = []
    rss_peak = process.memory_info().rss
    stop = threading.Event()
    interval = 0.05
    draft = _SampleDraft(peak_rss_bytes=rss_peak, sample_interval_s=interval)

    def _worker() -> None:
        nonlocal rss_peak
        process.cpu_percent(interval=None)
        while not stop.wait(interval):
            samples.append(process.cpu_percent(interval=None))
            rss_peak = max(rss_peak, process.memory_info().rss)

    thread = threading.Thread(target=_worker, name="sortlab-profile", daemon=True)
    tracemalloc.start()
    thread.start()
    start = time.perf_counter()
    # Provisional frozen sample; fields overwritten via object.__setattr__ on exit.
    provisional = ResourceSample(0, 0, [], interval)
    try:
        yield provisional
    finally:
        elapsed = time.perf_counter() - start
        stop.set()
        thread.join(timeout=2.0)
        current, peak = tracemalloc.get_traced_memory()
        del current
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        draft.peak_rss_bytes = rss_peak
        draft.tracemalloc_peak_bytes = peak
        draft.cpu_percent_samples = list(samples) if elapsed >= min_duration_s else []
        final = draft.freeze()
        object.__setattr__(provisional, "peak_rss_bytes", final.peak_rss_bytes)
        object.__setattr__(provisional, "tracemalloc_peak_bytes", final.tracemalloc_peak_bytes)
        object.__setattr__(provisional, "cpu_percent_samples", final.cpu_percent_samples)
        object.__setattr__(provisional, "sample_interval_s", final.sample_interval_s)
