"""List every run where a validator and the human labels disagree, per family.

    uv run python scripts/disagreements.py output/baseline_predictions.json \
        [--labels seed_labels.json] [--artifacts artifacts] [--out output/x.md]

Post-hoc analysis only: reads human labels after predictions exist, never the
other way round. For each family, prints false positives and false negatives
with the task excerpt, the human evidence and the validator's evidence, using
the scorer's convention that runs labelled execution_failure are excluded from
the other three families.
"""

import argparse
import json
from pathlib import Path

FAMILIES = ("execution_failure", "wrong_data", "wrong_chart", "hard_to_read")


def _families(errors: list[dict]) -> dict[str, str]:
    return {e["family"]: e.get("evidence", "") for e in errors or []}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--labels", type=Path, default=Path("seed_labels.json"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    labels = {x["run_id"]: _families(x["errors"])
              for x in json.loads(args.labels.read_text())["labels"]}
    preds = {x["run_id"]: _families(x["errors"])
             for x in json.loads(args.predictions.read_text())["predictions"]}
    lines = [f"# Disagreements: {args.predictions.name} vs {args.labels.name}", ""]
    for family in FAMILIES:
        fp, fn = [], []
        for run_id in sorted(set(labels) & set(preds)):
            human, model = labels[run_id], preds[run_id]
            if family != "execution_failure" and "execution_failure" in human:
                continue
            if family in model and family not in human:
                fp.append(run_id)
            elif family in human and family not in model:
                fn.append(run_id)
        lines += [f"## {family}: {len(fp)} false positives, {len(fn)} false negatives", ""]
        for kind, ids in (("FP", fp), ("FN", fn)):
            for run_id in ids:
                record = json.loads((args.artifacts / run_id / "result.json").read_text())
                task = " ".join(record["task"]["instructions"].split())[:400]
                lines += [
                    f"### {kind} {run_id}",
                    f"- task: {task}",
                    f"- human: {sorted(labels[run_id]) or 'acceptable'}"
                    + (f" — {labels[run_id][family]}" if family in labels[run_id] else ""),
                    f"- validator: {sorted(preds[run_id]) or 'acceptable'}"
                    + (f" — {preds[run_id][family][:400]}" if family in preds[run_id] else ""),
                    "",
                ]
    text = "\n".join(lines)
    if args.out:
        args.out.write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
