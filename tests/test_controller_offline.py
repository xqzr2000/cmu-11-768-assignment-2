"""Mock-only tests for the Session 010 stepped chart controller (no API/Docker)."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from integrations.chart_controller import ChartController, ControllerError, ControllerLimits
from integrations.models import get_model
from integrations.providers import NormalizedReply, ToolCall


def reply(role: str, *, calls: tuple[ToolCall, ...] = (), text: str = "") -> NormalizedReply:
    spec = get_model(role)
    if spec.api_style == "responses":
        items = tuple([
            {"type": "function_call", "call_id": call.call_id,
             "name": call.name, "arguments": json.dumps(call.arguments)}
            for call in calls
        ])
        if text:
            items += ({"type": "message", "content": [
                {"type": "output_text", "text": text}
            ]},)
    else:
        assistant = {"role": "assistant", "content": text or None}
        if calls:
            assistant["tool_calls"] = [
                {"id": call.call_id, "type": "function",
                 "function": {"name": call.name, "arguments": json.dumps(call.arguments)}}
                for call in calls
            ]
        items = (assistant,)
    return NormalizedReply(
        role=role, requested_model=spec.model_id, reported_model=spec.model_id,
        text=text, tool_calls=calls, input_tokens=10, output_tokens=8,
        total_tokens=18, continuation_items=items,
    )


def command(call_id: str = "call_one", value: str = "pwd") -> ToolCall:
    return ToolCall(call_id, "run_shell", {"command": value})


class ChartControllerOfflineTests(unittest.TestCase):
    def test_provider_specific_request_is_pure_and_has_no_network(self):
        for role in ("agent_a", "agent_b", "agent_c"):
            with self.subTest(role=role), patch(
                "integrations.providers.client.execute_one"
            ) as transport:
                controller = ChartController(get_model(role), "Create the chart.")
                preview = controller.preview_next_request()
                request = controller.prepare_next_request()
                self.assertEqual(preview["network_requests"], 0)
                self.assertEqual(preview["function_tool_names"], ["run_shell"])
                self.assertEqual(request["model"], get_model(role).model_id)
                self.assertIn("input" if role != "agent_c" else "messages", request)
                transport.assert_not_called()
                self.assertEqual(controller.model_turns, 0)

    def test_full_two_turn_tool_replay_for_each_provider(self):
        for role in ("agent_a", "agent_b", "agent_c"):
            with self.subTest(role=role):
                controller = ChartController(get_model(role), "Make a plot.")
                controller.accept_reply(reply(role, calls=(command(),)))
                self.assertEqual(controller.model_turns, 1)
                self.assertEqual(len(controller.pending_calls), 1)
                with self.assertRaises(ControllerError):
                    controller.prepare_next_request()
                controller.record_tool_result("call_one", {
                    "returncode": 0, "stdout": "ok\n", "stderr": ""
                })
                request = controller.prepare_next_request()
                entries = request.get("input", request.get("messages"))
                if role == "agent_c":
                    self.assertEqual(entries[-2]["role"], "assistant")
                    self.assertEqual(entries[-1]["role"], "tool")
                    self.assertEqual(entries[-1]["tool_call_id"], "call_one")
                else:
                    self.assertEqual(entries[-2]["type"], "function_call")
                    self.assertEqual(entries[-1]["type"], "function_call_output")
                    self.assertEqual(entries[-1]["call_id"], "call_one")
                parsed_output = json.loads(entries[-1].get("output", entries[-1].get("content")))
                self.assertEqual(parsed_output["returncode"], 0)
                controller.accept_reply(reply(role, text="Completed."))
                self.assertTrue(controller.completed)
                self.assertEqual(controller.final_text, "Completed.")
                self.assertEqual(controller.model_turns, 2)
                self.assertEqual(controller.tool_calls, 1)
                with self.assertRaises(ControllerError):
                    controller.prepare_next_request()

    def test_unregistered_or_judge_roles_rejected(self):
        with self.assertRaises(ValueError):
            ChartController(get_model("experimental_judge"), "Judge image")
        with self.assertRaises(ValueError):
            ChartController(get_model("agent_a"), "")
        with self.assertRaises(ValueError):
            ChartController(get_model("agent_a"), " ")

    def test_limits_are_strict_positive_integers(self):
        for kwargs in ({"max_model_turns": 0}, {"max_tool_calls": True},
                       {"max_output_chars": -1}, {"max_command_chars": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ControllerLimits(**kwargs)

    def test_wrong_provider_response_is_rejected_without_mutation(self):
        controller = ChartController(get_model("agent_a"), "Task")
        with self.assertRaises(ControllerError):
            controller.accept_reply(reply("agent_b", calls=(command(),)))
        self.assertEqual(controller.model_turns, 0)
        self.assertFalse(controller.pending_calls)

    def test_rejects_unknown_tool_extra_parameters_and_long_commands(self):
        for call in (
            ToolCall("c1", "run_python", {"command": "pwd"}),
            ToolCall("c1", "run_shell", {"command": "pwd", "unsafe": True}),
            ToolCall("c1", "run_shell", {"command": ""}),
            ToolCall("c1", "run_shell", {"command": "x" * 11}),
            ToolCall("c1", "run_shell", {"command": "pwd\x00ls"}),
        ):
            controller = ChartController(get_model("agent_a"), "Task",
                                         limits=ControllerLimits(max_command_chars=10))
            with self.subTest(call=call), self.assertRaises(ControllerError):
                controller.accept_reply(reply("agent_a", calls=(call,)))
            self.assertEqual(controller.model_turns, 0)
            self.assertEqual(controller.tool_calls, 0)

    def test_duplicate_ids_in_one_reply_or_across_turns_fail(self):
        controller = ChartController(get_model("agent_a"), "Task")
        with self.assertRaises(ControllerError):
            controller.accept_reply(reply("agent_a", calls=(command("x"), command("x"))))
        self.assertEqual(controller.model_turns, 0)
        controller.accept_reply(reply("agent_a", calls=(command("x"),)))
        controller.record_tool_result("x", {"returncode": 0, "stdout": "", "stderr": ""})
        with self.assertRaises(ControllerError):
            controller.accept_reply(reply("agent_a", calls=(command("x"),)))
        self.assertEqual(controller.model_turns, 1)

    def test_budgets_reject_more_tools_and_final_turn_tool_call(self):
        controller = ChartController(get_model("agent_a"), "Task",
                                     limits=ControllerLimits(max_tool_calls=1,
                                                             max_model_turns=2))
        with self.assertRaises(ControllerError):
            controller.accept_reply(reply("agent_a", calls=(command("1"), command("2"))))
        controller.accept_reply(reply("agent_a", calls=(command("1"),)))
        controller.record_tool_result("1", {"returncode": 0, "stdout": "", "stderr": ""})
        with self.assertRaises(ControllerError):
            controller.accept_reply(reply("agent_a", calls=(command("2"),)))
        controller.accept_reply(reply("agent_a", text="Done"))
        self.assertTrue(controller.completed)

    def test_one_turn_limit_still_accepts_final_text(self):
        controller = ChartController(get_model("agent_c"), "Task",
                                     limits=ControllerLimits(max_model_turns=1))
        with self.assertRaises(ControllerError):
            controller.accept_reply(reply("agent_c", calls=(command(),)))
        controller.accept_reply(reply("agent_c", text="No tools needed."))
        self.assertTrue(controller.completed)

    def test_tool_output_truncation_and_replay_safety(self):
        controller = ChartController(get_model("agent_c"), "Task",
                                     limits=ControllerLimits(max_output_chars=4))
        controller.accept_reply(reply("agent_c", calls=(command(),)))
        controller.record_tool_result("call_one", {
            "returncode": 124,
            "stdout": "abcdefgh", "stderr": "warning...",
            "output": "ignored-untrusted-full-output",
        })
        entries = controller.prepare_next_request()["messages"]
        tool_json = entries[-1]["content"]
        data = json.loads(tool_json)
        self.assertEqual(data["stdout"], "abcd")
        self.assertEqual(data["stderr"], "warn")
        self.assertTrue(data["stdout_truncated"])
        self.assertNotIn("ignored-untrusted-full-output", tool_json)
        with self.assertRaises(ControllerError):
            controller.record_tool_result("call_one", {
                "returncode": 0, "stdout": "", "stderr": ""
            })

    def test_unresolved_tools_cannot_be_skipped(self):
        controller = ChartController(get_model("agent_a"), "Task")
        controller.accept_reply(reply("agent_a", calls=(command("a"), command("b"))))
        controller.record_tool_result("a", {"returncode": 0, "stdout": "", "stderr": ""})
        with self.assertRaises(ControllerError):
            controller.prepare_next_request()
        with self.assertRaises(ControllerError):
            controller.record_tool_result("invalid", {
                "returncode": 0, "stdout": "", "stderr": ""
            })
        with self.assertRaises(ControllerError):
            controller.record_tool_result("b", {
                "returncode": True, "stdout": "", "stderr": ""
            })
        controller.record_tool_result("b", {"returncode": 0, "stdout": "", "stderr": ""})
        self.assertFalse(controller.pending_calls)


if __name__ == "__main__":
    unittest.main()
