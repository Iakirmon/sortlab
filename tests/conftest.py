"""Shared fixtures for sortlab tests."""

from __future__ import annotations

import pytest

from sortlab.registry import discover


@pytest.fixture(scope="session", autouse=True)
def _discover_algorithms() -> None:
    discover()
