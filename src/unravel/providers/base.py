"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from unravel.config import UnravelConfig
from unravel.models import Hunk, Walkthrough


class BaseProvider(ABC):
    def __init__(self, config: UnravelConfig) -> None:
        self.config = config

    @abstractmethod
    def analyze(
        self,
        hunks: list[Hunk],
        raw_diff: str,
        metadata: dict,
        *,
        on_status: Callable[[str], None] | None = None,
    ) -> Walkthrough:
        """Analyze a diff and return a structured walkthrough."""

    @abstractmethod
    def validate_config(self) -> None:
        """Validate that this provider is properly configured. Raises ValueError if not."""
