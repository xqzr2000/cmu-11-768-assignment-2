"""Pure parsing and normalization of provider replies.

This module has no API client and never runs model-proposed tools.
Response and tool-call IDs are retained so a future controller can replay
stateful rounds safely (DeepSeek's Responses endpoint is stateless).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from integrations.models import APIStyle, ModelSpec


class AdapterProtocolError(ValueError):
    """Provider response was incomplete, refused, or malformed."""


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class NormalizedReply:
    role: str
    requested_model: str
    reported_model: str | None
    text: str
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    # Unmodified model output items needed for a subsequent tool-response turn.
    # They are data, not trusted instructions or commands to execute.
    continuation_items: tuple[dict[str, Any], ...]


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _dump(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    method = getattr(value, "model_dump", None)
    if callable(method):
        data = method(mode="json", exclude_none=True)
    else:
        data = vars(value) if hasattr(value, "__dict__") else None
    if not isinstance(data, dict):
        raise AdapterProtocolError("Expected a serializable output item.")
    return data


def _token(usage: Any, key: str) -> int | None:
    value = _get(usage, key)
    return value if type(value) is int and value >= 0 else None


def _tool(call_id: Any, name: Any, arguments: Any) -> ToolCall:
    if not isinstance(call_id, str) or not call_id.strip():
        raise AdapterProtocolError("Tool call has no valid ID.")
    if not isinstance(name, str) or not name.strip():
        raise AdapterProtocolError("Tool call has no valid name.")
    if not isinstance(arguments, str):
        raise AdapterProtocolError("Tool arguments are not JSON text.")
    try:
        payload = json.loads(arguments)
    except (ValueError, TypeError) as exc:
        raise AdapterProtocolError("Tool arguments are not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise AdapterProtocolError("Tool arguments must be a JSON object.")
    return ToolCall(call_id=call_id, name=name, arguments=payload)


def _check_calls(calls: list[ToolCall]) -> None:
    ids = [item.call_id for item in calls]
    if len(ids) != len(set(ids)):
        raise AdapterProtocolError("Duplicate tool-call IDs.")


def _response_reply(spec: ModelSpec, response: Any) -> NormalizedReply:
    if _get(response, "status") != "completed":
        raise AdapterProtocolError("Responses API result did not complete.")
    output = _get(response, "output")
    if not isinstance(output, list):
        raise AdapterProtocolError("Responses API output is missing.")
    text_parts: list[str] = []
    calls: list[ToolCall] = []
    saved_items: list[dict[str, Any]] = []
    for item in output:
        item_type = _get(item, "type")
        saved_items.append(_dump(item))
        if item_type == "function_call":
            calls.append(_tool(
                _get(item, "call_id"), _get(item, "name"), _get(item, "arguments")
            ))
        elif item_type == "message":
            content = _get(item, "content")
            if not isinstance(content, list):
                raise AdapterProtocolError("Response message has invalid content.")
            for part in content:
                kind = _get(part, "type")
                if kind == "refusal":
                    raise AdapterProtocolError("Model refused the request.")
                if kind == "output_text":
                    value = _get(part, "text")
                    if not isinstance(value, str):
                        raise AdapterProtocolError("Response text was not a string.")
                    text_parts.append(value)
        elif item_type == "reasoning":
            # Preserve opaque reasoning items in continuation_items without
            # exposing them as user text or interpreting them as commands.
            continue
        else:
            # Unsupported calls are not silently treated as an acceptable answer.
            raise AdapterProtocolError("Unsupported Responses API output item.")
    _check_calls(calls)
    content = "".join(text_parts)
    if not content.strip() and not calls:
        raise AdapterProtocolError("No text or function calls in completed response.")
    usage = _get(response, "usage")
    reported = _get(response, "model")
    return NormalizedReply(
        role=spec.role, requested_model=spec.model_id,
        reported_model=reported if isinstance(reported, str) else None,
        text=content, tool_calls=tuple(calls),
        input_tokens=_token(usage, "input_tokens"),
        output_tokens=_token(usage, "output_tokens"),
        total_tokens=_token(usage, "total_tokens"),
        continuation_items=tuple(saved_items),
    )


def _chat_reply(spec: ModelSpec, response: Any) -> NormalizedReply:
    choices = _get(response, "choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise AdapterProtocolError("Expected exactly one chat completion choice.")
    choice = choices[0]
    finish_reason = _get(choice, "finish_reason")
    if finish_reason not in ("stop", "tool_calls"):
        raise AdapterProtocolError("Chat completion was interrupted.")
    message = _get(choice, "message")
    if _get(message, "refusal"):
        raise AdapterProtocolError("Model refused the request.")
    raw_text = _get(message, "content")
    if raw_text is not None and not isinstance(raw_text, str):
        raise AdapterProtocolError("Chat content is not text.")
    raw_calls = _get(message, "tool_calls") or []
    if not isinstance(raw_calls, list):
        raise AdapterProtocolError("Chat tool calls are malformed.")
    calls: list[ToolCall] = []
    for item in raw_calls:
        fn = _get(item, "function")
        calls.append(_tool(_get(item, "id"), _get(fn, "name"), _get(fn, "arguments")))
    _check_calls(calls)
    if finish_reason == "tool_calls" and not calls:
        raise AdapterProtocolError("Chat model signaled tools without calls.")
    if not (raw_text or "").strip() and not calls:
        raise AdapterProtocolError("No text or tool calls in completed chat response.")
    usage = _get(response, "usage")
    reported = _get(response, "model")
    # Chat continuation is an assistant message with tool_calls. Preserve the
    # provider message shape so a later tool result can be attached safely.
    saved: dict[str, Any] = {"role": "assistant", "content": raw_text}
    if calls:
        saved["tool_calls"] = [
            {"id": item.call_id, "type": "function",
             "function": {"name": item.name,
                          "arguments": json.dumps(item.arguments, separators=(",", ":"))}}
            for item in calls
        ]
    return NormalizedReply(
        role=spec.role, requested_model=spec.model_id,
        reported_model=reported if isinstance(reported, str) else None,
        text=raw_text or "", tool_calls=tuple(calls),
        input_tokens=_token(usage, "prompt_tokens"),
        output_tokens=_token(usage, "completion_tokens"),
        total_tokens=_token(usage, "total_tokens"),
        continuation_items=(saved,),
    )


def parse_reply(spec: ModelSpec, response: Any) -> NormalizedReply:
    if spec.api_style == "responses":
        return _response_reply(spec, response)
    if spec.api_style == "chat_completions":
        return _chat_reply(spec, response)
    raise ValueError("Unsupported API style.")


def make_tool_result(api_style: APIStyle, call_id: str, output: str) -> dict[str, Any]:
    """Represent *already executed* tool output; does not execute tools."""
    if not isinstance(call_id, str) or not call_id or not isinstance(output, str):
        raise ValueError("Tool response requires an ID and text output.")
    if api_style == "responses":
        return {"type": "function_call_output", "call_id": call_id, "output": output}
    if api_style == "chat_completions":
        return {"role": "tool", "tool_call_id": call_id, "content": output}
    raise ValueError("Unsupported API style.")
