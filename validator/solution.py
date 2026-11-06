"""Student validator: offline execution checks plus baseline semantic judgments.

Missing or undecodable PNGs produce a terminal execution failure without a
model request. For valid PNGs, reuse the official baseline's image-capable
judging path as the first integration step. This is NOT a measured improvement
over the baseline: actual data/chart/readability decisions require a live
vision-language endpoint, and need independent evaluation against human labels.
"""

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from validator import baseline
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
    """Delegate data and chart questions to the supplied baseline VLM judge."""
    return baseline.judge_data_and_chart(run)


def judge_readability(run: Run) -> list[Error]:
    """Delegate rendered-image readability checks to the baseline VLM judge."""
    return baseline.judge_readability(run)


def validate(run: Run) -> list[Error]:
    """Check the figure first; then ask the model about three semantic families.

    A valid PNG does not imply a correct chart. The semantic model failures
    propagate to the runner; they must not become false "acceptable" results.
    """
    execution = judge_execution(run)
    if execution:
        return execution
    return judge_data_and_chart(run) + judge_readability(run)
