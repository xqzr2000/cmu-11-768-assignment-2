"""One-model, one-request compatibility probe for Session 009.

Default invocation only builds and previews the request; it never reads keys,
constructs an HTTP client or executes model-suggested tool calls.
Live mode requires ALL THREE flags: --live --confirm-one-request
--approve-model EXACT_MODEL_ID. Use only after per-call user authorization.

Examples (OFFLINE ONLY):
    uv run python scripts/provider_compat_probe.py --role agent_a
    uv run python scripts/provider_compat_probe.py --role experimental_judge
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from integrations.judge import JUDGMENT_SCHEMA, decode_judgment, make_vision_input
from integrations.models import MODELS, ModelSpec, get_model
from integrations.providers import execute_one, preview_request

RELEASE = Path(__file__).resolve().parents[1]

# An inert tool descriptor: a compatibility check is NOT a shell command run.
SHELL_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "run_shell",
    "description": "Request a shell command; this test never executes it.",
    "parameters": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
        "additionalProperties": False,
    },
}


def _test_png() -> bytes:
    """Create a small deterministic synthetic chart; no task files or labels."""
    image = Image.new("RGB", (240, 160), "white")
    draw = ImageDraw.Draw(image)
    draw.line((32, 15, 32, 128), fill="black", width=2)
    draw.line((32, 128, 218, 128), fill="black", width=2)
    draw.rectangle((67, 80, 105, 127), fill=(55, 110, 190))
    draw.rectangle((143, 32, 181, 127), fill=(55, 110, 190))
    draw.text((77, 132), "A", fill="black")
    draw.text((153, 132), "B", fill="black")
    draw.text((9, 5), "Y", fill="black")
    data = io.BytesIO()
    image.save(data, "PNG")
    return data.getvalue()


def build_case(spec: ModelSpec) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    """Return (input, inert tools, schema), without a network or credentials."""
    if MODELS.get(spec.role) != spec:
        raise ValueError("Unregistered model specification.")
    if spec.is_judge:
        prompt = (
            "You are checking a synthetic data visualization. The task was: "
            "plot two vertical bars A=1 and B=2 with readable labels. "
            "Input data.csv contains category,value\\nA,1\\nB,2. "
            "The synthetic trajectory states that a figure was rendered and saved. "
            "Inspect the PNG; return an errors array with only grounded evidence. "
            "Use an empty errors array if no specified issue is observed. "
            "Valid families: execution_failure, wrong_data, wrong_chart, hard_to_read."
        )
        return make_vision_input(prompt, _test_png()), [], JUDGMENT_SCHEMA
    return (
        [{"role": "user", "content": (
            "This is a function-calling compatibility check for a chart agent. "
            "Please call the run_shell function ONCE with command exactly "
            "'printf session009'. Do not execute the command yourself. "
            "You may reply in text if you cannot use functions."
        )}],
        [SHELL_TOOL],
        None,
    )


def _result_record(spec: ModelSpec, reply: Any) -> dict[str, Any]:
    """Minimal, privacy-preserving record. Tool arguments/text are not stored."""
    record: dict[str, Any] = {
        "status": "completed",
        "role": spec.role,
        "provider": spec.provider,
        "requested_model": spec.model_id,
        "reported_model": reply.reported_model,
        "api_style": spec.api_style,
        "tool_call_count": len(reply.tool_calls),
        "tool_names": [call.name for call in reply.tool_calls],
        "expected_tool_called": any(call.name == "run_shell" for call in reply.tool_calls),
        "usage": {
            "input_tokens": reply.input_tokens,
            "output_tokens": reply.output_tokens,
            "total_tokens": reply.total_tokens,
        },
        "retries": 0,
        "model_proposed_commands_executed": 0,
        "official_qwen_equivalent": False,
    }
    if not spec.is_judge:
        record["tool_call_compatibility"] = record["expected_tool_called"]
    if spec.is_judge:
        verdicts = decode_judgment(reply)
        record["schema_valid"] = True
        record["judgment_families"] = [item["family"] for item in verdicts]
        # A synthetic schema probe is not evidence of judge accuracy.
        record["accuracy_evaluated"] = False
    return record


def _write_new(path: Path, data: dict[str, Any]) -> None:
    """Create a new ignored JSON file, never overwrite a previous attempt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=tuple(MODELS))
    parser.add_argument("--live", action="store_true",
                        help="ENABLE one API request (requires two further approvals)")
    parser.add_argument("--confirm-one-request", action="store_true")
    parser.add_argument("--approve-model",
                        help="Repeat the exact requested model ID for one live request")
    args = parser.parse_args(argv)
    spec = get_model(args.role)
    items, tools, schema = build_case(spec)

    if not args.live and not args.confirm_one_request and args.approve_model is None:
        summary = preview_request(spec, items, tools=tools, schema=schema)
        summary["probe"] = "synthetic_schema" if spec.is_judge else "inert_function_call"
        summary["live_approval_required"] = True
        print(json.dumps(summary, indent=2))
        return

    if not (args.live and args.confirm_one_request and args.approve_model == spec.model_id):
        parser.error("Live mode requires --live --confirm-one-request and "
                     f"--approve-model {spec.model_id}; no request was sent")

    destination = RELEASE / "output" / f"provider_compat_{spec.role}.json"
    if destination.exists():
        parser.error("A saved result already exists for this role. "
                     "No request sent; inspect the existing result instead.")
    from dotenv import load_dotenv

    load_dotenv()
    if not os.getenv(spec.key_env):
        # Accept Codespaces secrets or ignored local .env without showing values.
        parser.error(f"Missing {spec.key_env} environment secret; no request sent")

    try:
        reply = execute_one(spec, items, tools=tools, schema=schema,
                            live=True, confirm_one_request=True)
        result = _result_record(spec, reply)
    except Exception as exc:
        # Never print provider messages, raw prompts, tool arguments or credentials.
        # A failed request may still have been billed: no automatic retries.
        result = {
            "status": "failed",
            "role": spec.role,
            "provider": spec.provider,
            "requested_model": spec.model_id,
            "error_type": type(exc).__name__,
            "one_request_may_have_been_billed": True,
            "retries": 0,
        }
    _write_new(destination, result)
    print(json.dumps({"saved": str(destination.relative_to(RELEASE)), **result}, indent=2))
    if result["status"] != "completed":
        raise SystemExit("Compatibility probe failed. Do not retry without new approval.")


if __name__ == "__main__":
    main()
