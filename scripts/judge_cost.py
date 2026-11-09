"""Summarize judge spend from VALIDATOR_USAGE_LOG (default output/judge_usage.jsonl).

    uv run python scripts/judge_cost.py [path] [--input 1.0 --cached 0.05 --output 5.0]

Prices are USD per million tokens; defaults are GPT-6.1 Terra standard rates.
Pass --flex to halve them.
"""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="output/judge_usage.jsonl")
    parser.add_argument("--input", type=float, default=1.0)
    parser.add_argument("--cached", type=float, default=0.05)
    parser.add_argument("--output", type=float, default=5.0)
    parser.add_argument("--flex", action="store_true")
    args = parser.parse_args()

    calls = prompt = cached = completion = reasoning = 0
    for line in Path(args.path).read_text().splitlines():
        record = json.loads(line)
        calls += 1
        prompt += record.get("prompt_tokens") or 0
        cached += record.get("cached_tokens") or 0
        completion += record.get("completion_tokens") or 0
        reasoning += record.get("reasoning_tokens") or 0
    factor = 0.5 if args.flex else 1.0
    cost = factor * ((prompt - cached) * args.input + cached * args.cached
                     + completion * args.output) / 1e6
    print(f"calls={calls} prompt={prompt} (cached {cached}) "
          f"completion={completion} (reasoning {reasoning})")
    print(f"estimated cost: ${cost:.2f}")


if __name__ == "__main__":
    main()
