# Session 008 — Hosted-provider adapter migration (independent research)

**Status:** Initial provider-adapter implementation committed; user Codespace offline verification **pending**. No live calls, no agent runs, no full Terra judgment or new score claimed.

## Scope and departure from the course

This is an **independent, no-Modal adaptation** of CMU 11-768 Assignment 2. The official release requires Qwen3-VL as its judge and specifies its own chart generators. The original assignment text and original Modal entry points are preserved; our new models are **not the official judge/generator setup**. All experimental outcomes must carry provider/model provenance and must not be reported as official-grading results.

| Role | Provider | Requested direct API ID | API style | Key |
| --- | --- | --- | --- | --- |
| Agent A | DeepSeek | `deepseek-flash` | Responses (stateless) | `DEEPSEEK_API_KEY` |
| Agent B | OpenAI | `gpt-5.6-luna` | Responses | `OPENAI_API_KEY` |
| Agent C | Z.ai | `glm-4.7-flash` | Chat Completions | `ZAI_API_KEY` |
| Experimental judge | OpenAI | `gpt-6.1-terra` | Responses, image + structured JSON | `OPENAI_API_KEY` |

Use direct-provider IDs, not decorative `OpenAI/`, `DeepSeek/` or `zai-org/` prefixes. Record the **requested ID and provider-reported ID** separately, as aliases can change. Do not invent a served version when the API omits one.

Provider documentation checked when planning:
- [DeepSeek Responses API](https://api-docs.deepseek.com/guides/responses_api/): `https://api.deepseek.com`, stateless message history, functions
- [OpenAI GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna): Responses and function calling
- [OpenAI GPT-6.1 Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra): image inputs, structured output, Responses for tool calling
- [Z.ai Chat Completion API](https://docs.z.ai/api-reference/llm/chat-completion): chat tool-call messages

These documents describe provider capabilities; no access or exact deployed version has been confirmed on the user's accounts in Session 008.

## What the first PR introduces

New `integrations/models.py` declares an immutable role registry. `integrations/providers/` splits request building by provider, normalizes Responses versus Chat Completions output to `NormalizedReply`, and offers `execute_one`. `integrations/judge.py` separately builds a Terra image payload and locally validates the four-family JSON response. `scripts/provider_preflight.py` prints a **zero-network** registry preview. New `tests/test_provider_*_offline.py` files cover the registry, calls, requests, tool-response replay shapes, invalid outputs and double-opt-in. `pyproject.toml` adds `integrations` to the wheel, while the existing offline CI workflow adds provider tests and a preview step.

**Not implemented in the first PR:** the agent controller, plotting execution, sandbox input/output staging, automatic tool execution, production retry policy, a live Terra `validate(run)` integration, official Qwen equivalence, authored tasks, new human labels, or MCC results.

The old `workflow/generate.py` still uses Modal. It has not become a Docker-based runner. Session 007's `wrong_chart` v1/v2 decisions, errors, and saved outputs remain in their original paths.

## Pure requests and tool-result data

Responses requests are native `input` items and `function` tool descriptors. DeepSeek is **stateless**: the future controller must supply full history, including model `continuation_items` and matching `function_call_output` items. OpenAI Responses is configured without server-side storage for this adapter. Z.ai receives chat `messages`, legacy chat-format `tools`, assistant `tool_calls`, and `role=tool` replies.

The parser treats tool calls as **inert descriptions**; it does **not** run any model-proposed code or shell command. A future controller must validate approved tool names, parameters and resource budgets, execute only inside the Assignment 1 Docker sandbox with no credentials, and then attach the output using `make_tool_result`. Incomplete or refused model output, malformed tool-argument JSON, unsupported output items, duplicate tool-call IDs, or invalid judge-family lists fail explicitly.

Terra uses the schema `{"errors":[{"family":"wrong_chart","evidence":"..."}]}` (or `{"errors":[]}` for acceptable), preserving the four supported families and terminal-only `execution_failure` constraint. The model never sees human labels during inference. Figure payload assembly validates the PNG before encoding it.

## Live request safety contract

* The default `provider_preflight.py` makes **zero** network requests, loads no credentials and creates no SDK client.
* The one-call transport entry point `execute_one` requires **both** `live=True` and `confirm_one_request=True`, a provider-specific key from the environment / ignored `.env`, and an explicit caller. There is **no CLI live action in Session 008**.
* The code constructs an SDK client only after permission and key checks, with `max_retries=0`, a 60-second timeout, and a per-call completion cap of 512 tokens. This conservative cap is appropriate for compatibility probes, not a full plotting agent. The future runner will need separately defined budgets.
* No API requests are authorized by these code changes. Do not run live probes until each model-specific probe is separately approved, and distinguish provider errors from model errors.
* API keys belong to the host/secret store and must never enter a plotting sandbox, a Git commit, task input, judge prompt, or diagnostic output.
* All fixture labels remain separate: create judge predictions first, then run the existing `workflow.evaluate` comparison and report confusion matrices and MCC only on sufficiently representative, independently labeled cases.

## How to verify in Codespaces

From `feature/session-008-provider-adapters`, with a clean working tree:

```bash
git pull --ff-only
uv sync --locked
uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v
uv run python scripts/provider_preflight.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python scripts/offline_preflight.py
git status --short --branch
```

Expect all provider tests to pass and the preview to print four model roles, `network_requests: 0`, and one structured judgment role. **No test count or pass claim is recorded until verified in Codespaces/CI.**

After offline verification, the next milestone is three separately authorized live generation-provider probes plus one separately authorized Terra image/schema probe, followed later by integrating a bounded local Docker mini-SWE-agent loop. Each request and model substitution must retain its provenance.

## PR acceptance checklist

- [ ] The four provider/model roles match the user's selections
- [ ] `uv sync --locked` installs `integrations`
- [ ] All provider tests pass with mock clients and zero network
- [ ] The default preview remains offline and prints no prompts/keys
- [ ] Existing 55 validator tests, 5 structural tests and 110-run preflight remain valid
- [ ] No `validator/solution.py`, `workflow/generate.py`, released labels, or Session 007 experiments changed
- [ ] CI checks pass on PR, and the user reviews the diff before merging
