"""Run offline task artifact checks, failing on zero discovered tests.

Uses temporary synthetic files and Pillow; does not import Docker or send
any model requests. The repository's source task fixtures are unchanged.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = "test_task_artifacts_offline.py"


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"),
        pattern=PATTERN,
    )
    count = suite.countTestCases()
    print(f"Task artifact test discovery: {count} test(s)", flush=True)
    if count == 0:
        print(f"ERROR: no artifact tests found by {PATTERN!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
