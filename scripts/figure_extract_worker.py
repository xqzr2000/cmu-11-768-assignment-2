"""Fixed, standard-library-only container helper for figure.png extraction.

This file is NOT executed by Session 010's offline tests. Its read_figure()
function is unit-tested with temporary synthetic files on the host.

For a future explicitly approved sandbox, bake this trusted script into the
reviewed chart image as /opt/assignment/extract_figure.py. It reads ONLY
/workspace/figure.png, with no arguments, shell commands, or network access.
Do not use model-proposed scripts as extraction helpers.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

FIGURE_PATH = Path("/workspace/figure.png")
MAX_FIGURE_BYTES = 2 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ExtractionError(ValueError):
    """Missing, unsafe, or oversized output file."""


def read_figure(path: Path) -> str:
    """Return one size-bounded fixed-schema JSON envelope, no file writes.

    The explicit path exists only for synthetic unit tests. Production main()
    always uses FIGURE_PATH, and accepts no paths or arguments from a model.
    """
    path = Path(path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as handle:
        metadata = os.fstat(handle.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise ExtractionError("figure.png must be a regular file.")
        if not 0 < metadata.st_size <= MAX_FIGURE_BYTES:
            raise ExtractionError("figure.png exceeds the size boundary.")
        data = handle.read(MAX_FIGURE_BYTES + 1)
    if not 0 < len(data) <= MAX_FIGURE_BYTES:
        raise ExtractionError("figure.png exceeds the size boundary.")
    if not data.startswith(PNG_SIGNATURE):
        raise ExtractionError("figure.png does not have the PNG signature.")
    envelope = {
        "path": "figure.png",
        "encoding": "base64",
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "data_base64": base64.b64encode(data).decode("ascii"),
    }
    return json.dumps(envelope, separators=(",", ":"))


def main() -> int:
    if len(sys.argv) != 1:
        print("figure extraction accepts no arguments", file=sys.stderr)
        return 2
    try:
        envelope = read_figure(FIGURE_PATH)
    except (ExtractionError, OSError):
        print("figure extraction failed (missing, unsafe or oversized PNG)", file=sys.stderr)
        return 1
    print(envelope)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
