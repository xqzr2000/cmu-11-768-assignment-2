"""Minimum private Docker build context assembly; no Docker or model calls.

An ephemeral context contains ONLY Dockerfile, vetted CSV snapshots and the
version-controlled fixed extractor script. No repository checkout is copied.
The context is for future independent human review and authorized build only.

A digest-shaped base reference is NOT evidence that the image exists, is
trusted, or matches the runtime architecture. This module never builds it.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from integrations.chart_image_recipe import ChartImageRecipe, plan_chart_image
from integrations.chart_transfer import stage_input_snapshots
from integrations.task_artifacts import ArtifactError, TaskInputSnapshot

HELPER_SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "figure_extract_worker.py"
MAX_HELPER_BYTES = 128 * 1024
MAX_CONTEXT_BYTES = 512 * 1024
CONTEXT_FILE_MODE = 0o600
CONTEXT_DIRECTORY_MODE = 0o700
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class BuildContextError(ValueError):
    """Context assembly or verification cannot uphold the minimum-file policy."""


@dataclass(frozen=True)
class ContextFile:
    relative_path: str
    size_bytes: int
    sha256: str

    def manifest(self) -> dict[str, object]:
        return {
            "path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ChartBuildContext:
    """Ephemeral absolute path; never print host paths in a public manifest."""

    root: Path = field(repr=False)
    recipe: ChartImageRecipe
    files: tuple[ContextFile, ...]

    def manifest(self) -> dict[str, object]:
        return {
            "mode": "offline",
            "base_image": self.recipe.base_image,
            "dockerfile_sha256": self.recipe.dockerfile_sha256,
            "files": [entry.manifest() for entry in self.files],
            "file_count": len(self.files),
            "total_file_bytes": sum(entry.size_bytes for entry in self.files),
            "contains_checkout": False,
            "contains_host_credentials": False,
            "docker_build_authorized": False,
            "docker_builds": 0,
            "sandbox_launches": 0,
            "model_requests": 0,
        }


def _write_only(root: Path, rel: str, data: bytes) -> ContextFile:
    """Create a new regular file from supplied bytes, never follow a symlink."""
    destination = root.joinpath(*rel.split("/"))
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise BuildContextError("Required context directory is missing or unsafe.")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(destination, flags, CONTEXT_FILE_MODE)
    with os.fdopen(fd, "wb") as output:
        output.write(data)
    digest = hashlib.sha256(data).hexdigest()
    if destination.stat().st_size != len(data):
        raise BuildContextError("Context write size mismatch.")
    return ContextFile(rel, len(data), digest)


def _scan_context_paths(root: Path) -> tuple[set[str], set[str]]:
    """Inspect exactly one ephemeral context, without following symlinks."""
    observed_files: set[str] = set()
    observed_dirs: set[str] = set()
    for parent, folders, filenames in os.walk(root, followlinks=False):
        here = Path(parent)
        for name in folders:
            target = here / name
            if target.is_symlink() or not target.is_dir():
                raise BuildContextError("Context must not contain symlinked directories.")
            if stat.S_IMODE(target.stat().st_mode) != CONTEXT_DIRECTORY_MODE:
                raise BuildContextError("Context directories must remain private.")
            observed_dirs.add(target.relative_to(root).as_posix())
        for name in filenames:
            target = here / name
            if target.is_symlink() or not target.is_file():
                raise BuildContextError("Context must contain only regular files.")
            if stat.S_IMODE(target.stat().st_mode) != CONTEXT_FILE_MODE:
                raise BuildContextError("Context files must remain private.")
            observed_files.add(target.relative_to(root).as_posix())
    return observed_files, observed_dirs


def verify_chart_build_context(context: ChartBuildContext) -> dict[str, object]:
    """Verify exact allowlisted layout and byte checksums before a future build."""
    if not isinstance(context, ChartBuildContext):
        raise BuildContextError("Expected ChartBuildContext.")
    root = context.root
    if root.is_symlink() or not root.is_dir():
        raise BuildContextError("Build context must be a non-symlink directory.")
    if stat.S_IMODE(root.stat().st_mode) != CONTEXT_DIRECTORY_MODE:
        raise BuildContextError("Build context root must be private.")

    if not all(isinstance(entry, ContextFile) and isinstance(entry.relative_path, str)
               for entry in context.files):
        raise BuildContextError("Invalid context manifest entry.")
    expected = {entry.relative_path for entry in context.files}
    if len(expected) != len(context.files):
        raise BuildContextError("Duplicate context file declarations.")
    csv_files = {p for p in expected if p.startswith("inputs/")}
    allowed = csv_files | {"Dockerfile", "trusted/extract_figure.py"}
    if expected != allowed or not csv_files or len(csv_files) > 8:
        raise BuildContextError("Expected only the Dockerfile, trusted helper and 1-8 CSV files.")
    for name in csv_files:
        if not re.fullmatch(r"inputs/[A-Za-z0-9][A-Za-z0-9._-]{0,63}\.csv", name):
            raise BuildContextError("Context includes an unsafe CSV path.")

    found_files, found_dirs = _scan_context_paths(root)
    if found_files != expected or found_dirs != {"inputs", "trusted"}:
        raise BuildContextError("Unexpected, missing or extra files in minimal build context.")

    total_bytes = 0
    for entry in context.files:
        cap = MAX_HELPER_BYTES if entry.relative_path == "trusted/extract_figure.py" else (
            64 * 1024 if entry.relative_path.startswith("inputs/") else 16 * 1024
        )
        if (type(entry.size_bytes) is not int or not 0 < entry.size_bytes <= cap
            or not isinstance(entry.sha256, str) or not SHA256_PATTERN.fullmatch(entry.sha256)):
            raise BuildContextError("Invalid build context manifest entry.")
        total_bytes += entry.size_bytes
        if total_bytes > MAX_CONTEXT_BYTES:
            raise BuildContextError("Minimal build context exceeds total byte limit.")
        source = root.joinpath(*entry.relative_path.split("/"))
        # Reading back is bounded by declared sizes; no arbitrary host paths.
        with source.open("rb") as stream:
            content = stream.read(entry.size_bytes + 1)
        if len(content) != entry.size_bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise BuildContextError("Build context file content differs from its manifest.")

    actual_dockerfile = (root / "Dockerfile").read_bytes()
    if actual_dockerfile.decode("utf-8") != context.recipe.dockerfile:
        raise BuildContextError("Build-context Dockerfile differs from the approved recipe.")
    return context.manifest()


@contextmanager
def prepare_chart_build_context(
    snapshot: TaskInputSnapshot,
    base_image: str,
    *,
    parent_dir: Path | None = None,
) -> Iterator[ChartBuildContext]:
    """Build and verify a minimal *host-side* directory, clean it on exit.

    Caller supplies a digest-formatted reference, but this function does not
    verify it exists and never launches Docker or reads from the network.
    """
    recipe = plan_chart_image(base_image)  # Reject mutable/injected base tags early.
    if parent_dir is not None:
        parent_dir = Path(parent_dir)
        if parent_dir.is_symlink() or not parent_dir.is_dir():
            raise BuildContextError("Parent staging directory must be a regular directory.")

    # First staging pass revalidates all in-memory CSV bytes/digests; it uses
    # a separate temporary directory, not the project's checkout.
    with stage_input_snapshots(snapshot) as staged:
        with tempfile.TemporaryDirectory(prefix="session010-buildctx-", dir=parent_dir) as temp:
            root = Path(temp)
            (root / "inputs").mkdir(mode=CONTEXT_DIRECTORY_MODE)
            (root / "trusted").mkdir(mode=CONTEXT_DIRECTORY_MODE)
            files: list[ContextFile] = []
            files.append(_write_only(root, "Dockerfile", recipe.dockerfile.encode("utf-8")))
            for entry in staged.inputs:
                data = entry.source.read_bytes()
                if len(data) != entry.size_bytes or hashlib.sha256(data).hexdigest() != entry.sha256:
                    raise BuildContextError("Temporary CSV staging changed after its verification.")
                files.append(_write_only(root, "inputs/" + entry.source.name, data))

            if HELPER_SOURCE.is_symlink() or not HELPER_SOURCE.is_file():
                raise BuildContextError("Trusted extractor source is missing or symlinked.")
            if HELPER_SOURCE.stat().st_size > MAX_HELPER_BYTES:
                raise BuildContextError("Extractor source exceeds the 128 KiB limit.")
            helper_bytes = HELPER_SOURCE.read_bytes()
            if not helper_bytes or len(helper_bytes) > MAX_HELPER_BYTES:
                raise BuildContextError("Trusted extractor source is empty or oversized.")
            # Keep this source fixed; never let task data or a model replace it.
            files.append(_write_only(root, "trusted/extract_figure.py", helper_bytes))
            context = ChartBuildContext(root, recipe, tuple(files))
            verify_chart_build_context(context)
            yield context
