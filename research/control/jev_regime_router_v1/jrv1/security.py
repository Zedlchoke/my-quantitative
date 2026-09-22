"""Security surface for jrv1: S1 denial + static no-venue-surface self-scan.

Two guarantees, both testable:

1. Path denial: every file opened by jrv1 loaders passes through
   :func:`safe_open` / :func:`assert_safe_path`, which raises
   :class:`SecurityViolation` for any path containing ``/S1`` or a filename
   component beginning with ``s1_``. S1 stays SEALED_UNTOUCHED.

2. No execution-venue surface: :func:`scan_package_source` statically scans
   every ``*.py`` file in this package for forbidden substrings (order
   placement / venue-client APIs). Must always find none.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

# Forbidden substrings, assembled from fragments so this source file never
# itself contains any needle (the self-scan must always find none).
_F = (
    "order",
    "_send",
    "place",
    "brok",
    "ccx",
    "web",
    "socket",
    "ib_",
    "insync",
    "alpa",
    "ca",
    "binance cli",
    "ent",
)

FORBIDDEN_SUBSTRINGS = (
    _F[0] + _F[1],      # order transmission
    _F[2] + "_" + _F[0],  # order placement (underscored)
    _F[2] + _F[0],      # order placement (compact)
    _F[3] + "er",       # venue client word
    _F[4] + "t",        # crypto venue SDK
    _F[5] + _F[6],      # streaming surface
    _F[7] + _F[8],      # TWS SDK
    _F[9] + "ca",       # stock venue SDK
    _F[11] + _F[12],    # venue SDK name (spaced)
)


class SecurityViolation(RuntimeError):
    """Raised when a sealed path is touched or a forbidden surface appears."""


def assert_safe_path(path: str | os.PathLike) -> Path:
    """Raise SecurityViolation if the path touches S1 evidence space."""
    p = Path(path)
    s = str(p)
    # '/S1' anywhere in the path (directory component of the sealed tree) or
    # any path segment starting with 's1_' (case-sensitive per contract).
    if "/S1" in s or "/S1/" in s:
        raise SecurityViolation(f"S1 path access denied: {s}")
    for part in p.parts:
        if part.startswith("s1_") or part == "S1":
            raise SecurityViolation(f"S1 path access denied: {s}")
    return p


def safe_open(path: str | os.PathLike, mode: str = "rb", **kwargs):
    """Open a file only after S1 denial check. All jrv1 readers go through here."""
    p = assert_safe_path(path)
    return io.open(p, mode, **kwargs)


def scan_package_source(package_dir: str | os.PathLike | None = None) -> dict:
    """Static self-scan of all jrv1 *.py sources for forbidden substrings.

    Returns {'files_scanned': int, 'findings': [(file, needle)]}. findings
    must always be empty; tests assert this.
    """
    if package_dir is None:
        package_dir = Path(__file__).resolve().parent
    pkg = Path(package_dir)
    findings: list[tuple[str, str]] = []
    files_scanned = 0
    for f in sorted(pkg.rglob("*.py")):
        files_scanned += 1
        text = f.read_text(encoding="utf-8")
        lowered = text.lower()
        for needle in FORBIDDEN_SUBSTRINGS:
            if needle.lower() in lowered:
                findings.append((str(f), needle))
    return {"files_scanned": files_scanned, "findings": findings}
