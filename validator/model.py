"""The judge model, reached through an OpenAI-compatible endpoint.

`complete` takes chat messages and returns the whole response, so a question can
be one turn or several, with or without a figure attached. ASSIGNMENT.md shows
how to put an image in a message.
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI

load_dotenv()

#: Stable alias exposed by the canonical student/staff validator deployment.
MODEL = os.getenv("VALIDATOR_MODEL", "validator")


def _client() -> OpenAI:
    base_url = os.getenv("VALIDATOR_BASE_URL")
    api_key = os.getenv("VALIDATOR_API_KEY")
    if not api_key and base_url and "api.openai.com" in base_url:
        # Reuse the OPENAI_API_KEY Codespaces secret rather than copying it into .env.
        api_key = os.getenv("OPENAI_API_KEY")
    missing = [
        name
        for name, value in {
            "VALIDATOR_BASE_URL": base_url,
            "VALIDATOR_API_KEY": api_key,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"missing {', '.join(missing)}; copy .env.example to .env and fill in your deployment"
        )
    return OpenAI(base_url=base_url, api_key=api_key, timeout=300, max_retries=3)


#: Optional settings for hosted OpenAI judges (e.g. gpt-6.1-terra). All default
#: to the original behaviour, so the course's vLLM endpoint is unaffected.
#:   VALIDATOR_REASONING_EFFORT  e.g. "none" or "low"; sent as reasoning_effort
#:   VALIDATOR_SERVICE_TIER      e.g. "flex" (half price, slower)
REASONING_EFFORT = os.getenv("VALIDATOR_REASONING_EFFORT") or None
SERVICE_TIER = os.getenv("VALIDATOR_SERVICE_TIER") or None

# Parameter fixes learned from the server's 400 responses, kept for the process.
_RENAME_MAX_TOKENS = False
_DROP_TEMPERATURE = False


#: Set VALIDATOR_USAGE_LOG=output/judge_usage.jsonl to record token usage per call.
USAGE_LOG = os.getenv("VALIDATOR_USAGE_LOG") or None


def _log_usage(result: dict[str, Any]) -> None:
    if not USAGE_LOG:
        return
    usage = result.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
    record = {
        "model": result.get("model"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "cached_tokens": cached,
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": details.get("reasoning_tokens"),
    }
    path = Path(USAGE_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(record) + "\n")


def _adapt(options: dict[str, Any]) -> dict[str, Any]:
    options = dict(options)
    if _RENAME_MAX_TOKENS and "max_tokens" in options:
        options["max_completion_tokens"] = options.pop("max_tokens")
    if _DROP_TEMPERATURE:
        options.pop("temperature", None)
    return options


def complete(messages: list[dict[str, Any]], **generation: Any) -> dict[str, Any]:
    global _RENAME_MAX_TOKENS, _DROP_TEMPERATURE
    options: dict[str, Any] = {"temperature": 0, **generation}
    if REASONING_EFFORT:
        options.setdefault("reasoning_effort", REASONING_EFFORT)
    if SERVICE_TIER:
        options.setdefault("service_tier", SERVICE_TIER)
    client = _client()
    # Newer OpenAI models reject `max_tokens` and non-default `temperature`.
    # Learn each fix from the 400 once, instead of hard-coding one provider.
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,  # type: ignore[arg-type] - kept flexible for image parts
                **_adapt(options),
            )
            result = response.model_dump()
            _log_usage(result)
            return result
        except BadRequestError as error:
            message = str(error)
            if "max_tokens" in message and "max_completion_tokens" in message and not _RENAME_MAX_TOKENS:
                _RENAME_MAX_TOKENS = True
            elif "temperature" in message and not _DROP_TEMPERATURE:
                _DROP_TEMPERATURE = True
            else:
                raise
    raise RuntimeError("judge request kept failing after parameter adaptation")


def _tokenizer_request(endpoint: str, **body: Any) -> dict[str, Any]:
    # vLLM's tokenizer routes live beside /v1, not inside it. Keep any proxy
    # path prefix and use the same authenticated client as chat completions.
    client = _client()
    root = str(client.base_url).rstrip("/").removesuffix("/v1")
    return client.post(
        f"{root}/{endpoint}", cast_to=dict[str, Any], body={"model": MODEL, **body}
    )


def tokenize(text: str) -> dict[str, Any]:
    """Return token IDs and max_model_len from the deployed vLLM server."""
    return _tokenizer_request("tokenize", prompt=text, add_special_tokens=False)


def detokenize(tokens: list[int]) -> str:
    return _tokenizer_request("detokenize", tokens=tokens)["prompt"]
