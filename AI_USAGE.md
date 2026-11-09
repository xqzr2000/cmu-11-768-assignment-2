# AI usage

This is an independent, non-credit reproduction of 11-768 Assignment 2. AI tools
were used heavily; this file says exactly where.

## Tools

- **Claude (Anthropic), Claude Opus 5.5 via claude.ai with a code workspace.**
  Primary engineering assistant for the work on the `finish-assignment` branch.
- **An earlier AI coding assistant** (Sessions 001–014 on `main`) built the
  offline infrastructure: provider adapters, controller, the build-context and
  image-recipe modules, and the learning journal in `docs/Learning-Progress.md`.
- **Models used *as part of the experiment*, not as authoring assistants:**
  GPT-6.1 Terra (judge inside `validator/solution.py` and the baseline),
  DeepSeek Flash, GPT-5.6 Luna and GLM-5.3 Flash (the three chart agents).

## What Claude did on `finish-assignment`

- Reviewed the repository, proposed the plan, and asked the decisions that
  were mine to make: judge model, agent models, spending cap, sandbox approach.
- Wrote: the Terra adaptations in `validator/model.py`; `--workers` in
  `validator/runner.py`; `workflow/sandbox_generate.py` and `sandbox/` (agent
  runner on my Assignment 1 Docker sandbox); `scripts/judge_smoke.py`,
  `judge_cost.py`, `disagreements.py`, `make_part3_inputs.py`,
  `build_harbor_tasks.py`; `harbor/shared/verifier_core.py`; the offline tests.
- Analysed the baseline disagreements and proposed the two Part 1 error types;
  designed and implemented the Part 2 and Part 4 validator changes in
  `validator/solution.py`, including the 4a → 4b calibration.
- Designed the five Part 3 tasks, their synthetic data, reference solutions,
  verifiers and both mutants, and checked them in a local stand-in for Harbor.
- **Labels:** drafted every entry in `labels.json` by replaying each run under
  the savefig hook, checking values against independent answer keys, and
  inspecting each figure. I reviewed the drafts against the figures and kept
  them.
- Drafted `report.tex` and this file.

## What I did

- Ran everything that needed my API keys or Docker in my Codespace: the judge
  smoke test, image build, baseline and validator passes, the 15 agent runs,
  and `check-submission` with real Harbor. I also pushed the outputs.
- Made the model, cost and sandbox decisions; reviewed labels; reviewed the
  report.

## Things to know when reading this submission

- Nothing here uses the course's fixed Qwen3-VL judge or the fixed agents, so the
  MCCs are not comparable to course results (see the report's first paragraph).
- No public run IDs or labels are hard-coded in the validator; labels are read
  only by the scoring and analysis scripts.
