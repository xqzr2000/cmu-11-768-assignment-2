"""Pure input snapshot and PNG artifact checks for Session 010.

This module does not create containers, construct API clients, run commands,
build Docker images or write artifacts. Bytes are held in memory only.
A later trusted host must separately authorize and implement transport.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from workflow.tasks import AuthoredTask

MAX_INPUT_FILES = 8
MAX_CSV_BYTES = 64 * 1024
MAX_TOTAL_CSV_BYTES = 256 * 1024
MAX_FIGURE_BYTES = 2 * 1024 * 1024
MAX_FIGURE_PIXELS = 4_000_000
MAX_ENVELOPE_CHARS = ((MAX_FIGURE_BYTES + 2) // 3) * 4 + 512
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CSV_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.csv$")
SHA256_LOWER = re.compile(r"^[0-9a-f]{64}$")
FIGURE_PATH = "figure.png"
ENVELOPE_KEYS = frozenset({"path", "encoding", "size_bytes", "sha256", "data_base64"})


class ArtifactError(ValueError):
    """Unsafe task input, malformed artifact, or exceeded byte/pixel limit."""


@dataclass(frozen=True)
class CSVAsset:
    """Copy of one vetted CSV; never include raw contents in diagnostic repr."""

    name: str
    data: bytes = field(repr=False)
    sha256: str

    @property
    def size_bytes(self) -> int:
        return len(self.data)


@dataclass(frozen=True)
class TaskInputSnapshot:
    """Immutable input data snapshot; no files are sent or copied by this type."""

    task_id: str
    assets: tuple[CSVAsset, ...]

    def manifest(self) -> dict[str, Any]:
        """Small printable metadata only: no paths to host secrets or CSV bytes."""
        return {
            "mode": "offline",
            "task_id": self.task_id,
            "file_count": len(self.assets),
            "total_bytes": sum(asset.size_bytes for asset in self.assets),
            "files": [
                {
                    "name": asset.name,
                    "target": f"/opt/assignment/inputs/{asset.name}",
                    "size_bytes": asset.size_bytes,
                    "sha256": asset.sha256,
                }
                for asset in self.assets
            ],
            "docker_builds": 0,
            "sandbox_commands": 0,
            "network_requests": 0,
        }


@dataclass(frozen=True)
class ValidatedFigure:
    """Decoded PNG plus safe summary; caller decides whether and where to save."""

    data: bytes = field(repr=False)
    sha256: str
    width: int
    height: int

    def manifest(self) -> dict[str, Any]:
        return {
            "path": FIGURE_PATH,
            "format": "PNG",
            "size_bytes": len(self.data),
            "sha256": self.sha256,
            "width": self.width,
            "height": self.height,
        }


def _check_no_symlink(root: Path, candidate: Path) -> None:
    """Reject symlinks at every component below the task root."""
    try:
        rel = candidate.relative_to(root)
    except ValueError as exc:
        raise ArtifactError("CSV input is outside its task directory.") from exc
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ArtifactError("Symbolic links are not permitted in task CSV paths.")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ArtifactError("Task CSV input escapes its task directory.")


def snapshot_task_csvs(descriptor: Path) -> TaskInputSnapshot:
    """Load an authored task and copy zero or more small task-local UTF-8 CSVs.

    The snapshot is *not* automatically used as a Docker image build context.
    A future image builder must materialize the vetted bytes independently,
    recheck content digests and apply the same no-mount/no-credentials policy.
    """
    descriptor = Path(descriptor)
    if any(path.is_symlink() for path in (descriptor, *descriptor.parents)):
        raise ArtifactError("Symbolic links are not permitted in task descriptor paths.")
    if not descriptor.is_file():
        raise ArtifactError("Task descriptor must be a regular file.")
    if descriptor.stat().st_size > 128 * 1024:
        raise ArtifactError("Task descriptor exceeds the 128 KiB size cap.")
    task = AuthoredTask.load(descriptor)
    if len(task.inputs) > MAX_INPUT_FILES:
        raise ArtifactError("Chart tasks support at most 8 CSV input files.")
    root = descriptor.parent
    assets: list[CSVAsset] = []
    total = 0
    for item in task.inputs:
        if not CSV_FILENAME.fullmatch(item.name):
            raise ArtifactError("Input file name must be a safe ASCII .csv filename.")
        candidate = root / item.path
        _check_no_symlink(root, candidate)
        if not candidate.is_file():
            raise ArtifactError("Declared CSV is not a regular input file.")
        with candidate.open("rb") as stream:
            data = stream.read(MAX_CSV_BYTES + 1)
        if not data or len(data) > MAX_CSV_BYTES:
            raise ArtifactError("CSV input is empty or exceeds the 64 KiB per-file cap.")
        if b"\x00" in data:
            raise ArtifactError("CSV input contains a NUL byte.")
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ArtifactError("CSV input must be UTF-8 text.") from exc
        total += len(data)
        if total > MAX_TOTAL_CSV_BYTES:
            raise ArtifactError("CSV inputs exceed the 256 KiB total cap.")
        assets.append(CSVAsset(item.name, data, hashlib.sha256(data).hexdigest()))
    return TaskInputSnapshot(task.task_id, tuple(assets))


def validate_figure_png(data: bytes) -> ValidatedFigure:
    """Fail closed on oversized, corrupt, mislabeled or huge PNG images."""
    if not isinstance(data, bytes) or not data.startswith(PNG_SIGNATURE):
        raise ArtifactError("Artifact is not a PNG file.")
    if not 0 < len(data) <= MAX_FIGURE_BYTES:
        raise ArtifactError("PNG exceeds the 2 MiB size cap.")
    # A PNG must end exactly at its IEND chunk, not hide appended payloads.
    offset = len(PNG_SIGNATURE)
    first = True
    while offset < len(data):
        if len(data) - offset < 12:
            raise ArtifactError("PNG chunk header is truncated.")
        length = int.from_bytes(data[offset:offset + 4], "big")
        chunk_type = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ArtifactError("PNG chunk exceeds the available bytes.")
        if first and chunk_type != b"IHDR":
            raise ArtifactError("PNG must begin with IHDR.")
        first = False
        offset = end
        if chunk_type == b"IEND":
            if length != 0 or offset != len(data):
                raise ArtifactError("PNG has invalid or trailing data after IEND.")
            break
    else:
        raise ArtifactError("PNG does not contain a terminal IEND chunk.")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG":
                raise ArtifactError("Figure format must be PNG.")
            width, height = image.size
            if width < 1 or height < 1 or width * height > MAX_FIGURE_PIXELS:
                raise ArtifactError("Figure dimensions exceed the pixel limit.")
            image.verify()
        # Pillow verification checks structure; load checks pixel data too.
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except (OSError, SyntaxError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        if isinstance(exc, ArtifactError):
            raise
        raise ArtifactError("PNG data is malformed or unreadable.") from exc
    return ValidatedFigure(data, hashlib.sha256(data).hexdigest(), width, height)


def decode_figure_envelope(raw: str) -> ValidatedFigure:
    """Decode a *trusted extraction helper's* JSON result, not raw model text.

    The future fixed Docker extraction helper may emit this format. This
    decoder never accesses Docker and never writes data to the host.
    """
    if not isinstance(raw, str) or len(raw) > MAX_ENVELOPE_CHARS:
        raise ArtifactError("Figure transport envelope exceeds the size limit.")
    try:
        payload = json.loads(raw)
    except ValueError as exc:
        raise ArtifactError("Figure transport envelope is invalid JSON.") from exc
    if not isinstance(payload, dict) or set(payload) != ENVELOPE_KEYS:
        raise ArtifactError("Figure transport envelope has unexpected fields.")
    if payload["path"] != FIGURE_PATH or payload["encoding"] != "base64":
        raise ArtifactError("Figure transport path or encoding is not supported.")
    encoded = payload["data_base64"]
    count = payload["size_bytes"]
    sha = payload["sha256"]
    if (not isinstance(encoded, str)
        or len(encoded) > ((MAX_FIGURE_BYTES + 2) // 3 * 4)
        or type(count) is not int or not 0 < count <= MAX_FIGURE_BYTES
        or not isinstance(sha, str) or not SHA256_LOWER.fullmatch(sha)):
        raise ArtifactError("Figure transport size, digest or encoding is invalid.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ArtifactError("Figure transport is not valid base64.") from exc
    if base64.b64encode(data).decode("ascii") != encoded:
        raise ArtifactError("Figure transport is not canonical base64.")
    if len(data) != count or hashlib.sha256(data).hexdigest() != sha:
        raise ArtifactError("Figure transport size or digest does not match.")
    return validate_figure_png(data)
