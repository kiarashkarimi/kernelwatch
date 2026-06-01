import typer

from .doctor import doctor
from . import version

app = typer.Typer(help="kernelwatch - Arch Linux system health diagnostics")

@app.command(name="doctor")

def doctor_cmd():
    """Run full system diagnostics."""
    doctor()

@app.command(name="version")

def version_cmd():
    """Show kernelwatch version."""
    print(f"kernelwatch {version}")

if __name__ == "__main__":
    app()