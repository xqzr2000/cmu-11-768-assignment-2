"""Run the Session 010 Dockerfile recipe tests, fail on empty discovery.

The tests use a deliberately fake digest; no image existence, trust, package
availability, Docker build, network call, or model request is attempted.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_chart_image_recipe_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern=PATTERN
    )
    count = suite.countTestCases()
    print(f"Chart image recipe test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no chart image tests found by {PATTERN!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
