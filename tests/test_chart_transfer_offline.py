"""Offline transfer planning tests: temporary local files only, never Docker/API."""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from integrations.chart_transfer import (
    EXTRACTION_ARGV,
    FIGURE_CONTAINER_PATH,
    stage_input_snapshots,
    preview_figure_extraction,
)
from integrations.task_artifacts import (
    ArtifactError,
    CSVAsset,
    MAX_FIGURE_BYTES,
    MAX_ENVELOPE_CHARS,
    TaskInputSnapshot,
    decode_figure_envelope,
    snapshot_task_csvs,
)
from scripts.figure_extract_worker import (
    MAX_FIGURE_BYTES as HELPER_MAX_BYTES,
    ExtractionError,
    main as extractor_main,
    read_figure,
)


def snapshot(*, task_id: str = "demo",
             name: str = "data.csv",
             data: bytes = b"category,value\nA,1\nB,2\n") -> TaskInputSnapshot:
    return TaskInputSnapshot(
        task_id,
        (CSVAsset(name, data, hashlib.sha256(data).hexdigest()),),
    )


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 20), (20, 100, 200)).save(buffer, format="PNG")
    return buffer.getvalue()


class ChartTransferOfflineTests(unittest.TestCase):
    def test_staging_uses_private_temp_files_and_cleans_up(self):
        snap = snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            with stage_input_snapshots(snap, parent_dir=Path(tmp)) as plan:
                self.assertEqual(plan.task_id, "demo")
                self.assertEqual(len(plan.inputs), 1)
                entry = plan.inputs[0]
                source = entry.source
                self.assertEqual(source.read_bytes(), snap.assets[0].data)
                self.assertEqual(entry.destination, "/opt/assignment/inputs/data.csv")
                self.assertEqual(entry.sha256, snap.assets[0].sha256)
                self.assertEqual(stat.S_IMODE(source.stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE(source.parent.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE(source.parent.parent.stat().st_mode), 0o700)
                self.assertNotIn(str(source), repr(entry))
                self.assertNotIn(str(source), json.dumps(plan.manifest()))
                self.assertNotIn("A,1", json.dumps(plan.manifest()))
                self.assertEqual(plan.manifest()["docker_builds"], 0)
            self.assertFalse(source.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_two_csvs_have_distinct_trusted_destinations(self):
        a = snapshot().assets[0]
        data = b"key,value\nC,3\n"
        b = CSVAsset("secondary.csv", data, hashlib.sha256(data).hexdigest())
        snap = TaskInputSnapshot("demo", (a, b))
        with stage_input_snapshots(snap) as plan:
            self.assertEqual(len(plan.inputs), 2)
            self.assertEqual(
                {entry.destination for entry in plan.inputs},
                {
                    "/opt/assignment/inputs/data.csv",
                    "/opt/assignment/inputs/secondary.csv",
                },
            )
            self.assertEqual(plan.manifest()["model_requests"], 0)

    def test_manually_constructed_bad_snapshot_rejected_before_writing(self):
        bad_cases = (
            TaskInputSnapshot("../bad", snapshot().assets),
            TaskInputSnapshot("demo", ()),
            TaskInputSnapshot("demo", (snapshot().assets[0],) * 9),
            TaskInputSnapshot("demo", (CSVAsset("../secret.csv", b"x", "f" * 64),)),
            TaskInputSnapshot("demo", (CSVAsset("data.csv", b"x", "f" * 64),)),
            TaskInputSnapshot("demo", (CSVAsset("data.csv", b"\x00", hashlib.sha256(b"\x00").hexdigest()),)),
            TaskInputSnapshot("demo", (CSVAsset("data.csv", b"\xff", hashlib.sha256(b"\xff").hexdigest()),)),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for candidate in bad_cases:
                with self.subTest(candidate=repr(candidate)), self.assertRaises(ArtifactError):
                    with stage_input_snapshots(candidate, parent_dir=Path(tmp)):
                        pass
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_duplicate_input_names_rejected(self):
        a = snapshot().assets[0]
        with self.assertRaises(ArtifactError):
            with stage_input_snapshots(TaskInputSnapshot("demo", (a, a))):
                pass

    def test_size_limits_checked_before_writes(self):
        data = b"a" * (64 * 1024 + 1)
        malformed = TaskInputSnapshot(
            "demo",
            (CSVAsset("data.csv", data, hashlib.sha256(data).hexdigest()),),
        )
        with self.assertRaises(ArtifactError):
            with stage_input_snapshots(malformed):
                pass

    def test_fixed_extractor_preview_has_no_dynamic_path_or_execution(self):
        plan = preview_figure_extraction()
        self.assertEqual(plan["mode"], "offline")
        self.assertEqual(plan["container_path"], FIGURE_CONTAINER_PATH)
        self.assertEqual(plan["argv"], list(EXTRACTION_ARGV))
        self.assertFalse(plan["shell"])
        self.assertTrue(plan["requires_separate_sandbox_approval"])
        self.assertEqual(plan["docker_commands"], 0)
        self.assertEqual(plan["model_requests"], 0)
        self.assertEqual(plan["max_envelope_chars"], MAX_ENVELOPE_CHARS)
        self.assertEqual(HELPER_MAX_BYTES, MAX_FIGURE_BYTES)

    def test_helper_produces_valid_envelope_for_existing_png(self):
        data = png_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            figure = Path(tmp) / "figure.png"
            figure.write_bytes(data)
            envelope = read_figure(figure)
        self.assertLessEqual(len(envelope), MAX_ENVELOPE_CHARS)
        decoded = decode_figure_envelope(envelope)
        self.assertEqual(decoded.data, data)
        self.assertEqual(decoded.manifest()["path"], "figure.png")
        self.assertEqual((decoded.width, decoded.height), (32, 20))

    def test_helper_rejects_missing_empty_and_non_png_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "figure.png"
            with self.assertRaises(FileNotFoundError):
                read_figure(path)
            for bad in (b"", b"not-a-png"):
                path.write_bytes(bad)
                with self.subTest(contents=bad), self.assertRaises(ExtractionError):
                    read_figure(path)

    def test_helper_rejects_oversized_file_before_reading_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "figure.png"
            with path.open("wb") as handle:
                handle.truncate(MAX_FIGURE_BYTES + 1)
            with self.assertRaises(ExtractionError):
                read_figure(path)

    def test_helper_rejects_symlink_and_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            real = directory / "legitimate.png"
            real.write_bytes(png_bytes())
            alias = directory / "figure.png"
            alias.symlink_to(real)
            with self.assertRaises((OSError, ExtractionError)):
                read_figure(alias)
            with self.assertRaises((OSError, ExtractionError)):
                read_figure(directory)

    def test_helper_no_command_line_path_override(self):
        with patch("sys.argv", ["figure_extract_worker.py", "../secret.txt"]):
            with patch("sys.stderr", new_callable=io.StringIO) as stderr:
                self.assertEqual(extractor_main(), 2)
                self.assertIn("no arguments", stderr.getvalue())

    def test_host_decoder_rejects_pretend_png_with_valid_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "figure.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\ninvalid-payload")
            encoded = read_figure(path)
        with self.assertRaises(ArtifactError):
            decode_figure_envelope(encoded)


if __name__ == "__main__":
    unittest.main()
