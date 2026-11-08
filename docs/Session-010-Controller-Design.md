# Session 010 — Bounded chart-agent controller (offline-first)

**Status (2026-11-07 America/Vancouver):** Initial pure state-machine implementation and mock-only tests committed to the feature branch; **Codespaces regression results are pending**. No live model, Docker container, chart generation, sandbox command or new judge request has been performed in this session.

## Why a controller is necessary

Session 009 proved one-request compatibility for three generator roles and an experimental judge. Those results did not show that an agent can create a chart.

The two existing components are independent:

- `integrations.providers.execute_one` contacts a model only after explicit approval and returns a `NormalizedReply` with **inert** `ToolCall` descriptions. It never runs the commands.
- The pinned Assignment 1 dependency (`agent-sandbox-runtime` at `0cb0534c2fffb67ddfff619100057fad0be90a3c`) exposes `Sandbox` and `DockerImage`. The API supports `Sandbox.execute(command, timeout=..., env=..., shell=...)`, `stop()`, and context-manager cleanup. Its documentation warns that a Docker container is **not a hardened VM security boundary**.

A controller must bridge these only with explicit host authorization, strict resource limits, provider-specific message replay, no injected API credentials, and clearly documented provenance.

## First implementation slice: pure controller, no execution

New module: `integrations/chart_controller.py`.

`ChartController` is an **in-memory state machine**, not a live-agent CLI:

1. Construct it with a pinned generator `ModelSpec` and a nonblank task prompt. The Terra judge is rejected.
2. Call `preview_next_request()` to obtain metadata only, or `prepare_next_request()` to build a provider-native request. **Neither method sends anything.**
3. A separately approved host may eventually send **one** request through a provider adapter. The returned `NormalizedReply` must then be handed to `accept_reply()` explicitly.
4. The controller checks model/role provenance, exact `run_shell` tool names, argument shapes, valid unique call IDs, command size and turn/tool budgets. A tool call stays **pending** and is never executed here.
5. After a separately approved sandbox operation, supply its `returncode`, `stdout`, and `stderr` to `record_tool_result()`. The controller truncates outputs and uses the existing provider-specific `make_tool_result()` representation.
6. The next provider request can only be prepared after every pending tool result has been recorded. A final reply without calls marks the conversation completed.

### Default limits

| Budget | First-slice default | Enforcement |
| --- | ---: | --- |
| Model turns | 4 | Refuse additional turns; a final-budget model response cannot request more tools |
| Tool calls total | 6 | Reject a reply whose calls would exceed the limit |
| Command characters | 2,000 | Reject empty, overlong or NUL-bearing shell commands |
| Stored stdout/stderr per field | 2,048 characters | Truncate and annotate each tool output before model replay |
| Live API calls | 0 | Controller has no API client and no live dispatch |
| Docker launches / shell executions | 0 | Controller has no Docker construction or execution code |

**Important:** Each model turn would be a potentially billed request in a future live controller. The existing project rule—fresh explicit authorization **per model API request**—still applies. A four-turn budget is a ceiling, **not authorization to send four calls**. Likewise, acceptance of a model-suggested tool call is not permission to execute it.

## Provider-specific replay

The state machine delegates request construction to the existing Session 008/009 adapters:

- **DeepSeek `deepseek-flash`:** stateless Responses request; carry forward previous output items plus `function_call_output` entries.
- **OpenAI `gpt-5.6-luna`:** stateless-stored Responses in this adapter, same explicit item-history replay.
- **Z.ai `glm-5.3-flash`:** Chat Completions `messages` containing assistant `tool_calls` and subsequent `role=tool` messages; retain low reasoning effort as configured.
- **OpenAI `gpt-6.1-terra`:** explicitly excluded from this *generation* controller. Judge integration is a separate stage.

No code executes model-proposed commands or silently switches models. Provider-reported versions must still be captured in future actual runs.

## Sandbox security boundary: next implementation slice (not yet built)

The pinned `Sandbox` defaults to `network="bridge"`, so the eventual runner must **explicitly pass `network="none"`**. It must also use `ports=()`, no host mounts, no Docker socket, no secrets in the container environment, reduced CPU/memory, a short deployment lifetime, and a short command timeout. The host is responsible for starting the container only after user authorization and cleaning it up with a context manager.

The package has `DockerImage.add_local_file(...)` for safe *image-build-time* task-file injection, but no verified high-level artifact-copy/read API. We need to design bounded task-input staging and safe `figure.png` extraction before claiming end-to-end chart creation. Restrict file size, validate PNG via Pillow, and never expose a host directory to model-proposed shell commands.

A future runner must not blindly reuse `workflow/generate.py`: that original assignment entry point still targets Modal and the official model roster. Its output schema can inform the independent replacement without changing the released starter.

## Test coverage and verification

New `tests/test_controller_offline.py` covers:
- Zero-network, provider-native request preparation for all three generator roles.
- Two-turn function-call and tool-result replay in Responses and Chat Completions.
- Pending tool-call resolution, completion and refusal of extra turns.
- Strict model/provenance checks, unsupported tools, unexpected arguments, long/NUL commands and duplicate IDs.
- Model/tool budgets and missing outputs.
- Output truncation before tool results are added back into the prompt.

`.github/workflows/offline-ci.yml` now includes the controller mock suite. There are **no actual Docker launches or API calls** in these tests.

### Codespaces verification (no billed model calls or Docker)

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
git status --short --branch
uv run python -m unittest discover -s tests -p 'test_controller_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/provider_preflight.py
git status --short --branch
```

Please report the actual outcomes. Do not mark tests as passed until they run in Codespaces/CI.

## Next decisions before any live chart generation

First verify the pure controller and its tests. Then implement and mock-test a restricted `Sandbox` gateway using the pinned package, with explicit user permission before any real Docker launch. Design task-file staging and bounded PNG retrieval. Only after those pass should we propose any additional paid model request, approved **individually per turn**.

**Non-goals for this slice:** model-quality comparisons, MCC, human-label prediction, a live Terra judgment, course-equivalent results, automatic API retries, and unsupervised multi-turn execution.
