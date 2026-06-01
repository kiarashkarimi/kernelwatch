from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from collections import defaultdict
import json
import sys

from rich.table import Table

from .utils import console
from .kernel import get_running_kernel, get_installed_kernels
from .boot import check_initramfs, check_bootloader, check_boot_entries
from .pacman import check_pacman_db, check_package_integrity
from .services import check_failed_services
from .logs import get_kernel_errors

SEVERITY_WEIGHT = {
    "OK": 0,
    "INFO": 1,
    "WARN": 3,
    "CRITICAL": 6,
}

def filter_events(events, min_level=None):
    order = {
        "OK": 0,
        "INFO": 1,
        "WARN": 2,
        "CRITICAL": 3,
    }

    if not min_level:
        return events

    return [
        e for e in events
        if order[e.severity.value] >= order[min_level]
    ]

def events_to_json(events):
    return [
        {
            "section": e.section,
            "severity": e.severity.value,
            "message": e.message,
            "code": e.code,
        }
        for e in events
    ]

def compute_health_score(events):
    score = 100

    for e in events:
        score -= SEVERITY_WEIGHT[e.severity.value]

    return max(score, 0)

# ----------------------------
# Event Model
# ----------------------------

class Severity(Enum):
    OK = "OK"
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


@dataclass

class Event:

    section: str
    severity: Severity
    message: str
    code: Optional[str] = None


# ----------------------------
# Context Collector
# ----------------------------

def collect_context():
    import os
    from .kernel import get_running_kernel

    bootloader = None

    if os.path.exists("/boot/loader"):
        bootloader = "systemd-boot"
    elif os.path.exists("/boot/grub"):
        bootloader = "grub"

    return {
        "kernel": get_running_kernel(),
        "bootloader": bootloader,
    }


# ----------------------------
# Helpers
# ----------------------------

def make(section, severity, message, code=None):
    return Event(section, severity, message, code)


def ok(section, message):
    return make(section, Severity.OK, message)


def warn(section, message, code=None):
    return make(section, Severity.WARN, message, code)


def critical(section, message, code=None):
    return make(section, Severity.CRITICAL, message, code)


def info(section, message):
    return make(section, Severity.INFO, message)


# ----------------------------
# Boot Rule Layer
# ----------------------------

def evaluate_boot(init_ok: bool, msg: str, ctx):
    if init_ok:
        return ok("boot", msg)

    if ctx["bootloader"] is None:
        return critical("boot", msg)

    return warn("boot", msg)


# ----------------------------

# Log Clustering (embedded)

# ----------------------------


def cluster_logs(lines: List[str], limit: int = 5) -> List[str]:
    freq = defaultdict(int)

    for line in lines:
        parts = line.split()

        # strip timestamp if present
        cleaned = line.split("kernel:", 1)[-1] if "kernel:" in line else line
        freq[cleaned] += 1

    clustered = []

    for msg, count in sorted(freq.items(), key=lambda x: -x[1]):
        if count > 1:
            clustered.append(f"{msg} (x{count})")
        else:
            clustered.append(msg)

    return clustered[:limit]


# ----------------------------

# Core Engine

# ----------------------------

def run_diagnostics() -> List[Event]:
    results: List[Event] = []
    ctx = collect_context()

    # ---------------- Kernel ----------------
    kernel = get_running_kernel()
    results.append(ok("kernel", f"Running kernel: {kernel}"))

    installed = get_installed_kernels()
    results.append(info(
        "kernel",
        f"Installed kernels: {', '.join(installed) if installed else 'none'}"
    ))

    # ---------------- Boot ----------------
    ok_init, init_msg = check_initramfs()
    results.append(evaluate_boot(ok_init, init_msg, ctx))

    ok_boot, bootloader = check_bootloader()
    results.append(
        ok("boot", bootloader) if ok_boot else warn("boot", bootloader)
    )

    ok_entries, entries = check_boot_entries()
    results.append(
        ok("boot", entries) if ok_entries else warn("boot", entries)
    )

    # ---------------- Pacman ----------------
    ok_db, db = check_pacman_db()
    results.append(
        ok("pacman", "Database clean") if ok_db else warn("pacman", db)
    )

    ok_pkg, pkg = check_package_integrity()
    results.append(
        ok("pacman", "Package integrity OK") if ok_pkg else warn("pacman", pkg)
    )

    # ---------------- Services ----------------
    ok_svc, failed = check_failed_services()

    if ok_svc and failed:
        for s in failed:
            results.append(warn("systemd", f"Failed service: {s}"))
    else:
        results.append(ok("systemd", "No failed services"))

    # ---------------- Kernel Logs (clustered) ----------------
    ok_logs, logs = get_kernel_errors()

    if ok_logs and logs:
        clustered = cluster_logs(logs.splitlines())

        for line in clustered:
            results.append(warn("kernel-log", line))
    else:
        results.append(ok("kernel-log", "No critical kernel errors"))

    return results


# ----------------------------
# Aggregation
# ----------------------------

def summarize(events: List[Event]):
    summary = {s.value: 0 for s in Severity}

    for event in events:
        summary[event.severity.value] += 1

    summary["HEALTH_SCORE"] = compute_health_score(events)

    return summary


def overall_status(summary):
    if summary["CRITICAL"] > 0:
        return "CRITICAL"
    if summary["WARN"] > 0:
        return "WARN"
    return "OK"


# ----------------------------

# Renderer

# ----------------------------

def render(events: List[Event]):

    table = Table(title="kernelwatch diagnostic report")


    table.add_column("Section", style="cyan")
    table.add_column("Severity")
    table.add_column("Message")

    color_map = {
        "OK": "green",
        "INFO": "blue",
        "WARN": "yellow",
        "CRITICAL": "red",
    }

    for e in events:
        color = color_map[e.severity.value]

        table.add_row(
            e.section,
            f"[{color}]{e.severity.value}[/{color}]",
            e.message,
        )

    console.print(table)


# ----------------------------

# Entry Point

# ----------------------------

def doctor(output: str = "table", min_level: str | None = None):
    events = run_diagnostics()

    # -----------------------------
    # Optional severity filtering
    # -----------------------------
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

    # -----------------------------
    # Summary + score
    # -----------------------------
    summary = summarize(events)
    score = summary["HEALTH_SCORE"]

    # -----------------------------
    # JSON output mode
    # -----------------------------
    if output == "json":
        import json

        print(json.dumps({
            "summary": summary,
            "health_score": score,
            "status": overall_status(summary),
            "events": [
                {
                    "section": e.section,
                    "severity": e.severity.value,
                    "message": e.message,
                    "code": e.code,
                }
                for e in events
            ],
        }, indent=2))
        return

    # -----------------------------
    # Human-readable output
    # -----------------------------
    render(events)

    console.print("\n[bold]Summary:[/bold]")
    console.print(summary)

    console.print(f"[bold]Health Score:[/bold] {score}/100")
    console.print(f"[bold]Overall Status:[/bold] {overall_status(summary)}")


# ----------------------------