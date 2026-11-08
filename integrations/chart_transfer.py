"""Offline-only transfer planning for vetted task CSVs and figure extraction.

The staging context writes *only validated CSV snapshots (including none)* into a private,
short-lived host directory for a future reviewed Docker image build. It neither
imports Docker nor builds an image, launches a sandbox, runs commands, contacts
a model, or copies host credentials. Temporary files are deleted on exit.

The extraction plan is inert metadata for a trusted, fixed container helper;
it is NOT routed through model-generated run_shell calls or the gateway's
truncated command-output channel.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from integrations.task_artifacts import (
    ArtifactError,
    CSVAsset,
    CSV_FILENAME,
    MAX_CSV_BYTES,
    MAX_INPUT_FILES,
    MAX_TOTAL_CSV_BYTES,
    MAX_ENVELOPE_CHARS,
    TaskInputSnapshot,
)

# Script will be copied into a future chart-capable image only after approval.
EXTRACTION_HELPER_TARGET = "/opt/assignment/extract_figure.py"
EXTRACTION_ARGV = ("python", EXTRACTION_HELPER_TARGET)
FIGURE_CONTAINER_PATH = "/workspace/figure.png"
SHA256_LOWER = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class StagedInput:
    """Trusted build-time file reference; hide host staging path in repr."""

    source: Path = field(repr=False)
    destination: str
    size_bytes: int
    sha256: str

    def manifest(self) -> dict[str, object]:
        return {
            "destination": self.destination,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class InputStagingPlan:
    """Trusted staging paths only; no Docker recipe or execution attached."""

    task_id: str
    inputs: tuple[StagedInput, ...]

    def manifest(self) -> dict[str, object]:
        return {
            "mode": "offline",
            "task_id": self.task_id,
            "file_count": len(self.inputs),
            "files": [entry.manifest() for entry in self.inputs],
            "docker_builds": 0,
            "sandbox_launches": 0,
            "model_requests": 0,
        }


def _validate_snapshot(snapshot: TaskInputSnapshot) -> tuple[CSVAsset, ...]:
    """Revalidate bytes rather than trusting manually constructed dataclasses."""
    if not isinstance(snapshot, TaskInputSnapshot):
        raise ArtifactError("Expected a verified task-input snapshot.")
    if not isinstance(snapshot.task_id, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", snapshot.task_id
    ):
        raise ArtifactError("Unsafe task identifier.")
    if not isinstance(snapshot.assets, tuple) or len(snapshot.assets) > MAX_INPUT_FILES:
        raise ArtifactError("Invalid task input count (expected 0 to 8 CSV files).")
    total = 0
    names: set[str] = set()
    for asset in snapshot.assets:
        if not isinstance(asset, CSVAsset):
            raise ArtifactError("Invalid task input type.")
        if not isinstance(asset.name, str) or not CSV_FILENAME.fullmatch(asset.name):
            raise ArtifactError("Unsafe task input filename.")
        if asset.name in names:
            raise ArtifactError("Duplicate CSV filename.")
        names.add(asset.name)
        if not isinstance(asset.data, bytes) or not 0 < len(asset.data) <= MAX_CSV_BYTES:
            raise ArtifactError("CSV payload size exceeds allowed bounds.")
        if b"\x00" in asset.data:
            raise ArtifactError("CSV payload contains a NUL byte.")
        try:
            asset.data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ArtifactError("CSV payload is not UTF-8.") from exc
        if not isinstance(asset.sha256, str) or not SHA256_LOWER.fullmatch(asset.sha256):
            raise ArtifactError("CSV checksum is invalid.")
        if hashlib.sha256(asset.data).hexdigest() != asset.sha256:
            raise ArtifactError("CSV checksum differs from staged bytes.")
        total += len(asset.data)
        if total > MAX_TOTAL_CSV_BYTES:
            raise ArtifactError("Total CSV payload exceeds allowed bounds.")
    return snapshot.assets


@contextmanager
def stage_input_snapshots(
    snapshot: TaskInputSnapshot, *, parent_dir: Path | None = None
) -> Iterator[InputStagingPlan]:
    """Write private, short-lived host files from verified bytes; delete on exit.

    These paths are intended for a *future*, separately approved
    DockerImage.add_local_file(source, destination). That API must not be called
    until the image/digest and build policy have been reviewed.
    """
    assets = _validate_snapshot(snapshot)  # Validate *before* any host writes.
    with tempfile.TemporaryDirectory(
        prefix="session010-csv-", dir=parent_dir
    ) as temporary:
        root = Path(temporary)
        inputs_dir = root / "inputs"
        inputs_dir.mkdir(mode=0o700)
        staged: list[StagedInput] = []
        for asset in assets:
            destination = f"/opt/assignment/inputs/{asset.name}"
            source = inputs_dir / asset.name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(source, flags, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(asset.data)
            # Re-read the staged bytes before trusting them for future build.
            if hashlib.sha256(source.read_bytes()).hexdigest() != asset.sha256:
                raise ArtifactError("Staged CSV checksum verification failed.")
            staged.append(StagedInput(source, destination, len(asset.data), asset.sha256))
        yield InputStagingPlan(snapshot.task_id, tuple(staged))


def preview_figure_extraction() -> dict[str, object]:
    """Fixed helper protocol metadata; no extraction, Docker or shell execution."""
    return {
        "mode": "offline",
        "container_path": FIGURE_CONTAINER_PATH,
        "helper_target": EXTRACTION_HELPER_TARGET,
        "argv": list(EXTRACTION_ARGV),
        "shell": False,
        "max_envelope_chars": MAX_ENVELOPE_CHARS,
        "requires_separate_sandbox_approval": True,
        "docker_commands": 0,
        "model_requests": 0,
    }
