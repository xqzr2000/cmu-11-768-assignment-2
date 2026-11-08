# Assignment 2 — Learning Progress

> **Living study guide and chronological engineering journal.** Keep this file when a session ends; append a new session entry when we return. This is not the course's final report.
>
> **Project:** [xqzr2000/cmu-11-768-assignment-2](https://github.com/xqzr2000/cmu-11-768-assignment-2)  
> **Started:** 2026-11-05  
> **Source reviewed:** `main` at commit `4c28fd2bc0ee2499b7c632efbabbbb2c066c0ae8` (before this documentation-only change)  
> **Documentation branch:** `feature/learning-progress-journal`  
> **Learning mode:** beginner-friendly; explain purpose, inputs, outputs, commands, observations, failures, and follow-ups.  
> **Source of truth:** [ASSIGNMENT.md](../ASSIGNMENT.md) for official requirements; [README.md](../README.md) and [docs/ARCHITECTURE.md](ARCHITECTURE.md) for our independent adaptation.

## How to use this journal

1. Start with **What we are building**, then **How information flows**.
2. Use **Repo map** and **File-by-file guide** to find code before editing it.
3. Work through **Milestones and verification** in order. A checked item must have supporting evidence or a linked commit/test result.
4. At the end of each future working session, **append** an entry to **Session history** using the template below. Preserve failed experiments and the reasons for decisions; do not silently replace historical conclusions.
5. Keep observations separate from hypotheses, and distinguish **not run**, **passed**, **failed**, **blocked**, and **not applicable**. Do not confuse a data-format test with an evaluated model score.
6. Update the top-level **Current state** and **Next session** sections as the project progresses, without deleting the chronological entries.

## What we are building

The official Assignment 2 is titled **Evaluating a Data-Visualization Agent**. Our main deliverable is a **validator (an AI evaluator)**, rather than a chart-producing agent. It examines a visualization agent's task, input files, chronological actions, and final chart, then decides which mistakes occurred, with evidence.

**Mental model:** A human asks an agent to create a graph. The agent writes code, runs commands, and produces `figure.png`. We act as an independent reviewer: did a figure exist? Were the numbers right? Was the requested graph drawn? Can a reader actually see it?

### Four error families

| Family | Beginner's explanation | Example |
| --- | --- | --- |
| `execution_failure` | The task never ended with a valid figure. | Agent crashes and no final image exists. |
| `wrong_data` | The chart is displaying incorrect data. | Bars use sums when the request required averages. |
| `wrong_chart` | The chart design violates the instructions. | Requested a stacked bar chart but got a line chart. |
| `hard_to_read` | The rendering makes the figure hard or impossible to read. | Labels overlap or contrast is too low. |

A run can have multiple nonterminal families. **Ground-truth `execution_failure` is terminal**: it appears alone, and that run is omitted from scoring denominators for the other three families. Merely predicting execution failure does *not* exempt a validator from mistakes it also predicts in the other categories. Every reported error needs concrete evidence; an empty error list `[`] means the run is acceptable.

### How success is measured

For each family, compare the validator's *predicted yes/no* against human-labeled *actual yes/no*: true positive (TP), true negative (TN), false positive (FP), and false negative (FN). Then compute **Matthews correlation coefficient (MCC)**:

~~~text
MCC = (TP × TN − FP × FN)
      / sqrt((TP + FP)(TP + FN)(TN + FP)(TN + FN))
~~~

Range: **−1 to 1**, where 1 is perfect, 0 is no measured correlation, and negative values indicate inverse correlation. **macro-MCC** is the unweighted average of the four family MCCs. For degenerate cases the official scorer assigns 0 and may flag insufficient label support. On small self-authored datasets, always report each family's positive and negative support, not only its aggregate metric. Source: [ASSIGNMENT.md](../ASSIGNMENT.md#evaluation-format).

**Critical separation:** The seed human labels are a *measurement reference*, never inputs to the submitted validator; do not match or hard-code public run IDs. The final validator gets one run at a time with no label, reference figure, or other candidate runs.

## Official assignment milestones and outputs

| Part | What we learn/do | Required evidence |
| --- | --- | --- |
| **1. Understand seed runs** | Run the supplied VLM baseline, compare to the human labels, identify two recurring validator-error types (at least two trajectories for each). | All four family MCCs and macro-MCC; run IDs, evidence and proposed fixes. |
| **2. Improve validator** | Implement both changes in `validator/solution.py`, evaluate on public seed runs. | Updated MCCs, baseline comparison, at least one false positive and false negative with explanations. |
| **3. Create adversarial tasks** | Identify two weakness classes; author **at least five tasks**, at least two per class; run each against the **three fixed agents** for **at least 15 runs**, then human-label every result and score the validator. | Task JSONs, figures/trajectories, labels, per-family and macro-MCC, analysis of agent vs validator failures. |
| **3. Package in Harbor** | Wrap each authored task as a deterministic evaluation environment. Test the example, then make **every** packaged task's reference solution score **1.0**; author **two plausible mutants** total, one rejected with **0.0** and one incorrectly accepted with **1.0**. | Harbor task layouts, oracle reward logs, mutant descriptions, exact rewards and verifier limitations. |
| **4. Iterate** | Make at least one further validator improvement; evaluate the final solution on seed and authored runs. | Final MCCs on both sets and qualitative FP/FN analysis. |

**Official submission checklist:** `validator/solution.py`, prediction JSONs in `output/`, authored `tasks/`, generated `runs/`, `labels.json`, packaged `harbor/tasks/`, `report.tex`, `report.pdf`, and `AI_USAGE.md`. The original grading breakdown in the handout is report/design 40%, private validator macro-MCC 30%, comprehension quiz 20%, and code quality/reproducibility 10%. These are *course requirements*, not proof that our independent reproduction meets course grading conditions.

### Fixed official model policy versus our learning adaptation

The original course setup fixes the validator to **Qwen/Qwen3-VL-30B-A3B-Instruct-FP8** and the chart-generating agents to **Qwen/Qwen2.5-Coder-3B-Instruct**, **mistralai/Ministral-3-14B-Instruct-2512**, and **zai-org/GLM-4.7-Flash**, with student-owned Modal deployments. Our repository explicitly takes a separate **non-credit, no-Modal** route: keep the upstream starter, reuse the Assignment 1 Docker sandbox pinned at `0cb0534c2fffb67ddfff619100057fad0be90a3c`, and experiment with hosted DeepSeek `deepseek-flash`, OpenAI `gpt-5.6-luna`, and Z.ai `glm-5.3-flash` as potential chart generators (the earlier Z.ai `glm-4.7-flash` attempt remains historical). A hosted endpoint is **not automatically equivalent** to the official checkpoint/runtime. The multimodal validator endpoint is still **to be verified**. We must record every substitution and never present independently measured scores as official private-set scores. See [docs/UPSTREAM.md](UPSTREAM.md) and [docs/ARCHITECTURE.md](ARCHITECTURE.md).

## Current state — 2026-11-07

- **Session 010 in progress:** On `feature/session-010-chart-agent-controller`, **77/77 offline tests passed in Codespaces** (controller 11, fake-Docker gateway 14, task artifacts 16, chart transfer 12, image recipe 11, private build context 13). Existing provider 37/37 and validator 49/49 tests passed previously. User verified **real OCI registry index and linux/amd64 image manifest metadata** for `python:3.12-slim`; a 14-package chart-only wheel hash file and offline audit are committed but **audit execution remains pending**. No real Docker image pull/build/launch, model request or container chart extraction occurred.
- **Latest verified milestone — Session 009:** All four current hosted models passed a separately approved **one-turn live API transport/schema probe**: DeepSeek `deepseek-flash`, OpenAI `gpt-5.6-luna`, paid Z.ai `glm-5.3-flash` (inert function calls parsed), and experimental visual judge OpenAI `gpt-6.1-terra` (synthetic PNG and strict JSON parsed). The free Z.ai `glm-4.7-flash` attempt failed with `RateLimitError` and zero retries; its output is preserved. **37/37 provider and 49/49 validator offline tests** passed in Codespaces, and no agent controller, Docker plotting run, Terra accuracy/MCC benchmark or official Qwen equivalence is claimed. Session 009 feature branch is ready for a draft PR and CI review; **not yet merged**. All five one-request live authorizations are consumed.
- **Git (superseding the older point-in-time snapshot below):** PR #8 merged Session 008 at `5833b2b`; Session 007 was archived to tag `archive/session-007-20261107` at `939b01f`. Both old feature branches were deleted. Session 009 is on `feature/session-009-provider-compatibility`, with documentation updates after the verified Codespace tests; original course runner and validator remain unchanged.
- **Existing code:** imported full pinned official starter; offline preflight, its unit tests, GitHub Actions CI, development-container setup, and supporting Phase 0 docs.
- **Seed inventory:** 110 released `result.json` trajectories; 98 final `figure.png` files; 19 committed CSV input files; `seed_labels.json` contains 110 human labels. Some runs legitimately have no figure.
- **Reported Phase 0 label counts (not validator predictions):** 12 `execution_failure`, 25 `wrong_data`, 71 `wrong_chart`, 39 `hard_to_read`, and 16 fully acceptable runs; refer to [PHASE-0.md](PHASE-0.md) and rerun the preflight before relying on a local environment.
- **Session 002 offline preflight:** Verified in Codespace on 2026-11-05: 111 resolved packages, 110 seed runs / 98 figures / 110 labels, and 5/5 unit tests passed. Visual/trajectory case studies for runs 004 and 008 recorded below; no model judging performed.
- **Validator status:** Session 002 structural checks and Session 003 baseline semantic wiring remain mock-tested; 49/49 validator tests and 5/5 structural tests passed in Codespaces on 2026-11-07. The independent one-request Z.ai synthetic image probe passed in Session 004, but the later real-seed Z.ai attempt failed. OpenAI structured-output judgments on seeds 004 and 008 work independently of the official validator path. No full baseline sweep, official Qwen-equivalent score, or per-family/macro-MCC has been verified.
- **Agent generation:** `workflow/generate.py` still calls Modal; it has **not** been migrated to the Assignment 1 Docker runtime. Do not run it expecting local Docker behavior.
- **Harbor:** example and template exist; our own packaged tasks do not yet exist. Docker execution and reward tests were **not performed in this session**.
- **Documentation:** this journal is the session 001 deliverable. GitHub source inspection and branch creation are verified; **no code execution, model calls, score computation, or CI result is claimed by this journal-writing session**.
- **Git (current):** PRs #1–#7 have been merged into `main`, most recently [PR #7](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/7) at `91bd01c`. The user uploaded `docs/Progress-Explained-20261107.md` identically to both `main` (`252140e`) and the independent Session 007 feature branch (`939b01f`), then synchronized both local branches. Session 007 remains **unmerged** with an experimental wrong-chart v2 prompt that corrected seed 008 FP→TN but regressed seed 004 TP→FN. The current Session 008 feature branch `feature/session-008-provider-adapters` was created from `main` at `252140e`, and new offline-only provider-adapter code is committed there; **its tests are awaiting user Codespace verification**. No official Qwen evaluation, generalizable MCC, new plotting-agent runs or live Session 008 provider calls are claimed.

## How information flows through the code

~~~text
PUBLIC SEED EVALUATION                        NEW ADVERSARIAL EVALUATION
artifacts/<run_id>/result.json                tasks/<task_id>/task.json
artifacts/<run_id>/figure.png                        + inputs/
          |                                                 |
          |                                    workflow/generate.py
          |                                    (upstream: Modal)
          |                                                 |
          |                                        runs/<task>__<agent>/
          |                                                 |
          +-----------------------+-------------------------+
                                  |
                     validator/runner.py
                      loads a Run object
                                  |
                     validator/solution.py
                     validate(run) -> [Error]
                                  |
                     output/*_predictions.json
                                  |
        seed_labels.json OR our human-reviewed labels.json
                                  |
                       workflow/evaluate.py
                      4 MCCs and macro-MCC

For authored tasks:
tasks/ -> workflow/package.py -> harbor/tasks/<task_id>/
  -> oracle & mutants -> deterministic tests -> 0/1 reward
~~~

Key distinctions:

- **Run:** one actual attempt by an agent (prompt, messages, inputs, optional figure). `run_id` is the unique identifier; multiple runs may share a `task_id`.
- **Prediction:** what our validator *thinks* went wrong. Generated from the run without seeing human labels.
- **Label:** what a human reviewer *judges* went wrong; used only to score predictions.
- **Harbor verifier:** deterministic assertions, separate from the vision-model validator. It can check things like numeric sidecar values but can miss unreadable figures.

## Repo map — readable overview

This is an architectural map, not a replacement for the **complete, exact tracked-file tree** in the appendix.

~~~text
cmu-11-768-assignment-2/
├── .devcontainer/                 # Codespaces definition and setup
├── .github/workflows/             # offline CI on pushes/PRs
├── ASSIGNMENT.md                  # authoritative official task specification
├── README.md                      # our independent plan and quick start
├── docs/                          # architecture, upstream pins, phases, this journal
├── validator/                     # Run -> error predictions
├── workflow/                      # tasks, generation, labels, scoring, packaging
├── scripts/                       # offline check and original deployment entrypoints
├── infrastructure/                # preserved upstream Modal server/controller
├── harbor/                        # deterministic verifier guide, template, example
├── artifacts/<run_id>/            # 110 public seed trajectories; 98 PNGs
├── inputs/<run_id>/*.csv          # input data referenced by released runs
├── seed_labels.json               # public human labels for seed runs
├── labels.example.json            # example labels for authored runs
├── tasks/.gitkeep                 # future task descriptors
├── runs/.gitkeep                  # future generated runs (ignored locally)
├── output/.gitkeep                # future prediction files (ignored locally)
├── report_template.tex            # final LaTeX report scaffold
├── pyproject.toml + uv.lock       # Python requirements and pinned resolution
└── tests/                         # unit tests for offline preflight
~~~

## File-by-file guide

Read these entries as: **what is the file for?** → **what would make us edit/run it?** Where two or more files are nearly identical repeated fixtures, the shared format is explained once, and the exact set of paths is listed in the appendix.

### A. Root configuration, documentation, and data

| File | Purpose / when we use it |
| --- | --- |
| `ASSIGNMENT.md` | Full official handout. Check requirements, definitions, commands, scoring and submission before implementation. Kept unchanged as a reference. |
| `README.md` | Project identity, non-Modal plan, progress phases, reproducible starter commands and cautions; update as actual capabilities change. |
| `docs/ARCHITECTURE.md` | Proposed offline / online data flow, security boundary, independent validator, research safeguards and known missing integration work. |
| `docs/PHASE-0.md` | Already-completed Phase 0 checks, dataset facts, evidence and remaining checklist. Its old PR checkbox may need reconciliation against current GitHub history. |
| `docs/UPSTREAM.md` | Exact upstream starter revision `f609e76d2efd302b4b8babee06c5592899010b8b` and Assignment 1 sandbox revision. Essential for reproducing dependency history. |
| `docs/Learning-Progress.md` | This living tutorial, current state, decisions, test observations and append-only session log. |
| `pyproject.toml` | Defines Python >=3.12, dependencies and Python package build; **pins Assignment 1 sandbox as a Git dependency**, not copied source. |
| `uv.lock` | Full resolved dependency lock, so `uv sync --locked` can reproduce the same package set. Don't edit by hand. |
| `.python-version` | Requests Python 3.12 for tools such as `uv`. |
| `.gitignore` | Prevents committing real local secrets/environments, Harbor jobs, authored run outputs, and generated predictions; preserves placeholders. |
| `.gitattributes` | Normalizes shell-script and CSV line endings to LF so Linux execution and input hashes stay stable. |
| `.env.example` | Original course's **Modal** validator and three generation-model endpoint environment variable examples. Documentation, **not active secrets**. |
| `.env.local.example` | Our optional Z.ai endpoint/model settings for future local work; `ZAI_API_KEY` should come from Codespaces Secrets. |
| `.devcontainer/devcontainer.json` | Defines Python 3.12 Codespace image, Docker-in-Docker, VS Code extensions and post-create script. |
| `.devcontainer/post-create.sh` | Installs `uv` if needed, syncs locked dependencies, and runs the offline dataset preflight. |
| `.github/workflows/offline-ci.yml` | CI job for offline structural tests and dependency sync; triggered on pull requests plus configured push branches. CI is not a model accuracy test. |
| `seed_labels.json` | Human-reviewed answer key for the released seed runs. Never import it into a production validator. |
| `labels.example.json` | Demonstrates the shape of independent labels we will later write for authored runs. |
| `report_template.tex` | Course LaTeX report starter; later make `report.tex` and compile `report.pdf`. This journal is not the submission report. |
| `output/.gitkeep` | Keeps the currently empty prediction-output directory in Git; generated `output/*.json` files are ignored. |
| `runs/.gitkeep` | Keeps the currently empty future agent-run directory in Git; generated run directories are ignored. |
| `tasks/.gitkeep` | Keeps the currently empty future task-authoring directory in Git. |
| `inputs/<run_id>/*.csv` | Original data used by selected released seed cases; different runs have different field names and required calculations. The full list of 19 CSV paths appears in the tree appendix. |
| `artifacts/<run_id>/result.json` | One public seed run's task, agent trajectory and outcome. There are 110 of these. Use for close evidence inspection, never for run-ID-specific rules. |
| `artifacts/<run_id>/figure.png` | Agent-produced chart if it exists (there are 98); compare with the instruction and data, or inspect readability. No PNG can be valid evidence of execution success when absent. |

### B. Validator — our main implementation target

| File | Purpose |
| --- | --- |
| `validator/__init__.py` | Makes `validator` an importable Python package; currently empty. |
| `validator/model.py` | Creates OpenAI-compatible client from `VALIDATOR_BASE_URL`, `VALIDATOR_API_KEY`, optional `VALIDATOR_MODEL`; also supports tokenizer endpoints used by baseline compaction. |
| `validator/prediction.py` | Pydantic schema for `ErrorFamily`, `Error`, `Prediction` and `PredictionFile`. This is the contract: only allowed families and nonempty evidence. |
| `validator/runner.py` | Loads a `Run` from artifacts: run ID, task ID, instructions, messages, optional figure and named input paths. Imports chosen validator module, checks outputs, retries eligible failures and writes prediction JSON. |
| `validator/baseline.py` | Supplied working reference validator. It asks the VLM about execution, chart/data and readability; can trim trajectory/inputs and downscale oversized images on context overflow. Read and measure it *before* improving it. |
| `validator/solution.py` | **The file we implement.** Currently four stub functions—`judge_execution`, `judge_data_and_chart`, `judge_readability`, `validate`—all raise `NotImplementedError`. Must return a list of evidence-backed `Error` objects. |

**Beginner's call chain:** run `uv run python -m validator.runner --artifacts artifacts --out output/my_predictions.json`. The runner calls `validator.solution.validate(run)` unless `--solution validator.baseline` is specified. The validator creates one or more error reports (or `[`]), and the runner serializes them to JSON. The scorer later evaluates this JSON against labels. This command needs a working validator and may need a vision model; it is **not an offline preflight**.

### C. Workflow — preparing and measuring experiments

| File | Purpose |
| --- | --- |
| `workflow/__init__.py` | Importable package marker and short package description. |
| `workflow/__main__.py` | Command dispatcher for `python -m workflow`: `validate-tasks`, `generate`, `package`, `init-labels`, `validate-labels`, `score` and `check-submission`. |
| `workflow/tasks.py` | Pydantic validation of task JSON: legal task IDs, safe relative input paths, named inputs, valid structure and file existence. |
| `workflow/generate.py` | Original generation orchestrator using the upstream Modal `hw2-agent-runner`, fixed three model choices, task execution and result/figure writing; **not yet a Docker-backed local runner**. |
| `workflow/evaluate.py` | Initializes human-label JSON, verifies label coverage/schema, calculates per-family MCC and macro-MCC with the official terminal-execution convention. |
| `workflow/package.py` | Copies and partly fills Harbor template from authored `task.json` descriptors; cannot supply task-specific verifier logic for us. |
| `workflow/harbor_rewards.py` | Actually runs Harbor oracle/mutant trials via subprocess, reads rewards and verifies the required expected outcomes. Needs Docker. |
| `workflow/submission.py` | End-to-end structural/coverage check plus optional Harbor reward verification; does not assess human-label correctness or narrative report quality. |

**Separation:** `workflow/tasks.py` validates what a task *asks*, `workflow/generate.py` obtains an agent *attempt*, `validator/runner.py` obtains the evaluator *prediction*, and `workflow/evaluate.py` measures that prediction against *human truth*.

### D. Scripts and upstream infrastructure

| File | Purpose |
| --- | --- |
| `scripts/__init__.py` | Marks `scripts` as a Python package for test imports; empty. |
| `scripts/offline_preflight.py` | Validates seed inventory, run/label IDs, error families, PNG headers and dimensions, with **no model or network calls**. Does *not* judge correctness/readability. |
| `scripts/deploy_validator_model.sh` | Original Modal deployment entrypoint for the fixed vision validator. **Not our current route.** |
| `scripts/deploy_generation_models.sh` | Original Modal deployment entrypoint for all three fixed chart-generating models. |
| `scripts/deploy_agent_runner.sh` | Configures Modal generation secrets, gateway and mini-SWE-agent runner. |
| `infrastructure/README.md` | Deployment instructions and model aliases/GPUs, endpoint configuration, cold starts, and credential isolation in the original infrastructure. |
| `infrastructure/serving.py` | Shared helper to build model-serving container images, attach volumes, launch/warm/stop vLLM processes. |
| `infrastructure/validator_model.py` | Defines the fixed Qwen3-VL validator serving app on Modal. |
| `infrastructure/generation_models.py` | Defines the three generation-model Modal serving classes (Qwen, Ministral, GLM). |
| `infrastructure/configure_generation.py` | Reads generation endpoint settings and stores them as a Modal secret for the gateway. |
| `infrastructure/generation_gateway.py` | Credentialed call gateway from agent scaffold to model endpoints; isolates model API keys from the agent container. |
| `infrastructure/agent_runner.py` | Original mini-SWE-agent controller in a fresh Modal container; limits agent steps, command duration and total walltime. |
| `tests/test_offline_preflight.py` | Standard-library `unittest` cases on synthetic fixtures, exercising preflight behavior for valid and broken inputs. |

We preserve the deployment files as historical/upstream references. **Do not run `scripts/deploy_*.sh` as though they implement our non-Modal plan.** Future Docker adaptation should be a separate, testable change.

### E. Harbor — deterministic evaluation environments

| File | Purpose |
| --- | --- |
| `harbor/README.md` | Hands-on tutorial for packaging authored tasks, verifying reference solutions and measuring rejected/accepted mutants. |
| `harbor/TROUBLESHOOTING.md` | Diagnoses Harbor/Docker errors, missing tasks, task TOML formatting, interpreter paths, verifier reward files, CRLF and other practical traps. |
| `harbor/preflight.py` | Checks a task's TOML, expected files, scripts and unfinished sentinels **before** an expensive Docker run. |
| `harbor/reference/README.md` | Optional advanced deterministic verification idea: re-execute the plotting script, capture matplotlib artist metadata, and compare with expected values while defending against forged/stale output. |
| `harbor/template/task.toml` | Starter Harbor metadata, limits, artifact paths, runtime and verifier settings; edit per task. |
| `harbor/template/instruction.md` | Precise agent prompt template. Every verifier check must be justified by an instruction the agent actually receives. |
| `harbor/template/environment/Dockerfile` | Pinned, no-network execution image with plotting/test dependencies installed at build time. |
| `harbor/template/solution/solve.sh` | Intentionally failing placeholder for the task's **reference solution**; remove sentinel only after implementing it. |
| `harbor/template/tests/test.sh` | Verifier entrypoint: invoke pytest and write the reward file on either success or failure. |
| `harbor/template/tests/test_state.py` | Starter checks for files/PNG/sidecar; has a fail-closed sentinel until replaced with real correctness assertions. |
| `harbor/example/README.md` | Detailed synthetic orchard-ledger worked example, expected rewards and commands. |
| `harbor/example/task.toml` | Complete task definition and runnable container/verifier metadata for the example. |
| `harbor/example/instruction.md` | Example's agent-facing request: compute and plot orchard yields. |
| `harbor/example/environment/Dockerfile` | Pinned environment with the example CSV copied inside. |
| `harbor/example/environment/harvest_log.csv` | Small invented orchard delivery dataset, whose contents must remain intact. |
| `harbor/example/solution/solve.sh` | Known-good reference solver for the example, expected to obtain reward 1.0. |
| `harbor/example/tests/test.sh` | Runs example tests and writes deterministic success/failure reward. |
| `harbor/example/tests/test_state.py` | Real assertions for structure, totals, script/figure agreement, sensitivity to input changes and sidecar consistency. |
| `harbor/example/tests/sitecustomize.py` | Python-startup hook used during verification to instrument matplotlib `savefig` without editing the agent's script. |
| `harbor/example/tests/figure_manifest.py` | Converts matplotlib's artist tree into structured JSON of axes, plotted values, legends, annotations and styling for exact checks. |
| `harbor/example/mutants/sum_crates/solve.sh` | Plausible numerical mistake: sums crates, not calculated yield; should score 0.0. |
| `harbor/example/mutants/forgery/solve.sh` | Leaves correct code but submits a PNG inconsistent with that code; should score 0.0. |
| `harbor/example/mutants/hardcoded/solve.sh` | Hard-codes correct outputs without reading CSV; input-perturbation tests should catch it (0.0). |
| `harbor/example/mutants/illegible/solve.sh` | Computes values correctly but renders unreadably tiny text; deterministic example verifier accepts it (1.0). This teaches why visual judgment matters. |

**Harbor vocabulary:** An **oracle** runs a correct reference solution, a **nop** agent does nothing, a **mutant** deliberately violates the task, and the **verifier** writes a 0/1 reward. The test is only as good as the failure conditions its assertions can detect.

### F. Repeated public fixtures (all actual paths in appendix)

- `artifacts/` has **110 run-ID directories**. Every directory has a `result.json`; **98** also have `figure.png`. Lack of a PNG may be an actual execution failure, not a missing checkout.
- `inputs/` has **19 CSV files** under run-specific directories. Read the corresponding trajectory's requested inputs before asserting what values should be plotted.
- `seed_labels.json` is a separate, centralized set of public human judgments rather than labels next to each run.
- Source/control directories contain the **73 other tracked files** that comprise the code, config, docs, Harbor templates and examples. This new journal makes one more tracked file.

## Start-here commands (Codespace, from repo root)

### Safe offline checks

~~~bash
git status --short --branch
uv sync --locked
uv run python scripts/offline_preflight.py
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python -m workflow --help
~~~

**What this proves:** dependencies resolve; the released run/label dataset is internally consistent; and preflight tests behave as expected. **What it does not prove:** the validator can classify figures, a VLM endpoint works, agents can generate charts, or Harbor runs succeed. Treat actual outputs as evidence when logging this later.

### Read a few examples manually

~~~bash
# Review the task, messages and outcome; then inspect its figure if present.
python -m json.tool artifacts/004/result.json | less
python -m json.tool artifacts/008/result.json | less
# Check seed human labels without using them inside the validator.
python -m json.tool seed_labels.json | less
~~~

### Later commands — only after prerequisites are met

~~~bash
# Requires verified image-capable validator endpoint and credentials:
uv run python -m validator.runner --solution validator.baseline \
  --artifacts artifacts --out output/baseline_predictions.json
uv run python -m workflow score --labels seed_labels.json \
  --predictions output/baseline_predictions.json

# Requires completed validator/solution.py and valid endpoint:
uv run python -m validator.runner --artifacts artifacts \
  --out output/pre_iteration_seed_predictions.json

# Safe local descriptor verification; task writing comes first:
uv run python -m workflow validate-tasks

# Upstream workflow/generate.py still requires Modal; DO NOT treat as local.
# Our independent Docker generator must be implemented and validated first.
~~~

### Keeping Git history clean

~~~bash
git fetch origin
git switch feature/learning-progress-journal
git status --short
# After review/merge in a future step, work from a fresh main and new branch:
git switch main
git pull --ff-only
git switch -c feature/<next-focused-change>
~~~

Never commit secrets, generated jobs, copied environment files or transient artifacts. Check `git diff --check` and review staged changes before every commit. Keep implementation and documentation PRs reviewable.

## Common mistakes to avoid

1. **Data leak:** using `seed_labels.json` or public `run_id` lookups to choose predictions; this invalidates generalization.
2. **Terminal-category confusion:** scoring readability/data/chart on a run with no valid figure as though it had a usable visual artifact.
3. **False confidence from preflight:** PNG header/dimension validation is not data or chart correctness.
4. **Incorrect metric:** reporting accuracy or a single blended count instead of four separate MCCs and macro-MCC, including label support.
5. **Provider mismatch:** calling a text-only or different hosted model a reproduction of the official fixed Qwen3-VL evaluator.
6. **Transport vs. task failure:** confusing HTTP 429 / provider errors with a visualization agent's `execution_failure`.
7. **Mutable task spec:** rewriting an adversarial task prompt after generating its runs and labels; preserve prompt provenance.
8. **Harbor false success:** tests that merely check a PNG exists can reward a factually wrong chart; require semantic/numeric assertions.
9. **Automation overclaim:** existence of `workflow/generate.py` does not establish a working Docker agent; its code still uses Modal.
10. **Unreproducible experiments:** omitting model IDs, parameters, dependency revisions, task IDs, reward logs, commands or exact run paths.

## Milestones and verification board

| Milestone | State at journal start | Exit criterion |
| --- | --- | --- |
| Phase 0 starter import and pinned dependency | **Documented as complete** in PHASE-0.md | Rerun offline commands in our Codespace and record output here. |
| Familiarity with tree and official requirements | **Documented in this journal** | Can explain `Run`, `Error`, labels, MCC and Harbor without opening files. |
| Baseline vision validator | **Not yet verified** | Valid multimodal endpoint, predictions saved, four MCCs recorded, representative errors analyzed. |
| First improvements in `solution.py` | **Not started** | Two changes, score comparison and FP/FN case study. |
| Independent Docker agent runner | **Not started** | Bounded multi-step run with retained trajectory, inputs, final PNG and no leaked model credentials. |
| Five adversarial tasks / three agents | **Not started** | >=5 task descriptors, >=15 runs, human labels and measured scores. |
| Harbor packages and mutants | **Not started** | Every oracle 1.0, rejected mutant 0.0, accepted mutant 1.0 with evidence. |
| Final iteration and reproducible report | **Not started** | Final predictions, private-set limitations, `report.tex/pdf`, `AI_USAGE.md`, submission checks. |

## Session history — append, do not overwrite

### Session 001 — 2026-11-05 — Establish the learning journal

**Goal:** Understand the official Assignment 2, inspect *this actual repository* and its tracked files, document how the parts connect, and create one persistent tutorial/journal on a feature branch.

**Prior decisions carried forward:** full pinned upstream starter; Assignment 1 sandbox pinned Git dependency; feature-branch/PR workflow; offline-first validator exploration with no unverified vision-model claims.

**Actions and confirmed observations:**

- Inspected GitHub repository metadata, full recursive `main` tree, source and configuration files, official `ASSIGNMENT.md`, sample Harbor tasks, and current branch list.
- `main` was the only branch at inspection, and no pull requests were open. Created `feature/learning-progress-journal` from `main`.
- Inventory from recursive Git tree: **300 tracked files before the journal**, 110 public seed run result files, 98 figures, 19 input CSV files.
- Verified `validator/solution.py` still raises `NotImplementedError` in each function and `workflow/generate.py` still uses Modal.
- Wrote the architectural explanation, path-by-path guide, commands, official/independent distinction and reusable log format. New journal adds one tracked file after commit.
- This session made **no behavioral changes** to agent, validator, scores, official artifacts, or course source. It did **not** execute Python, launch Docker, call any LLM or deploy Modal.
- **Git result:** a documentation-only commit/PR should reference this session. Enter the final PR URL and review outcome here after GitHub confirms them.

**Tests/commands:** GitHub repository inspection and new branch creation: **successful**. `uv sync --locked`, preflight, unit tests, baseline scoring, Harbor oracle/nop, model calls: **not run this session**.

**Problems / limitations:** No pre-existing feature branch to reuse. We created a dedicated documentation branch. A GitHub source read does not test runtime behavior. Published Phase 0 status is not a fresh model-performance measurement.

**Lessons:**

1. Assignment 2 is an evaluator-research task, not merely chart generation.
2. Prediction, human truth and deterministic verifier reward are three different concepts.
3. Strong evidence requires the requested specification, trajectory, input data and actual rendered figure.
4. Offline dataset validation is a valuable first checkpoint but cannot substitute for a real image-capable judge.
5. Preserving official source and recording deliberate deviations makes an independent reproduction interpretable.

**Next session:** Run and log offline commands in the Assignment 2 Codespace; open several real public trajectories and compare their figures with instructions and human labels. Then design a reproducible **baseline vision-endpoint validation plan** without pretending text-only GLM tests prove image-evaluation ability.

### Session 002 — 2026-11-05 (America/Vancouver) — Offline preflight and real trajectory evidence

**Goal:** Validate the Codespace environment, inspect representative seed runs and figures, and learn to connect visible errors with agent tool calls before building an evaluator.

**Starting point:** The previous learning-journal PR [#2](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/2) was merged into `main` on 2026-11-05. The user created a clean local branch `feature/session-002-offline-preflight` after `git pull --ff-only origin main`. The GitHub documentation update is committed on a same-named remote branch; synchronize with `git fetch origin && git pull --ff-only origin feature/session-002-offline-preflight` before making more local edits.

**Verified Codespace commands and observations:**

| Command | Observed result | What this establishes |
| --- | --- | --- |
| `git switch main && git pull --ff-only origin main` | Already up to date | Merged journal is present on `main`. |
| `git switch -c feature/session-002-offline-preflight` | New local feature branch | Work is isolated from `main`. |
| `git status --short --branch` | `## feature/session-002-offline-preflight` | Clean status at start of session. |
| `ls -l docs/Learning-Progress.md` | File exists | Journal is available locally. |
| `uv sync --locked` | Resolved **111 packages**; rebuilt/reinstalled local `hw2-validator==0.1.0` | Dependency lock is usable in Codespaces. |
| `uv run python scripts/offline_preflight.py` | **PASSED**; **110** runs, **98** figures, **110** labels, **16** acceptable | Structural integrity of released dataset; **not** validator accuracy. |
| `uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v` | **5 tests passed**, 0.009s | Offline fixture/schema checks behave as expected. |
| `uv run python -m workflow --help` | All seven workflow commands shown | CLI dispatcher is importable. |
| Read-only Python script extracting matching agent tool-call lines from `artifacts/004/result.json` and `artifacts/008/result.json` | Matching source code printed as below | Confirms exact trajectory evidence, independent of a model call. |
| `Run.load()` for `001`, `004`, `008` (user-run Python heredoc) | 001: `figure=None`, 0 input files, 10 messages, instructions length 785; 004: figure path present, 0 inputs, 10 messages, length 1034; 008: figure path present, 1 input (`data.csv`), 23 messages, length 714 | Real dataset can be loaded as `Run` instances without a model; absence of a figure is distinct from parser failure. |

**Human seed label inventory** (these are not validator predictions): `execution_failure=12`, `wrong_chart=71`, `wrong_data=25`, `hard_to_read=39`. Categories overlap, except that terminal `execution_failure` stands alone. No MCC or macro-MCC was calculated.

**Codespace synchronization:** `git fetch origin`, `git branch --set-upstream-to=origin/feature/session-002-offline-preflight`, and `git pull --ff-only` fast-forwarded from `43fb242` to `586849b`; `git status --short --branch` showed the local branch tracking the remote and no uncommitted changes. The user then executed the `Run.load()` inspection above. No model or cloud call occurred.

**Case study — run `004`: mathematical function subplots.** The user inspected `artifacts/004/figure.png` and extracted the script text from the recorded `bash` tool call.

- The code sets `y4 = 15 ** x4`. Human reviewers label `wrong_data` because panel 4 omits a required cubing step. We have evidence for **what code executed** and for the reviewer judgment; do not infer a more specific intended formula without reconciling the assignment wording.
- The code sets `axs[1, 1].set_yscale('log')` but does not set the bottom-right subplot's x-axis to logarithmic. The image shows evenly spaced x ticks. This is a human-labeled `wrong_chart` error, not an execution failure.
- Other subplots contain `set_xscale('log')` where applicable, demonstrating why a broad search for "log" is insufficient: the validator must associate each instruction with the correct subplot.

**Case study — run `008`: Sankey diagram.** The user inspected `artifacts/008/figure.png` and the actual tool-call code.

- `pd.read_csv(...).query("source != 'orange'")` discards requested orange **source** rows, leaving no orange source node; human `wrong_data`.
- Both source and target `ax.text(..., color="#f4f4f4")` labels use near-white text on white; human `hard_to_read`. The image visually corroborates low contrast.
- An orange **target** node or a legend entry is not a substitute for a missing orange **source** node.

**Control example — run `001`:** Its human seed label is `execution_failure` and the released tree has no `artifacts/001/figure.png`. This was identified from source records, but the user has **not** yet reported running `Run.load()` interactively for this case.

**Concepts learned:**

1. A successful `figure.png` write proves that an image file exists, not that values, chart design or readability are correct.
2. The *task* defines expectations, the *trajectory* shows what the agent did, the *figure* reveals visual outcomes, and *human labels* let us measure evaluator predictions after the fact.
3. A defect in agent code is an **agent failure**; a missed or wrongly assigned category in our judge is a **validator failure**. We have studied agent failures, not measured validator failures.
4. `Run.load()` will turn raw JSON/PNG/input paths into a `Run` object; `validator.runner` invokes `validate(run)` and writes prediction JSON; `workflow score` compares those predictions with human labels.
5. Offline preflight and unit tests are meaningful reproducibility evidence, but do not establish any vision model's performance.

**Current blockers / limits:** No image-capable judge endpoint verified, no baseline predictions or MCC, no Docker-backed generation runner, no Harbor oracle/nop tests. The baseline has not been executed in this session. This session has so far been read-only for Python and fixture files.

**Step 6 — code walkthrough (user-verified):**

- The user ran `git pull --ff-only`, which fast-forwarded local `feature/session-002-offline-preflight` from `586849b` to `47cae2f`, retaining the documentation-only branch changes.
- The user printed numbered source lines of `validator/runner.py` (33–146) and `validator/baseline.py` (164–199). **This was source inspection only**, not a validator/model execution.
- `Run.load()` parses `result.json`, resolves task input file paths, rejects missing referenced inputs, and stores `figure=None` when `figure.png` is missing. `runs()` enumerates all `*/result.json` records in sorted order.
- `runner.main()` imports `validate` from the selected module (default `validator.solution`); calls `errors = validate(run)`; wraps successful results in `Prediction(run_id=..., errors=...)`; writes checkpointed `PredictionFile` JSON. The `--resume` option skips predictions already in the output file.
- Exception behavior: exceptions **inside** `validate(run)` are collected for retry. The initial attempt plus two retries imply delays of 30 and 60 seconds before remaining failures terminate; schema validation in `Prediction(...)` is *outside* that `try` block and does not receive this retry treatment. Avoid invoking the still-unimplemented `validator.solution` from the full runner.
- The baseline's `validate(run)` first asks about `execution_failure`. On a predicted failure it returns immediately, avoiding the other three checks. Otherwise it asks separately about `wrong_data`, `wrong_chart`, and `hard_to_read` and concatenates their errors. This is a model-based judgment, **not an infallible determination**.
- Normal nonterminal baseline processing calls the model once per category, for **four model requests per run**. What actually gets sent and how context overflow is handled will be examined next in `baseline._ask` and `validator/model.py`.

**Step 7 — source walkthrough of multimodal model requests (user-verified):**

- User fast-forwarded the feature branch to commit `f2a8bb7` and printed `validator/baseline.py` lines 99–163, `validator/model.py` lines 1–65, and `validator/prediction.py` lines 1–46.
- `baseline._ask(run, family, question)` reads each named input file's text, stringifies the complete trajectory, and reads PNG bytes if a figure exists; `make_prompt` adds task instructions and requests a **YES/NO with brief explanation**.
- `ask()` builds a multimodal chat request: `text` content plus, when available, a PNG encoded as a base64 `data:image/png` URL. It calls `validator.model.complete()` with `MAX_OUTPUT_TOKENS=250`. The endpoint must actually support image understanding.
- `validator/model.py` uses `VALIDATOR_BASE_URL`, `VALIDATOR_API_KEY`, and optional `VALIDATOR_MODEL` (default `validator`) to construct an OpenAI-compatible client. Client timeout is 300 seconds, SDK `max_retries=3`, and requests default to `temperature=0`. No live endpoint was contacted in this exercise.
- The baseline parses only the beginning of the response text: if it starts with `YES` (case-insensitive), it creates `Error(family=..., evidence=...)`; every other response becomes an empty list. `prediction.py` permits only the four `ErrorFamily` values and requires nonempty evidence. `PredictionFile` stores an array of `Prediction` records.
- On a context-length `BadRequestError`, the baseline tries shorter trajectory and input excerpts using compatible vLLM tokenizer endpoints, then progressively downscales the figure if needed. Non-context 400 errors are propagated. This **changes the evidence available to the judge**.
- Hypotheses to evaluate in future work (**not measured findings**): response-prefix parsing is brittle; asking separately for four families resends long evidence; truncation may lose decisive tool calls; reducing resolution can obscure readability defects; execution evidence could be handled partly with deterministic checks rather than only model judgment.
- Distinguish the `openai` client's internal request retries, the baseline's **context-overflow fallback**, and the outer runner's **per-run retries**—they are three separate mechanisms.

**Step 8 — offline mock of the baseline model (user-executed, passed):**

- Synchronized the branch via `git pull --ff-only`, fast-forwarding `f2a8bb7..bbc8b80`.
- Loaded run `008` using `Run.load(Path("artifacts/008"), Path.cwd())` and temporarily replaced `validator.baseline.complete` with a local `fake_complete()`. The original function was restored in a `finally` block.
- The mock returned four artificial messages in order: `NO` for execution failure, `YES` for wrong data, `NO` for wrong chart, and `YES` for readability.
- Observed exactly **four model-request payloads** with prompts asking the four expected questions. Every payload had content types `['text', 'image_url']`, confirming that the baseline included the run's PNG with each question.
- Observed **two parsed Pydantic `Error` objects**, with families `wrong_data` and `hard_to_read` and the exact mocked evidence strings. Printing `error.model_dump()` showed the Python `ErrorFamily` enum instance; `model_dump(mode="json")` would emit plain string values.
- **Result: PASS for local call-order, request-shape and answer-parsing control flow.** No real model request was made, no network API credits used, and no validator accuracy/macro-MCC can be inferred. The mock was run as a terminal heredoc, not committed as a reusable test.

**Design implication:** Separate deterministic artifact/execution checks from semantic chart judgments when designing `validator/solution.py`, but confirm what counts as a valid figure. A file's mere existence and PNG header are insufficient evidence of correctness. Build independent unit tests for the new logic before any live multimodal evaluation.

**What is not established yet:** No live-model execution test of `_ask()`, no verified vision endpoint, no actual validator predictions on the labeled dataset, no confusion matrix, and no MCC or macro-MCC result.

**Step 9 — first incremental implementation committed; execution checks pending in Codespaces:**

- Modified `validator/solution.py`: `judge_execution(run)` now gives a single evidence-backed terminal `execution_failure` when the final image is missing, points to a directory/non-file, isn't a PNG, or fails PNG structural verification/pixel decoding with Pillow. It does not inspect semantic plotted data and does not use any public labels or model calls.
- `validate(run)` short-circuits on that terminal execution failure, following the baseline's call sequence. If the PNG decodes, `judge_data_and_chart()` and `judge_readability()` still raise explicit `NotImplementedError`. This intentionally prevents false "acceptable" predictions.
- Added `tests/test_validator_solution_offline.py`: **seven synthetic cases**, covering None, nonexistent path, directory, garbage data, JPEG disguised as PNG, truncated PNG, and valid PNG (with mocked downstream judges proving execution continues).
- Updated `.github/workflows/offline-ci.yml` to execute these tests **after** `uv sync --locked`, leaving the original dependency-free preflight tests intact. Updated `README.md` to document the scope and command.
- Commit sequence: `3089b18` (implementation), `8641c16` (tests), `b77fbee` (CI), `2464c81` (README); this journal entry records the change as a separate documentation commit.
- **Verified after this initial implementation note:** seven tests passed in Codespaces, five original tests passed, dataset preflight passed, and the code commit's GitHub CI passed. **Not yet done:** image-model request, dataset accuracy metric, or full validator run.

**Step 10 — local verification passed (user-executed):**

- The user ran `git pull --ff-only`, fast-forwarding the local branch from `4ec99c0` to `5f79d76`. The changed files were `.github/workflows/offline-ci.yml`, `README.md`, `docs/Learning-Progress.md`, `tests/test_validator_solution_offline.py`, and `validator/solution.py`.
- New offline unit suite: `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v` yielded **7 tests, 7 passed, 0 failures/errors** (0.265 seconds). Cases covered directory, garbage bytes, misnamed JPEG, `None`, nonexistent path, truncated PNG, and structurally valid PNG with downstream semantic mocks.
- Original offline unit suite: `uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v` yielded **5 tests, 5 passed, 0 failures/errors** (0.006 seconds).
- Dataset structural preflight: **PASSED**, reporting 110 runs, 98 figures, 110 labeled runs, 16 acceptable runs; category counts `execution_failure=12`, `hard_to_read=39`, `wrong_chart=71`, `wrong_data=25`. No model or cloud infrastructure was called.
- Git status: `## feature/session-002-offline-preflight...origin/feature/session-002-offline-preflight`, with no modified/untracked file lines.
- GitHub Actions workflow `Offline dataset checks` for code commit `5f79d76` was also observed **completed/success** (workflow run 42162196977). A subsequent documentation-only commit may trigger another workflow run that needs its own status checked.
- **Interpretation:** Deterministic execution checks and synthetic offline tests are reproducibly passing; the semantic validator is still unimplemented. None of these successes measures MCC or chart-judge accuracy.

**Reproduce in Codespaces (after `git pull --ff-only`):**

~~~bash
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/offline_preflight.py
git diff --check
git status --short --branch
~~~

**What we'll learn next:** Interpret real unit-test output and any errors; distinguish "a well-formed PNG" from "a correct readable figure"; then establish the requirements for a genuinely image-capable semantic judge. **Do not run the full `validator.runner` with the partial solution yet**: valid PNG cases intentionally raise `NotImplementedError` and trigger retries.

**Next exercises:** (a) **Completed:** loading `001`, `004`, `008` with `Run.load()`. (b) **Completed:** runner import, call, retry and checkpoint source walkthrough. (c) **Completed:** baseline request construction, model adapter, response parser and context-overflow fallback source walkthrough. (d) **Completed:** offline mock of `baseline.complete()` verified four text+image calls and two parsed errors. (e) **Implemented, tests pending:** deterministic execution checks plus seven synthetic tests. (f) **Completed:** all local tests and dataset preflight passed; GitHub CI passed for code commit. (g) **Next:** review the draft PR for scope, merge if desired, and plan a separate milestone for a real image-capable semantic judge.

### Session 003 — 2026-11-05 (America/Vancouver) — Semantic validator design

**Starting point:** PR [#3](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/3) from Session 002 was merged into `main` at `c3b0189` (2026-11-06 UTC). The user pulled `main`, deleted the old local branch, and created a clean local `feature/session-003-semantic-validator` branch. A matching remote branch is created for this journal entry; synchronize the local branch before editing further.

**Goal:** Extend the structurally verified `validator/solution.py` so normal PNG-bearing runs can be judged for `wrong_data`, `wrong_chart`, and `hard_to_read` while retaining testability without paid API or cloud infrastructure.

**Design review and source constraints (not yet an executed implementation):**

- The official `ASSIGNMENT.md` fixes the evaluator model to `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8`, requires the existing `validate(run) -> list[Error]` contract, and scores per-family MCC and macro-MCC on human-labeled seed runs and private held-out trajectories. Do not quietly substitute another LLM or assume a text-only endpoint can inspect PNG images.
- `judge_execution(run)` already handles absent, corrupt, or misformatted PNG artifacts deterministically and returns the exclusive terminal family. It **does not establish semantic correctness** for a decodable image.
- The three remaining semantic error families require reasoning over `run.instructions`, `run.inputs`, `run.messages`, and `run.figure`. `validator/baseline.py` already implements separate VLM questions with text and image content, response parsing, and a vLLM-oriented context-overflow fallback.
- Proposed **minimal integration**: keep deterministic `judge_execution`, and delegate the other categories to the provided baseline semantic judges as the first functional implementation. Keep `validator/model.py` and the fixed category schema unchanged. This is an integration baseline, **not a claimed semantic accuracy improvement**.
- Test the integration by mocking model completion; assert that a valid PNG leads to three semantic model requests (one each for data, chart and readability), expected `Error` objects and JSON-safe schema, while missing/invalid PNGs lead to an immediate terminal error and **zero** model requests. Add cases for model response errors and for no semantic errors. Never import `seed_labels.json` into the validator or use task IDs in decision logic.
- Later, after a real image-capable endpoint is verified, measure the untouched baseline against the seeds and document two recurring validator failures before claiming assignment-style improvements. **Part 1's baseline measurement is not yet complete** and cannot be replaced by mocked scores.

**Step 1 — verified source review and branch sync (user-executed):** The user ran `git fetch origin`, attached local `feature/session-003-semantic-validator` to `origin/feature/session-003-semantic-validator`, and fast-forwarded from `c3b0189` to journal commit `e77e037`. `git status --short --branch` showed a clean tracking branch. Inspected `ASSIGNMENT.md` lines 78–108 (all four error families and label boundaries) and `validator/solution.py` lines 42–74 (incomplete semantic functions). No model or validation call was made.

**Step 3 — verification passed in Codespaces (user-executed):**

- `git pull --ff-only` fast-forwarded local `feature/session-003-semantic-validator` from `e77e037` to `20cc0f6`. Git reported exactly four changed files: `README.md`, `docs/Learning-Progress.md`, `tests/test_validator_semantic_offline.py`, and `validator/solution.py`.
- `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v`: **14 tests passed, 0 failures/errors**, in 0.053 seconds. The seven semantic-integration mocks and seven earlier deterministic-execution cases all passed.
- `uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v`: **five tests passed, 0 failures/errors**, in 0.017 seconds.
- `uv run python scripts/offline_preflight.py`: **PASSED**, with 110 runs, 98 figures, 110 labeled runs, 16 acceptable; label category counts: execution_failure 12, hard_to_read 39, wrong_chart 71, wrong_data 25. No model/cloud inference occurred.
- `git status --short --branch`: `## feature/session-003-semantic-validator...origin/feature/session-003-semantic-validator` with no modified or untracked file lines.
- GitHub Actions `Offline dataset checks` succeeded for implementation head `20cc0f6` (run 42163734524). CI should be checked again for the later journal-only commit before merge.

**Interpretation:** The first end-to-end semantic plumbing is verified with mocks and obeys the expected schema and short-circuit behavior. This is **not** evidence of real chart-judging accuracy; the supplied baseline semantics are reused rather than improved. No real predictions, per-family MCC, or macro-MCC yet.

**Step 2 — minimal semantic integration committed, Codespace verification pending:**

- Updated `validator/solution.py`: preserve image existence and PNG integrity checks for exclusive terminal `execution_failure`; for valid PNGs, `judge_data_and_chart` delegates to `validator.baseline.judge_data_and_chart` (two separate prompts), and `judge_readability` delegates to `validator.baseline.judge_readability` (one prompt). The final `validate(run)` contract is unchanged.
- This **reuses** the supplied judge; it is **not a measured improvement** on wrong-data, wrong-chart or readability accuracy and does not modify the official fixed model policy.
- Added `tests/test_validator_semantic_offline.py` with **seven synthetic mock tests**, covering three multimodal prompt payloads (task, CSV, trajectory, PNG), expected families + serialized schema, all-NO, all-YES, missing and corrupt PNG skipping the model, propagated model exceptions, and malformed response handling.
- Tests patch `validator.baseline.complete`, so no live endpoint is required and no label information is passed into the validator. The existing CI glob `test_validator_*_offline.py` is already configured to discover both the seven preexisting execution tests and these seven new tests.
- Updated `README.md` to distinguish the new end-to-end wiring from actual image-capable evaluation. Current code commits on this branch: `62164c8` (integration), `eb6619d` (new mock tests), `2235376` (README).
- **Verified:** all seven new semantic mock tests plus seven earlier execution tests passed in Codespaces, five structural tests passed, seed preflight passed, and Actions on the implementation head passed. **Still not verified:** a live image-capable judge and actual semantic accuracy. The full runner should not be invoked without a compatible image-capable endpoint because errors will propagate.

**What to run next from Codespaces:**

~~~bash
git pull --ff-only
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python scripts/offline_preflight.py
git status --short --branch
~~~

**What is not established:** correct model judgments on real charts, context fallback with an actual vLLM server, model credential deployment, per-family accuracy and macro-MCC.



**Next:** Review [draft PR #4](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/4), verify CI on its latest head, and decide whether to merge this explicitly limited, mock-tested integration milestone. Next learning goal: verify a permitted real vision-model endpoint and establish actual baseline and solution scores without using human labels to generate predictions.

### Session 004 — 2026-11-05 (America/Vancouver) — Planning exact-checkpoint vision evaluation

**Goal:** Establish a real, evidence-based route to the official `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` multimodal evaluator without Modal, then measure baseline and solution predictions against held-out-by-construction seed human labels. Do not call a paid model or mislabel mock responses as accuracy measurements.

**Starting Git state (user-confirmed):** Session 003 PR [#4](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/4) was merged into `main` at `4bfcd74`. The user fast-forwarded local `main`, deleted the old local feature branch, and created a clean `feature/session-004-vision-evaluation` branch with `git status --short --branch` showing no changes. A same-named remote branch now stores this journal entry. Sync it before making local edits.

**Verified source review:**

- `ASSIGNMENT.md` mandates **exact checkpoint** `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` for official validator comparisons, rather than an arbitrary vision-language or text-only model. The scorer expects `validate(run) -> list[Error]` and four families; `seed_labels.json` is for *scoring*, not for producing predictions.
- `validator/model.py` already supports OpenAI-compatible `VALIDATOR_BASE_URL`, `VALIDATOR_API_KEY`, and `VALIDATOR_MODEL` (default service alias `validator`). An alias alone does **not** demonstrate which weights back the endpoint.
- `.env.example` remains the canonical **Modal-oriented** template; its example URL and token are placeholders, not a working endpoint. Do **not** put secrets into git, terminal logs, or assistant messages.
- `validator.baseline` retries context overflow by calling vLLM-like `tokenize` / `detokenize` routes outside `/v1`. Thus ordinary OpenAI-compatible chat completion support **does not guarantee** that all existing context-overflow fallbacks work.
- The validator's Session 003 semantic integration is mock-tested (14 validator + 5 original offline tests and green CI), but **no image-bearing response from an actual VLM has been observed**, and no MCC is measured.

**External documentation reviewed on 2026-11-05:**

1. Official FP8 checkpoint: https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct-FP8 — publishes weights and documents `vllm serve "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8"` plus OpenAI-compatible image requests.
2. Qwen official deployment docs: https://github.com/QwenLM/Qwen3-VL — recommend vLLM (v0.11+) or SGLang for multimodal serving.
3. vLLM recipes: https://docs.vllm.ai/projects/recipes/en/stable/Qwen/Qwen3-VL.html — serving and OpenAI-compatible clients, including GPU requirements and practical limitations. Do **not** confuse a different 235B-model hardware example with an exact 30B requirement.

**Deployment approaches (investigation only; availability, cost and identity are NOT yet verified):**

- **Remotely host the exact FP8 checkpoint on a GPU VM / dedicated inference endpoint**, run vLLM or a compatible image-serving stack, use the Codespace only as an API client. This is a feasible technical route; deployment, GPU VRAM sufficiency, token handling, costs and checkpoint provenance require verification.
- **Use an already-hosted OpenAI-compatible provider only if the provider can attest to the exact FP8 checkpoint**, image support and authentication. Similar model names, a "Qwen3-VL" generic API, or an API model alias alone do not establish checkpoint identity.
- **Codespaces-only local inference** is not assumed possible. Verify whether this particular Codespace has CUDA GPUs and appropriate GPU memory before considering it. Installing Python libraries alone does not provide GPU access.

**Safety and reproducibility guardrails:** Offline discovery first. Before any `--live` or image-bearing request, record the provider, deployed checkpoint/revision, transport URL without credentials, request limits, billing/timeout policy, and how to avoid leaking secrets. A two-image *controlled content* probe is stronger evidence of actual vision support than a successful HTTP 200 from a text endpoint; it still cannot independently prove the model's weight identity. Do not claim a private-grade-equivalent score if the deployment or model differs.

**First Codespace exercise (offline, no model requests):**

~~~bash
git fetch origin
git branch --set-upstream-to=origin/feature/session-004-vision-evaluation
git pull --ff-only
command -v nvidia-smi >/dev/null && nvidia-smi -L || echo "No nvidia-smi GPU inventory available"
uv run python - <<'PY'
import os
from dotenv import load_dotenv

load_dotenv()
for key in ("VALIDATOR_BASE_URL", "VALIDATOR_API_KEY", "VALIDATOR_MODEL"):
    value = os.getenv(key)
    if key == "VALIDATOR_MODEL":
        print(f"{key}: {value if value else '(unset; code defaults to validator)'}")
    else:
        print(f"{key}: {'configured' if value else 'not configured'}")
print("No network or model call made.")
PY
git status --short --branch
~~~

**First Codespace audit — user-executed:**

- `git fetch origin`, `git branch --set-upstream-to=origin/feature/session-004-vision-evaluation` and `git pull --ff-only` succeeded; local branch advanced from `4bfcd74` to journal commit `147f811`. `git status --short --branch` showed a clean tracking branch.
- `command -v nvidia-smi >/dev/null && nvidia-smi -L || echo "No NVIDIA GPU inventory available"` printed **No NVIDIA GPU inventory available**. This shows no accessible NVIDIA inventory via that command, **not** a proof that no alternative accelerator exists. Avoid relying on Codespaces for the 30B FP8 inference deployment.
- The attempted `uv run python - <<'PY'` configuration audit raised `AssertionError` from `dotenv.find_dotenv`, at `assert frame.f_back is not None`, because `load_dotenv()` attempted automatic script-based discovery from Python executed via stdin. **Environment-variable status remains unknown.** This is a script-discovery issue; it is not evidence that a token or endpoint is missing.
- Safer next audit: `load_dotenv(dotenv_path=Path.cwd() / ".env")` with `from pathlib import Path`, and print only whether `VALIDATOR_BASE_URL` and `VALIDATOR_API_KEY` are configured, not their values. The actual repository's `validator/model.py` is imported from a normal file and need not be modified solely because the heredoc failed.
- No live requests, GPU deployment, model downloads, costs, or MCC scores occurred.

**Hosted-model selection discussion (verified public model/provider docs; deployment untested):**

- **Official exact-checkpoint route:** Qwen's `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` from https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct-FP8 served with GPU-backed vLLM/SGLang. This provides the strongest fidelity to the official model requirement if checkpoint/revision and serving configuration are recorded. Codespaces would be the API client, not the inference host.
- **Lower-operations same-family prototype:** A hosted API model named `qwen3-vl-30b-a3b-instruct` is listed by Alibaba Model Studio and Novita; its exact FP8 checkpoint, image behavior, and vLLM tokenizer extensions **must be verified** and cannot be assumed from the marketing/model ID. Novita's advertised standard pricing is approximately USD `$0.20 / 1M input tokens` and `$0.70 / 1M output tokens` at https://novita.ai/pricing; these are price-page figures, **not quoted job costs**, and availability may change.
- **Lower-cost pilot with a different model:** Alibaba Model Studio lists `qwen3-vl-flash` with low token rates (e.g. `$0.05 / 1M input` and `$0.40 / 1M output` for a Singapore region tier; source https://www.alibabacloud.com/help/en/model-studio/model-pricing). Its semantics/checkpoint differ from the assignment's required model, so results would be engineering experiments only, never official-equivalent baseline scores.
- Avoid using Assignment 1's previously tested **text-only GLM** chat endpoint for chart judging: its successful text/tool calls do not demonstrate vision.
- Before any model request, distinguish hardware setup (GPU hosting billable), provider API billing (token/image-dependent), and model accuracy. The old baseline's vLLM `/tokenize` fallback may not work on generic third-party chat endpoints.

**Current results:** Git/GPU-command audit and dotenv script-discovery failure confirmed. No reliable environment-variable configuration status, live endpoint, vision probe, model inference, score, or new code test yet. **Decision deferred to user:** prioritize exact official checkpoint fidelity versus cheap hosted exploration before writing a live probe.

**User decision — Z.ai vision first:** The user chose `glm-4.6v-flash` for **offline-first, cost-controlled independent exploration** instead of exact official-checkpoint scoring. This does **not** change the course's required Qwen3-VL validator or establish its accuracy.

**Provider evidence rechecked (2026-11-05 America/Vancouver):**

- https://docs.z.ai/guides/vlm/glm-4.6v lists GLM-4.6V-Flash as an image/text input model; https://docs.z.ai/guides/overview/quick-start documents the OpenAI-compatible client at `https://api.z.ai/api/paas/v4/`.
- https://docs.z.ai/guides/overview/pricing currently lists `GLM-4.6V-Flash` as **Free** for input, cached input, storage, and output; this is public pricing, not verified account entitlements or absence of rate limits.
- Z.ai API docs document `image_url` multimodal content, output token limits and the optional `thinking` setting: https://docs.z.ai/api-reference/llm/chat-completion . The live **data-URL/base64** form is plausible, but its acceptance by this exact hosted account has **not** been tested yet.
- Successful GLM-4.7-Flash **text** calls in Assignment 1 do not establish GLM-4.6V-Flash vision access; the model names and modalities differ.

**Step 2 — probe and mock tests committed, Codespace execution pending:**

- `scripts/zai_vision_probe.py`: creates a 256×256 synthetic bar chart (BLUE visibly taller than ORANGE), builds a text + PNG `image_url` data-URL request, and **defaults to offline mode with no network call**. Any live call needs **both** `--live` and `--confirm-one-request`, an existing `ZAI_API_KEY`, and uses the fixed Z.ai endpoint, `glm-4.6v-flash`, 64 max output tokens, disabled thinking, 45-second timeout, and **zero automatic retries**. Only one completion can be attempted per invocation. Prints minimal answer/usage without exposing API key or raw HTTP response body. Distinguishes a wrong/ambiguous answer from transport failure. Never touches seed artifacts, labels, or `validator/model.py`.
- `tests/test_validator_vision_probe_offline.py`: adds **eight synthetic tests** covering PNG pixel content and height, encoded image payload, zero-request dry run, double opt-in, missing-key short circuit, one fake request with fixed host/no retries, wrong answer handling, and provider failure handling. CI's existing `test_validator_*_offline.py` glob should discover all **22** validator tests (7 structural execution, 7 semantic integration, 8 probe) if this suite passes.
- `README.md`: includes usage, opt-in safeguards, cost/rate-limit caveats, and official-checkpoint non-equivalence.
- **Pending:** Codespace output for `uv run python scripts/zai_vision_probe.py`, 22 validator tests, five existing structural tests, and dataset preflight; GitHub Actions CI. No live Z.ai request was made in this session yet.

**Updated next exercise:**

~~~bash
git pull --ff-only
uv run python scripts/zai_vision_probe.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python scripts/offline_preflight.py
git status --short --branch
~~~

**Only after these pass and the user explicitly approves one live attempt:** `uv run python scripts/zai_vision_probe.py --live --confirm-one-request`. Check that `ZAI_API_KEY` is configured without printing its value. Do not launch live as part of CI or the offline test suite.

**Step 3 — offline checks and live Z.ai vision probe verified (user-executed):**

- The user ran `git pull --ff-only` from `147f811` to `603b3fc` and confirmed a clean `feature/session-004-vision-evaluation...origin/feature/session-004-vision-evaluation` tracking branch.
- Default `uv run python scripts/zai_vision_probe.py` reported `mode=offline`, `network_requests=0`, `api_key_configured=true`, synthetic image `256×256`, `image_bytes=827`, request parts `[text,image_url]`, expected answer BLUE, and `official_qwen_equivalent=false`. No credential value was printed.
- `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v` completed **22/22 tests passing** in 0.091 seconds (7 original execution + 7 semantic integration + 8 vision probe). The usage messages in the double-opt-in test are expected argparse error output; that test passed.
- `uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v` completed **5/5** in 0.008 seconds.
- `uv run python scripts/offline_preflight.py` **PASSED** (110 runs, 98 figures, 110 labeled runs, 16 acceptable; execution_failure 12, hard_to_read 39, wrong_chart 71, wrong_data 25). Offline checks called no model or cloud resources.
- The user voluntarily invoked the one-request live command `uv run python scripts/zai_vision_probe.py --live --confirm-one-request` **after offline validation**. Z.ai response: `model_requested=glm-4.6v-flash`, `model_reported=glm-4.6v-flash`, `answer=BLUE`, `expected=BLUE`, `vision_smoke_test_passed=true`, `completion_attempts=1`, usage **118 prompt tokens + 4 completion tokens = 122 total tokens**, and `official_qwen_equivalent=false`.
- GitHub Actions on code head `603b3fc`, workflow run `42165860956`, also completed **success**. Job logs show **22/22 validator tests and 5/5 structural tests passing**.
- **Interpretation:** We now have concrete evidence of account access to Z.ai GLM-4.6V-Flash and at least one correct image-grounded simple response using the actual OpenAI-compatible endpoint. This does **not** establish robust chart correctness, model checkpoint provenance beyond the API-reported ID, cost charged, or any MCC accuracy.
- **Next experiment:** A strictly bounded independent two-run pilot on real public data-visualization trajectories, with baseline and solution evaluated separately and existing human labels used only afterward for scoring. Design offline mocked plumbing, rate limits and output separation before sending larger or sensitive contents. The released trajectories may include task/user data, so review the specific pilot payload before upload to an external provider. Keep Z.ai results explicitly separate from official Qwen metrics. Do not run an unbounded sweep.

**Review state:** [Draft PR #5](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/5) is open and unmerged. Its purpose is solely the safe single-image capability probe. Review and merge this small milestone independently before expanding to multi-run scoring.

**Next after offline inventory:** Select exact-checkpoint deployment route based on actual hardware/access and budget, create a tiny opt-in image probe with mocked tests, run it once only after approval, and if successful pilot two seed trajectories before a full baseline sweep.

### Session 005 — 2026-11-05 (America/Vancouver) — Bounded real-seed vision evaluation

**Starting point:** The user merged [Session 004 PR #5](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/5) into `main` at `8b9baa0`, fast-forwarded the Codespace's `main`, removed `feature/session-004-vision-evaluation` locally and created a clean local `feature/session-005-seed-evaluation`. A matching remote branch was created.

**Goal:** Turn the proven one-request synthetic Z.ai GLM-4.6V-Flash vision probe into a reproducible, controlled evaluation of two real seed trajectories, using **labels only after predictions are complete**. This is an independent model experiment, not official-equivalent scoring.

**Source read and bounded study selection:**

- `Run.load()` in `validator/runner.py` loads `result.json` instructions, agent messages, existing `figure.png` and task input paths. The generic runner includes retries and is not appropriate for this small API-budget pilot.
- `validator/solution.py` first checks a PNG deterministically and then calls the three semantic baseline questions: `wrong_data`, `wrong_chart`, and `hard_to_read`. `validator.baseline._ask` sends the **full task instructions, trajectory, input file contents, and image** to a model; the baseline also uses vLLM-specific `/tokenize` routes if it detects context overflow.
- `workflow/evaluate.py` enforces matching coverage of labels/predictions for official MCC scoring. Two runs are not enough to support generalizable MCC claims; report per-run predicted/missed/false-alarm families before attempting a larger measurement.
- Seed **004** contains 10 trajectory messages and a mathematical multi-panel visualization with no CSV inputs. Seed **008** contains 23 messages, a Sankey diagram, and `inputs/008/data.csv`. Both have existing PNG figures. This small pilot chooses these IDs for **study scope only**, not for answer lookup or error rules.
- The human labels for 004 and 008 have been reviewed manually in earlier sessions; **do not put them into any model prompt or inference branch.** They remain for independent post-hoc analysis.

**Offline-first implementation committed, Codespace tests pending:**

- Added `scripts/zai_seed_pilot.py`. Default execution is a **zero-network preview** for both run IDs. The preview calls the real `solution.validate(run)` with patched completions; it prints only request sizes, figure dimensions and input filenames/lengths, never raw CSV/figure/labels/secrets. It rejects malformed figures and unexpected number of semantic requests.
- Live mode is **opt-in twice** (`--live --confirm-three-requests`), permits exactly **one** selected run per invocation (`--run-id 004` or `008`), pins `glm-4.6v-flash` and Z.ai's original verified endpoint, and caps the count at **three** completions with 250 max output tokens each, 60-second per-request timeout and `max_retries=0`. It suppresses the baseline's vLLM tokenizer overflow recovery, failing explicitly instead of calling a different provider. The Z.ai API key is read from Codespaces Secrets or an ignored local `.env`, never printed or passed into the run.
- The content uploaded to Z.ai when live includes **task specification, full agent messages/trajectory, full original input CSV(s), and base64-encoded `figure.png`**. Review this scope before authorizing any live call; an agent trajectory is data to evaluate, not trusted instructions to execute.
- The script writes per-run `PredictionFile` JSON and separate model usage metadata under ignored `output/`, refuses overwrite to prevent repeated requests, and avoids saving partial successes as full predictions.
- Only the separate offline `--compare --run-id ...` path imports human-label parsing, reads `seed_labels.json`, and compares category sets. Predictions come from the model without label consultation. This comparison is descriptive, **not macro-MCC**.
- Added **10 new offline tests** (`tests/test_validator_seed_pilot_offline.py`) verifying preview/no-network behavior, the two opt-ins, a one-run scope, valid three-call mock execution, transport and ambiguous-answer failure handling, budget exhaustion, duplicate-output protection and label separation.
- Updated `README.md` with the exact commands and limitations. Existing CI discovers these tests via the `test_validator_*_offline.py` glob, so it should run **32 validator tests** if all pass (22 previous + 10 new); the five structural tests should remain separate.

**Step 2 — CI test feedback and correction (verified in GitHub Actions):**

- First CI run **42167679888** failed 1 of 32 tests while five original tests passed. The failure was in the synthetic `test_live_calls_exactly_three_and_writes_only_new_output`: it mocked output file paths under a temporary directory but left `pilot.ROOT` pointing to the checkout; the application's relative-path status formatting therefore raised `ValueError: ... is not in the subpath of ...`. This was a **test-fixture configuration mistake**, not an inference/model issue.
- Updated the mock test to patch `pilot.ROOT` to the same temporary directory as the fake output files, commit `ceacaef`.
- Follow-up CI run **42167757712** completed **success**: **32/32 validator tests**, **5/5 structural tests**, dataset offline preflight **PASSED**. CI made **no model/cloud inference calls**.
- CI success verifies the integration and isolation under the synthetic tests; **user Codespace verification remains pending**. No live seed predictions or MCC exist yet.

**Step 3 — Codespace offline verification passed (user-executed):**

- Local branch `feature/session-005-seed-evaluation` set to track `origin/feature/session-005-seed-evaluation`; `git pull --ff-only` fast-forwarded from `8b9baa0` to `6ef1d80`, and final `git status --short --branch` showed no modified/untracked files.
- `uv run python scripts/zai_seed_pilot.py` printed a **zero-network** preview with `planned_completion_requests=3` for each seed, `model=glm-4.6v-flash`, `human_labels_sent=false`, and `official_qwen_equivalent=false`. Run 004: 1200×1000 PNG, 137,276 bytes, 1034 instruction characters, 10 trajectory messages, no input CSV, and three multimodal text prompt lengths **13,042 / 13,048 / 13,033** characters. Run 008: 1500×1050 PNG, 160,555 bytes, 714 instruction characters, 23 messages, one `data.csv` input (14,475 bytes), and prompt lengths **37,126 / 37,132 / 37,117** characters.
- `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v` **32/32 passed** (0.113 seconds); `uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v` **5/5 passed** (0.007 seconds). Argparse usage output in a deliberately invalid-flag test is expected; test was marked `ok`.
- Dataset preflight **PASSED**, reporting 110 runs, 98 figures, 110 labels, 16 acceptable and human label counts: `execution_failure=12`, `hard_to_read=39`, `wrong_chart=71`, `wrong_data=25`. This is ground-truth inventory, **not** Z.ai predictions.
- **Interpretation:** The pilot is ready for a separately authorized, single-run live call, beginning with 004; run 008's longer prompt and CSV are deferred. No live requests were made in these commands. Human labels must remain out of inference requests; `--compare` reads them only after a saved prediction exists.

**Proposed next step, only after reviewing the public seed payload and consenting to its transmission to Z.ai:**

~~~bash
git pull --ff-only
uv run python scripts/zai_seed_pilot.py --run-id 004 --live --confirm-three-requests
# If this created a prediction file successfully, compare offline:
uv run python scripts/zai_seed_pilot.py --run-id 004 --compare
git status --short --branch
~~~

There are **at most three** model completion attempts per live invocation with no automatic retries and a 60-second per-request timeout. Stop if authentication, rate limits or prompt-size errors occur; never share credentials or raw API error bodies. A two-case pilot cannot yield a statistically meaningful generalization claim or official Qwen score.

**Step 4 — first attempted live seed 004 evaluation failed (user-executed):**

- On clean local feature branch, `git pull --ff-only` succeeded and fast-forwarded to journal commit `0878a88`.
- The user explicitly invoked `uv run python scripts/zai_seed_pilot.py --run-id 004 --live --confirm-three-requests`. The program returned `mode=live`, `run_id=004`, `success=false`, `error_type=ValueError`, `http_status=null`, `automatic_retries=0`, `max_completion_attempts=3`. **Do not infer that three requests occurred**; this was the cap, not an observed request count.
- A subsequent `--run-id 004 --compare` returned `FileNotFoundError`, consistent with no complete saved `output/session005_zai_004_predictions.json`. This is a *missing output*, not a comparison score.
- The previous error reporting suppressed the exact `ValueError` source, so we cannot establish from the user-visible terminal whether the problem occurred before a request, in the model response format (e.g. reply not beginning YES/NO), or while storing results. **Do not claim a model-quality failure or a provider outage.** Z.ai had previously passed a simpler controlled image test.
- **Learning:** Mocked integration tests and successful HTTP vision probes cannot guarantee that a real multi-thousand-character chart-judging prompt elicits the required machine-parsable response. Future failures need secure structural telemetry without printing raw provider responses, input data or secrets.

**Step 5 — safe diagnostic changes added; offline verification complete:**

- `scripts/zai_seed_pilot.py` now tracks `stage`, `completion_attempts` (incremented before any API request), `responses_received`, and `validated_replies` on the live path. When the returned answer does not begin with YES or NO, it reports only `reply_class`, character count, allowlisted `finish_reason`, and `completion_tokens`. Exception strings and raw model-generated content remain suppressed; no human label is read during inference.
- `tests/test_validator_seed_pilot_offline.py` adds four synthetic tests of safe reporting for malformed replies, second-call failure, transport errors, and main's redacted error JSON; these run with **mock clients only**, without Z.ai.
- No provider retry has occurred as part of this code change. Since the earlier failed live response was not preserved, the new diagnostics cannot retrospectively identify its root cause. A further live attempt would be a **new** invocation with up to three potential model requests; obtain deliberate user opt-in only after the updated offline tests pass.
- The pilot remains independent, labeled `official_qwen_equivalent=false`. No actual model predictions or MCC exist yet.

**Next investigation commands (offline, no Z.ai request):**

~~~bash
git pull --ff-only
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python scripts/zai_seed_pilot.py --run-id 004
git status --short --branch
~~~

**Step 6 — diagnostic code confirmed in Codespaces (user-executed):**

- `git pull --ff-only` advanced the local feature branch from `0878a88` to `419633b`, including the privacy-safe diagnostic changes.
- `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v` completed **36/36 tests passing** in **0.226 seconds**. Mocked failure and redaction tests all passed. The expected argparse usage output from one intentionally invalid-flags test was not a failure.
- `uv run python scripts/zai_seed_pilot.py --run-id 004` reported `mode=offline`, `network_requests=0`, three planned model completions, figure dimensions **1200 × 1000**, figure size **137,276 bytes**, instruction length **1,034 characters**, **10** trajectory messages, zero CSV inputs, and prompt sizes **13,042 / 13,048 / 13,033 characters**. It confirmed `human_labels_sent=false`.
- Final `git status --short --branch` showed a clean feature branch tracking `origin/feature/session-005-seed-evaluation`.
- **No further live API call was made** in this verification. No new model prediction or MCC has been measured. Latest GitHub Actions on `419633b` also passed.

**Earlier plan before the second live attempt:** Given the user's earlier authorization to perform a tightly bounded one-run live evaluation, a new **deliberate** invocation of `uv run python scripts/zai_seed_pilot.py --run-id 004 --live --confirm-three-requests` is now reasonable if the user consents to send the same public seed content again. It may make up to three new Z.ai requests, with no automatic SDK retries. Check returned `stage`, actual `completion_attempts`, `responses_received`, `validated_replies`, `reply_class`, and `finish_reason`; do not reveal raw provider responses, secret tokens or user data. Only run `--compare` if the live command succeeds and saves a prediction file. Keep draft PR #6 unmerged until this live issue is understood, and do not proceed to run 008 automatically.



**Step 7 — second live run 004 attempt and model-provider decision point (user-executed):**

- User pulled latest docs `f0d63d2` and deliberately ran `uv run python scripts/zai_seed_pilot.py --run-id 004 --live --confirm-three-requests`.
- This time the privacy-safe failure report showed `error_type=ValueError`, `stage=response_validation`, `completion_attempts=1`, `responses_received=1`, `validated_replies=0`, `reply_class=non_yes_no_text`, `reply_characters=1084`, `finish_reason=length`, and `completion_tokens=250`. No HTTP status or automatic SDK retry was reported. The Z.ai endpoint **returned a response**, but the model's response did not begin with `YES` / `NO` and was cut off at the exact **250-token** output cap. This directly establishes a **response-format/truncation failure**, not a connection failure; it does **not** establish anything about the model's visual accuracy.
- The subsequent user-triggered `--compare` failed with `FileNotFoundError`, because the pilot does not save incomplete predictions. **No prediction, comparison, or MCC** is available. Do not retry with unchanged settings.
- The user asked whether to use **OpenAI API instead**. Recommended experimenting next with `gpt-5.4-mini` as a **separate, optional provider**, keeping GLM results distinct and documenting this as **not** the official `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8`. OpenAI's current model documentation confirms image inputs and Structured Outputs at https://developers.openai.com/api/docs/models/gpt-5.4-mini and https://developers.openai.com/api/docs/guides/structured-outputs .
- **Engineering recommendation:** Do **not** simply swap the client/model in the current `YES/NO` parser. Add a provider-isolated adapter with a strict machine-readable schema (e.g. `has_error: bool`, `evidence: str`), bounded token budget and one-call test, preserve label-free inference and output provenance, and add offline mock tests before running OpenAI. Current advertised pricing is USD `$0.75 / 1M` input and `$4.50 / 1M` output tokens for GPT-5.4 Mini, including billed image tokens; actual cost depends on usage and requires separately funded API access. Do not presume a ChatGPT subscription supplies API access.
- **Status:** Provider switch is a recommendation, **not yet approved or implemented**; no OpenAI request made, no API key requested or exposed, and draft PR #6 remains unmerged. Z.ai may still be worth revisiting later with different prompting/output limits.

**Step 8 — user approved OpenAI API integration (coding only; no live calls):**

- User explicitly asked to **add OpenAI API support to the repository**, noting that their existing Codespace may need refreshing. We did not ask the user to share credentials or assert their API account has billing enabled. The official Qwen checkpoint remains unchanged. Do not claim OpenAI experimental scores are official or equivalent to Z.ai/Qwen.
- Current OpenAI [GPT-5.4 Mini model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini) lists `gpt-5.4-mini` with **image inputs**, Chat Completions, and **Structured Outputs**. [Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs) explains a strict JSON schema and the need to handle refusal/incomplete output. Published token rates are currently USD **$0.75 per 1M input** and **$4.50 per 1M output** tokens, with images contributing billed input tokens; actual bills and availability depend on the API account. These were verified during this session; no API request or paid test has been initiated.
- Added standalone `scripts/openai_seed_pilot.py`: default **offline-only** preview, single selected `004` or `008` run and one semantic family (`wrong_data` by default), with **no human labels read**. Live mode requires **both** `--live --confirm-one-request` and `OPENAI_API_KEY`. The host is fixed at `https://api.openai.com/v1/`, model at `gpt-5.4-mini`, 400 max completion tokens, reasoning effort `none`, 60s timeout and `max_retries=0`. It requests exactly `has_error: boolean` and `evidence: string` via strict `json_schema` response format, with no vLLM tokenizer fallback and no response-prefix parsing.
- The new adapter **does not** modify `validator.model`, `validator.solution`, or `scripts/zai_seed_pilot.py`. The result is **one family decision**, not a full `PredictionFile`, stored in ignored `output/session005_openai_<run>_<family>_decision.json`. It prevents overwriting, validates response completion, JSON field types, and nonempty evidence, and prints only safe failure metadata rather than model exception strings or untrusted raw payloads.
- **Only** the separate `--compare` command can load `seed_labels.json`, after a decision file exists; it produces a single-family TP/FP/FN/TN observation, not MCC. Each API call includes real public task instructions, trajectory, relevant input-file contents and PNG, but **no human labels**. Preview outputs metadata only.
- Added `tests/test_validator_openai_seed_offline.py` with **13 mocked tests**, covering payload preparation, zero-network preview, strict schema, refused and truncated response rejection, exact call parameters, exception redaction, double opt-in, no key/no output overwrite, local output, and post-hoc label isolation. Alongside the previously passing 36 validator tests, CI should discover **49** tests; **this count is an expectation until CI verifies it**.
- Updated `README.md` and `.env.example` with separate OpenAI API setup and Codespaces instructions. No new Python packages were added (the starter already pins `openai==2.54.0`), and **no `.devcontainer` config was altered**. Configure `OPENAI_API_KEY` as a GitHub **Codespaces Secret**, scoped to this repo; a **stop/restart** of an existing Codespace activates new secrets, rather than rebuilding the whole container. Official source: https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces .
- No user-entered API key is recorded in GitHub source, journal, CI, or this conversation. Code and tests are committed on draft PR #6; **CI and user Codespace tests remain to be confirmed**. No OpenAI model inference was performed.

**Next commands (offline; no model request):**

~~~bash
git pull --ff-only
uv run python scripts/openai_seed_pilot.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
git status --short --branch
~~~

When a Codespaces secret has been added, verify `"key_configured": true` in the offline preview. If false, **stop and restart the existing Codespace**, not Rebuild Container. Only once offline tests and API budget checks pass should the user independently consent to the one-request opt-in. Keep PR #6 draft until that evidence is reviewed.

**Step 9 — Codespace OpenAI setup and offline checks verified (user-executed):**

- User fast-forwarded the feature branch from `f0d63d2` to `c4c38b2` with `git pull --ff-only`. No merge was performed.
- `uv run python scripts/openai_seed_pilot.py --run-id 004 --family wrong_data` completed an **offline** preview: `provider=OpenAI`, `model=gpt-5.4-mini`, `network_requests=0`, `planned_completion_requests=1`, `key_configured=true`, `prompt_chars=13424`, `trajectory_messages=10`, image `1200×1000` and `137276` bytes, no CSV inputs, `human_labels_sent=false`, and `official_qwen_equivalent=false`.
- The user ran `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v`: **49/49 passed** in **0.447 seconds**. `git status --short --branch` showed a clean branch tracking `origin/feature/session-005-seed-evaluation`.
- This is strong evidence that `OPENAI_API_KEY` is available in the active Codespace **without displaying its value**; no rebuild or restart is needed for this session. It is **not evidence** of sufficient billing credit, permissions, model access, or live compatibility.
- No OpenAI live request has yet been made. GitHub Actions had also passed 49 validator tests and five structural tests on the current implementation. The next step is a separately authorized, **one-call** `wrong_data` pilot. If successful, use `--compare` to compare the already saved decision against human labels offline. Do not move to other families or run 008 without reviewing this first case.

**Step 10 — first actual OpenAI seed-004 vision judgment (user-executed, SUCCESS):**

- The user pulled the journal update to `7355f53`, then explicitly invoked `uv run python scripts/openai_seed_pilot.py --run-id 004 --family wrong_data --live --confirm-one-request` after completing local offline tests and configuring the API key.
- **The call succeeded:** `mode=live`, `success=true`, one completion attempt, `model_requested=gpt-5.4-mini`, `model_reported=gpt-5.4-mini-2026-03-17`, `has_error=true`, `human_labels_sent=false`, `official_qwen_equivalent=false`. Usage was **5,649 prompt tokens + 101 completion tokens = 5,750 total**. The code saved the structured family decision under ignored `output/session005_openai_004_wrong_data_decision.json` in the user's Codespace; it did not commit or transmit the file to GitHub.
- The model's evidence was: "Yes. The fourth subplot is wrong: it plots 15^x on a linear x-axis, but the task requested data generated by raising 15 to a linearly spaced array and that both axes be logarithmic. The x-axis is not log-scaled, and the first three subplots also do not fully match the requested scaling/data layout (e.g., the first subplot uses a linear x-axis)." The full response is reproduced here **only because this public-data example was shared by the user**; the script itself does not emit or persist secrets.
- The user then ran the **offline** `--run-id 004 --family wrong_data --compare`: `predicted_error=true`, `human_error=true`, `match=true`, `outcome=TP`. This is **one true positive for one selected family**, not an MCC and not a full run verdict. The run's separate human `wrong_chart` label was **not** evaluated by this request.
- **Qualitative evidence audit is important:** the official seed human `wrong_data` explanation identifies a **missing cubing step in panel 4**, whereas this response did **not** explicitly identify that missing operation. It also mixed chart-design violations into a data judgment. In particular, the original instructions request a logarithmic **y-axis** for the first subplot, **not** a logarithmic x-axis; citing the first panel's linear x-axis as an error is therefore unsupported. The response correctly matched the binary family label but its explanation should **not** be counted as an accurate fault localization.
- **Engineering result:** OpenAI Chat Completions accepted the real 1,200×1,000 PNG + task/trajectory, returned a finished structured response, and the strict JSON parser accepted it without a prefix-format issue. This establishes a functioning experimental provider integration, **not** generalization, accurate evidence by itself, or equivalence to the official Qwen3-VL checkpoint.
- **Next controlled experiment:** Optionally test only `wrong_chart` on the **same** seed 004 using a new explicitly approved single request; it uses a separate per-family output file. Inspect its evidence against the public original instructions before expanding to run 008 or an MCC sweep. No automatic further model calls are authorized by this journal update.
- Keep [draft PR #6](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/6) open until the pilot is reviewed and the desired milestone scope is complete.

**Step 11 — OpenAI seed 004 `wrong_chart` single-request pilot (user-executed, SUCCESS):**

- The user fast-forwarded the Codespace feature branch from `7355f53` to `7033c56`. Offline preview for `--run-id 004 --family wrong_chart` reported `model=gpt-5.4-mini`, `network_requests=0`, `planned_completion_requests=1`, `key_configured=true`, `prompt_chars=13431`, `trajectory_messages=10`, a 1200×1000 PNG of 137,276 bytes, no input files, and `human_labels_sent=false`.
- The user explicitly authorized the **one-call** OpenAI live pilot for that family (`--live --confirm-one-request`). It returned `success=true`, `model_reported=gpt-5.4-mini-2026-03-17`, `has_error=true`, `completion_attempts=1`, usage **5,650 input + 104 output = 5,754 total tokens**, and a saved ignored local file `output/session005_openai_004_wrong_chart_decision.json`. No human labels were sent.
- Model evidence: "The figure does not follow the requested design in the fourth subplot: it should have both axes on a logarithmic scale, but the rendered plot only shows a log y-axis while the x-axis remains linear. Also, the requested x-data for the fourth subplot should be based on a linearly spaced array of powers of 15, but the plotted x-axis ranges from 0 to 30 and is not log-scaled."
- The user then ran the separate **offline** `--compare` command; it returned `predicted_error=true`, `human_error=true`, `match=true`, `outcome=TP`. The course human `wrong_chart` evidence is that the x-axis of `axes[3]` is linear when it should be logarithmic. The model's **central missing-log-x diagnosis is aligned with that evidence**; its additional claims about the fourth subplot's x-values were not independently established by this single-label comparison.
- **Comparison of the two independent family decisions on run 004:** `wrong_data` = TP and `wrong_chart` = TP; model calls used **5,750 + 5,754 = 11,504 total tokens** across two separate opt-in requests. The `wrong_data` label matched while its evidence missed the human-identified missing cubing operation. The `wrong_chart` justification is more faithful to the human-reviewed chart defect. No `hard_to_read` request was made; it must not be silently scored as negative based on an absent model result.
- **Conclusions:** The OpenAI structured-output integration now works for two distinct error families of a real figure, with two correct binary results but differing explanatory quality. This is not an estimate of overall accuracy, not a statistically meaningful MCC, and not equivalent to the assignment-required Qwen3-VL checkpoint. The two local decision files remain ignored by Git and PR #6 remains draft.
- **Next recommendation:** finish a controlled same-run 004 `hard_to_read` test (a possible true-negative case) only if the user explicitly opts into one more potentially billed request; compare offline afterward. Alternatively stop the live pilot here and review PR #6 as an integration milestone. Do not launch a broad sweep or run 008 automatically.

**Step 12 — OpenAI seed 004 `hard_to_read` evaluation completes all three semantic families (user-executed, SUCCESS):**

- User fast-forwarded the feature branch from `7033c56` to `8710a6f`. The default **offline** `--run-id 004 --family hard_to_read` preview reported `network_requests=0`, `planned_completion_requests=1`, `key_configured=true`, a 13,417-character prompt, 10 trajectory messages, a 1200×1000 PNG (137,276 bytes), and `human_labels_sent=false`.
- User explicitly opted into one live request: `uv run python scripts/openai_seed_pilot.py --run-id 004 --family hard_to_read --live --confirm-one-request`. It **succeeded** with one completion attempt, `model_reported=gpt-5.4-mini-2026-03-17`, `has_error=false`, usage **5,647 prompt tokens + 60 completion tokens = 5,707 total tokens**, and saved local ignored `output/session005_openai_004_hard_to_read_decision.json`. No label was supplied during inference.
- Model evidence: "The figure is legible overall: all four subplots, titles, axes, and curves are visible and readable. Some dense oscillations/error bars make parts busy, but not difficult or impossible to read."
- The separately executed offline `--compare` command reported `predicted_error=false`, `human_error=false`, `match=true`, `outcome=TN`. This is a **true negative** for the run's `hard_to_read` family; the evidence is consistent with the human label.
- **Completed seed 004 summary:** `wrong_data` = **TP** (5,750 tokens; explanation did **not** identify missing cubing operation); `wrong_chart` = **TP** (5,754 tokens; identified the human-noted missing logarithmic x-axis); `hard_to_read` = **TN** (5,707 tokens; legibility explanation aligned). **3/3 binary family decisions matched**, across exactly **3 separately authorized OpenAI API completions**, using **17,211 total reported tokens** (16,946 prompt + 265 completion). The case is still **one selected run**, not a statistical performance estimate. There is no valid macro-MCC from these three family decisions, and the official Qwen3-VL model was not used.
- The three `session005_openai_004_<family>_decision.json` files exist **only in the user's ignored Codespace `output/` directory**. The GitHub repo has source code, tests and this factual summary, but does not contain those raw response artifacts.
- **Recommended stopping point:** The run-004 pilot meets the goal of verifying OpenAI structured output on a real seed with independent post-hoc labels. Either close Session 005 as a reproducible integration milestone after CI and PR review, or separately opt into **run 008** (a longer trajectory plus 14,475-byte `data.csv`) as an additional case; do not auto-run three new billed questions or report MCC. Keep draft PR #6 unmerged until review.

**Next offline review commands (no model calls):**

~~~bash
git pull --ff-only
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python scripts/offline_preflight.py
git status --short --branch
~~~

**Next decision:** Review draft PR #6 as an integration milestone or independently authorize an additional single-family test on seed 008. Any seed 008 live request will send its task, 23 trajectory messages, `data.csv` contents and PNG to OpenAI, and is separate from the three completed seed 004 calls.

### Session 006 — 2026-11-07 (America/Vancouver) — Controlled seed-008 evaluation

**Starting point:** The user resumed after merging [Session 005 PR #6](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/6) into `main` at `d76e7e2`. In the restarted Codespace, 49/49 validator tests, 5/5 offline preflight tests, the 110-run/98-figure dataset check, and a clean `main` status were verified. The user created and pushed clean branch `feature/session-006-controlled-evaluation`.

**Goal:** Evaluate the released Sankey case `008` with a bounded OpenAI structured-output pilot. Inspect the data and figure independently; generate predictions **without human labels**; compare only after each response is saved. This is independent `gpt-5.4-mini` experimentation, **not** a run of the assignment-required Qwen3-VL judge.

**Offline preparation (user-executed):**

- `uv run python scripts/openai_seed_pilot.py --run-id 008 --family wrong_data` returned an offline preview with **0 requests**, **1 planned request**, `key_configured=true`, `prompt_chars=37508`, 23 trajectory messages, a 1500×1050 PNG of 160,555 bytes, and a 14,475-byte `data.csv`. `human_labels_sent=false`.
- `uv run python scripts/zai_seed_pilot.py --run-id 008` returned a separate **0-request** preview of 3 possible `glm-4.6v-flash` semantic requests. No live Z.ai request was made in Session 006.
- Independent CSV inspection found **1,000 input records**, five fruit labels, and **80** rows whose source is orange (targets: orange 53, banana 15, blueberry 8, apple 3, lime 1). The final plot script in `artifacts/008/result.json` uses `.query("source != 'orange'")`; the rendered figure shows four source nodes and total source weight **920**, consistent with the omitted 8% of rows. The original task did not authorize this filtering.
- Raw `csv.reader` using default UTF-8 gave **26** seemingly distinct source–target pairs because the first value contains a UTF-8 BOM (`\ufeffblueberry`). Re-reading with `encoding="utf-8-sig"` gave **25 normalized pairs** and exactly five labels: apple, banana, blueberry, lime, orange. The final plotting script itself already uses `utf-8-sig`. This is a data-inspection pitfall, not a second plotted-data defect.
- Visual inspection of the user-opened released `figure.png` showed pale, low-contrast node labels on white. The figure has an appropriate title and fruit-color legend; chart-design compliance was **not yet judged**. The released PNG is 160,555 bytes, whereas the final trajectory's file-check message reported 41,233 bytes; this discrepancy was noted but not resolved. Do not claim provenance of the released image beyond the released artifact.

**Bounded live judgments (user explicitly invoked each, separately):**

| Run/family | Model reported | API attempts | Tokens (prompt + completion = total) | Predicted error | Offline human label | Outcome |
| --- | --- | ---: | --- | --- | --- | --- |
| 008 / `wrong_data` | `gpt-5.4-mini-2026-03-17` | 1 | 13,508 + 73 = **13,581** | true | true | **TP** |
| 008 / `hard_to_read` | `gpt-5.4-mini-2026-03-17` | 1 | 13,506 + 60 = **13,566** | true | true | **TP** |
| 008 / `wrong_chart` | `gpt-5.4-mini-2026-03-17` | 1 | 13,509 + 88 = **13,597** | true | false | **FP** |

**Model evidence vs human evidence:**

- `wrong_data`: the model stated that the agent filtered out `source=orange`, altering Sankey flows/counts and leaving only four source nodes. The released human explanation identifies the missing orange source node. The explanation is aligned with the human-reviewed defect **and** the independent 80-row check. Offline `--compare` returned `match=true`, `outcome=TP`.
- `hard_to_read`: the model identified faint light-gray labels on white and also mentioned crowded overlapping ribbons. The released human explanation specifically identifies near-white `#f4f4f4` value labels on white. Label contrast aligns with the reference evidence; ribbon overlap is an additional observation, not a human-confirmed root cause. Offline `--compare` returned `match=true`, `outcome=TP`.
- `wrong_chart`: the model predicted `has_error=true`, claiming the figure is a custom ribbon rather than a proper Sankey and the labels are duplicated/mislabeled. The released human label has **no `wrong_chart` error**, and the task does not require a specific plotting library. The rendered figure contains source-left/target-right colored nodes with flow ribbons; showing the same fruit on both sides is expected for source and target roles. The model did not identify a specific unsupported chart-design deviation. Offline `--compare` returned `predicted_error=true`, `human_error=false`, `match=false`, `outcome=FP`. Treat this as an example of a **judge false positive and possible category confusion**, not as ground-truth proof that the generated chart is perfect.
- The first two successful responses reported `human_labels_sent=false` and `official_qwen_equivalent=false`. Those calls used **27,014 prompt + 133 completion = 27,147 tokens**. A third, separately opted-in `wrong_chart` request used **13,509 prompt + 88 completion = 13,597 tokens**. **All three** live requests together used **40,523 prompt + 221 completion = 40,744 tokens**. Token counts are usage, **not** monetary costs.
- The three successful decision artifacts are local, ignored Codespace files `output/session005_openai_008_wrong_data_decision.json`, `output/session005_openai_008_hard_to_read_decision.json`, and `output/session005_openai_008_wrong_chart_decision.json`. Their `session005` prefix comes from reusing the Session 005 script; these calls occurred in Session 006. **No raw decision file or API key is committed.**
- Final seed 008 outcome: **2/3 selected binary family matches (2 TP, 1 FP)**. Combined with completed seed 004 (2 TP, 1 TN), this yields **5 matches in 6 handpicked family judgments**; neither this fraction nor the degenerate two-run contingency tables supports generalizable accuracy or a meaningful per-family/macro-MCC.

**Commands executed and results:** Branch creation/push and `git status --short --branch` passed, the Z.ai preview and all three OpenAI family previews passed, independent CSV checks passed, and three separately authorized one-attempt `--live --confirm-one-request` invocations succeeded. Each subsequent `--compare` was offline: `wrong_data` TP, `hard_to_read` TP, and `wrong_chart` FP. The previously verified 49+5 tests and preflight preceded Session 006's branch creation; **no new tests or CI claim** is made for this documentation checkpoint.

**What we learned:** A model's correct binary answer is not enough: fault localization matters. Run `008` `wrong_data` provides both a model diagnosis and a deterministic cross-check, unlike the weaker `wrong_data` explanation on run `004`. Low contrast is a separate semantic failure. BOM handling can produce spurious raw CSV categories. Most importantly, the `wrong_chart` false positive demonstrates **overly restrictive chart-type interpretation**: a custom Matplotlib ribbon implementation can satisfy the requested Sankey's left-source/right-target structure, and repeated fruit labels on both sides are appropriate when categories participate in both roles. The model's claims of 'not a proper Sankey' and 'mislabeled/duplicated' nodes lack a concrete violated requirement. Neither the excluded orange source (wrong data) nor low-contrast labels (hard to read) proves a wrong-chart violation. This is one concrete **false-positive case study** for future validator-improvement work, not proof of a recurring failure mode across other runs.

**Next step:** Stop live testing for Session 006; no more paid calls are needed for the two preselected runs. Review this documentation-only milestone in a PR after rerunning the offline tests/CI. For a later session, design a narrowly scoped general `wrong_chart` improvement and evaluate it on additional independent cases rather than hard-coding run 008's answer. No validator behavior or official Qwen setting was changed in this session.

### Session 008 — 2026-11-07 (America/Vancouver) — Three generation providers and Terra judge adapter foundation (implementation pending verification)

**Starting Git state:** User verified `docs/Progress-Explained-20261107.md` was identical on `main` and `feature/session-007-wrong-chart-precision`, then fast-forward synchronized both. Local `main` tracked `origin/main` at `252140e`, working tree clean. User created and pushed `feature/session-008-provider-adapters` from that commit with a clean working tree. Session 007 remains unmerged at its own branch (`939b01f`) and its v1/v2 conclusions are not changed.

**User-approved independent research architecture and safety policy:** three plotting agent roles — DeepSeek `deepseek-flash`, OpenAI `gpt-5.6-luna`, Z.ai `glm-4.7-flash`; experimental visual judge — OpenAI `gpt-6.1-terra`. User has credentials for all three services and explicitly chose staged provider adapters before agent runner integration. Offline-first; **ask for approval before every potentially billed API request**. This changes the independent adaptation only, not the official course requirement for Qwen3-VL.

**Initial implementation on Session 008 feature branch (GitHub commits; Codespace tests pending):**

- `integrations/models.py` defines four immutable model role configurations with explicit provider, direct API ID, request API style, secret env var and endpoint. Requested and reported model versions are distinct; unknown roles fail.
- `integrations/providers/` implements pure, provider-specific request preparation: DeepSeek stateless Responses, OpenAI Responses, and Z.ai Chat Completions. A shared parser returns text, function-call IDs/names/JSON args, token usage, reported model and continuation items. Malformed, refused, truncated or unsupported outputs fail; tool calls are **data**, never executed.
- `execute_one` requires explicit `live=True` and `confirm_one_request=True` plus the relevant provider credential before creating a network client. It caps a compatibility completion at 512 output tokens, 60s timeout and 0 SDK retries. **No new live CLI is exposed or invoked.**
- `integrations/judge.py` defines a strict four-family Terra judgment JSON schema and an encoded/validated PNG input helper, without accessing labels or wiring into `validator.solution`.
- `scripts/provider_preflight.py` prints a safe four-role preview with `network_requests=0`; new `tests/test_provider_*_offline.py` use mocked replies and clients to check routing, tool-response formats, refusal/incomplete handling, authorization, and judge decoding.
- `pyproject.toml` includes `integrations` in the package build. `.github/workflows/offline-ci.yml` now discovers provider tests and runs the preview on PRs; `.env.example`, README and `docs/Provider-Migration-Plan.md` explain the environment and boundaries.
- Neither `validator/solution.py`, `validator/baseline.py`, `workflow/generate.py`, released artifacts, seed human labels, nor Session 007 pilot files was modified. The prior Modal runner and Qwen/vLLM baseline remain available, but no Modal service is deployed by these changes.

**Verified so far:** Branch creation/push and prior Git history; public provider documentation for API format. **Not verified yet:** Codespace `uv sync --locked`, provider offline unit-test results, GitHub Actions CI, user-account model access, live API replies, tool integration, figures from new agents, Terra judge predictions or MCC. No live request was made for Session 008.

**User Codespace verification — 2026-11-07 (completed, zero model API requests):**

- `git pull --ff-only` fast-forwarded `feature/session-008-provider-adapters` from `252140e` to `7e04d59` with 20 modified/added files and a clean working tree. `uv sync --locked` resolved 111 packages and rebuilt/reinstalled the local `hw2-validator` package with `integrations` included.
- `uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v`: **27/27 passed**. This tests provider registry, request routing, mock tool calls/replies, strict Terra judgment decoding, no-retry and double-consent gate paths.
- `uv run python scripts/provider_preflight.py`: **passed**, prints all four selected models and their correct API styles; global and individual `network_requests=0`, Terra alone marked as structured judgment, all `official_qwen_equivalent=false`.
- `uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v`: **49/49 passed**. (Session 008 branches from main rather than unmerged Session 007; the six Session 007-only tests are intentionally absent here.) The existing argument-parser rejection output is expected during a passing test.
- `uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v`: **5/5 passed**.
- `uv run python scripts/offline_preflight.py`: **PASSED**, confirming **110 runs, 98 figure PNGs, 110 labels**, with 12 execution_failure, 39 hard_to_read, 71 wrong_chart, 25 wrong_data and 16 acceptable labels. These are human-label counts, not model predictions.
- Final `git status --short --branch`: **clean and synchronized** with `origin/feature/session-008-provider-adapters`. Aggregate **81 passing offline tests** across all suites. No live network/model call, no generated figures, no Terra quality or MCC evaluation.

**Interpretation:** Phase A–C provider adapter scaffolding passes local mocked/synthetic verification. The configured API IDs are not yet confirmed accessible through the user's live accounts, and no agent tool loop, Docker integration, or actual judge inference has occurred. No claim of official equivalence.

**Next actions:** Sync this journal-only commit into the Codespace, review the 20-file branch diff and open a PR only after user approval. GitHub Actions runs on pull_request, so CI should be confirmed before merging. Keep Session 007 independent. All live provider smoke tests require separate explicit user approval after the reviewed offline PR.

### Session 009 — 2026-11-07 (America/Vancouver) — Individual API compatibility probe preparation

**Git starting point:** PR #8 merged into `main` at `5833b2b`, GitHub Actions successful. User synchronized Codespaces `main`, pushed an annotated Session 007 archive tag `archive/session-007-20261107` pointing to `939b01f`, deleted both local and remote Session 007 and Session 008 feature branches, verified clean synchronized `main` as the only remaining active branch. The archive preserves committed work, not ignored `output/` files.

**Session 009 intent:** User said to continue with the next agreed milestone: provider compatibility checks, with explicit authorization **before each model API request**. A new feature branch `feature/session-009-provider-compatibility` was created remotely from `main`. Public docs confirm configured API IDs and interfaces (DeepSeek stateless Responses, OpenAI Luna/Terra Responses, Z.ai Chat Completions); documentation is not evidence of account access.

**Offline preparation committed (user verification pending):**

- `scripts/provider_compat_probe.py` previews per-model synthetic requests without credentials or network. Generators receive an inert `run_shell` function descriptor requesting `printf session009`; the script never executes any model-proposed shell command. The experimental Terra judge receives an in-memory synthetic two-bar PNG and the existing strict four-family judgment schema; no released seed or human labels are included.
- One-request live path is guarded by all three of `--live`, `--confirm-one-request`, and `--approve-model EXACT_ID`, plus provider credentials. The code reuses `execute_one` (zero SDK retries, a 60s timeout, 512 max output tokens), and never silently switches models.
- The future live path saves only minimal metadata and reported usage to a new, locally ignored `output/provider_compat_<role>.json` file, refuses to overwrite an earlier result, and redacts provider exception contents. A text-only generator response is recorded as missing tool-call evidence, not a successful tool integration. A Terra schema-valid result does not imply a correct judge.
- `tests/test_provider_compat_probe_offline.py` mocks all four roles and verifies pure offline previews, strict authorization, sanitized errors, no retries, non-overwrite behavior, metadata records, and the synthetic image/schema.
- Documentation: README and `docs/Session-009-Compatibility-Probes.md`. Official `validator/solution.py` and Modal-based `workflow/generate.py` remain unchanged.

**Codespace offline verification (2026-11-07, user-supplied terminal log):**

- Fresh checkout of remote `feature/session-009-provider-compatibility` succeeded and was clean/synchronized.
- `uv sync --locked`: resolved 111 packages, rebuilt/reinstalled local `hw2-validator`.
- `uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v`: **34/34 passed** (27 prior adapter tests + 7 new compatibility-probe tests).
- All four `uv run python scripts/provider_compat_probe.py --role ...` offline previews passed: `agent_a` -> `deepseek-flash`, `agent_b` -> `gpt-5.6-luna`, `agent_c` -> `glm-4.7-flash`, `experimental_judge` -> `gpt-6.1-terra`. All reported `network_requests=0`, correct API styles; three roles had inert `run_shell` descriptors, Terra had `structured_judgment=true` and no tools.
- Existing validator tests: **49/49 passed**. Expected CLI usage diagnostics occurred in an intentionally rejected malformed-consent test and did not indicate a failure.
- Offline dataset preflight: **PASSED** with 110 runs, 98 PNG figures, 110 human-labeled runs, 16 acceptable, 12 execution_failure, 39 hard_to_read, 71 wrong_chart, 25 wrong_data.
- Final `git status --short --branch`: clean `feature/session-009-provider-compatibility...origin/feature/session-009-provider-compatibility`. **83/83 offline unit tests passed.** No model/provider calls, no cloud infrastructure invoked.

**Still not verified or performed:** any live API request, four-model account access, real tool/function-call responses, actual Terra structured JSON on a live synthetic image, chart-generation agent loop, or MCC. Mock test success does not confirm model/API compatibility or semantic correctness.

**First approved live compatibility request (DeepSeek, Agent A, 2026-11-07, user-supplied Codespace output):**

- User explicitly approved **exactly one** potentially billed `deepseek-flash` request with no retry and no tool execution. After pulling `ea0b182`, verified clean/synchronized Git, and confirmed `DEEPSEEK_API_KEY` was configured (without exposing it), user executed `uv run python scripts/provider_compat_probe.py --role agent_a --live --confirm-one-request --approve-model deepseek-flash` exactly once.
- The request **completed**. Provider: DeepSeek; requested model: `deepseek-flash`; reported model: `deepseek-flash`; interface: Responses. It returned **one** inert `run_shell` function call; `expected_tool_called=true`, `tool_call_compatibility=true`. No model-proposed commands were executed; retries=0.
- Usage reported by provider: **346 input tokens, 59 output tokens, 405 total tokens**. Actual monetary charge was not independently verified. No fallback or additional API request occurred.
- Saved local ignored result: `output/provider_compat_agent_a.json` (contents supplied by user match CLI output). Final `git status --short --branch` remained clean and synchronized; the committed files were unchanged before this documentation update.
- **Interpretation:** DeepSeek's live endpoint supports this exact one-turn function-call request and our parser accepts its response. This is not an end-to-end plotting agent, Docker/shell execution test, data-visualization quality evaluation, Terra judge inference or MCC benchmark.

**Second approved live compatibility request (OpenAI Luna, Agent B, 2026-11-07 America/Vancouver, user Codespace transcript):**

- Following the successful DeepSeek probe and its journal commits, user explicitly authorized **exactly one** potentially billed OpenAI `gpt-5.6-luna` compatibility request, without retries or tool execution. They verified the feature branch remained clean/synchronized and checked that `OPENAI_API_KEY` was configured without revealing it.
- User executed `uv run python scripts/provider_compat_probe.py --role agent_b --live --confirm-one-request --approve-model gpt-5.6-luna` **exactly once**. The real OpenAI Responses API request completed. Requested model: `gpt-5.6-luna`; reported model: `gpt-5.6-luna`; one inert `run_shell` function call was returned and correctly parsed (`expected_tool_called=true`, `tool_call_compatibility=true`).
- Reported usage: **94 input tokens, 33 output tokens, 127 total tokens**; retries=0; proposed commands executed=0; `official_qwen_equivalent=false`. Actual monetary charge was not independently verified.
- Ignored local record: `output/provider_compat_agent_b.json`, which user read back and verified matched the CLI's result. Final Git status was clean/synchronized before the documentation commit.
- **Interpretation:** Both DeepSeek Agent A and OpenAI Luna Agent B have now passed one-turn live function-call compatibility checks. Neither was a chart-generation agent run; Docker/shell behavior, plotting quality, and Terra judgment remain untested. No Z.ai or Terra calls have been made in Session 009.

**Third approved live compatibility request (Z.ai GLM, Agent C, 2026-11-07 America/Vancouver, user Codespace transcript):**

- User explicitly authorized **one** potentially billed Z.ai `glm-4.7-flash` request with no retries and no tool execution. The user pulled the then-current branch (already up to date), verified clean/synchronized Git, and checked `ZAI_API_KEY` existed without revealing it.
- Executed **once**: `uv run python scripts/provider_compat_probe.py --role agent_c --live --confirm-one-request --approve-model glm-4.7-flash`. This produced **`status=failed`, `error_type=RateLimitError`**, and the message `Compatibility probe failed. Do not retry without new approval.` No automatic retries occurred (`retries=0`).
- Saved safely redacted local result `output/provider_compat_agent_c.json` (user supplied matching output); it records that a failed request **may have been billed**. No response/model-ID/usage/tool call was returned; `glm-4.7-flash` Chat Completions **live compatibility remains unverified**, not disproven. We do not know the underlying Z.ai business error code from the intentionally minimal exception record.
- Final `git status --short --branch`: clean/synchronized feature branch. The one Z.ai approval has been **consumed**. No further live requests, fallback models, or retries are authorized.
- **Next diagnosis without model calls:** inspect Z.ai account dashboard for key type/billing plan, available balance or credits, quota, concurrency/rate-limit counters, and recent failed-request logs; distinguish account quota/access failure from temporary throttling if the dashboard exposes a safe numeric business error code. Never paste API keys, bearer tokens or full provider errors containing sensitive account metadata. Any follow-up GLM request needs fresh user consent.
- **Current status:** Agent A DeepSeek one-turn function call passed; Agent B Luna one-turn function call passed; Agent C GLM blocked with `RateLimitError`; experimental Terra judge has not been called.

**Session 009 follow-up — Agent C paid-model replacement decision (2026-11-07, America/Vancouver):**

- User asked: **switch from the free Z.ai model to `glm-5.3-flash` and test**. We interpret the change as a newly configured model, not a retry of the failed `glm-4.7-flash` probe; the earlier attempt's `RateLimitError` and its ignored `output/provider_compat_agent_c.json` must remain unchanged.
- Agent C's current configured model is now `glm-5.3-flash` (Chat Completions, standard `https://api.z.ai/api/paas/v4`, `ZAI_API_KEY`). The prior code/tests `glm-4.7-flash` are now historical. Other roles unchanged.
- GLM-5.3-Flash defaults to substantial mandatory reasoning; we send `reasoning_effort=low` using the OpenAI SDK's `extra_body` for a bounded 512-output-token one-turn tool-call probe. This is deliberately **not a benchmark of default model quality**.
- The compatibility CLI now saves model-scoped results such as `output/provider_compat_agent_c_glm-5.3-flash.json`, preserving the earlier role-only `output/provider_compat_agent_c.json`. It refuses a repeated model test if either a new model-scoped file or an old same-model legacy record already exists; malformed legacy files also block conservatively.
- Updated mocked unit tests pin `glm-5.3-flash` and verify correct Z.ai request, low reasoning effort, no network by default, preservation of `glm-4.7-flash` failure record, and rejection of same-model attempts. Existing official model settings, runner, judge, labels and pinned Docker dependency are untouched.
- Public model documentation and model-card material establish `glm-5.3-flash` as an API/model identifier, not the user's account entitlement. A previous rate-limit failure might affect the new model if caused by a shared account quota or insufficient balance.
- **Current state:** Source changes and documentation pushed to the Session 009 feature branch; **Codespace offline tests and a GLM-5.3-Flash live API call have not yet been performed or verified**. Per-request user approval remains mandatory before any possibly billed model request; no automatic retry, fallback or shell execution.

**GLM-5.3-Flash migration verification completed in Codespaces (2026-11-07 America/Vancouver; user-supplied terminal log):**

- `git pull --ff-only`: fast-forwarded Session 009 from `092c35c` to `957a9bc` with nine changed files. Working tree clean and tracking `origin/feature/session-009-provider-compatibility`.
- `uv run python -m unittest discover -s tests -p 'test_provider_*_offline.py' -v`: **37/37 passed**, including the three new tests for old-record preservation, duplicate legacy model rejection, and invalid legacy-result blocking.
- `uv run python scripts/provider_compat_probe.py --role agent_c`: offline preview requested **`glm-5.3-flash`**, provider `zai`, API style `chat_completions`, `max_output_tokens=512`, inert `run_shell`, `network_requests=0`, `live_approval_required=true`.
- `uv run python scripts/provider_preflight.py`: four registered roles, each with `network_requests=0`; Agent C now `glm-5.3-flash`; Terra remains strict structured judge in registry.
- Existing validator tests: **49/49 passed**. Expected argparse errors while testing incomplete live-consent flags did not indicate a failing test. Total **86/86 offline unit tests passed**.
- Final `git status --short --branch`: clean/synchronized. No additional API call, model output, shell execution, or cloud infrastructure invoked during these checks.

**Agent C paid-model live probe — GLM-5.3-Flash success (2026-11-07 America/Vancouver, user Codespace transcript):**

- User **separately and explicitly approved one** potentially billed `glm-5.3-flash` Chat Completions compatibility request with `reasoning_effort=low`, maximum 512 output tokens, 60-second timeout, no retries and no execution of model-proposed tools.
- Before testing, user confirmed the Session 009 branch was clean and synchronized (`git pull --ff-only` said already up to date), and `ZAI_API_KEY` was configured (without displaying it).
- User executed **once**: `uv run python scripts/provider_compat_probe.py --role agent_c --live --confirm-one-request --approve-model glm-5.3-flash`. The request **completed**. Requested model = reported model = `glm-5.3-flash`. API style: `chat_completions`. Exactly **one** inert `run_shell` tool call was returned, and the adapter reported `expected_tool_called=true` and `tool_call_compatibility=true`.
- Provider-reported usage: **212 input tokens, 15 output tokens, 227 total tokens**; `retries=0`, `model_proposed_commands_executed=0`. Monetary charge is not independently verified.
- Saved ignored result to `output/provider_compat_agent_c_glm-5.3-flash.json`. User also read the older `output/provider_compat_agent_c.json`, which **still contains the failed `glm-4.7-flash` `RateLimitError` record** with zero retries; neither was overwritten. Git status remained clean/synchronized.
- **Interpretation:** All three **current** generator roles now pass a one-request live tool-call compatibility smoke test: DeepSeek Flash, OpenAI GPT-5.6 Luna and Z.ai GLM-5.3 Flash. This demonstrates that the configured endpoints accept the synthetic request and the adapters parse one inert function call; **not** actual code/shell execution, multi-turn agent operations, plotting quality or benchmark equivalence. The earlier `glm-4.7-flash` failure remains unexplained; a successful new-model request does not prove the prior rate error was model-specific.
- The authorization for the GLM-5.3-Flash request has been **consumed**. Never retry it without fresh authorization. No live Terra judgment has yet been performed in this session.

**Fourth approved live compatibility request — OpenAI Terra synthetic PNG and strict JSON (2026-11-07 America/Vancouver, user-supplied Codespace transcript):**

- User separately and explicitly authorized **exactly one potentially billed `gpt-6.1-terra` request**, with no retries and no tool execution. They verified `OPENAI_API_KEY` was configured without printing it and that the Session 009 feature branch was clean and synchronized.
- User invoked **once**: `uv run python scripts/provider_compat_probe.py --role experimental_judge --live --confirm-one-request --approve-model gpt-6.1-terra`.
- The OpenAI Responses API request **completed**. Requested model and reported model: `gpt-6.1-terra`. Input was the local synthetic bar-chart PNG and synthetic task description; strict local JSON parsing reported `schema_valid=true`. The parsed `judgment_families=[]` indicates no error families were returned for this synthetic case. `accuracy_evaluated=false`.
- Provider-reported usage: **215 input tokens, 73 output tokens, 288 total tokens**. Tool calls=0; SDK retries=0; model-proposed shell commands executed=0; `official_qwen_equivalent=false`. Monetary charge is not independently verified.
- Ignored output `output/provider_compat_experimental_judge_gpt-6.1-terra.json` was read back and matched the CLI result. Final `git status --short --branch` remained clean and tracking the feature branch.
- **Interpretation:** Terra's API accepts this synthetic PNG and its response validates against the existing strict error-family schema. This **does not** establish error-detection accuracy, confusion matrices, MCC, calibration, or equivalence to the course Qwen judge. The one-call Terra authorization has been fully consumed.

**Session 009 compatibility milestone conclusion (2026-11-07 America/Vancouver):**

- All **four current roles** passed exactly one separately authorized live compatibility probe: Agent A DeepSeek `deepseek-flash`, Agent B OpenAI `gpt-5.6-luna`, Agent C paid Z.ai `glm-5.3-flash`, and experimental OpenAI judge `gpt-6.1-terra`. The first three each returned a parsable inert `run_shell` function call; Terra returned structured JSON from synthetic PNG input.
- A **fifth, historical model attempt** using free `glm-4.7-flash` failed with `RateLimitError`, zero retries and no parseable model response. This remains preserved separately from the successful paid GLM-5.3 result; we do not claim to know the original rate-limit cause.
- Latest Codespace offline verification before the final live probes: **37/37 provider tests, 49/49 validator tests**, four zero-network previews; no code changed following this verification (documentation updates only). Model-reported usage and model-ID strings were logged; monetary charges were not independently verified.
- **Not implemented:** a multi-turn agent controller, any model-generated chart inside Docker, a real Terra `validate(run)` integration, a human-label accuracy experiment, MCC analysis, authored-task suite, or the official course model setup.

**Next:** Pull the documentation-only completion commits, run one final offline regression/preflight and review the Session 009 branch diff; open a **draft PR to `main`** and check CI before considering merge. No further paid API calls are required for Session 009 or authorized by earlier consents. Plan the bounded Docker chart-agent controller as a **new feature branch** after Session 009 is merged.

### Session 010 — 2026-11-07 (America/Vancouver) — Starting a bounded chart-agent controller

**Goal:** Begin transforming Session 009's verified one-turn API adapters into a real chart-making agent architecture, without immediately sending model requests or executing shell commands.

**Starting point and Git hygiene (user Codespace transcript):**

- User verified merged PR #9 on `main`, which was clean/synchronized at merge commit `65b0a49`. Then `git fetch origin --prune` confirmed the remote Session 009 feature branch had been deleted, and `git branch -d feature/session-009-provider-compatibility` safely removed the local merged branch.
- User ran `git switch -c feature/session-010-chart-agent-controller` from clean `main`, followed by `git push -u origin feature/session-010-chart-agent-controller`. The new branch now tracks its matching remote; no model calls occurred.
- Previous four-model live compatibility milestone remains closed; its five separately approved one-request API attempts have all been consumed. Session 010 requires independent fresh per-request approval for any new model call.

**Source interfaces inspected before implementation:**

- Assignment 2 `integrations.providers`: `NormalizedReply`, `ToolCall`, `make_tool_result`, `prepare_request`, and `execute_one`; `execute_one` remains separately gated and never runs model-proposed tools.
- Pinned Assignment 1 `agent_sandbox_runtime` at `0cb0534c2fffb67ddfff619100057fad0be90a3c`: `Sandbox(image, network="none", ports=(), deployment_timeout=..., runtime_timeout=..., cpus=..., memory=...)`; `execute(..., timeout=..., env=...)`; context-manager `stop()`; `DockerImage.add_local_file` supports image-build-time file injection. The pinned package warns Docker is not a hardened VM security boundary. A real Docker launch and safe figure extraction are not yet verified.
- The existing `workflow/generate.py` remains Modal-based and points to the original official models; we will not quietly replace it or report hosted-model results as official-equivalent.

**Changes committed in Session 010's first offline slice:**

1. New `integrations/chart_controller.py`: Pure `ChartController` state machine for the three generator roles, an inert `run_shell` descriptor, provider-specific request preparation, explicitly accepted normalized replies, pending tool-call tracking, and pure recording of externally obtained sandbox outputs. Default caps: 4 model turns, 6 tools, 2,000 command characters, 2,048-character stdout/stderr fields. Every call remains separately approved by a future host; the budgets never grant authorization.
2. New `tests/test_controller_state_offline.py` (renamed from initially committed `tests/test_controller_offline.py` following discovery failure): Mock-only tests for three-provider request shapes and Responses-vs-Chat continuation, no-transport preview, terminal replies, pending tools, command arguments and IDs, strict budgets, malformed outputs, and truncation.
3. Updated `.github/workflows/offline-ci.yml` to run the dedicated mock-only controller suite.
4. New `docs/Session-010-Controller-Design.md` explains the runtime boundary and unresolved task-file/PNG transport decisions. Updated README with the current first-slice scope.

**What we deliberately did not do:** call any provider, start Docker, execute model-proposed shell commands, stage task data in a container, retrieve a model-generated figure, test end-to-end chart correctness, change the existing judge, score human labels, or update the official Modal runner.

**First user Codespace results (2026-11-07 America/Vancouver; terminal transcript):** `git pull --ff-only` fast-forwarded from `65b0a49` to `43a24ac`. The initial controller command `uv run python -m unittest discover -s tests -p 'test_controller_*_offline.py' -v` printed **`Ran 0 tests` / `NO TESTS RAN`**. That is **not a passing controller verification**, despite the successful command exit. Provider suite **37/37 passed**, validator suite **49/49 passed**, and `provider_preflight.py` reported four zero-network previews. Git tree remained clean and synchronized.

**Cause of the zero-test discovery:** The new test file was named `tests/test_controller_offline.py`, but the discovery glob `test_controller_*_offline.py` requires an additional segment between `controller_` and `_offline.py`. This exposed an important CI safety gap: `unittest discover` can silently succeed when it finds no tests.

**Repair (subsequent commits, pending user verification):** Renamed the suite to `tests/test_controller_state_offline.py`; added `scripts/check_controller_offline.py` to count discovered tests and **fail when count == 0**; changed `.github/workflows/offline-ci.yml` to run that guarded entry point. Updated README and Session 010 design notes. **No new model calls, Docker processes or command executions** occurred as part of the repair. The 11 controller test cases must still be actually executed to claim success.

**Verified controller test discovery repair (2026-11-07 America/Vancouver, user Codespace transcript):** User fast-forwarded the Session 010 branch from `43a24ac` to `e828672` and ran `uv run python scripts/check_controller_offline.py`. The guard reported **`Controller test discovery: 11 test(s)`**, and **all 11/11 tests passed** in 0.004 s. Git status remained clean and synchronized. This validates the state-machine unit tests, including three-provider replay, tool-result pending state, budgets, command argument rejection and truncation. Provider **37/37**, validator **49/49** and offline registry preflight passed in the immediately preceding Codespace run; those suites were not rerun in this specific repair command.

**Second offline implementation slice — gated Docker gateway (code committed; tests pending, 2026-11-07 America/Vancouver):**

- Inspected the pinned Assignment 1 runtime's actual `Sandbox` constructor and `execute`/stop APIs. Unlike the controller, the `Sandbox` constructor **immediately launches Docker**, so a production gateway must avoid instantiating it until a distinct human launch authorization is supplied.
- Added `integrations/sandbox_gateway.py`: `SandboxGateway` has pure prelaunch metadata, a one-time `launch(confirm_launch=True, approve_image="python:3.12-slim")` gate, explicit `network="none"`, `ports=()`, no host mounts or secret environment forwarding, default 120-second lifetime, 15-second per-command timeout, 1 CPU, 512 MB memory, six attempted commands, 2,000 maximum command characters and 2,048 replayed characters per output stream.
- Every future command must first pass `propose_command(command)` to expose its exact bytes and a step-specific SHA-256 fingerprint for **independent user review**. Only `execute_approved(confirm_one_command=True, approve_sha256=...)` can hand the already-reviewed command to the sandbox. Fingerprints/flags are **not evidence of actual human consent**; the caller is responsible for collecting it. Failed attempts count against the budget, with no automatic retry. `close()`/context manager stops the sandbox even on errors.
- Added **14 mock-only tests** under `tests/test_sandbox_gateway_offline.py`, covering non-launching previews, denied/wrong-image launches, fixed Docker policy options, blocked/unapproved commands, approval tokens, invalid/NUL commands, budgets, bounded outputs, no credential forwarding, no automatic retry, exception paths, and cleanup. A new `scripts/check_sandbox_gateway_offline.py` runner fails on zero discovered tests.
- Updated the offline GitHub Actions workflow to include the new fake-Docker tests, plus README and `docs/Session-010-Controller-Design.md`. The preexisting controller suite remains verified **11/11**; newly added gateway tests **have not yet run in Codespaces**.
- **Scope limitations:** No real Docker image pull/launch, shell execution, model request or chart artifact extraction occurred. The first image `python:3.12-slim` is **not digest-pinned and not chart-capable**. Docker containers are **not hardened VM boundaries**; a network-disabled runtime still requires a separate trusted execution decision. Future stages must design safe task input staging and PNG readback.

**Second-slice verification (2026-11-07 America/Vancouver, user Codespace transcript):** User ran `git pull --ff-only`, fast-forwarding the Session 010 feature branch from `e828672` to `353fcad`. `uv run python scripts/check_controller_offline.py` discovered **11 tests; 11/11 passed**. `uv run python scripts/check_sandbox_gateway_offline.py` discovered **14 tests; 14/14 passed**. **25/25 current Session 010 tests passed**, all with fake Docker and no model or real container execution. Final `git status --short --branch` was clean and synchronized. This verifies mocked launch policy, command approval checks, resource budgets, truncation, and cleanup, **not** a production-strength container isolation guarantee or real chart creation.

**Third offline slice implemented — task CSV and PNG artifact validation (code committed, tests pending):**

- Added `integrations/task_artifacts.py`: `snapshot_task_csvs(descriptor)` reads only small **task-local UTF-8 CSVs** (1–8 files; each ≤64 KiB, ≤256 KiB in total, 128 KiB maximum task descriptor). It refuses symlinked task descriptor paths, symlinked inputs, non-CSV names, NUL bytes, and oversized inputs. It creates an immutable byte snapshot and manifest containing intended `/opt/assignment/inputs/<name>` destination, byte count and SHA-256 — **not** raw CSV contents. The implementation does not build/copy into a container.
- Added strict in-memory `validate_figure_png`: exact PNG signature, ≤2 MiB file, ≤4 million pixels, complete terminal IEND with no trailing bytes, Pillow structure and pixel decode. It returns a validated byte artifact and safe metadata without writing a host file.
- Added `decode_figure_envelope` for a future *trusted* extraction helper's JSON response: exact `figure.png` path, base64 encoding, byte length, SHA-256, data; strict field set, size/hash/encoding checks, then image validation. This does **not** accept raw model-authored file contents as trustworthy, does not invoke Docker, and does not extract files itself.
- New `tests/test_task_artifacts_offline.py` contains **16** synthetic temporary-file unit tests for safe CSV snapshots and manifest privacy, path and file-size constraints, symlink and descriptor checks, good/bad PNG, truncation, appended payloads, pixel limits, and JSON/base64 envelope errors. New `scripts/check_task_artifacts_offline.py` refuses empty test discovery; GitHub Actions runs it.
- Updated `docs/Session-010-Controller-Design.md` and README. **There are no new Codespace test results for these 16 cases yet**. The previous verified Session 010 suites remain **11/11 controller plus 14/14 mock-gateway passed**, and the preceding provider/validator regression checks remain **37/37 and 49/49**.

**Third-slice Codespace verification (2026-11-07 America/Vancouver, user terminal transcript):** User pulled the feature branch from `353fcad` to `cf78030`, then ran the three guarded offline test scripts. Artifact suite discovered **16 cases; 16/16 passed** (0.188s); controller suite discovered **11 cases; 11/11 passed** (0.004s); fake-Docker gateway suite discovered **14 cases; 14/14 passed** (0.007s). Total **41/41 Session 010 tests passed**. Final `git status --short --branch` was clean and synchronized. Existing provider 37/37 and validator 49/49 checks passed in earlier Codespace runs but were **not rerun** in this specific verification. No paid API request or Docker container was launched.

**Fourth offline slice — private CSV staging and fixed PNG extractor protocol (committed; tests not yet run in Codespaces):**

- Inspected pinned Assignment 1 `DockerImage.add_local_file(source, destination)` and `Sandbox.execute` APIs. The former ultimately performs Docker image builds; the latter captures command output as text and our existing gateway deliberately truncates it. We must not mistake a 2,048-character tool-output channel for a binary PNG transfer mechanism.
- Added `integrations/chart_transfer.py`: `stage_input_snapshots` *revalidates* task ID, CSV filename uniqueness/safety, byte caps, UTF-8 encoding and SHA-256 of all input snapshots, then temporarily writes only those bytes to private host files (0600), with a private staging directory (0700). It verifies written checksums, exposes intended `/opt/assignment/inputs/*.csv` destinations to a trusted future image builder, and cleans up automatically on context exit. The printable `InputStagingPlan.manifest()` includes only counts, destinations, byte sizes and digests; not raw CSV data or temporary host paths. **Unlike the previous pure artifact boundary, this staging step creates temporary local files when called**, but does not build/pull images or start Docker.
- Added `scripts/figure_extract_worker.py`: fixed, standard-library-only extractor designed for the eventual chart image at `/opt/assignment/extract_figure.py`. Production path is hardcoded to `/workspace/figure.png`, with **no CLI path override**. Requires a regular file, rejects final symlinks (where `O_NOFOLLOW` is available), enforces a ≤2 MiB bounded read, checks a PNG signature and emits one canonical base64/length/SHA-256 JSON envelope for full host validation by `decode_figure_envelope`. No real container or `/workspace/figure.png` has been accessed yet.
- Added `preview_figure_extraction()`: prints metadata for a fixed `python /opt/assignment/extract_figure.py` argv with `shell=False`, and declares that a future independent sandbox approval is required. No commands are executed.
- Added `tests/test_chart_transfer_offline.py` with **12** local synthetic cases for private file permissions and deletion, input integrity/limits, denied path/duplicate/digest cases, immutable extractor argv, successful PNG envelope roundtrip, and unsafe figure-file handling. The tests call only the helper's local read function with temporary paths, not Docker. Added `scripts/check_chart_transfer_offline.py` with zero-discovery refusal; CI now runs it.
- Updated the README and `docs/Session-010-Controller-Design.md` with verified 41-test results and the new pending transfer tests. **No new API or Docker authorization was supplied or used.**

**Fourth-slice verification (2026-11-07 America/Vancouver, user Codespace transcript):** User pulled `feature/session-010-chart-agent-controller` to `f81f4d1`; all four guarded suites passed: **12/12 chart transfer**, **16/16 task artifacts**, **11/11 controller**, **14/14 fake gateway**. **53/53 total Session 010 tests passed**. The output explicitly shows each count and `OK`, with a clean and synchronized feature branch afterward. The tests only read/write synthetic temporary files and fake sandbox objects; no model APIs or Docker were used. Earlier provider/validator suites were not rerun in this specific user transcript.

**Fifth offline slice implemented — reviewable image recipe, no Docker build (tests pending):**

- Added `integrations/chart_image_recipe.py` with a side-effect-free `plan_chart_image(base_image)` that refuses mutable base tags and accepts only the syntax `python:3.12-slim@sha256:<64 lowercase hex>`. **No actual digest has been selected or verified**, and a digest-shaped string is not proof of a real or trusted image.
- Dockerfile text requests the chart libraries already pinned in `pyproject.toml`: Matplotlib 3.10.5, NumPy 2.3.2, Pandas 2.3.1 and Pillow 12.3.0. It requests headless rendering, a private writable `/workspace`, and unprivileged user `10001:10001`. Only two specific build context paths are planned: `inputs/` (CSV input staging) and `trusted/extract_figure.py` (reviewed helper), copied into `/opt/assignment` with read-only permissions. These are *expected future build-context files*; the module does not create or copy them.
- Supply-chain gaps are explicit in `ChartImageRecipe.preview()`: base image existence/trust/architecture and transitive wheel hashes are **not verified**; `docker_build_authorized=false`, and Docker builds, launches and model requests are all zero. Direct package version pins do **not** constitute a fully reproducible dependency lock.
- Added **11 synthetic offline tests** under `tests/test_chart_image_recipe_offline.py` for digest syntax/injection rejection, exact version pins, non-root workspace, narrow COPY sources, read-only task files, no secrets/ports/mounts, deterministic digests, honest manifest flags and no Docker/subprocess execution. The test fixture uses a deliberately **fake base digest**, not a deployable image.
- Added `scripts/check_chart_image_recipe_offline.py` with a nonzero-discovery guard and updated `.github/workflows/offline-ci.yml`, README and `docs/Session-010-Controller-Design.md`. **No Codespace verification of these 11 new tests yet**. No new authorization was requested or used.

**Fifth-slice verification (2026-11-07 America/Vancouver, user Codespace terminal transcript):** User pulled the feature branch from `f81f4d1` to `f0818ba` and ran all five guarded offline tests: **11/11 chart image recipe**, **12/12 chart transfer**, **16/16 task artifacts**, **11/11 controller**, and **14/14 fake-Docker gateway**. **All 64/64 Session 010 tests passed**; Git remained clean and tracking the feature branch. The image recipe's successful test validates *text and policy checks only*; it does not establish that the sample fake digest is real, trusted, architecture-matched, or that packages/install/build succeed. Provider and validator suites (previously 37/37 and 49/49) were not rerun in this specific transcript. No new model API calls or Docker operations occurred.

**Sixth offline implementation slice — minimal build context (code committed; tests pending):**

- Added `integrations/chart_build_context.py`: `prepare_chart_build_context(snapshot, base_image)` accepts only the previously validated digest-formatted base reference, revalidates all existing CSV snapshots through `stage_input_snapshots`, and produces a **private temporary host-side** directory containing **only** `Dockerfile`, `inputs/<approved-name>.csv` and the reviewed source `scripts/figure_extract_worker.py` staged as `trusted/extract_figure.py`. Directories have mode 0700; files have mode 0600. No host checkout, credential files or arbitrary model-provided paths are copied.
- `verify_chart_build_context` compares the exact allowlist and expected directory set, rejects symlinks/unexpected entries/non-private modes, checks bounded content sizes and SHA-256 for every file, and checks exact equality with the immutable-in-memory Dockerfile recipe. Printable manifests contain only relative names, sizes, hashes and policy flags; ephemeral absolute paths and CSV contents are excluded. The context manager removes the temporary tree on normal exit or exceptions.
- Added **13** tests in `tests/test_chart_build_context_offline.py`: private directory/file modes, all allowed files, fixed helper bytes and recipe, multi-CSV hashes, cleanup after exception, rejection of mutable base references and forged snapshots, tamper detection, exclusion of extra `.env`, `.git` and source files, symlink/mode rejection, forged huge manifests, invalid parent directories, and proof that no subprocess/Docker client is invoked.
- Added `scripts/check_chart_build_context_offline.py` with a fail-on-zero test count; updated GitHub Actions, README and `docs/Session-010-Controller-Design.md`. The new tests use fake digest strings and ephemeral synthetic files only. **They have not yet run in the user's Codespace.**
- **Execution safety:** This slice writes synthetic data to private temporary host files in tests, but does **not** call DockerImage, `Sandbox`, Docker CLI, shell executors, or a model. A digest-shaped string does not verify actual image existence/trust, platform or package wheel hashes, and passing tests cannot authorize a real Docker build.

**Sixth-slice verification (2026-11-07 America/Vancouver, user Codespace transcript):** User fast-forwarded the feature branch from `f0818ba` to `5eb498f`, then ran the six non-empty offline test runners. Results: minimal build context **13/13 passed**, image recipe **11/11**, chart transfer **12/12**, task artifact **16/16**, controller **11/11**, fake-Docker gateway **14/14**. **77/77 Session 010 offline tests passed**; Git working tree was clean and tracking the remote. Provider 37/37 and validator 49/49 were previously verified but were *not rerun* in this transcript. A passing build-context test demonstrates synthetic private-file integrity, **not** a real Docker build, supply-chain assurance or confinement of arbitrary generated code.

**Supply-chain inspection (public Docker Hub and existing committed lockfile, no runtime execution):** The official `python:3.12-slim` tag is **multi-platform and mutable** and has recent pushes. We must not select a digest from a cached web snippet without checking the current manifest index and target platform. The existing pinned `uv.lock` records exact versions and per-wheel SHA-256 metadata for project dependencies including Matplotlib 3.10.5, NumPy 2.3.2, Pandas 2.3.1 and Pillow 12.3.0. However, the **chart Dockerfile uses a separate pip command with direct version pins, not the complete uv lock**, so it currently does **not** enforce transitive wheel hashes or a platform-specific chart-only dependency graph. Neither OCI digest authenticity nor reproducibility has been established for the image.

**Registry/architecture inspection verified (2026-11-07 America/Vancouver, user Codespace transcript):** User pulled the feature branch from `5eb498f` to `79b63b3`; `uname -m` printed **`x86_64`**. `docker buildx imagetools inspect docker.io/library/python:3.12-slim` completed and reported OCI index `sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54`, its **matching `linux/amd64` Python manifest** `sha256:05a994d2344eb364cc186910f4fc8786a38215f39f00d0acc25bff33a08f4177`, version `3.12.16-slim-trixie`, and an unrelated underlying Debian `debian:trixie-slim` digest annotation `sha256:7378260c0a098d27ac206225db5e7d92b8c7c84ea7afccc86eeb513756bbd392`. No image layers were pulled, built or run. Git working tree remained clean/tracking origin. This is **real registry metadata evidence**, but not a successful layer download, signature/attestation validation, chart library install or test.

**Chart-only wheel lock derived from committed `uv.lock` (code committed; audit unverified):**

- Inspected committed `uv.lock` (Git blob `546d4d0839cc287c1b29b7c8b74ea4582737964a`) for the four exact chart roots: Matplotlib 3.10.5, NumPy 2.3.2, Pandas 2.3.1, Pillow 12.3.0. The recorded **unconditional transitive closure is 14 packages**: those four plus contourpy, cycler, fonttools, kiwisolver, packaging, pyparsing, python-dateutil, pytz, six and tzdata. Chose one existing Linux x86-64 CPython 3.12 wheel SHA-256 from each lockfile package, using a universal wheel when no CPython-specific wheel was needed.
- Committed `requirements/chart-cp312-linux-amd64.txt` with all 14 pinned versions, their selected wheel hashes and explanatory wheel filenames. This file contains *hash metadata*, **not** downloaded bytes or evidence of installability.
- Committed `scripts/check_chart_wheel_lock_offline.py` to re-derive the closure from the actual `uv.lock`, reject ambiguous dependency markers, check the wheel target/platform syntax, compare every exact package/version/hash, and refuse missing/extra dependencies. The audit calls no Docker, pip, provider API, or network. Added it to `.github/workflows/offline-ci.yml`.
- New `docs/Session-010-Supply-Chain.md` records full registry digests, architecture, version, source lockfile and unverified prerequisites. README and `docs/Session-010-Controller-Design.md` were updated.
- **Important:** The Dockerfile still uses four direct version pins with regular pip (without `--require-hashes`), and the minimal build context does not include the new requirements file. The default gateway image also remains the floating non-chart-capable transport-test image. **No image recipe, build context, sandbox runtime, or agent execution path was silently modified.**

**Next:** User pulls the latest feature commits and runs `uv run python scripts/check_chart_wheel_lock_offline.py` with `git status --short --branch`. Expected audit: 14 packages (4 direct, 10 transitive); **do not claim pass until actual output confirms it**. After audit verification, review a narrow integration of the hashed requirements into the Dockerfile and build context, then separately seek authorization for any real Docker image build or model API call.

### Template for future sessions

Copy this entire section to the bottom for each new session. Do not backfill invented results.

~~~markdown
### Session NNN — YYYY-MM-DD — Short descriptive title

**Goal:** What question or milestone are we working on?

**Starting point:** Branch, commit SHA, environment, model/endpoint and prerequisites.

**Plan / hypothesis:** What do we expect to learn or demonstrate?

**Changes made:** Paths touched, commits/PRs and why the design changed.

**Commands executed and results:**
| Command (or link to log) | Result (pass/fail/blocked/not run) | Output or artifact |
| --- | --- | --- |
| ... | ... | ... |

**Measurements:** Dataset size, per-family support, confusion counts, MCCs,
macro-MCC, model IDs, versions, costs/timeouts, and reproducibility details.
Write N/A if this was not an evaluation session.

**Failures and debugging:** Exact error messages, reproduction steps,
suspected causes, fixes tried and remaining uncertainty.

**What we learned:** Concepts, architecture, tradeoffs, and what contradicted
our original hypothesis.

**Decisions:** Chosen approach, rejected alternatives and reasons.

**Next session:** Specific reproducible starting command and success criteria.
~~~

## Appendix — complete tracked-file tree

**Snapshot method:** GitHub recursive tree of `main` at `4c28fd2bc0ee2499b7c632efbabbbb2c066c0ae8`, plus this newly created `docs/Learning-Progress.md` in the documentation branch. This section lists **every tracked file**, not ignored files, untracked local files or empty runtime folders. Pre-existing tracked count: **300**; with the journal: **301**. A missing figure is intentionally absent from the tree; it has not been fabricated. Grouped descriptions above explain repetitive artifact files by role.

<details>
<summary>Expand the full 301-file tree</summary>

~~~text
cmu-11-768-assignment-2/
├── .devcontainer/
│   ├── devcontainer.json
│   └── post-create.sh
├── .github/
│   └── workflows/
│       └── offline-ci.yml
├── artifacts/
│   ├── 001/
│   │   └── result.json
│   ├── 004/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 008/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 009/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 010/
│   │   └── result.json
│   ├── 013/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 016/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 021/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 022/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 023/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 025/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 026/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 028/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 029/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 030/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 031/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 034/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 038/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 039/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 046/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 047/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 050/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 051/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 052/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 053/
│   │   └── result.json
│   ├── 055/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 059/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 060/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 062/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 065/
│   │   └── result.json
│   ├── 068/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 069/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 070/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 074/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 075/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 077/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 079/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 080/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 081/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 082/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 083/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 086/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 087/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 089/
│   │   └── result.json
│   ├── 090/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 091/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 096/
│   │   └── result.json
│   ├── 097/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 098/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 099/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 103/
│   │   └── result.json
│   ├── 104/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 105/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 106/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 108/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 111/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 112/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 115/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 117/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 124/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 125/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 126/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 128/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 129/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 130/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 131/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 135/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 136/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 141/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 142/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 143/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 145/
│   │   └── result.json
│   ├── 146/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 150/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 153/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 155/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 156/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 161/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 163/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 164/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 165/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 166/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 167/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 168/
│   │   └── result.json
│   ├── 169/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 170/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 171/
│   │   └── result.json
│   ├── 173/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 175/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 177/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 180/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 181/
│   │   └── result.json
│   ├── 183/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 191/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 195/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 196/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 199/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 200/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 202/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 203/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 204/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 205/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 206/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 208/
│   │   └── result.json
│   ├── 209/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 210/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 212/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 213/
│   │   ├── figure.png
│   │   └── result.json
│   ├── 214/
│   │   ├── figure.png
│   │   └── result.json
│   └── 216/
│       ├── figure.png
│       └── result.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── Learning-Progress.md
│   ├── PHASE-0.md
│   └── UPSTREAM.md
├── harbor/
│   ├── example/
│   │   ├── environment/
│   │   │   ├── Dockerfile
│   │   │   └── harvest_log.csv
│   │   ├── mutants/
│   │   │   ├── forgery/
│   │   │   │   └── solve.sh
│   │   │   ├── hardcoded/
│   │   │   │   └── solve.sh
│   │   │   ├── illegible/
│   │   │   │   └── solve.sh
│   │   │   └── sum_crates/
│   │   │       └── solve.sh
│   │   ├── solution/
│   │   │   └── solve.sh
│   │   ├── tests/
│   │   │   ├── figure_manifest.py
│   │   │   ├── sitecustomize.py
│   │   │   ├── test_state.py
│   │   │   └── test.sh
│   │   ├── instruction.md
│   │   ├── README.md
│   │   └── task.toml
│   ├── reference/
│   │   └── README.md
│   ├── template/
│   │   ├── environment/
│   │   │   └── Dockerfile
│   │   ├── solution/
│   │   │   └── solve.sh
│   │   ├── tests/
│   │   │   ├── test_state.py
│   │   │   └── test.sh
│   │   ├── instruction.md
│   │   └── task.toml
│   ├── .gitignore
│   ├── preflight.py
│   ├── README.md
│   └── TROUBLESHOOTING.md
├── infrastructure/
│   ├── agent_runner.py
│   ├── configure_generation.py
│   ├── generation_gateway.py
│   ├── generation_models.py
│   ├── README.md
│   ├── serving.py
│   └── validator_model.py
├── inputs/
│   ├── 008/
│   │   └── data.csv
│   ├── 016/
│   │   └── data.csv
│   ├── 025/
│   │   └── data.csv
│   ├── 026/
│   │   └── data.csv
│   ├── 028/
│   │   └── data.csv
│   ├── 038/
│   │   └── data.csv
│   ├── 069/
│   │   └── data.csv
│   ├── 080/
│   │   └── checkouts.csv
│   ├── 125/
│   │   └── checkouts.csv
│   ├── 129/
│   │   └── data.csv
│   ├── 130/
│   │   └── data.csv
│   ├── 168/
│   │   └── data.csv
│   ├── 183/
│   │   └── data.csv
│   ├── 191/
│   │   └── data.csv
│   ├── 195/
│   │   └── data.csv
│   ├── 208/
│   │   └── data.csv
│   ├── 212/
│   │   └── data.csv
│   ├── 213/
│   │   └── data.csv
│   └── 214/
│       └── data.csv
├── output/
│   └── .gitkeep
├── runs/
│   └── .gitkeep
├── scripts/
│   ├── __init__.py
│   ├── deploy_agent_runner.sh
│   ├── deploy_generation_models.sh
│   ├── deploy_validator_model.sh
│   └── offline_preflight.py
├── tasks/
│   └── .gitkeep
├── tests/
│   └── test_offline_preflight.py
├── validator/
│   ├── __init__.py
│   ├── baseline.py
│   ├── model.py
│   ├── prediction.py
│   ├── runner.py
│   └── solution.py
├── workflow/
│   ├── __init__.py
│   ├── __main__.py
│   ├── evaluate.py
│   ├── generate.py
│   ├── harbor_rewards.py
│   ├── package.py
│   ├── submission.py
│   └── tasks.py
├── .env.example
├── .env.local.example
├── .gitattributes
├── .gitignore
├── .python-version
├── ASSIGNMENT.md
├── labels.example.json
├── pyproject.toml
├── README.md
├── report_template.tex
├── seed_labels.json
└── uv.lock
~~~

</details>

### Public seed run IDs

`artifacts/001/`, `artifacts/004/`, `artifacts/008/`, `artifacts/009/`, `artifacts/010/`, `artifacts/013/`, `artifacts/016/`, `artifacts/021/`, `artifacts/022/`, `artifacts/023/`, `artifacts/025/`, `artifacts/026/`, `artifacts/028/`, `artifacts/029/`, `artifacts/030/`, `artifacts/031/`, `artifacts/034/`, `artifacts/038/`, `artifacts/039/`, `artifacts/046/`, `artifacts/047/`, `artifacts/050/`, `artifacts/051/`, `artifacts/052/`, `artifacts/053/`, `artifacts/055/`, `artifacts/059/`, `artifacts/060/`, `artifacts/062/`, `artifacts/065/`, `artifacts/068/`, `artifacts/069/`, `artifacts/070/`, `artifacts/074/`, `artifacts/075/`, `artifacts/077/`, `artifacts/079/`, `artifacts/080/`, `artifacts/081/`, `artifacts/082/`, `artifacts/083/`, `artifacts/086/`, `artifacts/087/`, `artifacts/089/`, `artifacts/090/`, `artifacts/091/`, `artifacts/096/`, `artifacts/097/`, `artifacts/098/`, `artifacts/099/`, `artifacts/103/`, `artifacts/104/`, `artifacts/105/`, `artifacts/106/`, `artifacts/108/`, `artifacts/111/`, `artifacts/112/`, `artifacts/115/`, `artifacts/117/`, `artifacts/124/`, `artifacts/125/`, `artifacts/126/`, `artifacts/128/`, `artifacts/129/`, `artifacts/130/`, `artifacts/131/`, `artifacts/135/`, `artifacts/136/`, `artifacts/141/`, `artifacts/142/`, `artifacts/143/`, `artifacts/145/`, `artifacts/146/`, `artifacts/150/`, `artifacts/153/`, `artifacts/155/`, `artifacts/156/`, `artifacts/161/`, `artifacts/163/`, `artifacts/164/`, `artifacts/165/`, `artifacts/166/`, `artifacts/167/`, `artifacts/168/`, `artifacts/169/`, `artifacts/170/`, `artifacts/171/`, `artifacts/173/`, `artifacts/175/`, `artifacts/177/`, `artifacts/180/`, `artifacts/181/`, `artifacts/183/`, `artifacts/191/`, `artifacts/195/`, `artifacts/196/`, `artifacts/199/`, `artifacts/200/`, `artifacts/202/`, `artifacts/203/`, `artifacts/204/`, `artifacts/205/`, `artifacts/206/`, `artifacts/208/`, `artifacts/209/`, `artifacts/210/`, `artifacts/212/`, `artifacts/213/`, `artifacts/214/`, `artifacts/216/`.

### Input CSVs

- `inputs/008/data.csv`
- `inputs/016/data.csv`
- `inputs/025/data.csv`
- `inputs/026/data.csv`
- `inputs/028/data.csv`
- `inputs/038/data.csv`
- `inputs/069/data.csv`
- `inputs/080/checkouts.csv`
- `inputs/125/checkouts.csv`
- `inputs/129/data.csv`
- `inputs/130/data.csv`
- `inputs/168/data.csv`
- `inputs/183/data.csv`
- `inputs/191/data.csv`
- `inputs/195/data.csv`
- `inputs/208/data.csv`
- `inputs/212/data.csv`
- `inputs/213/data.csv`
- `inputs/214/data.csv`

---

**Journal rule:** When a fact changes, update **Current state** and add a new session entry with evidence. Keep the prior entry intact so we can reconstruct how our understanding evolved.
