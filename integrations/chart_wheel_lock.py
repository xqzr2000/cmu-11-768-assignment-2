"""Pure audit of chart wheel lock metadata against uv.lock; no network or execution.

Shared by the offline CLI and the private context staging code. An audit only
checks published metadata, not actual wheel downloads or installation.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from integrations.chart_image_recipe import PLOT_PACKAGES

ROOT = Path(__file__).resolve().parents[1]
UV_LOCK = ROOT / "uv.lock"
REQUIREMENTS = ROOT / "requirements/chart-cp312-linux-amd64.txt"
REQ_PATTERN = re.compile(
    r"^([a-z0-9][a-z0-9._-]*)==([0-9A-Za-z.+-]+) --hash=sha256:([0-9a-f]{64})$"
)
WHEEL_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
TARGET = "CPython 3.12 / linux/amd64 (manylinux)"


class ChartLockError(ValueError):
    """The chart lock is not complete or disagrees with the repository lock."""


def select_linux_cp312_wheel(pkg: dict) -> tuple[str, str]:
    """Choose exactly one CPython-ABI wheel or fall back to a universal wheel.

    A full resolver is still needed before claiming installability.
    This strict helper only recognizes the wheel labels in this committed lock.
    """
    if not isinstance(pkg.get("wheels"), list):
        raise ChartLockError(f"Missing wheels for {pkg.get('name')}")
    native: list[tuple[str, str]] = []
    universal: list[tuple[str, str]] = []
    for item in pkg["wheels"]:
        if not isinstance(item, dict) or not isinstance(item.get("url"), str):
            raise ChartLockError("Malformed wheel entry in uv.lock")
        name = urlparse(item["url"]).path.rsplit("/", 1)[-1]
        digest = item.get("hash")
        if not isinstance(digest, str) or not WHEEL_HASH_PATTERN.fullmatch(digest):
            raise ChartLockError("Missing or malformed wheel digest in uv.lock")
        entry = (name, digest.removeprefix("sha256:"))
        if re.search(r"-cp312-cp312-.*manylinux.*_x86_64\.whl$", name):
            native.append(entry)
        elif re.search(r"-(?:py3|py2\.py3)-none-any\.whl$", name):
            universal.append(entry)
    matched = native if native else universal
    if len(matched) != 1:
        raise ChartLockError(
            f"Expected one matching {TARGET} wheel for {pkg.get('name')}, found {len(matched)}"
        )
    return matched[0]


def audit_chart_wheel_lock(
    *, uv_lock: Path = UV_LOCK, requirements: Path = REQUIREMENTS
) -> list[tuple[str, str, str]]:
    """Return audited package/version/wheel records; raise on any discrepancy."""
    lock = tomllib.loads(uv_lock.read_text(encoding="utf-8"))
    by_name: dict[str, dict] = {}
    for package in lock.get("package", []):
        name = package.get("name")
        if not isinstance(name, str) or name in by_name:
            raise ChartLockError("Duplicate or invalid package identity in uv.lock")
        by_name[name] = package

    wanted_direct: dict[str, str] = {}
    for spec in PLOT_PACKAGES:
        name, version = spec.split("==", 1)
        wanted_direct[name] = version

    closure: dict[str, dict] = {}
    pending = list(wanted_direct)
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        package = by_name.get(name)
        if package is None or package.get("source") != {"registry": "https://pypi.org/simple"}:
            raise ChartLockError(f"Missing or non-registry package: {name}")
        if name in wanted_direct and package.get("version") != wanted_direct[name]:
            raise ChartLockError(f"Direct plotting version changed: {name}")
        dependencies = package.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise ChartLockError(f"Invalid dependency list for {name}")
        for dep in dependencies:
            # Fail closed if a future uv lock needs marker/extra interpretation.
            if not isinstance(dep, dict) or set(dep) != {"name"}:
                raise ChartLockError(f"Conditional/ambiguous dependency must be reviewed: {name}")
            if not isinstance(dep["name"], str):
                raise ChartLockError(f"Invalid dependency identity for {name}")
            pending.append(dep["name"])
        closure[name] = package

    actual: dict[str, tuple[str, str]] = {}
    for line in requirements.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        matched = REQ_PATTERN.fullmatch(line)
        if not matched:
            raise ChartLockError(f"Unexpected or unhashed requirement syntax: {line[:60]!r}")
        name, version, wheel_sha256 = matched.groups()
        if name in actual:
            raise ChartLockError(f"Duplicate requirement: {name}")
        actual[name] = (version, wheel_sha256)

    if set(actual) != set(closure):
        missing = sorted(set(closure) - set(actual))
        extra = sorted(set(actual) - set(closure))
        raise ChartLockError(f"Package closure mismatch: missing={missing}, extra={extra}")

    report: list[tuple[str, str, str]] = []
    for name in sorted(closure):
        package = closure[name]
        filename, expected_hash = select_linux_cp312_wheel(package)
        version = package.get("version")
        if not isinstance(version, str) or actual[name] != (version, expected_hash):
            raise ChartLockError(f"Pinned version or wheel hash mismatch: {name}")
        report.append((name, version, filename))
    return report
