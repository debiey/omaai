"""oma monitor - Show system CPU, RAM, and disk stats"""

import click
import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


console = Console()


def get_color(percent: float) -> str:
    if percent < 60:
        return "green"
    elif percent < 85:
        return "yellow"
    return "red"


def make_bar(percent: float, width: int = 20) -> str:
    filled = int(percent / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return bar


@click.command()
def monitor():
    """Show real-time system stats: CPU, RAM, and disk."""
    console.print("\n[bold cyan]📊 System Monitor[/bold cyan]\n")

    # CPU
    cpu = psutil.cpu_percent(interval=1)
    cpu_color = get_color(cpu)
    cpu_bar = make_bar(cpu)

    # Memory
    mem = psutil.virtual_memory()
    mem_color = get_color(mem.percent)
    mem_bar = make_bar(mem.percent)
    mem_used = mem.used / 1024 ** 3
    mem_total = mem.total / 1024 ** 3

    # Disk
    disk = psutil.disk_usage("/")
    disk_color = get_color(disk.percent)
    disk_bar = make_bar(disk.percent)
    disk_used = disk.used / 1024 ** 3
    disk_total = disk.total / 1024 ** 3
    disk_free = disk.free / 1024 ** 3

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Resource", style="bold", width=10)
    table.add_column("Usage", width=24)
    table.add_column("Percent", width=8)
    table.add_column("Details", width=25)

    table.add_row(
        "CPU",
        f"[{cpu_color}]{cpu_bar}[/{cpu_color}]",
        f"[{cpu_color}]{cpu:.1f}%[/{cpu_color}]",
        f"{psutil.cpu_count()} cores",
    )

    table.add_row(
        "RAM",
        f"[{mem_color}]{mem_bar}[/{mem_color}]",
        f"[{mem_color}]{mem.percent:.1f}%[/{mem_color}]",
        f"{mem_used:.1f}GB / {mem_total:.1f}GB",
    )

    table.add_row(
        "Disk",
        f"[{disk_color}]{disk_bar}[/{disk_color}]",
        f"[{disk_color}]{disk.percent:.1f}%[/{disk_color}]",
        f"{disk_free:.1f}GB free of {disk_total:.1f}GB",
    )

    console.print(table)

    # Health summary
    issues = []
    if cpu > 85:
        issues.append("CPU is very high")
    if mem.percent > 85:
        issues.append("RAM is running low")
    if disk.percent > 85:
        issues.append("Disk space is low")

    if issues:
        console.print(f"\n[bold red]⚠️  Warning:[/bold red] {', '.join(issues)}")
    else:
        console.print("\n[bold green]✅ System is healthy[/bold green]")

    console.print()
