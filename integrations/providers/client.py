"""Offline-first dispatch and optional one-call transport.

Nothing here automatically executes tools, contacts a network during import,
runs multiple steps, retries, or reads human labels. Explicit live consent and
the provider-specific credential are required before constructing an API client.
"""

from __future__ import annotations

import os
from typing import Any

from integrations.models import MODELS, ModelSpec
from . import deepseek, openai as openai_adapter, zai
from .base import NormalizedReply, parse_reply

MAX_OUTPUT_TOKENS = 512
TIMEOUT_SECONDS = 60.0


def _validate_tools(tools: list[dict[str, Any]]) -> None:
    names: list[str] = []
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("type") != "function":
            raise ValueError("Only explicitly declared function tools are supported.")
        name, description, params = (tool.get("name"), tool.get("description"),
                                     tool.get("parameters"))
        if not isinstance(name, str) or not name:
            raise ValueError("Tool needs a function name.")
        if not isinstance(description, str) or not description:
            raise ValueError("Tool needs a description.")
        if not isinstance(params, dict) or params.get("type") != "object":
            raise ValueError("Tool parameters must be a JSON object schema.")
        names.append(name)
    if len(set(names)) != len(names):
        raise ValueError("Tool names must be unique.")


def prepare_request(
    spec: ModelSpec, items: list[dict[str, Any]], *,
    tools: list[dict[str, Any]] | None = None,
    schema: dict[str, Any] | None = None,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
) -> dict[str, Any]:
    """Build one provider-native request; no SDK or credential is accessed."""
    if not isinstance(spec, ModelSpec) or MODELS.get(spec.role) != spec:
        raise ValueError("Unregistered model/provider configuration.")
    if not isinstance(items, list) or not items or not all(
        isinstance(x, dict) for x in items
    ):
        raise ValueError("Input must be a nonempty list of message/item objects.")
    if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= MAX_OUTPUT_TOKENS:
        raise ValueError("Output limit exceeds the offline-defined cap.")
    function_tools = tools if tools is not None else []
    if not isinstance(function_tools, list):
        raise ValueError("Tools must be a list.")
    _validate_tools(function_tools)
    if spec.provider == "openai" and spec.api_style == "responses":
        return openai_adapter.build(spec, items, function_tools, schema, max_output_tokens)
    if spec.provider == "deepseek" and spec.api_style == "responses":
        return deepseek.build(spec, items, function_tools, schema, max_output_tokens)
    if spec.provider == "zai" and spec.api_style == "chat_completions":
        return zai.build(spec, items, function_tools, schema, max_output_tokens)
    raise ValueError("Unsupported provider and API combination.")


def preview_request(spec: ModelSpec, items: list[dict[str, Any]], *,
                    tools: list[dict[str, Any]] | None = None,
                    schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return safe metadata only; never return raw prompt, image, or secrets."""
    request = prepare_request(spec, items, tools=tools, schema=schema)
    return {
        "mode": "offline",
        "role": spec.role,
        "provider": spec.provider,
        "model_requested": request["model"],
        "api_style": spec.api_style,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "input_items": len(items),
        "function_tool_names": [t["name"] for t in tools or []],
        "structured_judgment": schema is not None,
        "network_requests": 0,
        "official_qwen_equivalent": False,
    }


def execute_one(
    spec: ModelSpec, items: list[dict[str, Any]], *,
    tools: list[dict[str, Any]] | None = None,
    schema: dict[str, Any] | None = None,
    live: bool = False,
    confirm_one_request: bool = False,
    client: Any | None = None,
) -> NormalizedReply:
    """Perform at most one explicitly authorized completion, with no retries.

    The client argument enables offline tests with a mock transport, but NEVER
    bypasses approval or the requirement that the corresponding key is set.
    The returned function calls are inert descriptions only.
    """
    if not (live and confirm_one_request):
        raise PermissionError("A live request requires both explicit opt-in flags.")
    request = prepare_request(spec, items, tools=tools, schema=schema)
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ.get(spec.key_env)
    if not key:
        raise RuntimeError(f"Missing {spec.key_env}; no request was sent.")
    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=key, base_url=spec.base_url,
                        timeout=TIMEOUT_SECONDS, max_retries=0)
    if spec.api_style == "responses":
        response = client.responses.create(**request)
    else:
        response = client.chat.completions.create(**request)
    # Failed/incomplete/malformed responses never become 'acceptable'.
    return parse_reply(spec, response)
