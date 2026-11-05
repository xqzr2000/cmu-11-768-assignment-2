"""Offline structural preflight tests; no network, GPU, or model usage."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.offline_preflight import DatasetError, inspect_dataset


class OfflinePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        task_dir = self.root / "artifacts" / "demo"
        task_dir.mkdir(parents=True)
        (task_dir / "result.json").write_text(
            json.dumps({
                "run_id": "demo",
                "task_id": "demo",
                "task": {"instructions": "Create a chart", "inputs": []},
                "trajectory": {"messages": [{"role": "user", "content": "Create a chart"}]},
            })
        )
        self.label_path = self.root / "seed_labels.json"
        self.write_labels([{"run_id": "demo", "errors": []}])

    def write_labels(self, entries: list[dict]) -> None:
        self.label_path.write_text(json.dumps({"labels": entries}))

    def test_valid_run_and_label(self) -> None:
        summary = inspect_dataset(self.root)
        self.assertEqual(summary["runs"], 1)
        self.assertEqual(summary["acceptable"], 1)
        self.assertEqual(summary["figures"], 0)

    def test_missing_label_fails(self) -> None:
        self.write_labels([])
        with self.assertRaisesRegex(DatasetError, "coverage mismatch"):
            inspect_dataset(self.root)

    def test_duplicate_label_fails(self) -> None:
        self.write_labels([
            {"run_id": "demo", "errors": []},
            {"run_id": "demo", "errors": []},
        ])
        with self.assertRaisesRegex(DatasetError, "duplicate label"):
            inspect_dataset(self.root)

    def test_terminal_execution_failure_cannot_cooccur(self) -> None:
        self.write_labels([{
            "run_id": "demo",
            "errors": [
                {"family": "execution_failure", "evidence": "No chart"},
                {"family": "wrong_chart", "evidence": "Wrong axes"},
            ],
        }])
        with self.assertRaisesRegex(DatasetError, "terminal"):
            inspect_dataset(self.root)

    def test_rejects_invalid_png(self) -> None:
        (self.root / "artifacts" / "demo" / "figure.png").write_bytes(b"not a PNG")
        with self.assertRaisesRegex(DatasetError, "PNG"):
            inspect_dataset(self.root)


if __name__ == "__main__":
    unittest.main()
