#!/usr/bin/env python3
"""Inspect released seed trajectories and human labels without model calls.

This is a structural/data-quality check, NOT a validator or a prediction generator.
"""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any

FAMILIES = {"execution_failure", "wrong_data", "wrong_chart", "hard_to_read"}
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


class DatasetError(ValueError):
    """The released dataset has a missing or malformed element."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DatasetError(f"{path}: cannot read JSON: {exc}") from exc


def _check_png(path: Path) -> None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or not header.startswith(PNG_HEADER):
        raise DatasetError(f"{path}: missing PNG signature or IHDR header")
    if header[12:16] != b"IHDR":
        raise DatasetError(f"{path}: missing PNG IHDR chunk")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise DatasetError(f"{path}: nonpositive PNG dimensions")


def inspect_dataset(root: Path) -> dict[str, Any]:
    artifacts = root / "artifacts"
    seed_labels = root / "seed_labels.json"
    labels = _load_json(seed_labels)
    if not isinstance(labels, dict) or not isinstance(labels.get("labels"), list):
        raise DatasetError(f"{seed_labels}: expected {{'labels': [...]}}")

    directories = sorted(artifacts.glob("*/result.json"))
    if not directories:
        raise DatasetError(f"{artifacts}: no agent runs found")
    runs: set[str] = set()
    figures = 0
    for result_path in directories:
        result = _load_json(result_path)
        if not isinstance(result, dict):
            raise DatasetError(f"{result_path}: expected object")
        run_id = result.get("run_id")
        if not isinstance(run_id, str) or not run_id or run_id != result_path.parent.name:
            raise DatasetError(f"{result_path}: run_id must match parent directory")
        if run_id in runs:
            raise DatasetError(f"duplicate run_id: {run_id}")
        runs.add(run_id)
        task = result.get("task")
        if not isinstance(task, dict) or not isinstance(task.get("instructions"), str) or not task["instructions"].strip():
            raise DatasetError(f"{result_path}: task instructions missing")
        traj = result.get("trajectory")
        if not isinstance(traj, dict) or not isinstance(traj.get("messages"), list):
            raise DatasetError(f"{result_path}: missing trajectory.messages list")
        figure = result_path.parent / "figure.png"
        if figure.is_file():
            _check_png(figure)
            figures += 1

    labeled: set[str] = set()
    counter: Counter[str] = Counter()
    acceptable = 0
    for item in labels["labels"]:
        if not isinstance(item, dict) or not isinstance(item.get("run_id"), str):
            raise DatasetError(f"{seed_labels}: malformed label entry")
        run_id = item["run_id"]
        if run_id in labeled:
            raise DatasetError(f"{seed_labels}: duplicate label for {run_id}")
        labeled.add(run_id)
        errors = item.get("errors")
        if not isinstance(errors, list):
            raise DatasetError(f"{seed_labels}: {run_id}: errors must be a reviewed list")
        if not errors:
            acceptable += 1
        seen: set[str] = set()
        for error in errors:
            if not isinstance(error, dict):
                raise DatasetError(f"{seed_labels}: {run_id}: malformed error")
            family = error.get("family")
            evidence = error.get("evidence")
            if family not in FAMILIES or family in seen:
                raise DatasetError(f"{seed_labels}: {run_id}: invalid or duplicate family: {family}")
            if not isinstance(evidence, str) or not evidence.strip():
                raise DatasetError(f"{seed_labels}: {run_id}: missing evidence for {family}")
            seen.add(family)
            counter[family] += 1
        if "execution_failure" in seen and len(seen) != 1:
            raise DatasetError(f"{seed_labels}: {run_id}: execution_failure must be terminal")

    if runs != labeled:
        raise DatasetError(
            "run/label coverage mismatch: "
            f"unlabeled={sorted(runs - labeled)}, missing_runs={sorted(labeled - runs)}"
        )
    return {
        "runs": len(runs),
        "figures": figures,
        "labeled_runs": len(labeled),
        "acceptable": acceptable,
        "families": {family: counter[family] for family in sorted(FAMILIES)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        summary = inspect_dataset(args.root)
    except DatasetError as exc:
        parser.exit(1, f"Preflight FAILED: {exc}\n")
    print(json.dumps(summary, indent=2))
    print("Offline preflight PASSED. No model or cloud infrastructure was called.")


if __name__ == "__main__":
    main()
