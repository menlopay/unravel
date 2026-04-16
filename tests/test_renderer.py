"""Tests for markdown and GitHub comment rendering."""

from __future__ import annotations

import base64
import json

from unravel.models import Walkthrough
from unravel.renderer import (
    COMMENT_MARKER_DATA_PREFIX,
    COMMENT_MARKER_END,
    COMMENT_MARKER_START,
    render_github_comment,
    render_markdown,
)


def test_render_markdown_structure(sample_walkthrough: Walkthrough) -> None:
    md = render_markdown(sample_walkthrough)

    assert "2 threads across" in md
    assert "### Replace silent auth failures" in md
    assert "### Update middleware" in md
    assert "`auth-error-handling`" in md
    assert "**Root cause:**" in md
    assert "**Step 1:**" in md
    assert "**Suggested review order:**" in md
    assert "\u2192" in md  # arrow between suggested order items


def test_render_markdown_dependencies(sample_walkthrough: Walkthrough) -> None:
    md = render_markdown(sample_walkthrough)

    assert "*Depends on: auth-error-handling*" in md


def test_render_markdown_overview(sample_walkthrough: Walkthrough) -> None:
    md = render_markdown(sample_walkthrough)

    assert "auth error handling" in md


def test_render_github_comment_markers(sample_walkthrough: Walkthrough) -> None:
    comment = render_github_comment(sample_walkthrough)

    assert comment.startswith(COMMENT_MARKER_START)
    assert COMMENT_MARKER_END in comment
    assert COMMENT_MARKER_DATA_PREFIX in comment


def test_render_github_comment_collapsible(sample_walkthrough: Walkthrough) -> None:
    comment = render_github_comment(sample_walkthrough)

    assert "<details>" in comment
    assert "<summary>Click to expand walkthrough</summary>" in comment
    assert "</details>" in comment


def test_render_github_comment_header(sample_walkthrough: Walkthrough) -> None:
    comment = render_github_comment(sample_walkthrough)

    assert "### Unravel \u2014 2 threads across" in comment


def test_render_github_comment_roundtrip(sample_walkthrough: Walkthrough) -> None:
    """The base64 payload in the comment should decode back to the walkthrough."""
    comment = render_github_comment(sample_walkthrough)

    for line in comment.splitlines():
        stripped = line.strip()
        if stripped.startswith(COMMENT_MARKER_DATA_PREFIX):
            payload = stripped[len(COMMENT_MARKER_DATA_PREFIX):]
            payload = payload.removesuffix("-->").rstrip()
            decoded = base64.b64decode(payload).decode("utf-8")
            data = json.loads(decoded)
            restored = Walkthrough.from_dict(data)
            assert len(restored.threads) == len(sample_walkthrough.threads)
            assert restored.overview == sample_walkthrough.overview
            assert restored.suggested_order == sample_walkthrough.suggested_order
            for orig, rest in zip(
                sample_walkthrough.threads, restored.threads, strict=True
            ):
                assert orig.id == rest.id
                assert orig.title == rest.title
            return

    raise AssertionError("No data marker found in comment")  # pragma: no cover


def test_render_markdown_single_thread() -> None:
    wt = Walkthrough.from_dict({
        "overview": "Single thread change.",
        "suggested_order": ["only-thread"],
        "threads": [
            {
                "id": "only-thread",
                "title": "The Only Thread",
                "summary": "Does one thing.",
                "root_cause": "Needed it.",
                "steps": [
                    {"order": 1, "narration": "Do the thing.", "hunks": ["H1"]},
                ],
            }
        ],
    })
    md = render_markdown(wt)

    assert "1 thread across" in md
    assert "The Only Thread" in md
    assert "`only-thread`" in md
