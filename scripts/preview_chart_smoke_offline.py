"""Read-only, locally audited chart-image *preview*: NEVER build or run Docker.

Generates two synthetic private contexts (zero CSV, one CSV), verifies their
allowlisted contents and permissions, then destroys both. Only safe metadata
and the exact static Dockerfile text are printed, never CSV bytes or host paths.

This script has no Docker, subprocess, shell, network, model or cloud imports.
The candidate digest came from earlier registry *metadata* inspection only.
"""
from __future__ import annotations

import hashlib
import json
import stat

from integrations.chart_build_context import (
    prepare_chart_build_context,
    verify_chart_build_context,
)
from integrations.chart_image_recipe import plan_chart_image
from integrations.chart_wheel_lock import audit_chart_wheel_lock
from integrations.task_artifacts import CSVAsset, TaskInputSnapshot

# Previously observed linux/amd64 Python 3.12-slim OCI manifest candidate;
# not revalidated or authenticated by this offline preview.
CANDIDATE_BASE_IMAGE = (
    "python:3.12-slim@sha256:"
    "05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177"
)
SYNTHETIC_CSV = b"category,value\nA,1\nB,2\n"
CASE_FILES = {
    "zero_csv": frozenset({
        "Dockerfile",
        "trusted/extract_figure.py",
        "trusted/smoke_chart.py",
        "requirements/chart-cp312-linux-amd64.txt",
    }),
    "one_csv": frozenset({
        "Dockerfile",
        "inputs/synthetic.csv",
        "trusted/extract_figure.py",
        "trusted/smoke_chart.py",
        "requirements/chart-cp312-linux-amd64.txt",
    }),
}


def build_offline_preview() -> dict[str, object]:
    """Create and verify two short-lived host contexts. No Docker/API calls."""
    audited = audit_chart_wheel_lock()
    if len(audited) != 14:
        raise ValueError("Expected an audited 14-package plotting dependency closure.")
    recipe = plan_chart_image(CANDIDATE_BASE_IMAGE)
    one_csv = CSVAsset(
        "synthetic.csv", SYNTHETIC_CSV,
        hashlib.sha256(SYNTHETIC_CSV).hexdigest(),
    )
    samples = (
        ("zero_csv", TaskInputSnapshot("smoke_zero", ())),
        ("one_csv", TaskInputSnapshot("smoke_one", (one_csv,))),
    )
    cases: list[dict[str, object]] = []
    for label, snapshot in samples:
        # Temporary host context exists only INSIDE the with block and is
        # erased before this preview is returned. Never reveal context.root.
        with prepare_chart_build_context(snapshot, CANDIDATE_BASE_IMAGE) as context:
            manifest = verify_chart_build_context(context)
            found = frozenset(entry["path"] for entry in manifest["files"])
            if found != CASE_FILES[label]:
                raise ValueError("Private build context differs from expected allowlist.")
            if manifest["file_count"] != len(CASE_FILES[label]):
                raise ValueError("Unexpected context file count.")
            if manifest["dockerfile_sha256"] != recipe.dockerfile_sha256:
                raise ValueError("Dockerfile digest changed between contexts.")
            for rel in ("", "inputs", "trusted", "requirements"):
                directory = context.root if not rel else context.root / rel
                if stat.S_IMODE(directory.stat().st_mode) != 0o700:
                    raise ValueError("Unapproved context directory permissions.")
            actual_csv = sorted((context.root / "inputs").iterdir())
            if len(actual_csv) != len(snapshot.assets):
                raise ValueError("Private input directory differs from snapshot.")
            cases.append({
                "case": label,
                "declared_csv_count": len(snapshot.assets),
                "inputs_directory_exists": True,
                "private_directory_permissions_verified": True,
                "context": manifest,
            })

    return {
        "mode": "offline_preview_only",
        "candidate_base_image": CANDIDATE_BASE_IMAGE,
        "candidate_base_previously_observed_not_reverified": True,
        "target_platform": "linux/amd64",
        "audited_wheel_metadata_count": len(audited),
        "wheel_byte_integrity_verified": False,
        "pip_install_verified": False,
        "dockerfile_sha256": recipe.dockerfile_sha256,
        "dockerfile": recipe.dockerfile,
        "cases": cases,
        "private_contexts_destroyed": True,
        "docker_build_authorized": False,
        "docker_builds": 0,
        "docker_launches": 0,
        "network_requests": 0,
        "model_requests": 0,
        "requires_fresh_explicit_approval_for_real_build": True,
    }


def main() -> int:
    print(json.dumps(build_offline_preview(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
