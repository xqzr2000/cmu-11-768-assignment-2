"""Run authored tasks through our three hosted agents inside the Docker sandbox.

    docker build -t hw2-chart:1 sandbox/
    uv run python -m workflow.sandbox_generate                 # every task x agent
    uv run python -m workflow.sandbox_generate --models glm    # one agent
    uv run python -m workflow.sandbox_generate --force         # redo existing runs

This replaces the course's Modal runner (infrastructure/agent_runner.py) while
keeping its contract: the mini-swe-agent prompt, a single `bash` tool, at most
20 model steps, 120 s per command and 15 min per run, with the agent submitting
by running `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`. Each run is written to
runs/<task_id>__<agent>/ in the same result.json format as the seed artifacts,
so validator.runner and the workflow commands read it unchanged.

Isolation: every run gets a fresh container from the Assignment 1 Sandbox
(--network none, --cap-drop ALL, no-new-privileges, CPU/memory/PID limits, a
container lifetime cap). API keys stay in this host process; the container only
ever sees task inputs, and only figure.png is copied back out.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv
from tqdm import tqdm

from integrations.models import ModelSpec, get_model
from integrations.providers import (
    AdapterProtocolError,
    make_tool_result,
    prepare_request,
)
from integrations.providers.base import _get, parse_reply

from .generate import AGENT_BY_KEY, AGENT_ROLES, Agent, _valid_png, write_result
from .tasks import AuthoredTask, load_tasks

RELEASE = Path(__file__).resolve().parents[1]
IMAGE = "hw2-chart:1"
WORKDIR = "/workspace"
STEP_LIMIT = 20
COMMAND_TIMEOUT_SECONDS = 120
WALL_TIME_LIMIT_SECONDS = 15 * 60
MAX_OUTPUT_TOKENS = 8192
OBSERVATION_CHARS = 10_000
MAX_FIGURE_BYTES = 20_000_000
MAX_FORMAT_ERRORS = 3
SUBMIT = "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"
TRAJECTORY_FORMAT = "mini-swe-agent-1.1 (workflow.sandbox_generate)"

SYSTEM = "You are a helpful assistant that can interact with a computer."
INSTANCE_SUFFIX = (RELEASE / "sandbox" / "instance_suffix.txt").read_text()
BASH_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "bash",
    "description": "Execute a bash command in the task workspace and return its output.",
    "parameters": {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "The bash command to execute."}},
        "required": ["command"],
        "additionalProperties": False,
    },
}
FORMAT_ERROR = (
    "Tool call error: {problem}\n\nEvery response must call the `bash` tool with a "
    "`command` argument. When the task is complete, call it with exactly "
    f"`echo {SUBMIT}`."
)


def task_prompt(task: AuthoredTask) -> str:
    """Same wording as infrastructure/agent_runner._task_prompt, plus mini's template."""
    inputs = [item.name for item in task.inputs]
    return (
        f"Please solve this issue: TASK ID: {task.task_id}\n\n"
        f"USER REQUEST:\n{task.instructions}\n\n"
        f"INPUT FILES: {json.dumps(inputs)}\n"
        "REQUIRED OUTPUT: create figure.png in the workspace as a valid png file.\n"
        "Do not merely describe code: run it and leave the artifact at that exact path."
        + INSTANCE_SUFFIX
    )


# --------------------------------------------------------------------------- sandboxes


class Workspace(Protocol):
    def put(self, name: str, data: bytes) -> None: ...
    def execute(self, command: str, timeout: int) -> dict[str, Any]: ...
    def get(self, name: str) -> bytes | None: ...
    def stop(self) -> None: ...


class DockerWorkspace:
    """One fresh Assignment 1 Sandbox container per run."""

    def __init__(self, image: str) -> None:
        from agent_sandbox_runtime.sandbox import Sandbox

        self.box = Sandbox(
            image,
            cwd=WORKDIR,
            network="none",
            cpus=2.0,
            memory="2g",
            deployment_timeout=WALL_TIME_LIMIT_SECONDS + 120,
            runtime_timeout=COMMAND_TIMEOUT_SECONDS,
        )

    def put(self, name: str, data: bytes) -> None:
        if "/" in name or name in ("", ".", ".."):
            raise ValueError(f"unsafe input name: {name!r}")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / name
            source.write_bytes(data)
            source.chmod(0o644)
            _docker("cp", str(source), f"{self.box.id}:{WORKDIR}/{name}")

    def execute(self, command: str, timeout: int) -> dict[str, Any]:
        return self.box.execute(command, timeout=timeout)

    def get(self, name: str) -> bytes | None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out"
            copied = subprocess.run(
                ["docker", "cp", "--follow-link", f"{self.box.id}:{WORKDIR}/{name}", str(target)],
                capture_output=True, text=True, timeout=60,
            )
            if copied.returncode != 0 or not target.is_file():
                return None
            if target.stat().st_size > MAX_FIGURE_BYTES:
                raise ValueError(f"{name} exceeds {MAX_FIGURE_BYTES} bytes")
            return target.read_bytes()

    def stop(self) -> None:
        self.box.stop()


class LocalWorkspace:
    """NOT isolated: runs commands on this machine. Only for --local smoke tests."""

    def __init__(self) -> None:
        self.dir = tempfile.TemporaryDirectory(prefix="agent-local-")
        self.path = Path(self.dir.name)

    def put(self, name: str, data: bytes) -> None:
        (self.path / name).write_bytes(data)

    def execute(self, command: str, timeout: int) -> dict[str, Any]:
        env = {k: v for k, v in os.environ.items()
               if not any(m in k for m in ("TOKEN", "SECRET", "API_KEY"))}
        env.update(MPLBACKEND="Agg", PYTHONUNBUFFERED="1")
        try:
            done = subprocess.run(["bash", "-c", command], cwd=self.path, env=env,
                                  capture_output=True, text=True, timeout=timeout)
            return {"output": done.stdout + done.stderr, "returncode": done.returncode,
                    "exception_info": ""}
        except subprocess.TimeoutExpired as error:
            return {"output": str(error.output or ""), "returncode": 124,
                    "exception_info": f"Command timed out after {timeout}s"}

    def get(self, name: str) -> bytes | None:
        path = self.path / name
        return path.read_bytes() if path.is_file() else None

    def stop(self) -> None:
        self.dir.cleanup()


def _docker(*args: str) -> None:
    done = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        raise RuntimeError(f"docker {shlex.join(args)} failed: {done.stderr.strip()}")


# ------------------------------------------------------------------------- agent loop


def _client(spec: ModelSpec) -> Any:
    from openai import OpenAI

    key = os.environ.get(spec.key_env)
    if not key:
        raise RuntimeError(f"missing {spec.key_env}")
    # The SDK retries 408/409/429/5xx with backoff; Z.ai rate limits need it.
    return OpenAI(api_key=key, base_url=spec.base_url, timeout=300, max_retries=6)


def _observation(result: dict[str, Any]) -> str:
    output = result.get("output") or ""
    if result.get("exception_info"):
        output = f"{result['exception_info']}\n{output}"
    if len(output) > OBSERVATION_CHARS:
        half = OBSERVATION_CHARS // 2
        output = (output[:half] + f"\n[... {len(output) - OBSERVATION_CHARS} characters "
                  "elided ...]\n" + output[-half:])
    return json.dumps({"returncode": result.get("returncode"), "output": output}, indent=2)


def _strip_reasoning(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fallback history without reasoning items or server-side item IDs.

    With store=False some servers reject replayed items that reference IDs
    they never persisted; call_id (not id) is what links tool outputs.
    """
    cleaned = []
    for item in items:
        if item.get("type") == "reasoning":
            continue
        if item.get("type") in ("function_call", "message"):
            item = {k: v for k, v in item.items() if k not in ("id", "status")}
        cleaned.append(item)
    return cleaned


def run_agent(spec: ModelSpec, prompt: str, workspace: Workspace, client: Any) -> dict[str, Any]:
    """Drive one agent to submission or a limit; return trajectory and outcome."""
    from openai import BadRequestError

    style = spec.api_style
    items: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    messages: list[dict[str, Any]] = [dict(item) for item in items]
    usage = {"input_tokens": 0, "output_tokens": 0, "model_calls": 0}
    reported_models: set[str] = set()
    started = time.monotonic()
    format_errors = 0
    keep_reasoning = True
    status = "LimitsExceeded"

    def format_error(problem: str) -> None:
        text = FORMAT_ERROR.format(problem=problem)
        items.append({"role": "user", "content": text})
        messages.append({"role": "user", "content": text})

    for _ in range(STEP_LIMIT):
        if time.monotonic() - started > WALL_TIME_LIMIT_SECONDS:
            break
        request = prepare_request(
            spec, items if keep_reasoning else _strip_reasoning(items),
            tools=[BASH_TOOL], max_output_tokens=MAX_OUTPUT_TOKENS,
        )
        if spec.provider == "openai":
            # store=False: replaying reasoning items needs their encrypted content.
            request["include"] = ["reasoning.encrypted_content"]
        create = (client.responses.create if style == "responses"
                  else client.chat.completions.create)
        try:
            response = create(**request)
        except BadRequestError as error:
            text = str(error).lower()
            if keep_reasoning and style == "responses" and any(
                    hint in text for hint in ("reasoning", "not found", "store")):
                keep_reasoning = False
                response = create(**prepare_request(
                    spec, _strip_reasoning(items), tools=[BASH_TOOL],
                    max_output_tokens=MAX_OUTPUT_TOKENS))
            else:
                raise
        usage["model_calls"] += 1
        raw_usage = _get(response, "usage")
        for ours, theirs in (("input_tokens", ("input_tokens", "prompt_tokens")),
                             ("output_tokens", ("output_tokens", "completion_tokens"))):
            for name in theirs:
                value = _get(raw_usage, name) if raw_usage is not None else None
                if isinstance(value, int):
                    usage[ours] += value
                    break
        try:
            reply = parse_reply(spec, response)
        except AdapterProtocolError as error:
            format_errors += 1
            messages.append({"role": "assistant", "content": "",
                             "extra": {"format_error": str(error)}})
            if format_errors >= MAX_FORMAT_ERRORS:
                status = "RepeatedFormatError"
                break
            format_error(f"your previous response could not be used ({error}).")
            continue
        if reply.reported_model:
            reported_models.add(reply.reported_model)
        items.extend(dict(item) for item in reply.continuation_items)
        messages.append({
            "role": "assistant",
            "content": reply.text,
            "tool_calls": [
                {"id": call.call_id, "type": "function",
                 "function": {"name": call.name, "arguments": json.dumps(call.arguments)}}
                for call in reply.tool_calls
            ],
        })
        if not reply.tool_calls:
            format_errors += 1
            if format_errors >= MAX_FORMAT_ERRORS:
                status = "RepeatedFormatError"
                break
            format_error("no tool call was found in your response.")
            continue
        format_errors = 0

        submitted = False
        for call in reply.tool_calls:
            command = call.arguments.get("command")
            if call.name != "bash" or not isinstance(command, str) or not command.strip():
                result = {"output": "Error: call the `bash` tool with a non-empty "
                                    "string `command`.", "returncode": -1}
            else:
                result = workspace.execute(command, COMMAND_TIMEOUT_SECONDS)
                first = (result.get("output") or "").lstrip().splitlines()[:1]
                submitted = submitted or (first == [SUBMIT])
            observation = _observation(result)
            items.append(make_tool_result(style, call.call_id, observation))
            messages.append({"role": "tool", "tool_call_id": call.call_id,
                             "content": observation})
        if submitted:
            status = "Submitted"
            break

    messages.append({"role": "exit", "content": "", "extra": {"exit_status": status}})
    return {
        "messages": messages,
        "outcome": {
            "exit_status": status,
            "reported_models": sorted(reported_models),
            "usage": usage,
        },
    }


# ------------------------------------------------------------------------------ main


def run_one(task: AuthoredTask, descriptor: Path, agent: Agent, image: str,
            local: bool) -> dict[str, Any]:
    spec = get_model(AGENT_ROLES[agent.key])  # type: ignore[arg-type]
    workspace: Workspace = LocalWorkspace() if local else DockerWorkspace(image)
    started = time.monotonic()
    try:
        task_record = {
            "task_id": task.task_id, "task_class": task.task_class,
            "instructions": task.instructions,
            "inputs": [item.model_dump() for item in task.inputs],
            "expected_output": {"path": "figure.png", "format": "png"},
        }
        workspace.put("task.json", (json.dumps(task_record, indent=2) + "\n").encode())
        for item in task.inputs:
            workspace.put(item.name, (descriptor.parent / item.path).read_bytes())
        result = run_agent(spec, task_prompt(task), workspace, _client(spec))
        figure = workspace.get("figure.png")
    finally:
        workspace.stop()

    artifact_error = None
    if figure is not None:
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            Path(tmp.name).write_bytes(figure)
            if not _valid_png(Path(tmp.name)):
                artifact_error = "figure.png is not a valid PNG"
    return {
        "scaffold": "workflow.sandbox_generate (mini-swe-agent-compatible prompt and limits)",
        "outcome": result["outcome"],
        "trajectory": {"messages": result["messages"], "trajectory_format": TRAJECTORY_FORMAT},
        "artifact_present": figure is not None,
        "artifact_error": artifact_error,
        "artifact_bytes": figure,
        "elapsed_seconds": time.monotonic() - started,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", type=Path, default=RELEASE / "tasks")
    parser.add_argument("--artifacts", type=Path, default=RELEASE / "runs")
    parser.add_argument("--models", nargs="+", choices=tuple(AGENT_BY_KEY),
                        default=list(AGENT_BY_KEY))
    parser.add_argument("--only", nargs="+", metavar="TASK_ID", help="subset of task IDs")
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--force", action="store_true", help="replace completed runs")
    parser.add_argument("--local", action="store_true",
                        help="UNSAFE smoke test: run commands on this machine, no Docker")
    args = parser.parse_args(argv)
    load_dotenv()
    tasks = load_tasks(args.tasks)
    if args.only:
        tasks = [(t, d) for t, d in tasks if t.task_id in set(args.only)]
    jobs = [(t, d, AGENT_BY_KEY[k]) for t, d in tasks for k in args.models]
    failures = 0
    progress = tqdm(jobs, unit="run")
    for task, descriptor, agent in progress:
        progress.set_description(f"{task.task_id} / {agent.key}", refresh=True)
        destination = args.artifacts / f"{task.task_id}__{agent.key}"
        if destination.exists() and not args.force:
            progress.write(f"skip {destination} (exists)")
            continue
        try:
            result = run_one(task, descriptor, agent, args.image, args.local)
            written = write_result(task, descriptor, agent, args.artifacts, result,
                                   force=args.force)
            outcome = result["outcome"]
            progress.write(f"wrote {written}: {outcome['exit_status']}, "
                           f"figure={result['artifact_present']}, usage={outcome['usage']}")
        except Exception as error:  # one failed run must not stop the sweep
            failures += 1
            progress.write(f"ERROR {task.task_id} / {agent.key}: {type(error).__name__}: {error}")
    if failures:
        raise SystemExit(f"{failures} run(s) failed; rerun to resume")


if __name__ == "__main__":
    main()
