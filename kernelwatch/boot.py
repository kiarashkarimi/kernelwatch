import os
from typing import Tuple, List

# ----------------------------

# Initramfs Detection

# ----------------------------

def _list_initramfs() -> List[str]:
    """Return all initramfs images found in /boot."""
    try:
        return [
            f for f in os.listdir("/boot")
            if f.startswith("initramfs") and f.endswith(".img")
        ]
    except Exception:
        return []
    
def check_initramfs() -> Tuple[bool, str]:

    """
    Validate initramfs presence in a distro-agnostic way.
    Rules:
    - CRITICAL: no initramfs images exist
    - OK: at least one initramfs exists with expected naming
    - WARN: initramfs exists but no 'linux' hint in naming
    """

    files = _list_initramfs()

    if not files:
        return False, "no initramfs images found in /boot"

    # Heuristic: Arch standard kernels usually include "linux"
    canonical = any("linux" in f for f in files)

    if canonical:
        return True, f"initramfs detected: {', '.join(files)}"

    return True, f"initramfs present (non-standard layout): {', '.join(files)}"

# ----------------------------

# Bootloader Detection

# ----------------------------

def check_bootloader() -> Tuple[bool, str]:
    """
    Detect known bootloader installations.
    Does not assume configuration correctness.
    """

    loaders = []

    if os.path.isdir("/boot/loader"):
        loaders.append("systemd-boot")

    if os.path.isdir("/boot/grub"):
        loaders.append("GRUB")

    if loaders:
        return True, "bootloader(s) detected: " + ", ".join(loaders)

    return False, "no known bootloader detected"

# ----------------------------

# Boot Entries Validation

# ----------------------------

def check_boot_entries() -> Tuple[bool, str]:
    """
    Check for existence of boot entry configuration.
    This does NOT validate correctness, only presence.
    """

    systemd_entries = os.path.isdir("/boot/loader/entries")

    grub_cfg = os.path.isfile("/boot/grub/grub.cfg")

    if systemd_entries or grub_cfg:
        sources = []
        if systemd_entries:
            sources.append("systemd-boot entries")
        if grub_cfg:
            sources.append("GRUB config")

        return True, "boot entries present (" + ", ".join(sources) + ")"

    return False, "no boot entries found"

