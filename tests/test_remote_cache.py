"""Tests for remote cache (PR comment fetch/parse)."""

from __future__ import annotations

import base64
import json

from unravel.models import Walkthrough
from unravel.remote_cache import _extract_walkthrough, _split_comment_bodies
from unravel.renderer import (
    COMMENT_MARKER_DATA_PREFIX,
    COMMENT_MARKER_END,
    COMMENT_MARKER_START,
    render_github_comment,
)


def _make_comment_body(walkthrough: Walkthrough) -> str:
    """Use the real renderer to build a comment body."""
    return render_github_comment(walkthrough)


def test_extract_walkthrough_roundtrip(sample_walkthrough: Walkthrough) -> None:
    body = _make_comment_body(sample_walkthrough)
    result = _extract_walkthrough(body, raw_diff="fake diff")

    assert result is not None
    assert len(result.threads) == len(sample_walkthrough.threads)
    assert result.overview == sample_walkthrough.overview
    assert result.raw_diff == "fake diff"


def test_extract_walkthrough_no_marker() -> None:
    result = _extract_walkthrough("Just a normal comment.", raw_diff="")
    assert result is None


def test_extract_walkthrough_malformed_base64() -> None:
    body = (
        f"{COMMENT_MARKER_START}\n"
        f"{COMMENT_MARKER_DATA_PREFIX}not-valid-base64!!! -->\n"
        f"{COMMENT_MARKER_END}\n"
    )
    result = _extract_walkthrough(body, raw_diff="")
    assert result is None


def test_extract_walkthrough_invalid_json() -> None:
    encoded = base64.b64encode(b"not json").decode("ascii")
    body = (
        f"{COMMENT_MARKER_START}\n"
        f"{COMMENT_MARKER_DATA_PREFIX}{encoded} -->\n"
        f"{COMMENT_MARKER_END}\n"
    )
    result = _extract_walkthrough(body, raw_diff="")
    assert result is None


def test_extract_walkthrough_missing_fields() -> None:
    encoded = base64.b64encode(json.dumps({"foo": "bar"}).encode()).decode("ascii")
    body = (
        f"{COMMENT_MARKER_START}\n"
        f"{COMMENT_MARKER_DATA_PREFIX}{encoded} -->\n"
        f"{COMMENT_MARKER_END}\n"
    )
    result = _extract_walkthrough(body, raw_diff="")
    assert result is None


def test_split_comment_bodies_single(sample_walkthrough: Walkthrough) -> None:
    body = _make_comment_body(sample_walkthrough)
    bodies = _split_comment_bodies(body)
    assert len(bodies) == 1
    assert COMMENT_MARKER_START in bodies[0]


def test_split_comment_bodies_mixed() -> None:
    """Other comments before/after the unravel comment are ignored."""
    raw = (
        "Some other comment body\n"
        "another line\n"
        f"{COMMENT_MARKER_START}\n"
        "the real content\n"
        f"{COMMENT_MARKER_END}\n"
        "Yet another comment\n"
    )
    bodies = _split_comment_bodies(raw)
    assert len(bodies) == 1
    assert "the real content" in bodies[0]


def test_split_comment_bodies_empty() -> None:
    bodies = _split_comment_bodies("")
    assert bodies == []


def test_split_comment_bodies_no_marker() -> None:
    bodies = _split_comment_bodies("just a regular comment\nnothing special\n")
    assert bodies == []
