# kernelwatch

Minimal Arch Linux system health diagnostic tool focused on kernel, boot, and package integrity.

## Philosophy

* Read-only diagnostics
* No automatic system modification
* Explicit, transparent output
* Designed for Arch Linux users who want kernel-level awareness

## Installation

```bash
pip install .
```

or development:

```bash
pip install -r requirements.txt
```

## Usage

### Run full system check

```bash
kernelwatch doctor
```

### Show version

```bash
kernelwatch version
```

## Scope (v0.1)

* Kernel status inspection
* Boot integrity checks
* Pacman database validation
* Systemd failure detection
* Kernel log error reporting

## Design goal

Replace ad-hoc shell scripts with a structured, extensible diagnostic layer for Arch Linux systems.
