# CMU 11-768 Assignment 2 — Independent Evaluation Engineering

An independent, non-credit adaptation of [CMU 11-768 Assignment 2: Evaluating a Data-Visualization Agent](https://github.com/cmu-agents/assignment-2).

**Status:** Phase 1 (early) — reproducible offline exploration, deterministic execution checks, and mock-tested semantic integration; live vision validation remains unverified. We retained the **entire pinned official starter**, including the released agent trajectories, figures, human labels, evaluator, and Harbor examples. We do **not** use Modal for execution or model hosting.

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

**Review workflow:** develop on `feature/phase-0-offline-evaluation`, review the pull request, and merge manually when ready.
