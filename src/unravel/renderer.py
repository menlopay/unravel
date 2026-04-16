"""Output rendering for walkthroughs."""

from __future__ import annotations

import base64
import json

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree

from unravel.models import Walkthrough

COMMENT_MARKER_START = "<!-- unravel-cache-v1-start -->"
COMMENT_MARKER_DATA_PREFIX = "<!-- unravel-cache-v1-data:"
COMMENT_MARKER_END = "<!-- unravel-cache-v1-end -->"


def render_json(walkthrough: Walkthrough) -> str:
    return walkthrough.to_json(indent=2)


def render_rich(walkthrough: Walkthrough, console: Console) -> None:
    threads = walkthrough.threads
    file_count = len({
        h.file_path for t in threads for s in t.steps for h in s.hunks
    })

    header = Text()
    header.append(f"{len(threads)} thread{'s' if len(threads) != 1 else ''}", style="bold cyan")
    header.append(" across ")
    header.append(f"{file_count} file{'s' if file_count != 1 else ''}", style="bold cyan")
    console.print(Panel(header, title="[bold]Unravel[/bold]", border_style="cyan"))

    console.print()
    console.print(walkthrough.overview)
    console.print()

    if walkthrough.suggested_order:
        console.print("[bold]Suggested review order:[/bold]")
        for i, tid in enumerate(walkthrough.suggested_order, 1):
            console.print(f"  {i}. {tid}")
        console.print()

    for thread in threads:
        _render_thread(thread, walkthrough, console)


def _render_thread(thread, walkthrough: Walkthrough, console: Console) -> None:
    dep_text = ""
    if thread.dependencies:
        dep_text = f"\n[dim]Depends on: {', '.join(thread.dependencies)}[/dim]"

    panel_content = Text()
    panel_content.append(thread.summary)

    console.print(Panel(
        f"[bold]{thread.root_cause}[/bold]\n\n{thread.summary}{dep_text}",
        title=f"[bold magenta]{thread.title}[/bold magenta] [dim]({thread.id})[/dim]",
        border_style="magenta",
    ))

    for step in sorted(thread.steps, key=lambda s: s.order):
        console.print(f"  [bold]Step {step.order}:[/bold] {step.narration}")
        console.print()
        for hunk in step.hunks:
            console.print(f"    [dim]{hunk.file_path}[/dim]")
            if hunk.content and hunk.content != "[binary file]":
                syntax = Syntax(
                    hunk.content,
                    "diff",
                    theme="monokai",
                    line_numbers=False,
                    padding=1,
                )
                console.print(syntax)
        console.print()


def render_tree(walkthrough: Walkthrough, console: Console) -> None:
    tree = Tree("[bold cyan]Unravel[/bold cyan]")
    tree.add(f"[dim]{walkthrough.overview}[/dim]")

    for thread in walkthrough.threads:
        if thread.dependencies:
            deps = f" [dim](depends: {', '.join(thread.dependencies)})[/dim]"
        else:
            deps = ""
        label = f"[bold magenta]{thread.title}[/bold magenta] [dim]({thread.id})[/dim]{deps}"
        branch = tree.add(label)
        branch.add(f"[italic]{thread.root_cause}[/italic]")
        for step in sorted(thread.steps, key=lambda s: s.order):
            step_branch = branch.add(f"Step {step.order}: {step.narration}")
            for hunk in step.hunks:
                step_branch.add(f"[dim]{hunk.file_path}[/dim]")

    console.print(tree)


def _thread_file_count(walkthrough: Walkthrough) -> int:
    return len({
        h.file_path for t in walkthrough.threads for s in t.steps for h in s.hunks
    })


def render_markdown(walkthrough: Walkthrough) -> str:
    """Render walkthrough as GitHub-flavored markdown."""
    threads = walkthrough.threads
    file_count = _thread_file_count(walkthrough)

    parts: list[str] = []

    t_word = "thread" if len(threads) == 1 else "threads"
    f_word = "file" if file_count == 1 else "files"
    parts.append(f"{len(threads)} {t_word} across {file_count} {f_word}")
    parts.append("")
    parts.append(walkthrough.overview)
    parts.append("")

    if walkthrough.suggested_order:
        order_str = " \u2192 ".join(f"`{tid}`" for tid in walkthrough.suggested_order)
        parts.append(f"**Suggested review order:** {order_str}")
        parts.append("")

    for thread in threads:
        parts.append("---")
        parts.append("")
        parts.append(f"### {thread.title} (`{thread.id}`)")
        parts.append("")
        parts.append(f"**Root cause:** {thread.root_cause}")
        parts.append("")
        parts.append(thread.summary)
        parts.append("")

        if thread.dependencies:
            deps = ", ".join(thread.dependencies)
            parts.append(f"*Depends on: {deps}*")
            parts.append("")

        for step in sorted(thread.steps, key=lambda s: s.order):
            parts.append(f"**Step {step.order}:** {step.narration}")
            file_list = [f"- `{h.file_path}`" for h in step.hunks if h.file_path]
            if file_list:
                parts.extend(file_list)
            parts.append("")

    return "\n".join(parts)


def render_github_comment(walkthrough: Walkthrough) -> str:
    """Render the full GitHub PR comment body with visible summary and hidden cache.

    The comment has three parts:
    1. A header with thread/file counts
    2. A collapsible ``<details>`` block with the full markdown walkthrough
    3. A base64-encoded JSON payload hidden inside an HTML comment
    """
    threads = walkthrough.threads
    file_count = _thread_file_count(walkthrough)

    t_word = "thread" if len(threads) == 1 else "threads"
    f_word = "file" if file_count == 1 else "files"
    summary_line = f"{len(threads)} {t_word} across {file_count} {f_word}"

    md_body = render_markdown(walkthrough)
    json_payload = json.dumps(walkthrough.to_dict())
    encoded = base64.b64encode(json_payload.encode("utf-8")).decode("ascii")

    parts = [
        COMMENT_MARKER_START,
        "",
        f"### Unravel \u2014 {summary_line}",
        "",
        "<details>",
        "<summary>Click to expand walkthrough</summary>",
        "",
        md_body,
        "</details>",
        "",
        f"{COMMENT_MARKER_DATA_PREFIX}{encoded} -->",
        COMMENT_MARKER_END,
    ]

    return "\n".join(parts)
