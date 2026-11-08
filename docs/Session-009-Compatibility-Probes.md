# Session 009 — One-request live compatibility probes (independent adaptation)

**Status:** Offline preparation and tests committed on the Session 009 feature branch; Codespace test results and live API access **not yet verified**. No model call has been made in this session.

## Goal and decisions

We will run one separately user-approved, explicitly billed-compatible API request per model role to verify the exact endpoint/model, provider-specific API shape, tool-call parsing for the three generators, and image/structured-JSON parsing for the Terra judge. This is a **transport/schema compatibility exercise, not a plotting-agent run, validator benchmark, or official grading reproduction**.

The project's user requires **an explicit new authorization before every live paid request**. If a call fails or its parser rejects the reply, the operator must not retry without a fresh approval. Do not run multiple model calls in parallel or in a loop.

| Order | Role | Requested direct API ID | Endpoint behavior tested |
| --- | --- | --- | --- |
| 1 | `agent_a` | `deepseek-flash` | Stateless Responses with inert `run_shell` function descriptor |
| 2 | `agent_b` | `gpt-5.6-luna` | OpenAI Responses function descriptor |
| 3 | `agent_c` | `glm-4.7-flash` | Z.ai Chat Completions function descriptor |
| 4 | `experimental_judge` | `gpt-6.1-terra` | OpenAI Responses, synthetic PNG, strict JSON error-family schema |

**Public API documentation is not account entitlement**. An unsupported-model/provider error is a compatibility result, never a reason to silently switch model ID.

Provider sources:
- https://api-docs.deepseek.com/updates/ — DeepSeek V4.1 Flash `deepseek-flash` moving alias
- https://api-docs.deepseek.com/guides/responses_api/ — stateless DeepSeek Responses and function calls
- https://developers.openai.com/api/docs/models/gpt-5.6-luna — OpenAI Luna model and Responses tools
- https://developers.openai.com/api/docs/models/gpt-6.1-terra — Terra image input and structured outputs
- https://docs.z.ai/api-reference/llm/chat-completion — Z.ai chat endpoint

## Safety invariants

1. `scripts/provider_compat_probe.py` **defaults to offline** and prints request metadata only. Importing or previewing never reads a key, sends an API request, sends a synthetic PNG, invokes a Docker sandbox, or executes a tool.
2. Live execution is possible **only with all** `--live --confirm-one-request --approve-model EXACT_ID` and one `--role`. A missing role, mismatched ID, incomplete flags or missing provider key blocks the call.
3. No automatic retry (`max_retries=0`), no agent loops, 60s timeout and maximum 512 generated tokens. Provider/model errors are not hidden by fallback. A failed/incomplete request can still be billed; inspect billing/console separately.
4. The CLI creates `output/provider_compat_<role>.json` with restrictive permissions and `O_EXCL` (never overwrites an earlier result). The entire `/output/*.json` is gitignored. Never move raw credentials or output into committed files.
5. Saved results contain **only** role/provider, requested and returned model IDs, normalized token usage, number/names of inert tool requests, strict-schema success for Terra, and any safe error *type*. Raw prompts, provider error messages, model text, tool arguments, PNG bytes and secrets are omitted.
6. Model-proposed tools are **never run**. A successful function-call parse only indicates compatibility with a tool descriptor, not that agent execution works.
7. Terra receives a small synthetic PNG and instructions for bars A=1 and B=2. A syntactically valid JSON verdict only confirms schema compatibility, **not** accuracy, sensitivity, specificity or MCC.
8. Original `workflow/generate.py`, `validator/solution.py`, human labels, Session 007 archive, and official model requirements stay unchanged.

## First, verify offline in Codespaces

Start from updated `main` and check out the Session 009 feature branch. Then run **only these no-model-request commands**:

```bash
git fetch origin --prune
git switch --track origin/feature/session-009-provider-compatibility
git status --short --branch
uv sync --locked
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python scripts/provider_compat_probe.py --role agent_a
uv run python scripts/provider_compat_probe.py --role agent_b
uv run python scripts/provider_compat_probe.py --role agent_c
uv run python scripts/provider_compat_probe.py --role experimental_judge
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
git status --short --branch
```

Expected previews: `mode=offline`, `network_requests=0`, one inert function descriptor on the first three roles and `structured_judgment=true` for Terra. Existing validator tests must remain passing. The new test count is to be verified, not assumed.

## Live-call approval gate — STOP after offline tests

No live command is approved or provided in this document. After confirming offline verification, present the **exact planned model**, fixed synthetic prompt, expected maximum output tokens, estimated/request charge basis and **one-request** consent question to the user. Only when that specific request is approved, provide the corresponding live CLI invocation. Next role needs a separate approval regardless of whether the prior request worked.

Record the response from `output/provider_compat_<role>.json` and identify whether a function call was actually returned for a generator; a text-only response is **inconclusive** for tool-call compatibility, not a pass. No automatic retries.

## After the four approved checks

Record per-model access and actual returned IDs/usage, any provider-specific incompatibility, cost provenance and needed fixes. Do not merge if tests or requested checks fail without explanation. The next independent phase is a task-aware bounded mini-SWE-agent controller using the pinned Assignment 1 Docker sandbox, followed by three independent plotting runs per authored task and a separately evaluated Terra judge.
