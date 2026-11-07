"""DeepSeek stateless Responses API (pure request preparation).

Do not pass OpenAI-only state IDs: DeepSeek requires a complete history on each
turn. The runner/controller will be responsible for replaying that history.
"""

from typing import Any

from integrations.models import ModelSpec


def build(spec: ModelSpec, items: list[dict[str, Any]],
          tools: list[dict[str, Any]], schema: dict[str, Any] | None,
          max_output_tokens: int) -> dict[str, Any]:
    if schema is not None:
        raise ValueError("DeepSeek in this project is a chart-making agent, not judge.")
    request: dict[str, Any] = {
        "model": spec.model_id, "input": items,
        "max_output_tokens": max_output_tokens,
    }
    if tools:
        request["tools"] = tools
        request["tool_choice"] = "auto"
    return request
