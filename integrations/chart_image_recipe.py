"""Offline-only chart-capable Dockerfile *recipe* planning.

This pure module validates a caller-supplied immutable Python base image
reference, renders a fixed Dockerfile and reports its digest. It never calls
Docker, a package index, a model API, or reads host secrets.

A valid-looking sha256 string is NOT proof that its image exists or is trusted.
The pip pins below lack complete transitive dependency/wheel hashes, so this
is a reviewable development recipe, NOT a reproducible/authorized image build.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

BASE_REF_PATTERN = re.compile(r"^python:3\.12-slim@sha256:[0-9a-f]{64}$")

# Exactly the plotting packages pinned by the Assignment 2 pyproject.toml.
# They are direct-version pins, not a complete immutable package resolution.
PLOT_PACKAGES = (
    "matplotlib==3.10.5",
    "numpy==2.3.2",
    "pandas==2.3.1",
    "pillow==12.3.0",
)
RUNTIME_USER = "10001:10001"
WORKSPACE = "/workspace"
INPUT_DIRECTORY = "/opt/assignment/inputs"
EXTRACTOR_DESTINATION = "/opt/assignment/extract_figure.py"


class ImageRecipeError(ValueError):
    """Unpinned/unsupported image reference or invalid recipe configuration."""


@dataclass(frozen=True)
class ChartImageRecipe:
    """Inert Dockerfile and safe metadata; never a Docker build handle."""

    base_image: str
    dockerfile: str
    dockerfile_sha256: str

    def preview(self) -> dict[str, Any]:
        """Declare capabilities *intended*, not observed from a built image."""
        return {
            "mode": "offline",
            "base_image": self.base_image,
            "dockerfile_sha256": self.dockerfile_sha256,
            "plot_packages_requested": list(PLOT_PACKAGES),
            "runtime_user": RUNTIME_USER,
            "runtime_network_required": False,
            "workspace": WORKSPACE,
            "task_csv_directory": INPUT_DIRECTORY,
            "fixed_extractor_destination": EXTRACTOR_DESTINATION,
            "direct_dependency_versions_pinned": True,
            "full_dependency_hash_lock_verified": False,
            "image_platform_and_architecture_verified": False,
            "image_exists_verified": False,
            "image_trusted_verified": False,
            "docker_build_authorized": False,
            "docker_builds": 0,
            "sandbox_launches": 0,
            "model_requests": 0,
        }


def plan_chart_image(base_image: str) -> ChartImageRecipe:
    """Render a fixed non-root development Dockerfile with no side effects.

    A future human must supply/verify a *real* digest, platform and dependency
    lock, and separately approve any build/pull. No example digest is shipped
    as a supposedly valid release pin.
    """
    if not isinstance(base_image, str) or not BASE_REF_PATTERN.fullmatch(base_image):
        raise ImageRecipeError(
            "Supply an exact python:3.12-slim@sha256:<64 lowercase hex> base image."
        )
    dependencies = " ".join(PLOT_PACKAGES)
    dockerfile = (
        f"FROM {base_image}\n"
        "ENV MPLBACKEND=Agg \\\n"
        "    PYTHONDONTWRITEBYTECODE=1 \\\n"
        "    PYTHONUNBUFFERED=1 \\\n"
        "    HOME=/workspace\n"
        f"RUN python -m pip install --no-cache-dir --only-binary=:all: {dependencies}\n"
        "RUN mkdir -p /opt/assignment/inputs /workspace \\\n"
        "    && chmod 0755 /opt/assignment /opt/assignment/inputs \\\n"
        "    && chown 10001:10001 /workspace \\\n"
        "    && chmod 0700 /workspace\n"
        f"USER {RUNTIME_USER}\n"
        f"WORKDIR {WORKSPACE}\n"
    )
    return ChartImageRecipe(
        base_image=base_image,
        dockerfile=dockerfile,
        dockerfile_sha256=hashlib.sha256(dockerfile.encode("utf-8")).hexdigest(),
    )
