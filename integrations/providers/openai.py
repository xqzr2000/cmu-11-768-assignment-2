"""OpenAI Responses API request preparation (pure, no SDK client creation)."""

from typing import Any

from integrations.models import ModelSpec


def build(spec: ModelSpec, items: list[dict[str, Any]],
          tools: list[dict[str, Any]], schema: dict[str, Any] | None,
          max_output_tokens: int) -> dict[str, Any]:
    options: dict[str, Any] = {
        "model": spec.model_id, "input": items,
        "max_output_tokens": max_output_tokens, "store": False,
    }
    if tools:
        if spec.is_judge:
            raise ValueError("The experimental judge does not request shell tools.")
        options["tools"] = tools
        options["tool_choice"] = "auto"
    if schema is not None:
        if not spec.is_judge:
            raise ValueError("Only the experimental judge accepts a judgment schema.")
        options["text"] = {
            "format": {"type": "json_schema", "name": "viz_error_families",
                       "schema": schema, "strict": True}
        }
    elif spec.is_judge:
        raise ValueError("The experimental judge requires a structured response schema.")
    return options
