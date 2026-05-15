"""
OmaAI — Explain Module
Usage:
  oma explain "permission denied on /etc/shadow"
  oma explain "what is a zombie process"
  dmesg | tail -20 | oma explain --stdin
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import box

from oma.ai.engine import get_engine
from oma.ai.prompts import EXPLAIN_SYSTEM

console = Console()


def run_explain(query: str):
    if not query.strip():
        console.print("[red]❌  No input. Provide an error or question.[/red]")
        return

    with console.status(
        "[bold cyan]OmaAI is thinking...[/bold cyan]",
        spinner="dots"
    ):
        engine   = get_engine()
        response = engine.complete(
            system=EXPLAIN_SYSTEM,
            user=query.strip()
        )

    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold cyan]● OmaAI — Explain[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()
