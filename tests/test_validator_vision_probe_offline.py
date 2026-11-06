"""Offline-only tests for the opt-in Z.ai GLM-4.6V-Flash vision probe."""

from __future__ import annotations

import base64
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from PIL import Image

from scripts import zai_vision_probe as probe


def sample_response(answer: str):
    return SimpleNamespace(
        model=probe.MODEL,
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer))],
        usage=SimpleNamespace(prompt_tokens=80, completion_tokens=2, total_tokens=82),
    )


class VisionProbeOfflineTests(unittest.TestCase):
    def test_generated_png_is_valid_and_blue_bar_taller(self):
        png = probe.make_probe_png()
        self.assertLess(len(png), 20_000)
        with Image.open(io.BytesIO(png)) as image:
            image.load()
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (256, 256))
            # Both bars are colored; the blue one begins visibly higher.
            self.assertEqual(image.getpixel((80, 80)), (24, 94, 207))
            self.assertEqual(image.getpixel((175, 80)), (255, 255, 255))
            self.assertEqual(image.getpixel((175, 170)), (245, 132, 33))

    def test_multimodal_payload_embeds_the_png(self):
        png = probe.make_probe_png()
        messages = probe.build_messages(png)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(
            [part["type"] for part in messages[0]["content"]],
            ["text", "image_url"],
        )
        self.assertIn("taller", messages[0]["content"][0]["text"])
        url = messages[0]["content"][1]["image_url"]["url"]
        self.assertTrue(url.startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(url.split(",", 1)[1]), png)

    def test_default_mode_makes_zero_network_requests(self):
        output = io.StringIO()
        with patch.object(probe, "load_dotenv"), patch.object(probe, "OpenAI") as factory:
            with redirect_stdout(output):
                code = probe.main([])
        self.assertEqual(code, 0)
        factory.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(result["mode"], "offline")
        self.assertEqual(result["network_requests"], 0)
        self.assertFalse(result["official_qwen_equivalent"])

    def test_one_flag_is_not_sufficient_for_live_mode(self):
        with self.assertRaises(SystemExit) as only_live:
            probe.main(["--live"])
        self.assertEqual(only_live.exception.code, 2)
        with self.assertRaises(SystemExit) as only_confirm:
            probe.main(["--confirm-one-request"])
        self.assertEqual(only_confirm.exception.code, 2)

    def test_live_missing_key_does_not_construct_client(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"ZAI_API_KEY": ""}), patch.object(
            probe, "load_dotenv"
        ), patch.object(probe, "OpenAI") as factory:
            with redirect_stdout(output):
                code = probe.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 2)
        factory.assert_not_called()
        self.assertIn("not configured", output.getvalue())

    def test_one_mocked_live_request_uses_fixed_endpoint_and_no_retries(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = sample_response("BLUE")
        output = io.StringIO()
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-placeholder-key"}), patch.object(
            probe, "load_dotenv"
        ), patch.object(probe, "OpenAI", return_value=mock_client) as factory:
            with redirect_stdout(output):
                code = probe.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["vision_smoke_test_passed"])
        kwargs = factory.call_args.kwargs
        self.assertEqual(kwargs["base_url"], "https://api.z.ai/api/paas/v4/")
        self.assertEqual(kwargs["max_retries"], 0)
        self.assertEqual(kwargs["timeout"], probe.TIMEOUT_SECONDS)
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)
        call = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["model"], "glm-4.6v-flash")
        self.assertEqual(call["max_tokens"], probe.MAX_OUTPUT_TOKENS)
        self.assertEqual(call["extra_body"]["thinking"]["type"], "disabled")
        self.assertTrue(call["messages"][0]["content"][1]["image_url"]["url"].startswith(
            "data:image/png;base64,"
        ))

    def test_wrong_or_ambiguous_response_is_not_a_success(self):
        self.assertTrue(probe.is_correct(" blue."))
        for answer in ("ORANGE", "BLUE or ORANGE", "", "Maybe BLUE", "BLUE and ORANGE"):
            self.assertFalse(probe.is_correct(answer))
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = sample_response("ORANGE")
        output = io.StringIO()
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-placeholder-key"}), patch.object(
            probe, "load_dotenv"
        ), patch.object(probe, "OpenAI", return_value=mock_client):
            with redirect_stdout(output):
                code = probe.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())["vision_smoke_test_passed"])

    def test_provider_failure_is_reported_without_a_retry(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("do not display secret")
        output = io.StringIO()
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-placeholder-key"}), patch.object(
            probe, "load_dotenv"
        ), patch.object(probe, "OpenAI", return_value=mock_client):
            with redirect_stdout(output):
                code = probe.main(["--live", "--confirm-one-request"])
        self.assertEqual(code, 2)
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertNotIn("do not display secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
