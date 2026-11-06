"""Offline tests of semantic-validator wiring with a mocked model response.

No network, vision model, seed labels, or private task ID lookups are used.
These test plumbing and schema only; they do not measure semantic accuracy.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from validator.prediction import ErrorFamily, Prediction, PredictionFile
from validator.runner import Run
from validator.solution import validate


class SemanticIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.figure = self.root / "figure.png"
        Image.new("RGB", (50, 40), "white").save(self.figure, format="PNG")
        self.csv = self.root / "samples.csv"
        self.csv.write_text("group,value\napple,5\norange,8\n")

    def sample_run(self, figure: Path | None = None) -> Run:
        return Run(
            run_id="synthetic",
            task_id="synthetic",
            instructions="Plot the values in samples.csv, with labels and legend.",
            messages=[
                {"role": "user", "content": "Please draw the chart."},
                {"role": "tool", "content": "source != 'orange'"},
            ],
            figure=self.figure if figure is None else figure,
            inputs={"samples.csv": self.csv},
        )

    @staticmethod
    def reply(text: str) -> dict:
        return {"choices": [{"message": {"content": text}}]}

    def test_three_semantic_requests_contain_task_csv_trajectory_and_png(self) -> None:
        calls = []
        answers = iter([
            "YES: Requested orange series was omitted.",
            "NO: Chart design follows the requested layout.",
            "YES: Labels have insufficient contrast.",
        ])

        def fake_complete(messages, **kwargs):
            calls.append((messages, kwargs))
            return self.reply(next(answers))

        with patch("validator.baseline.complete", side_effect=fake_complete):
            errors = validate(self.sample_run())

        self.assertEqual([error.family for error in errors], [
            ErrorFamily.WRONG_DATA,
            ErrorFamily.HARD_TO_READ,
        ])
        self.assertEqual(errors[0].evidence, "Requested orange series was omitted.")
        self.assertEqual(errors[1].evidence, "Labels have insufficient contrast.")
        self.assertEqual(len(calls), 3)

        questions = [
            "Does the plotted data differ",
            "Does the figure fail to follow",
            "Is the rendered figure difficult",
        ]
        for (messages, kwargs), question in zip(calls, questions, strict=True):
            self.assertEqual(kwargs["max_tokens"], 250)
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["role"], "user")
            parts = messages[0]["content"]
            self.assertEqual([part["type"] for part in parts], ["text", "image_url"])
            prompt = parts[0]["text"]
            self.assertTrue(prompt.startswith(question))
            self.assertIn("samples.csv", prompt)
            self.assertIn("orange,8", prompt)
            self.assertIn("source != 'orange'", prompt)
            self.assertIn("Plot the values", prompt)
            self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))

        serialized = PredictionFile(
            predictions=[Prediction(run_id="synthetic", errors=errors)]
        ).model_dump(mode="json")
        self.assertEqual([error["family"] for error in serialized["predictions"][0]["errors"]],
                         ["wrong_data", "hard_to_read"])

    def test_all_no_responses_return_empty_list(self) -> None:
        with patch("validator.baseline.complete", return_value=self.reply("NO: Looks correct.")) as mock:
            errors = validate(self.sample_run())
        self.assertEqual(errors, [])
        self.assertEqual(mock.call_count, 3)

    def test_three_yes_responses_return_all_nonterminal_families(self) -> None:
        with patch("validator.baseline.complete", return_value=self.reply("YES: An issue is present.")) as mock:
            errors = validate(self.sample_run())
        self.assertEqual(
            [error.family for error in errors],
            [ErrorFamily.WRONG_DATA, ErrorFamily.WRONG_CHART, ErrorFamily.HARD_TO_READ],
        )
        self.assertEqual(mock.call_count, 3)

    def test_missing_figure_short_circuits_without_model_calls(self) -> None:
        run = self.sample_run()
        run = Run(
            run_id=run.run_id,
            task_id=run.task_id,
            instructions=run.instructions,
            messages=run.messages,
            figure=None,
            inputs=run.inputs,
        )
        with patch("validator.baseline.complete") as mock:
            errors = validate(run)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].family, ErrorFamily.EXECUTION_FAILURE)
        mock.assert_not_called()

    def test_corrupt_figure_short_circuits_without_model_calls(self) -> None:
        self.figure.write_bytes(b"not png bytes")
        with patch("validator.baseline.complete") as mock:
            errors = validate(self.sample_run())
        self.assertEqual([error.family for error in errors], [ErrorFamily.EXECUTION_FAILURE])
        mock.assert_not_called()

    def test_model_errors_are_not_misreported_as_acceptable(self) -> None:
        with patch("validator.baseline.complete", side_effect=RuntimeError("model unavailable")) as mock:
            with self.assertRaisesRegex(RuntimeError, "model unavailable"):
                validate(self.sample_run())
        self.assertEqual(mock.call_count, 1)

    def test_unexpected_model_response_is_not_silently_ignored(self) -> None:
        with patch("validator.baseline.complete", return_value={"choices": []}):
            with self.assertRaises(IndexError):
                validate(self.sample_run())


if __name__ == "__main__":
    unittest.main()
