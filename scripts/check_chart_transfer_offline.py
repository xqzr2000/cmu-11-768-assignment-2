"""Run offline chart transfer tests; reject a zero-test discovery.

Tests only handle temporary host files and a trusted pure Python reader.
They never build or launch Docker, call a model or execute shell commands.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_chart_transfer_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern=PATTERN
    )
    count = suite.countTestCases()
    print(f"Chart transfer test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no chart transfer tests found by {PATTERN!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
