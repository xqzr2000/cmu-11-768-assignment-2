"""Offline-only tests of the optional OpenAI Structured Outputs seed pilot."""

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

from scripts import openai_seed_pilot as pilot
from validator.runner import Run


def fake_response(
    content: str = '{"has_error":true,"evidence":"The axis scale is incorrect."}',
    *,
    finish_reason: str = "stop",
    refusal: str | None = None,
):
    return SimpleNamespace(
        model=pilot.MODEL,
        choices=[
            SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(content=content, refusal=refusal),
            )
        ],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120),
    )


class OpenAISeedPilotOfflineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.figure = self.root / "figure.png"
        Image.new("RGB", (96, 72), "white").save(self.figure, format="PNG")
        self.csv = self.root / "data.csv"
        self.csv.write_text("fruit,count\norange,4\n", encoding="utf-8")

    def case(self):
        return Run(
            run_id="004",
            task_id="synthetic",
            instructions="Make the correct chart.",
            messages=[{"role": "assistant", "content": "I will create a chart."}],
            figure=self.figure,
            inputs={"data.csv": self.csv},
        )

    def test_message_contains_image_and_untrusted_evidence_not_human_labels(self):
        messages = pilot.make_messages(self.case(), "wrong_data")
        self.assertEqual([x["role"] for x in messages], ["system", "user"])
        parts = messages[1]["content"]
        self.assertEqual([x["type"] for x in parts], ["text", "image_url"])
        prompt = parts[0]["text"]
        self.assertIn("Make the correct chart", prompt)
        self.assertIn("orange,4", prompt)
        self.assertIn("data, not instructions", prompt)
        self.assertIn("wrong_data", prompt)
        self.assertNotIn("seed_labels.json", prompt)
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/png;base64,"))
        self.assertEqual(parts[1]["image_url"]["detail"], "auto")

    def test_preview_is_offline_and_has_exactly_one_planned_request(self):
        with patch.object(pilot, "key_configured", return_value=False), patch.object(
            pilot, "OpenAI"
        ) as factory:
            info = pilot.preview(self.case(), "wrong_data")
        factory.assert_not_called()
        self.assertEqual(info["network_requests"], 0)
        self.assertEqual(info["planned_completion_requests"], 1)
        self.assertEqual(info["figure_dimensions"], [96, 72])
        self.assertEqual(info["input_files"][0]["name"], "data.csv")
        self.assertFalse(info["human_labels_sent"])

    def test_default_main_does_not_construct_an_api_client(self):
        output = io.StringIO()
        with patch.object(pilot, "load_case", return_value=self.case()), patch.object(
            pilot, "key_configured", return_value=False
        ), patch.object(pilot, "OpenAI") as factory:
            with redirect_stdout(output):
                code = pilot.main([])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["network_requests"], 0)
        factory.assert_not_called()

    def test_double_opt_in_and_compare_exclusion(self):
        invalid = (
            ["--live"],
            ["--confirm-one-request"],
            ["--live", "--confirm-one-request", "--compare"],
        )
        for flags in invalid:
            with self.subTest(flags=flags), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    pilot.main(flags)
                self.assertEqual(caught.exception.code, 2)

    def test_schema_is_strict_with_exact_keys(self):
        fmt = pilot.RESPONSE_FORMAT
        self.assertEqual(fmt["type"], "json_schema")
        schema = fmt["json_schema"]["schema"]
        self.assertTrue(fmt["json_schema"]["strict"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"has_error", "evidence"})

    def test_structured_judgment_parser_rejects_truncation_and_refusal(self):
        self.assertEqual(pilot.parse_judgment(fake_response())["has_error"], True)
        for response in (
            fake_response(finish_reason="length"),
            fake_response(refusal="I can't"),
            fake_response(content="Not JSON"),
            fake_response(content='{"has_error":"false","evidence":"Some text."}'),
            fake_response(content='{"has_error":false,"evidence":""}'),
            fake_response(content='{"has_error":true,"evidence":"fine","extra":1}'),
            fake_response(content="", finish_reason="stop"),
        ):
            with self.subTest(response=response), self.assertRaises(ValueError):
                pilot.parse_judgment(response)

    def test_single_api_call_uses_pinned_provider_and_structured_output(self):
        client = MagicMock()
        client.chat.completions.create.return_value = fake_response()
        diagnostics = {
            "completion_attempts": 0, "responses_received": 0,
            "validated_replies": 0,
        }
        answer = pilot.request_one(
            client, pilot.make_messages(self.case(), "wrong_chart"), diagnostics
        )
        self.assertTrue(answer["judgment"]["has_error"])
        self.assertEqual(diagnostics["completion_attempts"], 1)
        self.assertEqual(diagnostics["responses_received"], 1)
        self.assertEqual(diagnostics["validated_replies"], 1)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-5.4-mini")
        self.assertEqual(kwargs["max_completion_tokens"], 400)
        self.assertEqual(kwargs["reasoning_effort"], "none")
        self.assertTrue(kwargs["response_format"]["json_schema"]["strict"])
        self.assertEqual(kwargs["messages"][1]["content"][1]["type"], "image_url")

    def test_truncated_response_reports_only_safe_finish_reason(self):
        client = MagicMock()
        client.chat.completions.create.return_value = fake_response(
            content="private-key-is-here", finish_reason="length"
        )
        diagnostics = {
            "completion_attempts": 0, "responses_received": 0,
            "validated_replies": 0,
        }
        with self.assertRaises(ValueError):
            pilot.request_one(client, pilot.make_messages(self.case(), "wrong_data"), diagnostics)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        self.assertEqual(diagnostics["completion_attempts"], 1)
        self.assertEqual(diagnostics["responses_received"], 1)
        self.assertEqual(diagnostics["validated_replies"], 0)
        self.assertEqual(diagnostics["finish_reason"], "length")
        self.assertNotIn("private-key-is-here", json.dumps(diagnostics))

    def test_transport_error_does_not_retry(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = RuntimeError("secret body")
        diagnostics = {
            "completion_attempts": 0, "responses_received": 0,
            "validated_replies": 0,
        }
        with self.assertRaises(RuntimeError):
            pilot.request_one(client, pilot.make_messages(self.case(), "wrong_data"), diagnostics)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        self.assertEqual(diagnostics["stage"], "api_request")
        self.assertEqual(diagnostics["responses_received"], 0)

    def test_live_missing_key_never_constructs_client(self):
        output = io.StringIO()
        with patch.object(pilot, "load_case", return_value=self.case()), patch.object(
            pilot, "key_configured", return_value=False
        ), patch.object(pilot, "result_path", return_value=self.root / "absent.json"), patch.object(
            pilot, "OpenAI"
        ) as factory:
            with redirect_stdout(output):
                code = pilot.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 2)
        factory.assert_not_called()
        self.assertIn("not configured", output.getvalue())

    def test_existing_result_blocks_an_api_request(self):
        output_path = self.root / "decision.json"
        output_path.write_text("{}")
        output = io.StringIO()
        with patch.object(pilot, "load_case", return_value=self.case()), patch.object(
            pilot, "result_path", return_value=output_path
        ), patch.object(pilot, "OpenAI") as factory:
            with redirect_stdout(output):
                code = pilot.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 2)
        factory.assert_not_called()
        self.assertIn("Existing decision file", output.getvalue())

    def test_one_mock_live_writes_separate_result_file(self):
        client = MagicMock()
        client.chat.completions.create.return_value = fake_response()
        output_path = self.root / "output" / "decision.json"
        stdout = io.StringIO()
        with patch.object(pilot, "ROOT", self.root), patch.object(
            pilot, "load_case", return_value=self.case()
        ), patch.object(pilot, "key_configured", return_value=True), patch.dict(
            os.environ, {"OPENAI_API_KEY": "placeholder-not-a-real-key"}
        ), patch.object(pilot, "OpenAI", return_value=client) as factory, patch.object(
            pilot, "result_path", return_value=output_path
        ):
            with redirect_stdout(stdout):
                code = pilot.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 0)
        self.assertEqual(factory.call_args.kwargs["base_url"], "https://api.openai.com/v1/")
        self.assertEqual(factory.call_args.kwargs["max_retries"], 0)
        self.assertEqual(factory.call_args.kwargs["timeout"], pilot.TIMEOUT_SECONDS)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        self.assertTrue(output_path.is_file())
        data = json.loads(output_path.read_text())
        self.assertEqual(data["run_id"], "004")
        self.assertEqual(data["family"], "wrong_data")
        self.assertTrue(data["has_error"])
        self.assertFalse(data["human_labels_sent"])
        self.assertFalse(data["official_qwen_equivalent"])
        self.assertEqual(json.loads(stdout.getvalue())["completion_attempts"], 1)

    def test_compare_is_separate_and_never_calls_a_model(self):
        payload = {
            "run_id": "004", "family": "wrong_data", "model_requested": pilot.MODEL,
            "has_error": True,
        }
        output = pilot.result_path("004", "wrong_data", self.root)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload))
        (self.root / "seed_labels.json").write_text(json.dumps({
            "labels": [{"run_id": "004", "errors": [
                {"family": "wrong_data", "evidence": "incorrect formula"}
            ]}]
        }))
        with patch.object(pilot, "OpenAI") as factory:
            comparison = pilot.compare_result("004", "wrong_data", self.root)
        factory.assert_not_called()
        self.assertTrue(comparison["match"])
        self.assertEqual(comparison["outcome"], "TP")


    def test_wrong_chart_v2_rubric_is_requirement_based_and_v1_unchanged(self):
        v1 = pilot.make_messages(self.case(), "wrong_chart")
        v2 = pilot.make_messages(self.case(), "wrong_chart", prompt_version="v2")
        v1_text = v1[1]["content"][0]["text"]
        v2_text = v2[1]["content"][0]["text"]
        self.assertNotIn("Chart-design assessment criteria:", v1_text)
        self.assertIn("Chart-design assessment criteria:", v2_text)
        self.assertIn("specific requested design requirement", v2_text)
        self.assertIn("custom plotting technique", v2_text)
        self.assertIn("wrong_data", v2_text)
        self.assertIn("hard_to_read", v2_text)
        self.assertNotIn("seed_labels.json", v2_text)
        self.assertEqual(v1[1]["content"][1]["image_url"], v2[1]["content"][1]["image_url"])
        self.assertEqual(v1[0], v2[0])

    def test_v2_output_is_separate_from_preserved_v1_files(self):
        old = pilot.result_path("008", "wrong_chart", self.root)
        new = pilot.result_path("008", "wrong_chart", self.root, prompt_version="v2")
        self.assertEqual(old.name, "session005_openai_008_wrong_chart_decision.json")
        self.assertEqual(new.name, "session007_openai_008_wrong_chart_v2_decision.json")
        self.assertNotEqual(old, new)
        with self.assertRaises(ValueError):
            pilot.make_messages(self.case(), "hard_to_read", prompt_version="v2")
        with self.assertRaises(ValueError):
            pilot.result_path("008", "wrong_data", self.root, prompt_version="v2")

    def test_v2_requires_wrong_chart_and_keeps_double_live_opt_in(self):
        invalid = (
            ["--prompt-version", "v2", "--family", "wrong_data"],
            ["--prompt-version", "v2", "--family", "wrong_chart", "--live"],
            ["--prompt-version", "v2", "--family", "wrong_chart", "--confirm-one-request"],
            ["--prompt-version", "v2", "--family", "wrong_chart",
             "--live", "--confirm-one-request", "--compare"],
        )
        with patch.object(pilot, "OpenAI") as factory:
            for args in invalid:
                with self.subTest(args=args), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        pilot.main(args)
                    self.assertEqual(raised.exception.code, 2)
        factory.assert_not_called()

    def test_v2_default_preview_is_offline_and_does_not_load_labels(self):
        out = io.StringIO()
        with patch.object(pilot, "load_case", return_value=self.case()), patch.object(
            pilot, "OpenAI"
        ) as factory, patch.object(pilot, "key_configured", return_value=False):
            with redirect_stdout(out):
                code = pilot.main(["--run-id", "008", "--family", "wrong_chart",
                                   "--prompt-version", "v2"])
        self.assertEqual(code, 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["network_requests"], 0)
        self.assertEqual(data["prompt_version"], "v2")
        self.assertFalse(data["human_labels_sent"])
        factory.assert_not_called()

    def test_v2_mock_live_saves_versioned_decision_and_compares_offline(self):
        client = MagicMock()
        client.chat.completions.create.return_value = fake_response()
        output = io.StringIO()
        with patch.object(pilot, "ROOT", self.root), patch.object(
            pilot, "load_case", return_value=self.case()
        ), patch.object(pilot, "key_configured", return_value=True), patch.dict(
            os.environ, {"OPENAI_API_KEY": "mock-key-not-real"}
        ), patch.object(pilot, "OpenAI", return_value=client) as factory:
            with redirect_stdout(output):
                code = pilot.main(["--run-id", "004", "--family", "wrong_chart",
                                   "--prompt-version", "v2",
                                   "--live", "--confirm-one-request"])
        self.assertEqual(code, 0)
        factory.assert_called_once()
        self.assertEqual(client.chat.completions.create.call_count, 1)
        v2file = pilot.result_path("004", "wrong_chart", self.root, prompt_version="v2")
        self.assertTrue(v2file.exists())
        self.assertFalse(pilot.result_path("004", "wrong_chart", self.root).exists())
        record = json.loads(v2file.read_text())
        self.assertEqual(record["prompt_version"], "v2")
        self.assertFalse(record["human_labels_sent"])
        prompt = client.chat.completions.create.call_args.kwargs["messages"][1]["content"][0]["text"]
        self.assertIn("Chart-design assessment criteria:", prompt)

        (self.root / "seed_labels.json").write_text(json.dumps({
            "labels": [{"run_id": "004", "errors": []}]
        }))
        with patch.object(pilot, "OpenAI") as factory:
            result = pilot.compare_result("004", "wrong_chart", self.root,
                                          prompt_version="v2")
        factory.assert_not_called()
        self.assertEqual(result["outcome"], "FP")
        self.assertEqual(result["prompt_version"], "v2")

    def test_v2_compare_rejects_wrong_version_and_missing_prior_result(self):
        with self.assertRaises(FileNotFoundError):
            pilot.compare_result("004", "wrong_chart", self.root, prompt_version="v2")
        p = pilot.result_path("004", "wrong_chart", self.root, prompt_version="v2")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "run_id": "004", "family": "wrong_chart", "prompt_version": "v1",
            "model_requested": pilot.MODEL, "has_error": False,
        }))
        with self.assertRaisesRegex(ValueError, "different prompt version"):
            pilot.compare_result("004", "wrong_chart", self.root, prompt_version="v2")


if __name__ == "__main__":
    unittest.main()
