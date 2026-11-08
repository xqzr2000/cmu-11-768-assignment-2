"""Run the dedicated controller tests and fail if discovery finds zero cases.

This is intentionally offline: it loads only local unittest modules and never
creates a provider client or Docker sandbox.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_controller_*_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"),
        pattern=PATTERN,
    )
    count = suite.countTestCases()
    print(f"Controller test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no controller tests found by {PATTERN!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
