"""oma automate - Generate and run automation scripts from plain English"""

import click
import subprocess
import tempfile
import os
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from omaai.ai import ask

console = Console()


def run_script(script: str) -> None:
    """Write script to a temp file and execute it."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write("#!/bin/bash\nset -e\n\n")
        f.write(script)
        tmp_path = f.name

    os.chmod(tmp_path, 0o755)

    try:
        console.print("\n[bold yellow]⚙️  Running...[/bold yellow]\n")
        result = subprocess.run(
            ["bash", tmp_path],
            text=True,
            capture_output=False,
        )
        if result.returncode == 0:
            console.print("\n[bold green]✅ Done![/bold green]")
        else:
            console.print(f"\n[bold red]❌ Script exited with code {result.returncode}[/bold red]")
    finally:
        os.unlink(tmp_path)


def generate_script(task: str) -> str:
    """Ask AI to generate a bash script for the given task."""
    prompt = f"""You are a Linux bash scripting expert.
Generate a safe, clean bash script to perform this task:

Task: {task}

Rules:
- Output ONLY the bash script body, no explanations, no markdown, no backticks
- Use echo statements to show progress
- Make it safe — check if commands exist before running them
- Keep it simple and readable
- Do not include #!/bin/bash (it will be added automatically)

Script:"""

    return ask(prompt, max_tokens=500)


@click.group()
def automate():
    """Generate and run automation scripts from plain English."""
    pass


@automate.command()
@click.argument("task", nargs=-1, required=True)
def run(task):
    """Generate a bash script from plain English and run it.

    \b
    Examples:
      oma automate run backup /home/chioma to /backup
      oma automate run clean old log files in /var/log
      oma automate run create a new user called john
    """
    task_str = " ".join(task)

    console.print(f"\n[bold cyan]🤖 Generating script for:[/bold cyan] {task_str}\n")

    with console.status("[yellow]Generating script...[/yellow]"):
        script = generate_script(task_str)

    if script.startswith("❌"):
        console.print(Panel(script, border_style="red", title="[bold]Error[/bold]"))
        return

    # Show the generated script
    syntax = Syntax(script, "bash", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="cyan", title="[bold]Generated Script[/bold]"))

    # Ask for confirmation
    if Confirm.ask("\n[bold yellow]Run this script?[/bold yellow]", default=False):
        run_script(script)
    else:
        console.print("\n[yellow]Cancelled. Script was not run.[/yellow]")
        console.print("[dim]Tip: Copy the script above to run it manually.[/dim]\n")


@automate.command()
@click.argument("packages", nargs=-1, required=True)
def install(packages):
    """Install multiple packages at once.

    \b
    Examples:
      oma automate install nginx git docker
      oma automate install python3 pip curl wget
    """
    pkg_list = list(packages)
    pkg_str = " ".join(pkg_list)

    console.print(f"\n[bold cyan]📦 Packages to install:[/bold cyan] {pkg_str}\n")

    script_lines = []
    for pkg in pkg_list:
        script_lines.append(f'echo "Installing {pkg}..."')
        script_lines.append(f"sudo apt-get install -y {pkg}")
        script_lines.append(f'echo "✅ {pkg} installed"')
        script_lines.append("")

    script = "\n".join([
        'echo "Updating package list..."',
        "sudo apt-get update -qq",
        "",
    ] + script_lines + [
        'echo ""',
        'echo "✅ All packages installed successfully!"',
    ])

    syntax = Syntax(script, "bash", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, border_style="cyan", title="[bold]Install Script[/bold]"))

    if Confirm.ask("\n[bold yellow]Run this install script?[/bold yellow]", default=False):
        run_script(script)
    else:
        console.print("\n[yellow]Cancelled.[/yellow]\n")
