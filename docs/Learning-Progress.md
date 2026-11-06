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

The original course setup fixes the validator to **Qwen/Qwen3-VL-30B-A3B-Instruct-FP8** and the chart-generating agents to **Qwen/Qwen2.5-Coder-3B-Instruct**, **mistralai/Ministral-3-14B-Instruct-2512**, and **zai-org/GLM-4.7-Flash**, with student-owned Modal deployments. Our repository explicitly takes a separate **non-credit, no-Modal** route: keep the upstream starter, reuse the Assignment 1 Docker sandbox pinned at `0cb0534c2fffb67ddfff619100057fad0be90a3c`, and experiment with hosted Z.ai `glm-4.7-flash` for generation. A hosted endpoint is **not automatically equivalent** to the official checkpoint/runtime. The multimodal validator endpoint is still **to be verified**. We must record every substitution and never present independently measured scores as official private-set scores. See [docs/UPSTREAM.md](UPSTREAM.md) and [docs/ARCHITECTURE.md](ARCHITECTURE.md).

## Current state — 2026-11-05

- **Existing code:** imported full pinned official starter; offline preflight, its unit tests, GitHub Actions CI, development-container setup, and supporting Phase 0 docs.
- **Seed inventory:** 110 released `result.json` trajectories; 98 final `figure.png` files; 19 committed CSV input files; `seed_labels.json` contains 110 human labels. Some runs legitimately have no figure.
- **Reported Phase 0 label counts (not validator predictions):** 12 `execution_failure`, 25 `wrong_data`, 71 `wrong_chart`, 39 `hard_to_read`, and 16 fully acceptable runs; refer to [PHASE-0.md](PHASE-0.md) and rerun the preflight before relying on a local environment.
- **Session 002 offline preflight:** Verified in Codespace on 2026-11-05: 111 resolved packages, 110 seed runs / 98 figures / 110 labels, and 5/5 unit tests passed. Visual/trajectory case studies for runs 004 and 008 recorded below; no model judging performed.
- **Validator status:** The first offline-first layer of `validator/solution.py` checks for missing/non-file/corrupt/wrong-format/truncated final PNGs and returns terminal `execution_failure` evidence. On structurally decodable PNGs, semantic data/chart/readability judges remain **explicitly unimplemented** (`NotImplementedError`), pending a verified vision endpoint. Seven new synthetic tests have been committed; their Codespace/CI execution is **pending verification**. The supplied baseline has not been scored.
- **Agent generation:** `workflow/generate.py` still calls Modal; it has **not** been migrated to the Assignment 1 Docker runtime. Do not run it expecting local Docker behavior.
- **Harbor:** example and template exist; our own packaged tasks do not yet exist. Docker execution and reward tests were **not performed in this session**.
- **Documentation:** this journal is the session 001 deliverable. GitHub source inspection and branch creation are verified; **no code execution, model calls, score computation, or CI result is claimed by this journal-writing session**.
- **Git:** Learning journal PR [#2](https://github.com/xqzr2000/cmu-11-768-assignment-2/pull/2) has merged to `main`. Session 002 uses `feature/session-002-offline-preflight`; review its changes by PR before merging.

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
- **Not yet verified:** the seven tests, CI status, and how the code behaves in the user's Codespace. No image-model request, dataset accuracy metric, or full validator run has been performed.

**Reproduce in Codespaces (after `git pull --ff-only`):**

~~~bash
uv run python -m unittest discover -s tests -p 'test_offline_*.py' -v
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python scripts/offline_preflight.py
git diff --check
git status --short --branch
~~~

**What we'll learn next:** Interpret real unit-test output and any errors; distinguish "a well-formed PNG" from "a correct readable figure"; then establish the requirements for a genuinely image-capable semantic judge. **Do not run the full `validator.runner` with the partial solution yet**: valid PNG cases intentionally raise `NotImplementedError` and trigger retries.

**Next exercises:** (a) **Completed:** loading `001`, `004`, `008` with `Run.load()`. (b) **Completed:** runner import, call, retry and checkpoint source walkthrough. (c) **Completed:** baseline request construction, model adapter, response parser and context-overflow fallback source walkthrough. (d) **Completed:** offline mock of `baseline.complete()` verified four text+image calls and two parsed errors. (e) **Implemented, tests pending:** deterministic execution checks plus seven synthetic tests. (f) **Next:** run those tests and the existing preflight in Codespaces, and record the actual output before claiming a pass.

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
