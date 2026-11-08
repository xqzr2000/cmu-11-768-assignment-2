"""Pinned *requested* model IDs for our independent Assignment 2 adaptation.

IDs and endpoint URLs are kept distinct from human-friendly display names.
Provider-reported IDs/versions must be recorded separately after live calls.
No client, environment variable, or network request is read at import time.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

Provider = Literal["deepseek", "openai", "zai"]
APIStyle = Literal["responses", "chat_completions"]
Role = Literal["agent_a", "agent_b", "agent_c", "experimental_judge"]


@dataclass(frozen=True)
class ModelSpec:
    role: Role
    provider: Provider
    model_id: str
    display_name: str
    api_style: APIStyle
    key_env: str
    base_url: str

    @property
    def is_judge(self) -> bool:
        return self.role == "experimental_judge"


_MODELS: dict[str, ModelSpec] = {
    "agent_a": ModelSpec(
        "agent_a", "deepseek", "deepseek-flash", "DeepSeek Flash (moving alias)",
        "responses", "DEEPSEEK_API_KEY", "https://api.deepseek.com",
    ),
    "agent_b": ModelSpec(
        "agent_b", "openai", "gpt-5.6-luna", "GPT-5.6 Luna",
        "responses", "OPENAI_API_KEY", "https://api.openai.com/v1",
    ),
    "agent_c": ModelSpec(
        "agent_c", "zai", "glm-5.3-flash", "GLM-5.3 Flash",
        "chat_completions", "ZAI_API_KEY", "https://api.z.ai/api/paas/v4",
    ),
    "experimental_judge": ModelSpec(
        "experimental_judge", "openai", "gpt-6.1-terra", "GPT-6.1 Terra",
        "responses", "OPENAI_API_KEY", "https://api.openai.com/v1",
    ),
}

MODELS = MappingProxyType(_MODELS)


def get_model(role: Role) -> ModelSpec:
    """Return a configured role; unknown roles must never silently fall back."""
    try:
        return MODELS[role]
    except KeyError as exc:
        raise ValueError(f"Unknown experimental model role: {role!r}") from exc
