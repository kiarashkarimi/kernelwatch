from typing import Tuple, List

from .utils import run_command

def get_kernel_errors() -> Tuple[bool, List[str]]:
    """
    Extract critical kernel logs (errors only).
    """
    return run_command(["journalctl", "-k", "-p", "3", "-b", "--no-pager"])

def get_recent_warnings(limit: int = 20) -> Tuple[bool, List[str]]:

    return run_command(["journalctl", "-p", "4", "-b", "--no-pager", "-n", str(limit)])

def journal_disk_usage() -> Tuple[bool, str]:
    """
    Check journal disk usage.
    """
    return run_command(["journalctl", "--disk-usage"])
