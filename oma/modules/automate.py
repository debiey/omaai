"""
OmaAI -- Automate Module
Usage:
  oma automate "backup my home folder every day at 2am"
  oma automate "check disk usage every hour and alert if above 90%"
  oma automate list
  oma automate remove <id>
  oma automate run <id>
  oma automate logs <id>
"""

import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich import box

from oma.ai.engine import get_engine
from oma.ai.prompts import AUTOMATE_SYSTEM

console = Console()

# Where automations are stored
AUTOMATIONS_DIR = Path.home() / ".omaai" / "automations"
REGISTRY_FILE   = AUTOMATIONS_DIR / "registry.json"


# ── Storage helpers ───────────────────────────────────────

def _ensure_dirs():
    AUTOMATIONS_DIR.mkdir(parents=True, exist_ok=True)
    log_dir = Path("/var/log/omaai")
    if not log_dir.exists():
        try:
            subprocess.run(
                ["sudo", "mkdir", "-p", str(log_dir)], check=False
            )
            subprocess.run(
                ["sudo", "chmod", "777", str(log_dir)], check=False
            )
        except Exception:
            pass


def _load_registry() -> list:
    if not REGISTRY_FILE.exists():
        return []
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def _save_registry(registry: list):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def _next_id(registry: list) -> int:
    if not registry:
        return 1
    return max(a["id"] for a in registry) + 1


# ── Cron helpers ──────────────────────────────────────────

def _add_cron(script_path: str, schedule: str) -> bool:
    """Add a cron job for the given script."""
    cron_line = f"{schedule} /bin/bash {script_path} >> /var/log/omaai/cron.log 2>&1"
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True, text=True
    )
    existing = result.stdout if result.returncode == 0 else ""

    if cron_line in existing:
        return True  # already registered

    new_cron = existing.rstrip() + f"\n{cron_line}\n"
    proc = subprocess.run(
        ["crontab", "-"],
        input=new_cron, capture_output=True, text=True
    )
    return proc.returncode == 0


def _remove_cron(script_path: str) -> bool:
    """Remove a cron job by script path."""
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return True

    lines = [
        line for line in result.stdout.splitlines()
        if script_path not in line
    ]
    new_cron = "\n".join(lines) + "\n"
    proc = subprocess.run(
        ["crontab", "-"],
        input=new_cron, capture_output=True, text=True
    )
    return proc.returncode == 0


def _extract_script(text: str) -> str:
    """Pull bash script from LLM response."""
    match = re.search(r"```(?:bash|sh)?\n([\s\S]*?)```", text)
    return match.group(1).strip() if match else ""


def _extract_cron(text: str) -> str:
    """Pull cron expression from LLM response."""
    # Match standard 5-field cron expression
    match = re.search(
        r"(\*|[0-9,\-\*/]+)\s+"
        r"(\*|[0-9,\-\*/]+)\s+"
        r"(\*|[0-9,\-\*/]+)\s+"
        r"(\*|[0-9,\-\*/]+)\s+"
        r"(\*|[0-9,\-\*/]+)",
        text
    )
    return match.group(0).strip() if match else "0 2 * * *"


# ── Public API ────────────────────────────────────────────

def run_automate(task: str):
    """Generate and schedule a new automation."""
    _ensure_dirs()

    if not task.strip():
        console.print("[red]Describe the task to automate.[/red]")
        console.print(
            '[dim]Example: oma automate '
            '"backup my home folder every day at 2am"[/dim]\n'
        )
        return

    with console.status(
        "[bold green]OmaAI is generating your automation...[/bold green]",
        spinner="dots",
    ):
        engine   = get_engine()
        response = engine.complete(system=AUTOMATE_SYSTEM, user=task)

    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold green]● OmaAI -- Automation Plan[/bold green]",
        border_style="green", box=box.ROUNDED, padding=(1, 2),
    ))

    # Extract script and cron from response
    script_code = _extract_script(response)
    cron_expr   = _extract_cron(response)

    if not script_code:
        console.print(
            "[yellow]⚠  Could not extract script. "
            "Try rephrasing your task.[/yellow]\n"
        )
        return

    console.print(
        f"[dim]  Detected cron schedule: [/dim]"
        f"[cyan]{cron_expr}[/cyan]\n"
    )

    # Ask user to confirm
    if not Confirm.ask("[green]Save and schedule this automation?[/green]"):
        console.print("[dim]Cancelled.[/dim]\n")
        return

    # Allow user to override cron schedule
    custom = Prompt.ask(
        "[dim]Cron schedule (press Enter to keep detected)[/dim]",
        default=cron_expr,
    )
    if custom.strip():
        cron_expr = custom.strip()

    # Save the script
    registry   = _load_registry()
    auto_id    = _next_id(registry)
    safe_name  = re.sub(r"[^a-z0-9]", "_", task.lower())[:40]
    script_name = f"omaai_{auto_id:03d}_{safe_name}.sh"
    script_path = AUTOMATIONS_DIR / script_name

    script_path.write_text(script_code)
    script_path.chmod(0o700)

    # Register cron
    cron_ok = _add_cron(str(script_path), cron_expr)

    # Save to registry
    registry.append({
        "id":          auto_id,
        "task":        task,
        "script":      str(script_path),
        "schedule":    cron_expr,
        "created":     datetime.now().isoformat(),
        "cron_active": cron_ok,
    })
    _save_registry(registry)

    console.print()
    console.print(Panel(
        f"[green]✓ Automation #{auto_id} created[/green]\n\n"
        f"[dim]Script:[/dim]   {script_path}\n"
        f"[dim]Schedule:[/dim] [cyan]{cron_expr}[/cyan]\n"
        f"[dim]Cron:[/dim]     "
        + ("[green]registered[/green]" if cron_ok else "[yellow]manual setup needed[/yellow]")
        + f"\n\n[dim]Run now:  [/dim][cyan]oma automate run {auto_id}[/cyan]\n"
        f"[dim]View logs: [/dim][cyan]oma automate logs {auto_id}[/cyan]",
        title="[bold green]● Automation Saved[/bold green]",
        border_style="green", box=box.ROUNDED, padding=(1, 2),
    ))
    console.print()


def run_automate_list():
    """Show all registered automations."""
    registry = _load_registry()

    if not registry:
        console.print("\n[dim]  No automations yet.[/dim]")
        console.print(
            '[dim]  Run: oma automate "backup home folder daily"[/dim]\n'
        )
        return

    t = Table(
        box=box.ROUNDED, border_style="green",
        title="[bold green]● OmaAI Automations[/bold green]",
        show_header=True, header_style="bold green", padding=(0, 1),
    )
    t.add_column("ID",       style="dim",   width=5)
    t.add_column("Task",     style="white", width=38)
    t.add_column("Schedule", style="cyan",  width=16)
    t.add_column("Cron",     width=10)
    t.add_column("Created",  style="dim",   width=12)

    for a in registry:
        cron_status = (
            "[green]active[/green]"
            if a.get("cron_active") else
            "[yellow]manual[/yellow]"
        )
        created = a.get("created", "")[:10]
        t.add_row(
            str(a["id"]),
            a["task"][:38],
            a["schedule"],
            cron_status,
            created,
        )

    console.print()
    console.print(t)
    console.print(
        "[dim]  oma automate run <id>    — run now[/dim]\n"
        "[dim]  oma automate logs <id>   — view logs[/dim]\n"
        "[dim]  oma automate remove <id> — delete[/dim]\n"
    )


def run_automate_remove(auto_id: int):
    """Remove an automation by ID."""
    registry = _load_registry()
    target   = next((a for a in registry if a["id"] == auto_id), None)

    if not target:
        console.print(f"[red]❌  Automation #{auto_id} not found.[/red]\n")
        return

    # Remove cron
    _remove_cron(target["script"])

    # Remove script file
    script = Path(target["script"])
    if script.exists():
        script.unlink()

    # Remove from registry
    registry = [a for a in registry if a["id"] != auto_id]
    _save_registry(registry)

    console.print(
        f"[green]✓ Automation #{auto_id} removed.[/green]  "
        f"[dim]{target['task']}[/dim]\n"
    )


def run_automate_run(auto_id: int):
    """Run an automation immediately."""
    registry = _load_registry()
    target   = next((a for a in registry if a["id"] == auto_id), None)

    if not target:
        console.print(f"[red]❌  Automation #{auto_id} not found.[/red]\n")
        return

    script = target["script"]
    console.print(f"\n[cyan]▸ Running automation #{auto_id}: {target['task']}[/cyan]\n")
    result = subprocess.run(["bash", script])

    if result.returncode == 0:
        console.print("\n[green]✓ Completed successfully.[/green]\n")
    else:
        console.print(
            f"\n[red]✗ Exited with code {result.returncode}[/red]\n"
            f"[dim]  Check logs: oma automate logs {auto_id}[/dim]\n"
        )


def run_automate_logs(auto_id: int):
    """Show logs for an automation."""
    registry = _load_registry()
    target   = next((a for a in registry if a["id"] == auto_id), None)

    if not target:
        console.print(f"[red]❌  Automation #{auto_id} not found.[/red]\n")
        return

    # Check all log files in /var/log/omaai/
    log_dir = Path("/var/log/omaai")
    if not log_dir.exists():
        console.print("[dim]  No log directory found.[/dim]\n")
        return

    # Find any log file — get the most recently modified
    log_files = sorted(
        log_dir.glob("*.log"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    if not log_files:
        console.print(
            f"[dim]  No logs yet for automation #{auto_id}.[/dim]\n"
            f"[dim]  Run it first: oma automate --run {auto_id}[/dim]\n"
        )
        return

    # Show the most recent log
    log_file = log_files[0]
    result   = subprocess.run(
        ["tail", "-50", str(log_file)],
        capture_output=True, text=True
    )
    output = result.stdout.strip()

    if not output:
        console.print(f"[dim]  Log file is empty: {log_file}[/dim]\n")
        return

    console.print(Panel(
        output,
        title=f"[bold green]● Logs: {target['task'][:40]}[/bold green]  [dim]({log_file})[/dim]",
        border_style="green", box=box.ROUNDED, padding=(0, 1),
    ))
    console.print()

def _run_cmd(cmd: list) -> tuple:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode
