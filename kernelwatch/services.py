from typing import Tuple, List

from .utils import run_command

def check_failed_services() -> Tuple[bool, List[str]]:
    """
    Return failed systemd services.
    """
    ok, out = run_command(["systemctl", "--failed", "--no-legend", "--no-pager"])

    if not ok or not out:
        return False, []

    lines = [line.strip() for line in out.splitlines() if line.strip()]
    return True, lines

def list_all_services() -> Tuple[bool, str]:

    return run_command(["systemctl", "list-units", "--type=service", "--state=running"])
