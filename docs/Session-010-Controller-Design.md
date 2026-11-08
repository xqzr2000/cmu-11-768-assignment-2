# Session 010 — Bounded chart-agent controller (offline-first)

**Status (2026-11-07 America/Vancouver):** The pure controller test suite passed **11/11**, and the permission-gated fake-Docker gateway passed **14/14** in Codespaces (25/25 Session 010 tests so far); existing provider **37/37** and validator **49/49** regressions passed previously. A third **pure artifact-boundary** slice and **16 additional offline tests** are now committed but unverified. No live model, real Docker container, chart generation, sandbox command or new judge request has been performed in this session.

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

New `tests/test_controller_state_offline.py` covers:
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
uv run python scripts/check_controller_offline.py
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/provider_preflight.py
git status --short --branch
```

Please report the actual outcomes. Do not mark tests as passed until they run in Codespaces/CI.

## First Codespace verification and test discovery correction

The user pulled the initial Session 010 branch at commit `43a24ac` and ran the planned offline commands in Codespaces on 2026-11-07 (America/Vancouver):

- The initial controller invocation returned `Ran 0 tests` / `NO TESTS RAN`. **This is not a passed controller test suite.** Python `unittest discover` can exit successfully on zero discovered tests, so we must guard against this failure mode in CI.
- Provider adapter tests **37/37 passed**.
- Validator regression tests **49/49 passed** (the argparse errors shown in one test are expected/handled).
- Registry preflight reported **zero network requests** across the four model roles.
- Git working tree remained clean and tracking the Session 010 remote branch.

**Root cause:** Original file name `tests/test_controller_offline.py` did not match the committed glob `test_controller_*_offline.py`. The pattern expects an extra name segment after `controller_`.

**Remediation committed:**

1. Rename the file to `tests/test_controller_state_offline.py`, which matches the existing discovery pattern.
2. Add `scripts/check_controller_offline.py`, a deterministic test runner that checks `suite.countTestCases()` and **exits nonzero when discovery returns zero tests**, then executes the suite.
3. Update GitHub Actions to run the new guarded script rather than unguarded `unittest discover`; update README and this design report accordingly.

**Resolution verified in Codespaces:** The user pulled the corrected commits at `e828672` and ran `uv run python scripts/check_controller_offline.py`: **11 tests discovered and all 11/11 passed** in 0.004 s. Git remained clean/synchronized. No network or Docker was involved.

## Second implementation slice — strictly gated sandbox gateway (pending tests)

New `integrations/sandbox_gateway.py` imports and instantiates the pinned `Sandbox` **only after** an explicit `launch(confirm_launch=True, approve_image=IMAGE)` call. It is an opt-in host wrapper and **not yet connected to the chart controller or CLI**.

- `preview_launch()` is pure metadata: reports `docker_launches=0` and an explicit policy, without importing Docker or reading credentials. It is only available before any launch attempt.
- First-slice image is **exactly `python:3.12-slim`**. This is a **mutable, plain Python transport-test base image**, *not* the final pinned/chart-capable image. Changing the allowed image requires a future reviewed code change. Docker could pull the image on a real launch; none was performed here.
- The gateway invokes the pinned sandbox with `network="none"`, `ports=()`, `cwd="/workspace"`, `deployment_timeout=120`, `runtime_timeout=15`, `cpus=1.0`, and `memory="512m"`. The dependency itself provides `--cap-drop ALL`, `no-new-privileges`, `--pids-limit`, engine-enforced lifetime, no bind mounts, and context-manager cleanup.
- `propose_command("...")` validates the candidate and exposes the **exact command and one-step SHA-256 fingerprint** for human review, but **never executes** it. A pending proposal blocks another proposal until consumed or explicitly rejected.
- `execute_approved(confirm_one_command=True, approve_sha256=exact_fingerprint)` can execute **one** proposed command *only in an already-authorized sandbox*. It passes `env={}`, a bounded timeout and `check=False`, and returns only validated/truncated `returncode`, `stdout` and `stderr` fields. A failed attempt consumes a command budget slot. It does **not retry**.
- `close()` / context-manager exit stop the container without additional approval. The wrapper refuses repeated launches, prevents reuse after closure, and does not expose any general Docker CLI methods or host filesystem mounts.
- `SandboxLimits` validates bounded configurations (default maximum **6 commands**, **2,000 command characters**, **2,048 characters per output stream**, max 300-second lifetime). This command quota does **not** authorize actual execution.

**Crucial distinction:** The boolean flag and SHA-256 fingerprint are **guardrails, not proof of independent human consent**. A future host must present the exact proposed command for review, obtain consent, and only then call `execute_approved`. The gateway deliberately has **no automatic model-to-command execution path**. A real Docker container is **not a hardened VM security boundary**; treat model-generated shell commands as untrusted even with networking disabled.

**Not implemented:** task input transfer, safe `figure.png` extraction, chart-capable Docker image, binding the controller's `pending_calls` to a human approval UI, or any real Docker smoke run.

### New mock-only tests

New `tests/test_sandbox_gateway_offline.py` has **14 test cases**, using a `FakeSandbox` rather than Docker. The cases check denied launches, exact image approval, launch kwargs, proposal/approval mismatch, command budgets, malformed/NUL/oversized commands, result truncation, no secret environment forwarding, one-shot failure, no silent retry, and cleanup after exceptions.

New `scripts/check_sandbox_gateway_offline.py` explicitly **fails on zero discovered tests**. GitHub Actions runs this guarded suite in addition to the verified controller and existing provider/validator suites.

**To verify in Codespaces, with zero model requests and zero Docker launches:**

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_controller_offline.py
uv run python scripts/check_sandbox_gateway_offline.py
git status --short --branch
```

**Verified:** User pulled through commit `353fcad`; the guarded runners discovered **11 controller tests** and **14 gateway tests**, with **25/25 passing**, and final Git status was clean. All gateway operations used fake Docker; none started a real container.

## Third offline slice — task CSV and PNG artifact boundary (pending tests)

New `integrations/task_artifacts.py` implements **pure host-side validation and immutable in-memory snapshots**, not a Docker file-transfer mechanism:

1. `snapshot_task_csvs(task_descriptor)` uses the existing `workflow.tasks.AuthoredTask.load` schema and relative-path protection, then applies stricter staging constraints: **1–8** small task-local `.csv` inputs, safe ASCII filenames, **64 KiB per CSV** and **256 KiB total**, UTF-8 text only, no NUL bytes, a 128 KiB task-descriptor cap, and no symlinked descriptor ancestors or CSV paths. Each `CSVAsset` stores a byte snapshot plus SHA-256. `TaskInputSnapshot.manifest()` prints only name, intended `/opt/assignment/inputs/<name>` location, digest and byte length — **not** source data. The snapshot does **not** build an image or copy files into a container.
2. `validate_figure_png(raw_bytes)` enforces the exact PNG signature, **2 MiB compressed-byte cap**, **4,000,000-pixel cap**, a complete terminal `IEND` chunk with no extra payload, and Pillow structural/decoded pixel validation. Returns an in-memory `ValidatedFigure` with a safe metadata manifest. It does **not** write `figure.png` to the host.
3. `decode_figure_envelope(json_text)` accepts only the fixed `figure.png` transport format: `{"path":"figure.png","encoding":"base64","size_bytes":...,"sha256":...,"data_base64":"..."}`. It rejects extra fields, alternate or traversal paths, invalid sizes, noncanonical base64, digest mismatch, corrupt PNGs and oversized text. **This is a future trusted extraction-helper output format, not permission to accept raw model text as a file.**
4. The future transfer layer must create a reviewed, chart-capable **digest-pinned image**, materialize the already-vetted byte snapshots without secrets/host mounts, verify the copies, and extract one bounded figure through a supported and separately approved sandbox mechanism. The pinned DockerImage public API has `add_local_file(..., "/opt/assignment/inputs/<name>")` for **build-time file staging**, but it may start Docker builds and is **not called** by this slice. The gateway's normal 2,048-character command-output cap is **not** an appropriate PNG extraction channel; a separate size-aware transport is required.

New `tests/test_task_artifacts_offline.py` defines **16** synthetic, temporary-file tests for accepted CSV snapshots, ASCII/UTF-8 and file limits, symlink and descriptor size rejection, safe manifests, valid PNGs, invalid formats, truncated/oversized/pixel-bomb/trailing-payload PNGs, and strict base64-envelope checks. The new `scripts/check_task_artifacts_offline.py` fails when no tests are discovered. GitHub Actions now runs that guarded suite. **No actual Codespace pass is claimed yet for these 15 tests.**

**Next offline verification (zero API requests and zero Docker launches):**

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_task_artifacts_offline.py
uv run python scripts/check_controller_offline.py
uv run python scripts/check_sandbox_gateway_offline.py
git status --short --branch
```

Expected **16 newly discovered artifact tests**, and **41 total Session 010 tests** if all pass. Fix any actual test failures before adding real transfer operations.

## Next decisions before any live chart generation

First **verify the new 15-task-artifact tests** and fix any failures. Then design a reviewed task-local Docker image, safe data injection (no secret or host mounts), and size-limited PNG extraction using only supported pinned runtime interfaces. A separate human confirmation is required before any real Docker launch, and a fresh explicit model-specific approval is required **for every potentially billed model turn**. The bounded controller and gateway must not be wired to unattended live execution.

**Non-goals for this slice:** model-quality comparisons, MCC, human-label prediction, a live Terra judgment, course-equivalent results, automatic API retries, and unsupervised multi-turn execution.
