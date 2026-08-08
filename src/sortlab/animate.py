"""GIF animations from TrackedList write hooks."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import animation

from sortlab.datasets import generate
from sortlab.instrument import Counters, TrackedList
from sortlab.registry import get
from sortlab.types import Distribution


def animate(
    algorithm: str,
    out: Path,
    *,
    n: int = 60,
    distribution: Distribution = "random",
    max_frames: int = 300,
    fps: int = 30,
) -> None:
    """Render a sorting animation for ``algorithm`` to ``out``."""
    spec = get(algorithm)
    data = generate(distribution, n, seed=42)
    frames: list[list[int]] = []
    counters = Counters()

    def on_write(snapshot: list[object]) -> None:
        frames.append([int(x) for x in snapshot])

    tracked = TrackedList(data, counters, on_write=on_write)
    frames.append([int(x) for x in tracked.snapshot()])
    spec.func(tracked)

    if len(frames) > max_frames:
        step = max(1, len(frames) // max_frames)
        frames = frames[::step]
        if frames[-1] != sorted(data):
            frames.append(sorted(data))

    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(range(n), frames[0], color="#2f5d50")
    ax.set_xlim(-1, n)
    ax.set_ylim(0, max(data) * 1.1 if data else 1)
    ax.set_title(algorithm)
    ax.set_xticks([])

    def _update(frame_index: int) -> tuple[object, ...]:
        values = frames[frame_index]
        for bar, height in zip(bars, values, strict=True):
            bar.set_height(height)
        return tuple(bars)

    anim = animation.FuncAnimation(
        fig,
        _update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )
    anim.save(out, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
