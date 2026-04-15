"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from unravel.models import Walkthrough

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_diff() -> str:
    return (FIXTURES_DIR / "simple.diff").read_text()


@pytest.fixture
def sample_response_text() -> str:
    return (FIXTURES_DIR / "sample_response.json").read_text()


@pytest.fixture
def sample_response_dict(sample_response_text: str) -> dict:
    return json.loads(sample_response_text)


@pytest.fixture
def sample_walkthrough(sample_response_text: str, simple_diff: str) -> Walkthrough:
    return Walkthrough.from_json(sample_response_text, raw_diff=simple_diff)
