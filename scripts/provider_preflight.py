"""Zero-network preview of the four experimental provider configurations."""

from __future__ import annotations

import json

from integrations.models import MODELS
from integrations.providers import preview_request
from integrations.judge import JUDGMENT_SCHEMA


def main() -> None:
    items = [{"role": "user", "content": "Describe how you would plot a small dataset."}]
    rows = []
    for spec in MODELS.values():
        rows.append(preview_request(
            spec, items, schema=JUDGMENT_SCHEMA if spec.is_judge else None
        ))
    print(json.dumps({"mode": "offline", "network_requests": 0,
                      "models": rows}, indent=2))


if __name__ == "__main__":
    main()
