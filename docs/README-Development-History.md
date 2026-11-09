# Historical README — development sessions through November 8, 2026

> Archived verbatim from the earlier root README before the project summary was reorganized. Some milestone descriptions below were written **before** the completed experiment, and their statements about untested or unfinished work are historical, not the current project status. See [the current README](../README.md) and [final report](../report.pdf) for completed outcomes.

---

# CMU 11-768 Assignment 2 — Independent Evaluation Engineering

## Status (2026-11-08): assignment complete on `finish-assignment`

**Read [`report.pdf`](report.pdf)** (source `report.tex`). `workflow check-submission` reports
*submission valid*: every Harbor task scores 1.0 with its oracle, mutants score 0.0
(`sum_units`) and 1.0 (`unrotated_labels`).

| Seed runs (110), judge GPT-6.1 Terra | baseline | final `validator/solution.py` |
| --- | ---: | ---: |
| execution_failure | 0.5945 | 1.0000 |
| wrong_data | 0.2363 | 0.7093 |
| wrong_chart | 0.6286 | 0.9512 |
| hard_to_read | 0.6345 | 0.8297 |
| **macro-MCC** | **0.5235** | **0.8726** |

Agents (DeepSeek Flash, GPT-5.6 Luna, GLM-5.3 Flash) run via
`uv run python -m workflow.sandbox_generate` in the Docker sandbox from `sandbox/`.
Judge settings: see the Terra block in `.env.example`. Not comparable to course scores
(different judge and agents). Working notes: `docs/report-notes.md`. AI use: `AI_USAGE.md`.
The session history below is the earlier offline-infrastructure phase.

An independent, non-credit adaptation of [CMU 11-768 Assignment 2: Evaluating a Data-Visualization Agent](https://github.com/cmu-agents/assignment-2).

**Status:** Offline evaluation infrastructure and a completed four-model API compatibility milestone, but no end-to-end chart-agent run or Terra judge accuracy benchmark. Official-model-equivalent scoring remains unverified. We retained the **entire pinned official starter**, including the released agent trajectories, figures, human labels, evaluator, and Harbor examples. We do **not** use Modal for execution or model hosting.

## Our learning goals

- Evaluate data-visualization agent trajectories and figures against human judgments.
- Measure per-family confusion matrices, Matthews correlation coefficient (MCC), and macro-MCC.
- Diagnose false positives, false negatives, label imbalance, and judge failures.
- Build adversarial tasks and compare model-based evaluation with deterministic Harbor verifiers.
- Reuse the Docker sandbox developed in [our Assignment 1](https://github.com/xqzr2000/cmu-11-768-assignment-1), with a pinned Git dependency rather than copied code.

## Proven vs. not yet proven

- **Provided:** 110 public seed trajectories and their human labels, the official scoring workflow, and Harbor example tasks.
- **Verified outside this repository:** Z.ai `glm-4.7-flash` chat completion and structured function calling using `ZAI_API_KEY` in Codespaces. Intermittent HTTP 429 / error 1305 has been observed.
- **Not yet verified here:** a complete local mini-SWE-agent run, generated visualizations from GLM, a vision judge, full Harbor run, or reproducibility of the course's private grading score.

## Quick start — offline, no API or Modal

In GitHub Codespaces, open this repository and let the devcontainer install dependencies. Or use Python 3.12 with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked
uv run python scripts/offline_preflight.py
uv run python -m unittest discover -s tests -p 'test_offline_*.py'
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
```

`offline_preflight.py` checks the public run/label inventory, label schema, and PNG file headers without calling a model. It **does not** manufacture validator predictions or use human labels as model inputs.

The deterministic execution checks in `validator/solution.py` reject missing or undecodable `figure.png` files without any model calls. On decodable images the solution now delegates `wrong_data`, `wrong_chart`, and `hard_to_read` judgments to the supplied `validator.baseline` VLM methods. The **offline semantic tests use mocked model responses**; they demonstrate call ordering and schema, not chart-judging accuracy. Full `validator.runner` execution with normal PNGs will require a compatible, verified image-capable `VALIDATOR_BASE_URL` / `VALIDATOR_API_KEY` / `VALIDATOR_MODEL` setup. Without that endpoint, the model error intentionally propagates instead of silently accepting charts. The assignment's fixed evaluator model is Qwen/Qwen3-VL-30B-A3B-Instruct-FP8; do not substitute another judge and claim official equivalence.

The original course scorer is also available:

```bash
uv run python -m workflow --help
uv run python -m workflow score --help
```

To score a validator, first generate predictions independently, then use `python -m workflow score --labels seed_labels.json --predictions <path>`. The released labels are for measurement and analysis, not for hard-coded prediction lookup.

## Session 004: Z.ai visual-understanding smoke test (offline first)

This optional **independent experiment** uses `glm-4.6v-flash` as a vision judge; it is **not** the assignment-required `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` and does not alter `validator/model.py` or the official evaluator. Z.ai's [model guide](https://docs.z.ai/guides/vlm/glm-4.6v) documents image input, [API quick start](https://docs.z.ai/guides/overview/quick-start) supports the OpenAI client, and the [pricing page](https://docs.z.ai/guides/overview/pricing) currently lists `GLM-4.6V-Flash` as free. Check your account terms and rate limits before invoking it; free listing does not guarantee unlimited access.

Offline dry run (default; **zero API calls**, no key required):

```bash
uv run python scripts/zai_vision_probe.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
```

The probe creates a **256×256 synthetic chart** in memory with a tall blue bar and short orange bar, then assembles the official OpenAI-compatible `image_url` data-URL payload. It prints payload metadata, **not** base64 image data or secrets.

For an optional **single** live image request, set `ZAI_API_KEY` through Codespaces Secrets (or in a local, untracked `.env` file), then **explicitly opt in twice**:

```bash
uv run python scripts/zai_vision_probe.py --live --confirm-one-request
```

The live probe sends **at most one chat completion attempt** to `https://api.z.ai/api/paas/v4/` using model `glm-4.6v-flash`, `max_tokens=64`, `max_retries=0`, a 45-second client timeout, and disabled thinking. It reports the answer and any returned token usage, not credentials or raw error bodies. HTTP 429/auth/unsupported-image responses fail visibly and are **not retried automatically**. A failed/ambiguous answer is not reported as a passed vision test. No seed artifact, human label, or full validator sweep is sent in this probe.

**Do not use Z.ai results as official Qwen-equivalent scores.** Running the full seed validator with a different provider would require separate provider configuration and compatibility tests (the baseline's context-overflow fallback uses vLLM-only tokenizer routes). Keep model provenance on any experimental predictions.

## Session 005 — First real seed-figure evaluation (two-case pilot)

The independent Z.ai pilot sends **one selected seed run** to `glm-4.6v-flash`, not the official Qwen3-VL checkpoint. Its default command is an offline preview; it will never read human labels or make network calls. Pilot selection is limited to released runs `004` and `008` to bound the experiment, not to hardcode any prediction.

**1. Offline first (zero network requests):**

```bash
uv run python scripts/zai_seed_pilot.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/offline_preflight.py
```

The preview loads the authentic `Run` objects and exercises `validator.solution.validate` with fake completions. Its metadata shows **three potential multimodal requests per run**, instructions/trajectory lengths, filenames and byte counts of embedded CSV/PNG data. It does **not** send request content anywhere. To inspect these existing public fixtures yourself, use `artifacts/004/result.json`, `artifacts/008/result.json`, `inputs/008/data.csv`, and their associated `figure.png` files.

**2. Optional live mode, after inspecting the preview and consenting to send the public run's instructions, full agent trajectory, input file contents and figure to Z.ai:**

```bash
# At most 3 completions for run 004. Requires ZAI_API_KEY.
uv run python scripts/zai_seed_pilot.py --run-id 004 --live --confirm-three-requests

# Run 008 only as a separate, deliberate later invocation:
uv run python scripts/zai_seed_pilot.py --run-id 008 --live --confirm-three-requests
```

The Z.ai host and model are fixed in the script. OpenAI client automatic retries are off, timeout is 60s, output is capped at 250 tokens per request, and the code blocks a fourth attempt, including baseline overflow retries that expect the upstream vLLM tokenizer. The code also refuses to overwrite existing per-run output files to prevent accidental paid reruns. HTTP failures or ambiguous non-YES/NO answers abort without pretending that the run was acceptable. The provider's GLM-4.6V-Flash pricing currently lists a free tier, but access and rate limits can change.

Successful live predictions are stored locally in ignored files `output/session005_zai_<run_id>_predictions.json` and `output/session005_zai_<run_id>_metadata.json`, using the exact official `PredictionFile` schema. **Human labels are not loaded during inference.**

**3. Compare offline, only after the predictions exist:**

```bash
uv run python scripts/zai_seed_pilot.py --run-id 004 --compare
uv run python scripts/zai_seed_pilot.py --run-id 008 --compare
```

The compare command has no model client or network access; it reads `seed_labels.json` post-hoc and reports predicted families, human families, missed errors and false alarms. **Two preselected runs are not representative and should not be presented as a meaningful MCC.** Neither these independent GLM results nor the API-reported model ID establishes official Qwen3-VL equivalence. The general `validator/model.py` remains unchanged.

## Session 005: optional OpenAI API integration (separate provider)

We diagnosed the first real Z.ai GLM-4.6V-Flash seed-004 reply: the API returned one response, but the model used all 250 output tokens and did not begin with the expected YES/NO prefix. Instead of replacing the course validator or Z.ai provider, we added an **independent OpenAI pilot** using `gpt-5.4-mini`, a model with vision and [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs). This is **not** the assignment-required `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8`.

**OpenAI API credentials for Codespaces:**

1. Create an API key in the [OpenAI API dashboard](https://platform.openai.com/api-keys), and set a suitable usage budget in the API platform. **ChatGPT subscriptions do not automatically fund API calls**.
2. In [GitHub Codespaces secrets](https://github.com/settings/codespaces), create `OPENAI_API_KEY` and grant repository access to `xqzr2000/cmu-11-768-assignment-2`. **Do not** paste the key into source code or the chat.
3. **Stop and restart your existing Codespace** to inject the new secret. A full Rebuild Container is **not needed** for just a new Codespaces secret. Alternatively, put the key in a local, untracked `.env` file; `.gitignore` already excludes it.
4. Check secret status without exposing the key:

```bash
uv run python scripts/openai_seed_pilot.py
```

The default command sends **zero requests** and previews the exact selected public run/family (by default seed `004`, `wrong_data`). No new packages are necessary: `openai==2.54.0` was already pinned by the official starter. This change does not modify `.devcontainer/devcontainer.json`, `validator/model.py`, `ZAI_API_KEY`, the Qwen model setting, or the seed fixtures.

**Offline verification, before any API call:**

```bash
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/openai_seed_pilot.py --run-id 004 --family wrong_data
```

**One opt-in live OpenAI question**, only after reviewing the preview and API usage/billing:

```bash
uv run python scripts/openai_seed_pilot.py --run-id 004 --family wrong_data \
  --live --confirm-one-request
```

The API client uses **only** `https://api.openai.com/v1/`, the fixed `gpt-5.4-mini` model, an image+text Chat Completions request, a strict `{has_error: boolean, evidence: string}` JSON schema, `reasoning_effort="none"`, at most 400 completion tokens, a 60-second timeout and **no automatic retries**. At most **one** model request can be attempted per invocation. It rejects non-JSON replies, refusals, truncated outputs and type/schema violations. Never send raw provider error bodies or keys to the console.

Successful output is an **individual family decision**, stored only in ignored `output/session005_openai_004_wrong_data_decision.json`, not a complete official `PredictionFile`. The program refuses to overwrite that file and reports the model/usage for provenance. The prompt contains task instructions, original trajectory, optional input-file contents and a PNG. It **never loads human labels in live or dry-run mode**.

**Compare offline after a successful saved decision only:**

```bash
uv run python scripts/openai_seed_pilot.py --run-id 004 --family wrong_data --compare
```

The independent `--compare` path reads human labels locally, reports a single family decision's TP/FP/FN/TN, and makes no model requests. A single selected example is not evidence of MCC or model generalization. The existing Z.ai pilot and official Qwen3-VL configuration remain intact.

## Session 010 — Offline-first chart controller and chart environment

PR #9 merged Session 009 into `main` at `65b0a49`; PR #10 merged the completed Session 010 offline infrastructure at `19e0a27`. Session 011 now develops on `feature/session-011-chart-runtime`.

**Verified in Codespaces: 82/82 Session 010 offline tests passed** after hash-lock wiring, with a clean working tree. The suites cover the controller (11), fake-Docker gateway (14), bounded task CSV/PNG validation (16), file staging and extraction helper (12), inert Dockerfile recipe (12), and private build context (17). Provider **37/37**, validator **49/49**, and structural **5/5** regressions also passed, totaling **173/173** offline tests.

The following components remain separately gated and **do not yet form a live agent**:

- `integrations/chart_controller.py`: provider conversation replay and strict turn/tool budgets, with no model transport.
- `integrations/sandbox_gateway.py`: explicit sandbox launch and per-command approval; `network="none"`, no host mounts or ports; tested with fake Docker only.
- `integrations/task_artifacts.py`: bounded task-local CSV snapshots and strict PNG/JSON-envelope validation.
- `integrations/chart_transfer.py` and `scripts/figure_extract_worker.py`: private temporary host-file staging and a fixed bounded PNG extraction protocol, not connected to Docker.
- `integrations/chart_image_recipe.py`: inert digest-shaped Python 3.12 Dockerfile, direct plotting library pins and unprivileged runtime.
- `integrations/chart_build_context.py`: temporary, verified context containing only the Dockerfile, approved CSVs, and trusted extraction helper. No Docker build has been attempted.

**Supply-chain checkpoint:** User Codespace registry inspection verified an `x86_64` (`linux/amd64`) host, the official Python image's **multi-platform index** `sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54`, and its distinct **AMD64 image manifest** `sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177` (version `3.12.16-slim-trixie`). No image was pulled, built or launched.

**Chart-only wheel hash file (audit verified in Codespaces):** `requirements/chart-cp312-linux-amd64.txt` records the exact versions and selected wheel hashes for **14 plotting packages** derived from the existing committed `uv.lock`: four direct and ten transitive. The offline checker `scripts/check_chart_wheel_lock_offline.py` re-derives that dependency closure and rejects missing, extra, modified or ambiguously marked dependencies. CI runs the audit. In Codespaces, run:

```bash
uv run python scripts/check_chart_wheel_lock_offline.py
```

**Verified in Codespaces:** The audit checked all **14 package hashes** (4 direct, 10 transitive) against the committed `uv.lock` and reported **PASS**. This was an additional metadata audit after the existing **77/77 offline tests**, not a seventh set of counted unit tests. It performed no PyPI download, pip installation, Docker command, or model request. The hash-locked Dockerfile and vetted private-context integration passed **29/29 focused Codespace offline tests** (12 image recipe, 17 context), and the 14-wheel metadata audit passed again. The subsequent full offline regression passed **173/173** tests; these checks still do not establish wheel download integrity, successful installation or an actual Docker image.

See [Session 010 supply-chain provenance](docs/Session-010-Supply-Chain.md) for full observed digests, platform evidence, package closure and remaining build-trust gaps.

**Session 010 finished:** PR #10 [merged](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/10), CI passed, and the user cleaned the old local/remote branch. See [Learning Progress](docs/Learning-Progress.md) for the completed milestone and the active Session 011 handoff.

## Session 012 — Offline chart image and plotting smoke-test preflight (merged PR #12)

On `feature/session-012-docker-smoke-preflight`, the user verified the existing image recipe **13/13**, private context **19/19** offline tests and the separate **14/14** wheel metadata audit in Codespaces; Git stayed clean. The latest change adds `scripts/preview_chart_smoke_offline.py`, a **zero-Docker/no-model** JSON review of the fixed Dockerfile and short-lived private contexts for synthetic zero-CSV and one-CSV tasks. It has **seven new offline tests** in `tests/test_chart_smoke_preview_offline.py`, a guarded test script and CI wiring. **Verified in Codespaces:** the seven new preview tests passed **7/7**; recipe **13/13**, build-context **19/19**, and 14-wheel metadata audit passed in an earlier focused run. The preview emitted exact three-file/four-file zero/one-CSV manifests, consistent Dockerfile hashes, cleanup confirmation and zero Docker/model/network operations. The user then ran the **complete 185/185 offline regression**, and all tests passed at `c677bca`: 94 chart/controller infrastructure, 37 provider, 49 validator and 5 structural tests.

See [Session 012 smoke-test preflight and approval gates](docs/Session-012-Docker-Smoke-Preflight.md). The previously observed Python AMD64 manifest is only a review candidate. No real image pull/build/launch, wheel installation, PNG from Docker or model API call is authorized. The preview prints metadata and inert Dockerfile text, *not* an execution-ready Docker build context. Dataset preflight (110 runs, 98 figures, 110 labels), 14-package wheel metadata audit, and four-role zero-network provider preview also passed; Git was clean. **PR #12 merged into main at `1118bcd` on 2026-11-08 UTC; main-branch CI passed.** Historical source/preflight evidence remains offline-only. Real Docker operations still require a separate exact-command review and explicit authorization.

## Session 014 — Stage the trusted smoke worker in a planned chart image (offline only)

Starting from clean merged main at `e0242d6`, we created `feature/session-014-chart-worker-image-staging` and merged [PR #14](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/14) at **`39fbbf9`**. Its latest PR-head [CI run 42518103408](https://github.com/xqzr2000/cmu-11-768-assignment-2/actions/runs/42518103408) and post-merge main [CI run 42518586284](https://github.com/xqzr2000/cmu-11-768-assignment-2/actions/runs/42518586284) both passed. This first slice **changes the fixed Dockerfile text and private staging plan only**: the trusted, version-controlled `scripts/chart_smoke_worker.py` is copied as `trusted/smoke_chart.py` into the short-lived context and declared as a read-only `/opt/assignment/smoke_chart.py` in the *future* chart image. The context verifies script bytes against source even if an attacker rewrites the staged file's declared SHA-256.

The zero-/one-CSV context counts become **4/5** files (previously 3/4). **Verified in Codespaces at clean tracking feature head `118ea8a`: 51/51 focused chart tests and 197/197 full offline tests passed** (106 chart/controller infrastructure, 37 mocked providers, 49 validator, 5 structural). The separate 14/14 wheel-lock metadata audit and dataset (110 runs, 98 figures, 110 labels, 16 acceptable) and four-role zero-network preflights also passed. No Docker build, image pull, container launch, wheel download or model request has been performed. See the [Session 014 staging report](docs/Session-014-Chart-Worker-Image-Staging.md) and [current learning journal checkpoint](docs/Learning-Progress.md) for exact files, merge evidence, remaining Codespaces cleanup, and the proposed offline Session 015 build-lifecycle, runtime isolation, artifact-channel and Stage B approval requirements.

**Session 013 completed:** [PR #13 merged](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/13) at `e0242d6` with post-merge CI success; the feature branch was cleaned up locally and remotely.

## Session 013 — Trusted synthetic plotting smoke worker (offline only)

From clean synchronized main at `1118bcd`, we created `feature/session-013-docker-smoke-readiness` for the next *offline* readiness slice. The new fixed `scripts/chart_smoke_worker.py` draws a small 640×480 PNG from hard-coded values using the Matplotlib Agg backend; it never reads task data, executes Docker, calls a model, or accepts CLI parameters. It creates `figure.png` exclusively, refuses overwrite, and enforces a 2 MiB cap.

The eight new host-only tests check the PNG validator contract, the trusted extractor/envelope round trip, existing-file/symlink handling, oversized-output cleanup, fixed CLI behavior, and prohibited imports. CI runs the zero-test-guarded `scripts/check_chart_smoke_worker_offline.py`. **Verified in Codespaces on feature head `200d195`: focused smoke-worker tests 8/8 passed and the complete offline regression passed 193/193** (102 chart/controller infrastructure, 37 provider, 49 validator, 5 structural). A separate 14/14 chart wheel lock metadata audit, dataset preflight (110 runs, 98 figures, 110 labels, 16 acceptable) and four-role zero-network provider preview passed. Git remained clean and synchronized. This remains host/mock/fake evidence only, not a real Docker smoke run or official accuracy benchmark. [Initial draft PR #13 CI run 42516818263](https://github.com/xqzr2000/cmu-11-768-assignment-2/actions/runs/42516818263) succeeded (20/20 steps) at head `fc571b6`; documentation-only commits after this evidence require a separate latest-head CI check. Do not merge automatically.

See [Session 013 readiness plan](docs/Session-013-Docker-Smoke-Readiness.md) for outstanding base-image and wheel-byte provenance, BuildKit resource/time controls, future fixed-worker staging, container isolation, output extraction and exact-command approval gates. **Historical Session 013 limitation:** the worker was not included in the *then-proposed* image context; Session 014 subsequently added it to the inert trusted context allowlist. **No image has actually been built.** No real Docker build/run or new model API requests are authorized.

## Session 011 — Empty-input chart runtime support (full offline regression passed)

The official authored-task schema already accepts `inputs=[]` or an omitted input list, but our Session 010 snapshotter, transfer staging and private context previously required one CSV, and the inert Dockerfile's glob-based chmod would fail if the directory were empty. On `feature/session-011-chart-runtime` we now allow **0–8** CSV files while retaining file safety checks, a strictly allowlisted build context, the pinned plotting requirements file, and a fixed empty-file-safe `find ... -exec chmod` step. No tasks automatically enter Docker or a model API.

New offline regression cases cover zero-input descriptors, private staging and cleanup, exact three-file build contexts with empty `inputs/`, rejection of unexpected input files and Dockerfile handling. **Verified in Codespaces at `c1f5602`: all 62/62 focused offline tests passed** (17 task artifacts, 13 transfer, 13 recipe, 19 context). The separate 14-package wheel metadata audit also passed. Git was clean and synchronized. **Full Codespaces regression has now passed 178/178 offline tests** (87 chart/controller infrastructure, 37 provider, 49 validator, 5 structural), along with dataset preflight and the four-role zero-network provider preview. **Next: review a draft Session 011 PR and GitHub Actions**. The earlier **173/173** Session 010 result remains historical. These tests do not demonstrate an actual image build or authorize Docker/model operations.

No additional model API requests, real Docker builds, sandbox launches, live chart-generation runs, or Terra accuracy evaluations are authorized by Session 010's offline verification. The official Modal runner and assignment requirements are unchanged.

See [Session 010 engineering design](docs/Session-010-Controller-Design.md) and [Learning-Progress.md](docs/Learning-Progress.md).

## Session 009 — Completed four-model live API compatibility checks

Session 008's offline provider-adapter foundation was merged via PR #8 (`5833b2b`). Session 007's unmerged wrong-chart experiment is preserved at `archive/session-007-20261107`.

**Session 009 objective met:** All four *current* model roles passed one separately user-authorized live compatibility request each. The three chart-generator providers returned function-call descriptions that the adapters parsed; the experimental Terra judge accepted a synthetic PNG and returned strict JSON. No tool request was executed, no model-generated chart was produced and no judge accuracy or MCC was measured.

| Role | Requested / reported model | Live compatibility |
| --- | --- | --- |
| Agent A | `deepseek-flash` | Responses API tool call parsed (405 tokens) |
| Agent B | `gpt-5.6-luna` | Responses API tool call parsed (127 tokens) |
| Agent C | `glm-5.3-flash` | Z.ai Chat Completions tool call parsed (227 tokens) |
| Experimental judge | `gpt-6.1-terra` | Synthetic PNG + strict JSON schema parsed (288 tokens) |

A separate historical free-model attempt to `glm-4.7-flash` failed with `RateLimitError` and **zero retries**; it was preserved instead of overwritten. The paid replacement `glm-5.3-flash` is the current Agent C model, using `reasoning_effort=low` for this bounded transport test. The previous failure's exact root cause remains unknown.

The feature branch's Codespace verification passed **37/37 mocked provider tests and 49/49 validator regression tests** (86/86), plus four zero-network model previews. Run the zero-network checks at any time:

```bash
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/provider_preflight.py
uv run python scripts/provider_compat_probe.py --role agent_c
```

The offline-default probe script refuses live requests unless the role, consent flags, **exact model ID** and provider secret match. It saves per-model results to ignored `output/provider_compat_<role>_<model>.json` files, recognizes older role-only results, refuses repeated same-model attempts, has **zero automatic retries**, and never executes a model-suggested command. The earlier five one-request user approvals are all consumed; **any new model API request requires separate fresh approval**.

Read the [Session 009 compatibility experiment report](docs/Session-009-Compatibility-Probes.md) and [learning journal](docs/Learning-Progress.md). Next: review this branch in a PR, then design a separately tested bounded chart-generation controller that uses the pinned Assignment 1 Docker sandbox without exposing credentials to it.

## Session 008 — offline-only multi-provider adapters (completed, merged via PR #8)

This is an **independent research adaptation**. The course requires its Qwen3-VL validator and fixed generation models; we have **not replaced or re-scored** the official validator. Session 007's wrong-chart v1/v2 findings remain separate on their feature branch.

Four experimental roles are configured under `integrations/models.py`:

| Role | Provider | Requested API model | Request style |
| --- | --- | --- | --- |
| Agent A | DeepSeek | `deepseek-flash` | Stateless Responses |
| Agent B | OpenAI | `gpt-5.6-luna` | Responses |
| Agent C | Z.ai | `glm-5.3-flash` | Chat Completions (low reasoning effort) |
| Experimental judge | OpenAI | `gpt-6.1-terra` | Responses + image + JSON schema |

This phase adds provider request builders and normalizers, an opt-in one-request transport helper, an inert function-call representation, and strict local judge-response checking. It **does not yet run agents, execute model tool calls, host models, or make live API requests**. Existing `workflow/generate.py` remains a Modal runner; a future task will integrate the pinned Assignment 1 Docker sandbox.

**Verify offline (no provider credentials required, no network requests from test code):**

```bash
uv sync --locked
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python scripts/provider_preflight.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python scripts/offline_preflight.py
```

All live transport calls require `live=True`, `confirm_one_request=True`, an appropriate provider API key, and a separate deliberate caller. The adapters never run tools automatically. **No live CLI command is provided or authorized in this phase.**

See [docs/Provider-Migration-Plan.md](docs/Provider-Migration-Plan.md) for API details, output formats, security constraints, and the first PR acceptance checklist. Offline test results remain **unverified until executed in Codespaces or CI**.

## Development phases

1. **Phase 0 (this PR):** preserve upstream, pin sandbox dependency, validate offline dataset, establish Docker-ready Codespace and CI.
2. **Phase 1:** inspect seed cases; run and score an independent baseline (requires a validated multimodal inference endpoint).
3. **Phase 2:** improve evaluator, compare held-out performance and error evidence.
4. **Phase 3:** port the official mini-SWE-agent workflow to our Docker runtime and connect Z.ai GLM-4.7-Flash with bounded retries and resume.
5. **Phase 4:** design new tasks, human-label runs, package Harbor tasks, test oracle and mutant verifiers, and report limitations.

### Model policy

The official assignment fixes **Qwen/Qwen3-VL-30B-A3B-Instruct-FP8** as validator and three generation models: **Qwen/Qwen2.5-Coder-3B-Instruct**, **mistralai/Ministral-3-14B-Instruct-2512**, and **zai-org/GLM-4.7-Flash**. Hosted Z.ai `glm-4.7-flash` is an experimentally verified accessible generation endpoint, but is **not a verified exact-match reproduction** of the official deployment. We will disclose endpoint and model substitutions and never compare numbers as if setups were identical.

See [docs/PHASE-0.md](docs/PHASE-0.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/UPSTREAM.md](docs/UPSTREAM.md). The unchanged [official assignment instructions](ASSIGNMENT.md) remain the reference for course-specific requirements and the original Modal commands; those commands are **not** our planned execution path.

**Secrets:** set `ZAI_API_KEY` through Codespaces Secrets for later phases. No API key is needed for Phase 0. Never commit `.env` or pass credentials into an agent task container.

**Review workflow:** develop each learning milestone on its own `feature/session-...` branch, review the pull request and offline CI, then merge manually when ready.
