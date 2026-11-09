# Repository Tree and File-by-File Guide

**Repository:** [xqzr2000/cmu-11-768-assignment-2](https://github.com/xqzr2000/cmu-11-768-assignment-2)  
**Snapshot:** `main`, inspected November 9, 2026. GitHub tree-object SHA: `d8ed1f9ab23f215cbfb91f8082765034d315b069`.  
**Coverage:** **505 tracked files** in **725 total tree entries** (files and directories), including **110 seed-run result files, 98 seed PNGs, 15 newly generated agent runs, and 5 authored Harbor tasks**.  
**Purpose:** Explain what exists, why it exists, whether the adapted project needs it, and which material is mainly a learning or experiment record.

> **Scope of “necessary”:** A file can be unnecessary for starting the final validator yet still be essential to *reproduce the experiment*, *prove an assignment requirement*, or *rebuild the grading tasks*. Do not delete a file merely because a Python program does not import it. This is a classification and a reading guide, **not** a cleanup or deletion instruction. The final scores were reported in this repository's README; they were not freshly rerun for this guide.

## Contents

1. [Quick answer: what to keep and what is historical](#1-quick-answer-what-to-keep-and-what-is-historical)
2. [How the project works](#2-how-the-project-works)
3. [Full repository tree (every tracked file)](#3-full-repository-tree-every-tracked-file)
4. [Core source files: explanation and necessity](#4-core-source-files-explanation-and-necessity)
5. [Original seed dataset, authored tasks, and produced runs](#5-original-seed-dataset-authored-tasks-and-produced-runs)
6. [Harbor verifier: explain the repeated files](#6-harbor-verifier-explain-the-repeated-files)
7. [Scripts, tests, development setup, and documentation](#7-scripts-tests-development-setup-and-documentation)
8. [Generated outputs: which to keep](#8-generated-outputs-which-to-keep)
9. [Reading order, safe commands, and cleanup advice](#9-reading-order-safe-commands-and-cleanup-advice)
10. [Appendix: every individual file classified](#10-appendix-every-individual-file-classified)

## 1. Quick answer: what to keep and what is historical

| Mark | Meaning | Necessary to run the **adapted** program? | Keep in repository? |
| --- | --- | --- | --- |
| **CORE** | Actual code or task definition in the completed adapted workflow | Usually **yes**, for the relevant step | **Yes** |
| **SUPPORT** | Setup, lockfile, safety checks, unit tests, grading utilities | **Conditional**: needed for setup/test/reproduce | **Yes**, strongly recommended |
| **DATA** | Original published evidence or human labels | **Conditional**: essential for seed scoring/comparison | **Yes** |
| **RESULT** | Completed figures, trajectories, predictions, metrics, proof | **No** for a fresh run; **yes** to inspect the completed experiment | **Yes** for the assignment record |
| **HISTORY** | Upstream Modal path, earlier plans, archived docs, past probes | **No** for the adapted normal path | Usually **yes** for learning/provenance; optional in a streamlined product |
| **TEMPLATE** | An example or scaffold used to produce other files | **No**, once outputs exist; **yes** to repeat creation | **Yes**, for regeneration and teaching |

**Minimal mental model:** `tasks/` describes **what to draw** → `workflow/sandbox_generate.py` and `sandbox/` orchestrate **agents drawing it** → `runs/` captures **what they actually did** → `validator/solution.py` judges **what went wrong** → `labels.json` contains **human judgments** → `workflow/evaluate.py` measures **how well the validator matches humans** → `harbor/tasks/` verifies **specific outputs deterministically** → `report.tex`/`report.pdf` document **the results**.

### Critical distinctions

- **`artifacts/` is not disposable output.** It is the original assignment's released dataset: historical visualization-agent trajectories and figures. It is necessary to reproduce Part 1/2 seed evaluation.
- **`runs/` is output, but important experimental evidence.** It holds your 5 tasks × 3 agent results for Part 3. You can generate another set, but you should preserve the recorded evaluated set.
- **`output/` is evaluation evidence, not the agent's source code.** The prediction files and score files make the reported findings inspectable without paying for fresh model calls.
- **`infrastructure/` and the original `workflow/generate.py` are the upstream Modal approach.** Your independent implementation uses the Docker/hosted-API route. Do not assume `python -m workflow generate` invokes the Docker replacement.
- **`docs/Learning-Progress.md` and the dated `docs/Session-*.md` are a study journal and engineering history.** They teach what happened and why; they do not execute the model.
- **`integrations/chart_*.py` includes offline-only planning/auditing experiments.** Read their docstrings carefully: preparing an image recipe or a build-context *plan* is not the same as actually building or launching Docker.
- **`report.pdf`, `report.tex`, `README.md` and `AI_USAGE.md` are deliverables and disclosures.** They are not runtime dependencies, but they should be kept.

## 2. How the project works

### A. Evaluate the original seed runs (Parts 1–2)

```text
artifacts/<run-id>/result.json  +  optional figure.png
inputs/<run-id>/*.csv           +  original task details
                         |
                         v
             validator/runner.py
               |             |
               v             v
      validator/baseline.py   validator/solution.py
               \             /
                \-- validator/model.py --> hosted vision judge
                         |
                         v
              output/*_predictions.json
                         |
           seed_labels.json (human reference)
                         |
                         v
                  workflow/evaluate.py
                         |
                         v
                 output/*_score.txt
```

`validator/solution.py` first checks whether a usable final PNG exists; then its structured judge distinguishes **wrong data** from **wrong chart/design**, and separately reviews **hard-to-read** visual content. It must **not** receive the human labels when making a prediction. The labels are used only *afterward* to score it.

### B. Produce and evaluate new tasks (Part 3)

```text
tasks/<name>/task.json  +  optional input CSVs
                   |
                   v
workflow/sandbox_generate.py   --> model API (host-side key)
                   |
                   v
sandbox/Dockerfile             --> isolated Docker workspace (no key)
                   |
                   v
runs/<name>__<agent>/result.json + figure.png + input snapshots
                   |
                   v
validator/runner.py + labels.json + workflow/evaluate.py
                   |
                   v
scripts/build_harbor_tasks.py / workflow/package.py
                   |
                   v
harbor/tasks/<name>/ --> oracle, mutants, deterministic tests
```

The sandbox **executes model-proposed plotting commands**, but the API credentials remain with the host-side runner, not in the execution container. Harbor uses a *different* containerized verification workflow to test whether produced figures and accompanying calculation files meet requirements.

### C. The four error families

| Error family | Question it answers | Main evidence |
| --- | --- | --- |
| `execution_failure` | Did the agent fail to produce a valid final figure? | Artifact existence and PNG validity |
| `wrong_data` | Are quantities, aggregation, or represented values wrong? | Task, CSVs, recorded work, chart |
| `wrong_chart` | Is the design/type/structure different from the requested chart? | Task and chart/trajectory |
| `hard_to_read` | Is information illegible, clipped, obstructed, or unreadable? | Rendered figure |

A validator mistake is not the same thing as a chart-agent mistake. For instance, an agent can produce a perfectly good figure and a validator can incorrectly accuse it of `wrong_chart`.

## 3. Full repository tree (every tracked file)

This is the **complete** Git-tracked tree from the inspected `main` snapshot, not an invented sketch. It intentionally includes historical and generated files. A directory shown in the tree is inferred from tracked paths. `.venv`, `.env`, caches, local `jobs/`, and untracked local outputs are **not** included.

```text
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
│   ├── Progress-Explained-20261107.md
│   ├── Provider-Migration-Plan.md
│   ├── README-Development-History.md
│   ├── report-notes.md
│   ├── Session-009-Compatibility-Probes.md
│   ├── Session-010-Controller-Design.md
│   ├── Session-010-Supply-Chain.md
│   ├── Session-012-Docker-Smoke-Preflight.md
│   ├── Session-013-Docker-Smoke-Readiness.md
│   ├── Session-014-Chart-Worker-Image-Staging.md
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
│   │   │   ├── test.sh
│   │   │   └── test_state.py
│   │   ├── instruction.md
│   │   ├── README.md
│   │   └── task.toml
│   ├── reference/
│   │   └── README.md
│   ├── shared/
│   │   └── verifier_core.py
│   ├── tasks/
│   │   ├── dense-department-budgets/
│   │   │   ├── environment/
│   │   │   │   └── Dockerfile
│   │   │   ├── mutants/
│   │   │   │   └── unrotated_labels/
│   │   │   │       └── solve.sh
│   │   │   ├── solution/
│   │   │   │   └── solve.sh
│   │   │   ├── tests/
│   │   │   │   ├── figure_manifest.py
│   │   │   │   ├── sitecustomize.py
│   │   │   │   ├── test.sh
│   │   │   │   ├── test_state.py
│   │   │   │   └── verifier_core.py
│   │   │   ├── instruction.md
│   │   │   └── task.toml
│   │   ├── quarterly-revenue-by-region/
│   │   │   ├── environment/
│   │   │   │   ├── Dockerfile
│   │   │   │   └── transactions.csv
│   │   │   ├── mutants/
│   │   │   │   └── sum_units/
│   │   │   │       └── solve.sh
│   │   │   ├── solution/
│   │   │   │   └── solve.sh
│   │   │   ├── tests/
│   │   │   │   ├── figure_manifest.py
│   │   │   │   ├── sitecustomize.py
│   │   │   │   ├── test.sh
│   │   │   │   ├── test_state.py
│   │   │   │   └── verifier_core.py
│   │   │   ├── instruction.md
│   │   │   └── task.toml
│   │   ├── sensor-daily-median/
│   │   │   ├── environment/
│   │   │   │   ├── Dockerfile
│   │   │   │   └── sensors.csv
│   │   │   ├── solution/
│   │   │   │   └── solve.sh
│   │   │   ├── tests/
│   │   │   │   ├── figure_manifest.py
│   │   │   │   ├── sitecustomize.py
│   │   │   │   ├── test.sh
│   │   │   │   ├── test_state.py
│   │   │   │   └── verifier_core.py
│   │   │   ├── instruction.md
│   │   │   └── task.toml
│   │   ├── styled-decay-curves/
│   │   │   ├── environment/
│   │   │   │   └── Dockerfile
│   │   │   ├── solution/
│   │   │   │   └── solve.sh
│   │   │   ├── tests/
│   │   │   │   ├── figure_manifest.py
│   │   │   │   ├── sitecustomize.py
│   │   │   │   ├── test.sh
│   │   │   │   ├── test_state.py
│   │   │   │   └── verifier_core.py
│   │   │   ├── instruction.md
│   │   │   └── task.toml
│   │   └── top-products-unit-share/
│   │       ├── environment/
│   │       │   ├── Dockerfile
│   │       │   └── transactions.csv
│   │       ├── solution/
│   │       │   └── solve.sh
│   │       ├── tests/
│   │       │   ├── figure_manifest.py
│   │       │   ├── sitecustomize.py
│   │       │   ├── test.sh
│   │       │   ├── test_state.py
│   │       │   └── verifier_core.py
│   │       ├── instruction.md
│   │       └── task.toml
│   ├── template/
│   │   ├── environment/
│   │   │   └── Dockerfile
│   │   ├── solution/
│   │   │   └── solve.sh
│   │   ├── tests/
│   │   │   ├── test.sh
│   │   │   └── test_state.py
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
├── integrations/
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── client.py
│   │   ├── deepseek.py
│   │   ├── openai.py
│   │   └── zai.py
│   ├── __init__.py
│   ├── chart_build_context.py
│   ├── chart_controller.py
│   ├── chart_image_recipe.py
│   ├── chart_transfer.py
│   ├── chart_wheel_lock.py
│   ├── judge.py
│   ├── models.py
│   ├── sandbox_gateway.py
│   └── task_artifacts.py
├── output/
│   ├── .gitkeep
│   ├── authored_predictions.json
│   ├── authored_score.txt
│   ├── baseline_predictions.json
│   ├── baseline_score.txt
│   ├── check_submission.txt
│   ├── final_seed_predictions.json
│   ├── final_seed_score.txt
│   ├── part4a_authored_predictions.json
│   ├── part4a_authored_score.txt
│   ├── part4a_seed_predictions.json
│   ├── part4a_seed_score.txt
│   ├── part4b_authored_predictions.json
│   ├── part4b_authored_score.txt
│   ├── part4b_seed_predictions.json
│   ├── part4b_seed_score.txt
│   ├── pre_iteration_authored_predictions.json
│   ├── pre_iteration_authored_score.txt
│   ├── pre_iteration_seed_predictions.json
│   ├── pre_iteration_seed_score.txt
│   ├── provider_compat_agent_a.json
│   ├── provider_compat_agent_b.json
│   ├── provider_compat_agent_c.json
│   ├── provider_compat_agent_c_glm-5.3-flash.json
│   ├── provider_compat_experimental_judge_gpt-6.1-terra.json
│   ├── session005_openai_004_hard_to_read_decision.json
│   ├── session005_openai_004_wrong_chart_decision.json
│   ├── session005_openai_004_wrong_data_decision.json
│   ├── session005_openai_008_hard_to_read_decision.json
│   ├── session005_openai_008_wrong_chart_decision.json
│   ├── session005_openai_008_wrong_data_decision.json
│   ├── session007_openai_004_wrong_chart_v2_decision.json
│   └── session007_openai_008_wrong_chart_v2_decision.json
├── requirements/
│   └── chart-cp312-linux-amd64.txt
├── runs/
│   ├── dense-department-budgets__deepseek/
│   │   ├── figure.png
│   │   └── result.json
│   ├── dense-department-budgets__glm/
│   │   ├── figure.png
│   │   └── result.json
│   ├── dense-department-budgets__luna/
│   │   ├── figure.png
│   │   └── result.json
│   ├── quarterly-revenue-by-region__deepseek/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── quarterly-revenue-by-region__glm/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── quarterly-revenue-by-region__luna/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── sensor-daily-median__deepseek/
│   │   ├── inputs/
│   │   │   └── sensors.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── sensor-daily-median__glm/
│   │   ├── inputs/
│   │   │   └── sensors.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── sensor-daily-median__luna/
│   │   ├── inputs/
│   │   │   └── sensors.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── styled-decay-curves__deepseek/
│   │   ├── figure.png
│   │   └── result.json
│   ├── styled-decay-curves__glm/
│   │   ├── figure.png
│   │   └── result.json
│   ├── styled-decay-curves__luna/
│   │   ├── figure.png
│   │   └── result.json
│   ├── top-products-unit-share__deepseek/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── top-products-unit-share__glm/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   ├── figure.png
│   │   └── result.json
│   ├── top-products-unit-share__luna/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   ├── figure.png
│   │   └── result.json
│   └── .gitkeep
├── sandbox/
│   ├── Dockerfile
│   ├── instance_suffix.txt
│   └── requirements.txt
├── scripts/
│   ├── __init__.py
│   ├── build_harbor_tasks.py
│   ├── chart_smoke_worker.py
│   ├── check_chart_build_context_offline.py
│   ├── check_chart_image_recipe_offline.py
│   ├── check_chart_smoke_preview_offline.py
│   ├── check_chart_smoke_worker_offline.py
│   ├── check_chart_transfer_offline.py
│   ├── check_chart_wheel_lock_offline.py
│   ├── check_controller_offline.py
│   ├── check_sandbox_gateway_offline.py
│   ├── check_task_artifacts_offline.py
│   ├── deploy_agent_runner.sh
│   ├── deploy_generation_models.sh
│   ├── deploy_validator_model.sh
│   ├── disagreements.py
│   ├── figure_extract_worker.py
│   ├── judge_cost.py
│   ├── judge_smoke.py
│   ├── make_part3_inputs.py
│   ├── offline_preflight.py
│   ├── openai_seed_pilot.py
│   ├── preview_chart_smoke_offline.py
│   ├── provider_compat_probe.py
│   ├── provider_preflight.py
│   └── zai_vision_probe.py
├── tasks/
│   ├── dense-department-budgets/
│   │   └── task.json
│   ├── quarterly-revenue-by-region/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   └── task.json
│   ├── sensor-daily-median/
│   │   ├── inputs/
│   │   │   └── sensors.csv
│   │   └── task.json
│   ├── styled-decay-curves/
│   │   └── task.json
│   ├── top-products-unit-share/
│   │   ├── inputs/
│   │   │   └── transactions.csv
│   │   └── task.json
│   └── .gitkeep
├── tests/
│   ├── test_chart_build_context_offline.py
│   ├── test_chart_image_recipe_offline.py
│   ├── test_chart_smoke_preview_offline.py
│   ├── test_chart_smoke_worker_offline.py
│   ├── test_chart_transfer_offline.py
│   ├── test_controller_state_offline.py
│   ├── test_offline_preflight.py
│   ├── test_provider_compat_probe_offline.py
│   ├── test_provider_deepseek_offline.py
│   ├── test_provider_openai_offline.py
│   ├── test_provider_registry_offline.py
│   ├── test_provider_zai_offline.py
│   ├── test_sandbox_gateway_offline.py
│   ├── test_sandbox_generate_offline.py
│   ├── test_task_artifacts_offline.py
│   ├── test_validator_openai_seed_offline.py
│   ├── test_validator_semantic_offline.py
│   ├── test_validator_solution_offline.py
│   └── test_validator_vision_probe_offline.py
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
│   ├── sandbox_generate.py
│   ├── submission.py
│   └── tasks.py
├── .env.example
├── .env.local.example
├── .gitattributes
├── .gitignore
├── .python-version
├── AI_USAGE.md
├── ASSIGNMENT.md
├── labels.example.json
├── labels.json
├── pyproject.toml
├── README.md
├── report.pdf
├── report.tex
├── report_template.tex
├── seed_labels.json
└── uv.lock
```

The next sections explain the tree. Repeated layouts such as 110 seed folders and 15 agent-run folders use the *same file semantics*. The appendix still lists/classifies **every tracked file individually**.

## 4. Core source files: explanation and necessity

### `validator/`: the main AI evaluator

| File | Does | Classification |
| --- | --- | --- |
| `validator/__init__.py` | Makes this folder an importable Python package. | **CORE** — package plumbing |
| `validator/baseline.py` | Original-style validator for comparison. Questions the judge about execution, data/chart, and readability; includes prompt/context/image compaction. | **SUPPORT** — needed to reproduce the **baseline**, not the final evaluator's normal execution |
| `validator/solution.py` | **Your final submitted validator.** Validates the PNG, extracts compact trajectory/input evidence, uses structured requirement checks for data/design, and a separate image-first readability review. | **CORE** — essential |
| `validator/model.py` | Makes requests to the hosted judge using the configurable OpenAI-compatible client; handles model URL, key, and request options. | **CORE** — essential for live judgment |
| `validator/prediction.py` | Defines valid prediction schema (`ErrorFamily`, `Error`, `Prediction`, `PredictionFile`) with Pydantic. Prevents malformed outputs. | **CORE** — essential |
| `validator/runner.py` | Finds seed or authored runs, calls the chosen validator, validates and writes prediction files, supports retries/resume. | **CORE** — essential for batch evaluation |

**Teaching point:** `baseline.py` and `solution.py` are **alternatives**, not two sequential stages. The runner selects the module. `prediction.py` defines the *shape* of results, while `model.py` handles the *remote call*.

### `workflow/`: project commands and scoring

| File | Does | Classification |
| --- | --- | --- |
| `workflow/__init__.py` | Defines the importable package namespace. | **CORE** |
| `workflow/__main__.py` | Dispatches `python -m workflow` subcommands such as `score`, `validate-tasks`, `package`, `check-submission`. | **CORE** |
| `workflow/evaluate.py` | Creates/checks human-label files and scores predictions using per-family MCC (Matthews correlation coefficient). | **CORE** — for results/scoring |
| `workflow/tasks.py` | Loads and validates `tasks/*/task.json`, ensuring IDs and input paths are well formed and safe. | **CORE** |
| `workflow/sandbox_generate.py` | **Adapted live generation runner.** Calls the three hosted models, drives the bounded command/tool loop, uses sandbox workspaces, saves run trajectories/figures and input snapshots. | **CORE** — for new live generation |
| `workflow/package.py` | Converts a task descriptor into the Harbor folder scaffold; does not author the full solution or verifier for you. | **SUPPORT/TEMPLATE** — needed if rebuilding packaged tasks |
| `workflow/harbor_rewards.py` | Runs Harbor's real oracles and mutants and reads their reward values. Requires Docker. | **CORE** — for complete submission verification |
| `workflow/submission.py` | Verifies the whole adapted submission: tasks, runs, labels, packaging and (unless skipped) Harbor results. | **CORE** — for final checks |
| `workflow/generate.py` | Retained original Modal/mini-SWE-agent generation route. It is **not** the Docker-based runner. | **HISTORY** — keep as upstream reference |

**Teaching point:** a module's path is not enough to know what executes. The generic `workflow generate` command still points to `workflow/generate.py`; for your adapted Docker experiment, the README uses **`python -m workflow.sandbox_generate`** explicitly.

### `integrations/`: provider compatibility and offline-first engineering

| File | Does | Classification |
| --- | --- | --- |
| `integrations/__init__.py` | Package initializer. | **SUPPORT** |
| `integrations/models.py` | Registry of roles, provider names, model IDs, API styles, and key variable names. | **CORE/SUPPORT** — shared model configuration |
| `integrations/providers/__init__.py` | Exposes provider-adapter interfaces. | **SUPPORT** |
| `integrations/providers/base.py` | Normalizes different providers' replies and tool calls into consistent internal records. | **SUPPORT** — crucial for provider-controller experiments |
| `integrations/providers/client.py` | Validates/previews requests and performs a deliberately opt-in single live request when authorized. | **SUPPORT** — compatibility layer |
| `integrations/providers/deepseek.py` | Builds DeepSeek Responses-style requests, replaying full history rather than relying on stored response IDs. | **SUPPORT** |
| `integrations/providers/openai.py` | Builds OpenAI Responses-style requests, including strict judge JSON schema when appropriate. | **SUPPORT** |
| `integrations/providers/zai.py` | Builds Z.ai Chat Completions-style requests. | **SUPPORT** |
| `integrations/judge.py` | Experimental image/JSON judgment payload helpers; explicitly **not** the implementation of `validator.solution.validate`. | **HISTORY/SUPPORT** — research helper |
| `integrations/chart_controller.py` | Pure state machine for agent turns, tool proposals and budgets; it does not itself make network/Docker calls. | **SUPPORT** — controller design and tests |
| `integrations/sandbox_gateway.py` | Explicitly approved gateway/proposal layer for the pinned Assignment 1 sandbox; guards operations and limits. | **SUPPORT** — safety architecture |
| `integrations/task_artifacts.py` | Checks CSV input snapshots, PNG validity/size and transfer envelopes. | **SUPPORT** — artifact safety |
| `integrations/chart_transfer.py` | Previews/stages vetted CSV snapshots and the trusted PNG extraction plan, without launching Docker. | **SUPPORT** — offline integration experiment |
| `integrations/chart_image_recipe.py` | Plans a fixed chart-capable Dockerfile from a digest-shaped base reference; does **not** build the image. | **SUPPORT/HISTORY** |
| `integrations/chart_build_context.py` | Assembles and verifies an allowlisted temporary Docker build context (Dockerfile, trusted scripts, wheel hashes, CSVs). | **SUPPORT** — offline integrity |
| `integrations/chart_wheel_lock.py` | Audits Python wheel hashes/metadata in `uv.lock` against the chart-only requirements file. | **SUPPORT** — reproducibility/security |

The `integrations/` work documents a careful progressive design. Some modules participate in provider configuration and experimental probes; some are *offline-only plans* and should not be mistaken for your actual live agent loop or your final validator.

### Root files and final deliverables

| File | Does | Classification |
| --- | --- | --- |
| `README.md` | Current project explanation: course-versus-adaptation, architecture, methods, evidence, results and commands. | **SUPPORT** — primary public entry point |
| `ASSIGNMENT.md` | Original CMU task statement and required contracts. | **DATA/SUPPORT** — reference standard, not runnable |
| `AI_USAGE.md` | Discloses AI assistants and experimental models used in the project. | **SUPPORT** — transparency |
| `report.tex` | Your written final report as editable LaTeX source. | **SUPPORT/DELIVERABLE** |
| `report.pdf` | Compiled final report for reading/submission. | **RESULT/DELIVERABLE** |
| `report_template.tex` | Blank original report scaffold. | **TEMPLATE/HISTORY** |
| `pyproject.toml` | Python package metadata, minimum Python 3.12, dependencies, build settings; pins Assignment 1 sandbox via Git URL. | **CORE** — install/setup |
| `uv.lock` | Fully resolved Python dependency graph, used by `uv sync --locked`. | **CORE/SUPPORT** — reproducibility |
| `.python-version` | Preferred Python version for uv/other environment tools. | **SUPPORT** |
| `.env.example` | Example settings for Modal (upstream) and independent hosted-judge configuration. Not a secret file. | **SUPPORT** |
| `.env.local.example` | Local experimental Z.ai configuration example, retained from an early phase. | **HISTORY/SUPPORT** |
| `.gitignore` | Tells Git not to track `.env`, virtual envs, caches, Harbor `jobs/`, and local usage logs. | **SUPPORT** |
| `.gitattributes` | Normalizes shell and CSV line endings to LF; important for portable Harbor scripts and CSV hashes. | **SUPPORT** |
| `labels.example.json` | Example shape of a human-label file. | **TEMPLATE** |
| `seed_labels.json` | Human reference labels for the original 110 released runs. **Never pass them to the live judge.** | **DATA** — essential for Part 1/2 scoring |
| `labels.json` | Human-reviewed labels for the 15 authored runs. **Never pass them to the live judge.** | **DATA** — essential for Part 3 scoring |

### `sandbox/`: actual chart-making execution environment

| File | Does | Classification |
| --- | --- | --- |
| `sandbox/Dockerfile` | Pinned Python 3.12 plotting image; installs only hash-constrained packages, sets a non-root runtime and headless Matplotlib. | **CORE** — build the live chart-agent sandbox |
| `sandbox/requirements.txt` | Hash-locked packages used in that Docker image. | **CORE** — image reproducibility |
| `sandbox/instance_suffix.txt` | Work instructions appended to the chart agent's prompt, including the exact completion-marker command. | **CORE** — run protocol |
| `requirements/chart-cp312-linux-amd64.txt` | Smaller chart-only CPython 3.12/Linux x86-64 hashed wheel manifest used by offline recipe/build-context auditing. | **SUPPORT** — not the same as `sandbox/requirements.txt` |

**Teaching point:** the Dockerfile describes **the image's contents**. `workflow/sandbox_generate.py` controls **how a container is used**. Neither stores API keys in the sandbox; credentials stay in the runner process. The separate `integrations/chart_image_recipe.py` is an offline planning module, not proof that an alternate image has been built.

## 5. Original seed dataset, authored tasks, and produced runs

### `artifacts/`: supplied public evaluation dataset — **DATA**

There are **110** `artifacts/<three-digit-run-id>/result.json` files and **98** `figure.png` files. The 12 figure-less runs are `001`, `010`, `053`, `065`, `089`, `096`, `103`, `145`, `168`, `171`, `181`, and `208`. This matters because an absent valid figure is itself evidence of `execution_failure`.

| Repeated file | What is inside | Necessary? |
| --- | --- | --- |
| `artifacts/NNN/result.json` | The released seed run: the original user task/instruction, agent trajectory/messages/actions, and recorded outcome. | **Yes** for reproducing seed evaluation |
| `artifacts/NNN/figure.png` | Final chart produced by the released agent, if any. | **Yes** when present, as visual judging evidence |
| `inputs/NNN/data.csv` | Task-specific original tabular input for some seed runs. | **Yes** for data-grounded evaluation of these runs |
| `inputs/080/checkouts.csv`, `inputs/125/checkouts.csv` | Named checkout datasets for two seed examples. | **Yes** for those seed tasks |

**Never manufacture a missing figure** or treat it as a directory error. Also, do not mix up these `artifacts/` (original released agent runs) with `runs/` (your independently generated Part 3 agent runs).

### `tasks/`: the five tasks your team authored — **CORE**

| Directory and descriptor | What the agent is asked to do | Necessity |
| --- | --- | --- |
| `tasks/dense-department-budgets/task.json` | Plot 30 department budgets with long, exact, readable x-axis labels; adversarial **visual detail/legibility** task. | **CORE** |
| `tasks/quarterly-revenue-by-region/task.json` | Calculate **revenue = units × unit_price**, aggregate by quarter/region and draw grouped bars; adversarial large-input aggregation. | **CORE** |
| `tasks/sensor-daily-median/task.json` | Calculate daily **medians** for sensors S1/S2, handle missing temperatures and shade S2 ranges; adversarial statistics/readability. | **CORE** |
| `tasks/styled-decay-curves/task.json` | Plot three exponential decays with exact line/marker styles and logarithmic y axis; adversarial visual-specification precision. | **CORE** |
| `tasks/top-products-unit-share/task.json` | Compute product unit share of **all** products, display only top eight horizontal bars; adversarial denominator/order correctness. | **CORE** |
| `tasks/<name>/inputs/*.csv` | Deterministically created transaction/sensor datasets fed to tasks that need them. | **CORE** for the three data-based tasks |
| `tasks/.gitkeep` | Ensures empty `tasks/` can exist as a tracked directory before task files are added. | **HISTORY/MAINTENANCE** — no runtime role now |

`task.json` is a **machine-readable task descriptor**, not agent output. It declares instructions, input names/paths, and a task class. The chart-making agent sees the task; then `runs/` stores its answer.

### `runs/`: 15 authored agent trajectories — **RESULT**

The five authored tasks were each run with **three** agents: `deepseek`, `glm`, and `luna`. Thus each `<task>__<agent>` directory identifies *one task-and-agent attempt*.

| Repeated path | What it records | Necessary? |
| --- | --- | --- |
| `runs/<task>__<agent>/result.json` | The agent trajectory and result, compatible with `validator/runner.py`. | **RESULT** — not source code, but needed to inspect/score the recorded attempts |
| `runs/<task>__<agent>/figure.png` | The chart that the named agent actually produced. | **RESULT** — important judge and human-review evidence |
| `runs/<task>__<agent>/inputs/<file>.csv` | The input snapshot saved alongside that particular run. | **RESULT/SUPPORT** — enables audit/replay without guessing the input |
| `runs/.gitkeep` | Placeholder file from initial scaffold. | **HISTORY/MAINTENANCE** |

The 15 directories are intentional; they are not 15 versions of the same code. They test whether models with different reasoning and plotting behaviors produce different error patterns.

## 6. Harbor verifier: explain the repeated files

Harbor is the **deterministic grading harness** for the five authored tasks. The LLM judge checks broad task correctness; Harbor instead executes reference solutions and verifiers inside containerized task environments. Harbor tasks are not the same thing as `tasks/<name>/task.json`.

### Files in each of the five `harbor/tasks/<task-name>/` directories

| Repeated file | Exactly what it does | Classification |
| --- | --- | --- |
| `task.toml` | Harbor's task ID, version, output artifact list, metadata, runtime and verifier timeouts. | **CORE** — grading configuration |
| `instruction.md` | Task instructions for the agent in the Harbor environment; also describes required outputs. | **CORE** |
| `environment/Dockerfile` | Builds the task's verifier/agent environment. | **CORE** |
| `environment/*.csv` (three tasks only) | Dataset copied into the Harbor task image. | **CORE** for data tasks |
| `solution/solve.sh` | **Oracle**: a reference solution intended to succeed on that task. | **CORE** for grader self-tests |
| `tests/test.sh` | Shell entry point used by Harbor to run the verifier. | **CORE** |
| `tests/test_state.py` | Actual task-specific `pytest` checks: values, chart structure, dimensions, script/figure presence and sidecar correctness as appropriate. | **CORE** |
| `tests/figure_manifest.py` | Instrumentation for extracting structured Matplotlib figure/axes/artists data during verification. | **CORE** for these verifiers |
| `tests/sitecustomize.py` | Python hook loader that installs instrumentation early in a verifier-side rerun. | **CORE** for these verifiers |
| `tests/verifier_core.py` | Packaged copy of shared verification helpers; Harbor ships the task's own tests directory. | **CORE** |
| `mutants/.../solve.sh` (two tasks) | Deliberately **incorrect** solutions used to test the verifier's ability to reject mistakes. | **SUPPORT** — grading/verifier diagnostics |

The named mutants are **`sum_units`** under `quarterly-revenue-by-region` (wrong aggregation) and **`unrotated_labels`** under `dense-department-budgets` (a readability defect). The recorded `output/check_submission.txt` reports the oracle score as **1.0 on all five tasks**, `sum_units` as **0.0** (correctly rejected), and `unrotated_labels` as **1.0** (incorrectly accepted). **A passing submission check does not mean the verifier catches every possible error**; that latter observation is a documented blind spot.

### Other files in `harbor/`

| File or group | Role | Classification |
| --- | --- | --- |
| `harbor/README.md` | Explains how to package tasks, run oracles/mutants, and check grades. | **SUPPORT** |
| `harbor/TROUBLESHOOTING.md` | Documents common task-schema, Docker and verification failures. | **SUPPORT** |
| `harbor/preflight.py` | Structural checks for correct Harbor task packaging. | **SUPPORT** |
| `harbor/.gitignore` | Keeps Harbor-specific temporary files out of Git. | **SUPPORT** |
| `harbor/shared/verifier_core.py` | Authoritative reusable implementation of verifier mechanics; copied into each real task. | **CORE/SUPPORT** — retain to regenerate copies consistently |
| `harbor/reference/README.md` | Optional notes on stronger semantic verification and anti-forgery ordering. | **HISTORY/SUPPORT** |
| `harbor/template/task.toml` | Generic task config template used by `workflow/package.py`. | **TEMPLATE** |
| `harbor/template/instruction.md` | Generic instruction template with placeholders. | **TEMPLATE** |
| `harbor/template/environment/Dockerfile` | Generic Harbor environment image scaffold. | **TEMPLATE** |
| `harbor/template/solution/solve.sh` | Placeholder oracle script, **not** an actual completed solution. | **TEMPLATE** |
| `harbor/template/tests/test.sh` | Placeholder test runner. | **TEMPLATE** |
| `harbor/template/tests/test_state.py` | Placeholder verifier tests. | **TEMPLATE** |
| `harbor/example/README.md` | Worked example walkthrough. | **HISTORY/TEMPLATE** |
| `harbor/example/task.toml` | Worked example Harbor metadata. | **TEMPLATE** |
| `harbor/example/instruction.md` | Worked example task prompt. | **TEMPLATE** |
| `harbor/example/environment/Dockerfile` | Worked example image. | **TEMPLATE** |
| `harbor/example/environment/harvest_log.csv` | Worked example input data. | **TEMPLATE** |
| `harbor/example/solution/solve.sh` | Known-good reference example solution. | **TEMPLATE** |
| `harbor/example/tests/{test.sh,test_state.py,figure_manifest.py,sitecustomize.py}` | Worked example verifier, shell entry point and Matplotlib instrumentation. | **TEMPLATE** |
| `harbor/example/mutants/{forgery,hardcoded,illegible,sum_crates}/solve.sh` | Four deliberately flawed example implementations, used to teach what checks catch or miss. | **TEMPLATE/HISTORY** |

**Teaching point:** `solution/solve.sh` is not the final student agent; it is a **known reference solution**. `tests/test_state.py` is not a learning note; it is the **actual executable grader**. Mutants are deliberately wrong by design, not bugs to fix in the oracle.

## 7. Scripts, tests, development setup, and documentation

### `scripts/`: utilities with different purposes

| Script | What it does | Classification |
| --- | --- | --- |
| `scripts/__init__.py` | Python package namespace. | **SUPPORT** |
| `scripts/offline_preflight.py` | Checks seed run IDs, valid `result.json`, PNG headers/dimensions, human-label coverage, terminal-error rules. No inference. | **SUPPORT** — reliable first check |
| `scripts/disagreements.py` | Compares *saved* predictions with labels after judging; lists false positives/negatives by family. | **SUPPORT** — error analysis |
| `scripts/make_part3_inputs.py` | Recreates seeded synthetic transaction and sensor CSV datasets. | **SUPPORT** — data regeneration |
| `scripts/build_harbor_tasks.py` | Finishes Harbor scaffolds: writes verifier tests, reference solutions, task configs and mutants, and installs shared helpers. | **SUPPORT** — regenerate the 5 tasks; not needed just to run already-packaged tasks |
| `scripts/judge_smoke.py` | Makes a single live judge request on one seed run to check API access, model output and usage. | **SUPPORT** — billable smoke test |
| `scripts/judge_cost.py` | Reads JSONL token-use logs to calculate estimated judge API spending. | **SUPPORT** — spend accounting |
| `scripts/openai_seed_pilot.py` | Controlled early OpenAI image-judgment experiment; labels are only used in separate comparison mode. | **HISTORY/SUPPORT** |
| `scripts/zai_vision_probe.py` | Independent Z.ai vision request/probe, offline by default. | **HISTORY/SUPPORT** |
| `scripts/provider_compat_probe.py` | One-model compatibility probe with an offline preview and strictly gated live mode. | **SUPPORT** — model integration research |
| `scripts/provider_preflight.py` | Zero-network preview of requests for all model roles. | **SUPPORT** |
| `scripts/figure_extract_worker.py` | Fixed trusted helper for extracting `/workspace/figure.png` as a validated envelope; not a model-generated command. | **SUPPORT** — extraction design |
| `scripts/chart_smoke_worker.py` | Generates a fixed small synthetic Matplotlib PNG to check planned chart image plumbing. | **SUPPORT** — sandbox smoke tests |
| `scripts/preview_chart_smoke_offline.py` | Offline-only preview of temporary chart-image build contexts, zero/one input CSV, Dockerfile, and cleanup. | **SUPPORT** |
| `scripts/check_chart_build_context_offline.py` | Runs targeted tests of the allowlisted Docker context builder; fails if no tests are discovered. | **SUPPORT** |
| `scripts/check_chart_image_recipe_offline.py` | Runs offline Dockerfile recipe tests. | **SUPPORT** |
| `scripts/check_chart_smoke_preview_offline.py` | Runs offline chart smoke-preview tests. | **SUPPORT** |
| `scripts/check_chart_smoke_worker_offline.py` | Runs host-only synthetic chart worker tests. | **SUPPORT** |
| `scripts/check_chart_transfer_offline.py` | Runs CSV transfer/extraction planning tests. | **SUPPORT** |
| `scripts/check_chart_wheel_lock_offline.py` | Runs wheel-hash metadata audit. | **SUPPORT** |
| `scripts/check_controller_offline.py` | Runs targeted controller state-machine tests. | **SUPPORT** |
| `scripts/check_sandbox_gateway_offline.py` | Runs fake-Docker gateway authorization/state tests. | **SUPPORT** |
| `scripts/check_task_artifacts_offline.py` | Runs CSV/PNG artifact validation tests. | **SUPPORT** |
| `scripts/deploy_agent_runner.sh` | Original Modal agent-runner deployment helper. | **HISTORY** — not for the independent Docker path |
| `scripts/deploy_generation_models.sh` | Original Modal generation-model deployment helper. | **HISTORY** |
| `scripts/deploy_validator_model.sh` | Original Modal validator deployment helper. | **HISTORY** |

Note: the `check_*.py` commands are thin wrappers around the corresponding `tests/test_*.py` files. The scripts **select and run tests**; the tests **contain the assertions**. They are not extra chart-making models.

### `tests/`: automated regression checks, not experiment logs

| Test file | What behavior it exercises |
| --- | --- |
| `test_offline_preflight.py` | Seed dataset integrity/preflight logic |
| `test_validator_solution_offline.py` | Final validator logic without live model requests |
| `test_validator_semantic_offline.py` | Structured error-family judgments and semantic separation |
| `test_validator_openai_seed_offline.py` | OpenAI seed-pilot request/response handling |
| `test_validator_vision_probe_offline.py` | Vision probe payload/logic |
| `test_provider_deepseek_offline.py` | DeepSeek request format |
| `test_provider_openai_offline.py` | OpenAI request format |
| `test_provider_zai_offline.py` | Z.ai chat request format |
| `test_provider_registry_offline.py` | Model role registry and IDs |
| `test_provider_compat_probe_offline.py` | Provider compatibility probe safety/format |
| `test_controller_state_offline.py` | Tool-call/controller state transitions and limits |
| `test_sandbox_gateway_offline.py` | Explicit permission and fake-container gateway behavior |
| `test_sandbox_generate_offline.py` | Adapted Docker generation orchestration using offline doubles |
| `test_task_artifacts_offline.py` | CSV snapshot and PNG artifact validity/limits |
| `test_chart_transfer_offline.py` | Input staging and trusted figure-extraction plans |
| `test_chart_image_recipe_offline.py` | Dockerfile recipe/digest validation |
| `test_chart_build_context_offline.py` | Allowlisted build-context assembly |
| `test_chart_smoke_preview_offline.py` | Sandbox chart-image smoke preview |
| `test_chart_smoke_worker_offline.py` | Fixed plotting worker output contract |

All 19 tracked files under root `tests/` are **SUPPORT**. They are executable checks; none is just a diary. They matter because offline tests catch programming regressions without requiring paid model calls or Docker.

### Environment and CI configuration

| File | What it does | Classification |
| --- | --- | --- |
| `.devcontainer/devcontainer.json` | Defines the Codespaces/VS Code dev-container image, Docker-in-Docker feature, extensions and post-create command. | **SUPPORT** — needed for one-click Codespaces setup |
| `.devcontainer/post-create.sh` | Installs `uv` if missing, syncs pinned dependencies and runs seed preflight. | **SUPPORT** |
| `.github/workflows/offline-ci.yml` | GitHub Actions pipeline for structural checks, locked dependency setup and offline tests. | **SUPPORT** — protects changes |

**Teaching point:** Codespaces configuration is not the chart-agent sandbox. The **dev container** is where the *developer works*. The **sandbox image** under `sandbox/` is where the model's proposed plotting commands run. The **Harbor task images** are where oracle/grader checks run.

### `infrastructure/`: preserved upstream Modal implementation — **HISTORY**

| File | What it does |
| --- | --- |
| `infrastructure/README.md` | Original hosted GPU/Modal deployment instructions and endpoint URLs/settings |
| `infrastructure/validator_model.py` | Deploys the original validator model-serving endpoint |
| `infrastructure/generation_models.py` | Defines original hosted generation model servers |
| `infrastructure/generation_gateway.py` | Original generation-model gateway/router |
| `infrastructure/agent_runner.py` | Original mini-SWE-agent task runner on Modal |
| `infrastructure/configure_generation.py` | Original generation endpoint/secret setup helper |
| `infrastructure/serving.py` | Shared model-serving code used by upstream deployment |

These files are kept to show **what the course setup was** and how your alternative differs. They are **not required to run the completed hosted-API plus Docker adaptation**. They may still import and depend on Modal because they were preserved intentionally.

### `docs/`: mostly learning, design decisions, and provenance

| File | What it teaches or records | Classification |
| --- | --- | --- |
| `docs/ARCHITECTURE.md` | Earlier proposed offline-first architecture and security boundaries; treat future-tense statements as historical. | **HISTORY/SUPPORT** |
| `docs/Learning-Progress.md` | Long, append-only engineering journal: sessions, commands, failures, lessons and resume checkpoints. | **HISTORY — learning record** |
| `docs/PHASE-0.md` | Initial offline dataset inspection plan and acceptance criteria. | **HISTORY/SUPPORT** |
| `docs/Progress-Explained-20261107.md` | Beginner-oriented explainer of the assignment, models, errors, confusion matrices and progress at that date. | **HISTORY — learning record** |
| `docs/Provider-Migration-Plan.md` | Reasons and plan for moving from course models/Modal to hosted providers. | **HISTORY/SUPPORT** |
| `docs/README-Development-History.md` | Archived earlier README content, including superseded status statements. | **HISTORY — development archive** |
| `docs/Session-009-Compatibility-Probes.md` | Session 009 provider API compatibility observations. | **HISTORY — learning/experiment record** |
| `docs/Session-010-Controller-Design.md` | Controller state machine, request/tool budgeting and safe orchestration design. | **HISTORY — learning/design** |
| `docs/Session-010-Supply-Chain.md` | Dependency/image hash pinning and supply-chain thinking. | **HISTORY — learning/design** |
| `docs/Session-012-Docker-Smoke-Preflight.md` | Offline chart-image smoke planning/checks. | **HISTORY — learning/verification** |
| `docs/Session-013-Docker-Smoke-Readiness.md` | Progress on trusted synthetic chart worker/readiness. | **HISTORY — learning/verification** |
| `docs/Session-014-Chart-Worker-Image-Staging.md` | Progress on staging the trusted worker into an offline image plan. | **HISTORY — learning/verification** |
| `docs/UPSTREAM.md` | Exact upstream assignment revision and pinned Assignment 1 sandbox package provenance. | **SUPPORT** — valuable reproducibility reference |
| `docs/report-notes.md` | Working tables, costs and intermediate results used to compose the final report. | **HISTORY/SUPPORT** — analysis record |

**Important:** dated session documents are snapshots of what was known *then*. A statement like “no live chart generation yet” in an early learning journal is not evidence that the *finished* repository lacks generation. Prefer the **current `README.md`, final report, and final source code** for current status.

## 8. Generated outputs: which to keep

Everything here is **RESULT**, with a few useful subcategories. These files are **not needed for a fresh run**, but they are necessary if someone wants to verify what you claimed without rerunning expensive inference.

| Output file or pattern | Specific meaning | Keep? |
| --- | --- | --- |
| `output/baseline_predictions.json` | Baseline validator's saved 110-seed predictions. | **Yes** — Part 1 comparison |
| `output/baseline_score.txt` | Baseline MCC results. | **Yes** |
| `output/final_seed_predictions.json` | Final validator's saved 110-seed predictions. | **Yes** — Part 2/4 evaluation evidence |
| `output/final_seed_score.txt` | Final seed evaluation scores. | **Yes** |
| `output/authored_predictions.json` | Final validator predictions on the 15 new runs. | **Yes** — Part 3/4 evidence |
| `output/authored_score.txt` | Final authored-run scores. | **Yes** |
| `output/pre_iteration_{seed,authored}_{predictions.json,score.txt}` | Part 4 before-iteration checkpoints. | **Yes** — documents the before/after comparison |
| `output/part4a_{seed,authored}_{predictions.json,score.txt}` | A Part 4 intermediate variant's measurements. | **Yes** — ablation/iteration record |
| `output/part4b_{seed,authored}_{predictions.json,score.txt}` | Another Part 4 intermediate variant's measurements. | **Yes** — calibration record |
| `output/check_submission.txt` | Captured Harbor oracle and mutant rewards followed by `submission valid`. | **Yes** — recorded acceptance check, not proof of perfect verifier coverage |
| `output/provider_compat_*.json` | Early provider model/response compatibility probes. | **Optional HISTORY/RESULT** — useful when debugging APIs |
| `output/session005_openai_*.json` | Initial individual GPT judgment experiments on seeds 004/008. | **Optional HISTORY/RESULT** |
| `output/session007_openai_*.json` | Follow-up prompt/check experiments on seeds 004/008. | **Optional HISTORY/RESULT** |
| `output/.gitkeep` | Tracked empty-folder placeholder. | **No** runtime need now |

`report.pdf` is also a result, but unlike an exploratory probe it is the **final human-readable deliverable**. Keep the editable `report.tex` alongside it.

## 9. Reading order, safe commands, and cleanup advice

### Reading order for a learner

1. **`README.md`** — understand the four parts, model substitutions and final findings.
2. **`ASSIGNMENT.md`** — see the original requirement, so you can tell original contracts from adaptations.
3. **`validator/prediction.py` → `validator/runner.py` → `validator/baseline.py` → `validator/solution.py`** — learn how a run becomes an error judgment and how the solution improves the baseline.
4. **`workflow/evaluate.py` + `seed_labels.json`** — learn how the judged errors are compared to human truth and how MCC is calculated.
5. **One `artifacts/NNN/result.json` paired with its `figure.png` and any `inputs/NNN/` CSV** — connect the code with an actual agent trajectory.
6. **One `tasks/.../task.json` → `workflow/sandbox_generate.py` → `runs/.../`** — understand how your adaptation generated new agent attempts.
7. **`harbor/tasks/quarterly-revenue-by-region/`** — follow `task.toml`, `solution/solve.sh`, `tests/test_state.py`, then the `sum_units` mutant; this is the clearest example of a verifier catching incorrect aggregation.
8. **`report.tex`/`report.pdf`** — connect code behavior to measured findings. Use `docs/Learning-Progress.md` when you want detailed historical context.

### Commands (from repository root)

These first examples do not invoke paid model APIs and do not build containers:

```bash
uv sync --locked
uv run python scripts/offline_preflight.py
uv run python -m unittest discover -s tests -p 'test_*.py' -v

# Examine the command interface:
uv run python -m workflow --help

# Recompute a saved score from already-committed predictions and labels:
uv run python -m workflow score --help
```

Consult the `README.md` and command `--help` before choosing the exact score input/output flags. Do **not** rerun live judge calls when a saved score is all you need. Live generation (`python -m workflow.sandbox_generate`) invokes paid providers and needs the correct credentials/image; real Harbor oracle/mutant runs require Docker.

### What could be removed from a **future stripped-down software package**?

- **Archive elsewhere rather than delete outright:** `docs/Learning-Progress.md`, dated session docs, early probe results, upstream Modal files, example Harbor tasks, and `report_template.tex` are not required for the final validator's runtime. They are valuable as learning history and provenance in *this assignment repository*.
- **Keep as primary evidence:** seed data and labels, authored tasks/labels/runs, final prediction/score files, Harbor task verifiers and oracle/mutants, final report and current README.
- **Keep as software engineering infrastructure:** lockfiles, Git configuration, CI, unit tests and deterministic input-generation scripts. They prevent silent changes in behavior even if the code can execute without them on one machine.
- **Do not mistake intentionally bad files for clutter:** `harbor/**/mutants/**/solve.sh` are controlled negative tests; removing them erases evidence of what the verifier can and cannot catch.

### Quick questions and answers

**Do I need every one of the 505 tracked files to run the final judge?** No. The judge needs the validator code, compatible environment/model settings, and the task evidence. Many files support other assignment parts, tests or the historical record.

**Should I delete `artifacts/` because it sounds generated?** No. It is the released **seed dataset**; deleting it defeats the original evaluation.

**Can I delete `output/` and `runs/` and regenerate them?** In principle yes, with the right services and expense, but you would discard the actual evaluated observations. Model outputs can be nondeterministic, so a rerun may not produce identical evidence. Keep them for reproducibility.

**Are the Session 010–014 planning files obsolete?** They are not the main final result, but they document the careful security/reproducibility design and are covered by tests. They are sensible to retain in a learning repository.

**Is the original `infrastructure/` broken or unnecessary?** It is intentionally kept as **upstream reference code**. It is unnecessary for the adapted hosted-API + Docker route, not necessarily broken.

**Why are there two kinds of human labels?** `seed_labels.json` is for the original public seed set; `labels.json` is for your 15 newly generated runs. Neither should be exposed to a validator during inference.

## 10. Appendix: every individual file classified

The table below enumerates **every one of the 505 tracked files**. Descriptions of repeated paths are intentionally short; read Sections 4–8 for the detailed workflow explanation. This catalog is generated from the exact inspected path inventory rather than from a generic project template.

| Tracked file path | Category | One-line purpose |
| --- | --- | --- |
| [`.devcontainer/devcontainer.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.devcontainer/devcontainer.json) | **SUPPORT** | Codespaces/VS Code environment config |
| [`.devcontainer/post-create.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.devcontainer/post-create.sh) | **SUPPORT** | Post-create uv install and offline preflight |
| [`.env.example`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.env.example) | **SUPPORT** | Example hosted judge and original Modal endpoint settings |
| [`.env.local.example`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.env.local.example) | **HISTORY** | Earlier local provider configuration example |
| [`.gitattributes`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.gitattributes) | **SUPPORT** | Portable LF line endings for scripts and CSVs |
| [`.github/workflows/offline-ci.yml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.github/workflows/offline-ci.yml) | **SUPPORT** | GitHub Actions offline checks, dependency sync and tests |
| [`.gitignore`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.gitignore) | **SUPPORT** | Excludes secrets, caches, environments and transient jobs |
| [`.python-version`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/.python-version) | **SUPPORT** | Preferred Python interpreter version |
| [`AI_USAGE.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/AI_USAGE.md) | **SUPPORT** | AI authoring and model-use disclosure |
| [`ASSIGNMENT.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/ASSIGNMENT.md) | **SUPPORT** | Original course assignment specification |
| [`README.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/README.md) | **SUPPORT** | Current repository overview, methods, results and commands |
| [`artifacts/001/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/001/result.json) | **DATA** | Original seed run 001 trajectory/task/outcome |
| [`artifacts/004/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/004/figure.png) | **DATA** | Original seed run 004 generated chart |
| [`artifacts/004/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/004/result.json) | **DATA** | Original seed run 004 trajectory/task/outcome |
| [`artifacts/008/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/008/figure.png) | **DATA** | Original seed run 008 generated chart |
| [`artifacts/008/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/008/result.json) | **DATA** | Original seed run 008 trajectory/task/outcome |
| [`artifacts/009/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/009/figure.png) | **DATA** | Original seed run 009 generated chart |
| [`artifacts/009/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/009/result.json) | **DATA** | Original seed run 009 trajectory/task/outcome |
| [`artifacts/010/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/010/result.json) | **DATA** | Original seed run 010 trajectory/task/outcome |
| [`artifacts/013/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/013/figure.png) | **DATA** | Original seed run 013 generated chart |
| [`artifacts/013/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/013/result.json) | **DATA** | Original seed run 013 trajectory/task/outcome |
| [`artifacts/016/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/016/figure.png) | **DATA** | Original seed run 016 generated chart |
| [`artifacts/016/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/016/result.json) | **DATA** | Original seed run 016 trajectory/task/outcome |
| [`artifacts/021/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/021/figure.png) | **DATA** | Original seed run 021 generated chart |
| [`artifacts/021/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/021/result.json) | **DATA** | Original seed run 021 trajectory/task/outcome |
| [`artifacts/022/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/022/figure.png) | **DATA** | Original seed run 022 generated chart |
| [`artifacts/022/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/022/result.json) | **DATA** | Original seed run 022 trajectory/task/outcome |
| [`artifacts/023/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/023/figure.png) | **DATA** | Original seed run 023 generated chart |
| [`artifacts/023/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/023/result.json) | **DATA** | Original seed run 023 trajectory/task/outcome |
| [`artifacts/025/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/025/figure.png) | **DATA** | Original seed run 025 generated chart |
| [`artifacts/025/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/025/result.json) | **DATA** | Original seed run 025 trajectory/task/outcome |
| [`artifacts/026/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/026/figure.png) | **DATA** | Original seed run 026 generated chart |
| [`artifacts/026/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/026/result.json) | **DATA** | Original seed run 026 trajectory/task/outcome |
| [`artifacts/028/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/028/figure.png) | **DATA** | Original seed run 028 generated chart |
| [`artifacts/028/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/028/result.json) | **DATA** | Original seed run 028 trajectory/task/outcome |
| [`artifacts/029/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/029/figure.png) | **DATA** | Original seed run 029 generated chart |
| [`artifacts/029/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/029/result.json) | **DATA** | Original seed run 029 trajectory/task/outcome |
| [`artifacts/030/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/030/figure.png) | **DATA** | Original seed run 030 generated chart |
| [`artifacts/030/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/030/result.json) | **DATA** | Original seed run 030 trajectory/task/outcome |
| [`artifacts/031/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/031/figure.png) | **DATA** | Original seed run 031 generated chart |
| [`artifacts/031/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/031/result.json) | **DATA** | Original seed run 031 trajectory/task/outcome |
| [`artifacts/034/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/034/figure.png) | **DATA** | Original seed run 034 generated chart |
| [`artifacts/034/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/034/result.json) | **DATA** | Original seed run 034 trajectory/task/outcome |
| [`artifacts/038/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/038/figure.png) | **DATA** | Original seed run 038 generated chart |
| [`artifacts/038/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/038/result.json) | **DATA** | Original seed run 038 trajectory/task/outcome |
| [`artifacts/039/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/039/figure.png) | **DATA** | Original seed run 039 generated chart |
| [`artifacts/039/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/039/result.json) | **DATA** | Original seed run 039 trajectory/task/outcome |
| [`artifacts/046/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/046/figure.png) | **DATA** | Original seed run 046 generated chart |
| [`artifacts/046/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/046/result.json) | **DATA** | Original seed run 046 trajectory/task/outcome |
| [`artifacts/047/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/047/figure.png) | **DATA** | Original seed run 047 generated chart |
| [`artifacts/047/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/047/result.json) | **DATA** | Original seed run 047 trajectory/task/outcome |
| [`artifacts/050/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/050/figure.png) | **DATA** | Original seed run 050 generated chart |
| [`artifacts/050/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/050/result.json) | **DATA** | Original seed run 050 trajectory/task/outcome |
| [`artifacts/051/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/051/figure.png) | **DATA** | Original seed run 051 generated chart |
| [`artifacts/051/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/051/result.json) | **DATA** | Original seed run 051 trajectory/task/outcome |
| [`artifacts/052/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/052/figure.png) | **DATA** | Original seed run 052 generated chart |
| [`artifacts/052/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/052/result.json) | **DATA** | Original seed run 052 trajectory/task/outcome |
| [`artifacts/053/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/053/result.json) | **DATA** | Original seed run 053 trajectory/task/outcome |
| [`artifacts/055/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/055/figure.png) | **DATA** | Original seed run 055 generated chart |
| [`artifacts/055/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/055/result.json) | **DATA** | Original seed run 055 trajectory/task/outcome |
| [`artifacts/059/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/059/figure.png) | **DATA** | Original seed run 059 generated chart |
| [`artifacts/059/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/059/result.json) | **DATA** | Original seed run 059 trajectory/task/outcome |
| [`artifacts/060/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/060/figure.png) | **DATA** | Original seed run 060 generated chart |
| [`artifacts/060/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/060/result.json) | **DATA** | Original seed run 060 trajectory/task/outcome |
| [`artifacts/062/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/062/figure.png) | **DATA** | Original seed run 062 generated chart |
| [`artifacts/062/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/062/result.json) | **DATA** | Original seed run 062 trajectory/task/outcome |
| [`artifacts/065/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/065/result.json) | **DATA** | Original seed run 065 trajectory/task/outcome |
| [`artifacts/068/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/068/figure.png) | **DATA** | Original seed run 068 generated chart |
| [`artifacts/068/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/068/result.json) | **DATA** | Original seed run 068 trajectory/task/outcome |
| [`artifacts/069/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/069/figure.png) | **DATA** | Original seed run 069 generated chart |
| [`artifacts/069/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/069/result.json) | **DATA** | Original seed run 069 trajectory/task/outcome |
| [`artifacts/070/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/070/figure.png) | **DATA** | Original seed run 070 generated chart |
| [`artifacts/070/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/070/result.json) | **DATA** | Original seed run 070 trajectory/task/outcome |
| [`artifacts/074/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/074/figure.png) | **DATA** | Original seed run 074 generated chart |
| [`artifacts/074/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/074/result.json) | **DATA** | Original seed run 074 trajectory/task/outcome |
| [`artifacts/075/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/075/figure.png) | **DATA** | Original seed run 075 generated chart |
| [`artifacts/075/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/075/result.json) | **DATA** | Original seed run 075 trajectory/task/outcome |
| [`artifacts/077/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/077/figure.png) | **DATA** | Original seed run 077 generated chart |
| [`artifacts/077/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/077/result.json) | **DATA** | Original seed run 077 trajectory/task/outcome |
| [`artifacts/079/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/079/figure.png) | **DATA** | Original seed run 079 generated chart |
| [`artifacts/079/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/079/result.json) | **DATA** | Original seed run 079 trajectory/task/outcome |
| [`artifacts/080/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/080/figure.png) | **DATA** | Original seed run 080 generated chart |
| [`artifacts/080/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/080/result.json) | **DATA** | Original seed run 080 trajectory/task/outcome |
| [`artifacts/081/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/081/figure.png) | **DATA** | Original seed run 081 generated chart |
| [`artifacts/081/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/081/result.json) | **DATA** | Original seed run 081 trajectory/task/outcome |
| [`artifacts/082/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/082/figure.png) | **DATA** | Original seed run 082 generated chart |
| [`artifacts/082/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/082/result.json) | **DATA** | Original seed run 082 trajectory/task/outcome |
| [`artifacts/083/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/083/figure.png) | **DATA** | Original seed run 083 generated chart |
| [`artifacts/083/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/083/result.json) | **DATA** | Original seed run 083 trajectory/task/outcome |
| [`artifacts/086/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/086/figure.png) | **DATA** | Original seed run 086 generated chart |
| [`artifacts/086/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/086/result.json) | **DATA** | Original seed run 086 trajectory/task/outcome |
| [`artifacts/087/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/087/figure.png) | **DATA** | Original seed run 087 generated chart |
| [`artifacts/087/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/087/result.json) | **DATA** | Original seed run 087 trajectory/task/outcome |
| [`artifacts/089/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/089/result.json) | **DATA** | Original seed run 089 trajectory/task/outcome |
| [`artifacts/090/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/090/figure.png) | **DATA** | Original seed run 090 generated chart |
| [`artifacts/090/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/090/result.json) | **DATA** | Original seed run 090 trajectory/task/outcome |
| [`artifacts/091/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/091/figure.png) | **DATA** | Original seed run 091 generated chart |
| [`artifacts/091/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/091/result.json) | **DATA** | Original seed run 091 trajectory/task/outcome |
| [`artifacts/096/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/096/result.json) | **DATA** | Original seed run 096 trajectory/task/outcome |
| [`artifacts/097/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/097/figure.png) | **DATA** | Original seed run 097 generated chart |
| [`artifacts/097/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/097/result.json) | **DATA** | Original seed run 097 trajectory/task/outcome |
| [`artifacts/098/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/098/figure.png) | **DATA** | Original seed run 098 generated chart |
| [`artifacts/098/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/098/result.json) | **DATA** | Original seed run 098 trajectory/task/outcome |
| [`artifacts/099/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/099/figure.png) | **DATA** | Original seed run 099 generated chart |
| [`artifacts/099/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/099/result.json) | **DATA** | Original seed run 099 trajectory/task/outcome |
| [`artifacts/103/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/103/result.json) | **DATA** | Original seed run 103 trajectory/task/outcome |
| [`artifacts/104/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/104/figure.png) | **DATA** | Original seed run 104 generated chart |
| [`artifacts/104/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/104/result.json) | **DATA** | Original seed run 104 trajectory/task/outcome |
| [`artifacts/105/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/105/figure.png) | **DATA** | Original seed run 105 generated chart |
| [`artifacts/105/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/105/result.json) | **DATA** | Original seed run 105 trajectory/task/outcome |
| [`artifacts/106/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/106/figure.png) | **DATA** | Original seed run 106 generated chart |
| [`artifacts/106/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/106/result.json) | **DATA** | Original seed run 106 trajectory/task/outcome |
| [`artifacts/108/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/108/figure.png) | **DATA** | Original seed run 108 generated chart |
| [`artifacts/108/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/108/result.json) | **DATA** | Original seed run 108 trajectory/task/outcome |
| [`artifacts/111/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/111/figure.png) | **DATA** | Original seed run 111 generated chart |
| [`artifacts/111/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/111/result.json) | **DATA** | Original seed run 111 trajectory/task/outcome |
| [`artifacts/112/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/112/figure.png) | **DATA** | Original seed run 112 generated chart |
| [`artifacts/112/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/112/result.json) | **DATA** | Original seed run 112 trajectory/task/outcome |
| [`artifacts/115/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/115/figure.png) | **DATA** | Original seed run 115 generated chart |
| [`artifacts/115/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/115/result.json) | **DATA** | Original seed run 115 trajectory/task/outcome |
| [`artifacts/117/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/117/figure.png) | **DATA** | Original seed run 117 generated chart |
| [`artifacts/117/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/117/result.json) | **DATA** | Original seed run 117 trajectory/task/outcome |
| [`artifacts/124/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/124/figure.png) | **DATA** | Original seed run 124 generated chart |
| [`artifacts/124/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/124/result.json) | **DATA** | Original seed run 124 trajectory/task/outcome |
| [`artifacts/125/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/125/figure.png) | **DATA** | Original seed run 125 generated chart |
| [`artifacts/125/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/125/result.json) | **DATA** | Original seed run 125 trajectory/task/outcome |
| [`artifacts/126/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/126/figure.png) | **DATA** | Original seed run 126 generated chart |
| [`artifacts/126/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/126/result.json) | **DATA** | Original seed run 126 trajectory/task/outcome |
| [`artifacts/128/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/128/figure.png) | **DATA** | Original seed run 128 generated chart |
| [`artifacts/128/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/128/result.json) | **DATA** | Original seed run 128 trajectory/task/outcome |
| [`artifacts/129/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/129/figure.png) | **DATA** | Original seed run 129 generated chart |
| [`artifacts/129/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/129/result.json) | **DATA** | Original seed run 129 trajectory/task/outcome |
| [`artifacts/130/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/130/figure.png) | **DATA** | Original seed run 130 generated chart |
| [`artifacts/130/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/130/result.json) | **DATA** | Original seed run 130 trajectory/task/outcome |
| [`artifacts/131/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/131/figure.png) | **DATA** | Original seed run 131 generated chart |
| [`artifacts/131/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/131/result.json) | **DATA** | Original seed run 131 trajectory/task/outcome |
| [`artifacts/135/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/135/figure.png) | **DATA** | Original seed run 135 generated chart |
| [`artifacts/135/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/135/result.json) | **DATA** | Original seed run 135 trajectory/task/outcome |
| [`artifacts/136/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/136/figure.png) | **DATA** | Original seed run 136 generated chart |
| [`artifacts/136/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/136/result.json) | **DATA** | Original seed run 136 trajectory/task/outcome |
| [`artifacts/141/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/141/figure.png) | **DATA** | Original seed run 141 generated chart |
| [`artifacts/141/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/141/result.json) | **DATA** | Original seed run 141 trajectory/task/outcome |
| [`artifacts/142/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/142/figure.png) | **DATA** | Original seed run 142 generated chart |
| [`artifacts/142/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/142/result.json) | **DATA** | Original seed run 142 trajectory/task/outcome |
| [`artifacts/143/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/143/figure.png) | **DATA** | Original seed run 143 generated chart |
| [`artifacts/143/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/143/result.json) | **DATA** | Original seed run 143 trajectory/task/outcome |
| [`artifacts/145/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/145/result.json) | **DATA** | Original seed run 145 trajectory/task/outcome |
| [`artifacts/146/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/146/figure.png) | **DATA** | Original seed run 146 generated chart |
| [`artifacts/146/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/146/result.json) | **DATA** | Original seed run 146 trajectory/task/outcome |
| [`artifacts/150/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/150/figure.png) | **DATA** | Original seed run 150 generated chart |
| [`artifacts/150/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/150/result.json) | **DATA** | Original seed run 150 trajectory/task/outcome |
| [`artifacts/153/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/153/figure.png) | **DATA** | Original seed run 153 generated chart |
| [`artifacts/153/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/153/result.json) | **DATA** | Original seed run 153 trajectory/task/outcome |
| [`artifacts/155/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/155/figure.png) | **DATA** | Original seed run 155 generated chart |
| [`artifacts/155/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/155/result.json) | **DATA** | Original seed run 155 trajectory/task/outcome |
| [`artifacts/156/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/156/figure.png) | **DATA** | Original seed run 156 generated chart |
| [`artifacts/156/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/156/result.json) | **DATA** | Original seed run 156 trajectory/task/outcome |
| [`artifacts/161/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/161/figure.png) | **DATA** | Original seed run 161 generated chart |
| [`artifacts/161/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/161/result.json) | **DATA** | Original seed run 161 trajectory/task/outcome |
| [`artifacts/163/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/163/figure.png) | **DATA** | Original seed run 163 generated chart |
| [`artifacts/163/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/163/result.json) | **DATA** | Original seed run 163 trajectory/task/outcome |
| [`artifacts/164/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/164/figure.png) | **DATA** | Original seed run 164 generated chart |
| [`artifacts/164/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/164/result.json) | **DATA** | Original seed run 164 trajectory/task/outcome |
| [`artifacts/165/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/165/figure.png) | **DATA** | Original seed run 165 generated chart |
| [`artifacts/165/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/165/result.json) | **DATA** | Original seed run 165 trajectory/task/outcome |
| [`artifacts/166/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/166/figure.png) | **DATA** | Original seed run 166 generated chart |
| [`artifacts/166/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/166/result.json) | **DATA** | Original seed run 166 trajectory/task/outcome |
| [`artifacts/167/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/167/figure.png) | **DATA** | Original seed run 167 generated chart |
| [`artifacts/167/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/167/result.json) | **DATA** | Original seed run 167 trajectory/task/outcome |
| [`artifacts/168/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/168/result.json) | **DATA** | Original seed run 168 trajectory/task/outcome |
| [`artifacts/169/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/169/figure.png) | **DATA** | Original seed run 169 generated chart |
| [`artifacts/169/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/169/result.json) | **DATA** | Original seed run 169 trajectory/task/outcome |
| [`artifacts/170/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/170/figure.png) | **DATA** | Original seed run 170 generated chart |
| [`artifacts/170/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/170/result.json) | **DATA** | Original seed run 170 trajectory/task/outcome |
| [`artifacts/171/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/171/result.json) | **DATA** | Original seed run 171 trajectory/task/outcome |
| [`artifacts/173/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/173/figure.png) | **DATA** | Original seed run 173 generated chart |
| [`artifacts/173/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/173/result.json) | **DATA** | Original seed run 173 trajectory/task/outcome |
| [`artifacts/175/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/175/figure.png) | **DATA** | Original seed run 175 generated chart |
| [`artifacts/175/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/175/result.json) | **DATA** | Original seed run 175 trajectory/task/outcome |
| [`artifacts/177/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/177/figure.png) | **DATA** | Original seed run 177 generated chart |
| [`artifacts/177/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/177/result.json) | **DATA** | Original seed run 177 trajectory/task/outcome |
| [`artifacts/180/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/180/figure.png) | **DATA** | Original seed run 180 generated chart |
| [`artifacts/180/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/180/result.json) | **DATA** | Original seed run 180 trajectory/task/outcome |
| [`artifacts/181/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/181/result.json) | **DATA** | Original seed run 181 trajectory/task/outcome |
| [`artifacts/183/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/183/figure.png) | **DATA** | Original seed run 183 generated chart |
| [`artifacts/183/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/183/result.json) | **DATA** | Original seed run 183 trajectory/task/outcome |
| [`artifacts/191/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/191/figure.png) | **DATA** | Original seed run 191 generated chart |
| [`artifacts/191/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/191/result.json) | **DATA** | Original seed run 191 trajectory/task/outcome |
| [`artifacts/195/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/195/figure.png) | **DATA** | Original seed run 195 generated chart |
| [`artifacts/195/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/195/result.json) | **DATA** | Original seed run 195 trajectory/task/outcome |
| [`artifacts/196/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/196/figure.png) | **DATA** | Original seed run 196 generated chart |
| [`artifacts/196/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/196/result.json) | **DATA** | Original seed run 196 trajectory/task/outcome |
| [`artifacts/199/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/199/figure.png) | **DATA** | Original seed run 199 generated chart |
| [`artifacts/199/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/199/result.json) | **DATA** | Original seed run 199 trajectory/task/outcome |
| [`artifacts/200/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/200/figure.png) | **DATA** | Original seed run 200 generated chart |
| [`artifacts/200/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/200/result.json) | **DATA** | Original seed run 200 trajectory/task/outcome |
| [`artifacts/202/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/202/figure.png) | **DATA** | Original seed run 202 generated chart |
| [`artifacts/202/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/202/result.json) | **DATA** | Original seed run 202 trajectory/task/outcome |
| [`artifacts/203/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/203/figure.png) | **DATA** | Original seed run 203 generated chart |
| [`artifacts/203/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/203/result.json) | **DATA** | Original seed run 203 trajectory/task/outcome |
| [`artifacts/204/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/204/figure.png) | **DATA** | Original seed run 204 generated chart |
| [`artifacts/204/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/204/result.json) | **DATA** | Original seed run 204 trajectory/task/outcome |
| [`artifacts/205/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/205/figure.png) | **DATA** | Original seed run 205 generated chart |
| [`artifacts/205/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/205/result.json) | **DATA** | Original seed run 205 trajectory/task/outcome |
| [`artifacts/206/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/206/figure.png) | **DATA** | Original seed run 206 generated chart |
| [`artifacts/206/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/206/result.json) | **DATA** | Original seed run 206 trajectory/task/outcome |
| [`artifacts/208/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/208/result.json) | **DATA** | Original seed run 208 trajectory/task/outcome |
| [`artifacts/209/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/209/figure.png) | **DATA** | Original seed run 209 generated chart |
| [`artifacts/209/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/209/result.json) | **DATA** | Original seed run 209 trajectory/task/outcome |
| [`artifacts/210/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/210/figure.png) | **DATA** | Original seed run 210 generated chart |
| [`artifacts/210/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/210/result.json) | **DATA** | Original seed run 210 trajectory/task/outcome |
| [`artifacts/212/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/212/figure.png) | **DATA** | Original seed run 212 generated chart |
| [`artifacts/212/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/212/result.json) | **DATA** | Original seed run 212 trajectory/task/outcome |
| [`artifacts/213/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/213/figure.png) | **DATA** | Original seed run 213 generated chart |
| [`artifacts/213/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/213/result.json) | **DATA** | Original seed run 213 trajectory/task/outcome |
| [`artifacts/214/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/214/figure.png) | **DATA** | Original seed run 214 generated chart |
| [`artifacts/214/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/214/result.json) | **DATA** | Original seed run 214 trajectory/task/outcome |
| [`artifacts/216/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/216/figure.png) | **DATA** | Original seed run 216 generated chart |
| [`artifacts/216/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/artifacts/216/result.json) | **DATA** | Original seed run 216 trajectory/task/outcome |
| [`docs/ARCHITECTURE.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/ARCHITECTURE.md) | **HISTORY** | Historical offline-first architecture sketch |
| [`docs/Learning-Progress.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Learning-Progress.md) | **HISTORY** | Chronological engineering and learning journal |
| [`docs/PHASE-0.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/PHASE-0.md) | **HISTORY** | Initial zero-model-call dataset preflight plan |
| [`docs/Progress-Explained-20261107.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Progress-Explained-20261107.md) | **HISTORY** | Beginner-facing project explainer at November 7 checkpoint |
| [`docs/Provider-Migration-Plan.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Provider-Migration-Plan.md) | **HISTORY** | Plan and reasons for provider and execution substitutions |
| [`docs/README-Development-History.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/README-Development-History.md) | **HISTORY** | Archived earlier README versions and status notes |
| [`docs/Session-009-Compatibility-Probes.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Session-009-Compatibility-Probes.md) | **HISTORY** | Provider compatibility probe findings |
| [`docs/Session-010-Controller-Design.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Session-010-Controller-Design.md) | **HISTORY** | Chart-controller design and budget/state safeguards |
| [`docs/Session-010-Supply-Chain.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Session-010-Supply-Chain.md) | **HISTORY** | Image and package dependency trust research |
| [`docs/Session-012-Docker-Smoke-Preflight.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Session-012-Docker-Smoke-Preflight.md) | **HISTORY** | Offline Docker chart smoke preparation notes |
| [`docs/Session-013-Docker-Smoke-Readiness.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Session-013-Docker-Smoke-Readiness.md) | **HISTORY** | Trusted smoke worker test readiness notes |
| [`docs/Session-014-Chart-Worker-Image-Staging.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/Session-014-Chart-Worker-Image-Staging.md) | **HISTORY** | Offline staging of fixed chart smoke worker |
| [`docs/UPSTREAM.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/UPSTREAM.md) | **SUPPORT** | Exact pinned upstream code and sandbox provenance |
| [`docs/report-notes.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/docs/report-notes.md) | **HISTORY** | Working experiment results and draft report tables |
| [`harbor/.gitignore`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/.gitignore) | **SUPPORT** | Harbor local cache/outputs exclusion |
| [`harbor/README.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/README.md) | **SUPPORT** | Harbor packaging and test-run instructions |
| [`harbor/TROUBLESHOOTING.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/TROUBLESHOOTING.md) | **SUPPORT** | Harbor failure modes and debugging guidance |
| [`harbor/example/README.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/README.md) | **TEMPLATE** | Worked Harbor example file: README.md |
| [`harbor/example/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/environment/Dockerfile) | **TEMPLATE** | Worked Harbor example file: environment/Dockerfile |
| [`harbor/example/environment/harvest_log.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/environment/harvest_log.csv) | **TEMPLATE** | Worked example input dataset |
| [`harbor/example/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/instruction.md) | **TEMPLATE** | Worked Harbor example file: instruction.md |
| [`harbor/example/mutants/forgery/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/mutants/forgery/solve.sh) | **TEMPLATE** | Deliberately flawed example answer: forgery |
| [`harbor/example/mutants/hardcoded/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/mutants/hardcoded/solve.sh) | **TEMPLATE** | Deliberately flawed example answer: hardcoded |
| [`harbor/example/mutants/illegible/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/mutants/illegible/solve.sh) | **TEMPLATE** | Deliberately flawed example answer: illegible |
| [`harbor/example/mutants/sum_crates/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/mutants/sum_crates/solve.sh) | **TEMPLATE** | Deliberately flawed example answer: sum_crates |
| [`harbor/example/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/solution/solve.sh) | **TEMPLATE** | Known-good worked example answer |
| [`harbor/example/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/task.toml) | **TEMPLATE** | Worked Harbor example file: task.toml |
| [`harbor/example/tests/figure_manifest.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/tests/figure_manifest.py) | **TEMPLATE** | Worked example Matplotlib artist-tree capture hook |
| [`harbor/example/tests/sitecustomize.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/tests/sitecustomize.py) | **TEMPLATE** | Worked example Python verifier-side injection hook |
| [`harbor/example/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/tests/test.sh) | **TEMPLATE** | Worked example verifier shell entry point |
| [`harbor/example/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/example/tests/test_state.py) | **TEMPLATE** | Worked example verifier assertions |
| [`harbor/preflight.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/preflight.py) | **SUPPORT** | Harbor task directory preflight checks |
| [`harbor/reference/README.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/reference/README.md) | **HISTORY** | Optional stronger-verifier discussion and notes |
| [`harbor/shared/verifier_core.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/shared/verifier_core.py) | **SUPPORT** | Source-of-truth shared verifier runtime helpers |
| [`harbor/tasks/dense-department-budgets/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/environment/Dockerfile) | **CORE** | Harbor verification container for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/instruction.md) | **CORE** | Harbor agent instructions for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/mutants/unrotated_labels/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/mutants/unrotated_labels/solve.sh) | **SUPPORT** | Deliberately wrong unrotated_labels mutant for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/solution/solve.sh) | **CORE** | Oracle/reference solution for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/task.toml) | **CORE** | Harbor metadata and artifact rules for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/tests/figure_manifest.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/tests/figure_manifest.py) | **CORE** | Matplotlib artist-tree capture module for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/tests/sitecustomize.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/tests/sitecustomize.py) | **CORE** | Python hook loader used in dense-department-budgets verification |
| [`harbor/tasks/dense-department-budgets/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/tests/test.sh) | **CORE** | Harbor verifier execution entry point for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/tests/test_state.py) | **CORE** | Harbor task-specific assertions for dense-department-budgets |
| [`harbor/tasks/dense-department-budgets/tests/verifier_core.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/dense-department-budgets/tests/verifier_core.py) | **CORE** | Copied shared verifier helper for dense-department-budgets |
| [`harbor/tasks/quarterly-revenue-by-region/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/environment/Dockerfile) | **CORE** | Harbor verification container for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/environment/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/environment/transactions.csv) | **CORE** | Embedded Harbor task data for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/instruction.md) | **CORE** | Harbor agent instructions for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/mutants/sum_units/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/mutants/sum_units/solve.sh) | **SUPPORT** | Deliberately wrong sum_units mutant for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/solution/solve.sh) | **CORE** | Oracle/reference solution for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/task.toml) | **CORE** | Harbor metadata and artifact rules for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/tests/figure_manifest.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/tests/figure_manifest.py) | **CORE** | Matplotlib artist-tree capture module for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/tests/sitecustomize.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/tests/sitecustomize.py) | **CORE** | Python hook loader used in quarterly-revenue-by-region verification |
| [`harbor/tasks/quarterly-revenue-by-region/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/tests/test.sh) | **CORE** | Harbor verifier execution entry point for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/tests/test_state.py) | **CORE** | Harbor task-specific assertions for quarterly-revenue-by-region |
| [`harbor/tasks/quarterly-revenue-by-region/tests/verifier_core.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/quarterly-revenue-by-region/tests/verifier_core.py) | **CORE** | Copied shared verifier helper for quarterly-revenue-by-region |
| [`harbor/tasks/sensor-daily-median/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/environment/Dockerfile) | **CORE** | Harbor verification container for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/environment/sensors.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/environment/sensors.csv) | **CORE** | Embedded Harbor task data for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/instruction.md) | **CORE** | Harbor agent instructions for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/solution/solve.sh) | **CORE** | Oracle/reference solution for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/task.toml) | **CORE** | Harbor metadata and artifact rules for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/tests/figure_manifest.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/tests/figure_manifest.py) | **CORE** | Matplotlib artist-tree capture module for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/tests/sitecustomize.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/tests/sitecustomize.py) | **CORE** | Python hook loader used in sensor-daily-median verification |
| [`harbor/tasks/sensor-daily-median/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/tests/test.sh) | **CORE** | Harbor verifier execution entry point for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/tests/test_state.py) | **CORE** | Harbor task-specific assertions for sensor-daily-median |
| [`harbor/tasks/sensor-daily-median/tests/verifier_core.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/sensor-daily-median/tests/verifier_core.py) | **CORE** | Copied shared verifier helper for sensor-daily-median |
| [`harbor/tasks/styled-decay-curves/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/environment/Dockerfile) | **CORE** | Harbor verification container for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/instruction.md) | **CORE** | Harbor agent instructions for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/solution/solve.sh) | **CORE** | Oracle/reference solution for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/task.toml) | **CORE** | Harbor metadata and artifact rules for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/tests/figure_manifest.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/tests/figure_manifest.py) | **CORE** | Matplotlib artist-tree capture module for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/tests/sitecustomize.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/tests/sitecustomize.py) | **CORE** | Python hook loader used in styled-decay-curves verification |
| [`harbor/tasks/styled-decay-curves/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/tests/test.sh) | **CORE** | Harbor verifier execution entry point for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/tests/test_state.py) | **CORE** | Harbor task-specific assertions for styled-decay-curves |
| [`harbor/tasks/styled-decay-curves/tests/verifier_core.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/styled-decay-curves/tests/verifier_core.py) | **CORE** | Copied shared verifier helper for styled-decay-curves |
| [`harbor/tasks/top-products-unit-share/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/environment/Dockerfile) | **CORE** | Harbor verification container for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/environment/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/environment/transactions.csv) | **CORE** | Embedded Harbor task data for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/instruction.md) | **CORE** | Harbor agent instructions for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/solution/solve.sh) | **CORE** | Oracle/reference solution for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/task.toml) | **CORE** | Harbor metadata and artifact rules for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/tests/figure_manifest.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/tests/figure_manifest.py) | **CORE** | Matplotlib artist-tree capture module for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/tests/sitecustomize.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/tests/sitecustomize.py) | **CORE** | Python hook loader used in top-products-unit-share verification |
| [`harbor/tasks/top-products-unit-share/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/tests/test.sh) | **CORE** | Harbor verifier execution entry point for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/tests/test_state.py) | **CORE** | Harbor task-specific assertions for top-products-unit-share |
| [`harbor/tasks/top-products-unit-share/tests/verifier_core.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/tasks/top-products-unit-share/tests/verifier_core.py) | **CORE** | Copied shared verifier helper for top-products-unit-share |
| [`harbor/template/environment/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/template/environment/Dockerfile) | **TEMPLATE** | Harbor packaging scaffold: environment/Dockerfile |
| [`harbor/template/instruction.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/template/instruction.md) | **TEMPLATE** | Harbor packaging scaffold: instruction.md |
| [`harbor/template/solution/solve.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/template/solution/solve.sh) | **TEMPLATE** | Harbor packaging scaffold: solution/solve.sh |
| [`harbor/template/task.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/template/task.toml) | **TEMPLATE** | Harbor packaging scaffold: task.toml |
| [`harbor/template/tests/test.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/template/tests/test.sh) | **TEMPLATE** | Harbor packaging scaffold: tests/test.sh |
| [`harbor/template/tests/test_state.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/harbor/template/tests/test_state.py) | **TEMPLATE** | Harbor packaging scaffold: tests/test_state.py |
| [`infrastructure/README.md`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/README.md) | **HISTORY** | Original Modal GPU endpoint deployment instructions |
| [`infrastructure/agent_runner.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/agent_runner.py) | **HISTORY** | Original Modal mini-SWE-agent runner |
| [`infrastructure/configure_generation.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/configure_generation.py) | **HISTORY** | Original Modal generation environment/secrets setup |
| [`infrastructure/generation_gateway.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/generation_gateway.py) | **HISTORY** | Original Model gateway server on Modal |
| [`infrastructure/generation_models.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/generation_models.py) | **HISTORY** | Original generation model deployments |
| [`infrastructure/serving.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/serving.py) | **HISTORY** | Shared original vLLM model serving helpers |
| [`infrastructure/validator_model.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/infrastructure/validator_model.py) | **HISTORY** | Original validator model deployment |
| [`inputs/008/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/008/data.csv) | **DATA** | Original seed 008 task input (data.csv) |
| [`inputs/016/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/016/data.csv) | **DATA** | Original seed 016 task input (data.csv) |
| [`inputs/025/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/025/data.csv) | **DATA** | Original seed 025 task input (data.csv) |
| [`inputs/026/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/026/data.csv) | **DATA** | Original seed 026 task input (data.csv) |
| [`inputs/028/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/028/data.csv) | **DATA** | Original seed 028 task input (data.csv) |
| [`inputs/038/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/038/data.csv) | **DATA** | Original seed 038 task input (data.csv) |
| [`inputs/069/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/069/data.csv) | **DATA** | Original seed 069 task input (data.csv) |
| [`inputs/080/checkouts.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/080/checkouts.csv) | **DATA** | Original seed 080 task input (checkouts.csv) |
| [`inputs/125/checkouts.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/125/checkouts.csv) | **DATA** | Original seed 125 task input (checkouts.csv) |
| [`inputs/129/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/129/data.csv) | **DATA** | Original seed 129 task input (data.csv) |
| [`inputs/130/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/130/data.csv) | **DATA** | Original seed 130 task input (data.csv) |
| [`inputs/168/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/168/data.csv) | **DATA** | Original seed 168 task input (data.csv) |
| [`inputs/183/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/183/data.csv) | **DATA** | Original seed 183 task input (data.csv) |
| [`inputs/191/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/191/data.csv) | **DATA** | Original seed 191 task input (data.csv) |
| [`inputs/195/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/195/data.csv) | **DATA** | Original seed 195 task input (data.csv) |
| [`inputs/208/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/208/data.csv) | **DATA** | Original seed 208 task input (data.csv) |
| [`inputs/212/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/212/data.csv) | **DATA** | Original seed 212 task input (data.csv) |
| [`inputs/213/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/213/data.csv) | **DATA** | Original seed 213 task input (data.csv) |
| [`inputs/214/data.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/inputs/214/data.csv) | **DATA** | Original seed 214 task input (data.csv) |
| [`integrations/__init__.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/__init__.py) | **SUPPORT** | Package initializer |
| [`integrations/chart_build_context.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/chart_build_context.py) | **SUPPORT** | Allowlisted temporary Docker build-context assembly |
| [`integrations/chart_controller.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/chart_controller.py) | **SUPPORT** | Offline step-by-step chart agent tool-call state machine |
| [`integrations/chart_image_recipe.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/chart_image_recipe.py) | **HISTORY** | Offline planned chart-capable Dockerfile recipe |
| [`integrations/chart_transfer.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/chart_transfer.py) | **SUPPORT** | Validated CSV staging and figure extraction planning |
| [`integrations/chart_wheel_lock.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/chart_wheel_lock.py) | **SUPPORT** | Chart wheel metadata and hash audit |
| [`integrations/judge.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/judge.py) | **HISTORY** | Experimental structured vision-judgment payload helpers |
| [`integrations/models.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/models.py) | **SUPPORT** | Model role, ID, provider and API-style registry |
| [`integrations/providers/__init__.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/providers/__init__.py) | **SUPPORT** | Provider adapter exports |
| [`integrations/providers/base.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/providers/base.py) | **SUPPORT** | Parse normalized provider messages and tool calls |
| [`integrations/providers/client.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/providers/client.py) | **SUPPORT** | Gated provider request preview and one-call transport |
| [`integrations/providers/deepseek.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/providers/deepseek.py) | **SUPPORT** | DeepSeek Responses API request builder |
| [`integrations/providers/openai.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/providers/openai.py) | **SUPPORT** | OpenAI Responses API request builder |
| [`integrations/providers/zai.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/providers/zai.py) | **SUPPORT** | Z.ai Chat Completions API request builder |
| [`integrations/sandbox_gateway.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/sandbox_gateway.py) | **SUPPORT** | Explicit-approval sandbox gateway and resource controls |
| [`integrations/task_artifacts.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/integrations/task_artifacts.py) | **SUPPORT** | CSV snapshot and PNG artifact validation |
| [`labels.example.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/labels.example.json) | **TEMPLATE** | Example human-label schema |
| [`labels.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/labels.json) | **DATA** | Human labels for the 15 authored agent runs |
| [`output/.gitkeep`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/.gitkeep) | **HISTORY** | Placeholder for initially empty result directory |
| [`output/authored_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/authored_predictions.json) | **RESULT** | Saved predictions for authored experiment |
| [`output/authored_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/authored_score.txt) | **RESULT** | Saved scores for authored experiment |
| [`output/baseline_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/baseline_predictions.json) | **RESULT** | Saved predictions for baseline experiment |
| [`output/baseline_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/baseline_score.txt) | **RESULT** | Saved scores for baseline experiment |
| [`output/check_submission.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/check_submission.txt) | **RESULT** | Recorded Harbor oracle/mutant rewards and submission check |
| [`output/final_seed_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/final_seed_predictions.json) | **RESULT** | Saved predictions for final_seed experiment |
| [`output/final_seed_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/final_seed_score.txt) | **RESULT** | Saved scores for final_seed experiment |
| [`output/part4a_authored_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4a_authored_predictions.json) | **RESULT** | Saved predictions for part4a_authored experiment |
| [`output/part4a_authored_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4a_authored_score.txt) | **RESULT** | Saved scores for part4a_authored experiment |
| [`output/part4a_seed_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4a_seed_predictions.json) | **RESULT** | Saved predictions for part4a_seed experiment |
| [`output/part4a_seed_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4a_seed_score.txt) | **RESULT** | Saved scores for part4a_seed experiment |
| [`output/part4b_authored_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4b_authored_predictions.json) | **RESULT** | Saved predictions for part4b_authored experiment |
| [`output/part4b_authored_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4b_authored_score.txt) | **RESULT** | Saved scores for part4b_authored experiment |
| [`output/part4b_seed_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4b_seed_predictions.json) | **RESULT** | Saved predictions for part4b_seed experiment |
| [`output/part4b_seed_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/part4b_seed_score.txt) | **RESULT** | Saved scores for part4b_seed experiment |
| [`output/pre_iteration_authored_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/pre_iteration_authored_predictions.json) | **RESULT** | Saved predictions for pre_iteration_authored experiment |
| [`output/pre_iteration_authored_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/pre_iteration_authored_score.txt) | **RESULT** | Saved scores for pre_iteration_authored experiment |
| [`output/pre_iteration_seed_predictions.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/pre_iteration_seed_predictions.json) | **RESULT** | Saved predictions for pre_iteration_seed experiment |
| [`output/pre_iteration_seed_score.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/pre_iteration_seed_score.txt) | **RESULT** | Saved scores for pre_iteration_seed experiment |
| [`output/provider_compat_agent_a.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/provider_compat_agent_a.json) | **HISTORY** | Saved provider API compatibility probe result |
| [`output/provider_compat_agent_b.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/provider_compat_agent_b.json) | **HISTORY** | Saved provider API compatibility probe result |
| [`output/provider_compat_agent_c.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/provider_compat_agent_c.json) | **HISTORY** | Saved provider API compatibility probe result |
| [`output/provider_compat_agent_c_glm-5.3-flash.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/provider_compat_agent_c_glm-5.3-flash.json) | **HISTORY** | Saved provider API compatibility probe result |
| [`output/provider_compat_experimental_judge_gpt-6.1-terra.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/provider_compat_experimental_judge_gpt-6.1-terra.json) | **HISTORY** | Saved provider API compatibility probe result |
| [`output/session005_openai_004_hard_to_read_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session005_openai_004_hard_to_read_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session005_openai_004_wrong_chart_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session005_openai_004_wrong_chart_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session005_openai_004_wrong_data_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session005_openai_004_wrong_data_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session005_openai_008_hard_to_read_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session005_openai_008_hard_to_read_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session005_openai_008_wrong_chart_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session005_openai_008_wrong_chart_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session005_openai_008_wrong_data_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session005_openai_008_wrong_data_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session007_openai_004_wrong_chart_v2_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session007_openai_004_wrong_chart_v2_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`output/session007_openai_008_wrong_chart_v2_decision.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/output/session007_openai_008_wrong_chart_v2_decision.json) | **HISTORY** | Saved early seed-judgment experiment |
| [`pyproject.toml`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/pyproject.toml) | **CORE** | Python project dependencies and packaging configuration |
| [`report.pdf`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/report.pdf) | **RESULT** | Compiled final assignment report |
| [`report.tex`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/report.tex) | **SUPPORT** | Editable final report in LaTeX |
| [`report_template.tex`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/report_template.tex) | **TEMPLATE** | Blank report scaffold retained for comparison |
| [`requirements/chart-cp312-linux-amd64.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/requirements/chart-cp312-linux-amd64.txt) | **SUPPORT** | Audited CPython 3.12/Linux chart wheel hashes |
| [`runs/.gitkeep`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/.gitkeep) | **HISTORY** | Tracks initially empty agent-runs directory |
| [`runs/dense-department-budgets__deepseek/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/dense-department-budgets__deepseek/figure.png) | **RESULT** | Saved output chart: dense-department-budgets__deepseek |
| [`runs/dense-department-budgets__deepseek/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/dense-department-budgets__deepseek/result.json) | **RESULT** | Saved agent trajectory: dense-department-budgets__deepseek |
| [`runs/dense-department-budgets__glm/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/dense-department-budgets__glm/figure.png) | **RESULT** | Saved output chart: dense-department-budgets__glm |
| [`runs/dense-department-budgets__glm/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/dense-department-budgets__glm/result.json) | **RESULT** | Saved agent trajectory: dense-department-budgets__glm |
| [`runs/dense-department-budgets__luna/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/dense-department-budgets__luna/figure.png) | **RESULT** | Saved output chart: dense-department-budgets__luna |
| [`runs/dense-department-budgets__luna/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/dense-department-budgets__luna/result.json) | **RESULT** | Saved agent trajectory: dense-department-budgets__luna |
| [`runs/quarterly-revenue-by-region__deepseek/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__deepseek/figure.png) | **RESULT** | Saved output chart: quarterly-revenue-by-region__deepseek |
| [`runs/quarterly-revenue-by-region__deepseek/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__deepseek/inputs/transactions.csv) | **RESULT** | Saved input snapshot: quarterly-revenue-by-region__deepseek |
| [`runs/quarterly-revenue-by-region__deepseek/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__deepseek/result.json) | **RESULT** | Saved agent trajectory: quarterly-revenue-by-region__deepseek |
| [`runs/quarterly-revenue-by-region__glm/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__glm/figure.png) | **RESULT** | Saved output chart: quarterly-revenue-by-region__glm |
| [`runs/quarterly-revenue-by-region__glm/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__glm/inputs/transactions.csv) | **RESULT** | Saved input snapshot: quarterly-revenue-by-region__glm |
| [`runs/quarterly-revenue-by-region__glm/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__glm/result.json) | **RESULT** | Saved agent trajectory: quarterly-revenue-by-region__glm |
| [`runs/quarterly-revenue-by-region__luna/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__luna/figure.png) | **RESULT** | Saved output chart: quarterly-revenue-by-region__luna |
| [`runs/quarterly-revenue-by-region__luna/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__luna/inputs/transactions.csv) | **RESULT** | Saved input snapshot: quarterly-revenue-by-region__luna |
| [`runs/quarterly-revenue-by-region__luna/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/quarterly-revenue-by-region__luna/result.json) | **RESULT** | Saved agent trajectory: quarterly-revenue-by-region__luna |
| [`runs/sensor-daily-median__deepseek/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__deepseek/figure.png) | **RESULT** | Saved output chart: sensor-daily-median__deepseek |
| [`runs/sensor-daily-median__deepseek/inputs/sensors.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__deepseek/inputs/sensors.csv) | **RESULT** | Saved input snapshot: sensor-daily-median__deepseek |
| [`runs/sensor-daily-median__deepseek/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__deepseek/result.json) | **RESULT** | Saved agent trajectory: sensor-daily-median__deepseek |
| [`runs/sensor-daily-median__glm/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__glm/figure.png) | **RESULT** | Saved output chart: sensor-daily-median__glm |
| [`runs/sensor-daily-median__glm/inputs/sensors.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__glm/inputs/sensors.csv) | **RESULT** | Saved input snapshot: sensor-daily-median__glm |
| [`runs/sensor-daily-median__glm/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__glm/result.json) | **RESULT** | Saved agent trajectory: sensor-daily-median__glm |
| [`runs/sensor-daily-median__luna/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__luna/figure.png) | **RESULT** | Saved output chart: sensor-daily-median__luna |
| [`runs/sensor-daily-median__luna/inputs/sensors.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__luna/inputs/sensors.csv) | **RESULT** | Saved input snapshot: sensor-daily-median__luna |
| [`runs/sensor-daily-median__luna/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/sensor-daily-median__luna/result.json) | **RESULT** | Saved agent trajectory: sensor-daily-median__luna |
| [`runs/styled-decay-curves__deepseek/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/styled-decay-curves__deepseek/figure.png) | **RESULT** | Saved output chart: styled-decay-curves__deepseek |
| [`runs/styled-decay-curves__deepseek/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/styled-decay-curves__deepseek/result.json) | **RESULT** | Saved agent trajectory: styled-decay-curves__deepseek |
| [`runs/styled-decay-curves__glm/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/styled-decay-curves__glm/figure.png) | **RESULT** | Saved output chart: styled-decay-curves__glm |
| [`runs/styled-decay-curves__glm/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/styled-decay-curves__glm/result.json) | **RESULT** | Saved agent trajectory: styled-decay-curves__glm |
| [`runs/styled-decay-curves__luna/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/styled-decay-curves__luna/figure.png) | **RESULT** | Saved output chart: styled-decay-curves__luna |
| [`runs/styled-decay-curves__luna/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/styled-decay-curves__luna/result.json) | **RESULT** | Saved agent trajectory: styled-decay-curves__luna |
| [`runs/top-products-unit-share__deepseek/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__deepseek/figure.png) | **RESULT** | Saved output chart: top-products-unit-share__deepseek |
| [`runs/top-products-unit-share__deepseek/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__deepseek/inputs/transactions.csv) | **RESULT** | Saved input snapshot: top-products-unit-share__deepseek |
| [`runs/top-products-unit-share__deepseek/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__deepseek/result.json) | **RESULT** | Saved agent trajectory: top-products-unit-share__deepseek |
| [`runs/top-products-unit-share__glm/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__glm/figure.png) | **RESULT** | Saved output chart: top-products-unit-share__glm |
| [`runs/top-products-unit-share__glm/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__glm/inputs/transactions.csv) | **RESULT** | Saved input snapshot: top-products-unit-share__glm |
| [`runs/top-products-unit-share__glm/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__glm/result.json) | **RESULT** | Saved agent trajectory: top-products-unit-share__glm |
| [`runs/top-products-unit-share__luna/figure.png`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__luna/figure.png) | **RESULT** | Saved output chart: top-products-unit-share__luna |
| [`runs/top-products-unit-share__luna/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__luna/inputs/transactions.csv) | **RESULT** | Saved input snapshot: top-products-unit-share__luna |
| [`runs/top-products-unit-share__luna/result.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/runs/top-products-unit-share__luna/result.json) | **RESULT** | Saved agent trajectory: top-products-unit-share__luna |
| [`sandbox/Dockerfile`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/sandbox/Dockerfile) | **CORE** | Chart-agent Docker image build recipe |
| [`sandbox/instance_suffix.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/sandbox/instance_suffix.txt) | **CORE** | Agent instruction suffix and completion protocol |
| [`sandbox/requirements.txt`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/sandbox/requirements.txt) | **CORE** | Hashed chart sandbox Python dependencies |
| [`scripts/__init__.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/__init__.py) | **SUPPORT** | Python scripts package namespace |
| [`scripts/build_harbor_tasks.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/build_harbor_tasks.py) | **SUPPORT** | Build complete five Harbor tasks, verifiers and mutants |
| [`scripts/chart_smoke_worker.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/chart_smoke_worker.py) | **SUPPORT** | Render fixed synthetic plot for sandbox smoke tests |
| [`scripts/check_chart_build_context_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_chart_build_context_offline.py) | **SUPPORT** | Run chart build-context regression tests |
| [`scripts/check_chart_image_recipe_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_chart_image_recipe_offline.py) | **SUPPORT** | Run chart Dockerfile-recipe tests |
| [`scripts/check_chart_smoke_preview_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_chart_smoke_preview_offline.py) | **SUPPORT** | Run chart smoke-preview tests |
| [`scripts/check_chart_smoke_worker_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_chart_smoke_worker_offline.py) | **SUPPORT** | Run fixed chart smoke-worker tests |
| [`scripts/check_chart_transfer_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_chart_transfer_offline.py) | **SUPPORT** | Run validated CSV/PNG transfer tests |
| [`scripts/check_chart_wheel_lock_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_chart_wheel_lock_offline.py) | **SUPPORT** | Audit chart-only wheel lock metadata |
| [`scripts/check_controller_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_controller_offline.py) | **SUPPORT** | Run offline controller state-machine tests |
| [`scripts/check_sandbox_gateway_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_sandbox_gateway_offline.py) | **SUPPORT** | Run fake-sandbox gateway tests |
| [`scripts/check_task_artifacts_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/check_task_artifacts_offline.py) | **SUPPORT** | Run CSV/PNG artifact validation tests |
| [`scripts/deploy_agent_runner.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/deploy_agent_runner.sh) | **HISTORY** | Historical Modal agent-runner deployment |
| [`scripts/deploy_generation_models.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/deploy_generation_models.sh) | **HISTORY** | Historical Modal agent-server deployment |
| [`scripts/deploy_validator_model.sh`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/deploy_validator_model.sh) | **HISTORY** | Historical Modal judge-server deployment |
| [`scripts/disagreements.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/disagreements.py) | **SUPPORT** | List saved prediction mistakes versus human labels |
| [`scripts/figure_extract_worker.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/figure_extract_worker.py) | **SUPPORT** | Trusted PNG extraction helper for chart container |
| [`scripts/judge_cost.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/judge_cost.py) | **SUPPORT** | Estimate judge spending from usage logs |
| [`scripts/judge_smoke.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/judge_smoke.py) | **SUPPORT** | One hosted-judge endpoint smoke call |
| [`scripts/make_part3_inputs.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/make_part3_inputs.py) | **SUPPORT** | Deterministically recreate authored-task CSV inputs |
| [`scripts/offline_preflight.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/offline_preflight.py) | **SUPPORT** | Inspect released seed run/PNG/label consistency |
| [`scripts/openai_seed_pilot.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/openai_seed_pilot.py) | **HISTORY** | Early OpenAI image-judgment experiment |
| [`scripts/preview_chart_smoke_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/preview_chart_smoke_offline.py) | **SUPPORT** | Print read-only image-build-context preview |
| [`scripts/provider_compat_probe.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/provider_compat_probe.py) | **SUPPORT** | Offline/live opt-in per-provider compatibility test |
| [`scripts/provider_preflight.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/provider_preflight.py) | **SUPPORT** | Zero-network preview for all configured providers |
| [`scripts/zai_vision_probe.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/scripts/zai_vision_probe.py) | **HISTORY** | Early Z.ai vision payload/API probe |
| [`seed_labels.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/seed_labels.json) | **DATA** | Human labels for the original 110 seed runs |
| [`tasks/.gitkeep`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/.gitkeep) | **HISTORY** | Tracks empty authored-task directory initially |
| [`tasks/dense-department-budgets/task.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/dense-department-budgets/task.json) | **CORE** | Authored instructions and input schema: dense-department-budgets |
| [`tasks/quarterly-revenue-by-region/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/quarterly-revenue-by-region/inputs/transactions.csv) | **CORE** | Authored-task CSV input for quarterly-revenue-by-region |
| [`tasks/quarterly-revenue-by-region/task.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/quarterly-revenue-by-region/task.json) | **CORE** | Authored instructions and input schema: quarterly-revenue-by-region |
| [`tasks/sensor-daily-median/inputs/sensors.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/sensor-daily-median/inputs/sensors.csv) | **CORE** | Authored-task CSV input for sensor-daily-median |
| [`tasks/sensor-daily-median/task.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/sensor-daily-median/task.json) | **CORE** | Authored instructions and input schema: sensor-daily-median |
| [`tasks/styled-decay-curves/task.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/styled-decay-curves/task.json) | **CORE** | Authored instructions and input schema: styled-decay-curves |
| [`tasks/top-products-unit-share/inputs/transactions.csv`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/top-products-unit-share/inputs/transactions.csv) | **CORE** | Authored-task CSV input for top-products-unit-share |
| [`tasks/top-products-unit-share/task.json`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tasks/top-products-unit-share/task.json) | **CORE** | Authored instructions and input schema: top-products-unit-share |
| [`tests/test_chart_build_context_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_chart_build_context_offline.py) | **SUPPORT** | Offline regression tests: chart build context |
| [`tests/test_chart_image_recipe_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_chart_image_recipe_offline.py) | **SUPPORT** | Offline regression tests: chart image recipe |
| [`tests/test_chart_smoke_preview_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_chart_smoke_preview_offline.py) | **SUPPORT** | Offline regression tests: chart smoke preview |
| [`tests/test_chart_smoke_worker_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_chart_smoke_worker_offline.py) | **SUPPORT** | Offline regression tests: chart smoke worker |
| [`tests/test_chart_transfer_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_chart_transfer_offline.py) | **SUPPORT** | Offline regression tests: chart transfer |
| [`tests/test_controller_state_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_controller_state_offline.py) | **SUPPORT** | Offline regression tests: controller state |
| [`tests/test_offline_preflight.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_offline_preflight.py) | **SUPPORT** | Offline regression tests: offline preflight.py |
| [`tests/test_provider_compat_probe_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_provider_compat_probe_offline.py) | **SUPPORT** | Offline regression tests: provider compat probe |
| [`tests/test_provider_deepseek_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_provider_deepseek_offline.py) | **SUPPORT** | Offline regression tests: provider deepseek |
| [`tests/test_provider_openai_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_provider_openai_offline.py) | **SUPPORT** | Offline regression tests: provider openai |
| [`tests/test_provider_registry_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_provider_registry_offline.py) | **SUPPORT** | Offline regression tests: provider registry |
| [`tests/test_provider_zai_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_provider_zai_offline.py) | **SUPPORT** | Offline regression tests: provider zai |
| [`tests/test_sandbox_gateway_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_sandbox_gateway_offline.py) | **SUPPORT** | Offline regression tests: sandbox gateway |
| [`tests/test_sandbox_generate_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_sandbox_generate_offline.py) | **SUPPORT** | Offline regression tests: sandbox generate |
| [`tests/test_task_artifacts_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_task_artifacts_offline.py) | **SUPPORT** | Offline regression tests: task artifacts |
| [`tests/test_validator_openai_seed_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_validator_openai_seed_offline.py) | **SUPPORT** | Offline regression tests: validator openai seed |
| [`tests/test_validator_semantic_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_validator_semantic_offline.py) | **SUPPORT** | Offline regression tests: validator semantic |
| [`tests/test_validator_solution_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_validator_solution_offline.py) | **SUPPORT** | Offline regression tests: validator solution |
| [`tests/test_validator_vision_probe_offline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/tests/test_validator_vision_probe_offline.py) | **SUPPORT** | Offline regression tests: validator vision probe |
| [`uv.lock`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/uv.lock) | **SUPPORT** | Pinned resolved Python dependency graph |
| [`validator/__init__.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/validator/__init__.py) | **CORE** | Python package initializer |
| [`validator/baseline.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/validator/baseline.py) | **SUPPORT** | Reference validator for comparison with final design |
| [`validator/model.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/validator/model.py) | **CORE** | Hosted vision-judge client and request adaptation |
| [`validator/prediction.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/validator/prediction.py) | **CORE** | Typed error families and prediction JSON schema |
| [`validator/runner.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/validator/runner.py) | **CORE** | Batch prediction generation with retry/resume |
| [`validator/solution.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/validator/solution.py) | **CORE** | Final artifact-gated, structured AI chart validator |
| [`workflow/__init__.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/__init__.py) | **CORE** | Python package initializer |
| [`workflow/__main__.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/__main__.py) | **CORE** | CLI command dispatcher |
| [`workflow/evaluate.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/evaluate.py) | **CORE** | Human-label validation and MCC scoring |
| [`workflow/generate.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/generate.py) | **HISTORY** | Original Modal-driven authored-task generator |
| [`workflow/harbor_rewards.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/harbor_rewards.py) | **CORE** | Run Harbor oracles/mutants and verify rewards |
| [`workflow/package.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/package.py) | **SUPPORT** | Generate Harbor task scaffolds from task JSON |
| [`workflow/sandbox_generate.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/sandbox_generate.py) | **CORE** | Adapted live hosted-agent Docker generation runner |
| [`workflow/submission.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/submission.py) | **CORE** | Full submission structure and reward validation |
| [`workflow/tasks.py`](https://github.com/xqzr2000/cmu-11-768-assignment-2/blob/main/workflow/tasks.py) | **CORE** | Load and validate authored visualization task descriptors |

---

**Source verification note:** The tracked-path inventory, directory structure and file roles were inspected using the linked GitHub repository on November 9, 2026. Descriptions are based on file contents, program docstrings, the repository's README and original assignment documentation. This is a repository **reading guide**, not an execution audit of the live provider services or a fresh benchmark. For any file changed after this snapshot, consult the current GitHub source.
