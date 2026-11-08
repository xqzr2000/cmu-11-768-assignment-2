"""Trusted constant-data plot for a future separately approved Docker smoke run.

Session 013 tests this module on the host only. It is not staged in the chart
image, does not call Docker or a model, and is not a general plotting agent.
Production main() accepts no arguments and writes only /workspace/figure.png.
No task CSVs, environment secrets, network, shell, or arbitrary model code.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

FIGURE_PATH = Path("/workspace/figure.png")
CATEGORIES = ("Alpha", "Beta", "Gamma")
VALUES = (2, 5, 3)
WIDTH_PX = 640
HEIGHT_PX = 480
MAX_FIGURE_BYTES = 2 * 1024 * 1024


def render_synthetic_chart(destination: Path) -> None:
    """Make one known-good PNG, exclusively creating an absent figure.png.

    The destination argument is for offline tests only. Production main()
    always passes the fixed /workspace path. The future container must have
    a private /workspace owned by its unprivileged runtime user.
    """
    destination = Path(destination)
    if (destination.name != "figure.png" or not destination.parent.is_dir()
            or destination.parent.is_symlink()):
        raise ValueError("Expected figure.png in an existing regular directory.")

    # Import lazily: importing the module for a static review does not render.
    import matplotlib
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    figure, axes = plt.subplots(figsize=(6.4, 4.8), dpi=100)
    try:
        axes.bar(CATEGORIES, VALUES)
        axes.set_title("Synthetic chart smoke test")
        axes.set_ylabel("Fixed values")
        axes.set_ylim(0, 6)
        figure.tight_layout()

        # Exclusive open prevents accidental overwrite or symlink traversal.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(destination, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as output:
                figure.savefig(output, format="png", dpi=100)
            size = destination.stat().st_size
            if not 0 < size <= MAX_FIGURE_BYTES:
                raise ValueError("Synthetic figure is missing or oversized.")
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    finally:
        plt.close(figure)


def main() -> int:
    if len(sys.argv) != 1:
        print("Synthetic smoke worker accepts no arguments.", file=sys.stderr)
        return 2
    try:
        render_synthetic_chart(FIGURE_PATH)
    except (OSError, ValueError, RuntimeError):
        print("Synthetic chart smoke rendering failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
