"""No-network tests for the strictly bounded two-case Z.ai seed pilot."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image

from scripts import zai_seed_pilot as pilot
from validator.prediction import Error, ErrorFamily, Prediction, PredictionFile
from validator.runner import Run


def fake_response(answer: str):
    payload = {"choices": [{"message": {"content": answer}}]}
    return SimpleNamespace(
        model=pilot.MODEL,
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=15, total_tokens=115),
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer))],
        model_dump=lambda: payload,
    )


class SeedPilotOfflineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.figure = self.root / "figure.png"
        Image.new("RGB", (48, 40), "white").save(self.figure, format="PNG")
        self.csv = self.root / "small.csv"
        self.csv.write_text("fruit,count\napple,1\norange,2\n", encoding="utf-8")

    def run_case(self, run_id="004"):
        return Run(
            run_id=run_id,
            task_id="synthetic",
            instructions="Make a labeled chart from the input data.",
            messages=[{"role": "assistant", "content": "Plotting sample data."}],
            figure=self.figure,
            inputs={"small.csv": self.csv},
        )

    def test_offline_preview_uses_real_solution_with_mock_completion(self):
        info = pilot.describe_case(self.run_case())
        self.assertEqual(info["mode"], "offline_preview")
        self.assertEqual(info["network_requests"], 0)
        self.assertEqual(info["planned_completion_requests"], 3)
        self.assertFalse(info["human_labels_sent"])
        self.assertEqual(info["figure_dimensions"], [48, 40])
        self.assertEqual(len(info["requests"]), 3)
        self.assertTrue(all(r["image_bytes"] == self.figure.stat().st_size for r in info["requests"]))
        self.assertTrue(all(r["prompt_chars"] > 50 for r in info["requests"]))

    def test_main_defaults_to_two_case_zero_request_preview(self):
        output = io.StringIO()
        with patch.object(pilot, "load_case", side_effect=lambda rid: self.run_case(rid)), patch.object(
            pilot, "OpenAI"
        ) as factory:
            with redirect_stdout(output):
                result = pilot.main([])
        self.assertEqual(result, 0)
        factory.assert_not_called()
        data = json.loads(output.getvalue())
        self.assertEqual(set(data["plans"]), {"004", "008"})
        self.assertEqual({p["network_requests"] for p in data["plans"].values()}, {0})

    def test_live_requires_both_flags_and_exact_run(self):
        for args in (
            ["--live", "--run-id", "004"],
            ["--confirm-three-requests", "--run-id", "004"],
            ["--live", "--confirm-three-requests"],
            ["--compare"],
            ["--compare", "--run-id", "004", "--live", "--confirm-three-requests"],
        ):
            with self.subTest(args=args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    pilot.main(args)
                self.assertEqual(caught.exception.code, 2)

    def test_live_without_key_never_constructs_client(self):
        out = io.StringIO()
        with patch.object(pilot, "load_case", return_value=self.run_case()), patch.object(
            pilot, "load_dotenv"
        ), patch.dict(os.environ, {"ZAI_API_KEY": ""}), patch.object(pilot, "OpenAI") as factory, patch.object(
            pilot, "prediction_path", return_value=self.root / "not-there.json"
        ), patch.object(pilot, "metadata_path", return_value=self.root / "not-there-meta.json"):
            with redirect_stdout(out):
                result = pilot.main(["--live", "--confirm-three-requests", "--run-id", "004"])
        self.assertEqual(result, 2)
        factory.assert_not_called()
        self.assertIn("not configured", out.getvalue())

    def test_live_calls_exactly_three_and_writes_only_new_output(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            fake_response("YES: Missing requested orange series."),
            fake_response("NO: Chart layout matches."),
            fake_response("YES: Low contrast labels."),
        ]
        out = io.StringIO()
        saved = []
        # The mock output paths live outside the real checkout; point ROOT at
        # that same temporary directory so relative-path reporting is realistic.
        with patch.object(pilot, "ROOT", self.root), patch.object(
            pilot, "load_case", return_value=self.run_case()
        ), patch.object(
            pilot, "load_dotenv"
        ), patch.dict(os.environ, {"ZAI_API_KEY": "test-placeholder"}), patch.object(
            pilot, "OpenAI", return_value=mock_client
        ) as factory, patch.object(
            pilot, "prediction_path", return_value=self.root / "output" / "p.json"
        ), patch.object(
            pilot, "metadata_path", return_value=self.root / "output" / "m.json"
        ), patch.object(
            pilot, "write_one_run", side_effect=lambda run_id, pred, meta: saved.append(
                (run_id, pred, meta)
            )
        ):
            with redirect_stdout(out):
                result = pilot.main(["--live", "--confirm-three-requests", "--run-id", "004"])
        self.assertEqual(result, 0)
        self.assertEqual(factory.call_args.kwargs["base_url"], pilot.BASE_URL)
        self.assertEqual(factory.call_args.kwargs["max_retries"], 0)
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)
        self.assertEqual(len(saved), 1)
        rid, prediction, metadata = saved[0]
        self.assertEqual(rid, "004")
        self.assertEqual(
            [error.family for error in prediction.errors],
            [ErrorFamily.WRONG_DATA, ErrorFamily.HARD_TO_READ],
        )
        self.assertFalse(metadata["human_labels_sent"])
        self.assertEqual(metadata["completion_attempts"], 3)
        for call in mock_client.chat.completions.create.call_args_list:
            kwargs = call.kwargs
            self.assertEqual(kwargs["model"], "glm-4.6v-flash")
            self.assertEqual(kwargs["max_tokens"], pilot.MAX_OUTPUT_TOKENS)
            self.assertEqual(kwargs["extra_body"]["thinking"]["type"], "disabled")
            parts = kwargs["messages"][0]["content"]
            self.assertEqual([p["type"] for p in parts], ["text", "image_url"])
            self.assertIn("orange,2", parts[0]["text"])

    def test_completion_budget_cannot_be_exceeded(self):
        client = MagicMock()
        client.chat.completions.create.return_value = fake_response("NO: No issue.")
        with self.assertRaisesRegex(RuntimeError, "budget exhausted"):
            pilot.send_one_run(self.run_case(), client, max_completions=2)
        self.assertEqual(client.chat.completions.create.call_count, 2)

    def test_ambiguous_answer_does_not_become_false_acceptable(self):
        client = MagicMock()
        client.chat.completions.create.return_value = fake_response("Maybe there is a problem.")
        with self.assertRaisesRegex(ValueError, "YES or NO"):
            pilot.send_one_run(self.run_case(), client)
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_transport_failure_is_not_retried(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("secret request body")
        with self.assertRaisesRegex(RuntimeError, "secret request body"):
            pilot.send_one_run(self.run_case(), client)
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_existing_prediction_blocks_future_live_requests(self):
        exists = self.root / "output" / "p.json"
        exists.parent.mkdir(parents=True, exist_ok=True)
        exists.write_text("{}")
        out = io.StringIO()
        with patch.object(pilot, "load_case", return_value=self.run_case()), patch.object(
            pilot, "prediction_path", return_value=exists
        ), patch.object(
            pilot, "metadata_path", return_value=self.root / "output" / "m.json"
        ), patch.object(pilot, "OpenAI") as factory:
            with redirect_stdout(out):
                result = pilot.main(["--live", "--confirm-three-requests", "--run-id", "004"])
        self.assertEqual(result, 2)
        factory.assert_not_called()
        self.assertIn("Existing output", out.getvalue())

    def test_output_and_label_comparison_are_strictly_separate(self):
        predicted = Prediction(
            run_id="004",
            errors=[Error(family=ErrorFamily.WRONG_CHART, evidence="Wrong axis.")],
        )
        pilot.write_one_run("004", predicted, {"pilot_only": True}, root=self.root)
        self.assertTrue(pilot.prediction_path("004", self.root).is_file())
        with self.assertRaises(FileExistsError):
            pilot.write_one_run("004", predicted, {"pilot_only": True}, root=self.root)
        (self.root / "seed_labels.json").write_text(json.dumps({
            "labels": [{
                "run_id": "004",
                "errors": [{"family": "wrong_data", "evidence": "Incorrect values."}],
            }]
        }))
        report = pilot.compare_one_run("004", root=self.root)
        self.assertEqual(report["predicted_families"], ["wrong_chart"])
        self.assertEqual(report["human_families"], ["wrong_data"])
        self.assertEqual(report["false_alarms"], ["wrong_chart"])
        self.assertEqual(report["missed"], ["wrong_data"])
        self.assertFalse(report["official_qwen_equivalent"])


if __name__ == "__main__":
    unittest.main()
