"""Mock-only Z.ai chat-completions adapter tests (no API calls)."""

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
    "description": "Run one approved command in an isolated container.",
    "parameters": {"type": "object", "properties": {
        "command": {"type": "string"}
    }, "required": ["command"], "additionalProperties": False},
}


class ZaiProviderOfflineTests(unittest.TestCase):
    def setUp(self):
        self.spec = get_model("agent_c")
        self.messages = [{"role": "user", "content": "Create a line chart."}]

    def test_uses_chat_completions_and_converts_function_schema(self):
        request = prepare_request(self.spec, self.messages, tools=[SHELL_TOOL])
        self.assertEqual(request["model"], "glm-5.3-flash")
        self.assertEqual(request["messages"], self.messages)
        self.assertEqual(request["tool_choice"], "auto")
        self.assertEqual(request["tools"][0]["function"]["name"], "run_shell")
        self.assertEqual(request["tools"][0]["type"], "function")
        self.assertEqual(request["max_tokens"], 512)
        self.assertEqual(request["extra_body"], {"reasoning_effort": "low"})
        self.assertFalse(request["stream"])
        self.assertNotIn("input", request)
        with self.assertRaises(ValueError):
            prepare_request(self.spec, [
                {"type": "function_call_output", "call_id": "xyz", "output": "done"}
            ])

    def test_parses_tool_call_and_keeps_chat_turn(self):
        response = {
            "model": "glm-5.3-flash",
            "choices": [{"finish_reason": "tool_calls", "message": {
                "content": None,
                "tool_calls": [{"id": "c1", "type": "function",
                                "function": {"name": "run_shell",
                                             "arguments": '{"command":"ls"}'}}],
            }}],
            "usage": {"prompt_tokens": 14, "completion_tokens": 9, "total_tokens": 23},
        }
        reply = parse_reply(self.spec, response)
        self.assertEqual(reply.tool_calls[0].call_id, "c1")
        self.assertEqual(reply.tool_calls[0].arguments["command"], "ls")
        self.assertEqual(reply.input_tokens, 14)
        self.assertEqual(reply.continuation_items[0]["role"], "assistant")
        result = make_tool_result(self.spec.api_style, "c1", "figure.png")
        self.assertEqual(result, {
            "role": "tool", "tool_call_id": "c1", "content": "figure.png"
        })
        followup = self.messages + list(reply.continuation_items) + [result]
        self.assertEqual(prepare_request(self.spec, followup)["messages"][-1], result)

    def test_rejects_incomplete_response_and_bad_json(self):
        for response in (
            {"choices": []},
            {"choices": [{"finish_reason": "length", "message": {"content": "ok"}}]},
            {"choices": [{"finish_reason": "tool_calls", "message": {
                "tool_calls": [{"id": "c1", "function": {
                    "name": "run_shell", "arguments": "not JSON"
                }}]
            }}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": None}}]},
        ):
            with self.subTest(response=response), self.assertRaises(AdapterProtocolError):
                parse_reply(self.spec, response)

    def test_mocked_live_call_requires_double_approval(self):
        client = MagicMock()
        with patch.dict(os.environ, {"ZAI_API_KEY": "mock-key"}):
            with self.assertRaises(PermissionError):
                execute_one(self.spec, self.messages, client=client)
        client.chat.completions.create.assert_not_called()

    def test_one_mocked_chat_completion(self):
        client = MagicMock()
        client.chat.completions.create.return_value = {
            "model": "glm-5.3-flash",
            "choices": [{"finish_reason": "stop", "message": {
                "content": "Use a line graph.",
            }}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }
        with patch.dict(os.environ, {"ZAI_API_KEY": "mock-key"}):
            reply = execute_one(
                self.spec, self.messages, tools=[SHELL_TOOL],
                live=True, confirm_one_request=True, client=client,
            )
        self.assertEqual(reply.text, "Use a line graph.")
        self.assertEqual(reply.total_tokens, 14)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        client.responses.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
