import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

BANNER = """\
[bold cyan]
  ██████╗ ███╗   ███╗ █████╗  █████╗ ██╗
 ██╔═══██╗████╗ ████║██╔══██╗██╔══██╗██║
 ██║   ██║██╔████╔██║███████║███████║██║
 ██║   ██║██║╚██╔╝██║██╔══██║██╔══██║██║
 ╚██████╔╝██║ ╚═╝ ██║██║  ██║██║  ██║██║
  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝[/bold cyan]
[dim]  CLI-first AI developer platform · v0.1.0[/dim]
"""


@click.group(invoke_without_command=True)
@click.version_option("0.1.0", prog_name="OmaAI")
@click.pass_context
def cli(ctx):
    """OmaAI — your AI-powered Linux developer platform."""
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print(Panel(
            "  [cyan]oma explain[/cyan] [dim]<error or question>[/dim]"
            "     Explain any error or concept\n"
            "  [yellow]oma fix[/yellow] [dim]<script.sh>[/dim]"
            "                Fix a broken script\n"
            "  [green]oma monitor[/green]"
            "                        Live system dashboard\n"
            "  [magenta]oma teach[/magenta] [dim]<topic>[/dim]"
            "               Interactive Linux lessons\n"
            "  [bold green]oma build[/bold green] [dim]<project>[/dim]"
            "              Scaffold a full project\n"
            "  [dim]oma config[/dim]"
            "                         View and change settings\n\n"
            "[dim]  Run [bold]oma <command> --help[/bold] for details.[/dim]",
            title="[bold cyan]● OmaAI[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        ))


@cli.command()
@click.argument("query", nargs=-1, required=False)
@click.option("--stdin", "-", "from_stdin", is_flag=True)
def explain(query, from_stdin):
    """Explain an error, command output, or Linux concept."""
    from oma.modules.explain import run_explain

    if from_stdin or not sys.stdin.isatty():
        text = sys.stdin.read()
        if query:
            text = " ".join(query) + "\n\nContext:\n" + text
    elif query:
        text = " ".join(query)
    else:
        console.print("[red]❌  Provide a query or pipe input with --stdin.[/red]")
        console.print('[dim]Example: oma explain "permission denied"[/dim]')
        return

    run_explain(text)


@cli.command()
@click.argument("file", required=False, type=click.Path())
@click.option("--stdin", "-", "from_stdin", is_flag=True)
@click.option("--execute", "-x", is_flag=True)
@click.option("--save", "-s", "save_path", default=None)
def fix(file, from_stdin, execute, save_path):
    """Fix a broken script or code file."""
    from oma.modules.fix import run_fix

    if from_stdin or (not file and not sys.stdin.isatty()):
        content  = sys.stdin.read()
        filename = "stdin"
    elif file:
        try:
            from pathlib import Path
            content  = Path(file).read_text()
            filename = file
        except FileNotFoundError:
            console.print(f"[red]❌  File not found: {file}[/red]")
            return
    else:
        console.print("[red]❌  Provide a file or use --stdin.[/red]")
        return

    run_fix(content, filename=filename, execute=execute, save_path=save_path)


@cli.command()
@click.option("--once", is_flag=True)
@click.option("--explain", "with_explain", is_flag=True)
@click.option("--interval", "-i", default=None, type=int)
def monitor(once, with_explain, interval):
    """Live system monitor — CPU, memory, disk, services."""
    from oma.modules.monitor import run_monitor_once, run_monitor_live, run_monitor_explain
    from oma.config import load_config

    if with_explain:
        run_monitor_explain()
    elif once:
        run_monitor_once()
    else:
        cfg  = load_config()
        secs = interval or cfg.get("monitor_interval", 3)
        console.print(f"[dim]  OmaAI Monitor · refresh every {secs}s · Ctrl+C to exit[/dim]\n")
        run_monitor_live(interval=secs)


@cli.command()
@click.argument("topic", nargs=-1, required=False)
@click.option("--level", "-l",
              type=click.Choice(["beginner", "intermediate", "advanced"]),
              default="intermediate")
def teach(topic, level):
    """Interactive Linux and tech learning mode."""
    from oma.modules.teach import run_teach
    run_teach(" ".join(topic) if topic else "", level=level)


@cli.command()
@click.option("--set", "set_key", nargs=2, metavar="KEY VALUE")
def config(set_key):
    """View and edit OmaAI configuration."""
    from oma.config import load_config, save_config, CONFIG_FILE
    from rich.table import Table

    cfg = load_config()

    if set_key:
        key, value = set_key
        keys   = key.split(".")
        target = cfg
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        if value.lower() == "true":    value = True
        elif value.lower() == "false": value = False
        elif value.isdigit():          value = int(value)
        target[keys[-1]] = value
        save_config(cfg)
        console.print(f"[green]✓ {key} = {value}[/green]  [dim](saved to {CONFIG_FILE})[/dim]\n")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title=f"[bold cyan]OmaAI Config[/bold cyan] [dim]({CONFIG_FILE})[/dim]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Key",   style="white", width=24)
    t.add_column("Value", style="cyan",  width=40)

    def _flat(d, prefix=""):
        for k, v in d.items():
            fk = f"{prefix}{k}"
            if isinstance(v, dict):
                yield from _flat(v, f"{fk}.")
            else:
                yield fk, str(v)

    for k, v in _flat(cfg):
        t.add_row(k, v)

    console.print()
    console.print(t)
    console.print()
    console.print("[dim]  Switch provider:[/dim]")
    console.print("[dim]    oma config --set provider ollama[/dim]")
    console.print("[dim]    oma config --set provider openai[/dim]")
    console.print("[dim]    oma config --set provider anthropic[/dim]")
    console.print()
    console.print("[dim]  Switch Ollama model:[/dim]")
    console.print("[dim]    oma config --set model.ollama mistral[/dim]")
    console.print("[dim]    oma config --set model.ollama gemma3[/dim]\n")

@cli.command()
@click.argument("project", nargs=-1, required=False)
@click.option("--stack", "-s", default=None,
              help="Preferred tech stack e.g. fastapi, django, flask")
def build(project, stack):
    """Generate full project architecture, structure, and starter code.

    \b
    Examples:
      oma build "CBT exam system"
      oma build "REST API for a school" --stack fastapi
      oma build "e-commerce backend"
      oma build "Linux monitoring dashboard"
    """
    from oma.modules.build import run_build
    project_str = " ".join(project) if project else ""
    if not project_str:
        console.print("[red]❌  Describe what you want to build.[/red]")
        console.print('[dim]Example: oma build "CBT exam system"[/dim]')
        return
    run_build(project_str, stack=stack)


if __name__ == "__main__":
    cli()
