"""Registry and zero-network provider-preflight invariants."""

from __future__ import annotations

import io
import json
import unittest
from dataclasses import replace
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError

from integrations.models import MODELS, get_model
from integrations.providers import prepare_request, preview_request
from scripts import provider_preflight


class ProviderRegistryOfflineTests(unittest.TestCase):
    def test_exact_four_roles_providers_and_requested_models(self):
        self.assertEqual(set(MODELS), {
            "agent_a", "agent_b", "agent_c", "experimental_judge"
        })
        self.assertEqual(
            {key: (spec.provider, spec.model_id) for key, spec in MODELS.items()},
            {
                "agent_a": ("deepseek", "deepseek-flash"),
                "agent_b": ("openai", "gpt-5.6-luna"),
                "agent_c": ("zai", "glm-4.7-flash"),
                "experimental_judge": ("openai", "gpt-6.1-terra"),
            },
        )

    def test_registry_is_read_only_and_unknown_role_is_rejected(self):
        with self.assertRaises(TypeError):
            MODELS["agent_d"] = MODELS["agent_a"]
        with self.assertRaises(FrozenInstanceError):
            get_model("agent_a").model_id = "other"
        with self.assertRaises(ValueError):
            get_model("unknown-role")

    def test_cannot_dispatch_to_silent_model_or_endpoint_substitution(self):
        original = get_model("agent_b")
        items = [{"role": "user", "content": "Make a graph."}]
        for replaced in (
            replace(original, model_id="gpt-unapproved"),
            replace(original, base_url="https://untrusted.invalid"),
        ):
            with self.subTest(replaced=replaced), self.assertRaisesRegex(
                ValueError, "Unregistered"
            ):
                prepare_request(replaced, items)

    def test_key_and_base_url_are_provider_specific(self):
        self.assertEqual(get_model("agent_a").key_env, "DEEPSEEK_API_KEY")
        self.assertEqual(get_model("agent_c").key_env, "ZAI_API_KEY")
        self.assertEqual(get_model("agent_b").key_env, "OPENAI_API_KEY")
        self.assertEqual(get_model("experimental_judge").key_env, "OPENAI_API_KEY")
        self.assertEqual(get_model("agent_a").base_url, "https://api.deepseek.com")
        self.assertEqual(get_model("agent_c").api_style, "chat_completions")
        self.assertEqual(get_model("experimental_judge").api_style, "responses")

    def test_default_offline_preflight_never_builds_an_api_client(self):
        output = io.StringIO()
        with redirect_stdout(output):
            provider_preflight.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(len(result["models"]), 4)
        self.assertTrue(all(m["network_requests"] == 0 for m in result["models"]))
        self.assertEqual(
            sum(m["structured_judgment"] for m in result["models"]), 1
        )
        self.assertFalse(any("api_key" in json.dumps(m) for m in result["models"]))

    def test_output_token_limit_is_bounded_offline(self):
        spec = get_model("agent_a")
        messages = [{"role": "user", "content": "Create a chart."}]
        self.assertEqual(prepare_request(spec, messages)["max_output_tokens"], 512)
        for limit in (0, -1, 513, 1.5, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                prepare_request(spec, messages, max_output_tokens=limit)

    def test_preview_reports_only_metadata(self):
        case = [{"role": "user", "content": "PRIVATE EXAMPLE: no secrets"}]
        result = preview_request(get_model("agent_a"), case)
        self.assertEqual(result["network_requests"], 0)
        self.assertNotIn("PRIVATE EXAMPLE", json.dumps(result))
        self.assertFalse(result["official_qwen_equivalent"])


if __name__ == "__main__":
    unittest.main()
