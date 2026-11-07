# CMU 11-768 Assignment 2 — What We Are Building and What We Have Learned

**A beginner-friendly guide to our project, as of November 7, 2026**  
**Repository:** [cmu-11-768-assignment-2](https://github.com/xqzr2000/cmu-11-768-assignment-2)  
**Current work:** `feature/session-007-wrong-chart-precision` (unmerged at this checkpoint)  
**Sources:** the repository's `ASSIGNMENT.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/PHASE-0.md`, `docs/Learning-Progress.md`, `workflow/generate.py`, `workflow/evaluate.py`, and our recorded Codespace experiments.

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

### A simple picture of the workflow

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

## 3. Why Qwen, Z.ai, and OpenAI? Did we change the assignment's model?

**No: we have not replaced the official Qwen validator.** The three names show up in our story for different reasons.

### Qwen: the required official judge and one generator

The assignment **fixes** the validator's vision-language model to `Qwen3-VL-30B-A3B-Instruct-FP8`. Its fixed identity matters because students should improve the *evaluation design and logic*, not get a better score simply by swapping in a more powerful model. Official grading uses that same model family/checkpoint.

A different Qwen model, **Qwen2.5-Coder-3B**, is one of the three fixed **chart generators**. Those two Qwen models have different roles and must not be confused.

The course's normal setup uses **Modal** to host these models. Our independent project intentionally has not deployed the official validator this way, so **we do not have official Qwen baseline scores or macro-MCC yet**.

### Z.ai: an accessible provider for independent experiments

We had previously explored a Z.ai-hosted **GLM-4.7-Flash text model** in Assignment 1. In Assignment 2, we also tried **`glm-4.6v-flash`**, a *different* GLM model with image-understanding capability, as an **optional experimental judge**.

We chose that route because it provided an OpenAI-compatible API for exploring multimodal evaluation from Codespaces without first standing up the official large Qwen vision model on Modal. Its advertised pricing/free access made it an attractive experiment, but API availability, rate limits, and model output behavior are separate concerns. **Z.ai was not a course requirement for judging.**

We verified one small synthetic vision probe: it could inspect a generated bar chart. But the later full seed-004 evaluation did **not** produce a complete usable result. In subsequent diagnostics, the provider response/format and output-budget behavior did not satisfy our strict YES/NO pipeline. That is a **failed experimental integration**, not proof that the model is generally bad at reading charts.

**Important name difference:** `zai-org/GLM-4.7-Flash` is the course's third **generator** model; `glm-4.6v-flash` was our separate **experimental vision judge**. Their roles and versions differ.

### OpenAI: a more controllable experimental vision judge

After the Z.ai pilot's real-seed reliability problems, we added an isolated OpenAI API pilot using **`gpt-5.4-mini`**. We did this to test multimodal judging with **strict structured JSON output** such as:

```json
{
  "has_error": true,
  "evidence": "The chart omits a required source category."
}
```

That is easier to validate consistently than trying to interpret a free-form reply beginning with “YES” or “NO.” The pilot also supports **one deliberately authorized request at a time**, disabled automatic retries, offline previews, and **human-label comparison only after the answer has been saved**.

We changed **the model used in our research pilot**, **not** the model used for the official assignment submission. Results from GPT-5.4 Mini are informative for our learning, but **must not be presented as Qwen3-VL scores**. A ChatGPT subscription and OpenAI API billing are also separate things.

### What is our current infrastructure?

- **GitHub Codespaces**: editor, terminal, Python environment, Git and tests.
- **`uv`**: Python dependencies and commands.
- **Pinned Assignment 1 Docker sandbox dependency**: retained in our project for future local agent execution, **not yet wired into** the official generation workflow.
- **Existing `workflow/generate.py`**: still uses Modal; our local generation replacement is unfinished.
- **Model API pilots**: Z.ai and OpenAI experimentation only; both separate from the fixed official Qwen validator.

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

## 8. Our project progress so far: Sessions 001–007

| Session | What we did | Outcome / status |
| --- | --- | --- |
| **001 — Repo setup and study guide** | Imported the pinned full official starter, retained the published artifacts and labels, set up the independent repository and documented our plan. | Foundation established. |
| **002 — Offline dataset inspection** | Mapped the released runs, plots, CSVs and human labels; inspected selected cases and built dataset preflight checks. | 110 runs / 98 figures / 110 labels verified. |
| **003 — Validator wiring** | Created structural PNG validation and integrated baseline semantic questions with mock testing. | Offline tests exercised the interface; no real Qwen accuracy measurement. |
| **004 — First vision experiment** | Built and verified a bounded synthetic-image probe using Z.ai `glm-4.6v-flash`. | Simple image understanding worked; not a full seed evaluation. |
| **005 — Real-seed pilot** | Tried Z.ai on a real seed, encountered response/budget problems, then added a strict OpenAI structured-output pilot. | OpenAI seed 004: `wrong_data` TP, `wrong_chart` TP, `hard_to_read` TN. Explanations were not uniformly good. |
| **006 — Controlled seed 008** | Independently checked the CSV and plotted figure, then evaluated three families with GPT-5.4 Mini. | `wrong_data` TP, `hard_to_read` TP, `wrong_chart` **FP**. Documented why the chart-design accusation was unjustified. PR #7 merged. |
| **007 — Prompt precision experiment** | Added optional versioned `wrong_chart` rubric v2, independent result filenames and six new mock tests. Re-evaluated two known cases. | **v2:** seed 008 changed FP→TN, **but seed 004 changed TP→FN**. Regression documented; branch remains unmerged. |

### Verified engineering checkpoint

As of the last Codespace checks on November 7:

- **55 validator offline tests passed**, including the six new versioned-prompt tests.
- **5 dataset/infrastructure offline tests passed**.
- **Dataset preflight passed**: 110 released runs, 98 figures, 110 labels.
- The Session 007 branch was clean and synchronized after documentation commit **`28e30e1`**.
- The new **v2 prompt is only an experiment**; the official `validator/solution.py` and `validator/baseline.py` have **not** been updated to use it.
- The pilot prediction JSON files live in the **ignored local `output/` directory**. They are not necessarily on GitHub; preserve the Codespace or back them up safely before deleting it.

### What we can and cannot claim

**We can claim:** We loaded and checked the public dataset, exercised our validator plumbing offline, made controlled real-image model calls, identified both correct diagnoses and evaluator mistakes, and recorded an instructive **FP-versus-FN tradeoff**.

**We cannot claim:** That our official Qwen3-VL validator is accurate, that we have completed the full seed baseline sweep, that v2 is an improvement in general, that we have generated the 15 new agent runs, or that our self-authored Harbor tasks and mutants have passed evaluation. Those milestones remain to be done.

## 9. What comes next?

**First: improve the evaluation method, not simply force a better answer on two known plots.** A possible v3 approach is a requirement-by-requirement checklist: identify explicit chart requirements; check each against figure evidence *and* plotting operations; distinguish confirmed success, confirmed violation, and uncertainty; and avoid confusing data errors with design errors. Then test on independent positive and negative examples to avoid overfitting to seeds 004 and 008.

The broader assignment roadmap remains:

1. **Establish a full baseline:** Run the prescribed Qwen3-VL validator over the released seed set and compute all four confusion matrices, MCCs, and macro-MCC.
2. **Improve the actual validator:** Implement at least two justified changes in `validator/solution.py`, evaluate them against the baseline, and document FP/FN cases.
3. **Author adversarial tasks:** Create at least five tasks across two weakness classes (at least two tasks per class), run all three fixed chart agents on each (at least 15 runs), human-label the outputs, and score the validator.
4. **Package tasks in Harbor:** Create deterministic verifiers and reference solutions, verify expected scores, and include both a caught and an undetected mutant to analyze verifier limits.
5. **Iterate and report:** Improve the validator again, score seed and newly authored runs, and produce the required final report and submission artifacts.

Our independent infrastructure route still needs to be completed before we can run these official-model-equivalent experiments locally.

## 10. Where to look in the repository

| File/path | Purpose |
| --- | --- |
| [`ASSIGNMENT.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/ASSIGNMENT.md) | Authoritative course requirements and definitions. |
| [`docs/Learning-Progress.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/feature/session-007-wrong-chart-precision/docs/Learning-Progress.md) | Detailed chronological engineering journal. |
| [`README.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/feature/session-007-wrong-chart-precision/README.md) | Our independent setup, safety rules and experimental commands. |
| `artifacts/<run_id>/result.json` | Released task and agent trajectory. |
| `artifacts/<run_id>/figure.png` | Agent-generated figure, if present. |
| `inputs/<run_id>/*.csv` | Released task input CSVs, when required. |
| `seed_labels.json` | Released **human error annotations**, never an inference input. |
| `validator/runner.py` | Loads runs and invokes the validator. |
| `validator/solution.py` | Our main official validator entry point. |
| `validator/baseline.py` | Starter semantic judge questions and multimodal call path. |
| `validator/model.py` | Official model endpoint configuration and client. |
| `scripts/zai_seed_pilot.py` | Independent Z.ai image-judge experiment. |
| `scripts/openai_seed_pilot.py` | Independent OpenAI experiment, with v1/v2 prompt versions. |
| `workflow/generate.py` | Official fixed three-agent generation workflow (still Modal-based). |
| `workflow/evaluate.py` | Compares human labels with predictions and computes MCC. |
| `harbor/` | Example and template for future deterministic evaluation tasks. |

### A small glossary

- **Run:** One attempt by one chart-making agent on a task.
- **Trajectory:** The actions/messages/tool calls during that attempt.
- **Artifact:** A saved output such as `result.json` or `figure.png`.
- **Validator / judge:** The checker that produces error predictions.
- **Ground truth / human label:** The human-reviewed reference for whether an error was present.
- **Confusion matrix:** Counts of correct detections, correct rejections, false alarms and misses.
- **MCC:** A metric derived from those counts; balances positive and negative performance.
- **Macro-MCC:** Average MCC across the four error families.
- **Pilot:** A deliberately small experiment to learn about behavior and integration, not a complete benchmark.
- **Regression:** A previously correct case becomes incorrect after a change.
- **Harbor verifier:** Deterministic tests of a task's submitted files or values, rather than a model's free-form visual judgment.

---

## One-sentence takeaway

**We are building a reliable judge for AI-generated visualizations: three prescribed agents will make charts, our validator must find their mistakes using the task, data, trajectory and image, and human-reviewed error labels let us measure when the judge itself is right or wrong. Our recent progress has shown that eliminating false alarms is not enough—we must also avoid missing real errors.**
