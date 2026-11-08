"""Zero-Docker tests of allowlisted chart build-context assembly and cleanup."""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from integrations.chart_build_context import (
    BuildContextError,
    ChartBuildContext,
    ContextFile,
    HELPER_SOURCE,
    prepare_chart_build_context,
    verify_chart_build_context,
)
from integrations.chart_image_recipe import ImageRecipeError
from integrations.task_artifacts import ArtifactError, CSVAsset, TaskInputSnapshot

# Deliberately fictitious, syntax-valid reference: never used for a real build.
FAKE_BASE = "python:3.12-slim@sha256:" + "c" * 64


def snapshot(data: bytes = b"category,value\nA,1\nB,2\n") -> TaskInputSnapshot:
    return TaskInputSnapshot(
        "synthetic",
        (CSVAsset("data.csv", data, hashlib.sha256(data).hexdigest()),),
    )


class ChartBuildContextOfflineTests(unittest.TestCase):
    def test_exact_three_file_context_and_private_permissions(self):
        with tempfile.TemporaryDirectory() as parent:
            with prepare_chart_build_context(snapshot(), FAKE_BASE, parent_dir=Path(parent)) as context:
                self.assertEqual(
                    {entry.relative_path for entry in context.files},
                    {"Dockerfile", "inputs/data.csv", "trusted/extract_figure.py"},
                )
                self.assertEqual(
                    stat.S_IMODE(context.root.stat().st_mode), 0o700
                )
                self.assertEqual((context.root / "inputs/data.csv").read_bytes(),
                                 b"category,value\nA,1\nB,2\n")
                for directory in ("inputs", "trusted"):
                    self.assertEqual(
                        stat.S_IMODE((context.root / directory).stat().st_mode), 0o700
                    )
                for entry in context.files:
                    self.assertEqual(
                        stat.S_IMODE((context.root / entry.relative_path).stat().st_mode), 0o600
                    )
                verify = verify_chart_build_context(context)
                self.assertEqual(verify["file_count"], 3)
                self.assertFalse(verify["docker_build_authorized"])
                self.assertEqual(verify["docker_builds"], 0)
                self.assertEqual(verify["model_requests"], 0)
                self.assertNotIn(parent, str(verify))
                self.assertNotIn(parent, repr(context))
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_context_uses_only_fixed_trusted_extractor_source(self):
        with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
            self.assertEqual(
                (context.root / "trusted/extract_figure.py").read_bytes(),
                HELPER_SOURCE.read_bytes(),
            )
            self.assertEqual(
                (context.root / "Dockerfile").read_text(encoding="utf-8"),
                context.recipe.dockerfile,
            )

    def test_multiple_csv_files_staged_by_name_and_digest(self):
        original = snapshot().assets[0]
        extra = b"category,value\nC,3\n"
        other = CSVAsset("other.csv", extra, hashlib.sha256(extra).hexdigest())
        task = TaskInputSnapshot("synthetic", (original, other))
        with prepare_chart_build_context(task, FAKE_BASE) as context:
            self.assertEqual(
                {entry.relative_path for entry in context.files},
                {"Dockerfile", "inputs/data.csv", "inputs/other.csv",
                 "trusted/extract_figure.py"}
            )
            self.assertEqual((context.root / "inputs/other.csv").read_bytes(), extra)
            self.assertEqual(verify_chart_build_context(context)["file_count"], 4)

    def test_cleanup_on_exception_inside_context(self):
        with tempfile.TemporaryDirectory() as parent:
            with self.assertRaisesRegex(RuntimeError, "abort"):
                with prepare_chart_build_context(snapshot(), FAKE_BASE,
                                                 parent_dir=Path(parent)) as context:
                    self.assertTrue((context.root / "Dockerfile").exists())
                    raise RuntimeError("abort")
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_rejects_unsupported_or_mutable_base_before_any_writes(self):
        with tempfile.TemporaryDirectory() as parent:
            with self.assertRaises(ImageRecipeError):
                with prepare_chart_build_context(snapshot(), "python:3.12-slim",
                                                 parent_dir=Path(parent)):
                    pass
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_rejects_untrusted_snapshot_before_context_creation(self):
        bad = TaskInputSnapshot("synthetic", (
            CSVAsset("data.csv", b"secret", "0" * 64),
        ))
        with tempfile.TemporaryDirectory() as parent:
            with self.assertRaises(ArtifactError):
                with prepare_chart_build_context(bad, FAKE_BASE,
                                                 parent_dir=Path(parent)):
                    pass
            self.assertEqual(list(Path(parent).iterdir()), [])

    def test_verify_detects_tampered_csv_content(self):
        with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
            (context.root / "inputs/data.csv").write_bytes(b"tampered")
            with self.assertRaises(BuildContextError):
                verify_chart_build_context(context)

    def test_verify_detects_modified_dockerfile_or_helper(self):
        for file in ("Dockerfile", "trusted/extract_figure.py"):
            with self.subTest(file=file):
                with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
                    (context.root / file).write_bytes(b"not the trusted source")
                    with self.assertRaises(BuildContextError):
                        verify_chart_build_context(context)

    def test_verify_rejects_extra_secret_or_repository_content(self):
        for unexpected in (".env", ".git/config", "src/other.py"):
            with self.subTest(unexpected=unexpected):
                with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
                    extra = context.root / unexpected
                    extra.parent.mkdir(parents=True, exist_ok=True)
                    extra.write_bytes(b"untrusted")
                    with self.assertRaises(BuildContextError):
                        verify_chart_build_context(context)

    def test_verify_rejects_symlinks_and_changed_permissions(self):
        with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
            target = context.root / "inputs/data.csv"
            target.unlink()
            target.symlink_to(context.root / "Dockerfile")
            with self.assertRaises(BuildContextError):
                verify_chart_build_context(context)
        with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
            (context.root / "Dockerfile").chmod(0o644)
            with self.assertRaises(BuildContextError):
                verify_chart_build_context(context)

    def test_verify_rejects_forged_or_oversized_manifest(self):
        with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
            forged = replace(context.files[0], size_bytes=10**10)
            candidate = ChartBuildContext(
                context.root, context.recipe,
                (forged, *context.files[1:])
            )
            with self.assertRaises(BuildContextError):
                verify_chart_build_context(candidate)

    def test_disallows_symlinked_parent_and_invalid_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            link = parent / "alias"
            link.symlink_to(parent, target_is_directory=True)
            with self.assertRaises(BuildContextError):
                with prepare_chart_build_context(snapshot(), FAKE_BASE,
                                                 parent_dir=link):
                    pass
            with self.assertRaises(BuildContextError):
                with prepare_chart_build_context(snapshot(), FAKE_BASE,
                                                 parent_dir=parent / "missing"):
                    pass

    def test_never_runs_docker_or_subprocess_or_reads_env_secrets(self):
        with patch.object(subprocess, "run",
                          side_effect=AssertionError("subprocess not authorized")) as run:
            with patch.dict(os.environ, {"OPENAI_API_KEY": "sensitive-token"}):
                with prepare_chart_build_context(snapshot(), FAKE_BASE) as context:
                    manifest = context.manifest()
                    self.assertNotIn("sensitive-token", str(manifest))
                    self.assertEqual(verify_chart_build_context(context)["docker_builds"], 0)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
