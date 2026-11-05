# Upstream sources and reproducibility

## Starter code

- Origin: https://github.com/cmu-agents/assignment-2
- **Pinned source revision:** `f609e76d2efd302b4b8babee06c5592899010b8b`
- Imported by copying the full repository tree **without** importing its separate Git history or credentials.
- The official `ASSIGNMENT.md`, `seed_labels.json`, `artifacts/`, `validator/`, `workflow/`, `infrastructure/`, `harbor/`, and `tasks/` are retained. Downstream adaptations should be documented and reviewed.
- The project's `uv.lock` records the full resolved Python dependency graph. The first import ran via a one-time GitHub Actions bootstrap on the feature branch. The import and lockfile bootstrap workflows were removed after completion to avoid stale automation.
- **Not a fork/merge:** the resulting repository intentionally has an independent history. To compare later changes, use a clone of the exact pinned upstream revision.

## Sandbox dependency

- Origin: https://github.com/xqzr2000/cmu-11-768-assignment-1
- **Pinned revision:** `0cb0534c2fffb67ddfff619100057fad0be90a3c`
- Package subdirectory: `packages/agent-sandbox-runtime`
- Source is referenced as a pinned Git dependency from `pyproject.toml`; the package is **not** vendored.
- The Docker sandbox is a controlled-development boundary, not hardened for hostile multi-tenant code. No secrets should be passed into the agent's execution container.

## Infrastructure departures

The official starter's `infrastructure/` files and `workflow/generate.py` still reference Modal. We preserve them as upstream reference implementations but do not deploy them. An independent local runner will be added in a later phase. Do not run `scripts/deploy_*.sh` while following our non-Modal path.

Original model-serving configuration and grading are not reproduced by the Phase 0 checks.
