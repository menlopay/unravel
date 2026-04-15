"""Tests for hunk hydration."""

from __future__ import annotations

from unravel.git import parse_diff
from unravel.hydration import hydrate_walkthrough
from unravel.models import Hunk, Thread, ThreadStep, Walkthrough


class TestHydrateWalkthrough:
    def test_exact_match(self, simple_diff: str):
        parsed = parse_diff(simple_diff)
        first = parsed[0]

        wt = Walkthrough(
            threads=[
                Thread(
                    id="t1",
                    title="T1",
                    summary="s",
                    root_cause="r",
                    steps=[
                        ThreadStep(
                            hunks=[
                                Hunk(
                                    file_path=first.file_path,
                                    new_start=first.new_start,
                                    new_count=first.new_count,
                                )
                            ],
                            narration="test",
                            order=1,
                        )
                    ],
                )
            ],
            overview="test",
            suggested_order=["t1"],
        )

        wt, warnings = hydrate_walkthrough(wt, parsed)
        assert wt.threads[0].steps[0].hunks[0].content == first.content
        assert wt.threads[0].steps[0].hunks[0].language == first.language
        assert not any("Fuzzy" in w for w in warnings)

    def test_fuzzy_match(self, simple_diff: str):
        parsed = parse_diff(simple_diff)
        first = parsed[0]

        wt = Walkthrough(
            threads=[
                Thread(
                    id="t1",
                    title="T1",
                    summary="s",
                    root_cause="r",
                    steps=[
                        ThreadStep(
                            hunks=[
                                Hunk(
                                    file_path=first.file_path,
                                    new_start=first.new_start,
                                    new_count=first.new_count + 2,
                                )
                            ],
                            narration="test",
                            order=1,
                        )
                    ],
                )
            ],
            overview="test",
            suggested_order=["t1"],
        )

        wt, warnings = hydrate_walkthrough(wt, parsed)
        assert wt.threads[0].steps[0].hunks[0].content == first.content
        assert any("Fuzzy" in w for w in warnings)

    def test_no_match(self, simple_diff: str):
        parsed = parse_diff(simple_diff)

        wt = Walkthrough(
            threads=[
                Thread(
                    id="t1",
                    title="T1",
                    summary="s",
                    root_cause="r",
                    steps=[
                        ThreadStep(
                            hunks=[
                                Hunk(
                                    file_path="nonexistent.py",
                                    new_start=999,
                                    new_count=1,
                                )
                            ],
                            narration="test",
                            order=1,
                        )
                    ],
                )
            ],
            overview="test",
            suggested_order=["t1"],
        )

        wt, warnings = hydrate_walkthrough(wt, parsed)
        assert wt.threads[0].steps[0].hunks[0].content == ""
        assert any("No matching" in w for w in warnings)

    def test_with_fixture(self, sample_walkthrough: Walkthrough, simple_diff: str):
        parsed = parse_diff(simple_diff)
        wt, warnings = hydrate_walkthrough(sample_walkthrough, parsed)
        hydrated_count = sum(
            1
            for t in wt.threads
            for s in t.steps
            for h in s.hunks
            if h.content
        )
        assert hydrated_count > 0
