"""
OmaAI — Monitor Module
Usage:
  oma monitor              Live dashboard
  oma monitor --once       Single snapshot
  oma monitor --explain    Snapshot + AI health analysis
"""

import time
import json
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.markdown import Markdown
from rich.align import Align
from rich import box

from oma.system.metrics import snapshot
from oma.ai.engine import get_engine
from oma.ai.prompts import MONITOR_EXPLAIN_SYSTEM

console = Console()


# ── Rendering helpers ─────────────────────────────────────

def _bar(percent: float, width: int = 20) -> str:
    filled = int(width * percent / 100)
    bar    = "█" * filled + "░" * (width - filled)
    color  = "green" if percent < 70 else ("yellow" if percent < 90 else "red")
    return f"[{color}]{bar}[/{color}] [dim]{percent:.1f}%[/dim]"


def _cpu_panel(d: dict) -> Panel:
    cpu   = d["cpu"]
    cores = f"{cpu['count_physical']}p / {cpu['count_logical']}t"
    freq  = f" @ {cpu['freq_mhz']} MHz" if cpu["freq_mhz"] else ""
    lines = [
        f"[bold]Overall:[/bold] {_bar(cpu['percent'])}",
        f"[dim]{cores}{freq}[/dim]",
    ]
    if cpu["per_core"]:
        lines.append(
            "  ".join(
                f"[dim]C{i}[/dim] {_bar(p, 8)}"
                for i, p in enumerate(cpu["per_core"])
            )
        )
    return Panel(
        "\n".join(lines),
        title="[bold cyan]● CPU[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(0, 1),
    )


def _mem_panel(d: dict) -> Panel:
    m     = d["memory"]
    lines = [
        f"[bold]RAM:[/bold]  {_bar(m['percent'])}  "
        f"[dim]{m['used_gb']}/{m['total_gb']} GB[/dim]",
    ]
    if m["swap_total_gb"] > 0:
        lines.append(
            f"[bold]Swap:[/bold] {_bar(m['swap_percent'])}  "
            f"[dim]{m['swap_used_gb']}/{m['swap_total_gb']} GB[/dim]"
        )
    return Panel(
        "\n".join(lines),
        title="[bold magenta]● Memory[/bold magenta]",
        border_style="magenta", box=box.ROUNDED, padding=(0, 1),
    )


def _disk_panel(d: dict) -> Panel:
    lines = [
        f"[dim]{p['mountpoint']:12}[/dim] {_bar(p['percent'])}  "
        f"[dim]{p['free_gb']:.1f} GB free[/dim]"
        for p in d["disk"] if p["total_gb"] > 0.1
    ]
    return Panel(
        "\n".join(lines) or "[dim]No disk data[/dim]",
        title="[bold yellow]● Disk[/bold yellow]",
        border_style="yellow", box=box.ROUNDED, padding=(0, 1),
    )


def _net_panel(d: dict) -> Panel:
    n = d["network"]
    return Panel(
        f"[dim]Sent:[/dim]     [green]{n['bytes_sent_mb']:>8.1f} MB[/green]\n"
        f"[dim]Received:[/dim] [cyan]{n['bytes_recv_mb']:>8.1f} MB[/cyan]\n"
        f"[dim]Packets  out: {n['packets_sent']:,}  in: {n['packets_recv']:,}[/dim]",
        title="[bold green]● Network[/bold green]",
        border_style="green", box=box.ROUNDED, padding=(0, 1),
    )


def _proc_panel(d: dict) -> Panel:
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    t.add_column("PID",   style="dim",   width=7)
    t.add_column("Name",  style="white", width=22)
    t.add_column("CPU%",  justify="right", width=7)
    t.add_column("MEM%",  justify="right", width=7)
    t.add_column("State", style="dim",   width=10)

    for p in d["top_processes"]:
        cpu = p.get("cpu_percent") or 0
        mem = p.get("memory_percent") or 0
        c   = "red" if cpu > 80 else ("yellow" if cpu > 40 else "green")
        t.add_row(
            str(p.get("pid", "")),
            (p.get("name", "") or "")[:22],
            f"[{c}]{cpu:.1f}[/{c}]",
            f"{mem:.1f}",
            p.get("status", ""),
        )
    return Panel(
        t,
        title="[bold white]● Top Processes[/bold white]",
        border_style="white", box=box.ROUNDED, padding=(0, 1),
    )


def _svc_panel(d: dict) -> Panel:
    svcs = d.get("services", [])
    if not svcs:
        return Panel(
            "[green]✓ No failed services[/green]",
            title="[bold]● Services[/bold]",
            border_style="dim", box=box.ROUNDED,
        )
    lines = [
        f"[red]✗[/red] [dim]{s.get('name', '')[:40]}[/dim]"
        for s in svcs[:8]
    ]
    return Panel(
        "\n".join(lines),
        title="[bold red]● Failed Services[/bold red]",
        border_style="red", box=box.ROUNDED, padding=(0, 1),
    )


def _header(d: dict) -> Text:
    t = Text()
    t.append(" OmaAI Monitor ", style="bold black on cyan")
    t.append(f"  uptime: {d['uptime']}", style="dim")
    t.append(f"  {d['timestamp'][11:19]}", style="dim cyan")
    return t


def _layout(d: dict):
    from rich.console import Group
    return Group(
        Align(_header(d), align="left"),
        Text(""),
        Columns([_cpu_panel(d), _mem_panel(d)], equal=True, expand=True),
        _disk_panel(d),
        Columns([_net_panel(d), _svc_panel(d)], equal=True, expand=True),
        _proc_panel(d),
        Text(
            "  [dim]Ctrl+C to exit  ·  "
            "oma monitor --explain for AI analysis  ·  "
            "oma monitor --once for snapshot[/dim]"
        ),
    )


# ── Public API ────────────────────────────────────────────

def run_monitor_once():
    console.print(_layout(snapshot()))


def run_monitor_live(interval: int = 3):
    try:
        with Live(console=console, refresh_per_second=1, screen=True) as live:
            while True:
                live.update(_layout(snapshot()))
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]Monitor stopped.[/dim]\n")


def run_monitor_explain():
    with console.status(
        "[bold cyan]Reading your system...[/bold cyan]", spinner="dots"
    ):
        data = snapshot()

    summary = {
        "uptime":          data["uptime"],
        "cpu_percent":     data["cpu"]["percent"],
        "memory_percent":  data["memory"]["percent"],
        "swap_percent":    data["memory"]["swap_percent"],
        "disk":            [
            {"mount": d["mountpoint"], "pct": d["percent"], "free_gb": d["free_gb"]}
            for d in data["disk"]
        ],
        "failed_services": data["services"],
        "top_processes":   [
            {
                "name": p["name"],
                "cpu":  p.get("cpu_percent", 0),
                "mem":  round(p.get("memory_percent", 0), 1),
            }
            for p in data["top_processes"][:5]
        ],
    }

    with console.status(
        "[bold cyan]OmaAI is analyzing...[/bold cyan]", spinner="dots"
    ):
        engine   = get_engine()
        analysis = engine.complete(
            system=MONITOR_EXPLAIN_SYSTEM,
            user=f"System snapshot:\n{json.dumps(summary, indent=2)}"
        )

    run_monitor_once()
    console.print()
    console.print(Panel(
        Markdown(analysis),
        title="[bold cyan]● OmaAI — System Analysis[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(1, 2),
    ))
    console.print()
