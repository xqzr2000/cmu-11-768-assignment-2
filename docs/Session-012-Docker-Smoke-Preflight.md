# Session 012 — Chart Docker build and plotting smoke-test preflight

**Status:** Planning only. No Docker pull, image build, package download/install, container launch, model tool execution, or live model API request is authorized by this document.

**Starting point:** PR #11 merged to `main` at `55299ad` on 2026-11-08 UTC. The user synchronized local `main` and deleted both Session 011 branches. Session 011 verification: **178/178** offline tests passed in Codespaces; GitHub Actions passed on its latest feature head. This does **not** establish a functioning chart image.

## Purpose and boundary

Validate whether the *reviewed chart Dockerfile* could eventually produce a deterministic `figure.png` from a **fixed, trusted local script**, using both **zero CSV** and **one benign CSV** input case. This is an environment smoke test, **not** a multi-turn model-agent test or course-equivalent evaluation.

The initial Session 012 activity is a static, offline review of candidate commands, image refs, dependency provenance, resource limits, and cleanup. The subsequent real image operation, if approved, is a **separate milestone**.

## Source components in the merged repository

| Component | What it currently supports | Unverified boundary |
| --- | --- | --- |
| `integrations/chart_image_recipe.py` | Renders a fixed Dockerfile from digest-formatted `python:3.12-slim@sha256:<64 hex>`; requests hashed wheels and runs as `10001:10001` with headless matplotlib | The digest's existence/trust and whether Dockerfile steps work in Docker |
| `requirements/chart-cp312-linux-amd64.txt` | 14 pins/hashes (four direct plotting roots and ten transitives) audited against `uv.lock` metadata | Downloaded wheel bytes, actual pip install and runtime imports |
| `integrations/chart_build_context.py` | Stages exactly Dockerfile, reviewed PNG extractor, approved requirements, and 0–8 small vetted CSVs; revalidates hashes and permissions | Docker build behavior with either empty or nonempty `inputs/` |
| `integrations/chart_transfer.py` / `integrations/task_artifacts.py` | Byte-bounded input snapshots and PNG envelope decoding, zero-input cases included | Actual trusted output transfer from a container |
| `integrations/sandbox_gateway.py` | Fake-tested opt-in command gateway, network disabled during sandbox launch, resource-limited | It still defaults to floating transport-test `python:3.12-slim`, **not** the proposed chart image; do not silently substitute |

An earlier metadata-only registry inspection recorded the `linux/amd64` Python manifest candidate `sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177`. Treat that as a **candidate observed previously**, not an authenticated or freshly verified image. No base-image layers have been pulled.

## Stage A — Offline-only review (authorized by this documentation work)

1. Inspect the current code, Dockerfile recipe and pre-existing tests. Do not import Docker, contact external registries, or call models as a side effect.
2. Produce an exact human-readable preview of the candidate Dockerfile, its SHA-256, planned base reference, 14-package requirements hash closure, and all allowlisted context file names. Never print CSV content, API keys or temporary absolute host paths.
3. Confirm that zero-input and one-input contexts both have private directories, correct per-file hashes, and no extra source checkout, symlink, secret, mount, Docker socket or unbounded file.
4. Review a **future** build command for explicit single-use tag, declared `linux/amd64` platform, fixed private context, timeout, expected network requirement for fetching base/wheels, and cleanup. A Docker image build normally needs a network unless required layers and packages are already cached. Runtime sandbox networking is a separate policy and should remain disabled.
5. Review a later trusted plotting script with hard-coded synthetic numeric values and a bounded PNG export to `/workspace/figure.png`. No model-proposed shell commands and no user secrets; if using CSV, read only the vetted `/opt/assignment/inputs/` location. Ensure the run uses constrained CPU/memory/time and non-root permissions.
6. Define pass/fail evidence before execution: actual Docker exit code, package import/version checks, PNG created, output size/pixels and figure envelope verified, cleanup, and no unreviewed network or extra commands.

**Current Stage A status:** The user verified the existing 14-package wheel metadata audit (**PASS**), recipe **13/13**, and private build context **19/19** in Codespaces, with a clean `feature/session-012-docker-smoke-preflight` branch. We then committed a new **offline-only zero/one-CSV preview**, seven synthetic tests, a guarded test runner and a CI test step; **the new preview code/tests have NOT been run in Codespaces yet**. No Docker operations have occurred.

### Preview entry point: safe metadata, real private host staging, zero container execution

The new `scripts/preview_chart_smoke_offline.py` evaluates two *synthetic* input snapshots: `smoke_zero` (no CSV) and `smoke_one` (one tiny `synthetic.csv`). Within separate short-lived temporary host contexts it checks **exactly** the allowlisted relative filenames, the private `0700` directory modes, the static Dockerfile's exact SHA-256, and the 14-item audited requirements closure. It discards each context before returning. The only output is JSON with relative paths, sizes, hashes and the **actual inert Dockerfile text**, not CSV data, absolute host paths, API keys, commands that were run, or Docker handles.

Run this `uv` command once the new branch commit is pulled:

```bash
uv run python scripts/check_chart_smoke_preview_offline.py
uv run python scripts/preview_chart_smoke_offline.py
```

**Important:** `preview_chart_smoke_offline.py` is not a builder; its contexts are cleaned on exit, so **no build can reference those discarded directories**. A future separately approved build runner would have to keep a vetted context open through build, re-verify immediately before use and clean it afterward. The preview uses the **previously observed** Python AMD64 manifest as a **candidate only**, not a rechecked/trusted base or working Docker artifact.

### Conditional Stage B build-command *template* (NOT executable from this preview)

The following is an **unapproved review template**, not a command to run now. `<private-verified-context>` is deliberately a placeholder because the temporary preview context is destroyed:

```text
timeout 900s docker buildx build --load --platform linux/amd64 --pull --network default --progress plain --tag cmu-chart-smoke:session012-review --file <private-verified-context>/Dockerfile <private-verified-context>
```

The template fixes the target platform, candidate tag and build-time network intent, and has a client-side timeout. **It does not yet provide independently verified CPU/memory limits for the BuildKit builder**, guarantee that timeout interrupts server-side work, revalidate the base image from registry signatures/attestation, or establish reproducible wheel installation. Those items remain blockers for a real attempt. An approved and audited runner must not expose the host Docker socket inside the chart container, inject secrets, copy the full checkout, or quietly substitute the gateway's floating test image. No build or run command is included in the safe preview's JSON.

**Proposed trusted runtime smoke case, still not authorized:** a hard-coded Matplotlib `Agg` drawing using constants (no model text), writing `/workspace/figure.png` as uid/gid `10001:10001` with network disabled, bounded CPU/RAM/PIDs/time, and a private writable workspace. A future vetted extractor may transfer the PNG only over a trusted size-aware output channel; the existing bounded text-command channel must **not** receive a multi-megabyte base64 envelope. We must review exact container flags and output retrieval before this stage.

**Before Stage B can be approved:** confirm base digest+platform against registry, actual selected wheel bytes/hashes and install, BuildKit builder resource/time controls, the exact in-context build/run orchestration, cleanup even on exceptions, artifact extraction protocol, and user's explicit approval of the exact resulting operations.

## Stage B — Separately approved real environment smoke test (NOT AUTHORIZED)

**Do not start Stage B without a fresh, explicit user approval for the exact reviewed build/pull and smoke-run commands.** The approval should identify: immutable base digest and platform, image tag, Dockerfile/context, network policy during build, max resources/time, whether image pull/wheel download is permitted, test script and expected files, and cleanup.

If approved later, run **one** bounded trusted plotting smoke case at a time with no model calls and report observed evidence. Confirm that the pinned Assignment 1 sandbox API can actually accept the new chart image; do not bypass `SandboxGateway` approvals or wire agent commands automatically. Docker is **not** a hardened VM boundary.

## Known open questions

- Does the previously observed Python AMD64 manifest still resolve and match the intended base image and environment?
- Will `pip --require-hashes --only-binary=:all:` successfully install all 14 wheels in the pinned Linux CPython 3.12 image? Metadata-only hash auditing does not establish this.
- Does the real Dockerfile copy an empty `inputs/` directory successfully, and does the zero-match `find -exec` step behave as designed? No real build has tested this.
- Are there filesystem ownership constraints when the non-root container creates `figure.png` and the trusted extractor reads it?
- How should a separately verified chart image be connected to the intentionally fixed fake-tested gateway without weakening command approvals?

## Session 012 initial offline commands

Run in a clean `feature/session-012-docker-smoke-preflight` worktree; these **do not** build or launch containers:

```bash
uv run python scripts/check_chart_wheel_lock_offline.py
uv run python scripts/check_chart_image_recipe_offline.py
uv run python scripts/check_chart_build_context_offline.py
git status --short --branch
```

After the **new** guarded preview tests and JSON preview pass in Codespaces, record their observed results in `docs/Learning-Progress.md` and inspect draft-PR CI. Stage B remains blocked until the control and approval gaps above are resolved. Do not claim any actual chart image results.
