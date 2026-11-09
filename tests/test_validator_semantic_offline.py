"""Offline tests for the checklist and readability judge calls in validator.solution.

The judge is replaced by a scripted `complete`; no network, no labels.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from validator import solution
from validator.prediction import ErrorFamily
from validator.runner import Run


def reply(payload: object) -> dict:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return {"choices": [{"message": {"content": text}}]}


def item(kind: str, status: str, requirement: str = "req", evidence: str = "ev") -> dict:
    return {"requirement": requirement, "kind": kind, "status": status, "evidence": evidence}


class ScriptedJudge:
    def __init__(self, *replies: dict) -> None:
        self.replies = list(replies)
        self.calls: list[dict] = []

    def __call__(self, messages, **options):
        self.calls.append({"messages": messages, "options": options})
        return self.replies.pop(0)

    def text(self, index: int) -> str:
        content = self.calls[index]["messages"][0]["content"]
        return "\n".join(part.get("text", "") for part in content if part["type"] == "text")


class SolutionJudgeTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.figure = root / "figure.png"
        Image.new("RGB", (640, 480), "white").save(self.figure, dpi=(100, 100))
        Image.open(self.figure).close()
        csv = root / "data.csv"
        csv.write_text("region,sales\nnorth,10\nsouth,20\n")
        self.run = Run(
            run_id="synthetic", task_id="synthetic",
            instructions="Bar chart of sales by region, sorted descending, viridis.",
            messages=[
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "task text"},
                {"role": "assistant", "content": "plotting", "tool_calls": [{"function": {
                    "name": "bash", "arguments": json.dumps({"command": "python plot.py"})}}]},
                {"role": "tool", "content": json.dumps(
                    {"returncode": 0, "output": "x" * 5000})},
                {"role": "exit", "content": "", "extra": {"exit_status": "Submitted"}},
            ],
            figure=self.figure, inputs={"data.csv": csv},
        )

    def validate(self, *replies: dict) -> tuple[list, ScriptedJudge]:
        judge = ScriptedJudge(*replies)
        with patch.object(solution, "complete", judge):
            return solution.validate(self.run), judge

    def test_clean_run_is_acceptable_with_two_calls(self) -> None:
        errors, judge = self.validate(
            reply({"requirements": [item("data", "met"), item("design", "met")]}),
            reply({"overlays": [], "issues": []}))
        self.assertEqual(errors, [])
        self.assertEqual(len(judge.calls), 2)

    def test_design_violation_is_wrong_chart_only(self) -> None:
        errors, _ = self.validate(
            reply({"requirements": [item("data", "met"),
                                    item("design", "violated", "viridis colormap", "uses jet")]}),
            reply({"overlays": [], "issues": []}))
        self.assertEqual([e.family for e in errors], [ErrorFamily.WRONG_CHART])
        self.assertIn("uses jet", errors[0].evidence)

    def test_data_violation_is_wrong_data_and_unclear_is_ignored(self) -> None:
        errors, _ = self.validate(
            reply({"requirements": [item("data", "violated", "sorted", "unsorted"),
                                    item("design", "unclear")]}),
            reply({"overlays": [], "issues": []}))
        self.assertEqual([e.family for e in errors], [ErrorFamily.WRONG_DATA])

    def test_only_major_readability_issues_count(self) -> None:
        minor = {"category": "overlapping_text", "where": "x ticks",
                 "description": "slightly tight", "severity": "minor"}
        major = dict(minor, severity="major", description="labels overprint")
        errors, _ = self.validate(reply({"requirements": []}), reply({"overlays": [], "issues": [minor]}))
        self.assertEqual(errors, [])
        errors, _ = self.validate(reply({"requirements": []}), reply({"overlays": [], "issues": [minor, major]}))
        self.assertEqual([e.family for e in errors], [ErrorFamily.HARD_TO_READ])
        self.assertIn("labels overprint", errors[0].evidence)
        self.assertNotIn("slightly tight", errors[0].evidence)

    def test_checklist_request_carries_task_inputs_transcript_facts_and_image(self) -> None:
        _, judge = self.validate(reply({"requirements": []}), reply({"overlays": [], "issues": []}))
        text = judge.text(0)
        self.assertIn("sorted descending", text)
        self.assertIn("north,10", text)
        self.assertIn("$ python plot.py", text)
        self.assertIn("pixel size 640x480", text)
        self.assertIn("DPI metadata 100", text)
        self.assertIn("characters omitted", text)  # long tool output is clipped
        parts = judge.calls[0]["messages"][0]["content"]
        self.assertTrue(any(p["type"] == "image_url" for p in parts))
        self.assertEqual(judge.calls[0]["options"]["response_format"]["type"], "json_schema")
        # The readability call never sees the transcript or the code.
        self.assertNotIn("python plot.py", judge.text(1))

    def test_fenced_json_is_parsed(self) -> None:
        fenced = "```json\n" + json.dumps({"requirements": [item("data", "violated")]}) + "\n```"
        errors, _ = self.validate(reply(fenced), reply({"overlays": [], "issues": []}))
        self.assertEqual([e.family for e in errors], [ErrorFamily.WRONG_DATA])

    def test_bad_json_is_retried_then_raised_not_accepted(self) -> None:
        errors, judge = self.validate(reply("oops"), reply({"requirements": []}),
                                      reply({"overlays": [], "issues": []}))
        self.assertEqual(errors, [])
        self.assertEqual(len(judge.calls), 3)
        with self.assertRaises(ValueError):
            self.validate(reply("oops"), reply("still not json"))

    def test_legibility_requirements_never_become_wrong_chart(self) -> None:
        errors, _ = self.validate(
            reply({"requirements": [item("legibility", "violated", "labels must not overlap"),
                                    item("design", "met")]}),
            reply({"overlays": [], "issues": []}))
        self.assertEqual(errors, [])

    def test_overlay_over_data_is_hard_to_read_even_if_issues_empty(self) -> None:
        over_band = {"element": "legend (upper left)", "covers": "data", "hides_information": True,
                     "detail": "hides the band's upper edge near 06-02"}
        over_grid = {"element": "legend", "covers": "empty_space_or_gridlines",
                     "hides_information": False, "detail": "-"}
        on_segment = {"element": "value label 34", "covers": "data", "hides_information": False,
                      "detail": "written on its own bar segment"}
        errors, _ = self.validate(reply({"requirements": []}),
                                  reply({"overlays": [over_grid, on_segment], "issues": []}))
        self.assertEqual(errors, [])
        errors, _ = self.validate(reply({"requirements": []}),
                                  reply({"overlays": [over_grid, over_band], "issues": []}))
        self.assertEqual([e.family for e in errors], [ErrorFamily.HARD_TO_READ])
        self.assertIn("band's upper edge", errors[0].evidence)

    def test_readability_call_gets_whole_image_plus_four_enlarged_quadrants(self) -> None:
        _, judge = self.validate(reply({"requirements": []}), reply({"overlays": [], "issues": []}))
        images = [p for p in judge.calls[1]["messages"][0]["content"] if p["type"] == "image_url"]
        self.assertEqual(len(images), 5)
        self.assertEqual(len([p for p in judge.calls[0]["messages"][0]["content"]
                              if p["type"] == "image_url"]), 1)

    def test_blank_image_is_reported_in_facts(self) -> None:
        self.assertIn("blank", solution.image_facts(self.figure))


if __name__ == "__main__":
    unittest.main()
