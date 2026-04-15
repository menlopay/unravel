"""Hydrate walkthrough hunks with diff content from parsed hunks."""

from __future__ import annotations

from unravel.models import Hunk, Walkthrough


def hydrate_walkthrough(
    walkthrough: Walkthrough, parsed_hunks: list[Hunk]
) -> tuple[Walkthrough, list[str]]:
    """Match LLM hunk references to parsed hunks and copy content + language.

    Returns (walkthrough, warnings). The walkthrough is mutated in place.
    """
    warnings: list[str] = []
    exact = _build_exact_index(parsed_hunks)
    fuzzy = _build_fuzzy_index(parsed_hunks)

    for thread in walkthrough.threads:
        for step in thread.steps:
            for hunk in step.hunks:
                key = (hunk.file_path, hunk.new_start, hunk.new_count)
                if key in exact:
                    source = exact[key]
                    hunk.content = source.content
                    hunk.language = source.language
                else:
                    fuzzy_key = (hunk.file_path, hunk.new_start)
                    if fuzzy_key in fuzzy:
                        source = _closest_by_count(fuzzy[fuzzy_key], hunk.new_count)
                        hunk.content = source.content
                        hunk.language = source.language
                        warnings.append(
                            f"Fuzzy match for {hunk.file_path} "
                            f"(new_start={hunk.new_start}, "
                            f"expected count={hunk.new_count}, "
                            f"matched count={source.new_count})"
                        )
                    else:
                        warnings.append(
                            f"No matching parsed hunk for {hunk.file_path} "
                            f"(new_start={hunk.new_start}, new_count={hunk.new_count})"
                        )

    return walkthrough, warnings


def _build_exact_index(hunks: list[Hunk]) -> dict[tuple[str, int, int], Hunk]:
    index: dict[tuple[str, int, int], Hunk] = {}
    for h in hunks:
        index[(h.file_path, h.new_start, h.new_count)] = h
    return index


def _build_fuzzy_index(hunks: list[Hunk]) -> dict[tuple[str, int], list[Hunk]]:
    index: dict[tuple[str, int], list[Hunk]] = {}
    for h in hunks:
        key = (h.file_path, h.new_start)
        index.setdefault(key, []).append(h)
    return index


def _closest_by_count(candidates: list[Hunk], target_count: int) -> Hunk:
    return min(candidates, key=lambda h: abs(h.new_count - target_count))
