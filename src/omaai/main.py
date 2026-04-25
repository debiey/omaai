"""OmaAI - CLI entry point"""

import click
from rich.console import Console
from rich.panel import Panel

from omaai.commands.explain import explain
from omaai.commands.fix import fix
from omaai.commands.monitor import monitor
from omaai.commands.teach import teach

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="OmaAI")
def cli():
    """OmaAI - Your AI-powered Linux companion.

    \b
    Commands:
      explain   Explain a Linux command or error
      fix       Suggest a fix for a broken command
      monitor   Show system CPU, RAM, and disk stats
      teach     Interactive Linux lessons and quizzes
    """
    pass


cli.add_command(explain)
cli.add_command(fix)
cli.add_command(monitor)
cli.add_command(teach)


if __name__ == "__main__":
    cli()
