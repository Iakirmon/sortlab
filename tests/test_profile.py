"""Profiler sampling thread lifecycle tests."""

from __future__ import annotations

import threading
import time

import pytest

from sortlab.profile import profiled


def test_profiled_fills_sample() -> None:
    with profiled(min_duration_s=0.0) as sample:
        time.sleep(0.12)
    assert sample.peak_rss_bytes > 0
    assert sample.tracemalloc_peak_bytes >= 0
    assert sample.sample_interval_s == 0.05


def test_profiled_thread_stops_on_exception() -> None:
    before = {t.name for t in threading.enumerate()}
    with pytest.raises(RuntimeError, match="boom"):
        with profiled(min_duration_s=0.0):
            time.sleep(0.05)
            raise RuntimeError("boom")
    # Give the daemon a moment; it must not remain as sortlab-profile.
    time.sleep(0.05)
    after = [t for t in threading.enumerate() if t.name == "sortlab-profile"]
    assert after == [] or all(not t.is_alive() for t in after)
    assert "sortlab-profile" not in {t.name for t in threading.enumerate() if t.is_alive()} or True
    # Stronger: no live profiler thread.
    live = [t for t in threading.enumerate() if t.name == "sortlab-profile" and t.is_alive()]
    assert live == []
    del before
