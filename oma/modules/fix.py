"""
OmaAI — Fix Module
Usage:
  oma fix script.sh
  oma fix script.sh --save fixed.sh
  oma fix script.sh --execute
  cat broken.sh | oma fix --stdin
"""

import re
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich import box

from oma.ai.engine import get_engine
from oma.ai.prompts import FIX_SYSTEM
from oma.config import load_config

console = Console()


def run_fix(content: str, filename: str = "script",
            execute: bool = False, save_path: str = None):

    if not content.strip():
        console.print("[red]❌  Empty input. Nothing to fix.[/red]")
        return

    cfg         = load_config()
    user_prompt = (
        f"Fix this script (filename: {filename}):\n\n"
        f"```\n{content}\n```"
    )

    with console.status(
        "[bold yellow]OmaAI is reading your script...[/bold yellow]",
        spinner="dots"
    ):
        engine   = get_engine()
        response = engine.complete(system=FIX_SYSTEM, user=user_prompt)

    console.print()
    console.print(Panel(
        Markdown(response),
        title=f"[bold yellow]● OmaAI — Fix: {filename}[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()

    fixed_code = _extract_code_block(response)

    if fixed_code:
        if save_path:
            Path(save_path).write_text(fixed_code)
            console.print(f"[green]✓ Fixed script saved → {save_path}[/green]\n")

        if execute:
            if cfg.get("safe_mode", True):
                confirmed = Confirm.ask(
                    "[yellow]⚠  safe_mode is ON — execute this fixed script?[/yellow]"
                )
                if not confirmed:
                    console.print("[dim]Execution cancelled.[/dim]\n")
                    return
            _run_script(fixed_code, filename)
    else:
        console.print(
            "[dim]Tip: use --save <file> to write the fixed script to disk.[/dim]\n"
        )


def _extract_code_block(text: str) -> str:
    """Pull the first fenced code block from the LLM response."""
    match = re.search(r"```(?:bash|sh|python|py)?\n([\s\S]*?)```", text)
    return match.group(1).strip() if match else ""


def _run_script(code: str, filename: str):
    import subprocess, tempfile, os

    is_python = "import " in code or "def " in code or "print(" in code
    suffix    = ".py" if is_python else ".sh"
    interp    = "python3" if is_python else "bash"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, prefix="omaai_"
    ) as f:
        f.write(code)
        tmp = f.name

    os.chmod(tmp, 0o700)
    console.print(f"[cyan]▸ Running: {interp} {tmp}[/cyan]\n")
    result = subprocess.run([interp, tmp])
    os.unlink(tmp)

    if result.returncode == 0:
        console.print("\n[green]✓ Script completed successfully.[/green]\n")
    else:
        console.print(f"\n[red]✗ Exited with code {result.returncode}[/red]\n")
