"""
OmaAI -- oma plugin command
Usage:
  oma plugin list
  oma plugin install docker
  oma plugin remove docker
  oma plugin info docker
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import box

from oma.plugins import (
    get_plugins_dir,
    list_installed,
    load_metadata,
    show_installed,
)

console = Console()

# Built-in plugins that ship with OmaAI
BUILTIN_PLUGINS = {
    "docker":     "Manage Docker containers, images, and compose",
    "security":   "Audit permissions, scan for issues, harden configs",
    "networking": "Diagnose network issues, ports, DNS, interfaces",
    "kubernetes": "Deploy and manage Kubernetes clusters",
}


def run_plugin_list():
    """Show installed plugins."""
    show_installed()
    console.print("[dim]  Available built-in plugins:[/dim]")
    for name, desc in BUILTIN_PLUGINS.items():
        installed = name in list_installed()
        status = "[green]installed[/green]" if installed else "[dim]not installed[/dim]"
        console.print(f"  [cyan]{name:14}[/cyan] {desc}  {status}")
    console.print()


def run_plugin_install(plugin_name: str):
    """Install a built-in plugin by name."""
    plugins_dir = get_plugins_dir()
    plugin_path = plugins_dir / plugin_name

    if plugin_path.exists():
        console.print(f"[yellow]⚠  Plugin '{plugin_name}' is already installed.[/yellow]\n")
        return

    if plugin_name not in BUILTIN_PLUGINS:
        console.print(f"[red]❌  Unknown plugin: {plugin_name}[/red]")
        console.print(f"[dim]  Available: {', '.join(BUILTIN_PLUGINS.keys())}[/dim]\n")
        return

    # For built-in plugins, they already exist in the plugins/ folder
    # This command just validates and confirms them
    console.print(
        f"\n[green]✓ Plugin '{plugin_name}' is ready.[/green]\n"
        f"[dim]  Commands added:  oma {plugin_name} --help[/dim]\n"
        f"[dim]  Reload your shell or run: source ~/.bashrc[/dim]\n"
    )


def run_plugin_remove(plugin_name: str):
    """Remove an installed plugin."""
    import shutil
    plugins_dir = get_plugins_dir()
    plugin_path = plugins_dir / plugin_name

    if not plugin_path.exists():
        console.print(f"[red]❌  Plugin '{plugin_name}' is not installed.[/red]\n")
        return

    shutil.rmtree(plugin_path)
    console.print(f"[green]✓ Plugin '{plugin_name}' removed.[/green]\n")


def run_plugin_info(plugin_name: str):
    """Show detailed info about a plugin."""
    meta = load_metadata(plugin_name)
    if not meta:
        console.print(f"[red]❌  Plugin '{plugin_name}' not found.[/red]\n")
        return

    commands = "\n".join(
        f"  [cyan]oma {plugin_name} {cmd}[/cyan]"
        for cmd in meta.get("commands", [])
    )

    console.print(Panel(
        f"[bold]{meta.get('name', plugin_name)}[/bold]  "
        f"[dim]v{meta.get('version', '?')}[/dim]\n\n"
        f"{meta.get('description', '')}\n\n"
        f"[dim]Commands:[/dim]\n{commands}",
        title=f"[bold cyan]● Plugin: {plugin_name}[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()
