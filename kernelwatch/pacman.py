from typing import Tuple, List

from .utils import run_command

def check_pacman_db() -> Tuple[bool, str]:
    """
    Verify pacman database consistency.
    """
    return run_command(["pacman", "-Dk"])

def check_package_integrity() -> Tuple[bool, str]:
    """
    Verify installed package file integrity.
    WARNING: can be slow on large systems.
    """
    return run_command(["pacman", "-Qk"])

def list_orphan_packages() -> Tuple[bool, List[str]]:
    """
    Returns orphan packages (unrequired dependencies).
    """
    ok, out = run_command(["pacman", "-Qtdq"])

    if not ok or not out:
        return False, []

    return True, out.splitlines()

def check_sync_db() -> Tuple[bool, str]:
    """
    Check for sync database issues.
    """
    return run_command(["pacman", "-Dk"])
