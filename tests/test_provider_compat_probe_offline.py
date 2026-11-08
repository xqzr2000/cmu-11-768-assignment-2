"""Offline-only tests for Session 009's one-request compatibility probe CLI."""

from __future__ import annotations

import base64
import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from integrations.judge import JUDGMENT_SCHEMA
from integrations.models import MODELS, get_model
from integrations.providers.base import NormalizedReply, ToolCall
from scripts import provider_compat_probe as probe


def _mock_reply(role: str) -> NormalizedReply:
    spec = get_model(role)
    calls = () if spec.is_judge else (
        ToolCall("call_mock", "run_shell", {"command": "printf session009"}),
    )
    return NormalizedReply(
        role=role,
        requested_model=spec.model_id,
        reported_model=spec.model_id,
        text='{"errors":[]}' if spec.is_judge else "",
        tool_calls=calls,
        input_tokens=12, output_tokens=6, total_tokens=18,
        continuation_items=(),
    )


class ProviderCompatibilityProbeOfflineTests(unittest.TestCase):
    def _main(self, *args: str) -> dict:
        with io.StringIO() as buffer, redirect_stdout(buffer):
            probe.main(list(args))
            return json.loads(buffer.getvalue())

    def test_four_registered_roles_have_pure_synthetic_cases(self):
        for role, spec in MODELS.items():
            with self.subTest(role=role):
                items, tools, schema = probe.build_case(spec)
                self.assertEqual(len(items), 1)
                if spec.is_judge:
                    self.assertEqual(schema, JUDGMENT_SCHEMA)
                    self.assertEqual(tools, [])
                    self.assertEqual(items[0]["content"][1]["type"], "input_image")
                    base64.b64decode(items[0]["content"][1]["image_url"].split(",", 1)[1])
                else:
                    self.assertIsNone(schema)
                    self.assertEqual([tool["name"] for tool in tools], ["run_shell"])
                    self.assertIn("function-calling compatibility", items[0]["content"])
                self.assertNotIn("seed_labels", json.dumps(items))

    def test_default_preview_makes_zero_network_calls(self):
        with patch.object(probe, "execute_one") as execute:
            for role, spec in MODELS.items():
                with self.subTest(role=role):
                    result = self._main("--role", role)
                    self.assertEqual(result["mode"], "offline")
                    self.assertEqual(result["network_requests"], 0)
                    self.assertEqual(result["model_requested"], spec.model_id)
                    self.assertTrue(result["live_approval_required"])
                    self.assertNotIn("image_url", result)
                    self.assertNotIn("printf session009", result)
            execute.assert_not_called()

    def test_partial_consent_is_not_sufficient(self):
        with patch.object(probe, "execute_one") as execute, redirect_stderr(io.StringIO()):
            for args in (
                ("--role", "agent_a", "--live"),
                ("--role", "agent_a", "--confirm-one-request"),
                ("--role", "agent_a", "--approve-model", "deepseek-flash"),
                ("--role", "agent_a", "--live", "--confirm-one-request"),
                ("--role", "agent_a", "--live", "--confirm-one-request",
                 "--approve-model", "wrong-model"),
            ):
                with self.subTest(args=args), self.assertRaises(SystemExit):
                    probe.main(list(args))
            execute.assert_not_called()

    def test_missing_secret_blocks_before_api_client(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            probe, "RELEASE", Path(tmp)
        ), patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}), patch.object(
            probe, "execute_one"
        ) as execute, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                probe.main(["--role", "agent_a", "--live",
                            "--confirm-one-request", "--approve-model", "deepseek-flash"])
            execute.assert_not_called()

    def test_each_model_mock_call_writes_minimal_ignored_result(self):
        for role, spec in MODELS.items():
            with self.subTest(role=role), tempfile.TemporaryDirectory() as tmp, patch.object(
                probe, "RELEASE", Path(tmp)
            ), patch.dict(os.environ, {spec.key_env: "fake-key"}), patch.object(
                probe, "execute_one", return_value=_mock_reply(role)
            ) as execute:
                output = self._main("--role", role, "--live",
                                    "--confirm-one-request", "--approve-model", spec.model_id)
                self.assertEqual(execute.call_count, 1)
                self.assertEqual(output["status"], "completed")
                self.assertEqual(output["requested_model"], spec.model_id)
                self.assertEqual(output["retries"], 0)
                self.assertEqual(output["model_proposed_commands_executed"], 0)
                saved = probe.result_path(spec)
                self.assertTrue(saved.is_file())
                record = json.loads(saved.read_text())
                self.assertEqual(record["usage"]["total_tokens"], 18)
                self.assertNotIn("fake-key", saved.read_text())
                self.assertNotIn("printf session009", saved.read_text())
                self.assertNotIn("image_url", saved.read_text())
                if spec.is_judge:
                    self.assertTrue(record["schema_valid"])
                    self.assertFalse(record["accuracy_evaluated"])
                else:
                    self.assertTrue(record["tool_call_compatibility"])
                if os.name == "posix":
                    self.assertEqual(stat.S_IMODE(saved.stat().st_mode), 0o600)

    def test_saved_result_blocks_second_approved_request(self):
        role = "agent_a"
        spec = get_model(role)
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            probe, "RELEASE", Path(tmp)
        ), patch.dict(os.environ, {spec.key_env: "fake-key"}), patch.object(
            probe, "execute_one", return_value=_mock_reply(role)
        ) as execute:
            args = ["--role", role, "--live", "--confirm-one-request",
                    "--approve-model", spec.model_id]
            self._main(*args)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                probe.main(args)
            self.assertEqual(execute.call_count, 1)

    def test_legacy_old_model_error_does_not_block_new_agent_c(self):
        role = "agent_c"
        spec = get_model(role)
        self.assertEqual(spec.model_id, "glm-5.3-flash")
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            probe, "RELEASE", Path(tmp)
        ), patch.dict(os.environ, {spec.key_env: "fake-key"}), patch.object(
            probe, "execute_one", return_value=_mock_reply(role)
        ) as execute:
            previous = Path(tmp) / "output" / "provider_compat_agent_c.json"
            previous.parent.mkdir(parents=True)
            old_text = json.dumps({
                "status": "failed", "requested_model": "glm-4.7-flash",
                "error_type": "RateLimitError", "retries": 0,
            })
            previous.write_text(old_text)
            result = self._main("--role", role, "--live",
                                "--confirm-one-request", "--approve-model", spec.model_id)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["saved"], f"output/provider_compat_{role}_{spec.model_id}.json")
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(previous.read_text(), old_text)
            self.assertEqual(json.loads(probe.result_path(spec).read_text())["requested_model"],
                             "glm-5.3-flash")

    def test_legacy_same_model_blocks_before_network(self):
        spec = get_model("agent_b")
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            probe, "RELEASE", Path(tmp)
        ), patch.dict(os.environ, {spec.key_env: "fake-key"}), patch.object(
            probe, "execute_one"
        ) as execute, redirect_stderr(io.StringIO()):
            legacy = Path(tmp) / "output" / "provider_compat_agent_b.json"
            legacy.parent.mkdir(parents=True)
            legacy.write_text(json.dumps({"status": "completed",
                                          "requested_model": spec.model_id}))
            with self.assertRaises(SystemExit):
                probe.main(["--role", spec.role, "--live",
                            "--confirm-one-request", "--approve-model", spec.model_id])
            execute.assert_not_called()

    def test_unreadable_legacy_record_blocks_before_network(self):
        spec = get_model("agent_c")
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            probe, "RELEASE", Path(tmp)
        ), patch.dict(os.environ, {spec.key_env: "fake-key"}), patch.object(
            probe, "execute_one"
        ) as execute, redirect_stderr(io.StringIO()):
            legacy = Path(tmp) / "output" / "provider_compat_agent_c.json"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("invalid json")
            with self.assertRaises(SystemExit):
                probe.main(["--role", spec.role, "--live",
                            "--confirm-one-request", "--approve-model", spec.model_id])
            execute.assert_not_called()

    def test_provider_error_is_sanitized_and_never_auto_retried(self):
        role = "agent_a"
        spec = get_model(role)
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            probe, "RELEASE", Path(tmp)
        ), patch.dict(os.environ, {spec.key_env: "fake-key"}), patch.object(
            probe, "execute_one", side_effect=RuntimeError("private-provider-message")
        ) as execute, redirect_stdout(io.StringIO()) as stdout:
            with self.assertRaises(SystemExit):
                probe.main(["--role", role, "--live",
                            "--confirm-one-request", "--approve-model", spec.model_id])
            self.assertEqual(execute.call_count, 1)
            saved = probe.result_path(spec).read_text()
            self.assertIn('"status": "failed"', saved)
            self.assertIn('"error_type": "RuntimeError"', saved)
            self.assertNotIn("private-provider-message", saved)
            self.assertNotIn("private-provider-message", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
