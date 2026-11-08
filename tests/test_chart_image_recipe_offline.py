"""Mock-free, zero-network tests for the digest-guarded chart image recipe."""

from __future__ import annotations

import hashlib
import subprocess
import unittest
from unittest.mock import patch

from integrations.chart_image_recipe import (
    ImageRecipeError,
    PLOT_PACKAGES,
    REQUIREMENTS_CONTEXT_PATH,
    REQUIREMENTS_DESTINATION,
    plan_chart_image,
)

# Deliberately fictitious hash. Test input only; not an available/trusted image.
FAKE_BASE = "python:3.12-slim@sha256:" + "a" * 64


class ChartImageRecipeOfflineTests(unittest.TestCase):
    def test_requires_exact_digest_pinned_python_base(self):
        invalid = (
            "python:3.12-slim",
            "python:latest",
            "python:3.12@sha256:" + "a" * 64,
            "python:3.12-slim@sha256:" + "a" * 63,
            "python:3.12-slim@sha256:" + "g" * 64,
            "python:3.12-slim@sha256:" + "A" * 64,
            "evil.registry/python:3.12-slim@sha256:" + "a" * 64,
            "python:3.12-slim@sha256:" + "a" * 64 + "\nRUN echo hello",
            "",
            None,
            123,
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ImageRecipeError):
                plan_chart_image(value)

    def test_accepts_syntactically_pinned_base_and_preserves_full_digest(self):
        planned = plan_chart_image(FAKE_BASE)
        self.assertEqual(planned.base_image, FAKE_BASE)
        self.assertTrue(planned.dockerfile.startswith(f"FROM {FAKE_BASE}\n"))
        self.assertEqual(planned.dockerfile.count("FROM "), 1)

    def test_fixed_package_versions_match_project_pins(self):
        self.assertEqual(PLOT_PACKAGES, (
            "matplotlib==3.10.5",
            "numpy==2.3.2",
            "pandas==2.3.1",
            "pillow==12.3.0",
        ))
        result = plan_chart_image(FAKE_BASE).dockerfile
        self.assertIn(
            "RUN python -m pip install --no-cache-dir --require-hashes "
            "--only-binary=:all: -r /opt/assignment/chart-requirements.txt", result
        )
        self.assertIn(f"COPY {REQUIREMENTS_CONTEXT_PATH} {REQUIREMENTS_DESTINATION}", result)
        for package in PLOT_PACKAGES:
            self.assertNotIn(f" {package}", result)
        self.assertNotIn("pip install -U", result)

    def test_lockfile_copy_precedes_pip_install_and_no_bare_pins(self):
        dockerfile = plan_chart_image(FAKE_BASE).dockerfile
        self.assertLess(dockerfile.index("COPY requirements/"), dockerfile.index("RUN python -m pip"))
        self.assertEqual(dockerfile.count("RUN python -m pip"), 1)
        self.assertEqual(dockerfile.count("--require-hashes"), 1)
        self.assertNotIn(" --extra-index-url", dockerfile)

    def test_runtime_is_nonroot_and_has_private_writable_workspace(self):
        content = plan_chart_image(FAKE_BASE).dockerfile
        self.assertIn("chown 10001:10001 /workspace", content)
        self.assertIn("chmod 0700 /workspace", content)
        self.assertIn("USER 10001:10001\n", content)
        self.assertIn("WORKDIR /workspace\n", content)
        self.assertLess(content.index("chown 10001:10001"), content.index("USER 10001:10001"))
        self.assertIn("ENV MPLBACKEND=Agg", content)

    def test_only_explicit_context_paths_are_copied(self):
        content = plan_chart_image(FAKE_BASE).dockerfile
        copy_lines = [line for line in content.splitlines() if line.startswith("COPY ")]
        self.assertEqual(copy_lines, [
            "COPY requirements/chart-cp312-linux-amd64.txt /opt/assignment/chart-requirements.txt",
            "COPY inputs/ /opt/assignment/inputs/",
            "COPY trusted/extract_figure.py /opt/assignment/extract_figure.py",
        ])
        self.assertNotIn("COPY .", content)
        self.assertNotIn("ADD ", content)
        self.assertIn("chmod 0444 /opt/assignment/extract_figure.py", content)
        self.assertIn("find /opt/assignment/inputs -maxdepth 1 -type f -name '*.csv'", content)
        self.assertIn("-exec chmod 0444 {} +", content)
        self.assertNotIn("chmod 0444 /opt/assignment/inputs/*.csv", content)

    def test_zero_csv_input_directory_has_no_failing_chmod_glob(self):
        content = plan_chart_image(FAKE_BASE).dockerfile
        self.assertIn("COPY inputs/ /opt/assignment/inputs/", content)
        self.assertIn("RUN mkdir -p /opt/assignment/inputs", content)
        self.assertNotIn("chmod 0444 /opt/assignment/inputs/*.csv", content)
        self.assertIn("-exec chmod 0444 {} +", content)
        self.assertEqual(content.count("COPY inputs/ "), 1)

    def test_no_host_network_ports_secrets_or_docker_socket_in_recipe(self):
        content = plan_chart_image(FAKE_BASE).dockerfile
        self.assertNotIn("EXPOSE ", content)
        self.assertNotIn("VOLUME ", content)
        self.assertNotIn("/var/run/docker.sock", content)
        self.assertNotIn("OPENAI_API_KEY", content)
        self.assertNotIn("ZAI_API_KEY", content)
        self.assertNotIn("DEEPSEEK_API_KEY", content)
        self.assertNotIn("curl ", content)

    def test_preview_reports_build_not_authorized_and_supply_chain_gaps(self):
        manifest = plan_chart_image(FAKE_BASE).preview()
        self.assertEqual(manifest["mode"], "offline")
        self.assertFalse(manifest["docker_build_authorized"])
        self.assertFalse(manifest["image_exists_verified"])
        self.assertFalse(manifest["image_trusted_verified"])
        self.assertFalse(manifest["image_platform_and_architecture_verified"])
        self.assertFalse(manifest["full_dependency_hash_lock_verified"])
        self.assertTrue(manifest["hash_locked_install_requested"])
        self.assertEqual(manifest["required_context_requirements_path"], REQUIREMENTS_CONTEXT_PATH)
        self.assertEqual(manifest["docker_builds"], 0)
        self.assertEqual(manifest["sandbox_launches"], 0)
        self.assertEqual(manifest["model_requests"], 0)

    def test_preview_reports_exact_expected_minimal_build_context(self):
        manifest = plan_chart_image(FAKE_BASE).preview()
        self.assertEqual(manifest["required_context_inputs_directory"], "inputs/")
        self.assertEqual(manifest["required_context_helper_path"], "trusted/extract_figure.py")
        self.assertFalse(manifest["staging_context_prepared"])
        self.assertEqual(manifest["runtime_user"], "10001:10001")
        self.assertEqual(manifest["task_csv_directory"], "/opt/assignment/inputs")

    def test_dockerfile_checksum_matches_content_exactly(self):
        result = plan_chart_image(FAKE_BASE)
        self.assertEqual(result.dockerfile_sha256,
                         hashlib.sha256(result.dockerfile.encode("utf-8")).hexdigest())

    def test_planning_is_deterministic(self):
        first, second = plan_chart_image(FAKE_BASE), plan_chart_image(FAKE_BASE)
        self.assertEqual(first, second)
        other = plan_chart_image("python:3.12-slim@sha256:" + "b" * 64)
        self.assertNotEqual(first.dockerfile_sha256, other.dockerfile_sha256)

    def test_planning_does_not_execute_or_build_anything(self):
        with patch.object(subprocess, "run", side_effect=AssertionError("subprocess forbidden")) as run:
            plan = plan_chart_image(FAKE_BASE)
            self.assertTrue(plan.dockerfile.startswith("FROM "))
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
