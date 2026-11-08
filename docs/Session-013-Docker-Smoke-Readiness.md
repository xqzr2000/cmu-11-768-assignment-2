# Session 013 — Chart smoke-test readiness (offline only)

**Status:** In progress on feature/session-013-docker-smoke-readiness. This session does **not** authorize Docker pull/build/launch, internet package downloads, registry queries, agent-operated commands, or model requests.

**Starting point:** Session 012 PR #12 merged into main at 1118bcd on 2026-11-08 UTC; the main-branch GitHub Actions run succeeded. The user verified a clean synchronized Codespaces main. Session 012 passed 185 offline tests, the 14-package metadata-only lock audit and the synthetic zero/one-CSV context preview. None of this proves a runnable image.

## First slice — trusted synthetic plotting fixture

- scripts/chart_smoke_worker.py contains fixed numeric values and produces a 640×480 Matplotlib Agg PNG. No task input, CSV read, model response, CLI option, HTTP request or Docker call is used.
- Production main() has the single fixed path /workspace/figure.png and accepts no arguments. It exclusively creates the PNG (does not overwrite) and enforces the existing 2 MiB output cap.
- tests/test_chart_smoke_worker_offline.py exercises the code **on the host**, in temporary directories, and validates the PNG with existing validate_figure_png(). It also checks fixed read_figure()/decode_figure_envelope() round-trip compatibility **without a container or the limited gateway command-output channel**; existing-file and symlink rejection; oversized PNG cleanup; argument rejection; and import restrictions.
- The guarded runner scripts/check_chart_smoke_worker_offline.py rejects zero discovered tests. CI runs it after uv sync --locked.

This is a **host-Python test only**. Matplotlib working in Codespaces is not evidence that the 14 Linux AMD64 wheels install in a Docker image. The worker is **not yet copied into the chart Docker build context**, and is **not executable in the proposed image**. Any integration must be independently reviewed, not silently added to the prior exact allowlist. The output uses synthetic constants, not human labels.

### Safe Codespaces commands (no Docker or API requests)

~~~bash
uv run python scripts/check_chart_smoke_worker_offline.py
uv run python scripts/check_chart_smoke_preview_offline.py
uv run python scripts/check_chart_wheel_lock_offline.py
git status --short --branch
~~~

## Unresolved gates before a real Stage B build and run

1. **Base provenance and packages:** Freshly validate the Python 3.12 linux/amd64 base manifest and independently verify selected wheel archives against actual bytes and the dependency closure. Historical metadata is insufficient. Contacting a registry or downloading wheels needs separate authorization.
2. **Build lifecycle:** Design a reviewed builder that holds the same verified private context alive through the build, rechecks immediately before use, selects the immutable platform/base, uses a unique image tag and cleans even on failure. Verify the build-time network policy, BuildKit server-side cancellation behavior, resource caps and wall time. A client-side timeout alone is not a complete control.
3. **Fixture integration:** Explicitly allowlist/hash the fixed worker in context, revise the Dockerfile COPY and permissions, and update file counts, digests and tampering tests. The Dockerfile hash will change and need review. Never copy unvetted task/model files or the full checkout.
4. **Runtime:** Review exact operations with unprivileged UID/GID, --network none, CPU/RAM/PID/wall-time limits, no published ports, credentials, host mounts or Docker socket, and only a private writable /workspace. The gateway's floating transport image must not be silently substituted.
5. **Output:** Invoke the trusted plotting worker, not an agent-proposed command. Extract PNG over a separate, size-bounded trusted channel rather than the current gateway's short command stdout. Verify size/dimensions and clean container/image on all exits.
6. **Approval:** Present exact build, image pull, runtime, network, file movement and cleanup operations for a fresh explicit user decision. Prior one-request model consent and offline CI do not authorize Stage B.

## Verification and limits

At creation, GitHub source, tests and CI were prepared, but **Codespaces tests on the new head were not yet verified**. Do not mark them passed until user or CI output confirms. Session 012's 185/185 remains historical evidence. This slice adds 8 host-only tests, giving an **expected** 193 total if all previous tests still pass.

No paid model requests, actual Docker-built chart, BuildKit performance test, model-agent chart generation, judge MCC or official-model-equivalent results are claimed.

**Next:** Verify the guarded tests and full offline regression in Codespaces, inspect draft PR CI, and then design a separately reviewed exact-command Stage B proposal.
