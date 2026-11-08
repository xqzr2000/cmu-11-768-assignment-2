"""Strictly opt-in gateway to the pinned Assignment 1 Docker Sandbox.

This module does not start containers on import or preview. It never calls a
model and has no tool-loop automation. Approval flags and command fingerprints
are guardrails for a future human-controlled host, NOT authentication.

Docker is not a hardened VM security boundary: only run in a trusted Codespace
after explicitly reviewing the command and accepting the sandbox risk.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable

# Deliberately fixed until a vetted chart-capable image is designed and tested.
# This floating base tag is only a transport test image, not a final pinned
# chart-generation environment. The module never pulls/builds it itself.
IMAGE = "python:3.12-slim"
WORKDIR = "/workspace"


class GatewayError(ValueError):
    """An unsafe parameter, unauthorized operation, or state error."""


@dataclass(frozen=True)
class SandboxLimits:
    """Limits no greater than the pinned runtime's own restrictions."""

    deployment_seconds: int = 120
    command_seconds: int = 15
    cpus: float = 1.0
    memory: str = "512m"
    max_commands: int = 6
    max_command_chars: int = 2000
    max_output_chars: int = 2048

    def __post_init__(self) -> None:
        if type(self.deployment_seconds) is not int or not 10 <= self.deployment_seconds <= 300:
            raise ValueError("Deployment lifetime must be 10-300 seconds.")
        if (type(self.command_seconds) is not int
            or not 1 <= self.command_seconds <= min(60, self.deployment_seconds)):
            raise ValueError("Command timeout exceeds the bounded sandbox lifetime.")
        if (type(self.cpus) not in (int, float) or not 0 < self.cpus <= 2.0):
            raise ValueError("CPU limit must be between 0 and 2 cores.")
        if self.memory not in ("256m", "512m", "1g"):
            raise ValueError("Select a bounded memory limit: 256m, 512m or 1g.")
        if type(self.max_commands) is not int or not 1 <= self.max_commands <= 12:
            raise ValueError("Command budget must be between 1 and 12.")
        if (type(self.max_command_chars) is not int
            or not 1 <= self.max_command_chars <= 4096):
            raise ValueError("Command length cap must be between 1 and 4096.")
        if (type(self.max_output_chars) is not int
            or not 1 <= self.max_output_chars <= 8192):
            raise ValueError("Output length cap must be between 1 and 8192.")


class SandboxGateway:
    """One explicit sandbox launch, then separately approved shell commands.

    The actual Sandbox is instantiated lazily only by launch(). A fake factory
    is accepted for offline tests. No file injection/artifact extraction is
    supported in this initial gateway.
    """

    def __init__(self, *, limits: SandboxLimits | None = None,
                 sandbox_factory: Callable[..., Any] | None = None) -> None:
        if limits is not None and not isinstance(limits, SandboxLimits):
            raise TypeError("Expected SandboxLimits.")
        self.limits = limits or SandboxLimits()
        self._factory = sandbox_factory
        self._sandbox: Any | None = None
        self._launch_attempted = False
        self._closed = False
        self._proposal: tuple[str, str] | None = None
        self.commands_attempted = 0

    @property
    def running(self) -> bool:
        """Locally tracked handle, not a fresh Docker health check."""
        return self._sandbox is not None and not self._closed

    def preview_launch(self) -> dict[str, Any]:
        """Report safe metadata without importing Docker or launching."""
        return {
            "mode": "offline",
            "image": IMAGE,
            "network": "none",
            "ports": [],
            "host_mounts": [],
            "passes_host_environment": False,
            "deployment_seconds": self.limits.deployment_seconds,
            "command_seconds": self.limits.command_seconds,
            "cpus": self.limits.cpus,
            "memory": self.limits.memory,
            "max_commands": self.limits.max_commands,
            "docker_launches": 0,
            "shell_commands_executed": 0,
            "approval_required": True,
        }

    def launch(self, *, confirm_launch: bool = False,
               approve_image: str | None = None) -> None:
        """One user-authorized launch; a failed attempt is never auto-retried."""
        if self._closed or self._launch_attempted:
            raise GatewayError("Sandbox launch already attempted or gateway closed.")
        if confirm_launch is not True or approve_image != IMAGE:
            raise PermissionError("Sandbox launch requires explicit approval of the exact image.")
        self._launch_attempted = True
        if self._factory is None:
            from agent_sandbox_runtime import Sandbox
            factory = Sandbox
        else:
            factory = self._factory
        # The pinned runtime itself sets no host mounts, drops capabilities,
        # and applies a Docker-enforced lifetime. Explicitly disable networking.
        self._sandbox = factory(
            IMAGE,
            cwd=WORKDIR,
            ports=(),
            network="none",
            deployment_timeout=self.limits.deployment_seconds,
            runtime_timeout=self.limits.command_seconds,
            cpus=self.limits.cpus,
            memory=self.limits.memory,
        )

    def _require_running(self) -> None:
        if not self.running:
            raise GatewayError("No active sandbox; launch permission is required.")

    def propose_command(self, command: str) -> dict[str, Any]:
        """Create one command proposal for external human review, never run it."""
        self._require_running()
        if self._proposal is not None:
            raise GatewayError("Resolve or reject the existing command proposal first.")
        if self.commands_attempted >= self.limits.max_commands:
            raise GatewayError("Sandbox command budget exhausted.")
        if (not isinstance(command, str) or not command.strip()
            or len(command) > self.limits.max_command_chars or "\x00" in command):
            raise GatewayError("Invalid or oversized shell command.")
        ordinal = self.commands_attempted + 1
        fingerprint = hashlib.sha256(
            f"session010-command:{ordinal}\n{command}".encode("utf-8")
        ).hexdigest()
        self._proposal = (command, fingerprint)
        return {
            "step": ordinal,
            "command": command,
            "approval_sha256": fingerprint,
            "requires_explicit_command_approval": True,
            "shell_commands_executed_by_preview": 0,
        }

    def reject_proposal(self) -> None:
        """Discard a proposal without consuming a command or executing it."""
        self._require_running()
        if self._proposal is None:
            raise GatewayError("No pending command proposal.")
        self._proposal = None

    def execute_approved(self, *, confirm_one_command: bool = False,
                         approve_sha256: str | None = None) -> dict[str, Any]:
        """Consume one reviewed proposal and run only inside the sandbox.

        IMPORTANT: the caller must obtain *independent human approval* for the
        exact command shown by propose_command(). Possessing its fingerprint
        does not prove that a human reviewed it. Never automate this method
        from raw model output without a separate approval interface.
        """
        self._require_running()
        if self._proposal is None:
            raise GatewayError("No proposed command to approve.")
        command, expected_hash = self._proposal
        if confirm_one_command is not True or approve_sha256 != expected_hash:
            raise PermissionError("Exact command hash and single-command consent required.")
        self._proposal = None
        # Count *attempts* before calling Docker, even if execution raises.
        # No silent retry of a failed or possibly side-effecting command.
        self.commands_attempted += 1
        result = self._sandbox.execute(
            command,
            timeout=self.limits.command_seconds,
            cwd=WORKDIR,
            env={},
            shell=True,
            check=False,
        )
        if not isinstance(result, dict):
            raise GatewayError("Unexpected sandbox output shape.")
        stdout, stderr = result.get("stdout"), result.get("stderr")
        rc = result.get("returncode")
        if not isinstance(stdout, str) or not isinstance(stderr, str) or type(rc) is not int:
            raise GatewayError("Malformed sandbox stdout/stderr/returncode.")
        cap = self.limits.max_output_chars
        # The gateway returns only bounded output. No environment values,
        # Docker object, command contents or host secrets are included.
        return {
            "returncode": rc,
            "stdout": stdout[:cap],
            "stderr": stderr[:cap],
            "stdout_truncated": len(stdout) > cap,
            "stderr_truncated": len(stderr) > cap,
        }

    def close(self) -> None:
        """Always permit cleanup; never require approval to stop a sandbox."""
        if self._closed:
            return
        self._closed = True
        self._proposal = None
        sandbox, self._sandbox = self._sandbox, None
        if sandbox is not None:
            sandbox.stop()

    def __enter__(self) -> "SandboxGateway":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
