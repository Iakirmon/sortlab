#!/usr/bin/env python3
"""Generate the deterministic records.csv used for real-data demos."""

from __future__ import annotations

import argparse
from pathlib import Path

from sortlab.datasets import write_records_csv


def write_dataset(path: Path, *, rows: int = 200_000, seed: int = 42) -> None:
    write_records_csv(path, rows=rows, seed=seed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("-o", "--output", type=Path, default=Path("data/records.csv"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    write_dataset(args.output, rows=args.rows, seed=args.seed)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
