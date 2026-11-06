"""Student validator: deterministic execution checks before semantic judging.

Phase 1, offline-first: recognize when the final figure is missing or cannot be
opened as a complete PNG. These are structural failures, not judgments about
data correctness, chart design, or readability.

The other judges remain deliberately unimplemented until we have a verified
image-capable endpoint. Do not treat a decodable PNG as an acceptable run.
"""

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from validator.prediction import Error, ErrorFamily
from validator.runner import Run


def _execution_error(evidence: str) -> list[Error]:
    """Return one terminal execution failure with concrete artifact evidence."""
    return [Error(family=ErrorFamily.EXECUTION_FAILURE, evidence=evidence)]


def judge_execution(run: Run) -> list[Error]:
    """Check for a missing or undecodable saved figure, without model calls.

    An empty list means only that the figure passed these structural checks.
    It does NOT mean that a readable or correct visualization was produced.
    """
    figure: Path | None = run.figure
    if figure is None:
        return _execution_error("No final figure.png was produced.")
    if not figure.is_file():
        return _execution_error("The final figure.png is missing or is not a file.")

    try:
        # verify() examines the PNG container/checksums; it invalidates the
        # decoder state, so re-open to force decoding of the actual pixels.
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


def judge_data_and_chart(run: Run) -> list[Error]:
    """Judge numerical correctness and requested chart design (future stage)."""
    raise NotImplementedError("Semantic data/chart judging needs a validated image-capable endpoint")


def judge_readability(run: Run) -> list[Error]:
    """Judge the actual legibility of the rendered image (future stage)."""
    raise NotImplementedError("Readability judging needs a validated image-capable endpoint")


def validate(run: Run) -> list[Error]:
    """Return terminal execution failures, otherwise invoke remaining judges.

    This is intentionally incomplete for figures that pass structural checks:
    never silently return [] just because Pillow could decode a PNG.
    """
    execution = judge_execution(run)
    if execution:
        return execution
    return judge_data_and_chart(run) + judge_readability(run)
