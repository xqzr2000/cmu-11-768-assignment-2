"""Session 012 synthetic zero/one CSV preflight tests; no Docker or API requests."""
from __future__ import annotations

import json
import socket
import subprocess
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from integrations.chart_image_recipe import plan_chart_image
from integrations.chart_wheel_lock import ChartLockError
from scripts import preview_chart_smoke_offline as preview


class ChartSmokePreviewOfflineTests(unittest.TestCase):
    def test_two_cases_have_strict_allowlists_and_zero_docker_work(self):
        output = preview.build_offline_preview()
        self.assertEqual(output["mode"], "offline_preview_only")
        self.assertEqual(output["audited_wheel_metadata_count"], 14)
        self.assertEqual(output["target_platform"], "linux/amd64")
        self.assertEqual([case["case"] for case in output["cases"]],
                         ["zero_csv", "one_csv"])
        for case in output["cases"]:
            expected = preview.CASE_FILES[case["case"]]
            self.assertEqual({item["path"] for item in case["context"]["files"]},
                             expected)
            self.assertEqual(case["context"]["file_count"], len(expected))
            self.assertTrue(case["inputs_directory_exists"])
            self.assertTrue(case["private_directory_permissions_verified"])
            self.assertFalse(case["context"]["docker_build_authorized"])
            self.assertEqual(case["context"]["docker_builds"], 0)
            self.assertEqual(case["context"]["model_requests"], 0)
        self.assertEqual(output["cases"][0]["context"]["file_count"], 4)
        self.assertEqual(output["cases"][1]["context"]["file_count"], 5)
        self.assertIn("trusted/smoke_chart.py", preview.CASE_FILES["zero_csv"])
        self.assertIn("trusted/smoke_chart.py", preview.CASE_FILES["one_csv"])
        self.assertEqual(output["cases"][0]["declared_csv_count"], 0)
        self.assertEqual(output["cases"][1]["declared_csv_count"], 1)

    def test_dockerfile_digests_match_both_contexts(self):
        output = preview.build_offline_preview()
        recipe = plan_chart_image(preview.CANDIDATE_BASE_IMAGE)
        self.assertEqual(output["dockerfile"], recipe.dockerfile)
        self.assertEqual(output["dockerfile_sha256"], recipe.dockerfile_sha256)
        self.assertEqual(
            [case["context"]["dockerfile_sha256"] for case in output["cases"]],
            [recipe.dockerfile_sha256] * 2,
        )
        self.assertIn("--require-hashes --only-binary=:all:", recipe.dockerfile)
        self.assertIn("COPY inputs/ /opt/assignment/inputs/", recipe.dockerfile)
        self.assertIn("COPY trusted/smoke_chart.py /opt/assignment/smoke_chart.py",
                      recipe.dockerfile)

    def test_preview_exposes_neither_csv_bytes_nor_private_host_paths(self):
        raw = json.dumps(preview.build_offline_preview(), sort_keys=True)
        self.assertNotIn("category,value", raw)
        self.assertNotIn("A,1", raw)
        self.assertNotIn("B,2", raw)
        self.assertNotIn("/tmp/", raw)
        self.assertNotIn("session010-buildctx-", raw)
        self.assertNotIn("session010-csv-", raw)

    def test_explicit_lack_of_build_and_wheel_integrity_claims(self):
        output = preview.build_offline_preview()
        self.assertTrue(output["candidate_base_previously_observed_not_reverified"])
        self.assertFalse(output["wheel_byte_integrity_verified"])
        self.assertFalse(output["pip_install_verified"])
        self.assertFalse(output["docker_build_authorized"])
        self.assertTrue(output["requires_fresh_explicit_approval_for_real_build"])
        for counter in ("docker_builds", "docker_launches", "network_requests",
                        "model_requests"):
            self.assertEqual(output[counter], 0)

    def test_context_directories_are_removed_on_success(self):
        roots: list[Path] = []
        original = preview.prepare_chart_build_context

        @contextmanager
        def observing_context(*args, **kwargs):
            with original(*args, **kwargs) as context:
                roots.append(context.root)
                yield context

        with patch.object(preview, "prepare_chart_build_context", observing_context):
            self.assertTrue(preview.build_offline_preview()["private_contexts_destroyed"])
        self.assertEqual(len(roots), 2)
        self.assertTrue(all(not root.exists() for root in roots))

    def test_no_subprocess_or_network_even_when_system_calls_are_poisoned(self):
        with patch.object(subprocess, "Popen", side_effect=AssertionError("Popen forbidden")), \
             patch.object(subprocess, "run", side_effect=AssertionError("run forbidden")), \
             patch.object(socket, "create_connection",
                          side_effect=AssertionError("network forbidden")):
            output = preview.build_offline_preview()
        self.assertEqual(output["docker_builds"], 0)
        self.assertEqual(output["network_requests"], 0)

    def test_bad_wheel_audit_prevents_even_a_preview(self):
        with patch.object(preview, "audit_chart_wheel_lock",
                          side_effect=ChartLockError("unreviewed lock")):
            with self.assertRaises(ChartLockError):
                preview.build_offline_preview()


if __name__ == "__main__":
    unittest.main()
