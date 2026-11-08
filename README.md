# CMU 11-768 Assignment 2 — Independent Evaluation Engineering

An independent, non-credit adaptation of [CMU 11-768 Assignment 2: Evaluating a Data-Visualization Agent](https://github.com/cmu-agents/assignment-2).

**Status:** Phase 1 (early) — offline evaluation infrastructure, mock-tested validator integration, and one verified Z.ai synthetic image probe. Real seed judgments and official-model-equivalent scoring remain unverified. We retained the **entire pinned official starter**, including the released agent trajectories, figures, human labels, evaluator, and Harbor examples. We do **not** use Modal for execution or model hosting.

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

## Session 009 — One-model-at-a-time compatibility probes (offline preparation)

Session 008's provider adapters are merged through PR #8 (`5833b2b`); its 27 provider tests, 49 validator tests, 5 infrastructure tests and dataset preflight passed locally, and GitHub Actions passed on the PR. Session 007 remains safely archived at `archive/session-007-20261107`.

Session 009 adds `scripts/provider_compat_probe.py`, an **offline-by-default** per-model compatibility preview and a strictly gated, one-request transport probe for a later separately authorized live check. For a fully offline preview, run:

```bash
uv run python scripts/provider_compat_probe.py --role agent_a
uv run python scripts/provider_compat_probe.py --role agent_b
uv run python scripts/provider_compat_probe.py --role agent_c
uv run python scripts/provider_compat_probe.py --role experimental_judge
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
```

The live path is **not authorized yet**. Every possibly billed call needs separate user approval for that exact model. There are no automatic retries, model-proposed shell commands are never executed, results are stored in ignored `output/*.json`, and full plotting-agent/Docker integration is still future work. See [docs/Session-009-Compatibility-Probes.md](docs/Session-009-Compatibility-Probes.md). Offline tests added in this branch remain **pending Codespace verification**.

### Session 009 model-switch preparation — Z.ai GLM-5.3-Flash

After a separately authorized `glm-4.7-flash` function-call probe failed with `RateLimitError` (zero retries), we selected paid `glm-5.3-flash` as Agent C's **current** requested model. The prior attempt is retained as historical evidence; an account-wide balance/quota problem could still affect the replacement model.

The new probe saves `output/provider_compat_agent_c_glm-5.3-flash.json` and **does not delete or overwrite** the previous `output/provider_compat_agent_c.json`. New offline tests cover this distinction. `reasoning_effort=low` is used for the GLM-5.3-Flash request because its thinking cannot be fully disabled; this is a transport smoke test, not a benchmark with default reasoning.

Run only these zero-network checks first on `feature/session-009-provider-compatibility`:

```bash
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python scripts/provider_compat_probe.py --role agent_c
uv run python scripts/provider_preflight.py
```

**No new live GLM-5.3-Flash request has been performed or authorized yet.** Its single-request test must be separately approved after Codespace offline verification. See [Session 009 compatibility probes](docs/Session-009-Compatibility-Probes.md).

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
