# kernelwatch/utils.py

import subprocess
from rich.console import Console
from typing import Tuple, Optional, Sequence

console = Console()


def run_command(command: Sequence[str]) -> Tuple[bool, str]:
    """Execute a system command safely.

    Returns:
        (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return True, result.stdout.strip()

        # Prefer stderr but fallback to stdout
        err = result.stderr.strip() or result.stdout.strip()
        return False, err

    except FileNotFoundError:
        return False, "Command not found: " + " ".join(command)
    except Exception as e:
        return False, str(e)


def status_label(ok: bool) -> str:
    """Return colored status label for CLI output."""
    return "[green]OK[/green]" if ok else "[red]FAIL[/red]"


def warning_label() -> str:
    return "[yellow]WARN[/yellow]"


def section(title: str) -> None:
    """Print a visual section separator."""
    console.rule("[bold cyan]" + title + "[/bold cyan]")


def safe_read(path: str) -> Optional[str]:
    """Safely read a file from disk.

    Returns:
        str | None
    """
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None
