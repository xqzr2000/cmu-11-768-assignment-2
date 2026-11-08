# Session 010 — Bounded chart-agent controller (offline-first)

**Status (2026-11-07 America/Vancouver):** The six Session 010 suites passed **77/77 offline tests** in Codespaces: controller 11, fake-Docker gateway 14, task artifact 16, chart transfer 12, image recipe 11, and minimal build context 13. Existing provider 37/37 and validator 49/49 passed earlier. No model API request, real Docker build/pull/launch, or container-based PNG extraction has been performed. The next gate is actual base-image and package supply-chain verification, not more mocked execution.

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

## Third offline slice — task CSV and PNG artifact boundary (verified)

New `integrations/task_artifacts.py` implements **pure host-side validation and immutable in-memory snapshots**, not a Docker file-transfer mechanism:

1. `snapshot_task_csvs(task_descriptor)` uses the existing `workflow.tasks.AuthoredTask.load` schema and relative-path protection, then applies stricter staging constraints: **1–8** small task-local `.csv` inputs, safe ASCII filenames, **64 KiB per CSV** and **256 KiB total**, UTF-8 text only, no NUL bytes, a 128 KiB task-descriptor cap, and no symlinked descriptor ancestors or CSV paths. Each `CSVAsset` stores a byte snapshot plus SHA-256. `TaskInputSnapshot.manifest()` prints only name, intended `/opt/assignment/inputs/<name>` location, digest and byte length — **not** source data. The snapshot does **not** build an image or copy files into a container.
2. `validate_figure_png(raw_bytes)` enforces the exact PNG signature, **2 MiB compressed-byte cap**, **4,000,000-pixel cap**, a complete terminal `IEND` chunk with no extra payload, and Pillow structural/decoded pixel validation. Returns an in-memory `ValidatedFigure` with a safe metadata manifest. It does **not** write `figure.png` to the host.
3. `decode_figure_envelope(json_text)` accepts only the fixed `figure.png` transport format: `{"path":"figure.png","encoding":"base64","size_bytes":...,"sha256":...,"data_base64":"..."}`. It rejects extra fields, alternate or traversal paths, invalid sizes, noncanonical base64, digest mismatch, corrupt PNGs and oversized text. **This is a future trusted extraction-helper output format, not permission to accept raw model text as a file.**
4. The future transfer layer must create a reviewed, chart-capable **digest-pinned image**, materialize the already-vetted byte snapshots without secrets/host mounts, verify the copies, and extract one bounded figure through a supported and separately approved sandbox mechanism. The pinned DockerImage public API has `add_local_file(..., "/opt/assignment/inputs/<name>")` for **build-time file staging**, but it may start Docker builds and is **not called** by this slice. The gateway's normal 2,048-character command-output cap is **not** an appropriate PNG extraction channel; a separate size-aware transport is required.

New `tests/test_task_artifacts_offline.py` defines **16** synthetic, temporary-file tests for accepted CSV snapshots, ASCII/UTF-8 and file limits, symlink and descriptor size rejection, safe manifests, valid PNGs, invalid formats, truncated/oversized/pixel-bomb/trailing-payload PNGs, and strict base64-envelope checks. The new `scripts/check_task_artifacts_offline.py` fails when no tests are discovered. GitHub Actions runs that guarded suite. The user verified **16/16 passed** in Codespaces at commit `cf78030`, with a clean worktree.

**Verified Codespace command sequence (zero API requests and zero Docker launches):**

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_task_artifacts_offline.py
uv run python scripts/check_controller_offline.py
uv run python scripts/check_sandbox_gateway_offline.py
git status --short --branch
```

**Observed:** 16 artifact, 11 controller and 14 gateway tests all passed (**41/41**); the final Git worktree was clean and synchronized.

## Fourth offline slice — private CSV staging and a fixed PNG extraction protocol (verified)

**Goal:** Prepare bounded, reviewable file transport without using a Docker engine, provider SDK, network or unattended tool loop.

- `integrations/chart_transfer.py` defines `stage_input_snapshots(snapshot)`, a context manager that **revalidates already-snapshotted bytes and SHA-256 checksums before writing** private, short-lived host files. It rejects malformed task IDs, unsafe/duplicate CSV filenames, invalid UTF-8, NUL bytes, mismatched digests and excess file counts/bytes. It stages one `0600` CSV under a private `0700` temporary input directory per accepted asset, verifies the written digest, and removes the entire staging directory on context exit. `InputStagingPlan` returns intended `/opt/assignment/inputs/<name>` container destinations and trusted host staging paths for a *future authorized image build*; its printable manifest omits temporary host paths and data. The staging function **writes temporary host files** but does not build images or copy data into containers.
- `scripts/figure_extract_worker.py` is a **fixed, standard-library-only trusted helper** intended for eventual review and inclusion in the chart image at `/opt/assignment/extract_figure.py`. At production entry its path is fixed to `/workspace/figure.png`; no user/model-provided CLI arguments are accepted. It opens without following final-component symlinks (where supported), requires a regular file, checks the maximum **2 MiB** size before and after a bounded read, confirms the PNG signature, and emits the canonical fixed-field JSON/base64 envelope. It is **not a chart generator**, does not fully validate PNG pixels inside the image, and is **not yet executed inside Docker**.
- `preview_figure_extraction()` is inert protocol metadata: fixed `["python", "/opt/assignment/extract_figure.py"]` argv, `shell=False`, fixed `/workspace/figure.png` path, and an explicit **separate approval requirement**. The previously verified `decode_figure_envelope` and `validate_figure_png` validate checksum, byte length, PNG structure and pixels **after** trusted extraction output is delivered to the host.
- **Key integration gap:** the current `SandboxGateway.execute_approved` truncates command output to 2,048 characters, which cannot transfer a valid 2 MiB image. No special trusted-extraction execution path has been added. The future host must design a separate bounded-output transport, explicit approval gate and suitable container image. Nothing in these modules calls the actual pinned `DockerImage.add_local_file` or `Sandbox.execute`.
- The current gateway uses the floating transport-test image `python:3.12-slim`, **not** a digest-pinned image with Matplotlib/Pandas or a writable workspace guarantee. The image selection, build reproducibility and native host-to-Docker staging/extraction remain **unverified**.

New `tests/test_chart_transfer_offline.py` contains **12** pure/offline tests using only temporary synthetic CSV and PNG bytes: private file modes and cleanup, strict source bytes/digest, hostile/malformed snapshot rejections, uniqueness and size bounds, static extraction metadata, successful fixed envelope round-trip, missing/invalid/oversized/symlinked output, CLI argument rejection, and full host PNG decoding. The tests call the helper's local read function with temporary paths only; they do **not** start a container.

New `scripts/check_chart_transfer_offline.py` fails on zero discovered tests, and the offline CI workflow now invokes it.

**Codespace verification (passed):**

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_chart_transfer_offline.py
uv run python scripts/check_task_artifacts_offline.py
uv run python scripts/check_controller_offline.py
uv run python scripts/check_sandbox_gateway_offline.py
git status --short --branch
```

**Observed:** The user pulled the feature branch to `f81f4d1`; 12 chart-transfer tests, 16 artifact tests, 11 controller tests, and 14 fake-gateway tests all passed (**53/53**). Working tree was clean and synchronized; no Docker or model API was used.

## Fifth offline slice — digest-guarded chart image recipe (verified)

Session 010 needs a chart-capable image, but a real image digest, build results, and package wheel hashes have **not** yet been verified. We must not invent an immutable base digest or claim that a Docker build has succeeded.

New `integrations/chart_image_recipe.py` is a **pure text renderer**. Its `plan_chart_image(base_image)` accepts only the exact syntax `python:3.12-slim@sha256:<64 lowercase hex digits>`, with the actual digest to be researched and validated separately for the chosen platform. A digest-shaped string **alone proves neither the image's existence nor its trustworthiness**.

The rendered Dockerfile fixes the requested versions already pinned in `pyproject.toml`: `matplotlib==3.10.5`, `numpy==2.3.2`, `pandas==2.3.1`, and `pillow==12.3.0`. It configures headless Matplotlib (`MPLBACKEND=Agg`), a dedicated non-root runtime identity (`10001:10001`), and writable private `/workspace`. It expects a *future independently vetted minimal build context* with exactly `inputs/*.csv` and `trusted/extract_figure.py`, copies these to fixed `/opt/assignment/` paths, and changes their in-image permissions to **read-only**. The source staging paths are never accepted as arbitrary model input. No host mounts, API credentials, Docker socket, exposed ports or model SDKs are configured by this recipe.

**Important supply-chain limitation:** Exact **direct** package versions are not an immutable full dependency lock: transitive wheels, their hashes, their platform availability, and the selected base image architecture are not yet proven. `ChartImageRecipe.preview()` explicitly says `full_dependency_hash_lock_verified=false`, `image_exists_verified=false`, `docker_build_authorized=false`, and reports zero Docker/model operations. The emitted Dockerfile is a reviewable **development plan**, not a trusted, tested or authorized image.

New `tests/test_chart_image_recipe_offline.py` has **11 synthetic checks** for rejecting moving or injected base references, requesting the exact versions, non-root workspace, only fixed context copies, safe file permissions, absence of secrets/mounts/ports, metadata honesty, deterministic Dockerfile checksum, and no subprocess execution. The fake base digest used in unit tests is not a known real artifact. New `scripts/check_chart_image_recipe_offline.py` fails on zero discovered tests; the existing offline GitHub Actions workflow invokes it. All **11/11 recipe tests passed** in Codespaces at `f0818ba`, using only a fictitious digest. No image was looked up or built.

**Next offline verification (zero API requests and zero Docker operations):**

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_chart_image_recipe_offline.py
uv run python scripts/check_chart_transfer_offline.py
uv run python scripts/check_task_artifacts_offline.py
uv run python scripts/check_controller_offline.py
uv run python scripts/check_sandbox_gateway_offline.py
git status --short --branch
```

**Observed:** The five guarded suites discovered and passed **64/64 tests**, with a clean worktree. These do not verify image existence or runtime compatibility.

**Subsequent engineering decision:** Verify a real Python base image digest for a specific architecture; resolve and hash-lock the actual package wheels; create a minimal private Docker build context exclusively from the checked CSV bytes and reviewed extractor source; only then consider a separately approved image build and a trusted large-output extraction path. The current `SandboxGateway` still targets the non-chart-capable floating `python:3.12-slim` transport-test image and cannot silently adopt the new recipe.

## Sixth offline slice — minimal private Docker build-context assembly (verified)

**Goal:** Ensure a future Docker build sees exactly the reviewed Dockerfile, already validated CSV bytes and version-controlled trusted extraction helper—not a broad repository or user home directory.

New `integrations/chart_build_context.py` exposes `prepare_chart_build_context(snapshot, base_image)` as a temporary **host-side** context manager. It first validates the digest-formatted base reference using the fifth-slice inert `plan_chart_image`; this still does **not** verify the digest exists. It then calls the fourth-slice `stage_input_snapshots` to revalidate task CSV bytes and hashes, copies the verified CSV bytes into a separate temporary build context, and adds only the module's fixed Dockerfile text and the repository-reviewed `scripts/figure_extract_worker.py` bytes. It does not accept arbitrary model-provided source paths or copy the checkout.

The exact expected layout for one CSV is:

```text
build-context/                (0700; temporary)
├── Dockerfile               (0600; deterministic recipe)
├── inputs/                  (0700)
│   └── data.csv             (0600; rehashed snapshot bytes)
└── trusted/                 (0700)
    └── extract_figure.py    (0600; fixed reviewed helper source)
```

`ChartBuildContext.manifest()` hides the temporary absolute host path and CSV contents. `verify_chart_build_context` checks the **exact allowlist**, absence of symlinks and unexpected `.env`/`.git`/source files, private file/directory modes, per-file and total byte caps, SHA-256 integrity, and exact Dockerfile correspondence. The temporary context is removed on normal exit and exceptions.

**Important:** This stage **does write temporary, private host files**, but never invokes `DockerImage.build`, `Sandbox`, Docker CLI, subprocesses, or model APIs. The context path should only be handed to a future, independently approved build operation while its context manager is active. Existing `DockerImage` supports taking a Dockerfile/context path, but no such call has been made. The pinned `python:3.12-slim` digest, platform, dependency wheel hashes and actual build success remain unknown. The image recipe has **not** been changed to point to a deployable digest.

Added `tests/test_chart_build_context_offline.py` with **13 synthetic offline tests**: exact layout and private modes, fixed helper provenance, multi-CSV integrity, cleanup on exceptions, refusal of mutable base references and forged snapshots, detection of tampered files/Dockerfile/helper, unexpected credentials or checkout files, symlinks, modified permissions, oversized forged metadata, unsafe parent directories, and zero subprocess/model/Docker calls. Added `scripts/check_chart_build_context_offline.py` with nonzero-discovery enforcement and wired the test runner into GitHub Actions. **Verified:** User ran the guarded suite in Codespaces and all **13/13 tests passed**.

Verify entirely offline:

```bash
cd /workspaces/cmu-11-768-assignment-2
git pull --ff-only
uv run python scripts/check_chart_build_context_offline.py
uv run python scripts/check_chart_image_recipe_offline.py
uv run python scripts/check_chart_transfer_offline.py
uv run python scripts/check_task_artifacts_offline.py
uv run python scripts/check_controller_offline.py
uv run python scripts/check_sandbox_gateway_offline.py
git status --short --branch
```

**Observed in Codespaces:** **13 new + 64 previously passed = 77/77 Session 010 tests**, with clean tracking branch.

## Supply-chain verification checkpoint after 77 passing tests

The image-planning module does **not** yet identify a real base image digest. The Docker Official Image `python:3.12-slim` tag is multi-platform and mutable. Docker Hub's tag page changes as upstream publishes new images, and cached pages can show different digests. Before selecting a pin, inspect **the current registry manifest metadata** and the Codespace architecture together. Do not derive the full digest from an abbreviated per-platform display or an old screenshot.

```bash
cd /workspaces/cmu-11-768-assignment-2
uname -m
docker buildx imagetools inspect docker.io/library/python:3.12-slim
git status --short --branch
```

`docker buildx imagetools inspect` **queries registry metadata over the network**. It does **not** build or pull image layers, run a container, use a model API, or incur LLM charges. If the command is unavailable, record the exact error and do not substitute `docker pull` or `docker build`. The result must establish a full image/index SHA-256 digest and the matching `linux/amd64` or `linux/arm64` manifest. We have not verified those against the actual Codespace yet.

The committed `uv.lock` already contains versions and SHA-256 artifact metadata for `matplotlib==3.10.5`, `numpy==2.3.2`, `pandas==2.3.1` and `pillow==12.3.0`. **But** `integrations/chart_image_recipe.py` currently emits `pip install` with *only the four direct package pins*; it does not install from the committed `uv.lock` or enforce hashes on every transitive dependency. A chart-only, platform-specific and fully hashed wheel resolution is still required, followed by validation that selected wheels are available for the pinned image's Python ABI and Linux architecture. No new dependency lock was generated in this checkpoint.

We should first capture reliable registry/platform evidence, then review a hash-locked installation plan and only later ask the user to approve a real Docker image pull/build. **Do not automatically advance from a metadata lookup to any image or shell execution.**

## Next decisions before any live chart generation

The **13 minimal build-context tests are verified**. Next inspect registry metadata and the Codespace architecture, then design a complete chart-only wheel hash lock. No Docker image build/pull, sandbox command, or model request is authorized by these checks; any real execution requires separate explicit user approval. A separate human confirmation is required before any real Docker launch, and a fresh explicit model-specific approval is required **for every potentially billed model turn**. The bounded controller and gateway must not be wired to unattended live execution.

**Non-goals for this slice:** model-quality comparisons, MCC, human-label prediction, a live Terra judgment, course-equivalent results, automatic API retries, and unsupervised multi-turn execution.
