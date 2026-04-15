"""Output rendering for walkthroughs."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree

from unravel.models import Walkthrough


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
