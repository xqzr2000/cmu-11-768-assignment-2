# CMU 11-768 Assignment 2 — Evaluating a Data-Visualization Agent

**Independent, non-credit reproduction and adaptation | November 2026 | Completed experiment**

This project follows the four-part evaluation workflow in [CMU's original Assignment 2](ASSIGNMENT.md) ([upstream repository](https://github.com/cmu-agents/assignment-2)). We retained its seed artifacts, human labels, error taxonomy, prediction schema, MCC scorer and Harbor task format. **We deliberately replaced the mandated models and Modal infrastructure** with hosted model APIs and our own Docker sandbox, making this an educational adaptation—not a course-compliant model configuration or a claim about official/private grades.

**Start here:** [Final report (PDF)](report.pdf) · [LaTeX source](report.tex) · [Original requirements](ASSIGNMENT.md) · [AI-use disclosure](AI_USAGE.md) · [Recorded submission check](output/check_submission.txt)

| Final checkpoint | Observed result |
| --- | --- |
| Public seed evaluation | **110 runs**; baseline macro-MCC **0.5235** → final **0.8726** |
| New agent evaluations | **5 tasks × 3 agents = 15 runs**, all with saved figures and human-reviewed labels |
| Harbor reference solutions | **5/5 scored 1.0** with the actual Docker/Harbor runner |
| Harbor mutant tests | Bad aggregation **rejected (0.0)**; unreadable labels **incorrectly accepted (1.0)**, demonstrating a verifier limitation |
| Submission checker | `submission valid`, using this repository's adapted workflow |
| Official course equivalence | **Not established:** the judge, agent models and execution infrastructure differ |

## 1. Original assignment requirements and our adaptation

The original assignment asks students to inspect existing visualization-agent trajectories, improve a validator that reports errors, develop new adversarial visualization tasks, run three prescribed agents, build Harbor verifiers and iterate based on measured failures. The evaluator receives **one task, its inputs, the agent trajectory and a final figure**, without ground-truth labels or reference images at inference time.

| Aspect | Original course requirement | Our implementation |
| --- | --- | --- |
| Validator model | **`Qwen/Qwen3-VL-30B-A3B-Instruct-FP8`**, deployed on Modal; no substitution allowed for graded work | **`gpt-6.1-terra`** via the OpenAI API. This is a declared deviation, not Qwen-equivalent evidence |
| Chart agents | **`Qwen/Qwen2.5-Coder-3B-Instruct`**, **`mistralai/Ministral-3-14B-Instruct-2512`**, **`zai-org/GLM-4.7-Flash`** | **`deepseek-flash`**, **`gpt-5.6-luna`**, **`glm-5.3-flash`** via three providers |
| Agent infrastructure | Course mini-SWE-agent workflow on student-hosted Modal infrastructure | `workflow/sandbox_generate.py`: mini-SWE-agent-compatible prompting, bash-tool protocol and limits; command execution in the Assignment 1 Docker sandbox |
| Part 1 | Score the baseline on seed runs; identify two recurring validator error types and cite run IDs | Baseline scored on 110 released runs; analyzed execution-artifact disagreements and confused error families |
| Part 2 | Implement two improvements in `validator/solution.py` and compare four MCCs plus macro-MCC | Deterministic figure check, structured data/design checklist, independent readability evaluation; scored all 110 runs |
| Part 3 | At least five tasks in two weakness classes (at least two per class); one run per prescribed agent; human labels; Harbor tasks and two mutants | Five tasks in a **3+2** split; **15 runs** with alternative agents; reviewed `labels.json`; five Harbor packages, two tested mutants |
| Part 4 | Make an additional validator change, evaluate seed and authored runs, analyze FP/FN, retain final deliverables | Added a distinct legibility requirement kind; experimented with enlarged-image overlay checks, measured a regression and deliberately disabled that option in the final validator |
| Deliverables/check | Validator, tasks, runs, labels, predictions, Harbor packages, report, end-to-end `check-submission` | Committed all of these, plus `AI_USAGE.md` and recorded results. Local checker passed; **this does not waive the original fixed-model requirement** |

The four error families and scoring definitions are unchanged:

- **`execution_failure`** — missing or invalid final figure.
- **`wrong_data`** — incorrect values, selections, aggregations or ordering.
- **`wrong_chart`** — chart design does not match the request.
- **`hard_to_read`** — clipped, overlapping, obscured or otherwise unreadable content.

A prediction can contain multiple families, except a ground-truth execution failure excludes the other three from their MCC denominators. The [official scoring implementation](workflow/evaluate.py) computes MCC separately for each family; **macro-MCC is the unweighted mean of the four**.

## 2. Architecture: hosted model intelligence, isolated local execution

```text
  task.json + task-local CSVs
              |
  Host/controller: workflow/sandbox_generate.py
  |           |                          |
  |     Hosted agent model API      Keys stay on host
  |     (DeepSeek / OpenAI / Z.ai)
  |           |
  |     Agent proposes bash commands
  |           v
  |     Fresh Docker sandbox per run
  |     network disabled; no API keys
  |     executes commands, creates figure.png
  |           |
  +---- result.json + figure.png --> runs/<task>__<agent>/
                                          |
  seed artifacts/ ------------------------+ 
                                          v
                  validator/solution.py + hosted Terra judge
                                          |
                    output/*_predictions.json
                                          |
                         ground-truth labels (scoring ONLY)
                                          |
                             per-family MCC / macro-MCC

  Independently: tasks/ --> harbor/tasks/ --> oracle/mutant verifier rewards
```

### Why reuse the Assignment 1 sandbox?

Instead of copying an execution framework or deploying the course's Modal agent runner, we reuse the [Assignment 1 sandbox](https://github.com/xqzr2000/cmu-11-768-assignment-1) as a **pinned Git dependency** (`agent-sandbox-runtime` in [`pyproject.toml`](pyproject.toml)). This separates two responsibilities: the **host** holds API keys, calls models and manages the conversation; the **sandbox** only executes model-proposed commands against the task data.

The implementation in [`workflow/sandbox_generate.py`](workflow/sandbox_generate.py) and [`sandbox/`](sandbox/) provides:

- **A new container for every run**, running as an unprivileged user, with networking off, capabilities dropped, no-new-privileges and resource/process limits (configured by the reused sandbox runtime). No host source-tree mount, Docker socket or provider credentials are passed to agent code.
- **A small plotting image:** [`sandbox/Dockerfile`](sandbox/Dockerfile) pins the Python base-image digest and installs a hash-locked plotting stack from [`sandbox/requirements.txt`](sandbox/requirements.txt).
- **Task-local staging:** `task.json` and only its referenced input files are copied into the container. The agent can use a single `bash` tool; its commands and observations become the recorded trajectory.
- **Course-style limits:** at most **20 model steps**, **120 seconds per shell command**, **15 minutes per agent run**; the submission marker is `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`.
- **Artifact extraction:** the host retrieves `figure.png`, checks it as a PNG, and writes `runs/<task>__<agent>/result.json` plus the figure. That format remains readable by the existing validator and scoring workflow.

**Security boundary:** This is a useful development sandbox, **not a guarantee of security against a hostile multi-tenant adversary**. The optional `--local` runner executes generated commands on the host and is **not isolated**; do not use it for untrusted model output. The Docker sandbox isolates *agent shell execution*; the hosted providers still receive task instructions and conversation content, while the vision judge additionally receives images and the selected input/trajectory evidence.

### Why these model choices?

We wanted to study **evaluation design and agent behavior** without deploying or paying to host several large checkpoints on Modal. Using hosted APIs also let us compare agents from different providers through a shared bash-tool interface.

| Role | Model used in this project | Purpose |
| --- | --- | --- |
| Agent A | **DeepSeek Flash** (`deepseek-flash`) | Generates charts using the DeepSeek API |
| Agent B | **GPT-5.6 Luna** (`gpt-5.6-luna`) | Generates charts using the OpenAI API |
| Agent C | **GLM-5.3 Flash** (`glm-5.3-flash`) | Generates charts using the Z.ai API |
| Independent judge | **GPT-6.1 Terra** (`gpt-6.1-terra`) | Image-capable structured evaluation through OpenAI Chat Completions |

The agents' API configuration lives in [`integrations/models.py`](integrations/models.py). The judge is configured through `VALIDATOR_*` environment variables in [`validator/model.py`](validator/model.py) (the recorded experiment used `reasoning_effort=none`, temperature 0, and `service_tier=flex`). Model names—especially moving provider aliases—are experiment provenance, not proof of equivalence to the fixed course checkpoints. The [report](report.pdf) records the setup and limitations. Earlier optional Z.ai/OpenAI pilot scripts in `scripts/` are historical experiments, **not additional models secretly used in the final validator**.

## 3. What we implemented in each assignment part

### Part 1 — Evaluate the starter baseline and diagnose errors

We ran the supplied [`validator/baseline.py`](validator/baseline.py) against **110 public seed trajectories**, compared predictions with `seed_labels.json`, and identified two repeated failure patterns:

1. **Confusing the trajectory's story with the existence of a valid figure.** Seed runs `026`, `047`, `081`, `191` and `205` had saved PNGs but were called execution failures; `001`, `145` and `171` were accepted despite no PNG. This motivated checking the *artifact itself* before asking a model.
2. **Mixing data, design and legibility.** The baseline marked wrong chart designs as `wrong_data` (for example `021` and `090` were missing an x-axis label, not incorrect values), and sometimes missed readable-versus-unreadable distinctions. This motivated an explicit requirement taxonomy rather than independent open-ended yes/no prompts.

The initial seed **macro-MCC was 0.5235**. See [`output/baseline_score.txt`](output/baseline_score.txt) and [the report](report.pdf) for confusion matrices and more run-level evidence.

### Part 2 — Improve the validator without looking up labels

[`validator/solution.py`](validator/solution.py) implements the two proposed changes:

- **Deterministic execution gate:** Pillow verifies and decodes `figure.png`. Missing, wrong-format or undecodable images yield terminal `execution_failure` without spending a model call. A failed agent trajectory does **not** automatically mean the final image is missing.
- **Family-aware structured evaluation:** one strict-JSON requirement checklist classifies requested elements as data or design and records whether each was met; a separate image-first pass assesses `hard_to_read` severity. Measured pixel size, DPI and blank-image facts are supplied to avoid asking the judge to guess them.

The validator sees the task, relevant input files, a compact trajectory and the figure; human labels are used **only after predictions exist**, for scoring and analysis. Part 2 raised seed macro-MCC to **0.8747**. See [`output/pre_iteration_seed_score.txt`](output/pre_iteration_seed_score.txt).

### Part 3 — Design adversarial tasks, generate runs and package Harbor environments

We chose two potential generalization weaknesses: **large-input aggregation** (where a compact transcript and clipped data may conceal numerical mistakes) and **fine visual detail** (where correct-looking charts can fail on styling, text and overlap).

| Task | Class | What it probes |
| --- | --- | --- |
| [`quarterly-revenue-by-region`](tasks/quarterly-revenue-by-region/task.json) | Large-input aggregation | Grouping 3,000 orders and calculating revenue rather than unit totals |
| [`top-products-unit-share`](tasks/top-products-unit-share/task.json) | Large-input aggregation | Correct denominator, top-eight selection, percentages and sorting |
| [`sensor-daily-median`](tasks/sensor-daily-median/task.json) | Large-input aggregation | Missing readings, daily medians, sensor filtering and a min–max band |
| [`styled-decay-curves`](tasks/styled-decay-curves/task.json) | Fine visual detail | Exact line colours, styles, markers, log scale, grid and legend |
| [`dense-department-budgets`](tasks/dense-department-budgets/task.json) | Fine visual detail | Thirty long category names, rotation, layout and readable labels |

Each task was run once with each of the three **adapted** agents, producing **15 recorded runs** in [`runs/`](runs/). Every run produced a figure. The 15 labels in [`labels.json`](labels.json) were drafted with AI assistance, checked against independently computed keys and replays of agent-generated plotting commands, visually inspected and human-reviewed; the use of AI is disclosed in [`AI_USAGE.md`](AI_USAGE.md).

**Observed agent failures:** all 15 depicted the requested data and chart design, but **five** were labelled `hard_to_read`: the GLM budget chart clipped long names; the Luna budget chart overlapped wrapped labels; and each of the three sensor plots placed its legend over part of the S2 band. Thus the authored set contains **no positive `execution_failure`, `wrong_data` or `wrong_chart` labels**—an important limit on what its MCC scores demonstrate.

#### Harbor: deterministic checks and their blind spot

Each task was also packaged in [`harbor/tasks/`](harbor/tasks/) with a reference `solution/solve.sh`, an independently checked `plotted_values.json` sidecar, and a deterministic verifier. The verifier checks artifact validity, input integrity, re-rendering consistency and plotted values/styles against task-specific expectations.

**Actual Harbor results**, recorded in [`output/check_submission.txt`](output/check_submission.txt):

| Test | Harbor reward | Interpretation |
| --- | ---: | --- |
| Each of the **five oracle/reference solutions** | **1.0** | All five passed their packaged verifiers |
| `quarterly-revenue-by-region/mutants/sum_units` | **0.0** | Incorrect aggregation caught by numeric checks |
| `dense-department-budgets/mutants/unrotated_labels` | **1.0** | Incorrect but accepted: labels overlap, exposing a deterministic verifier blind spot |

The mutant that scores 1.0 is **intentionally a test failure of the verifier**, not evidence that the chart is good. The real `workflow check-submission` invocation reported **`submission valid`** for the adapted deliverables. That check confirms local structural and Harbor requirements; it is **not a grade under the course's prescribed model infrastructure**.

### Part 4 — Iterate, evaluate and keep the better-supported configuration

The additional change in the **final** validator gives legibility-related instructions their own `legibility` requirement kind, so an instruction about overlapping labels no longer creates a `wrong_chart` false positive.

We also tested an enlarged-quadrant image and mandatory overlay inventory to catch the sensor legend occlusions. It worked on all three authored sensor failures, but **increased false positives on the more varied seed set**. We calibrated the rule and measured it again; the larger experiment still performed worse. Therefore the final code keeps that feature **disabled** (`OVERLAY_INVENTORY = False`) and retains the legibility taxonomy fix. This is a measured choice rather than claiming that every attempted change improved accuracy.

## 4. Final measured results

### Released seed runs (110; GPT-6.1 Terra judge)

Numbers below are from committed score files—not estimates.

| Error family | Baseline MCC | Part 2 MCC | **Final MCC** |
| --- | ---: | ---: | ---: |
| `execution_failure` | 0.5945 | 1.0000 | **1.0000** |
| `wrong_data` | 0.2363 | 0.7406 | **0.7093** |
| `wrong_chart` | 0.6286 | 0.9284 | **0.9512** |
| `hard_to_read` | 0.6345 | 0.8297 | **0.8297** |
| **Macro-MCC** | **0.5235** | **0.8747** | **0.8726** |

Final seed confusion counts: `execution_failure` **TP 12 / FP 0 / FN 0**; `wrong_data` **TP 22 / FP 9 / FN 3**; `wrong_chart` **TP 69 / FP 0 / FN 2**; `hard_to_read` **TP 33 / FP 2 / FN 6**. The final score substantially beats the baseline but is slightly below the particular Part 2 pass, which is consistent with observed model-output variation. Do **not** claim the Part 4 iteration improved seed macro-MCC.

Sources: [baseline](output/baseline_score.txt) · [Part 2](output/pre_iteration_seed_score.txt) · [final seeds](output/final_seed_score.txt) · [prediction JSON](output/final_seed_predictions.json).

### Self-authored runs (15; human-reviewed)

| Error family | Final MCC | Positive human labels | Caveat |
| --- | ---: | ---: | --- |
| `execution_failure` | 0.0000 | 0/15 | No positive examples |
| `wrong_data` | 0.0000 | 0/15 | No positive examples |
| `wrong_chart` | 0.0000 | 0/15 | No positive examples (and **0** final false positives) |
| `hard_to_read` | **0.5547** | 5/15 | TP 2, TN 10, FP 0, FN 3 |
| **Macro-MCC** | **0.1387** | — | Three categories have insufficient support |

A zero MCC for the first three families is the scorer's **insufficient-support convention**, not evidence that the validator failed all those categories. The final change removed the authored `wrong_chart` false positive, but still missed the three sensor-overlay readability errors. The more aggressive overlay candidate caught all five readability positives (MCC 1.0 on that small family) yet regressed on the broader seed set, so it was **not** shipped.

Sources: [final authored scores](output/authored_score.txt) · [authored predictions](output/authored_predictions.json) · [iteration notes and alternatives](docs/report-notes.md).

**Scope of the result:** These are descriptive scores on released seeds and our own small task set, using **different models** from those mandated by the course. No held-out private score, official Qwen3-VL evaluation, or same-model head-to-head comparison is claimed. The report records a cumulative **$4.84 in judge API spending** across all measured passes; this is historical cost, not a guaranteed price for rerunning.

## 5. Reproduce and inspect

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and Docker **only** for agent generation and real Harbor runs. Work from the repository root; a Codespace can supply the environment. Offline inspection and scoring require **no model API calls**.

```bash
uv sync --locked

# Offline integrity and unit tests (no model usage).
uv run python scripts/offline_preflight.py
uv run python -m unittest discover -s tests -p 'test_validator_*_offline.py' -v
uv run python -m workflow validate-tasks
uv run python -m workflow validate-labels

# Re-score committed predictions, with no model calls.
uv run python -m workflow score --labels seed_labels.json --predictions output/final_seed_predictions.json
uv run python -m workflow score --predictions output/authored_predictions.json

# View the recorded Docker/Harbor check (does not rerun Docker).
cat output/check_submission.txt
```

For an **opt-in live reproduction**, configure `DEEPSEEK_API_KEY`, `OPENAI_API_KEY` and `ZAI_API_KEY` securely (Codespaces secrets or ignored local `.env`). To use Terra as judge, replace the default Modal example values in `.env` with `VALIDATOR_BASE_URL=https://api.openai.com/v1` and `VALIDATOR_MODEL=gpt-6.1-terra`; remove the placeholder `VALIDATOR_API_KEY` so the client can use `OPENAI_API_KEY`. Set `VALIDATOR_REASONING_EFFORT=none` and `VALIDATOR_SERVICE_TIER=flex` to match the reported experiment (subject to current provider availability). **Never commit keys.** The example file is [`.env.example`](.env.example).

```bash
# Live: builds a Docker image, calls three hosted agent APIs and may incur charges.
docker build -t hw2-chart:1 sandbox/
uv run python -m workflow.sandbox_generate

# Live: calls a hosted vision judge; use a NEW output file.
uv run python -m validator.runner --artifacts artifacts --out output/my_seed_predictions.json --workers 1
uv run python -m workflow score --labels seed_labels.json --predictions output/my_seed_predictions.json

# Docker required: rerun real Harbor oracles and mutants.
uv run python -m workflow check-submission
```

The original Modal deployment scripts and `workflow generate` remain as upstream reference code; use **`workflow.sandbox_generate`** for this independent non-Modal workflow. API requests may cost money or fail because of provider access, rate limits or changing model aliases. Re-running a model does not guarantee byte-identical predictions.

## 6. Files, provenance and limitations

| Path | Contents |
| --- | --- |
| [`ASSIGNMENT.md`](ASSIGNMENT.md) | Unmodified assignment requirements and grading specification |
| [`validator/solution.py`](validator/solution.py) | Final task-agnostic validator; no seed IDs or ground-truth lookup |
| [`artifacts/`](artifacts/) / [`seed_labels.json`](seed_labels.json) | Original public seed trajectories, figures and labels |
| [`tasks/`](tasks/) / [`runs/`](runs/) / [`labels.json`](labels.json) | Authored tasks, 15 real agent runs and human-reviewed labels |
| [`sandbox/`](sandbox/) / [`workflow/sandbox_generate.py`](workflow/sandbox_generate.py) | Container image, task staging and host-side model/tool loop |
| [`harbor/tasks/`](harbor/tasks/) | Five self-contained Harbor environments, oracle solutions and two mutants |
| [`output/`](output/) | Committed scored predictions, per-family scores and submission-check evidence |
| [`report.pdf`](report.pdf) / [`report.tex`](report.tex) | Full experiment, failure analyses, trade-offs and results |
| [`AI_USAGE.md`](AI_USAGE.md) / [`docs/UPSTREAM.md`](docs/UPSTREAM.md) | AI-assisted work disclosure and pinned upstream/sandbox revisions |
| [`docs/README-Development-History.md`](docs/README-Development-History.md) / [`docs/Learning-Progress.md`](docs/Learning-Progress.md) | Archived phase-by-phase experiments and engineering history |

The key lesson is that **valid execution, correct data, faithful chart design and perceptual readability require different checks**. Deterministic artifact checks eliminated avoidable execution mistakes, while schema-guided judging reduced family confusion. Task-specific Harbor verifiers were excellent at exact numerical errors but missed a genuinely unreadable chart; conversely, a stronger vision rule improved one small task family while creating false alarms elsewhere.

**This repository is an educational research reproduction, not an official CMU grading result.** For the original fixed models, Modal deployment, course agent semantics and private evaluation, follow the [course specification](ASSIGNMENT.md) rather than treating our adapted setup as interchangeable.
