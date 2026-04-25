"""oma explain - Explain Linux commands and errors"""

import click
from rich.console import Console
from rich.panel import Panel
from omaai.ai import ask

console = Console()


@click.command()
@click.argument("topic", nargs=-1, required=True)
def explain(topic):
    """Explain a Linux command or error message."""
    query = " ".join(topic)

    console.print(f"\n[bold cyan]🔍 Explaining:[/bold cyan] {query}\n")

    prompt = f"""You are a Linux expert. Explain the following in simple, clear terms.
Keep it concise — 3 to 5 sentences max. Use plain text, no markdown.

Topic: {query}

Explanation:"""

    with console.status("[yellow]Thinking...[/yellow]"):
        result = ask(prompt)

    console.print(Panel(result, border_style="cyan", title="[bold]Explanation[/bold]"))
