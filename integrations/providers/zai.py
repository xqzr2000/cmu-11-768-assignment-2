"""Z.ai's OpenAI-compatible Chat Completions request builder (pure)."""

from typing import Any

from integrations.models import ModelSpec


def build(spec: ModelSpec, items: list[dict[str, Any]],
          tools: list[dict[str, Any]], schema: dict[str, Any] | None,
          max_output_tokens: int) -> dict[str, Any]:
    if schema is not None:
        raise ValueError("Z.ai is only a chart-making agent in this configuration.")
    # Items are already chat-formatted. A future controller must not mix them
    # with Responses-only function_call and function_call_output items.
    for item in items:
        if item.get("role") not in ("system", "user", "assistant", "tool"):
            raise ValueError("Z.ai requires chat-message-shaped input items.")
        if item.get("type") is not None:
            raise ValueError("Responses API items cannot be sent as chat messages.")
    request: dict[str, Any] = {
        "model": spec.model_id, "messages": items,
        "max_tokens": max_output_tokens, "stream": False,
    }
    if spec.model_id == "glm-5.3-flash":
        # 5.3 Flash always reasons; select low effort for the 512-token probe.
        # OpenAI SDK merges extra_body into the provider-native JSON payload.
        request["extra_body"] = {"reasoning_effort": "low"}
    if tools:
        request["tools"] = [
            {"type": "function", "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            }} for tool in tools
        ]
        request["tool_choice"] = "auto"
    return request
