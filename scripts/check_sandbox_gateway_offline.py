"""Run Session 010 fake-Docker gateway tests; fail if discovery is empty.

All test doubles live in the repository. There are no API or Docker calls.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_sandbox_gateway_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"), pattern=PATTERN
    )
    count = suite.countTestCases()
    print(f"Sandbox gateway test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no tests found by {PATTERN!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
