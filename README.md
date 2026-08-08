# sortlab

A measurement lab for sorting algorithms in Python: readable implementations, honest
instrumentation, and complexity you can read off a log-log plot.

<!-- sortlab:tables:start -->
### Measured exponents (random)

| Algorithm | Theory | Measured exponent | R² | Classification |
|---|---|---:|---:|---|
| `bubble_sort` | O(n^2) | 2.02 | 1.000 | ≈O(n²) |
| `bubble_sort_early_exit` | O(n^2) | 2.04 | 1.000 | ≈O(n²) |
| `builtin_timsort` | O(n log n) | 1.24 | 0.998 | ≈O(n log n) |
| `counting_sort` | O(n + k) | 1.05 | 0.999 | ≈O(n) |
| `heap_sort` | O(n log n) | 1.17 | 1.000 | ≈O(n log n) |
| `insertion_sort` | O(n^2) | 2.03 | 1.000 | ≈O(n²) |
| `merge_sort` | O(n log n) | 1.16 | 1.000 | ≈O(n log n) |
| `quick_sort_last` | O(n log n) | 1.13 | 1.000 | ≈O(n log n) |
| `quick_sort_median3` | O(n log n) | 1.11 | 1.000 | ≈O(n) |
| `quick_sort_random` | O(n log n) | 1.08 | 0.999 | ≈O(n) |
| `radix_sort` | O(n · k) | 1.10 | 0.998 | ≈O(n) |
| `selection_sort` | O(n^2) | 2.01 | 1.000 | ≈O(n²) |
| `shell_sort_ciura` | O(n^1.25) | 1.21 | 0.997 | ≈O(n log n) |
| `shell_sort_shell` | O(n^1.5) | 1.26 | 1.000 | ≈O(n log n) |

_Skipped/timeout rows in matrix: 0_
<!-- sortlab:tables:end -->

## Animations

| bubble | insertion | quick (median-of-3) | merge |
|---|---|---|---|
| ![bubble](docs/animations/bubble_sort.gif) | ![insertion](docs/animations/insertion_sort.gif) | ![quick](docs/animations/quick_sort_median3.gif) | ![merge](docs/animations/merge_sort.gif) |

## Charts

![time vs n random](docs/charts/time_vs_n_random.png)

![time vs n sorted](docs/charts/time_vs_n_sorted.png)

![distribution comparison](docs/charts/distribution_comparison.png)

![heatmap](docs/charts/heatmap.png)

![complexity fit](docs/charts/complexity_fit.png)

![operation counts](docs/charts/operation_counts.png)

![memory](docs/charts/memory.png)

## Findings

Numbers below come from `benchmarks/results/latest.json` on this machine
(see chart captions for CPU / Python).

1. **Insertion sort beats quicksort on nearly sorted input across the whole measured
   range.** At every `n` from 200 to 3200, `insertion_sort` on `nearly_sorted` finished
   in about **9–15%** of the time of `quick_sort_median3` (e.g. n=3200: 0.144 ms vs
   1.59 ms). There is no crossover in this window — “O(n²) is always worse” is false
   for adaptive quadratic sorts.

2. **A naive pivot turns quicksort into quadratic work on sorted data.**
   `quick_sort_last` on `sorted` vs `random` slows down by **9.5× at n=200**, **54× at
   n=1600**, and **99× at n=3200** (0.212 s vs 0.0021 s). Same algorithm, same `n`,
   different input shape.

3. **Comparisons and writes are different metrics.** On random n=3200, `selection_sort`
   performed **5,118,400** comparisons but only **6,384** writes; `bubble_sort` wrote
   about **5.18 million** times. Selection is still slow — it just proves the counters
   measure separate things.

4. **Radix sort breaks the comparison-sort story.** On random n=3200, `radix_sort`
   measured exponent **1.08** with **0 comparisons** in the counting mode (bucket work
   only), while comparison sorts sit on Ω(n log n). The cost is the integer-key
   assumption and extra memory.

5. **CPython’s Timsort is still far ahead.** On random n=3200, `builtin_timsort`
   took **0.212 ms**; the best pure-Python entry (`counting_sort`) was ~**3×** slower,
   and `quick_sort_median3` ~**9×** slower. The gap is the interpreter, not the idea.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

sortlab list
sortlab bench                          # writes benchmarks/results/latest.json
sortlab report                         # charts + README tables
sortlab animate --algorithm merge_sort
sortlab dataset --rows 200000 -o data/records.csv
```

## Add your own algorithm

Create `src/sortlab/algorithms/<name>/` with `algorithm.py`, `__init__.py`, and a Polish
`README.md`, then decorate the function with `@register(...)`. No other files need editing —
discovery and the shared test suite pick it up automatically.

## Measurement methodology

- **Timing mode:** raw `int` values, fresh copy per repeat, one discarded warmup,
  `gc.disable()` during measurement, `time.perf_counter()`, reported **median**.
- **Counting mode:** `TrackedList` + `Tracked` values. Never mixed with timing.
- **Guards:** `max_n` skips and hard timeouts stay in the result matrix as skipped rows.
- **Limits (stated honestly):** CPU noise on short runs; RSS sampling only kept for
  runs ≥ 0.5 s; results are from one machine; `builtin_timsort` comparisons happen in C
  and are **not** visible to `Tracked`.

## Architecture

Algorithms never import the measurement layer. Dependencies point one way:
`algorithms → registry → types`, while `bench` / `instrument` / `report` read the
registry. An algorithm that knows it is being measured stops being an honest object of
measurement.
