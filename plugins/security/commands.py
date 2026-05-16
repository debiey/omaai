"""
OmaAI Security Plugin -- commands
Adds: oma security audit|ports|ssh|firewall|users|explain
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
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", 127


def _ok(msg):  console.print(f"  [green]✓[/green]  {msg}")
def _warn(msg): console.print(f"  [yellow]⚠[/yellow]  {msg}")
def _fail(msg): console.print(f"  [red]✗[/red]  {msg}")
def _info(msg): console.print(f"  [dim]→[/dim]  {msg}")


# ── Plugin group ──────────────────────────────────────────
@click.group()
def plugin_group():
    """Security plugin -- audit and harden your Ubuntu system."""
    pass


# ── oma security audit ────────────────────────────────────
@plugin_group.command()
def audit():
    """Run a full system security audit."""
    console.print()
    console.print(
        "[bold red]● OmaAI Security Audit[/bold red]  "
        "[dim]scanning your system...[/dim]\n"
    )

    issues   = []
    score    = 100

    # ── 1. SSH root login ─────────────────────────────────
    console.print("[bold]SSH Configuration[/bold]")
    sshd = "/etc/ssh/sshd_config"
    stdout, _, code = _run(["grep", "-i", "permitrootlogin", sshd])
    if "yes" in stdout.lower():
        _fail("Root SSH login is ENABLED — high risk")
        issues.append("Disable root SSH: set PermitRootLogin no in /etc/ssh/sshd_config")
        score -= 20
    elif "no" in stdout.lower() or "prohibit-password" in stdout.lower():
        _ok("Root SSH login is disabled")
    else:
        _warn("PermitRootLogin not explicitly set — defaults may allow root")
        score -= 5

    stdout, _, _ = _run(["grep", "-i", "passwordauthentication", sshd])
    if "yes" in stdout.lower():
        _warn("Password authentication enabled — consider key-only auth")
        issues.append("Use SSH keys only: set PasswordAuthentication no")
        score -= 10
    else:
        _ok("Password authentication disabled — key-only SSH")

    stdout, _, _ = _run(["grep", "-i", "^port", sshd])
    if stdout and "22" in stdout:
        _warn("SSH running on default port 22")
        issues.append("Change SSH port from 22 to a high port (e.g. 2222)")
        score -= 5
    else:
        _ok("SSH not on default port 22")

    # ── 2. Firewall ───────────────────────────────────────
    console.print("\n[bold]Firewall[/bold]")
    stdout, _, code = _run(["sudo", "ufw", "status"])
    if "inactive" in stdout.lower() or code != 0:
        _fail("UFW firewall is INACTIVE")
        issues.append("Enable firewall: sudo ufw enable")
        score -= 25
    elif "active" in stdout.lower():
        _ok("UFW firewall is active")
    else:
        _warn("Could not determine firewall status")
        score -= 5

    # ── 3. Unattended upgrades ────────────────────────────
    console.print("\n[bold]Automatic Security Updates[/bold]")
    stdout, _, code = _run(
        ["dpkg", "-l", "unattended-upgrades"]
    )
    if "ii" in stdout:
        _ok("unattended-upgrades is installed")
    else:
        _warn("unattended-upgrades not installed")
        issues.append(
            "Enable auto security updates: "
            "sudo apt install unattended-upgrades"
        )
        score -= 10

    # ── 4. Sudo users ─────────────────────────────────────
    console.print("\n[bold]Sudo Access[/bold]")
    stdout, _, _ = _run(["getent", "group", "sudo"])
    if stdout:
        members = stdout.split(":")[3] if len(stdout.split(":")) > 3 else ""
        if members:
            _info(f"Users with sudo: {members}")
        else:
            _ok("No non-root sudo users")
    else:
        _info("Could not read sudo group")

    # ── 5. World-writable files ───────────────────────────
    console.print("\n[bold]File System[/bold]")
    stdout, _, _ = _run(
        ["find", "/etc", "-maxdepth", "2",
         "-perm", "-o+w", "-type", "f"],
        timeout=10
    )
    if stdout:
        count = len(stdout.splitlines())
        _warn(f"{count} world-writable file(s) in /etc")
        issues.append(
            f"Fix world-writable files in /etc: "
            "find /etc -maxdepth 2 -perm -o+w -type f"
        )
        score -= 10
    else:
        _ok("No world-writable files in /etc")

    # ── 6. Empty password accounts ────────────────────────
    stdout, _, _ = _run(
        ["sudo", "awk", "-F:", "($2==\"\"){print $1}", "/etc/shadow"]
    )
    if stdout:
        _fail(f"Accounts with empty passwords: {stdout}")
        issues.append(f"Set passwords for: {stdout}")
        score -= 20
    else:
        _ok("No accounts with empty passwords")

    # ── 7. Fail2ban ───────────────────────────────────────
    console.print("\n[bold]Intrusion Prevention[/bold]")
    stdout, _, code = _run(["systemctl", "is-active", "fail2ban"])
    if "active" in stdout:
        _ok("fail2ban is running")
    else:
        _warn("fail2ban is not running")
        issues.append(
            "Install fail2ban: sudo apt install fail2ban && "
            "sudo systemctl enable --now fail2ban"
        )
        score -= 10

    # ── Score ─────────────────────────────────────────────
    score = max(0, score)
    color = "green" if score >= 80 else ("yellow" if score >= 50 else "red")
    grade = "Good" if score >= 80 else ("Needs Work" if score >= 50 else "Critical")

    console.print()
    console.print(Panel(
        f"[bold {color}]Security Score: {score}/100 — {grade}[/bold {color}]\n\n"
        + (
            "\n".join(f"  [yellow]▸[/yellow] {i}" for i in issues)
            if issues else
            "[green]  No critical issues found.[/green]"
        ),
        title="[bold red]● Audit Summary[/bold red]",
        border_style=color,
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()


# ── oma security ports ────────────────────────────────────
@plugin_group.command("ports")
def security_ports():
    """Audit open ports and flag risky ones."""
    RISKY_PORTS = {
        21:   ("FTP",      "red",    "Unencrypted file transfer — use SFTP"),
        23:   ("Telnet",   "red",    "Unencrypted remote access — use SSH"),
        25:   ("SMTP",     "yellow", "Mail server — ensure it is not an open relay"),
        80:   ("HTTP",     "yellow", "Unencrypted web — consider HTTPS"),
        110:  ("POP3",     "yellow", "Unencrypted mail — use POP3S"),
        143:  ("IMAP",     "yellow", "Unencrypted mail — use IMAPS"),
        445:  ("SMB",      "red",    "Windows file sharing — high attack surface"),
        3306: ("MySQL",    "yellow", "Database exposed — should not be public"),
        5432: ("Postgres", "yellow", "Database exposed — should not be public"),
        6379: ("Redis",    "red",    "Redis often has no auth — never expose publicly"),
        27017:("MongoDB",  "red",    "MongoDB — ensure auth is enabled"),
    }

    stdout, _, _ = _run(["ss", "-tulnp"])

    t = Table(
        box=box.ROUNDED, border_style="red",
        title="[bold red]● Security Port Audit[/bold red]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Port",    style="white", width=8)
    t.add_column("Service", style="cyan",  width=12)
    t.add_column("Risk",    width=10)
    t.add_column("Advice",  style="dim",   width=50)

    found = False
    for line in stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        local = parts[4]
        try:
            port_num = int(local.split(":")[-1])
        except ValueError:
            continue

        if port_num in RISKY_PORTS:
            service, color, advice = RISKY_PORTS[port_num]
            t.add_row(
                str(port_num),
                service,
                f"[{color}]{'HIGH' if color == 'red' else 'MEDIUM'}[/{color}]",
                advice,
            )
            found = True

    if not found:
        console.print("\n[green]✓ No high-risk ports detected.[/green]\n")
        return

    console.print()
    console.print(t)
    console.print(
        "[dim]  Run [/dim][cyan]oma security explain[/cyan]"
        "[dim] to understand any of these risks.[/dim]\n"
    )


# ── oma security ssh ──────────────────────────────────────
@plugin_group.command()
def ssh():
    """Audit SSH configuration and show hardening tips."""
    console.print()
    console.print("[bold]● SSH Security Audit[/bold]\n")

    sshd = "/etc/ssh/sshd_config"
    checks = [
        ("PermitRootLogin",        "no",  "Root login disabled"),
        ("PasswordAuthentication", "no",  "Password auth disabled (keys only)"),
        ("X11Forwarding",          "no",  "X11 forwarding disabled"),
        ("MaxAuthTries",           "3",   "Max auth tries set low"),
        ("Protocol",               "2",   "Using SSH protocol 2"),
        ("PermitEmptyPasswords",   "no",  "Empty passwords blocked"),
    ]

    hardening = []
    for key, good_val, label in checks:
        stdout, _, _ = _run(["grep", "-i", f"^{key}", sshd])
        val = stdout.split()[-1].lower() if stdout else None

        if val == good_val.lower():
            _ok(label)
        else:
            current = f"(currently: {val})" if val else "(not set)"
            _warn(f"{label} {current}")
            hardening.append(f"Set {key} {good_val} in {sshd}")

    if hardening:
        console.print()
        console.print("[bold yellow]Hardening Steps:[/bold yellow]")
        for step in hardening:
            console.print(f"  [yellow]▸[/yellow] {step}")
        console.print(
            "\n[dim]  Apply changes: sudo systemctl restart sshd[/dim]"
        )
    else:
        console.print("\n[green]✓ SSH is well configured.[/green]")
    console.print()


# ── oma security firewall ─────────────────────────────────
@plugin_group.command()
def firewall():
    """Show UFW firewall rules and status."""
    stdout, stderr, code = _run(["sudo", "ufw", "status", "verbose"])

    if code != 0 or "inactive" in stdout.lower():
        console.print()
        console.print(Panel(
            "[red]✗  UFW firewall is INACTIVE[/red]\n\n"
            "  Your system has no active firewall.\n\n"
            "  Enable it:\n"
            "  [cyan]sudo ufw allow ssh[/cyan]\n"
            "  [cyan]sudo ufw enable[/cyan]",
            title="[bold red]● Firewall Status[/bold red]",
            border_style="red", box=box.ROUNDED, padding=(1, 2),
        ))
        console.print()
        return

    console.print()
    console.print(Panel(
        stdout,
        title="[bold green]● UFW Firewall Rules[/bold green]",
        border_style="green", box=box.ROUNDED, padding=(0, 1),
    ))
    console.print()


# ── oma security users ────────────────────────────────────
@plugin_group.command()
def users():
    """List system users, sudo access, and login status."""
    console.print()

    t = Table(
        box=box.ROUNDED, border_style="cyan",
        title="[bold cyan]● System Users[/bold cyan]",
        show_header=True, header_style="bold cyan", padding=(0, 1),
    )
    t.add_column("Username",  style="white", width=18)
    t.add_column("UID",       style="dim",   width=7)
    t.add_column("Shell",     style="cyan",  width=20)
    t.add_column("Sudo",      width=8)
    t.add_column("Home",      style="dim",   width=24)

    # Get sudo group members
    sudo_out, _, _ = _run(["getent", "group", "sudo"])
    sudo_members = []
    if sudo_out:
        parts = sudo_out.split(":")
        if len(parts) > 3:
            sudo_members = parts[3].split(",")

    # Read /etc/passwd for real users (UID >= 1000)
    passwd_out, _, _ = _run(["getent", "passwd"])
    for line in passwd_out.splitlines():
        parts = line.split(":")
        if len(parts) < 7:
            continue
        username = parts[0]
        uid      = int(parts[2])
        home     = parts[5]
        shell    = parts[6]

        # Only show human users and root
        if uid < 1000 and uid != 0:
            continue
        if shell in ("/usr/sbin/nologin", "/bin/false", "/sbin/nologin"):
            continue

        is_sudo = username in sudo_members or uid == 0
        sudo_badge = "[red]YES[/red]" if is_sudo else "[dim]no[/dim]"

        t.add_row(username, str(uid), shell, sudo_badge, home)

    console.print(t)

    # Last logins
    console.print()
    stdout, _, _ = _run(["last", "-n", "5"])
    if stdout:
        console.print(Panel(
            stdout,
            title="[bold]● Last 5 Logins[/bold]",
            border_style="dim", box=box.ROUNDED, padding=(0, 1),
        ))
    console.print()


# ── oma security explain ──────────────────────────────────
@plugin_group.command()
@click.argument("query", nargs=-1)
def explain(query):
    """Ask OmaAI to explain a security concept or vulnerability."""
    from oma.ai.engine import get_engine
    from oma.ai.prompts import EXPLAIN_SYSTEM

    text = " ".join(query)
    if not text:
        console.print("[red]❌  Provide a security question.[/red]")
        console.print(
            '[dim]Example: oma security explain '
            '"what is fail2ban and how does it work"[/dim]\n'
        )
        return

    with console.status(
        "[bold red]OmaAI is analyzing...[/bold red]", spinner="dots"
    ):
        engine   = get_engine()
        response = engine.complete(
            system=EXPLAIN_SYSTEM,
            user=f"Linux security question: {text}"
        )

    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold red]● OmaAI -- Security Explain[/bold red]",
        border_style="red", box=box.ROUNDED, padding=(1, 2),
    ))
    console.print()
