"""Sandbox gateway offline contract tests: fake Docker only, no model API."""

from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from integrations.sandbox_gateway import (
    IMAGE,
    SandboxGateway,
    SandboxLimits,
    GatewayError,
)


class FakeSandbox:
    """Record constructor and execute arguments; never import or run Docker."""

    def __init__(self, image: str, **kwargs: object) -> None:
        self.image = image
        self.kwargs = kwargs
        self.executions: list[tuple[str, dict]] = []
        self.stops = 0
        self.next_result = {"returncode": 0, "stdout": "hello", "stderr": ""}
        self.error: Exception | None = None

    def execute(self, command: str, **kwargs: object) -> dict:
        self.executions.append((command, dict(kwargs)))
        if self.error is not None:
            raise self.error
        return self.next_result

    def stop(self) -> None:
        self.stops += 1


def fake_factory():
    sandboxes: list[FakeSandbox] = []

    def create(image: str, **kwargs: object) -> FakeSandbox:
        fake = FakeSandbox(image, **kwargs)
        sandboxes.append(fake)
        return fake

    return create, sandboxes


def launch_fake(*, limits: SandboxLimits | None = None):
    factory, sandboxes = fake_factory()
    gateway = SandboxGateway(limits=limits, sandbox_factory=factory)
    gateway.launch(confirm_launch=True, approve_image=IMAGE)
    return gateway, sandboxes[0]


class SandboxGatewayOfflineTests(unittest.TestCase):
    def test_preview_does_not_construct_docker_or_read_keys(self):
        factory = Mock()
        gateway = SandboxGateway(sandbox_factory=factory)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "dummy-private-value"}):
            preview = gateway.preview_launch()
        self.assertEqual(preview["mode"], "offline")
        self.assertEqual(preview["network"], "none")
        self.assertEqual(preview["ports"], [])
        self.assertEqual(preview["host_mounts"], [])
        self.assertFalse(preview["passes_host_environment"])
        self.assertEqual(preview["docker_launches"], 0)
        factory.assert_not_called()
        self.assertFalse(gateway.running)

    def test_launch_requires_exact_image_and_explicit_consent(self):
        factory, sandboxes = fake_factory()
        gateway = SandboxGateway(sandbox_factory=factory)
        for args in ({}, {"confirm_launch": True},
                     {"approve_image": IMAGE},
                     {"confirm_launch": True, "approve_image": "other-image"}):
            with self.subTest(args=args), self.assertRaises(PermissionError):
                gateway.launch(**args)
        self.assertEqual(sandboxes, [])
        gateway.launch(confirm_launch=True, approve_image=IMAGE)
        self.assertEqual(len(sandboxes), 1)
        with self.assertRaises(GatewayError):
            gateway.launch(confirm_launch=True, approve_image=IMAGE)
        gateway.close()

    def test_launch_uses_network_none_and_strict_resource_args(self):
        gateway, sandbox = launch_fake()
        self.assertEqual(sandbox.image, IMAGE)
        self.assertEqual(sandbox.kwargs, {
            "cwd": "/workspace",
            "ports": (),
            "network": "none",
            "deployment_timeout": 120,
            "runtime_timeout": 15,
            "cpus": 1.0,
            "memory": "512m",
        })
        gateway.close()
        self.assertEqual(sandbox.stops, 1)

    def test_proposed_command_requires_separate_matching_approval(self):
        gateway, sandbox = launch_fake()
        proposal = gateway.propose_command("pwd")
        self.assertEqual(proposal["command"], "pwd")
        self.assertEqual(proposal["step"], 1)
        self.assertEqual(len(proposal["approval_sha256"]), 64)
        self.assertFalse(sandbox.executions)
        for kwargs in ({}, {"confirm_one_command": True},
                       {"approve_sha256": proposal["approval_sha256"]},
                       {"confirm_one_command": True, "approve_sha256": "wrong"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(PermissionError):
                gateway.execute_approved(**kwargs)
        self.assertFalse(sandbox.executions)
        output = gateway.execute_approved(
            confirm_one_command=True, approve_sha256=proposal["approval_sha256"]
        )
        self.assertEqual(output["stdout"], "hello")
        self.assertEqual(output["returncode"], 0)
        self.assertEqual(gateway.commands_attempted, 1)
        self.assertEqual(sandbox.executions, [("pwd", {
            "timeout": 15, "cwd": "/workspace", "env": {}, "shell": True,
            "check": False,
        })])
        with self.assertRaises(GatewayError):
            gateway.execute_approved(
                confirm_one_command=True, approve_sha256=proposal["approval_sha256"]
            )
        gateway.close()

    def test_no_execution_before_launch_or_after_close(self):
        factory, sandboxes = fake_factory()
        gateway = SandboxGateway(sandbox_factory=factory)
        with self.assertRaises(GatewayError):
            gateway.propose_command("pwd")
        gateway.close()
        with self.assertRaises(GatewayError):
            gateway.launch(confirm_launch=True, approve_image=IMAGE)
        self.assertFalse(sandboxes)

    def test_proposal_rejection_does_not_execute_or_consume_budget(self):
        gateway, sandbox = launch_fake()
        proposal = gateway.propose_command("printf first")
        with self.assertRaises(GatewayError):
            gateway.propose_command("printf second")
        gateway.reject_proposal()
        self.assertEqual(gateway.commands_attempted, 0)
        second = gateway.propose_command("printf second")
        self.assertNotEqual(proposal["approval_sha256"], second["approval_sha256"])
        self.assertEqual(second["step"], 1)
        self.assertFalse(sandbox.executions)
        gateway.close()

    def test_rejects_malformed_oversized_and_nul_commands(self):
        gateway, sandbox = launch_fake(limits=SandboxLimits(max_command_chars=8))
        for command in ("", "    ", "012345678", "echo\x00hi", None, 123):
            with self.subTest(command=command), self.assertRaises(GatewayError):
                gateway.propose_command(command)
        self.assertFalse(sandbox.executions)
        gateway.close()

    def test_command_budget_and_unique_step_fingerprint(self):
        gateway, sandbox = launch_fake(limits=SandboxLimits(max_commands=2))
        first = gateway.propose_command("pwd")
        gateway.execute_approved(confirm_one_command=True,
                                 approve_sha256=first["approval_sha256"])
        second = gateway.propose_command("pwd")
        self.assertEqual(second["step"], 2)
        self.assertNotEqual(first["approval_sha256"], second["approval_sha256"])
        gateway.execute_approved(confirm_one_command=True,
                                 approve_sha256=second["approval_sha256"])
        with self.assertRaises(GatewayError):
            gateway.propose_command("pwd")
        self.assertEqual(len(sandbox.executions), 2)
        gateway.close()

    def test_output_is_bounded_and_external_environment_not_passed(self):
        gateway, sandbox = launch_fake(limits=SandboxLimits(max_output_chars=4))
        sandbox.next_result = {
            "returncode": 124, "stdout": "abcdefgh", "stderr": "warning!",
            "output": "unbounded combined output",
        }
        proposal = gateway.propose_command("printf something")
        with patch.dict(os.environ, {"ZAI_API_KEY": "sensitive-host-value"}):
            result = gateway.execute_approved(
                confirm_one_command=True, approve_sha256=proposal["approval_sha256"]
            )
        self.assertEqual(result, {
            "returncode": 124, "stdout": "abcd", "stderr": "warn",
            "stdout_truncated": True, "stderr_truncated": True,
        })
        self.assertNotIn("sensitive-host-value", repr(result))
        self.assertEqual(sandbox.executions[0][1]["env"], {})
        gateway.close()

    def test_failed_command_attempt_consumes_budget_and_never_retries(self):
        gateway, sandbox = launch_fake(limits=SandboxLimits(max_commands=1))
        sandbox.error = RuntimeError("fake Docker failure")
        proposal = gateway.propose_command("pwd")
        with self.assertRaisesRegex(RuntimeError, "fake Docker failure"):
            gateway.execute_approved(
                confirm_one_command=True, approve_sha256=proposal["approval_sha256"]
            )
        self.assertEqual(gateway.commands_attempted, 1)
        self.assertEqual(len(sandbox.executions), 1)
        with self.assertRaises(GatewayError):
            gateway.propose_command("pwd")
        gateway.close()

    def test_invalid_result_cannot_be_replayed_as_success(self):
        gateway, sandbox = launch_fake()
        sandbox.next_result = {"returncode": True, "stdout": "", "stderr": ""}
        proposal = gateway.propose_command("pwd")
        with self.assertRaises(GatewayError):
            gateway.execute_approved(
                confirm_one_command=True, approve_sha256=proposal["approval_sha256"]
            )
        self.assertEqual(gateway.commands_attempted, 1)
        gateway.close()

    def test_launch_failure_is_not_retried(self):
        factory = Mock(side_effect=RuntimeError("fake launch failed"))
        gateway = SandboxGateway(sandbox_factory=factory)
        with self.assertRaisesRegex(RuntimeError, "fake launch failed"):
            gateway.launch(confirm_launch=True, approve_image=IMAGE)
        with self.assertRaises(GatewayError):
            gateway.launch(confirm_launch=True, approve_image=IMAGE)
        self.assertEqual(factory.call_count, 1)
        gateway.close()

    def test_context_manager_cleans_up_even_after_exception(self):
        factory, sandboxes = fake_factory()
        with self.assertRaisesRegex(RuntimeError, "user abort"):
            with SandboxGateway(sandbox_factory=factory) as gateway:
                gateway.launch(confirm_launch=True, approve_image=IMAGE)
                gateway.propose_command("pwd")
                raise RuntimeError("user abort")
        self.assertEqual(sandboxes[0].stops, 1)
        self.assertFalse(sandboxes[0].executions)
        gateway.close()
        self.assertEqual(sandboxes[0].stops, 1)

    def test_bad_resource_limits_fail_before_any_sandbox(self):
        for kwargs in (
            {"deployment_seconds": 9}, {"deployment_seconds": 301},
            {"command_seconds": 0}, {"command_seconds": 121},
            {"cpus": True}, {"cpus": 3.0}, {"memory": "16g"},
            {"max_commands": 0}, {"max_commands": 13},
            {"max_command_chars": 5000}, {"max_output_chars": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SandboxLimits(**kwargs)


if __name__ == "__main__":
    unittest.main()
