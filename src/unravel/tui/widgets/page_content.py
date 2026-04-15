"""Rich-based page content rendering for the walkthrough screen."""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from unravel.models import Thread
from unravel.tui.state import WalkthroughState


def render_page(state: WalkthroughState) -> RenderableType:
    """Build a Rich renderable for the current page."""
    if state.is_overview:
        return _render_overview(state)
    return _render_thread(state)


def _render_overview(state: WalkthroughState) -> RenderableType:
    wt = state.walkthrough
    thread_count = len(wt.threads)
    file_count = len(
        {h.file_path for t in wt.threads for s in t.steps for h in s.hunks}
    )

    header_text = Text()
    header_text.append(
        f"{thread_count} thread{'s' if thread_count != 1 else ''}",
        style="bold cyan",
    )
    header_text.append(" across ")
    header_text.append(
        f"{file_count} file{'s' if file_count != 1 else ''}", style="bold cyan"
    )

    parts: list[RenderableType] = [
        Panel(header_text, title="[bold]unravel[/bold]", border_style="cyan"),
        Text(""),
        Text(wt.overview),
        Text(""),
        Text("Suggested review order:", style="bold"),
    ]
    for i, tid in enumerate(wt.suggested_order, 1):
        thread = next((t for t in wt.threads if t.id == tid), None)
        if thread:
            line = Text()
            line.append(f"  {i}. ", style="bold cyan")
            line.append(thread.title)
            line.append(f"  ({len(thread.steps)} steps)", style="dim")
            parts.append(line)

    parts.append(Text(""))
    parts.append(
        Text("Press → to start reviewing threads.", style="dim italic")
    )

    return Group(*parts)


def _render_thread(state: WalkthroughState) -> RenderableType:
    thread = state.current_thread
    assert thread is not None

    dep_text = ""
    if thread.dependencies:
        dep_text = f"\n\n[dim]Depends on: {', '.join(thread.dependencies)}[/dim]"

    panel_body = (
        f"[bold]{thread.root_cause}[/bold]\n\n{thread.summary}{dep_text}"
    )

    header = Panel(
        panel_body,
        title=(
            f"[bold magenta]{thread.title}[/bold magenta] "
            f"[dim]({thread.id})[/dim]"
        ),
        border_style="magenta",
    )

    parts: list[RenderableType] = [header, Text("")]
    parts.extend(_render_thread_rows(state, thread))

    return Group(*parts)


def _render_thread_rows(
    state: WalkthroughState, thread: Thread
) -> list[RenderableType]:
    """Render each step with its focusable file rows and expanded diffs."""
    rows_list = state.current_rows()
    row_cursor = 0
    parts: list[RenderableType] = []
    sorted_steps = sorted(thread.steps, key=lambda s: s.order)

    for si, step in enumerate(sorted_steps):
        step_line = Text()
        step_line.append(f"  Step {step.order}: ", style="bold green")
        step_line.append(step.narration)
        parts.append(step_line)
        parts.append(Text(""))

        for hi, hunk in enumerate(step.hunks):
            is_focused = row_cursor == state.row_index
            is_expanded = state.is_expanded(state.page_index, row_cursor)

            file_line = Text()
            prefix = "▼ " if is_expanded else "▶ "
            file_line.append(
                f"    {prefix}",
                style="bold yellow" if is_focused else "dim",
            )

            path_style = "bold" if is_focused else ""
            if is_focused:
                file_line.append(
                    f"{hunk.file_path}",
                    style=f"{path_style} reverse yellow".strip(),
                )
            else:
                file_line.append(hunk.file_path, style=path_style)

            if hunk.new_count > 0:
                file_line.append(
                    f"  (lines {hunk.new_start}-"
                    f"{hunk.new_start + hunk.new_count})",
                    style="dim",
                )
            parts.append(file_line)

            if is_expanded:
                parts.append(_render_hunk_diff(hunk))

            row_cursor += 1

        parts.append(Text(""))

    if not rows_list:
        parts.append(Text("    (no hunks in this thread)", style="dim"))

    return parts


def _render_hunk_diff(hunk) -> RenderableType:
    """Render a single hunk's diff content."""
    if hunk.content == "[binary file]":
        return Text("      (binary file)", style="dim")
    if not hunk.content:
        return Text(
            "      (no diff content available)", style="dim italic"
        )
    return Panel(
        Syntax(
            hunk.content,
            "diff",
            theme="monokai",
            line_numbers=False,
            padding=(0, 1),
        ),
        border_style="dim",
        padding=(0, 1),
    )
