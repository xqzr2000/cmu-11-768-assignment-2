# Phase 0: reproducible offline dataset inspection

**Goal:** establish a trustworthy, zero-inference evaluation starting point before spending tokens or provisioning compute.

## Preconditions

- Python 3.12 and `uv` for the official project; GitHub Codespaces is supported.
- No Modal account, GPU, Z.ai key, or other model API is required.
- Official seed data and human labels are present at the pinned upstream revision (see `UPSTREAM.md`).

## Checks

```bash
uv sync --locked
uv run python scripts/offline_preflight.py
uv run python -m unittest discover -s tests -p 'test_offline_*.py'
```

The preflight checks exact run-ID coverage between the released `artifacts/*/result.json` and `seed_labels.json`, parses trajectories and instructions, verifies PNG magic and positive image dimensions, checks nonblank evidence and permitted error-family values, enforces the execution-failure terminal rule, and prints class frequencies. It does **not** evaluate whether human labels are correct.

Known released inventory at initial inspection: 110 labeled runs, 98 `figure.png` artifacts, 16 fully acceptable labels; family presence counts: execution_failure=12, wrong_data=25, wrong_chart=71, hard_to_read=39. These are **descriptive human-label counts**, not model performance metrics.

## Completion criteria

- [x] Full official starter imported on feature branch from pinned source revision.
- [x] Sandbox package dependency pinned to a specific Assignment 1 commit.
- [x] Offline preflight successfully checks the original fixtures.
- [x] Offline unit tests pass in CI.
- [x] No credentials and no model inference in the preflight process.
- [ ] Open PR reviewed before merging into `main`.

The pinned Python dependency graph is captured in `uv.lock`; use `uv sync --locked` to check that the lockfile matches `pyproject.toml`.

## Next milestone

Start with targeted inspection of the official `validator/baseline.py` and representative false-positive/false-negative examples. Obtain a verified **image-capable** validator endpoint before claiming a VLM baseline. A Z.ai GLM API test proves basic inference and function-calling access only, not suitability as the image validator.

Do not use the upstream `workflow generate` command yet: it still targets Modal. Future work will provide a separate Docker-backed runner.
