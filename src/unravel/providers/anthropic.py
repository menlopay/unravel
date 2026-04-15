"""Anthropic (Claude) provider implementation."""

from __future__ import annotations

import json
import time
from collections.abc import Callable

import anthropic

from unravel.config import UnravelConfig
from unravel.models import Hunk, Walkthrough
from unravel.prompts import build_analysis_prompt
from unravel.providers.base import BaseProvider

MAX_RETRIES = 2


class AnthropicProvider(BaseProvider):
    def __init__(self, config: UnravelConfig) -> None:
        super().__init__(config)
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.config.resolved_api_key)
        return self._client

    def validate_config(self) -> None:
        _ = self.config.resolved_api_key
        if not self.config.resolved_model:
            raise ValueError("No model configured for Anthropic provider.")

    def analyze(
        self,
        hunks: list[Hunk],
        raw_diff: str,
        metadata: dict,
        *,
        on_status: Callable[[str], None] | None = None,
    ) -> Walkthrough:
        system_prompt, user_prompt = build_analysis_prompt(raw_diff, hunks, metadata)

        def status(msg: str) -> None:
            if on_status:
                on_status(msg)

        status("Sending diff to Claude for analysis...")
        start = time.monotonic()

        response_text = self._call_with_retry(system_prompt, user_prompt, status)

        elapsed = time.monotonic() - start
        status(f"Analysis complete in {elapsed:.1f}s")

        walkthrough = Walkthrough.from_json(response_text, raw_diff=raw_diff)
        walkthrough.metadata["model"] = self.config.resolved_model
        walkthrough.metadata["provider"] = "anthropic"
        walkthrough.metadata["elapsed_seconds"] = round(elapsed, 2)

        return walkthrough

    def _call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        status: Callable[[str], None],
    ) -> str:
        messages: list[dict] = [{"role": "user", "content": user_prompt}]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                text = self._send_request(system_prompt, messages)
                json.loads(text)
                return text
            except json.JSONDecodeError as exc:
                if attempt >= MAX_RETRIES:
                    raise ValueError(
                        f"Failed to parse JSON from Claude after {MAX_RETRIES} attempts. "
                        f"Last error: {exc}"
                    ) from exc
                status(f"JSON parse failed (attempt {attempt}), retrying...")
                messages.append({"role": "assistant", "content": text})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your response was not valid JSON. Parse error: {exc}\n\n"
                        "Please respond with ONLY the valid JSON object, no other text."
                    ),
                })

        raise RuntimeError("Unreachable")  # pragma: no cover

    def _send_request(self, system_prompt: str, messages: list[dict]) -> str:
        model = self.config.resolved_model
        thinking_budget = self.config.thinking_budget
        max_output = self.config.max_output_tokens

        kwargs: dict = {
            "model": model,
            "max_tokens": max_output,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": messages,
        }

        if thinking_budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }

        response = self.client.messages.create(**kwargs)

        for block in response.content:
            if block.type == "text":
                return block.text

        raise ValueError("No text block found in Claude response.")
