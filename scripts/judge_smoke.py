"""One judge call on one seed run, to confirm the endpoint before a full pass.

    uv run python scripts/judge_smoke.py [--run-id 004]

Sends the run's task, figure and a one-line question through validator.model,
the same client the validator uses, then prints the reply, finish reason and
token usage. Costs a fraction of a cent.
"""

import argparse
import base64
import json
from pathlib import Path

from validator import model
from validator.runner import RELEASE, Run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="004")
    args = parser.parse_args()

    run = Run.load(RELEASE / "artifacts" / args.run_id, RELEASE)
    if run.figure is None:
        raise SystemExit(f"run {args.run_id} has no figure; pick another")
    image = base64.b64encode(run.figure.read_bytes()).decode()
    content = [
        {"type": "text", "text": (
            "In one sentence, describe the chart in this image, then on a new "
            "line answer YES or NO: does it plausibly match this request?\n\n"
            f"Request: {run.instructions[:1500]}"
        )},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}},
    ]
    print(f"model={model.MODEL} reasoning_effort={model.REASONING_EFFORT} "
          f"service_tier={model.SERVICE_TIER}")
    response = model.complete([{"role": "user", "content": content}], max_tokens=250)
    choice = response["choices"][0]
    print("finish_reason:", choice.get("finish_reason"))
    print("reply:", (choice["message"].get("content") or "").strip() or "(empty)")
    print("usage:", json.dumps(response.get("usage"), indent=2))
    print("adapted params: max_completion_tokens=%s drop_temperature=%s"
          % (model._RENAME_MAX_TOKENS, model._DROP_TEMPERATURE))


if __name__ == "__main__":
    main()
