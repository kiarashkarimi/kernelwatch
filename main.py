import typer

from kernelwatch.doctor import run_diagnostics, summarize, overall_status, render, Severity
from kernelwatch.doctor import cluster_logs, collect_context
from kernelwatch.doctor import Event  # if needed elsewhere

app = typer.Typer(help="kernelwatch - Arch Linux system health diagnostics")


# ----------------------------
# Doctor Command
# ----------------------------

@app.command()
def doctor(
    json: bool = typer.Option(False, "--json", help="Output JSON format"),
    quiet: bool = typer.Option(False, "--quiet", help="Show only WARN and CRITICAL"),
    only: str = typer.Option(None, "--only", help="Filter by severity (OK/INFO/WARN/CRITICAL)")
):
    events = run_diagnostics()
    summary = summarize(events)

    # ---------------- Filtering ----------------
    if quiet:
        min_level = "WARN"
    else:
        min_level = only

    if min_level:
        order = {
            "OK": 0,
            "INFO": 1,
            "WARN": 2,
            "CRITICAL": 3,
        }

        events = [
            e for e in events
            if order[e.severity.value] >= order[min_level]
        ]

        summary = summarize(events)

    # ---------------- JSON Output ----------------
    if json:
        import json as pyjson

        print(pyjson.dumps({
            "summary": summary,
            "status": overall_status(summary),
            "events": [
                {
                    "section": e.section,
                    "severity": e.severity.value,
                    "message": e.message,
                    "code": e.code,
                }
                for e in events
            ]
        }, indent=2))
        return

    # ---------------- Table Output ----------------
    render(events)

    typer.echo("\nSummary:")
    typer.echo(summary)
    typer.echo(f"Overall status: {overall_status(summary)}")


# ----------------------------
# Version Command
# ----------------------------

@app.command()
def version():
    typer.echo("kernelwatch 0.3.0")


# ----------------------------
# Entry Point
# ----------------------------

def main():
    app()


if __name__ == "__main__":
    main()