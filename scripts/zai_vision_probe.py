"""One-request Z.ai vision probe with an offline-by-default preflight.

Independent learning experiment ONLY: GLM-4.6V-Flash is not the exact required
Qwen3-VL validator checkpoint. This script does not touch validator/model.py,
read seed labels, or run the official evaluator.

Offline mode creates a tiny synthetic bar chart in memory and validates the
request payload without network calls. Live mode requires TWO explicit flags.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw

MODEL = "glm-4.6v-flash"
BASE_URL = "https://api.z.ai/api/paas/v4/"
MAX_OUTPUT_TOKENS = 64
TIMEOUT_SECONDS = 45.0
PROMPT = (
    "Inspect the attached bar chart image. Which colored bar is visibly taller? "
    "Reply with exactly one word: BLUE or ORANGE."
)
EXPECTED = "BLUE"


def make_probe_png() -> bytes:
    """Generate our controlled test image; never read public seed figures."""
    image = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(image)
    draw.line([(25, 214), (230, 214)], fill="black", width=2)
    draw.rectangle((51, 54, 108, 213), fill=(24, 94, 207))
    draw.rectangle((146, 130, 203, 213), fill=(245, 132, 33))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def build_messages(png: bytes) -> list[dict[str, Any]]:
    """Use the OpenAI-compatible image_url data-URL message format."""
    encoded = base64.b64encode(png).decode("ascii")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encoded}"},
                },
            ],
        }
    ]


def is_correct(answer: str) -> bool:
    """Require an unambiguous answer instead of guessing from a long response."""
    return re.fullmatch(r"\s*BLUE[\s.!]*", answer, flags=re.IGNORECASE) is not None


def complete_one_request(client: Any, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Exactly one completion attempt; client must be created with retries=0."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=False,
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    if not response.choices or not isinstance(response.choices[0].message.content, str):
        raise ValueError("Vision provider did not return a text answer")
    answer = response.choices[0].message.content.strip()
    usage = response.usage
    return {
        "provider": "Z.ai",
        "model_requested": MODEL,
        "model_reported": response.model,
        "answer": answer[:240],
        "expected": EXPECTED,
        "vision_smoke_test_passed": is_correct(answer),
        "completion_attempts": 1,
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        },
        "official_qwen_equivalent": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline by default; a one-request Z.ai image probe needs explicit opt-in."
    )
    parser.add_argument("--live", action="store_true", help="Allow one Z.ai API request")
    parser.add_argument(
        "--confirm-one-request",
        action="store_true",
        help="Second explicit opt-in to one potentially rate-limited/billable request",
    )
    options = parser.parse_args(argv)
    if options.live != options.confirm_one_request:
        parser.error("live mode requires both --live and --confirm-one-request")

    # Use an explicit path: load_dotenv() without a path can fail under python -.
    load_dotenv(dotenv_path=Path.cwd() / ".env")
    key_available = bool(os.getenv("ZAI_API_KEY"))
    png = make_probe_png()
    messages = build_messages(png)

    if not options.live:
        print(
            json.dumps(
                {
                    "mode": "offline",
                    "model": MODEL,
                    "network_requests": 0,
                    "api_key_configured": key_available,
                    "image_size": [256, 256],
                    "image_bytes": len(png),
                    "message_parts": [part["type"] for part in messages[0]["content"]],
                    "expected_visual_answer": EXPECTED,
                    "official_qwen_equivalent": False,
                },
                indent=2,
            )
        )
        return 0

    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("Live probe cancelled: ZAI_API_KEY is not configured.")
        return 2

    # Do not change the base URL from user input: the key must only go to Z.ai.
    # Disable automatic retries: even a network failure must not silently
    # trigger multiple requests.
    try:
        client = OpenAI(
            base_url=BASE_URL,
            api_key=api_key,
            timeout=TIMEOUT_SECONDS,
            max_retries=0,
        )
        result = complete_one_request(client, messages)
    except Exception as error:
        # Error bodies and request payloads could contain sensitive content.
        # Print just the error class/status, not raw provider response bodies.
        status = getattr(error, "status_code", None)
        print(
            json.dumps(
                {"mode": "live", "success": False, "error_type": type(error).__name__,
                 "http_status": status, "max_completion_attempts": 1},
                indent=2,
            )
        )
        return 2

    print(json.dumps({"mode": "live", **result}, indent=2))
    return 0 if result["vision_smoke_test_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
