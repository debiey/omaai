"""
OmaAI Plugin Manager
Handles loading, registering, and managing plugins.

Plugin structure:
  plugins/
  └── docker/
      ├── plugin.yaml
      ├── __init__.py
      └── commands.py
"""

import sys
import importlib
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# Plugins live here — next to the omaai project root
PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


def get_plugins_dir() -> Path:
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    return PLUGINS_DIR


def list_installed() -> list:
    """Return a list of all installed plugin names."""
    plugins_dir = get_plugins_dir()
    installed = []
    for path in sorted(plugins_dir.iterdir()):
        if path.is_dir() and (path / "plugin.yaml").exists():
            installed.append(path.name)
    return installed


def load_metadata(plugin_name: str) -> Optional[dict]:
    """Read plugin.yaml for a given plugin."""
    yaml_path = get_plugins_dir() / plugin_name / "plugin.yaml"
    if not yaml_path.exists():
        return None
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def load_plugin(plugin_name: str):
    """
    Dynamically import a plugin's commands module.
    Returns the module or None if it fails.
    """
    plugin_path = get_plugins_dir() / plugin_name
    if not plugin_path.exists():
        return None

    # Add plugins dir to path so imports work
    plugins_parent = str(plugin_path.parent)
    if plugins_parent not in sys.path:
        sys.path.insert(0, plugins_parent)

    try:
        module = importlib.import_module(f"{plugin_name}.commands")
        return module
    except ImportError as e:
        console.print(f"[red]❌  Failed to load plugin '{plugin_name}': {e}[/red]")
        return None


def load_all_plugins(cli_group):
    """
    Load all installed plugins and register their
    Click command groups onto the main cli.
    Called at startup from cli.py.
    """
    for plugin_name in list_installed():
        module = load_plugin(plugin_name)
        if module and hasattr(module, "plugin_group"):
            cli_group.add_command(module.plugin_group, name=plugin_name)


def show_installed():
    """Print a table of installed plugins."""
    installed = list_installed()

    if not installed:
        console.print("\n[dim]  No plugins installed.[/dim]")
        console.print("[dim]  Run: oma plugin install docker[/dim]\n")
        return

    t = Table(
        box=box.ROUNDED,
        border_style="cyan",
        title="[bold cyan]OmaAI — Installed Plugins[/bold cyan]",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    t.add_column("Plugin",      style="white",  width=16)
    t.add_column("Version",     style="cyan",   width=10)
    t.add_column("Description", style="dim",    width=44)
    t.add_column("Commands",    style="green",  width=24)

    for name in installed:
        meta = load_metadata(name) or {}
        commands = ", ".join(meta.get("commands", []))
        t.add_row(
            f"[bold]{name}[/bold]",
            meta.get("version", "?"),
            meta.get("description", ""),
            commands,
        )

    console.print()
    console.print(t)
    console.print()
