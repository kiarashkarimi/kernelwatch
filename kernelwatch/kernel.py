import os
from typing import List, Tuple

from .utils import run_command


def get_running_kernel() -> str:
    ok, out = run_command(["uname", "-r"])
    return out if ok else "unknown"


def get_installed_kernels() -> List[str]:
    """Detect installed Linux kernels via pacman query."""
    kernels: List[str] = []

    ok, out = run_command(["pacman", "-Q", "linux"])
    if ok:
        kernels.append(out)

    # try common Arch kernels
    candidates = ["linux-lts", "linux-zen", "linux-hardened"]
    for pkg in candidates:
        ok, out = run_command(["pacman", "-Q", pkg])
        if ok:
            kernels.append(out)

    return kernels


def get_kernel_modules_count() -> Tuple[bool, int]:
    ok, out = run_command(["lsmod"])
    if not ok:
        return False, 0

    # first line is header
    lines = out.splitlines()
    return True, max(0, len(lines) - 1)


def check_dkms_status() -> Tuple[bool, str]:
    return run_command(["dkms", "status"])


def check_kernel_taint() -> Tuple[bool, str]:
    """Reads kernel taint flag."""
    path = "/proc/sys/kernel/tainted"
    try:
        with open(path, "r") as f:
            value = f.read().strip()
        return True, value
    except Exception:
        return False, "unavailable"
