# Session 014 — Offline chart-worker image staging

**Scope:** Source-only, offline-first integration. No Docker pull, build, launch, model API calls, registry access, wheel downloads or package installations in a chart image are authorized.

**Baseline:** Session 013 [PR #13](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/13) merged at `e0242d6`; the user confirmed a clean synchronized `main`, deleted the old local and remote feature branches, and observed post-merge GitHub Actions success. The verified historical baseline is **193/193** host-only/fake/mock offline tests, the **14/14** dependency *metadata* audit, and zero-network provider preview.

## Why this small integration is necessary

Session 013's trusted `scripts/chart_smoke_worker.py` generated a valid 640×480 Matplotlib PNG **in Codespaces**, but the Session 012 proposed Dockerfile and private build context did not carry that worker. A real future smoke test could not have invoked the fixed worker by path. Session 014 makes that path available **in an inert image plan**, not in a built or running container.

The only new trusted file in the short-lived context is `trusted/smoke_chart.py`, byte-for-byte copied from version-controlled `scripts/chart_smoke_worker.py`. The fixed Dockerfile now declares:

~~~dockerfile
COPY trusted/smoke_chart.py /opt/assignment/smoke_chart.py
~~~

The same `RUN chmod` step that makes the extractor readable marks the worker `0444` (read-only) in the proposed image. Runtime remains `USER 10001:10001`, with a private writable `/workspace`. The Dockerfile does **not** invoke the worker during build and does not specify an ENTRYPOINT or CMD. The intended later fixed command is `python /opt/assignment/smoke_chart.py`, to be presented for separate exact-operation approval, not executed by this session.

## Context inventory and security invariants

| Input case | Exact context files | Count |
| --- | --- | ---: |
| Zero CSV | Dockerfile, 14-wheel requirements lock, fixed extractor, fixed smoke worker | 4 |
| One CSV | All four trusted files plus `inputs/synthetic.csv` | 5 |
| N task CSVs | Four trusted files plus 0–8 validated task CSV snapshots | 4–12 |

The previous context allowed three immutable-purpose support files plus CSVs. This change adds **exactly one** version-controlled support file. The build context still contains no repository checkout, `.git`, `.env`, arbitrary model script, secret, Docker socket or host mount. Staging uses private `0700` directories, private `0600` files, the same 512 KiB total cap, per-file cap for the new worker of **16 KiB**, CSV constraints and context lifetime/cleanup.

Verification now checks both the staged worker's declared size/SHA-256 and its **actual bytes against the current trusted source**. A caller cannot replace the staged worker and merely recompute the manifest digest to evade the trusted-source check. This does not make the trusted source or host Docker daemon a high-assurance sandbox; source review and exact-command approval remain essential.

## Offline tests affected

- `tests/test_chart_image_recipe_offline.py`: exact Dockerfile COPY allowlist, new worker read-only permission, presence once, no build-time execution and preview metadata. **One additional test.**
- `tests/test_chart_build_context_offline.py`: context 4/5/6-file expectations, exact source copy, altered-worker forgery detection even with a rewritten manifest, missing staged file, and missing/symlinked/oversized original source. **Three additional tests.**
- `scripts/preview_chart_smoke_offline.py` and `tests/test_chart_smoke_preview_offline.py`: both zero-CSV and one-CSV strict allowlists updated; the same offline preview must still show zero Docker/network/model requests and destroy temporary contexts.

Previous baseline **193 tests** plus **four new tests** yields **197 expected**, pending actual verification on this Session 014 head. Do not report them as passed yet.

### First focused Codespaces checks

After fetching and tracking `origin/feature/session-014-chart-worker-image-staging`:

~~~bash
uv run --offline --locked python scripts/check_chart_image_recipe_offline.py
uv run --offline --locked python scripts/check_chart_build_context_offline.py
uv run --offline --locked python scripts/check_chart_smoke_preview_offline.py
uv run --offline --locked python scripts/check_chart_smoke_worker_offline.py
uv run --offline --locked python scripts/check_chart_wheel_lock_offline.py
git status --short --branch
~~~

Only proceed to full provider/validator/structural/offline regression once focused tests pass. GitHub Actions must be reviewed on a **draft PR** after Codespaces evidence is available. No PR should be merged automatically.

## Still needed before an explicitly authorized real Docker smoke test

1. Confirm current platform/base provenance and selected wheel **bytes**, not just lock metadata, with separately reviewed registry/download operations.
2. Define a builder whose private verified context stays alive through a bounded build, and establish enforceable build-time CPU/memory/network/wall-time policy with controlled cancellation, unique image tagging and cleanup. A client-side timeout alone is not enough to constrain BuildKit.
3. Define bounded, fake-tested runtime/container operations with unprivileged user, network disabled, no mounts/ports/secrets, limits on CPU/RAM/PIDs and wall time, and guaranteed stop/remove.
4. Design a trusted **size-bounded** PNG artifact channel and validate the returned image against the existing strict PNG checker. The gateway's shortened stdout is not adequate for base64 PNGs.
5. Review precise build/pull/run/extraction/cleanup commands and risks with the user for **fresh specific authorization**. Prior offline checks and historical API probes are not authorization.

**Resume checkpoint:** Session 014 branch created at clean `e0242d6`. Source, offline tests and docs are being prepared remotely. Await Codespaces focused verification; no Docker or model operations have been performed by this work.
