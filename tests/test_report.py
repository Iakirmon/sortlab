"""Smoke tests for report generation."""

from __future__ import annotations

from pathlib import Path

from sortlab.bench import run_matrix, save
from sortlab.report import inject_tables, markdown_tables, write_all


def test_write_all_creates_nonempty_pngs(tmp_path: Path) -> None:
    report = run_matrix(
        algorithms=["insertion_sort", "builtin_timsort", "merge_sort"],
        distributions=["random", "sorted"],
        sizes=[40, 80, 160, 320],
        repeats=1,
        warmup=0,
    )
    charts = tmp_path / "charts"
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Demo\n\n<!-- sortlab:tables:start -->\n<!-- sortlab:tables:end -->\n",
        encoding="utf-8",
    )
    write_all(report, charts, readme)
    pngs = list(charts.glob("*.png"))
    assert pngs
    assert all(p.stat().st_size > 0 for p in pngs)
    text = readme.read_text(encoding="utf-8")
    assert "Measured exponents" in text
    assert "# Demo" in text


def test_table_injection_idempotent(tmp_path: Path) -> None:
    report = run_matrix(
        algorithms=["insertion_sort"],
        distributions=["random"],
        sizes=[30, 60, 120, 240],
        repeats=1,
        warmup=0,
    )
    readme = tmp_path / "README.md"
    readme.write_text(
        "HEAD\n<!-- sortlab:tables:start -->\nold\n<!-- sortlab:tables:end -->\nTAIL\n",
        encoding="utf-8",
    )
    tables = markdown_tables(report)
    inject_tables(readme, tables)
    first = readme.read_text(encoding="utf-8")
    inject_tables(readme, tables)
    second = readme.read_text(encoding="utf-8")
    assert first == second
    assert first.startswith("HEAD\n")
    assert first.endswith("TAIL\n")
    save(report, tmp_path / "r.json")
