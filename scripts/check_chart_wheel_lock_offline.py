"""CLI entry point for the shared offline chart wheel metadata auditor."""

from __future__ import annotations

import sys

from integrations.chart_wheel_lock import (
    PLOT_PACKAGES,
    ChartLockError,
    TARGET,
    audit_chart_wheel_lock,
    select_linux_cp312_wheel,
)


def main() -> int:
    try:
        report = audit_chart_wheel_lock()
    except (ChartLockError, ValueError, OSError, KeyError) as error:
        print(f"Chart wheel lock audit FAILED: {error}", file=sys.stderr)
        return 1
    print(f"Chart wheel lock audit: {len(report)} fully hashed package(s), {TARGET}")
    print(f"Direct roots: {len(PLOT_PACKAGES)}; transitive: {len(report) - len(PLOT_PACKAGES)}")
    for name, version, filename in report:
        print(f"  {name}=={version} -> {filename}")
    print("PASS: requirements match the committed uv.lock metadata; no network/download/install.")
    print("NOT VERIFIED: actual package download, wheel integrity, pip resolution or Docker build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
