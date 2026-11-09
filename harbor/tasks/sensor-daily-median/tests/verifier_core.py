"""Shared verifier machinery for our five packaged tasks.

Source of truth: harbor/shared/verifier_core.py. scripts/sync_harbor_shared.py
copies it (with the course's figure_manifest.py and sitecustomize.py) into each
task's tests/, because harbor ships only that directory into the container.

Adapted from the course's harbor/example/tests/test_state.py (strategies S1,
S2, S3 and S5): snapshot the deliverables, re-run the agent's plot.py in a
scrubbed copy of /app with Figure.savefig instrumented, and read the resulting
JSON manifest of the artist tree. Task files hold the answer keys and the
task-specific assertions.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

APP = Path("/app")
FIGURE = APP / "figure.png"
SIDECAR = APP / "plotted_values.json"
SCRIPT_NAME = "plot.py"
TESTS = Path(__file__).resolve().parent
PYTHON = "/usr/local/bin/python3"
REEXEC_TIMEOUT = 120

DELIVERED_DIR = Path(tempfile.mkdtemp(prefix="delivered_"))
DELIVERED_FIGURE = DELIVERED_DIR / "figure.png"
DELIVERED_SIDECAR = DELIVERED_DIR / "plotted_values.json"
_DELIVERED_SHA: dict[Path, str] = {}
_SNAPSHOT_TAKEN = False
_HOOK_DIR: Path | None = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_delivered() -> None:
    """Copy figure.png and the sidecar aside before any re-run can overwrite them."""
    global _SNAPSHOT_TAKEN
    if _SNAPSHOT_TAKEN:
        return
    for source, destination in ((FIGURE, DELIVERED_FIGURE), (SIDECAR, DELIVERED_SIDECAR)):
        if source.exists():
            shutil.copy2(source, destination)
            _DELIVERED_SHA[destination] = sha256(destination)
    _SNAPSHOT_TAKEN = True


def delivered(path: Path) -> Path:
    assert path.exists(), f"{path.name} was not delivered"
    assert sha256(path) == _DELIVERED_SHA.get(path), (
        f"the snapshot of {path.name} was overwritten while the script under test ran")
    return path


def _instrumentation_dir() -> Path:
    """Private copy of the savefig hook, so the re-run never sees the answer key."""
    global _HOOK_DIR
    if _HOOK_DIR is None:
        private = Path(tempfile.mkdtemp(prefix="hook_"))
        for name in ("figure_manifest.py", "sitecustomize.py"):
            shutil.copy2(TESTS / name, private / name)
        _HOOK_DIR = private
    return _HOOK_DIR


def find_script() -> Path:
    named = APP / SCRIPT_NAME
    if named.exists():
        return named
    fallback = sorted(p for p in APP.rglob("*.py")
                      if p.is_file() and "savefig" in p.read_text(errors="replace"))
    assert fallback, f"no {SCRIPT_NAME} in /app and no other script there calls savefig"
    return fallback[0]


def reexecute(workdir: Path) -> dict[str, Any]:
    """Run the agent's script in a scrubbed copy of /app; return figure.png's manifest."""
    script = find_script()
    relative = script.relative_to(APP)
    if workdir.exists():
        shutil.rmtree(workdir)
    shutil.copytree(APP, workdir)
    for stale in (*workdir.rglob("*.png"), *workdir.rglob("*.manifest.json")):
        stale.unlink()
    env = dict(os.environ, PYTHONPATH=str(_instrumentation_dir()), MPLBACKEND="Agg",
               HOME="/tmp", SOURCE_DATE_EPOCH="1700000000", PYTHONDONTWRITEBYTECODE="1")
    started = time.time() - 1
    logs = Path(tempfile.mkdtemp(prefix="reexec_log_"))
    with (logs / "out").open("wb") as out, (logs / "err").open("wb") as err:
        proc = subprocess.Popen([PYTHON, str(relative)], cwd=workdir, env=env,
                                stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                start_new_session=True)
        try:
            code = proc.wait(timeout=REEXEC_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            proc.wait()
            raise AssertionError(f"re-running {relative} exceeded {REEXEC_TIMEOUT}s") from None
    stderr = (logs / "err").read_text(errors="replace")
    assert code == 0, f"re-running {relative} exited {code}\n{stderr[-2000:]}"
    candidates = [p for root in (workdir, APP) for p in sorted(root.rglob("*.manifest.json"))
                  if p.stat().st_mtime >= started]
    assert candidates, (f"{relative} ran but saved no matplotlib figure the verifier can see; "
                        "plot.py must call savefig with a relative path")
    chosen = next((p for p in candidates if p.name == "figure.manifest.json"), candidates[0])
    manifest = json.loads(chosen.read_text())
    saved_to = manifest.get("saved_to")
    manifest["_png"] = str(Path(workdir, saved_to) if saved_to
                           else chosen.with_name("figure.png"))
    return manifest


# ----------------------------------------------------------------- S1 checks


def check_valid_nonblank_png(path: Path = FIGURE) -> tuple[int, int]:
    import numpy as np
    from PIL import Image

    assert path.exists(), f"no figure at {path}"
    assert path.stat().st_size > 1000, f"{path} is only {path.stat().st_size} bytes"
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        assert image.format == "PNG", f"{path} is a {image.format}, not a PNG"
        size = image.size
        pixels = np.asarray(image.convert("RGB")).reshape(-1, 3)
    assert min(size) > 100, f"{path} is {size}, too small"
    assert len(np.unique(pixels, axis=0)) > 4, f"{path} is a flat colour field"
    return size


def check_input_unchanged(name: str, expected_sha: str) -> None:
    path = APP / name
    assert path.exists(), f"{name} is missing from /app"
    assert sha256(path) == expected_sha, f"{name} was modified; the task forbids editing input"


def check_rerender_matches(manifest: dict[str, Any]) -> None:
    """S3: the delivered figure.png must be what plot.py renders."""
    import numpy as np
    from PIL import Image

    produced = Path(manifest["_png"])
    assert produced.exists(), "the re-run emitted a manifest but no PNG"
    recorded = manifest.get("image_sha256")
    assert recorded and sha256(produced) == recorded, (
        "figure.png was replaced after plot.py saved it")
    original = delivered(DELIVERED_FIGURE)
    if sha256(original) == recorded:
        return
    a = np.asarray(Image.open(original).convert("RGB")).astype(int)
    b = np.asarray(Image.open(produced).convert("RGB")).astype(int)
    assert a.shape == b.shape, f"plot.py renders {b.shape} but figure.png is {a.shape}"
    differing = float((np.abs(a - b).sum(axis=2) > 0).mean())
    assert differing < 1e-4, f"figure.png is not what plot.py renders ({differing:.2%} differ)"


def load_sidecar() -> dict[str, Any]:
    data = json.loads(delivered(DELIVERED_SIDECAR).read_text())
    assert isinstance(data, dict), "plotted_values.json must hold a JSON object"
    return data


# ------------------------------------------------------------ manifest readers


def axes(manifest: dict[str, Any], index: int = 0) -> dict[str, Any]:
    entries = manifest.get("axes") or []
    assert len(entries) > index, f"the figure has {len(entries)} axes"
    return entries[index]


def bar_containers(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    found = [c for c in axes(manifest).get("containers", []) if c.get("type") == "bar"]
    assert found, "the axes contain no bars"
    return found


def lines(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [line for line in axes(manifest).get("lines", [])
            if not str(line.get("label", "")).startswith("_")]


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def assert_close(actual: list[Any], expected: list[float], tol: float, what: str) -> None:
    assert isinstance(actual, list) and len(actual) == len(expected), (
        f"{what}: expected {len(expected)} values, got {actual!r}"[:300])
    for index, (got, want) in enumerate(zip(actual, expected)):
        assert is_number(got), f"{what}[{index}] is {got!r}, not a JSON number"
        assert abs(float(got) - want) <= tol, f"{what}[{index}] = {got}, expected {want} ± {tol}"


def norm_colour(value: Any) -> str:
    """Matplotlib colour (name, hex or RGBA list) as lowercase #rrggbb."""
    from matplotlib.colors import to_hex

    return to_hex(value).lower()
