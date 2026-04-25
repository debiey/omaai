"""oma fix - Suggest fixes for broken Linux commands"""

import click
from rich.console import Console
from rich.panel import Panel
from omaai.ai import ask

console = Console()


@click.command()
@click.argument("command", nargs=-1, required=True)
def fix(command):
    """Suggest a fix for a broken or failing command."""
    cmd = " ".join(command)

    console.print(f"\n[bold red]🔧 Analyzing:[/bold red] {cmd}\n")

    prompt = f"""You are a Linux expert. A user ran this command and it failed or they need help fixing it.

Command: {cmd}

Give a short, practical response:
1. What is likely wrong
2. The corrected command (if applicable)
3. One tip to avoid this issue

Keep it brief and practical. Plain text only, no markdown."""

    with console.status("[yellow]Analyzing...[/yellow]"):
        result = ask(prompt)

    console.print(Panel(result, border_style="red", title="[bold]Fix Suggestion[/bold]"))
