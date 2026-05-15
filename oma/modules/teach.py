"""
OmaAI — Teach Module
Usage:
  oma teach                        List all topics
  oma teach "linux file permissions"
  oma teach "bash scripting" --level beginner
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import box

from oma.ai.engine import get_engine
from oma.ai.prompts import TEACH_SYSTEM

console = Console()

TOPICS = {
    "linux-basics":       {"title": "Linux Basics",          "desc": "Filesystem navigation, core commands",       "level": "beginner"},
    "file-permissions":   {"title": "File Permissions",       "desc": "chmod, chown, umask, SUID, SGID",            "level": "beginner"},
    "bash-scripting":     {"title": "Bash Scripting",         "desc": "Variables, loops, functions, conditionals",  "level": "intermediate"},
    "systemd":            {"title": "Systemd & Services",     "desc": "systemctl, units, journald",                 "level": "intermediate"},
    "networking":         {"title": "Linux Networking",        "desc": "ip, ss, netstat, DNS, ports, curl",          "level": "intermediate"},
    "ssh":                {"title": "SSH & Remote Access",     "desc": "Keys, config, tunnels, scp, rsync",          "level": "intermediate"},
    "cron":               {"title": "Cron & Scheduling",       "desc": "crontab syntax, at, task automation",        "level": "beginner"},
    "process-management": {"title": "Process Management",     "desc": "ps, kill, nice, jobs, htop",                 "level": "beginner"},
    "disk-management":    {"title": "Disk & Storage",          "desc": "df, du, lsblk, fdisk, mount",               "level": "intermediate"},
    "python-sysadmin":    {"title": "Python for Sysadmins",   "desc": "Automate Linux tasks with Python",           "level": "intermediate"},
    "docker-basics":      {"title": "Docker Fundamentals",    "desc": "Images, containers, volumes, networks",      "level": "intermediate"},
    "git":                {"title": "Git & Version Control",   "desc": "Commits, branches, merges, remotes",         "level": "beginner"},
    "vim":                {"title": "Vim Essentials",          "desc": "Modes, navigation, editing, config",         "level": "beginner"},
    "awk-sed":            {"title": "AWK & SED",              "desc": "Text processing power tools",                "level": "intermediate"},
    "security-basics":    {"title": "Linux Security Basics",  "desc": "UFW, fail2ban, SSH hardening",               "level": "intermediate"},
}

LEVEL_COLORS = {
    "beginner":     "green",
    "intermediate": "yellow",
    "advanced":     "red",
}


def _show_topics():
    t = Table(
        box=box.ROUNDED, border_style="cyan",
        show_header=True, header_style="bold cyan",
        title="[bold cyan]OmaAI — Lesson Library[/bold cyan]",
        padding=(0, 1),
    )
    t.add_column("Topic",       style="white", width=26)
    t.add_column("Description", style="dim",   width=42)
    t.add_column("Level",                      width=14)

    for info in TOPICS.values():
        c = LEVEL_COLORS.get(info["level"], "white")
        t.add_row(
            f"[bold]{info['title']}[/bold]",
            info["desc"],
            f"[{c}]{info['level']}[/{c}]",
        )

    console.print()
    console.print(t)
    console.print()
    console.print('[dim]  Usage:  oma teach "file permissions"[/dim]')
    console.print('[dim]         oma teach "bash scripting" --level advanced[/dim]\n')


def run_teach(topic: str, level: str = "intermediate"):
    if not topic or topic.strip().lower() in ("", "list", "topics", "help", "?"):
        _show_topics()
        return

    user_prompt = (
        f"Teach me about: {topic}\n\n"
        f"Level: {level}\n"
        "Use Ubuntu/Linux examples. Keep it practical and hands-on."
    )

    with console.status(
        f"[bold magenta]Preparing lesson: {topic}...[/bold magenta]",
        spinner="dots",
    ):
        engine = get_engine()
        lesson = engine.complete(system=TEACH_SYSTEM, user=user_prompt)

    console.print()
    console.print(Panel(
        Markdown(lesson),
        title=f"[bold magenta]● OmaAI — Lesson: {topic.title()}[/bold magenta]",
        border_style="magenta", box=box.ROUNDED, padding=(1, 2),
    ))
    c = LEVEL_COLORS.get(level, "white")
    console.print(
        f"  [dim]Level:[/dim] [{c}]{level}[/{c}]  "
        f"[dim]·  run [/dim][cyan]oma teach list[/cyan]"
        f"[dim] to see all topics[/dim]\n"
    )
