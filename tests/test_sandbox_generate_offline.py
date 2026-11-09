"""Offline end-to-end test of workflow.sandbox_generate with scripted model replies.

No network and no Docker: replies are canned per provider API style, and commands
run in LocalWorkspace (a temp dir). Checks that a run writes a seed-compatible
result.json + figure.png that validator.runner.Run.load can read.
"""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from validator.runner import Run
from workflow import sandbox_generate as sg
from workflow.generate import AGENT_BY_KEY, write_result
from workflow.tasks import load_tasks

PLOT = (
    "cat > plot.py <<'EOF'\nimport pandas as pd, matplotlib.pyplot as plt\n"
    "d = pd.read_csv('data.csv')\nplt.bar(d.x, d.y)\nplt.savefig('figure.png')\nEOF\n"
    "python plot.py && ls figure.png"
)
COMMANDS = ["cat data.csv", PLOT, f"echo {sg.SUBMIT}"]


def responses_reply(step: int, command: str) -> dict:
    return {
        "status": "completed", "model": "fake-responses",
        "output": [
            {"type": "reasoning", "id": f"rs_{step}", "summary": []},
            {"type": "function_call", "id": f"fc_{step}", "call_id": f"call_{step}",
             "name": "bash", "arguments": json.dumps({"command": command})},
        ],
        "usage": {"input_tokens": 100, "output_tokens": 20},
    }


def chat_reply(step: int, command: str | None) -> dict:
    message = {"content": "thinking", "tool_calls": []}
    finish = "stop"
    if command is not None:
        finish = "tool_calls"
        message["tool_calls"] = [{"id": f"t{step}", "type": "function", "function": {
            "name": "bash", "arguments": json.dumps({"command": command})}}]
    return {"model": "fake-chat", "choices": [{"finish_reason": finish, "message": message}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 10}}


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        create = self._create
        self.responses = type("R", (), {"create": staticmethod(create)})()
        self.chat = type("C", (), {"completions": type("CC", (), {
            "create": staticmethod(create)})()})()

    def _create(self, **request):
        self.requests.append(copy.deepcopy(request))
        return self.replies.pop(0)


class SandboxGenerateOffline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        task_dir = root / "tasks" / "bars"
        (task_dir / "inputs").mkdir(parents=True)
        (task_dir / "inputs" / "data.csv").write_text("x,y\na,1\nb,3\n")
        (task_dir / "task.json").write_text(json.dumps({
            "task_id": "bars", "task_class": "demo",
            "instructions": "Read data.csv and draw a bar chart of y by x. Save figure.png.",
            "inputs": [{"name": "data.csv", "path": "inputs/data.csv"}],
        }))
        self.root = root
        self.task, self.descriptor = load_tasks(root / "tasks")[0]

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, key, replies):
        client = FakeClient(replies)
        with mock.patch.object(sg, "_client", return_value=client):
            result = sg.run_one(self.task, self.descriptor, AGENT_BY_KEY[key],
                                image="unused", local=True)
        out = write_result(self.task, self.descriptor, AGENT_BY_KEY[key],
                           self.root / "runs", result, force=False)
        return client, result, out

    def test_responses_agent_submits_and_writes_loadable_run(self):
        client, result, out = self._run(
            "luna", [responses_reply(i, c) for i, c in enumerate(COMMANDS)])
        self.assertEqual(result["outcome"]["exit_status"], "Submitted")
        self.assertTrue(result["artifact_present"])
        self.assertIsNone(result["artifact_error"])
        self.assertEqual(client.requests[0]["include"], ["reasoning.encrypted_content"])
        # The second request replays the first call's output under its call_id.
        replayed = client.requests[1]["input"]
        self.assertIn({"type": "function_call_output", "call_id": "call_0",
                       "output": mock.ANY}, replayed)
        run = Run.load(out, self.root)
        self.assertIsNotNone(run.figure)
        self.assertEqual(run.messages[0]["role"], "system")
        self.assertTrue(run.messages[1]["content"].startswith("Please solve this issue"))
        self.assertEqual(run.messages[-1]["extra"]["exit_status"], "Submitted")
        record = json.loads((out / "result.json").read_text())
        self.assertEqual(record["agent"], {"key": "luna", "model": "gpt-5.6-luna"})

    def test_chat_agent_gets_format_error_then_recovers(self):
        replies = [chat_reply(0, None)] + [chat_reply(i + 1, c) for i, c in enumerate(COMMANDS)]
        client, result, _ = self._run("glm", replies)
        self.assertEqual(result["outcome"]["exit_status"], "Submitted")
        second = client.requests[1]["messages"]
        self.assertEqual(second[-1]["role"], "user")
        self.assertIn("Tool call error", second[-1]["content"])
        self.assertEqual(client.requests[0]["extra_body"], {"reasoning_effort": "low"})

    def test_repeated_format_errors_stop_without_figure(self):
        client, result, out = self._run("glm", [chat_reply(i, None) for i in range(3)])
        self.assertEqual(result["outcome"]["exit_status"], "RepeatedFormatError")
        self.assertFalse(result["artifact_present"])
        self.assertIsNone(Run.load(out, self.root).figure)

    def test_step_limit(self):
        replies = [responses_reply(i, "echo working") for i in range(sg.STEP_LIMIT)]
        _, result, _ = self._run("deepseek", replies)
        self.assertEqual(result["outcome"]["exit_status"], "LimitsExceeded")
        self.assertEqual(result["outcome"]["usage"]["model_calls"], sg.STEP_LIMIT)

    def test_api_keys_not_visible_to_commands(self):
        workspace = sg.LocalWorkspace()
        try:
            with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "sk-secret"}):
                out = workspace.execute("env", 10)["output"]
        finally:
            workspace.stop()
        self.assertNotIn("sk-secret", out)


if __name__ == "__main__":
    unittest.main()
