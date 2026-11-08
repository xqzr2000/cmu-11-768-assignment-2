"""Offline-only, explicitly stepped state machine for chart-generator conversations.

No API clients, Docker containers or shell commands are constructed or run here.
A caller must separately approve each billable request and each sandbox command.
The controller tracks parsed provider replies and tool-result *data* only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from integrations.models import MODELS, ModelSpec
from integrations.providers import NormalizedReply, ToolCall, make_tool_result, prepare_request, preview_request

SHELL_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "run_shell",
    "description": "Propose a shell command to run in a separately approved isolated Docker sandbox.",
    "parameters": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
        "additionalProperties": False,
    },
}


class ControllerError(ValueError):
    """A model reply, state transition or configured execution budget is invalid."""


@dataclass(frozen=True)
class ControllerLimits:
    max_model_turns: int = 4
    max_tool_calls: int = 6
    max_command_chars: int = 2000
    max_output_chars: int = 2048

    def __post_init__(self) -> None:
        if any(type(value) is not int or value < 1 for value in (
            self.max_model_turns,
            self.max_tool_calls,
            self.max_command_chars,
            self.max_output_chars,
        )):
            raise ValueError("Controller limits must be positive integers.")


class ChartController:
    """Pure per-task controller; never sends requests or executes commands.

    Each request is prepared for a caller which has to obtain a *new* approval
    before using any live provider transport. Returned function calls are
    untrusted descriptions, not executable instructions. Tool outputs may only
    be added after separately approved sandbox execution.
    """

    def __init__(self, spec: ModelSpec, task_prompt: str, *,
                 limits: ControllerLimits | None = None) -> None:
        if not isinstance(spec, ModelSpec) or MODELS.get(spec.role) != spec:
            raise ValueError("Controller requires a registered model.")
        if spec.is_judge:
            raise ValueError("The Terra judge is not a chart-generation agent.")
        if not isinstance(task_prompt, str) or not task_prompt.strip():
            raise ValueError("Task prompt cannot be blank.")
        self.spec = spec
        self.limits = limits or ControllerLimits()
        self._items: list[dict[str, Any]] = [
            {"role": "user", "content": task_prompt}
        ]
        self._pending: dict[str, ToolCall] = {}
        self._used_call_ids: set[str] = set()
        self.model_turns = 0
        self.tool_calls = 0
        self.completed = False
        self.final_text: str | None = None

    @property
    def pending_calls(self) -> tuple[ToolCall, ...]:
        return tuple(self._pending.values())

    def _require_next_turn(self) -> None:
        if self.completed:
            raise ControllerError("The controller is already complete.")
        if self._pending:
            raise ControllerError("Tool outputs are still pending.")
        if self.model_turns >= self.limits.max_model_turns:
            raise ControllerError("Model-turn budget exhausted.")

    def preview_next_request(self) -> dict[str, Any]:
        """Safe metadata preview, without exposing prompt contents."""
        self._require_next_turn()
        return preview_request(self.spec, list(self._items), tools=[SHELL_TOOL])

    def prepare_next_request(self) -> dict[str, Any]:
        """Pure provider-native request for a separately approved caller."""
        self._require_next_turn()
        return prepare_request(self.spec, list(self._items), tools=[SHELL_TOOL])

    def accept_reply(self, reply: NormalizedReply) -> None:
        """Validate one *already received* reply and advance the state."""
        self._require_next_turn()
        if not isinstance(reply, NormalizedReply):
            raise ControllerError("Expected a normalized provider reply.")
        if reply.role != self.spec.role or reply.requested_model != self.spec.model_id:
            raise ControllerError("Reply does not match the pinned provider role/model.")
        if not reply.continuation_items or not all(
            isinstance(item, dict) for item in reply.continuation_items
        ):
            raise ControllerError("Provider continuation items are missing.")

        calls = reply.tool_calls
        if calls and self.model_turns + 1 >= self.limits.max_model_turns:
            raise ControllerError("No model-turn budget remains after tools.")
        if self.tool_calls + len(calls) > self.limits.max_tool_calls:
            raise ControllerError("Tool-call budget exhausted.")
        ids: set[str] = set()
        for call in calls:
            if not isinstance(call, ToolCall) or call.name != "run_shell":
                raise ControllerError("Only the run_shell tool is supported.")
            if not isinstance(call.call_id, str) or not call.call_id.strip():
                raise ControllerError("Invalid tool call ID.")
            if call.call_id in self._used_call_ids or call.call_id in ids:
                raise ControllerError("Repeated tool call ID.")
            if not isinstance(call.arguments, dict) or set(call.arguments) != {"command"}:
                raise ControllerError("Shell tool requires only a command argument.")
            command = call.arguments["command"]
            if (not isinstance(command, str) or not command.strip()
                or len(command) > self.limits.max_command_chars
                or "\x00" in command):
                raise ControllerError("Invalid or oversized command.")
            ids.add(call.call_id)

        if not calls and not reply.text.strip():
            raise ControllerError("Reply contained neither a tool call nor final text.")
        # Everything above validates before mutable state changes.
        self._items.extend(dict(item) for item in reply.continuation_items)
        self.model_turns += 1
        self.tool_calls += len(calls)
        self._used_call_ids.update(ids)
        self._pending.update((call.call_id, call) for call in calls)
        if not calls:
            self.completed = True
            self.final_text = reply.text

    def record_tool_result(self, call_id: str, result: dict[str, Any]) -> None:
        """Record externally obtained sandbox output; does not execute a tool."""
        if call_id not in self._pending:
            raise ControllerError("Unknown or already resolved tool call.")
        if not isinstance(result, dict):
            raise ControllerError("Tool result must be a mapping.")
        exit_code = result.get("returncode")
        stdout, stderr = result.get("stdout"), result.get("stderr")
        if type(exit_code) is not int or not isinstance(stdout, str) or not isinstance(stderr, str):
            raise ControllerError("Malformed sandbox result.")
        limit = self.limits.max_output_chars
        output = json.dumps({
            "returncode": exit_code,
            "stdout": stdout[:limit],
            "stderr": stderr[:limit],
            "stdout_truncated": len(stdout) > limit,
            "stderr_truncated": len(stderr) > limit,
        }, separators=(",", ":"))
        self._items.append(make_tool_result(self.spec.api_style, call_id, output))
        del self._pending[call_id]
