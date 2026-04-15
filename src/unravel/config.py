"""Configuration loading for Unravel."""

from __future__ import annotations

import os
from dataclasses import dataclass

PROVIDER_ENV_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
}


@dataclass
class UnravelConfig:
    provider: str = "anthropic"
    api_key: str | None = None
    model: str | None = None
    thinking_budget: int = 10_000
    max_output_tokens: int = 16_000

    @property
    def resolved_model(self) -> str:
        if self.model:
            return self.model
        return PROVIDER_DEFAULT_MODELS.get(self.provider, "")

    @property
    def resolved_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        env_var = PROVIDER_ENV_KEYS.get(self.provider)
        if env_var:
            key = os.environ.get(env_var, "")
            if key:
                return key
        raise ValueError(
            f"No API key found for provider '{self.provider}'. "
            f"Set {PROVIDER_ENV_KEYS.get(self.provider, 'the appropriate env var')} "
            f"or pass --api-key."
        )


def load_config(**cli_overrides: str | int | None) -> UnravelConfig:
    provider = cli_overrides.get("provider") or os.environ.get("UNRAVEL_PROVIDER", "anthropic")
    model = cli_overrides.get("model") or os.environ.get("UNRAVEL_MODEL")
    api_key = cli_overrides.get("api_key") or None
    thinking_budget = cli_overrides.get("thinking_budget") or os.environ.get(
        "UNRAVEL_THINKING_BUDGET", 10_000
    )
    max_output_tokens = cli_overrides.get("max_output_tokens") or os.environ.get(
        "UNRAVEL_MAX_OUTPUT_TOKENS", 16_000
    )

    return UnravelConfig(
        provider=str(provider),
        api_key=str(api_key) if api_key else None,
        model=str(model) if model else None,
        thinking_budget=int(thinking_budget),
        max_output_tokens=int(max_output_tokens),
    )
