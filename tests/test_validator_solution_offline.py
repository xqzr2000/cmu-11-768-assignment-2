"""Offline tests for the first, deterministic validator layer.

All runs here are synthetic. No seed labels, network calls, or model needed.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from validator.prediction import Error, ErrorFamily
from validator.runner import Run
from validator.solution import judge_execution, validate


class DeterministicExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_with(self, figure: Path | None) -> Run:
        return Run(
            run_id="synthetic",
            task_id="synthetic",
            instructions="Create a figure.",
            messages=[],
            figure=figure,
            inputs={},
        )

    def assert_execution_failure(self, errors: list[Error]) -> None:
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].family, ErrorFamily.EXECUTION_FAILURE)
        self.assertTrue(errors[0].evidence)

    def test_none_figure_is_terminal_without_calling_semantic_judges(self) -> None:
        run = self.run_with(None)
        with patch("validator.solution.judge_data_and_chart") as data_judge, patch(
            "validator.solution.judge_readability"
        ) as readability_judge:
            errors = validate(run)
        self.assert_execution_failure(errors)
        data_judge.assert_not_called()
        readability_judge.assert_not_called()

    def test_nonexistent_figure_path_is_execution_failure(self) -> None:
        errors = judge_execution(self.run_with(self.root / "missing.png"))
        self.assert_execution_failure(errors)
        self.assertIn("missing", errors[0].evidence)

    def test_directory_instead_of_file_is_execution_failure(self) -> None:
        errors = judge_execution(self.run_with(self.root))
        self.assert_execution_failure(errors)

    def test_garbage_png_bytes_are_execution_failure(self) -> None:
        figure = self.root / "figure.png"
        figure.write_bytes(b"not a real PNG")
        errors = judge_execution(self.run_with(figure))
        self.assert_execution_failure(errors)
        self.assertIn("decode", errors[0].evidence)

    def test_jpeg_renamed_to_png_is_execution_failure(self) -> None:
        figure = self.root / "figure.png"
        Image.new("RGB", (40, 20), "white").save(figure, format="JPEG")
        errors = judge_execution(self.run_with(figure))
        self.assert_execution_failure(errors)
        self.assertIn("JPEG", errors[0].evidence)

    def test_truncated_png_is_execution_failure(self) -> None:
        figure = self.root / "figure.png"
        Image.new("RGB", (40, 20), "white").save(figure, format="PNG")
        data = figure.read_bytes()
        figure.write_bytes(data[: len(data) // 2])
        self.assert_execution_failure(judge_execution(self.run_with(figure)))

    def test_valid_png_passes_structure_and_continues_to_semantic_judges(self) -> None:
        figure = self.root / "figure.png"
        # A plain white PNG decodes but is NOT necessarily a correct chart.
        Image.new("RGB", (40, 20), "white").save(figure, format="PNG")
        run = self.run_with(figure)
        self.assertEqual(judge_execution(run), [])
        data_error = Error(
            family=ErrorFamily.WRONG_DATA, evidence="Mock: wrong numbers."
        )
        with patch("validator.solution.judge_data_and_chart", return_value=[data_error]) as data, patch(
            "validator.solution.judge_readability", return_value=[]
        ) as readability:
            errors = validate(run)
        self.assertEqual(errors, [data_error])
        data.assert_called_once_with(run)
        readability.assert_called_once_with(run)


if __name__ == "__main__":
    unittest.main()
