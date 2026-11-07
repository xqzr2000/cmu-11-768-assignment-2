"""Mock-only OpenAI Luna/Terra adapter tests; no paid completions."""

from __future__ import annotations

import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from integrations.judge import JUDGMENT_SCHEMA, decode_judgment, make_vision_input
from integrations.models import get_model
from integrations.providers import (
    AdapterProtocolError, execute_one, make_tool_result, prepare_request,
)
from integrations.providers.base import parse_reply

FUNCTION_TOOL = {
    "type": "function", "name": "run_shell",
    "description": "Execute an approved command inside the isolated sandbox.",
    "parameters": {"type": "object", "properties": {
        "command": {"type": "string"}
    }, "required": ["command"], "additionalProperties": False},
}


def response_for(text, *, model, status="completed"):
    return {
        "status": status, "model": model,
        "output": [{"type": "message", "content": [
            {"type": "output_text", "text": text}
        ]}],
        "usage": {"input_tokens": 14, "output_tokens": 9, "total_tokens": 23},
    }


class OpenAIProviderOfflineTests(unittest.TestCase):
    def setUp(self):
        self.luna = get_model("agent_b")
        self.terra = get_model("experimental_judge")
        self.items = [{"role": "user", "content": "Plot a bar chart."}]

    def test_luna_tool_request_uses_responses_and_local_only_tools(self):
        request = prepare_request(self.luna, self.items, tools=[FUNCTION_TOOL])
        self.assertEqual(request["model"], "gpt-5.6-luna")
        self.assertEqual(request["tools"], [FUNCTION_TOOL])
        self.assertEqual(request["tool_choice"], "auto")
        self.assertFalse(request["store"])
        self.assertNotIn("text", request)
        with self.assertRaises(ValueError):
            prepare_request(self.luna, self.items, schema=JUDGMENT_SCHEMA)

    def test_luna_tool_calls_and_followup_are_inert_data(self):
        reply = parse_reply(self.luna, {
            "status": "completed", "model": "gpt-5.6-luna",
            "output": [{"type": "function_call", "call_id": "fn_9",
                        "name": "run_shell", "arguments": '{"command":"ls"}'}],
        })
        self.assertEqual(reply.tool_calls[0].arguments, {"command": "ls"})
        item = make_tool_result(self.luna.api_style, "fn_9", "figure.png")
        request = prepare_request(
            self.luna, self.items + list(reply.continuation_items) + [item]
        )
        self.assertEqual(request["input"][-1]["type"], "function_call_output")

    def test_terra_requires_strict_schema_and_rejects_shell_tools(self):
        with self.assertRaises(ValueError):
            prepare_request(self.terra, self.items)
        with self.assertRaises(ValueError):
            prepare_request(self.terra, self.items,
                            tools=[FUNCTION_TOOL], schema=JUDGMENT_SCHEMA)
        request = prepare_request(self.terra, self.items, schema=JUDGMENT_SCHEMA)
        self.assertEqual(request["model"], "gpt-6.1-terra")
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertTrue(request["text"]["format"]["strict"])
        self.assertEqual(request["text"]["format"]["schema"], JUDGMENT_SCHEMA)
        self.assertNotIn("tools", request)

    def test_terra_payload_contains_png_not_reference_labels(self):
        memory = io.BytesIO()
        Image.new("RGB", (30, 25), "white").save(memory, "PNG")
        items = make_vision_input("Inspect axes and legend", memory.getvalue())
        request = prepare_request(self.terra, items, schema=JUDGMENT_SCHEMA)
        contents = request["input"][0]["content"]
        self.assertEqual(contents[0], {
            "type": "input_text", "text": "Inspect axes and legend"
        })
        self.assertTrue(contents[1]["image_url"].startswith("data:image/png;base64,"))
        self.assertNotIn("seed_labels", json.dumps(request))

    def test_terra_decoder_rejects_invalid_or_duplicate_errors(self):
        valid = json.dumps({"errors": [
            {"family": "wrong_chart", "evidence": "  Missing log x axis.  "}
        ]})
        reply = parse_reply(self.terra, response_for(valid, model="gpt-6.1-terra"))
        self.assertEqual(decode_judgment(reply), [
            {"family": "wrong_chart", "evidence": "Missing log x axis."}
        ])
        for text in (
            "not json", "{}", '{"errors":"no"}',
            json.dumps({"errors": [{"family": "wrong_chart", "evidence": ""}]}),
            json.dumps({"errors": [{"family": "wrong_chart", "evidence": "x"},
                                   {"family": "wrong_chart", "evidence": "y"}]}),
            json.dumps({"errors": [{"family": "execution_failure", "evidence": "No PNG"},
                                   {"family": "wrong_chart", "evidence": "Wrong axes"}]}),
            json.dumps({"errors": [{"family": "made_up", "evidence": "why"}]}),
        ):
            with self.subTest(text=text), self.assertRaises(AdapterProtocolError):
                decode_judgment(parse_reply(
                    self.terra, response_for(text, model="gpt-6.1-terra")
                ))
        self.assertEqual(decode_judgment(parse_reply(
            self.terra, response_for('{"errors":[]}', model="gpt-6.1-terra")
        )), [])

    def test_terra_incomplete_response_never_becomes_acceptable(self):
        incomplete = response_for('{"errors":[]}', model="gpt-6.1-terra",
                                  status="incomplete")
        with self.assertRaises(AdapterProtocolError):
            parse_reply(self.terra, incomplete)

    def test_live_gate_applies_even_to_mocked_openai_client(self):
        client = MagicMock()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "mock-key"}):
            with self.assertRaises(PermissionError):
                execute_one(self.luna, self.items, live=True, client=client)
            with self.assertRaises(PermissionError):
                execute_one(self.terra, self.items, schema=JUDGMENT_SCHEMA,
                            confirm_one_request=True, client=client)
        client.responses.create.assert_not_called()

    def test_sdk_factory_is_gated_and_uses_pinned_endpoint_without_retries(self):
        with patch("openai.OpenAI") as factory, patch.dict(
            os.environ, {"OPENAI_API_KEY": "placeholder-not-real"}
        ):
            client = factory.return_value
            client.responses.create.return_value = response_for(
                "Plan a graph.", model="gpt-5.6-luna"
            )
            with self.assertRaises(PermissionError):
                execute_one(self.luna, self.items, live=True)
            factory.assert_not_called()
            reply = execute_one(self.luna, self.items, live=True,
                                confirm_one_request=True)
        self.assertEqual(reply.text, "Plan a graph.")
        factory.assert_called_once()
        kwargs = factory.call_args.kwargs
        self.assertEqual(kwargs["base_url"], "https://api.openai.com/v1")
        self.assertEqual(kwargs["max_retries"], 0)
        self.assertEqual(kwargs["timeout"], 60.0)
        self.assertEqual(client.responses.create.call_count, 1)

    def test_one_mocked_terra_request_and_normalized_usage(self):
        client = MagicMock()
        client.responses.create.return_value = response_for(
            '{"errors":[]}', model="gpt-6.1-terra"
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "mock-key"}):
            result = execute_one(
                self.terra, self.items, schema=JUDGMENT_SCHEMA,
                live=True, confirm_one_request=True, client=client
            )
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertEqual(result.reported_model, "gpt-6.1-terra")
        self.assertEqual(result.total_tokens, 23)
        self.assertEqual(decode_judgment(result), [])


if __name__ == "__main__":
    unittest.main()
