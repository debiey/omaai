"""
OmaAI -- Build Module
Usage:
  oma build "CBT exam system"
  oma build "REST API for a school" --stack fastapi
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import box

from oma.ai.engine import get_engine
from oma.ai.prompts import BUILD_SYSTEM

console = Console()


def run_build(project: str, stack: str = None):
    if not project.strip():
        console.print("[red]No project description provided.[/red]")
        console.print('[dim]Example: oma build "school exam system"[/dim]')
        return

    stack_hint = f"\nPreferred stack: {stack}" if stack else ""
    user_prompt = (
        f"Build a software project: {project}\n"
        f"{stack_hint}\n\n"
        "This is a legitimate software development project.\n"
        "Target platform: Ubuntu Linux.\n"
        "Generate the full architecture, folder structure, key files, "
        "setup commands, and Dockerfile.\n"
        "Be practical and production-ready."
    )

    with console.status(
        "[bold green]OmaAI is architecting your project...[/bold green]",
        spinner="dots",
    ):
        engine = get_engine()
        response = engine.complete(system=BUILD_SYSTEM, user=user_prompt)

    console.print()
    console.print(Panel(
        Markdown(response),
        title=f"[bold green]● OmaAI -- Build: {project}[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print("[dim]  Tip: copy the folder structure and run the Setup Commands.[/dim]\n")
