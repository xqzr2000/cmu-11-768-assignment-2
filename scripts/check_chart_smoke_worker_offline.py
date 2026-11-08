"""Guarded host-only tests for the fixed synthetic chart smoke worker."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_chart_smoke_worker_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern=PATTERN
    )
    count = suite.countTestCases()
    print(f"Chart smoke worker offline test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no chart smoke worker tests found by {PATTERN!r}",
              file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
