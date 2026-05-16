"""
OmaAI Docker Plugin -- commands
Adds: oma docker ps|images|logs|build|stop|remove|compose|stats|explain
"""

import subprocess
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

console = Console()


def _run(cmd: list, capture: bool = True) -> tuple:
    """Run a shell command safely. Returns (stdout, stderr, returncode)."""
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def _docker_available() -> bool:
    _, _, code = _run(["docker", "info"])
    if code != 0:
        console.print(
            "[red]❌  Docker is not running or not installed.[/red]\n"
            "[dim]  Install: https://docs.docker.com/engine/install/ubuntu/[/dim]\n"
            "[dim]  Start:   sudo systemctl start docker[/dim]\n"
        )
        return False
    return True


# ── Plugin group ──────────────────────────────────────────
@click.group()
def plugin_group():
    """Docker plugin -- manage containers, images, and compose."""
    pass


# ── oma docker ps ─────────────────────────────────────────
@plugin_group.command()
@click.option("--all", "-a", "show_all", is_flag=True,
              help="Show all containers including stopped ones")
def ps(show_all):
    """List running containers."""
    if not _docker_available():
        return

    cmd = ["docker", "ps", "--format",
           "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"]
    if show_all:
        cmd.insert(2, "-a")

    stdout, stderr, code = _run(cmd)

    if code != 0:
        console.print(f"[red]❌  {stderr}[/red]")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● Docker Containers[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("ID",      style="dim",   width=14)
    t.add_column("Name",    style="white", width=20)
    t.add_column("Image",   style="cyan",  width=22)
    t.add_column("Status",  style="green", width=20)
    t.add_column("Ports",   style="dim",   width=24)

    if not stdout:
        console.print("[dim]  No containers running.[/dim]")
        console.print("[dim]  Use --all to show stopped containers.[/dim]\n")
        return

    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            t.add_row(*parts[:5])

    console.print()
    console.print(t)
    console.print()


# ── oma docker images ─────────────────────────────────────
@plugin_group.command()
def images():
    """List Docker images."""
    if not _docker_available():
        return

    stdout, stderr, code = _run([
        "docker", "images",
        "--format", "{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"
    ])

    if code != 0:
        console.print(f"[red]❌  {stderr}[/red]")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● Docker Images[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Repository", style="white", width=24)
    t.add_column("Tag",        style="cyan",  width=14)
    t.add_column("ID",         style="dim",   width=14)
    t.add_column("Size",       style="green", width=10)
    t.add_column("Created",    style="dim",   width=16)

    if not stdout:
        console.print("[dim]  No images found.[/dim]\n")
        return

    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            t.add_row(*parts[:5])

    console.print()
    console.print(t)
    console.print()


# ── oma docker logs ───────────────────────────────────────
@plugin_group.command()
@click.argument("container")
@click.option("--lines", "-n", default=50, help="Number of lines to show")
@click.option("--explain", "with_explain", is_flag=True,
              help="Ask OmaAI to explain the logs")
def logs(container, lines, with_explain):
    """Show logs for a container."""
    if not _docker_available():
        return

    stdout, stderr, code = _run([
        "docker", "logs", "--tail", str(lines), container
    ])

    output = stdout or stderr

    if not output:
        console.print(f"[dim]  No logs for container: {container}[/dim]\n")
        return

    console.print(Panel(
        output,
        title=f"[bold cyan]● Docker Logs: {container}[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(0, 1),
    ))

    if with_explain:
        from oma.ai.engine import get_engine
        from oma.ai.prompts import EXPLAIN_SYSTEM
        with console.status("[bold cyan]OmaAI is analyzing logs...[/bold cyan]", spinner="dots"):
            engine   = get_engine()
            analysis = engine.complete(
                system=EXPLAIN_SYSTEM,
                user=f"Analyze these Docker container logs:\n\n{output}"
            )
        console.print()
        console.print(Panel(
            Markdown(analysis),
            title="[bold cyan]● OmaAI -- Log Analysis[/bold cyan]",
            border_style="cyan", box=box.ROUNDED, padding=(1, 2),
        ))
    console.print()


# ── oma docker build ──────────────────────────────────────
@plugin_group.command("build")
@click.argument("path", default=".")
@click.option("--tag", "-t", default=None, help="Image tag e.g. myapp:latest")
def docker_build(path, tag):
    """Build a Docker image from a Dockerfile."""
    if not _docker_available():
        return

    cmd = ["docker", "build", path]
    if tag:
        cmd += ["-t", tag]

    console.print(f"[cyan]▸ Building image from {path}...[/cyan]\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        console.print("\n[green]✓ Image built successfully.[/green]\n")
    else:
        console.print("\n[red]✗ Build failed.[/red]\n")


# ── oma docker stop ───────────────────────────────────────
@plugin_group.command()
@click.argument("container")
def stop(container):
    """Stop a running container."""
    if not _docker_available():
        return

    stdout, stderr, code = _run(["docker", "stop", container])
    if code == 0:
        console.print(f"[green]✓ Stopped: {container}[/green]\n")
    else:
        console.print(f"[red]❌  {stderr}[/red]\n")


# ── oma docker remove ─────────────────────────────────────
@plugin_group.command()
@click.argument("container")
@click.option("--force", "-f", is_flag=True, help="Force remove running container")
def remove(container, force):
    """Remove a container."""
    if not _docker_available():
        return

    cmd = ["docker", "rm", container]
    if force:
        cmd.insert(2, "-f")

    stdout, stderr, code = _run(cmd)
    if code == 0:
        console.print(f"[green]✓ Removed: {container}[/green]\n")
    else:
        console.print(f"[red]❌  {stderr}[/red]\n")


# ── oma docker stats ──────────────────────────────────────
@plugin_group.command()
def stats():
    """Show live resource usage for all containers."""
    if not _docker_available():
        return

    stdout, stderr, code = _run([
        "docker", "stats", "--no-stream",
        "--format",
        "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    ])

    if not stdout:
        console.print("[dim]  No containers running.[/dim]\n")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● Docker Stats[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Container", style="white", width=22)
    t.add_column("CPU%",      style="green", width=8)
    t.add_column("Memory",    style="cyan",  width=22)
    t.add_column("Net I/O",   style="dim",   width=20)
    t.add_column("Block I/O", style="dim",   width=20)

    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            t.add_row(*parts[:5])

    console.print()
    console.print(t)
    console.print()


# ── oma docker compose ────────────────────────────────────
@plugin_group.command()
@click.argument("action",
                type=click.Choice(["up", "down", "restart", "ps", "logs"]))
@click.option("--detach", "-d", is_flag=True, help="Run in background")
def compose(action, detach):
    """Run docker compose commands."""
    if not _docker_available():
        return

    cmd = ["docker", "compose", action]
    if action == "up" and detach:
        cmd.append("-d")

    console.print(f"[cyan]▸ docker compose {action}...[/cyan]\n")
    subprocess.run(cmd)
    console.print()


# ── oma docker explain ────────────────────────────────────
@plugin_group.command()
@click.argument("query", nargs=-1)
def explain(query):
    """Ask OmaAI to explain a Docker concept or error."""
    from oma.ai.engine import get_engine
    from oma.ai.prompts import EXPLAIN_SYSTEM

    text = " ".join(query)
    if not text:
        console.print("[red]❌  Provide a Docker question or error.[/red]")
        console.print('[dim]Example: oma docker explain "what is a volume"[/dim]\n')
        return

    with console.status("[bold cyan]OmaAI is thinking...[/bold cyan]", spinner="dots"):
        engine   = get_engine()
        response = engine.complete(
            system=EXPLAIN_SYSTEM,
            user=f"Docker question: {text}"
        )

    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold cyan]● OmaAI -- Docker Explain[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(1, 2),
    ))
    console.print()
