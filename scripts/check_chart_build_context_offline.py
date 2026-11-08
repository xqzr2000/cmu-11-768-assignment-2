"""Run minimal Docker build-context offline tests, failing on empty discovery.

Tests only use synthetic temporary host files. No Docker builds/launches,
network requests, shell commands or model calls are authorized or executed.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_chart_build_context_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern=PATTERN
    )
    count = suite.countTestCases()
    print(f"Chart build context test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no chart build context tests found by {PATTERN!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
