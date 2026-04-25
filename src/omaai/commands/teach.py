"""oma teach - Interactive Linux lessons and quizzes"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

PROGRESS_FILE = Path.home() / ".omaai" / "progress.json"

LESSONS = {
    "1": {
        "title": "Navigating the Filesystem",
        "questions": [
            {"q": "What command shows your current directory?", "a": "pwd"},
            {"q": "What command lists files in a directory?", "a": "ls"},
            {"q": "What command changes your directory?", "a": "cd"},
            {"q": "What command goes up one directory level?", "a": "cd .."},
        ],
    },
    "2": {
        "title": "Working with Files",
        "questions": [
            {"q": "What command creates an empty file?", "a": "touch"},
            {"q": "What command copies a file?", "a": "cp"},
            {"q": "What command moves or renames a file?", "a": "mv"},
            {"q": "What command deletes a file?", "a": "rm"},
        ],
    },
    "3": {
        "title": "Viewing File Contents",
        "questions": [
            {"q": "What command shows the contents of a file?", "a": "cat"},
            {"q": "What command shows the first 10 lines of a file?", "a": "head"},
            {"q": "What command shows the last 10 lines of a file?", "a": "tail"},
            {"q": "What command lets you scroll through a file?", "a": "less"},
        ],
    },
    "4": {
        "title": "Permissions",
        "questions": [
            {"q": "What command changes file permissions?", "a": "chmod"},
            {"q": "What command changes file ownership?", "a": "chown"},
            {"q": "What permission number means read+write+execute for owner?", "a": "700"},
            {"q": "What permission number makes a file executable by everyone?", "a": "755"},
        ],
    },
    "5": {
        "title": "Processes",
        "questions": [
            {"q": "What command shows running processes?", "a": "ps"},
            {"q": "What command shows live process activity?", "a": "top"},
            {"q": "What command kills a process by PID?", "a": "kill"},
            {"q": "What command finds a process by name?", "a": "pgrep"},
        ],
    },
}


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text())
        except Exception:
            pass
    return {"completed": [], "score": 0, "total_questions": 0}


def save_progress(progress: dict):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def show_lessons():
    progress = load_progress()
    console.print("\n[bold cyan]📚 OmaAI Linux Lessons[/bold cyan]\n")
    for num, lesson in LESSONS.items():
        done = num in progress.get("completed", [])
        status = "[green]✅[/green]" if done else "  "
        console.print(f"  {status} Lesson {num}: [bold]{lesson['title']}[/bold]")
    console.print()


def run_lesson(lesson_num: str):
    if lesson_num not in LESSONS:
        console.print(f"[red]Lesson {lesson_num} not found. Choose 1–{len(LESSONS)}[/red]")
        return

    lesson = LESSONS[lesson_num]
    progress = load_progress()

    console.print(Panel.fit(
        f"[bold cyan]Lesson {lesson_num}: {lesson['title']}[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    correct = 0
    total = len(lesson["questions"])

    for i, item in enumerate(lesson["questions"], 1):
        console.print(f"[bold]Q{i}:[/bold] {item['q']}")
        answer = Prompt.ask("  Your answer").strip().lower()
        expected = item["a"].lower()

        if answer == expected:
            console.print("  [green]✅ Correct![/green]\n")
            correct += 1
        else:
            console.print(f"  [red]❌ Answer: {item['a']}[/red]\n")

    # Update progress
    progress["score"] = progress.get("score", 0) + correct
    progress["total_questions"] = progress.get("total_questions", 0) + total
    if correct == total and lesson_num not in progress.get("completed", []):
        progress.setdefault("completed", []).append(lesson_num)
        console.print("[bold green]🎉 Lesson complete! Perfect score![/bold green]")
    else:
        console.print(f"[bold yellow]Score: {correct}/{total}[/bold yellow]")

    save_progress(progress)
    console.print()


@click.command()
@click.option("--lesson", "-l", default=None, help="Lesson number to start (1-5)")
@click.option("--progress", "-p", "show_prog", is_flag=True, help="Show your progress")
def teach(lesson, show_prog):
    """Interactive Linux lessons and quizzes."""
    if show_prog:
        progress = load_progress()
        completed = progress.get("completed", [])
        score = progress.get("score", 0)
        total = progress.get("total_questions", 0)
        console.print(f"\n[bold cyan]📈 Your Progress[/bold cyan]")
        console.print(f"  Lessons completed: [green]{len(completed)}/{len(LESSONS)}[/green]")
        if total > 0:
            pct = score / total * 100
            console.print(f"  Score: [green]{score}/{total} ({pct:.0f}%)[/green]")
        console.print()
        return

    if lesson:
        run_lesson(lesson)
    else:
        show_lessons()
        choice = Prompt.ask("Enter lesson number", default="1")
        run_lesson(choice)
