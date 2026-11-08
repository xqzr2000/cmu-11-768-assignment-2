"""Session 013 host-only synthetic plot tests; no Docker or provider requests."""
from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations.task_artifacts import decode_figure_envelope, validate_figure_png
from scripts import chart_smoke_worker as smoke
from scripts.figure_extract_worker import read_figure


class ChartSmokeWorkerOfflineTests(unittest.TestCase):
    def test_constant_data_and_dimensions_are_fixed(self):
        self.assertEqual(smoke.CATEGORIES, ("Alpha", "Beta", "Gamma"))
        self.assertEqual(smoke.VALUES, (2, 5, 3))
        self.assertEqual((smoke.WIDTH_PX, smoke.HEIGHT_PX), (640, 480))
        self.assertEqual(smoke.FIGURE_PATH.as_posix(), "/workspace/figure.png")

    def test_rendered_png_passes_existing_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "figure.png"
            smoke.render_synthetic_chart(target)
            figure = validate_figure_png(target.read_bytes())
            self.assertEqual((figure.width, figure.height), (640, 480))
            self.assertTrue(0 < len(figure.data) < smoke.MAX_FIGURE_BYTES)

    def test_fixed_extractor_round_trips_without_gateway_output_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "figure.png"
            smoke.render_synthetic_chart(target)
            envelope = read_figure(target)
            recovered = decode_figure_envelope(envelope)
            self.assertEqual(recovered.data, target.read_bytes())
            self.assertEqual((recovered.width, recovered.height), (640, 480))

    def test_will_not_overwrite_existing_chart(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "figure.png"
            target.write_bytes(b"existing evidence")
            with self.assertRaises(FileExistsError):
                smoke.render_synthetic_chart(target)
            self.assertEqual(target.read_bytes(), b"existing evidence")

    def test_will_not_follow_symlinked_figure_or_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            target = parent / "figure.png"
            secret = parent / "unrelated.txt"
            secret.write_bytes(b"unchanged")
            target.symlink_to(secret)
            with self.assertRaises(FileExistsError):
                smoke.render_synthetic_chart(target)
            self.assertEqual(secret.read_bytes(), b"unchanged")
            alias = parent / "alias"
            alias.symlink_to(parent, target_is_directory=True)
            with self.assertRaises(ValueError):
                smoke.render_synthetic_chart(alias / "figure.png")

    def test_oversized_output_is_removed_before_error_returns(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "figure.png"
            with patch.object(smoke, "MAX_FIGURE_BYTES", 1):
                with self.assertRaisesRegex(ValueError, "oversized"):
                    smoke.render_synthetic_chart(target)
            self.assertFalse(target.exists())

    def test_main_rejects_args_and_uses_only_fixed_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "figure.png"
            with patch.object(smoke, "FIGURE_PATH", target):
                with patch.object(sys, "argv", ["chart_smoke_worker.py", "user.csv"]):
                    self.assertEqual(smoke.main(), 2)
                    self.assertFalse(target.exists())
                with patch.object(sys, "argv", ["chart_smoke_worker.py"]):
                    self.assertEqual(smoke.main(), 0)
                    self.assertEqual(smoke.main(), 1)  # No overwrite.

    def test_worker_has_no_docker_provider_shell_or_network_import(self):
        source = Path(smoke.__file__).read_text(encoding="utf-8")
        modules = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        self.assertEqual(modules, {"__future__", "os", "sys", "pathlib", "matplotlib"})


if __name__ == "__main__":
    unittest.main()
