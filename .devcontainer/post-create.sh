#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
export UV_LINK_MODE=copy
uv sync --locked
uv run python scripts/offline_preflight.py
echo "Offline setup complete. ZAI_API_KEY is not required for Phase 0."
