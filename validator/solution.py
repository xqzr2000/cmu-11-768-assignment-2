"""Student validator: artifact-gated execution check plus two structured judge calls.

Pipeline for one run:

1. execution_failure is decided from the artifact alone: a missing, non-PNG or
   undecodable figure.png is terminal; no model call. (Part 1, error type A:
   the baseline judged execution from the trajectory's story and both invented
   crashes for runs with a figure and passed runs without one.)
2. wrong_data / wrong_chart come from ONE requirement-checklist call. The judge
   lists every requirement in the instruction, tags it `data` or `design` using
   the official definitions, and marks it met / violated / unclear. A family is
   flagged only if a requirement of that kind is violated, so a colormap or a
   missing label can no longer turn into wrong_data. (Error type B: the
   baseline's per-family YES/NO questions answered YES for any problem.)
3. hard_to_read comes from a separate image-first call that only checks
   legibility of what is drawn, against the official checklist, and is told
   that missing or wrong elements are not readability problems.

Part 4 additions (motivated by the authored runs):
4. A third requirement kind, `legibility`, which never counts as wrong_chart:
   an instruction like "no labels may overlap" is a readability matter under
   the official taxonomy, and the judge had filed it as a design violation.
5. The readability call first inventories every legend / annotation / text
   box and what lies beneath it (any box over data or text is hard_to_read by
   the official definition), and it sees the four quadrants enlarged, so a
   legend clipping a band edge or text cut at the image border is visible.

The judge sees the instruction, input files, a compact transcript (commands
and truncated outputs) and the figure, plus measured image facts (pixel size,
DPI metadata) so size/DPI requirements are checked against facts, not guesses.
"""

from __future__ import annotations

import base64
import io
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from validator.model import complete
from validator.prediction import Error, ErrorFamily
from validator.runner import Run

MAX_INPUT_CHARS_PER_FILE = 20_000
MAX_TRANSCRIPT_CHARS = 60_000
MAX_OUTPUT_CHARS = 1_500
MAX_COMPLETION_TOKENS = 6_000
JSON_RETRIES = 1

# --------------------------------------------------------------------- execution


def _execution_error(evidence: str) -> list[Error]:
    return [Error(family=ErrorFamily.EXECUTION_FAILURE, evidence=evidence)]


def judge_execution(run: Run) -> list[Error]:
    """Missing or undecodable figure.png -> terminal execution_failure. No model."""
    figure: Path | None = run.figure
    if figure is None:
        return _execution_error("No final figure.png was produced.")
    if not figure.is_file():
        return _execution_error("The final figure.png is missing or is not a file.")
    try:
        with Image.open(figure) as image:
            if image.format != "PNG":
                return _execution_error(
                    f"The final figure.png is not a PNG (detected {image.format or 'unknown'})."
                )
            image.verify()
        with Image.open(figure) as image:
            image.load()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        return _execution_error(
            f"The final figure.png cannot be decoded as a complete PNG ({type(exc).__name__})."
        )
    return []


# ------------------------------------------------------------------- evidence


def image_facts(figure: Path) -> str:
    """Measured facts the judge should not have to estimate."""
    with Image.open(figure) as image:
        width, height = image.size
        dpi = image.info.get("dpi")
        extrema = image.convert("L").getextrema()
    facts = [f"pixel size {width}x{height}"]
    if dpi:
        x_dpi = round(float(dpi[0]))
        facts.append(f"DPI metadata {x_dpi}")
        facts.append(f"implied figure size {width / x_dpi:.2f}x{height / x_dpi:.2f} inches")
    else:
        facts.append("no DPI metadata")
    if extrema[0] == extrema[1]:
        facts.append("the image is a single flat colour (blank)")
    return "; ".join(facts)


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return "" if content is None else str(content)


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n[... {len(text) - limit} characters omitted ...]\n{text[-half:]}"


def transcript(messages: list[dict]) -> str:
    """Readable trajectory: agent text and commands in full, tool output clipped."""
    lines: list[str] = []
    for message in messages:
        role = message.get("role", "?")
        if role == "system":
            continue
        if role == "user" and not lines:
            continue  # the first user turn repeats the task, shown separately
        content = _text(message.get("content")).strip()
        if role == "tool":
            try:
                payload = json.loads(content)
                content = (f"returncode={payload.get('returncode')}\n"
                           f"{payload.get('output', '')}")
            except (ValueError, AttributeError):
                pass
            lines.append(f"[tool output]\n{_clip(content.strip(), MAX_OUTPUT_CHARS)}")
            continue
        if role == "exit":
            status = (message.get("extra") or {}).get("exit_status")
            lines.append(f"[run ended: {status}]")
            continue
        if content:
            lines.append(f"[{role}]\n{content}")
        for call in message.get("tool_calls") or []:
            arguments = (call.get("function") or {}).get("arguments", "")
            try:
                command = json.loads(arguments).get("command", arguments)
            except (ValueError, AttributeError):
                command = arguments
            lines.append(f"[{role} runs]\n$ {command}")
    return _clip("\n\n".join(lines), MAX_TRANSCRIPT_CHARS)


def input_files(run: Run) -> str:
    if not run.inputs:
        return "(none)"
    return "\n\n".join(
        f"--- {name} ---\n{_clip(path.read_text(errors='replace'), MAX_INPUT_CHARS_PER_FILE)}"
        for name, path in run.inputs.items()
    )


def _image_part(figure: Path) -> dict[str, Any]:
    encoded = base64.b64encode(figure.read_bytes()).decode()
    return {"type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encoded}", "detail": "high"}}


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in judge reply")
    return json.loads(text[start:end + 1])


def _ask_json(content: list[dict[str, Any]], schema_name: str,
              schema: dict[str, Any]) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [{"role": "user", "content": content}]
    last_error: Exception | None = None
    for _ in range(JSON_RETRIES + 1):
        response = complete(
            messages,
            max_tokens=MAX_COMPLETION_TOKENS,
            response_format={"type": "json_schema", "json_schema": {
                "name": schema_name, "schema": schema, "strict": True}},
        )
        reply = response["choices"][0]["message"].get("content") or ""
        try:
            return _parse_json(reply)
        except (ValueError, json.JSONDecodeError) as error:
            last_error = error
            messages = messages + [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": "That was not valid JSON for the schema. "
                                            "Reply with the JSON object only."},
            ]
    raise ValueError(f"judge did not return valid JSON: {last_error}")


# ---------------------------------------------------------- data and chart design

DATA_DEFINITION = """\
`data` requirements are about WHAT is plotted: which values, series, categories,
groups, columns, rows, subsets or filters; aggregation, scaling, normalisation
and formulas; the range or grid a function is sampled on; which dimension of
the data each encoding carries (bubble size, colour value, error bar); and the
ORDER of points, bars, categories or sequences, including requested sorting
and which panel shows which data."""

DESIGN_DEFINITION = """\
`design` requirements are about HOW it is drawn: chart type and projection
(bar vs line, stacked vs grouped, horizontal vs vertical, 3D, polar, contour,
twin axes, inset); layout (number and arrangement of subplots, figure size,
DPI, shared axes); axes (labels, exact title and label text, limits, scale,
ticks, tick labels and rotation, spines, grid); legend, colour bar,
annotations, value labels, rendered formulas, shaded regions; style (colormap,
line style, marker, named colours, fills, whiskers, connectors). A required
title or axis label that is entirely outside the saved image counts as missing
(design). Axis limits that cut off requested data are a design violation."""

CHECKLIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement": {"type": "string"},
                    "kind": {"type": "string", "enum": ["data", "design", "legibility"]},
                    "status": {"type": "string", "enum": ["met", "violated", "unclear"]},
                    "evidence": {"type": "string"},
                },
                "required": ["requirement", "kind", "status", "evidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["requirements"],
    "additionalProperties": False,
}


def checklist_prompt(run: Run, facts: str) -> str:
    return f"""You are auditing the output of a data-visualisation agent.

Make a checklist of EVERY requirement stated or clearly implied by the task
instruction below, one item per checkable requirement, then check each one
against the rendered figure (attached). Use the agent's code, the input files
and the image facts as supporting evidence for what values were plotted, but
judge the figure that was actually saved.

Tag each requirement with exactly one kind:
{DATA_DEFINITION}
{DESIGN_DEFINITION}
`legibility` requirements ask for text or marks to be readable: labels fully
visible, not overlapping, large enough, legible contrast. List them, but they
never count as design violations; a separate reviewer judges readability.

Status: `violated` only when the figure clearly fails that requirement and you
can say how; `met` when it is satisfied; `unclear` when the image does not let
you tell. Evidence must be specific (what is drawn vs what was asked).
Do not add requirements the instruction does not make, and never mark a
design requirement violated because of a legibility problem (overlapping or
clipped text, low contrast): tag such requirements `legibility` instead.

TASK INSTRUCTION:
{run.instructions}

IMAGE FACTS (measured from figure.png): {facts}

INPUT FILES:
{input_files(run)}

AGENT TRANSCRIPT (commands and clipped outputs):
{transcript(run.messages)}
"""


def judge_data_and_chart(run: Run) -> list[Error]:
    assert run.figure is not None
    content = [
        {"type": "text", "text": checklist_prompt(run, image_facts(run.figure))},
        _image_part(run.figure),
    ]
    result = _ask_json(content, "requirement_checklist", CHECKLIST_SCHEMA)
    errors: list[Error] = []
    for kind, family in (("data", ErrorFamily.WRONG_DATA), ("design", ErrorFamily.WRONG_CHART)):
        violated = [item for item in result.get("requirements", [])
                    if item.get("kind") == kind and item.get("status") == "violated"]
        if violated:
            evidence = " ".join(
                f"{item['requirement'].rstrip('.')}: {item['evidence'].strip()}"
                for item in violated
            )
            errors.append(Error(family=family, evidence=evidence))
    return errors


# ------------------------------------------------------------------ readability

READABILITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "overlays": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "element": {"type": "string"},
                    "covers": {"type": "string", "enum": [
                        "empty_space_or_gridlines", "data", "text_or_labels"]},
                    "detail": {"type": "string"},
                },
                "required": ["element", "covers", "detail"],
                "additionalProperties": False,
            },
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": [
                        "clipped_text", "overlapping_text", "element_covers_content",
                        "low_contrast_or_invisible", "indistinguishable_series",
                        "squeezed_layout"]},
                    "where": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["minor", "major"]},
                },
                "required": ["category", "where", "description", "severity"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["overlays", "issues"],
    "additionalProperties": False,
}

READABILITY_PROMPT = """You are checking whether a rendered chart is legible.
Look closely at the whole image, including its edges. Report only these
problems with what IS drawn:

- clipped_text: a title, axis label, tick label or annotation partly cut off by
  the edge of the image.
- overlapping_text: tick labels, annotations, titles or labels overlapping each
  other, or markers drawn on top of the text that labels them.
- element_covers_content: a legend, annotation or text box hiding data, labels
  or other text (a legend over empty space is fine).
- low_contrast_or_invisible: text or value labels with very low contrast
  against their background (e.g. white on white or pale yellow), or a series
  drawn in the background colour, with zero width, or otherwise invisible.
- indistinguishable_series: two series or groups that must be told apart drawn
  with the same or nearly the same colour, line style and marker; a colormap
  that merges values that should look different.
- squeezed_layout: data, boxes or panels crushed into an unreadable sliver by
  axis limits or by overlapping axes.

First fill `overlays`: list EVERY legend, colour bar, annotation, text box and
value label that sits inside a plotting area, and say exactly what is beneath
it. Look closely: a legend box that hides part of a line, a band, a bar top or
some markers covers `data`, even if most of the area under it is empty.
Use `empty_space_or_gridlines` only when nothing but background or gridlines
is hidden. Then fill `issues`.

Severity `major` means a reader cannot read that element, or can only with real
difficulty; `minor` means it is slightly cramped but still readable.
Missing elements, wrong chart types, wrong colours or wrong values are NOT
readability problems; ignore them. A clean chart has no issues.

You get the whole image first, then its four quadrants enlarged (top-left,
top-right, bottom-left, bottom-right) so small text and edges are visible.

For context, the chart was meant to show:
{instructions}

IMAGE FACTS: {facts}
"""


def quadrant_parts(figure: Path) -> list[dict[str, Any]]:
    """The four quadrants, enlarged so their long side is about 1600 px."""
    parts = []
    with Image.open(figure) as image:
        image = image.convert("RGB")
        width, height = image.size
        scale = max(1.0, min(2.5, 1600 / max(width / 2, height / 2)))
        for left, top in ((0, 0), (width // 2, 0), (0, height // 2), (width // 2, height // 2)):
            crop = image.crop((left, top, left + (width + 1) // 2, top + (height + 1) // 2))
            if scale > 1.0:
                crop = crop.resize((round(crop.width * scale), round(crop.height * scale)),
                                   Image.LANCZOS)
            buffer = io.BytesIO()
            crop.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode()
            parts.append({"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{encoded}", "detail": "high"}})
    return parts


def judge_readability(run: Run) -> list[Error]:
    assert run.figure is not None
    content = [
        {"type": "text", "text": READABILITY_PROMPT.format(
            instructions=_clip(run.instructions, 3_000), facts=image_facts(run.figure))},
        _image_part(run.figure),
        *quadrant_parts(run.figure),
    ]
    result = _ask_json(content, "readability_issues", READABILITY_SCHEMA)
    findings = [
        f"{item['category']} at {item['where'].strip()}: {item['description'].strip()}"
        for item in result.get("issues", []) if item.get("severity") == "major"
    ]
    # A legend or text box over data or text is a readability error by the
    # official definition, however the judge rated its severity.
    findings += [
        f"element_covers_content: {item['element'].strip()} covers "
        f"{item['covers'].replace('_', ' ')}: {item['detail'].strip()}"
        for item in result.get("overlays", [])
        if item.get("covers") in ("data", "text_or_labels")
    ]
    if not findings:
        return []
    return [Error(family=ErrorFamily.HARD_TO_READ, evidence=" ".join(findings))]


def validate(run: Run) -> list[Error]:
    execution = judge_execution(run)
    if execution:
        return execution
    return judge_data_and_chart(run) + judge_readability(run)
