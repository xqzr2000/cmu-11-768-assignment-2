# CMU 11-768 Assignment 2 — What We Are Building and What We Have Learned

**A beginner-friendly guide to our project, updated after Sessions 008–010 on November 7, 2026**  
**Repository:** [cmu-11-768-assignment-2](https://github.com/xqzr2000/cmu-11-768-assignment-2)  
**Current work:** `feature/session-010-chart-agent-controller` (unmerged; paused after offline wheel-lock audit). Session 007's prompt experiment is preserved in `archive/session-007-20261107`.  
**Sources:** repository `ASSIGNMENT.md`, `README.md`, `docs/Learning-Progress.md`, the Session 008–010 design and compatibility reports, `integrations/models.py`, `validator/`, `workflow/`, and verified Codespaces checkpoints.

> **The central idea:** We are learning to **evaluate an AI agent**, not mainly to teach AI to draw charts. A chart-making agent tries to finish a user's visualization task. Our validator checks whether its resulting figure and its recorded actions satisfy the task. Human judgments let us measure whether the validator is trustworthy.

---

## 1. What is Assignment 2 asking us to do?

A user might ask an AI agent:

> “Read `data.csv` and make a Sankey diagram with all fruit categories, showing each source–target pair with the correct weight. Save it as `figure.png`."

The **visualization agent** receives the instructions and any data files, writes Python code, uses a shell or plotting tools, and attempts to save an image. It can make mistakes, even when the resulting image looks convincing.

**Our assignment is to build a validator (an AI-based evaluator) that can inspect this attempt and determine what went wrong.** Its available evidence is:

1. The original task instructions (what the user actually requested).
2. The input data and other files (what the chart should represent).
3. The agent's trajectory (its messages, tool calls, and code/actions).
4. Its final `figure.png`, if it produced one.

The validator returns a set of named errors with concrete explanations, or an **empty error list** if it judges the result acceptable. During official grading it receives **one run at a time**, without the human label, an ideal reference image, or competing runs to compare against.

This is more difficult than “does the image look nice?” We need to check **correctness, design compliance, and readability** while understanding what went wrong in the agent's process.

The course assignment then asks us to develop harder tasks, test the evaluator on them, and build deterministic checks using the **Harbor** evaluation framework. Our repository is an **independent, non-credit adaptation** of the official starter, using Codespaces and a planned local Docker sandbox instead of deploying on the course's Modal infrastructure.

## 2. How many agents/models do we have?

**The official task-generation setup has three fixed chart-making agent models and one separate fixed judge model.** These are distinct jobs.

| Role | Exact model | What it is supposed to do |
| --- | --- | --- |
| **Chart-making agent A** | `Qwen/Qwen2.5-Coder-3B-Instruct` | Operate through an agent/tool scaffold and attempt a visualization task, including writing/running plotting code. |
| **Chart-making agent B** | `mistralai/Ministral-3-14B-Instruct-2512` | Attempt the *same* authored visualization task independently. |
| **Chart-making agent C** | `zai-org/GLM-4.7-Flash` | Make a third independent attempt at the same task. |
| **Official validator / judge** | `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` | Look at the task, trajectory, data, and final image and decide which errors occurred. |

A **model** is the underlying language/vision system; an **agent** is a model operating inside a workflow with instructions, tools, and opportunities to take actions. So the three models above become *chart-making agents* when run through the provided scaffold (a mini-SWE-agent-style setup).

The course requires **at least five new visualization tasks**, each run once by **all three agents**: a minimum of **5 × 3 = 15 new runs**, each to be human-reviewed. We **have not yet generated those 15 new runs** in our independent environment. The existing 110 seed runs were supplied in the starter; they are not runs we generated during Sessions 001–007.

### Official assignment workflow (not our current experimental model deployment)

```text
                 USER'S VISUALIZATION REQUEST
                        + input data
                             |
          +------------------+------------------+
          |                  |                  |
    Qwen2.5-Coder        Ministral-3        GLM-4.7-Flash
     chart agent          chart agent          chart agent
          |                  |                  |
       Python code + tool calls + attempted figure.png
          |                  |                  |
          +------------------+------------------+
                             |
                Individual run artifacts
              (task + trajectory + PNG)
                             |
                             v
                    OUR VALIDATOR
        (official model: Qwen3-VL + our logic)
                             |
                  Predicted error labels
                             |
                             v
         COMPARE AGAINST HUMAN-REVIEWED LABELS
                             |
                TP / TN / FP / FN, MCC
```

The figure-generating agents are **the systems being tested**. The validator is **the system we are trying to improve**. The human labels are a **reference for evaluating the validator**, not instructions we give the validator.

**Important as of Session 010:** This diagram names the *official* models. Our current independent API-backed roles differ; see Section 3. We have not yet generated the 15 required new agent runs in either setup.

## 3. Why did we change model selection? The APIs we can actually use

**Short answer:** The official assignment specifies models normally deployed through Modal. We are doing an **independent, non-credit adaptation** in GitHub Codespaces. We have working credentials and accessible hosted APIs for **DeepSeek, OpenAI, and Z.ai**, but we have not deployed the required Qwen/Ministral models and Qwen3-VL judge ourselves. Therefore we chose API-accessible models to learn how to build and evaluate the *same type of chart-making agent system* without pretending these are identical models or an official course submission.

**The API constraint is a practical implementation reason, not a scientific reason to prefer these models.** We must distinguish what we can execute from what the course requires. An API connection that works does not guarantee equal chart quality, reasoning, vision performance, cost, or official grading comparability.

### Original course models versus our current API-backed choices

| Role | Official required model (in `ASSIGNMENT.md`) | Our independent API choice (in `integrations/models.py`) | Provider / protocol |
| --- | --- | --- | --- |
| Chart agent A | `Qwen/Qwen2.5-Coder-3B-Instruct` | `deepseek-flash` | DeepSeek / stateless Responses |
| Chart agent B | `mistralai/Ministral-3-14B-Instruct-2512` | `gpt-5.6-luna` | OpenAI / Responses |
| Chart agent C | `zai-org/GLM-4.7-Flash` | `glm-5.3-flash` | Z.ai / Chat Completions |
| Chart-error validator | `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` (fixed; no replacement permitted for official grading) | `gpt-6.1-terra` (**experimental judge only**) | OpenAI / Responses, image input, strict JSON |

The **original models and Modal scripts are still in the repository**. The new role registry and adapters are under `integrations/`; `workflow/generate.py` still represents the original Modal generation route, and `validator/solution.py` has not been converted into a Terra-powered official validator. Calling the Terra adapter an *experimental judge* is deliberate: a Terra result is **not** a Qwen3-VL validator result.

The direct-provider IDs are request names, not proof of immutable model weights. In particular, `deepseek-flash` is a moving alias; record both the requested and provider-reported ID (and date) rather than asserting an exact underlying checkpoint. Similarly, the hosted `glm-5.3-flash` endpoint is not a verified checkpoint-equivalent replacement for the course's `zai-org/GLM-4.7-Flash`.

### How we arrived at these choices (Sessions 004–009)

1. **Official starting point:** The course gives us three named chart agents and the fixed Qwen3-VL judge. Its expected deployment uses Modal. We retained the starter and began with offline dataset and validator work.
2. **Early Z.ai vision exploration:** `glm-4.6v-flash` could inspect a small synthetic bar chart, but a real-seed pilot did not produce a reliable strict YES/NO result. This was an *experimental judge*, never the official generator GLM.
3. **Early OpenAI vision exploration:** We used `gpt-5.4-mini` for separately controlled, structured per-error-family questions on seeds 004 and 008. These tests taught us about false positives and false negatives, not official Qwen accuracy.
4. **Session 008 provider migration:** We added an explicit four-role registry and provider-specific request builders because we have practical API access to DeepSeek, OpenAI and Z.ai. Three adapters can describe a `run_shell` tool request; Terra has a separate image-and-JSON judging adapter. None of these adapters automatically executes proposed commands.
5. **Session 009 live compatibility tests:** The user separately authorized **one** live probe for each current model role. `deepseek-flash`, `gpt-5.6-luna`, and `glm-5.3-flash` each returned a parsable *inert* function call. `gpt-6.1-terra` returned schema-valid structured JSON for a **synthetic** chart image. The earlier attempt to use a free `glm-4.7-flash` endpoint instead failed with `RateLimitError` and no retry. We moved to paid `glm-5.3-flash` for the experimental Agent C; the exact cause of the earlier rate limit is unknown.

**What the four successes prove:** the requested hosted APIs accepted these particular requests and our adapters understood their tool-call or structured-output formats.

**What they do *not* prove:** that any agent can write, run and save a correct chart; that Terra correctly diagnoses real failures; that a full multi-turn workflow works; or that a score from these model substitutions can be compared directly with official Qwen/Ministral/GLM grading.

### Why the provider differences matter

The same agent-controller idea must work across *different message formats*. DeepSeek requires stateless Responses history replay; OpenAI uses Responses items and function-call outputs; Z.ai uses Chat Completions messages and tool replies. We added normalization so the rest of our program sees a consistent representation of a model's **proposed** tool call.

A model **proposing** `run_shell` is not permission to run it. The controller and Docker gateway enforce bounded turns, tools, command sizes and result sizes; a host must still request **separate explicit authorization** before each potentially billed model request, sandbox launch and command execution. No old API-test permission carries over into Session 010.

### What has actually been built around the new models (Session 010)

The new local architecture is still **offline-first and incomplete**:

- `integrations/chart_controller.py` implements an in-memory controller with provider-specific conversation replay and budgets; it makes no API calls and runs no tools.
- `integrations/sandbox_gateway.py` is a separately gated interface to our **pinned Assignment 1 Docker sandbox**. It rejects unapproved launches/commands, limits resources, does not forward model API keys, and requests a fingerprint-based check of exact commands. The tests use fake Docker.
- `integrations/task_artifacts.py`, `integrations/chart_transfer.py` and `scripts/figure_extract_worker.py` validate task CSVs, stage controlled inputs, and define a strict bounded PNG extraction format. These are not yet wired into a live chart loop.
- `integrations/chart_image_recipe.py` and `integrations/chart_build_context.py` generate an **inert** non-root Dockerfile recipe and a tightly limited private build context; they have not built an image.
- `requirements/chart-cp312-linux-amd64.txt` pins **14** plotting dependencies (4 direct, 10 transitive) to selected wheel hashes derived from `uv.lock`. The independent offline audit **passed** in Codespaces. **However, the Dockerfile and build context do not consume that hash file yet**, and no wheels have been downloaded or installed. A registry-inspected `python:3.12-slim` AMD64 manifest is only a *candidate image pin*, not a built or trusted environment.

**Current verified boundary:** Session 010's six offline suites passed **77/77** tests; the earlier provider **37/37** and validator **49/49** regressions also passed. The later 14-wheel hash audit separately passed. None of this constitutes an end-to-end agent run, model-accuracy benchmark, real Docker build, or official reproduction.

### The rule that keeps our experiment scientifically honest

We must maintain **two clearly labeled tracks**:

| Track | What we can conclude |
| --- | --- |
| **Independent API-based learning track** | We can study orchestration, trajectory collection, visual error definitions, human labeling, confusion matrices, MCC, and failure analysis using our API-backed agents and Terra. Every result must identify actual provider, requested/reported model, task set, prompt, rubric, date, and runtime. |
| **Strict course-equivalent track** | Only the prescribed three generation models and fixed Qwen3-VL judge, under the required assignment interfaces and evaluation conditions, can support a claim of following the official model constraints. Completing our API-based experiment **does not** automatically satisfy those requirements. |

The assignment's **intellectual goal remains unchanged:** build a validator that detects genuine errors in agent-generated visualizations, measure where it fails against independent human labels, create harder tests, and improve the evaluator. **The model substitutions change the experimental population and judge; they must not be hidden or described as a drop-in official solution.**


## 4. Is the assignment simply “one agent draws, another checks against human-labelled plots”?

**That is a helpful first approximation—but with three important corrections.**

1. **The checker does not receive the human label.** It independently looks at the task, data, trajectory, and final figure. *Afterward*, our scoring program compares the checker's prediction with human annotations.
2. **There are three prescribed chart-making agents for the new tasks**, not just one. They let us observe whether the same task produces different failures in different agents.
3. **The assignment goes beyond image checking:** it includes analyzing trajectories, improving a validator, inventing adversarial tasks, and creating deterministic Harbor test environments.

Here is the distinction:

| Artifact | Who creates it? | Why it exists |
| --- | --- | --- |
| `task` / instructions | Dataset author or, later, us | Defines what should be produced. |
| `data.csv` or other inputs | Dataset/task author | Supplies actual numbers/categories to plot. Some tasks have no CSV. |
| `result.json` / trajectory | Agent run infrastructure | Records the agent's instructions, actions, and outcome. |
| `figure.png` | Visualization agent (if successful) | The actual chart to inspect, which **may be incorrect**. |
| `seed_labels.json` | Human reviewers supplied with the starter | Tells us which errors the released runs contain. |
| Validator prediction JSON | Our evaluator | Its independent judgment; compared with human labels later. |
| `labels.json` for new tasks | We will create after human review | The reference labels for our future authored runs. |

### Are there human-labelled plots? Yes, in one sense—not in another.

The course released **human-reviewed outcomes for chart-producing runs**. A label might state:

```json
{
  "run_id": "008",
  "errors": [
    {"family": "wrong_data", "evidence": "..."},
    {"family": "hard_to_read", "evidence": "..."}
  ]
}
```

This means the human found those two problems in that run. It **does not** mean a human provided an ideal replacement image or a per-pixel annotation. An acceptable run has an empty `errors` list, and an unsuccessful run can have **no figure at all**.

The starter contains **110 released runs, 98 final PNG figures, and 110 human-reviewed labels**. Twelve runs are labeled `execution_failure`, consistent with some runs having no valid figure. The starter does **not** supply a perfect human-drawn chart to compare pixel-for-pixel against each agent output; the grading reference is the **error annotation per run**.

The assignment materials provided do not explain the external origin of every source CSV or how every original row was collected. What we can state confidently is that these **are task input files bundled with the released starter**, not files we collected or generated during our sessions.

### Where are the CSV files?

For a public seed run such as **008**:

```text
inputs/008/data.csv           # released data: fruit source,target records
artifacts/008/result.json     # task instructions + complete agent trajectory
artifacts/008/figure.png      # rendered Sankey-style diagram
seed_labels.json              # human reference error tags for run 008
```

The starter has **19 committed CSV input files**; not every task needs a CSV. For example, seed **004** is a mathematical-function plotting task with **no CSV**: its data is created from formulas in the instructions.

For our own future tasks, the official instructions allow us to **synthetically generate data or reuse data** from another visualization task, and to put it under `tasks/<task_id>/inputs/`. We will need to document the chosen source and human-review each generated run.

## 5. What exactly does the validator evaluate?

The assignment specifies **four error families**, each a binary yes/no decision for a given run.

| Error family | Question | Concrete example |
| --- | --- | --- |
| `execution_failure` | Did the agent fail to produce a valid final figure? | PNG missing or corrupt. |
| `wrong_data` | Are the plotted values, selections, or calculations wrong? | Missing a fruit source category; incorrect mathematical operation. |
| `wrong_chart` | Does the *design* violate the requested chart specifications? | Linear axis where a logarithmic axis was explicitly requested. |
| `hard_to_read` | Is the image unreadable or unusually difficult to interpret? | Near-white text on a white background. |

The same figure can have **more than one error**. In seed 008 the data are wrong **and** the labels are hard to read, but the human reviewers did **not** label the diagram's chart design wrong.

**Special rule:** A human-labeled `execution_failure` is *terminal*: for such a run, the scoring system omits that run from the other three categories' denominators. A validator that itself predicts execution failure does **not** get to ignore mistakes it also predicts elsewhere.

The official released label inventory is:

| Human label category | Number of runs |
| --- | ---: |
| `execution_failure` | 12 |
| `wrong_data` | 25 |
| `wrong_chart` | 71 |
| `hard_to_read` | 39 |
| Fully acceptable (no labeled errors) | 16 |

**Do not add these counts to get 110:** the categories overlap. A single run can contribute to two or three of the nonterminal families. These numbers are **human reference-label counts**, not our validator's accuracy.

## 6. What is a confusion matrix, and why do we use one?

Once the validator makes a prediction **without seeing the human label**, we compare its yes/no answer to the human yes/no answer **for each error family separately**.

Suppose we are evaluating `wrong_chart`:

| | **Human: chart error YES** | **Human: chart error NO** |
| --- | --- | --- |
| **Validator: YES** | **TP — True Positive**: correctly found a chart error | **FP — False Positive**: falsely accused a correct design |
| **Validator: NO** | **FN — False Negative**: missed a genuine error | **TN — True Negative**: correctly accepted the design |

This table is a **confusion matrix**. It tells us *how* the judge is failing, not merely how often it matches a label.

- **FP (false alarm):** The checker says there is a problem when there is not. This makes the checker overcritical.
- **FN (missed problem):** The checker says the design is fine even though it violates the task. This makes the checker too permissive.
- **TP and TN:** The two kinds of correct answers.

We build **four confusion matrices**, one per family. We do **not** put the four errors into one mutually exclusive four-class matrix, because a run can have multiple errors simultaneously.

### Our actual confusion-matrix lesson: seeds 004 and 008

We tested the OpenAI judge's `wrong_chart` decision on two **known development cases**:

| Run | Human judgment | Original prompt (`v1`) | More cautious prompt (`v2`) |
| --- | --- | --- | --- |
| **004**: missing requested log x-axis | Error present | YES → **TP** | NO → **FN** |
| **008**: custom Sankey design | No chart-design error | YES → **FP** | NO → **TN** |

So the two tiny confusion matrices are:

| Version | TP | FP | FN | TN |
| --- | ---: | ---: | ---: | ---: |
| **v1** | 1 | 1 | 0 | 0 |
| **v2** | 0 | 0 | 1 | 1 |

The change helped on **008** but hurt on **004**. A simplistic “v2 has fewer false alarms!” claim would miss the new **false negative**. Both prompts matched **one of two** selected cases. The two cases are known, tiny, and not representative; we cannot draw a reliable model-performance conclusion from them.

### What is MCC, and why not just use accuracy?

The official scorer summarizes **each category's confusion matrix** using **Matthews correlation coefficient (MCC)**:

```text
              TP × TN − FP × FN
MCC = ------------------------------------
      sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
```

MCC ranges from **−1 to +1**:

- **+1**: perfect classification.
- **0**: no measured correlation (also the official convention in certain zero-denominator cases).
- **−1**: perfectly inverted classification.

Unlike plain accuracy, MCC considers all four cell types and is useful when some error categories are much more frequent than others. For instance, with mostly easy negative examples, an evaluator that constantly says “no error” can achieve deceptively high accuracy while missing the positives.

The scorer computes an MCC **separately for `execution_failure`, `wrong_data`, `wrong_chart`, and `hard_to_read`**, then reports their unweighted average, called **`macro_mcc`**:

```text
macro_mcc = (MCC_execution_failure + MCC_wrong_data
           + MCC_wrong_chart + MCC_hard_to_read) / 4
```

The scorer also reports how many human positives and negatives exist for each family. If a class is missing, it flags **insufficient support** and uses MCC = 0 by convention. If predictions are constant on mixed classes, the denominator also becomes zero and MCC is recorded as 0.

**We have not yet computed a meaningful official four-family macro-MCC.** A handful of deliberately chosen GPT-5.4 Mini answers on two runs does not replace a complete scored sweep using the required Qwen3-VL validator.

Finally, MCC measures **whether the yes/no classifications agree**; it does not itself score whether the explanations are specific, truthful, or helpful. We separately inspect the explanations.

## 7. Two real examples we investigated

### Seed 008: Fruit Sankey diagram

**Task:** Read `data.csv`, show fruit-to-fruit flows, keep left-hand sources and right-hand targets, use consistent fruit colors, and include a title/legend.

**Input data:** 1,000 source–target rows, with five fruit names. After correctly handling a UTF-8 byte-order mark, there are 25 distinct fruit pairs.

**Agent's error:** Its final plotting script included:

```python
df = pd.read_csv("data.csv", header=None,
                 names=["source", "target"],
                 encoding="utf-8-sig").query("source != 'orange'")
```

This discarded **80 rows** (8%) with `orange` as the source. The displayed left-hand nodes therefore omit orange entirely. The missing orange-source flows were: orange→orange 53, orange→banana 15, orange→blueberry 8, orange→apple 3, and orange→lime 1.

**Human reference:** `wrong_data` (missing source category) and `hard_to_read` (near-white labels on white background), **not** `wrong_chart`.

**What we learned:**

- A visually plausible chart can still misrepresent the CSV.
- A genuine error in the data does not automatically imply the chart *type* is wrong.
- A custom Sankey-like drawing can satisfy the design even when built without a dedicated Sankey library.
- CSV text encoding can affect category counting: our initial raw CSV inspection saw 26 distinct pair strings because the first fruit contained a UTF-8 BOM; using `utf-8-sig` correctly gives 25.

### Seed 004: Four mathematical subplots

**Task:** Draw a 2×2 figure of mathematical functions with specified formulas, error bars and logarithmic axes. The fourth subplot requires **both** x and y axes on log scales.

**Agent's error:** Its recorded plotting script sets the fourth panel's y-axis to log, but **does not** call `axs[1, 1].set_xscale('log')`, leaving its x-axis linear. The human label therefore includes `wrong_chart`. The script also omits a required cubing step in the fourth panel, which supports a separate `wrong_data` label. A requested base-3 x-axis on panel three was also not explicitly configured in the script.

**What we learned:** A model may claim that requested axes are correct even when the trajectory's code demonstrates otherwise. We need to check **specific requirements** rather than trust a fluent summary.

## 8. Our project progress so far: Sessions 001–010

The earlier sections' seed examples and confusion-matrix lesson remain valid **historical development examples**. This section updates the *current project state* instead of erasing those observations.

| Session | Work performed | Verified result / important limit |
| --- | --- | --- |
| **001 — Repo setup** | Imported the full starter, pinned Assignment 1 sandbox dependency, documented the independent workflow. | Official starter retained. |
| **002 — Seed inspection** | Inspected released artifacts, figures, inputs and human labels. | 110 released runs / 98 figures / 110 labels verified. |
| **003 — Validator plumbing** | Added structural figure checks and mock-tested the baseline interface. | Offline wiring, not model accuracy. |
| **004 — Z.ai vision probe** | Tested `glm-4.6v-flash` on a synthetic figure. | Limited image-understanding smoke test. |
| **005 — Real-seed pilots** | Diagnosed Z.ai response/budget mismatch; introduced `gpt-5.4-mini` structured pilot. | Selected family-level judgments only. |
| **006 — Seed 008** | Inspected actual CSV/figure and performed three-family OpenAI pilot. | Found `wrong_chart` false positive alongside correct detections. |
| **007 — Chart-design rubric** | Tested versioned `wrong_chart` prompt v2 against seeds 004 and 008. | 008 FP→TN **but** 004 TP→FN; experiment archived, not universal improvement. |
| **008 — API model migration** | Added DeepSeek/OpenAI/Z.ai adapters, immutable four-role registry, normalizers and Terra judge parser. | Mocked provider integration merged via PR #8; no agent chart run. |
| **009 — API compatibility** | Ran separately authorized one-call checks for three generators and Terra, including a documented GLM rate-limit failure and later paid GLM replacement. | Four current roles successfully parsed a tool call / synthetic-image JSON; no shell execution or MCC. Merged via PR #9. |
| **010 — Chart controller and environment** | Built pure controller, gated fake-Docker gateway, CSV/PNG guards, extractor protocol, inert Docker image/context planning, and chart-only wheel hash audit. | **77/77** Session 010 offline tests, **14/14** wheel hashes audited; **no** real build, launch, model-agent loop or generated chart. Feature branch **not merged**. |

### What we can and cannot claim at this checkpoint

**Verified:** The seed inventory and selected human-versus-model examples; the four current model API/schema handshakes; robust offline unit checks for the prospective controller, sandbox boundary, artifact protocols, and locked dependency *metadata*. The most recent documented Codespace checkpoint has a clean `feature/session-010-chart-agent-controller` working tree and successful hash audit.

**Not verified or completed:** downloading the hashed wheels; installing packages inside a chart image; pulling/building/running that image; full multi-turn chart creation by any of the three replacement agents; real Terra judgments across labeled runs; official Qwen3-VL predictions or an official macro-MCC; five original tasks with 15 human-reviewed runs; completed Harbor packages/mutants; or a final graded submission.

Our initial `gpt-5.4-mini` seed pilots are **not** evidence of Terra's performance. Session 009's Terra **schema** success is **not** evidence of Terra's classification accuracy. Offline unit-test totals and the 14-package audit are engineering checks, **not** MCC scores.

## 9. How do we finish without losing the purpose of Assignment 2?

We can keep studying the assignment's actual *evaluation methodology* with the APIs we have, **provided we preserve honest provenance and keep the official requirements visible**. The following order keeps implementation and evaluation logically separate.

### Step 1 — Finish a reproducible, safe chart environment (next offline task)

On `feature/session-010-chart-agent-controller`, update `integrations/chart_image_recipe.py` to copy the reviewed `requirements/chart-cp312-linux-amd64.txt` into the image and install packages with `pip --require-hashes --only-binary=:all:`. Update `integrations/chart_build_context.py` to stage **only** the approved lockfile alongside the existing vetted CSVs, Dockerfile and trusted extractor. Extend fake/offline tests for the requirement allowlist, tampering, hashes and cleanup; run the suite and check CI.

**Important limitation:** The minimal planned image currently specifies matplotlib, NumPy, pandas and Pillow, plus their dependencies. The course environment also mentions SciPy and seaborn as supported packages. Before running tasks that need either, explicitly add and verify appropriately pinned dependencies or state that our independent environment supports a narrower task subset. Do not imply that a smaller Docker image is identical to the course runtime.

Only **after** offline checks should we consider a separately reviewed, approved Docker build, actual wheel integrity/installation verification, library import/render smoke test, and sandbox launch. A Docker container with networking disabled is **not** a hardened security boundary.

### Step 2 — Prove one complete chart-making agent run

Connect the controller, provider adapter, sandbox gateway, task staging and PNG extraction through a **new explicitly gated host orchestration path**. Keep model requests and shell commands opt-in, one at a time, with exact role/model and command review, quotas, timeout/cleanup, no sandbox network access or API secrets, and full trajectory records. Start with a simple known task before trying all three agents.

Save a reproducible `result.json`, original inputs, and `figure.png` (or a documented execution failure). Match the official **run evidence/schema** as closely as possible, even if the generating models differ. Do not modify the upstream Modal runner silently; use a clearly named independent runner.

### Step 3 — Get a meaningful independent validator baseline

Wire the Terra adapter into an **experimental** validator that takes one run at a time, sees the task, inputs, trajectory and figure, and emits only the four official error families with concrete evidence. It must **not** receive `seed_labels.json`, a reference plot or predictions from other runs. Keep `validator/solution.py` / `validator/prediction.py` interface and official Qwen path separate unless intentionally implementing the strictly compliant track.

Freeze a baseline evaluator version, evaluate the released seed set (rather than two selected examples), and **only afterward** compare saved predictions with human labels. Report per-family TP/TN/FP/FN, four MCCs and macro-MCC, as well as dataset coverage and any request failures. If a complete run is not affordable or available, explicitly report the subset and avoid claiming a representative baseline.

Then implement at least two **justified evaluator changes** based on observed repeated mistakes, rerun the same cases, and analyze a false positive and false negative. Do not overfit the rubric to just seeds 004 and 008.

### Step 4 — Create genuinely new stress tests

Author **at least five** human-reviewable chart tasks spanning **two** suspected weakness classes (**at least two tasks in each class**). Generate **one** run per task from each of our **three current** chart-agent roles (at least **15 independent-adaptation runs**), freeze the tasks and model provenance, and inspect *every* trajectory/figure yourself.

Label errors independently with the official four-family rubric and terminal `execution_failure` rule. Evaluate the experimental judge against those labels; compute the same confusion matrices and MCCs. Treat results as evidence about **the API-backed agents and Terra**, **not** as a controlled replication of the prescribed Qwen/Ministral/GLM task-generation conditions. For a strictly course-conformant submission, repeat this step using the **three officially required agents**.

### Step 5 — Build Harbor verifiers and measure their blind spots

Package each authored task into `harbor/tasks/<task_id>/`. Require `plot.py` and `plotted_values.json` in the Harbor instructions without rewriting the original seeded chart specification. Create independent deterministic checks and a reference solution that earns **1.0**. Add two plausible wrong-answer mutants: one verifier **catches (0.0)** and one it **misses (1.0)**. Explain what this teaches us about the boundary between rule-based verifiers and visual/trajectory-aware validation.

Then make **at least one further validator improvement**, score both seed and authored runs again, explain successes/regressions, and prepare the report with actual evidence and model-provenance disclosures.

### Step 6 — Decide whether the deliverable is independent or strictly compliant

| Intended deliverable | Requirement before claiming completion |
| --- | --- |
| **Independent learning / research report** | The API-backed 3-agent workflow, independently labeled runs, Terra scoring, Harbor checks and honest limitations above; explicitly state this is **not official-model-equivalent**. |
| **Submission satisfying the original assignment rules** | Deploy/use **`Qwen/Qwen3-VL-30B-A3B-Instruct-FP8`** in the validator **and do not call a different judge model**, generate the required runs with **all three specified original agents**, preserve `validate(run)` and prediction schema, score and package the required artifacts, and pass `workflow check-submission`. Seek course approval for any exception; API access alone does not create one. |

**The key principle:** API limitations justify our *alternative implementation path*, but not silently changing the course's evaluation standard. We can preserve the educational goal with transparent adaptation; we cannot claim literal model-compliant grading without the prescribed models.

### Immediate next session (no paid API calls)

Continue on the **unmerged** `feature/session-010-chart-agent-controller` branch. Pull latest changes, re-run the 14-wheel offline audit, integrate its hash file into the Dockerfile and private build context, add tests, and validate offline before discussing a real build. **Do not rerun Session 009's live model probes**; their per-request authorizations were already consumed.

For exact restart commands and evidence, use `docs/Learning-Progress.md` (pause/resume checkpoint) and `docs/Session-010-Supply-Chain.md`. Documentation changes in this report alone do **not** authorize new model requests, Docker builds, sandbox launches or shell execution.

## 10. Where to look in the repository

| File/path | Purpose |
| --- | --- |
| [`ASSIGNMENT.md`](../ASSIGNMENT.md) | Official course objectives, exact required models, metrics, task counts and submission rules. |
| [`docs/Learning-Progress.md`](Learning-Progress.md) | Detailed history through Session 010 and the latest pause/resume checkpoint. |
| [`README.md`](../README.md) | The independent Codespaces workflow and safe/offline commands. |
| [`docs/Provider-Migration-Plan.md`](Provider-Migration-Plan.md) | Why we introduced hosted-provider adapters, message formats and research-scope limits. |
| [`docs/Session-009-Compatibility-Probes.md`](Session-009-Compatibility-Probes.md) | Individual live API checks and the free-GLM failure / paid-GLM substitution. |
| [`docs/Session-010-Controller-Design.md`](Session-010-Controller-Design.md) | Pure controller, fake-Docker gateway and artifact-handling design. |
| [`docs/Session-010-Supply-Chain.md`](Session-010-Supply-Chain.md) | OCI manifest evidence, hashed wheel metadata, verification limits and next offline change. |
| `integrations/models.py`; `integrations/providers/` | Current four experimental model IDs, API request builders and reply normalizers. |
| `integrations/judge.py` | Experimental Terra image + structured judgment adapter (not the official validator entry point). |
| `integrations/chart_controller.py`; `integrations/sandbox_gateway.py` | Offline controller and independently gated sandbox boundary. |
| `integrations/chart_image_recipe.py`; `integrations/chart_build_context.py` | Inert chart image recipe and allowlisted staging context. |
| `requirements/chart-cp312-linux-amd64.txt`; `scripts/check_chart_wheel_lock_offline.py` | Audited plotting wheel requirements and no-network consistency checker. |
| `artifacts/<run_id>/result.json` / `figure.png`; `inputs/<run_id>/` | Original seed task, trajectory, PNG and optional input evidence. |
| `seed_labels.json` | **Human reference labels**; never include them in judge inference. |
| `validator/solution.py`; `validator/prediction.py` | Official validator interface and output contract. |
| `workflow/generate.py`; `workflow/evaluate.py` | Original Modal generation path and label-vs-prediction scoring. |
| `tasks/`; `runs/`; `harbor/` | Future authored tasks, generated runs and deterministic verifier environments. |

### A small glossary

- **Generator / chart agent:** A model, prompt, tools and run loop working to produce a visualization.
- **Validator / judge:** The evaluator that returns named errors and concrete evidence for an individual run.
- **Official model:** The exact model identity prescribed by the course, not merely one with similar capabilities.
- **Experimental model:** Our API-accessible alternative, which can support learning but changes the benchmark conditions.
- **API compatibility probe:** One bounded test of model endpoint/request/response parsing; **not** a full chart run or accuracy measurement.
- **Controller:** A state machine that builds the next model request and records *approved* tool results.
- **Sandbox gateway:** The separately authorized interface through which a reviewed command might eventually reach Docker.
- **Trajectory:** The full agent messages, actions and tool results needed for later evaluation.
- **Human label:** An independently reviewed reference error family and supporting evidence.
- **TP, TN, FP, FN:** Correct detection, correct rejection, false alarm and missed error.
- **MCC / macro-MCC:** Classification measure per error family / its four-family average.
- **Harbor verifier:** Deterministic task checks, which can miss failures that remain visually obvious.
- **Hash-lock metadata audit:** A check that recorded dependency versions/hashes agree; **not** proof a package was downloaded, installed or safely executed.

---

## One-sentence takeaway

**We changed experimental models primarily because of the hosted APIs we can access, not because the assignment's objectives changed. The goal is still to build and stress-test a trustworthy validator of chart-making agents; to preserve that goal we need full agent trajectories, independent human labels, fair MCC evaluation, adversarial tasks and Harbor checks, while keeping substituted-model findings separate from any claim of strict official-model compliance.**
