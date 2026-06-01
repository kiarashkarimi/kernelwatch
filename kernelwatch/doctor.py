from dataclasses import dataclass
from enum import Enum
from typing import List

from rich.table import Table

from .utils import console
from .kernel import get_running_kernel, get_installed_kernels
from .boot import check_initramfs, check_bootloader, check_boot_entries
from .pacman import check_pacman_db, check_package_integrity
from .services import check_failed_services
from .logs import get_kernel_errors

# ----------------------------

# Severity Model

# ----------------------------

class Severity(Enum):
    OK = "OK"
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"

@dataclass
class Diagnostic:
    section: str
    message: str
    severity: Severity

# ----------------------------

# Rule Engine Helpers

# ----------------------------

def make(section: str, message: str, severity: Severity):
    return Diagnostic(section, message, severity)

def ok(section: str, message: str):
    return make(section, message, Severity.OK)

def warn(section: str, message: str):
    return make(section, message, Severity.WARN)

def critical(section: str, message: str):
    return make(section, message, Severity.CRITICAL)

def info(section: str, message: str):
    return make(section, message, Severity.INFO)

# ----------------------------

# Core Engine

# ----------------------------

def run_diagnostics() -> List[Diagnostic]:
    results: List[Diagnostic] = []

    # ---------------- Kernel ----------------
    kernel = get_running_kernel()
    results.append(ok("kernel", f"Running kernel: {kernel}"))

    installed = get_installed_kernels()
    results.append(info("kernel", f"Installed kernels: {', '.join(installed) if installed else 'none'}"))

    # ---------------- Boot ----------------

    ok_init, initramfs_msg = check_initramfs()

    if ok_init:
        results.append(ok("boot", initramfs_msg))
    else:
        # downgrade to WARN unless system is clearly broken
        ok_boot, _ = check_bootloader()
        ok_entries, _ = check_boot_entries()

        if ok_boot or ok_entries:
            results.append(warn("boot", initramfs_msg))
        else:
            results.append(critical("boot", initramfs_msg))

    ok_boot, bootloader = check_bootloader()
    if ok_boot:
        results.append(ok("boot", bootloader))
    else:
        results.append(warn("boot", bootloader))

    ok_entries, entries = check_boot_entries()
    if ok_entries:
        results.append(ok("boot", entries))
    else:
        results.append(warn("boot", entries))

    # ---------------- Pacman ----------------
    ok_db, db = check_pacman_db()
    if ok_db:
        results.append(ok("pacman", "Database clean"))
    else:
        results.append(warn("pacman", db))

    ok_pkg, pkg = check_package_integrity()
    if ok_pkg:
        results.append(ok("pacman", "Package integrity OK"))
    else:
        results.append(warn("pacman", pkg))

    # ---------------- Services ----------------
    ok_svc, failed = check_failed_services()

    if ok_svc and failed:
        for s in failed:
            results.append(warn("systemd", f"Failed service: {s}"))
    else:
        results.append(ok("systemd", "No failed services"))

    # ---------------- Kernel Logs ----------------
    ok_logs, logs = get_kernel_errors()

    if ok_logs and logs:
        lines = logs.splitlines()[:5]
        for line in lines:
            results.append(warn("kernel-log", line))
    else:
        results.append(ok("kernel-log", "No critical kernel errors"))

    return results


# ----------------------------

# Severity Aggregation

# ----------------------------

def summarize(results: List[Diagnostic]):
    summary = {
        "OK": 0,
        "INFO": 0,
        "WARN": 0,
        "CRITICAL": 0,
    }


    for r in results:
        summary[r.severity.value] += 1

    return summary


def overall_status(summary):
    if summary["CRITICAL"] > 0:
        return "CRITICAL"
    if summary["WARN"] > 0:
        return "WARN"
    return "OK"

# ----------------------------

# Renderer (CLI output)

# ----------------------------

def render(results: List[Diagnostic]):
    table = Table(title="kernelwatch diagnostic report")


    table.add_column("Section", style="cyan")
    table.add_column("Severity")
    table.add_column("Message")

    for r in results:
        color = {
            "OK": "green",
            "INFO": "blue",
            "WARN": "yellow",
            "CRITICAL": "red",
        }[r.severity.value]

        table.add_row(
            r.section,
            f"[{color}]{r.severity.value}[/{color}]",
            r.message,
        )

    console.print(table)


# ----------------------------

# Entry Point

# ----------------------------

def doctor():
    results = run_diagnostics()
    summary = summarize(results)


    render(results)

    console.print("\n[bold]Summary:[/bold]")
    console.print(summary)
    console.print(f"[bold]Overall status:[/bold] {overall_status(summary)}")

