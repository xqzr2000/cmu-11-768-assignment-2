"""Separate experimental Terra judge: image request and strict local decoding.

Not wired to validator.solution.validate, not a replacement for course Qwen.
Human labels are not read and evidence/labels are never included automatically.
"""

from __future__ import annotations

import base64
import io
import json
from typing import Any

from PIL import Image

from integrations.models import get_model
from integrations.providers.base import AdapterProtocolError, NormalizedReply

FAMILIES = ("execution_failure", "wrong_data", "wrong_chart", "hard_to_read")
JUDGMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "family": {"type": "string", "enum": list(FAMILIES)},
                    "evidence": {"type": "string"},
                },
                "required": ["family", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["errors"],
    "additionalProperties": False,
}


def make_vision_input(prompt: str, png_bytes: bytes) -> list[dict[str, Any]]:
    """Encode an existing PNG; never produce a graph or load reference labels."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Judge prompt must be nonempty.")
    if not isinstance(png_bytes, bytes) or not png_bytes or len(png_bytes) > 10_000_000:
        raise ValueError("Image must be PNG bytes no larger than 10 MB.")
    try:
        with Image.open(io.BytesIO(png_bytes)) as image:
            if image.format != "PNG":
                raise ValueError("Figure is not a PNG.")
            image.verify()
        with Image.open(io.BytesIO(png_bytes)) as image:
            image.load()
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Figure is not a complete decodable PNG.") from exc
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return [{"role": "user", "content": [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": f"data:image/png;base64,{encoded}"},
    ]}]


def decode_judgment(reply: NormalizedReply) -> list[dict[str, str]]:
    """Reject incomplete, duplicate, or semantically invalid family lists."""
    if reply.role != get_model("experimental_judge").role or reply.tool_calls:
        raise AdapterProtocolError("Not a plain structured Terra judge response.")
    try:
        data = json.loads(reply.text)
    except (ValueError, TypeError) as exc:
        raise AdapterProtocolError("Judge result is not valid JSON.") from exc
    if not isinstance(data, dict) or set(data) != {"errors"}:
        raise AdapterProtocolError("Judge result requires only the errors key.")
    values = data["errors"]
    if not isinstance(values, list):
        raise AdapterProtocolError("Judge errors must be an array.")
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in values:
        if not isinstance(item, dict) or set(item) != {"family", "evidence"}:
            raise AdapterProtocolError("Judge error item shape is invalid.")
        family, evidence = item["family"], item["evidence"]
        if family not in FAMILIES or family in seen:
            raise AdapterProtocolError("Unknown or duplicated judge family.")
        if not isinstance(evidence, str) or not evidence.strip():
            raise AdapterProtocolError("Judge evidence must be a nonempty string.")
        seen.add(family)
        result.append({"family": family, "evidence": evidence.strip()})
    if "execution_failure" in seen and len(seen) != 1:
        raise AdapterProtocolError("Terminal execution_failure must appear alone.")
    return result
