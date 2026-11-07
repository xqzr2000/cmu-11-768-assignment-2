"""Mock-only DeepSeek Responses API adapter tests (no HTTP calls)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from integrations.models import get_model
from integrations.providers import (
    AdapterProtocolError, execute_one, make_tool_result, prepare_request,
)
from integrations.providers.base import parse_reply

SHELL_TOOL = {
    "type": "function", "name": "run_shell",
    "description": "Run a bounded command inside the task sandbox.",
    "parameters": {
        "type": "object", "properties": {"command": {"type": "string"}},
        "required": ["command"], "additionalProperties": False,
    },
}


class DeepSeekProviderOfflineTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_model("agent_a")
        self.items = [{"role": "user", "content": "Plot x against y."}]

    def test_stateless_responses_request_and_tool_shape(self):
        request = prepare_request(self.spec, self.items, tools=[SHELL_TOOL])
        self.assertEqual(request["model"], "deepseek-flash")
        self.assertEqual(request["input"], self.items)
        self.assertEqual(request["tools"], [SHELL_TOOL])
        self.assertEqual(request["tool_choice"], "auto")
        self.assertNotIn("previous_response_id", request)
        self.assertNotIn("store", request)
        self.assertNotIn("messages", request)

    def test_mocked_tool_call_is_parsed_and_never_executed(self):
        response = {
            "status": "completed", "model": "deepseek-flash",
            "output": [
                {"type": "reasoning", "id": "r1", "summary": []},
                {"type": "function_call", "call_id": "call_1",
                 "name": "run_shell", "arguments": '{"command":"python plot.py"}'},
            ],
            "usage": {"input_tokens": 20, "output_tokens": 8, "total_tokens": 28},
        }
        reply = parse_reply(self.spec, response)
        self.assertEqual(reply.tool_calls[0].name, "run_shell")
        self.assertEqual(reply.tool_calls[0].arguments["command"], "python plot.py")
        self.assertEqual(reply.input_tokens, 20)
        self.assertEqual(reply.total_tokens, 28)
        self.assertEqual(len(reply.continuation_items), 2)
        tool_result = make_tool_result(self.spec.api_style, "call_1", "exit 0")
        self.assertEqual(tool_result, {
            "type": "function_call_output", "call_id": "call_1", "output": "exit 0"
        })
        # Stateless DeepSeek needs the previous output items and tool result.
        next_items = self.items + list(reply.continuation_items) + [tool_result]
        self.assertEqual(prepare_request(self.spec, next_items)["input"][-1], tool_result)

    def test_bad_tool_json_refusal_and_incomplete_results_fail(self):
        valid = {"type": "function_call", "call_id": "c", "name": "run_shell"}
        for response in (
            {"status": "incomplete", "output": []},
            {"status": "completed", "output": [{**valid, "arguments": "oops"}]},
            {"status": "completed", "output": [{**valid, "arguments": "[]"}]},
            {"status": "completed", "output": [{
                "type": "message", "content": [{"type": "refusal", "refusal": "no"}]
            }]},
            {"status": "completed", "output": []},
        ):
            with self.subTest(response=response), self.assertRaises(AdapterProtocolError):
                parse_reply(self.spec, response)

    def test_double_consent_blocks_even_injected_client(self):
        client = MagicMock()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "mock-secret"}):
            for live, confirm in ((False, False), (True, False), (False, True)):
                with self.subTest(flags=(live, confirm)):
                    with self.assertRaises(PermissionError):
                        execute_one(self.spec, self.items, live=live,
                                    confirm_one_request=confirm, client=client)
        client.responses.create.assert_not_called()

    def test_missing_key_blocks_injected_client(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            client = MagicMock()
            with self.assertRaisesRegex(RuntimeError, "DEEPSEEK_API_KEY"):
                execute_one(self.spec, self.items, live=True,
                            confirm_one_request=True, client=client)
            client.responses.create.assert_not_called()

    def test_one_explicit_mocked_request_has_no_retry(self):
        fake = {
            "status": "completed", "model": "deepseek-flash",
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": "I'll create the chart."}
            ]}],
            "usage": {"input_tokens": 10, "output_tokens": 6, "total_tokens": 16},
        }
        client = MagicMock()
        client.responses.create.return_value = fake
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "mock-key"}):
            reply = execute_one(self.spec, self.items, tools=[SHELL_TOOL],
                                live=True, confirm_one_request=True, client=client)
        self.assertEqual(reply.text, "I'll create the chart.")
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertEqual(client.responses.create.call_args.kwargs["model"], "deepseek-flash")
        client.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
