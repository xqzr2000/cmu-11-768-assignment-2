"""Offline-first two-case pilot for Z.ai vision evaluation.

Independent learning study ONLY. The course requires the different
Qwen/Qwen3-VL-30B-A3B-Instruct-FP8 checkpoint for official grading.

Dry run is the default. Live mode requires two flags, one explicitly selected
seed case, and can issue at most three chat completions (no automatic retries).
Official human labels are never read or sent by either dry run or live mode;
the separate --compare mode reads them only AFTER predictions exist.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from validator import solution
from validator.prediction import ERROR_FAMILIES, Prediction, PredictionFile
from validator.runner import Run

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
RUN_IDS = ("004", "008")  # Pilot selection only, NEVER error-label logic.
MODEL = "glm-4.6v-flash"
BASE_URL = "https://api.z.ai/api/paas/v4/"
MAX_COMPLETIONS = 3
MAX_OUTPUT_TOKENS = 250
MAX_PROMPT_CHARS = 50_000
TIMEOUT_SECONDS = 60.0


def load_case(run_id: str, root: Path = ROOT) -> Run:
    if run_id not in RUN_IDS:
        raise ValueError("This pilot allows only seed runs 004 and 008.")
    return Run.load(root / "artifacts" / run_id, root)


def prediction_path(run_id: str, root: Path = ROOT) -> Path:
    return root / "output" / f"session005_zai_{run_id}_predictions.json"


def metadata_path(run_id: str, root: Path = ROOT) -> Path:
    return root / "output" / f"session005_zai_{run_id}_metadata.json"


def describe_case(run: Run) -> dict[str, Any]:
    """Construct exact baseline requests with fake replies; never use a network."""
    outgoing: list[dict[str, Any]] = []

    def capture(messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        if len(outgoing) >= MAX_COMPLETIONS:
            raise RuntimeError("The pilot must create exactly three semantic requests.")
        parts = messages[0]["content"]
        if [part["type"] for part in parts] != ["text", "image_url"]:
            raise ValueError("The baseline did not prepare the expected text + image request.")
        image_url = parts[1]["image_url"]["url"]
        if not image_url.startswith("data:image/png;base64,"):
            raise ValueError("The multimodal request does not contain an embedded PNG.")
        prompt_chars = len(parts[0]["text"])
        if prompt_chars > MAX_PROMPT_CHARS:
            raise ValueError("Pilot prompt exceeds the conservative character limit.")
        outgoing.append({
            "prompt_chars": prompt_chars,
            "image_bytes": len(base64.b64decode(image_url.split(",", 1)[1])),
            "max_tokens": kwargs.get("max_tokens"),
        })
        return {"choices": [{"message": {"content": "NO: synthetic offline-only response"}}]}

    with patch("validator.baseline.complete", side_effect=capture):
        errors = solution.validate(run)

    if errors or len(outgoing) != MAX_COMPLETIONS:
        raise ValueError("Pilot expects a structurally valid PNG and exactly three requests.")
    if run.figure is None:
        raise ValueError("Pilot requires a final PNG.")
    with Image.open(run.figure) as image:
        dimensions = list(image.size)

    return {
        "run_id": run.run_id,
        "mode": "offline_preview",
        "model": MODEL,
        "network_requests": 0,
        "planned_completion_requests": len(outgoing),
        "figure_dimensions": dimensions,
        "figure_bytes": run.figure.stat().st_size,
        "instruction_chars": len(run.instructions),
        "trajectory_messages": len(run.messages),
        "input_files": [
            {"name": name, "bytes": path.stat().st_size}
            for name, path in sorted(run.inputs.items())
        ],
        "requests": outgoing,
        "source_includes": ["task instructions", "agent trajectory", "input file contents", "figure PNG"],
        "human_labels_sent": False,
        "official_qwen_equivalent": False,
    }


def send_one_run(
    run: Run, client: Any, *, max_completions: int = MAX_COMPLETIONS
) -> tuple[Prediction, dict[str, Any]]:
    """Reuse solution's prompts, with a hard cap and no vLLM-only fallback."""
    attempted = 0
    usage_records: list[dict[str, Any]] = []

    def complete(messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        nonlocal attempted
        if attempted >= max_completions:
            raise RuntimeError("Completion budget exhausted; no further request sent.")
        parts = messages[0]["content"]
        if [part["type"] for part in parts] != ["text", "image_url"]:
            raise ValueError("Expected the baseline's image and text content.")
        if len(parts[0]["text"]) > MAX_PROMPT_CHARS:
            raise ValueError("Prompt is too long for this pilot.")
        attempted += 1  # Count before the call, including transport failures.
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=False,
            max_tokens=min(kwargs.get("max_tokens", MAX_OUTPUT_TOKENS), MAX_OUTPUT_TOKENS),
            temperature=0,
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = response.choices[0].message.content if response.choices else None
        if not isinstance(content, str) or not re.match(
            r"^\s*(YES|NO)\b", content, flags=re.IGNORECASE
        ):
            raise ValueError("Vision reply must start with YES or NO; result not scored.")
        usage = response.usage
        usage_records.append({
            "model_reported": response.model,
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        })
        return response.model_dump()

    # The baseline's overflow fallback calls /tokenize on a vLLM endpoint that
    # Z.ai does not promise to provide. Fail immediately rather than silently
    # switching to some other configured model/server or retrying on overflow.
    with patch("validator.baseline.complete", side_effect=complete), patch(
        "validator.baseline._context_overflow", return_value=False
    ):
        errors = solution.validate(run)

    if attempted != MAX_COMPLETIONS:
        raise RuntimeError("The successful pilot must make exactly three completions.")
    prediction = Prediction(run_id=run.run_id, errors=errors)
    meta = {
        "provider": "Z.ai",
        "model_requested": MODEL,
        "model_reported": sorted({x["model_reported"] for x in usage_records}),
        "completion_attempts": attempted,
        "request_usage": usage_records,
        "human_labels_sent": False,
        "official_qwen_equivalent": False,
        "pilot_only": True,
    }
    return prediction, meta


def write_one_run(run_id: str, prediction: Prediction, meta: dict[str, Any], root: Path = ROOT) -> None:
    """Store predictions for one run only. Never overwrite automatically."""
    out = prediction_path(run_id, root)
    manifest = metadata_path(run_id, root)
    if out.exists() or manifest.exists():
        raise FileExistsError("Pilot output already exists; review it before any new API call.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        PredictionFile(predictions=[prediction]).model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    manifest.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def compare_one_run(run_id: str, root: Path = ROOT) -> dict[str, Any]:
    """Only this explicit post-hoc mode may read seed_labels.json."""
    file = PredictionFile.model_validate_json(prediction_path(run_id, root).read_text())
    if len(file.predictions) != 1 or file.predictions[0].run_id != run_id:
        raise ValueError("Expected exactly one prediction for the requested run.")
    from workflow.evaluate import LabelFile  # Never imported on inference path.

    label_file = LabelFile.model_validate_json((root / "seed_labels.json").read_text())
    reference = next((item for item in label_file.labels if item.run_id == run_id), None)
    if reference is None or reference.errors is None:
        raise ValueError("Human label for this run is missing.")
    predicted = {e.family.value for e in file.predictions[0].errors}
    expected = {e.family.value for e in reference.errors}
    return {
        "run_id": run_id,
        "model": MODEL,
        "predicted_families": sorted(predicted),
        "human_families": sorted(expected),
        "missed": sorted(expected - predicted),
        "false_alarms": sorted(predicted - expected),
        "family_matches": {family: (family in expected) == (family in predicted)
                           for family in ERROR_FAMILIES},
        "note": "Two selected examples are for debugging, not a reliable MCC estimate.",
        "official_qwen_equivalent": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", choices=RUN_IDS, help="One run to evaluate (004 or 008)")
    parser.add_argument("--live", action="store_true", help="Allow API requests")
    parser.add_argument("--confirm-three-requests", action="store_true",
                        help="Second opt-in to up to 3 model completions")
    parser.add_argument("--compare", action="store_true",
                        help="Offline only: compare a saved prediction to human labels")
    args = parser.parse_args(argv)

    if args.live != args.confirm_three_requests:
        parser.error("Live mode requires both --live and --confirm-three-requests.")
    if args.compare and args.live:
        parser.error("--compare is separate from --live and must never send data.")
    if (args.live or args.compare) and not args.run_id:
        parser.error("Live and compare modes require exactly one --run-id.")

    if args.compare:
        try:
            print(json.dumps(compare_one_run(args.run_id), indent=2))
            return 0
        except (OSError, ValueError) as error:
            print(json.dumps({"mode": "compare", "error_type": type(error).__name__}))
            return 2

    selected = (args.run_id,) if args.run_id else RUN_IDS
    try:
        plans = {rid: describe_case(load_case(rid)) for rid in selected}
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"mode": "offline", "error_type": type(error).__name__,
                          "network_requests": 0}))
        return 2
    if not args.live:
        print(json.dumps({"mode": "offline", "plans": plans}, indent=2))
        return 0

    # No connection before all required checks and an existing-output check.
    output = prediction_path(args.run_id)
    metadata = metadata_path(args.run_id)
    if output.exists() or metadata.exists():
        print(json.dumps({"mode": "live", "error": "Existing output; no API calls."}))
        return 2
    load_dotenv(dotenv_path=ROOT / ".env")
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print(json.dumps({"mode": "live", "error": "ZAI_API_KEY not configured."}))
        return 2

    client = OpenAI(
        base_url=BASE_URL,
        api_key=api_key,
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )
    try:
        prediction, meta = send_one_run(load_case(args.run_id), client)
        write_one_run(args.run_id, prediction, meta)
    except Exception as error:
        # Never print raw provider payloads, CSV, or accidental secret strings.
        print(json.dumps({
            "mode": "live",
            "run_id": args.run_id,
            "success": False,
            "error_type": type(error).__name__,
            "http_status": getattr(error, "status_code", None),
            "automatic_retries": 0,
            "max_completion_attempts": MAX_COMPLETIONS,
        }, indent=2))
        return 2

    print(json.dumps({
        "mode": "live",
        "run_id": args.run_id,
        "success": True,
        "model": MODEL,
        "predicted_families": [e.family.value for e in prediction.errors],
        "completion_attempts": meta["completion_attempts"],
        "request_usage": meta["request_usage"],
        "predictions_file": str(prediction_path(args.run_id).relative_to(ROOT)),
        "metadata_file": str(metadata_path(args.run_id).relative_to(ROOT)),
        "human_labels_sent": False,
        "official_qwen_equivalent": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
