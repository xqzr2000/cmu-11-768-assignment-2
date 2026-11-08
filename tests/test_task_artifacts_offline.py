"""Offline contract tests for vetted task CSVs and PNG extraction envelopes."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from integrations.task_artifacts import (
    ArtifactError,
    MAX_CSV_BYTES,
    MAX_FIGURE_BYTES,
    decode_figure_envelope,
    snapshot_task_csvs,
    validate_figure_png,
)


def make_png(*, size: tuple[int, int] = (24, 16)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (90, 140, 190)).save(buffer, format="PNG")
    return buffer.getvalue()


def make_envelope(raw: bytes) -> dict:
    return {
        "path": "figure.png",
        "encoding": "base64",
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "data_base64": base64.b64encode(raw).decode("ascii"),
    }


def write_task(root: Path, contents: dict[str, bytes],
               *, task_id: str = "demo") -> Path:
    directory = root / task_id
    directory.mkdir()
    inputs = directory / "inputs"
    inputs.mkdir()
    records = []
    for name, data in contents.items():
        (inputs / name).write_bytes(data)
        records.append({"name": name, "path": f"inputs/{name}"})
    descriptor = directory / "task.json"
    descriptor.write_text(json.dumps({
        "task_id": task_id,
        "task_class": "bar_chart",
        "instructions": "Plot a bar chart from data.csv",
        "inputs": records,
    }), encoding="utf-8")
    return descriptor


class TaskArtifactsOfflineTests(unittest.TestCase):
    def test_small_csv_snapshot_is_in_memory_and_manifest_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_bytes = b"category,value\nA,1\nB,2\n"
            descriptor = write_task(Path(tmp), {"data.csv": csv_bytes})
            snapshot = snapshot_task_csvs(descriptor)
            self.assertEqual(snapshot.task_id, "demo")
            self.assertEqual(snapshot.assets[0].data, csv_bytes)
            self.assertEqual(snapshot.assets[0].sha256,
                             hashlib.sha256(csv_bytes).hexdigest())
            manifest = snapshot.manifest()
            self.assertEqual(manifest["docker_builds"], 0)
            self.assertEqual(manifest["network_requests"], 0)
            self.assertEqual(manifest["files"][0]["target"],
                             "/opt/assignment/inputs/data.csv")
            self.assertNotIn("A,1", json.dumps(manifest))
            self.assertNotIn("A,1", repr(snapshot))

    def test_utf8_and_multiple_csv_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = write_task(Path(tmp), {
                "data.csv": "name,value\nCafé,1\n".encode("utf-8"),
                "more.csv": b"key,value\nx,2\n",
            })
            snapshot = snapshot_task_csvs(descriptor)
            self.assertEqual(snapshot.manifest()["file_count"], 2)
            self.assertEqual(len(snapshot.assets), 2)

    def test_rejects_empty_and_excessively_large_csv(self):
        for data in (b"", b"a" * (MAX_CSV_BYTES + 1)):
            with tempfile.TemporaryDirectory() as tmp:
                descriptor = write_task(Path(tmp), {"data.csv": data})
                with self.assertRaises(ArtifactError):
                    snapshot_task_csvs(descriptor)

    def test_rejects_too_many_files_and_total_input_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = write_task(Path(tmp), {
                f"input{i}.csv": b"a" for i in range(9)
            })
            with self.assertRaises(ArtifactError):
                snapshot_task_csvs(descriptor)
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = write_task(Path(tmp), {
                f"input{i}.csv": b"a" * 60000 for i in range(5)
            })
            with self.assertRaises(ArtifactError):
                snapshot_task_csvs(descriptor)

    def test_rejects_non_csv_nul_and_non_utf8_inputs(self):
        cases = {
            "wrong.txt": b"a,b\n1,2\n",
            "data.csv": b"abc\x00def",
        }
        for name, data in cases.items():
            with tempfile.TemporaryDirectory() as tmp:
                descriptor = write_task(Path(tmp), {name: data})
                with self.assertRaises(ArtifactError):
                    snapshot_task_csvs(descriptor)
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = write_task(Path(tmp), {"data.csv": b"\xff"})
            with self.assertRaises(ArtifactError):
                snapshot_task_csvs(descriptor)

    def test_symlink_files_and_parent_directories_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            descriptor = write_task(root, {"data.csv": b"k,v\na,1\n"})
            entry = root / "demo" / "inputs" / "data.csv"
            entry.rename(entry.with_name("orig.csv"))
            entry.symlink_to("orig.csv")
            with self.assertRaises(ArtifactError):
                snapshot_task_csvs(descriptor)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            descriptor = write_task(root, {"data.csv": b"k,v\na,1\n"})
            input_dir = root / "demo" / "inputs"
            input_dir.rename(root / "demo" / "original_inputs")
            input_dir.symlink_to("original_inputs", target_is_directory=True)
            with self.assertRaises(ArtifactError):
                snapshot_task_csvs(descriptor)

    def test_symlink_descriptor_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            descriptor = write_task(root, {"data.csv": b"x,y\n1,2\n"})
            alias = descriptor.with_name("alias.json")
            alias.symlink_to(descriptor.name)
            with self.assertRaises(ArtifactError):
                snapshot_task_csvs(alias)

    def test_png_validation_success_and_safe_metadata(self):
        png = make_png()
        figure = validate_figure_png(png)
        self.assertEqual((figure.width, figure.height), (24, 16))
        self.assertEqual(figure.data, png)
        self.assertEqual(figure.manifest()["size_bytes"], len(png))
        self.assertEqual(figure.manifest()["path"], "figure.png")
        self.assertNotIn(repr(png), repr(figure))

    def test_png_rejects_invalid_format_and_truncation(self):
        jpeg = io.BytesIO()
        Image.new("RGB", (24, 16)).save(jpeg, format="JPEG")
        for bad in (b"", b"not png", jpeg.getvalue(), make_png()[:28],
                    make_png() + b"trailing bytes" * (MAX_FIGURE_BYTES // 8)):
            with self.subTest(length=len(bad)), self.assertRaises(ArtifactError):
                validate_figure_png(bad)

    def test_png_rejects_excessive_pixel_count(self):
        oversized_dimensions = make_png(size=(2100, 2000))
        with self.assertRaises(ArtifactError):
            validate_figure_png(oversized_dimensions)

    def test_envelope_decodes_valid_png_without_host_writes(self):
        png = make_png()
        payload = make_envelope(png)
        decoded = decode_figure_envelope(json.dumps(payload))
        self.assertEqual(decoded.data, png)
        self.assertEqual(decoded.sha256, payload["sha256"])

    def test_envelope_rejects_path_traversal_and_extra_fields(self):
        png = make_png()
        for updates in (
            {"path": "../secret.png"},
            {"path": "/tmp/figure.png"},
            {"encoding": "raw"},
            {"unexpected": True},
        ):
            payload = {**make_envelope(png), **updates}
            with self.subTest(updates=updates), self.assertRaises(ArtifactError):
                decode_figure_envelope(json.dumps(payload))

    def test_envelope_rejects_length_hash_and_base64_mismatches(self):
        png = make_png()
        for updates in (
            {"size_bytes": len(png) + 1},
            {"size_bytes": True},
            {"sha256": "f" * 64},
            {"sha256": "garbage"},
            {"data_base64": "@@bad@@@"},
            {"data_base64": ""},
        ):
            payload = {**make_envelope(png), **updates}
            with self.subTest(updates=updates), self.assertRaises(ArtifactError):
                decode_figure_envelope(json.dumps(payload))

    def test_envelope_rejects_broken_json_and_unbounded_text(self):
        for raw in ("{}", "{bad json}", "x" * (2 * MAX_FIGURE_BYTES + 4000)):
            with self.subTest(length=len(raw)), self.assertRaises(ArtifactError):
                decode_figure_envelope(raw)


if __name__ == "__main__":
    unittest.main()
