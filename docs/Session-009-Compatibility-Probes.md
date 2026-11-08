# Session 009 — One-request live compatibility probes (independent adaptation)

**Status (2026-11-07):** Session 009 offline preparation verified in Codespaces (**34/34** provider tests and **49/49** validator tests passed; four request previews reported zero network requests). Two separately authorized live compatibility requests **succeeded**: DeepSeek `deepseek-flash` (Agent A) and OpenAI `gpt-5.6-luna` (Agent B). The separately authorized Z.ai `glm-4.7-flash` (Agent C) call **failed with `RateLimitError` and zero retries**; its model/tool compatibility remains unverified. Terra has not been called; its access remains unverified. **New Agent C configuration:** `glm-5.3-flash` with low reasoning effort; its migration passed **37/37** provider tests, **49/49** existing validator tests and offline request previews in Codespaces. **The GLM-5.3 live request is not yet authorized or attempted.**

## Goal and decisions

We will run one separately user-approved, explicitly billed-compatible API request per model role to verify the exact endpoint/model, provider-specific API shape, tool-call parsing for the three generators, and image/structured-JSON parsing for the Terra judge. This is a **transport/schema compatibility exercise, not a plotting-agent run, validator benchmark, or official grading reproduction**.

The project's user requires **an explicit new authorization before every live paid request**. If a call fails or its parser rejects the reply, the operator must not retry without a fresh approval. Do not run multiple model calls in parallel or in a loop.

| Order | Role | Requested direct API ID | Endpoint behavior tested |
| --- | --- | --- | --- |
| 1 | `agent_a` | `deepseek-flash` | Stateless Responses with inert `run_shell` function descriptor |
| 2 | `agent_b` | `gpt-5.6-luna` | OpenAI Responses function descriptor |
| 3 | `agent_c` | `glm-5.3-flash` | Z.ai Chat Completions function descriptor, `reasoning_effort=low` |
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
4. Since the model migration, the CLI creates `output/provider_compat_<role>_<model>.json` with restrictive permissions and `O_EXCL` (never overwrites an earlier result). It also refuses a repeated request when a legacy `provider_compat_<role>.json` already contains that same model ID. The original three legacy results remain untouched, including GLM-4.7's failed attempt. The entire `/output/*.json` is gitignored. Never move raw credentials or output into committed files.
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

Record the response from `output/provider_compat_<role>_<model>.json` and identify whether a function call was actually returned for a generator; a text-only response is **inconclusive** for tool-call compatibility, not a pass. No automatic retries.

## Verified live compatibility: Agent A, DeepSeek

**Date:** 2026-11-07 (America/Vancouver; user Codespace transcript). The user separately authorized exactly one potentially billed DeepSeek call, after confirming the environment key existed without printing it.

| Field | Observed |
| --- | --- |
| Role | `agent_a` |
| Requested / reported model | `deepseek-flash` / `deepseek-flash` |
| Provider interface | Responses |
| Status | `completed` |
| Function calls | One inert `run_shell` request |
| Parsed compatibility | `expected_tool_called=true`, `tool_call_compatibility=true` |
| Usage | 346 input tokens, 59 output tokens, 405 total tokens |
| Retries / commands actually executed | 0 / 0 |
| Local ignored result | `output/provider_compat_agent_a.json` |
| Confirmed Git status after the request | Clean / tracking remote |
| Monetary charge | Not independently verified |

The model returned one function call and the normalized adapter parsed it. The probe **did not execute a shell command** or run a Docker container. This proves only a successful one-turn live API/function-call compatibility probe, not the chart-making controller, complete tool-call loop, successful plotting, or judge/metric accuracy. The reported model string does not independently identify the checkpoint behind a moving alias.

**The previously approved DeepSeek request has been consumed.** Do not issue any retry or Luna/GLM/Terra request without another explicit one-request approval.

## Verified live compatibility: Agent B, OpenAI Luna

**Date:** 2026-11-07 (America/Vancouver, user Codespace transcript). The user separately and explicitly authorized one OpenAI Luna request with no retries and no tool execution; confirmed `OPENAI_API_KEY` was available without showing its value.

| Field | Observed |
| --- | --- |
| Role | `agent_b` |
| Requested / reported model | `gpt-5.6-luna` / `gpt-5.6-luna` |
| Provider interface | OpenAI Responses |
| Status | `completed` |
| Function calls | One inert `run_shell` request |
| Parsed compatibility | `expected_tool_called=true`, `tool_call_compatibility=true` |
| Usage | 94 input tokens, 33 output tokens, 127 total tokens |
| Retries / commands actually executed | 0 / 0 |
| Local ignored result | `output/provider_compat_agent_b.json` |
| Confirmed Git status after request | Clean / tracking remote |
| Monetary charge | Not independently verified |

This confirms actual one-turn API/function-call interoperability and the local parser for Luna, but **not** multi-turn tool execution, plotting quality, Docker sandbox integration, or human-label judgment. The Luna request's authorization has been consumed. Z.ai GLM and OpenAI Terra each require their own separately approved request.

## Blocked live compatibility: Agent C, Z.ai GLM

**Date:** 2026-11-07 (America/Vancouver; user Codespace transcript). User separately authorized exactly one potentially billed request to `glm-4.7-flash`, no retries or shell execution, and confirmed `ZAI_API_KEY` was configured without displaying its value.

| Field | Observed |
| --- | --- |
| Role | `agent_c` |
| Requested model | `glm-4.7-flash` |
| Provider / API style | Z.ai / Chat Completions |
| Status | `failed` |
| Error type | `RateLimitError` |
| Retry attempts | 0 |
| Provider-reported model / token usage | Not returned |
| Function-call compatibility | **Not tested** — no parseable response |
| Local ignored result | `output/provider_compat_agent_c.json` |
| Git status afterward | Clean and synchronized |
| Billing | May have been billed; actual charge not verified |

`RateLimitError` alone cannot determine whether the account encountered transient request throttling, a credit/balance restriction, a limit window, or another Z.ai quota condition. The probe intentionally records only the Python exception type and does not retain the vendor's business error code, body, or headers. Consequently **do not assert Z.ai model incompatibility** from this result.

Safe next steps: inspect Z.ai account dashboard for key class/plan, standard API balance or quota, per-model rate/concurrency limits and usage/failure records. Do not reveal API keys or sensitive logs. There is no permission to retry this request or substitute models; any follow-up live model request requires a fresh explicit user approval.

## Agent C replacement selected — GLM-5.3-Flash

**Decision (2026-11-07, America/Vancouver):** User requested a switch from the free `glm-4.7-flash` to paid `glm-5.3-flash` and compatibility testing after the previous attempt failed with `RateLimitError`. This is a **new model configuration**, not a retry of the rejected request.

Code changes on `feature/session-009-provider-compatibility`:
- `integrations/models.py`: Agent C now requests `glm-5.3-flash`; all other roles, keys, and base URLs unchanged.
- `integrations/providers/zai.py`: Keep native Chat Completions plus function descriptor; send `reasoning_effort=low` through OpenAI SDK `extra_body` to bound mandatory model reasoning in a short one-turn test. The default `max` reasoning could use the 512-token budget before producing a tool call.
- `scripts/provider_compat_probe.py`: Save the new test to **`output/provider_compat_agent_c_glm-5.3-flash.json`**, without changing `output/provider_compat_agent_c.json` (the `glm-4.7-flash` `RateLimitError` record). Same-model legacy records still prevent repeat requests, and no automatic retry is possible.
- Offline tests update model assertions and verify preservation of the older GLM record and rejection of attempted repeated probes.
- No changes to course runner, official judge, sandbox integration, human labels or metrics. Changing a model may improve access, but does not prove that the previous `RateLimitError` was model-specific.

**Verification (2026-11-07 America/Vancouver, supplied Codespace log):** The migration has passed **37/37** mocked provider tests and **49/49** offline validator regression tests (86/86 total). The dedicated Agent C preview returned `glm-5.3-flash`, `chat_completions`, `max_output_tokens=512`, inert `run_shell`, and `network_requests=0`. The four-model registry preflight also reported zero model requests. Final Git status was clean and synchronized. **No live GLM-5.3-Flash request has been made or authorized yet**; exact account access and function-call support remain unknown. Every potentially billed live call needs fresh per-model authorization, with zero retries and no tool execution.

## After the four approved checks

Record per-model access and actual returned IDs/usage, any provider-specific incompatibility, cost provenance and needed fixes. Do not merge if tests or requested checks fail without explanation. The next independent phase is a task-aware bounded mini-SWE-agent controller using the pinned Assignment 1 Docker sandbox, followed by three independent plotting runs per authored task and a separately evaluated Terra judge.
