"""Provider factory."""

from __future__ import annotations

from unravel.config import UnravelConfig
from unravel.providers.base import BaseProvider


def get_provider(config: UnravelConfig) -> BaseProvider:
    match config.provider:
        case "anthropic":
            from unravel.providers.anthropic import AnthropicProvider

            return AnthropicProvider(config)
        case _:
            supported = ["anthropic"]
            raise ValueError(
                f"Unsupported provider: '{config.provider}'. "
                f"Supported providers: {', '.join(supported)}"
            )
