"""
OmaAI Networking Plugin -- commands
Adds: oma networking ports|scan|dns|interfaces|connections|ping|trace|explain
"""

import subprocess
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich import box

console = Console()


def _run(cmd: list, timeout: int = 30) -> tuple:
    """Run a shell command. Returns (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", 127


def _tool_missing(tool: str) -> bool:
    """Check if a CLI tool is available."""
    _, _, code = _run(["which", tool])
    if code != 0:
        console.print(
            f"[red]❌  '{tool}' is not installed.[/red]\n"
            f"[dim]  Install: sudo apt install {tool}[/dim]\n"
        )
        return True
    return False


# ── Plugin group ──────────────────────────────────────────
@click.group()
def plugin_group():
    """Networking plugin -- diagnose and monitor network activity."""
    pass


# ── oma networking ports ──────────────────────────────────
@plugin_group.command()
@click.option("--all", "-a", "show_all", is_flag=True,
              help="Show all ports including non-listening")
@click.option("--port", "-p", default=None, type=int,
              help="Filter by specific port number")
def ports(show_all, port):
    """Show open ports and what is listening on them."""
    stdout, stderr, code = _run(["ss", "-tulnp"])

    if code != 0:
        console.print(f"[red]❌  {stderr}[/red]")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● Open Ports[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Protocol", style="cyan",  width=10)
    t.add_column("State",    style="green", width=12)
    t.add_column("Local Address",  style="white", width=28)
    t.add_column("Process", style="dim",   width=30)

    lines = stdout.splitlines()
    found = 0
    for line in lines[1:]:  # skip header
        parts = line.split()
        if len(parts) < 5:
            continue
        proto   = parts[0]
        state   = parts[1]
        local   = parts[4]
        process = parts[6] if len(parts) > 6 else ""

        # Filter by port if specified
        if port and f":{port}" not in local:
            continue

        # Skip non-listening unless --all
        if not show_all and state not in ("LISTEN", "UNCONN"):
            continue

        process = process.replace('users:(("', '').split('"')[0] if process else "—"
        t.add_row(proto, state, local, process)
        found += 1

    if found == 0:
        console.print("[dim]  No open ports found.[/dim]\n")
        return

    console.print()
    console.print(t)
    console.print(
        f"[dim]  {found} ports shown · "
        "use --all to include all states · "
        "--port <n> to filter[/dim]\n"
    )


# ── oma networking scan ───────────────────────────────────
@plugin_group.command()
@click.argument("target")
@click.option("--ports", "-p", default="1-1024",
              help="Port range to scan (default: 1-1024)")
@click.option("--fast", "-f", is_flag=True,
              help="Fast scan -- top 100 ports only")
def scan(target, ports, fast):
    """Scan a host or network for open ports."""
    if _tool_missing("nmap"):
        console.print("[dim]  Alternative: sudo apt install nmap[/dim]\n")
        return

    console.print(f"\n[cyan]▸ Scanning {target}...[/cyan]\n")

    cmd = ["nmap", "-sV"]
    if fast:
        cmd += ["-F"]
    else:
        cmd += ["-p", ports]
    cmd.append(target)

    stdout, stderr, code = _run(cmd, timeout=120)

    if code != 0:
        console.print(f"[red]❌  Scan failed: {stderr}[/red]\n")
        return

    console.print(Panel(
        stdout,
        title=f"[bold cyan]● Nmap Scan: {target}[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(0, 1),
    ))
    console.print()


# ── oma networking dns ────────────────────────────────────
@plugin_group.command()
@click.argument("domain")
@click.option("--type", "-t", "record_type", default="A",
              type=click.Choice(["A", "AAAA", "MX", "NS", "TXT", "CNAME", "ALL"]),
              help="DNS record type to look up")
def dns(domain, record_type):
    """Look up DNS records for a domain."""
    console.print(f"\n[cyan]▸ DNS lookup: {domain} ({record_type})[/cyan]\n")

    if record_type == "ALL":
        types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]
    else:
        types = [record_type]

    for rtype in types:
        stdout, stderr, code = _run(["dig", "+short", f"-t{rtype}", domain])
        result = stdout if stdout else "[dim]no record[/dim]"
        console.print(
            f"  [bold cyan]{rtype:6}[/bold cyan]  {result}"
        )

    console.print()
    # Also show reverse lookup
    stdout, _, _ = _run(["dig", "+short", "-x", domain])
    if stdout:
        console.print(f"  [bold cyan]PTR   [/bold cyan]  {stdout}\n")


# ── oma networking interfaces ─────────────────────────────
@plugin_group.command()
def interfaces():
    """Show all network interfaces and their IP addresses."""
    stdout, stderr, code = _run(["ip", "-brief", "address"])

    if code != 0:
        console.print(f"[red]❌  {stderr}[/red]")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● Network Interfaces[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Interface", style="white", width=16)
    t.add_column("State",     style="green", width=10)
    t.add_column("IP Address", style="cyan", width=40)

    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            iface  = parts[0]
            state  = parts[1]
            ips    = " ".join(parts[2:]) if len(parts) > 2 else "—"
            color  = "green" if state == "UP" else "dim"
            t.add_row(iface, f"[{color}]{state}[/{color}]", ips)

    console.print()
    console.print(t)

    # Show default gateway
    gw_out, _, _ = _run(["ip", "route", "show", "default"])
    if gw_out:
        console.print(f"  [dim]Default gateway:[/dim] [cyan]{gw_out}[/cyan]")
    console.print()


# ── oma networking connections ────────────────────────────
@plugin_group.command()
@click.option("--state", "-s", default=None,
              type=click.Choice(["ESTABLISHED", "LISTEN",
                                 "TIME_WAIT", "CLOSE_WAIT"]),
              help="Filter by connection state")
def connections(state):
    """Show active network connections."""
    cmd = ["ss", "-tunp"]
    stdout, stderr, code = _run(cmd)

    if code != 0:
        console.print(f"[red]❌  {stderr}[/red]")
        return

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● Active Connections[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Proto",   style="cyan",  width=7)
    t.add_column("State",   style="green", width=14)
    t.add_column("Local",   style="white", width=26)
    t.add_column("Remote",  style="dim",   width=26)
    t.add_column("Process", style="dim",   width=20)

    lines   = stdout.splitlines()
    count   = 0
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        proto   = parts[0]
        cstate  = parts[1]
        local   = parts[4]
        remote  = parts[5] if len(parts) > 5 else "—"
        process = parts[6] if len(parts) > 6 else "—"

        if state and cstate != state:
            continue

        process = process.replace('users:(("', '').split('"')[0] if process else "—"
        color   = "green" if cstate == "ESTAB" else "dim"
        t.add_row(proto, f"[{color}]{cstate}[/{color}]",
                  local, remote, process)
        count += 1

    if count == 0:
        console.print("[dim]  No connections found.[/dim]\n")
        return

    console.print()
    console.print(t)
    console.print(f"[dim]  {count} connections[/dim]\n")


# ── oma networking ping ───────────────────────────────────
@plugin_group.command()
@click.argument("host")
@click.option("--count", "-c", default=4, help="Number of pings (default: 4)")
def ping(host, count):
    """Ping a host and show results."""
    console.print(f"\n[cyan]▸ Pinging {host}...[/cyan]\n")
    stdout, stderr, code = _run(
        ["ping", "-c", str(count), host], timeout=30
    )

    output = stdout or stderr
    color  = "green" if code == 0 else "red"
    status = "reachable" if code == 0 else "unreachable"

    console.print(Panel(
        output,
        title=f"[bold {color}]● Ping: {host} — {status}[/bold {color}]",
        border_style=color, box=box.ROUNDED, padding=(0, 1),
    ))
    console.print()


# ── oma networking trace ──────────────────────────────────
@plugin_group.command()
@click.argument("host")
def trace(host):
    """Traceroute to a host — show the network path."""
    if _tool_missing("traceroute"):
        console.print("[dim]  Install: sudo apt install traceroute[/dim]\n")
        return

    console.print(f"\n[cyan]▸ Tracing route to {host}...[/cyan]\n")
    stdout, stderr, code = _run(["traceroute", host], timeout=60)

    output = stdout or stderr
    console.print(Panel(
        output,
        title=f"[bold cyan]● Traceroute: {host}[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(0, 1),
    ))
    console.print()


# ── oma networking explain ────────────────────────────────
@plugin_group.command()
@click.argument("query", nargs=-1)
def explain(query):
    """Ask OmaAI to explain a networking concept or error."""
    from oma.ai.engine import get_engine
    from oma.ai.prompts import EXPLAIN_SYSTEM

    text = " ".join(query)
    if not text:
        console.print("[red]❌  Provide a networking question or error.[/red]")
        console.print(
            '[dim]Example: oma networking explain '
            '"connection refused on port 5432"[/dim]\n'
        )
        return

    with console.status(
        "[bold cyan]OmaAI is thinking...[/bold cyan]", spinner="dots"
    ):
        engine   = get_engine()
        response = engine.complete(
            system=EXPLAIN_SYSTEM,
            user=f"Linux networking question: {text}"
        )

    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold cyan]● OmaAI -- Networking Explain[/bold cyan]",
        border_style="cyan", box=box.ROUNDED, padding=(1, 2),
    ))
    console.print()
