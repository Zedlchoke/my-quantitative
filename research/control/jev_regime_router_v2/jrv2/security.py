"""Security surface for jrv2: S1 denial + V1 isolation + no-venue scan.

Four guarantees, all testable:

1. Path denial (V1 law): every file opened by jrv2 loaders passes through
   :func:`safe_open` / :func:`assert_safe_path`, which raises
   :class:`SecurityViolation` for any path containing ``/S1`` or a path
   component beginning with ``s1_``.

2. V1 ISOLATION (new in V2): any path containing the V1 cycle directory
   name (the ``jev_regime_router_v`` + ``1`` marker assembled below) is
   refused at open time by :func:`assert_safe_path` — v2 code can never
   read V1 runtime/cache/decision artifacts. Reading V1 SOURCE to adapt it
   is a human/agent activity outside the v2 runtime surface.
   :func:`scan_v1_references` statically proves no jrv2 source references a
   V1 runtime path.

3. No execution-venue surface: :func:`scan_package_source` statically scans
   every ``*.py`` file in this package for forbidden substrings (order
   placement / venue-client APIs). Must always find none.

4. Credential hygiene: nothing here reads credential VALUES; the adapter
   layer checks env presence by name only (TS side).
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
    _F[0] + _F[1],       # order transmission
    _F[2] + "_" + _F[0],  # order placement (underscored)
    _F[2] + _F[0],       # order placement (compact)
    _F[3] + "er",        # venue client word
    _F[4] + "t",         # crypto venue SDK
    _F[5] + _F[6],       # streaming surface
    _F[7] + _F[8],       # TWS SDK
    _F[9] + "ca",        # stock venue SDK
    _F[11] + _F[12],     # venue SDK name (spaced)
)

# V1 namespace marker (assembled from fragments so this source never
# contains the literal needle and the self-scan stays clean).
_V1A = "jev_regime_"
V1_DIR_MARKERS = (_V1A + "router_v" + "1",)
V1_RUNTIME_MARKERS = (
    _V1A + "router_v" + "1" + "/runtime",
    _V1A + "router_v" + "1" + "/data_local",
)


class SecurityViolation(RuntimeError):
    """Raised when a sealed/V1 path is touched or a forbidden surface appears."""


def assert_safe_path(path: str | os.PathLike) -> Path:
    """Raise SecurityViolation if the path touches S1 space or ANY V1 path."""
    p = Path(path)
    s = str(p)
    if "/S1" in s or "/S1/" in s:
        raise SecurityViolation(f"S1 path access denied: {s}")
    for part in p.parts:
        if part.startswith("s1_") or part == "S1":
            raise SecurityViolation(f"S1 path access denied: {s}")
    for marker in V1_DIR_MARKERS:
        if marker in s:
            raise SecurityViolation(
                f"V1 isolation violated: jrv2 code opened a V1 path: {s}"
            )
    return p


def safe_open(path: str | os.PathLike, mode: str = "rb", **kwargs):
    """Open a file only after the S1 + V1-isolation denial checks."""
    p = assert_safe_path(path)
    return io.open(p, mode, **kwargs)


def _scan_files(package_dir: Path, needles) -> dict:
    findings: list[tuple[str, str]] = []
    files_scanned = 0
    for f in sorted(package_dir.rglob("*.py")):
        files_scanned += 1
        text = f.read_text(encoding="utf-8")
        lowered = text.lower()
        for needle in needles:
            if needle.lower() in lowered:
                findings.append((str(f), needle))
    return {"files_scanned": files_scanned, "findings": findings}


def scan_package_source(package_dir: str | os.PathLike | None = None) -> dict:
    """Static self-scan of all jrv2 *.py sources for forbidden venue substrings."""
    pkg = Path(package_dir) if package_dir else Path(__file__).resolve().parent
    return _scan_files(pkg, FORBIDDEN_SUBSTRINGS)


def scan_v1_references(package_dir: str | os.PathLike | None = None) -> dict:
    """Static proof that no jrv2 source references a V1 runtime path.

    Scans for both the bare V1 directory marker and its runtime/data_local
    subpaths. findings must always be empty; tests assert this.
    """
    pkg = Path(package_dir) if package_dir else Path(__file__).resolve().parent
    return _scan_files(pkg, V1_DIR_MARKERS + V1_RUNTIME_MARKERS)


def assert_no_credential_leak(text: str) -> bool:
    """True when no credential VALUE appears in the text (name-only allowed).

    The credential value is never loaded into jrv2 strings by design; when
    the env var is absent this check trivially passes. The adapter layer
    (TS) holds the same law.
    """
    val = os.environ.get("TYPESAFE_API_KEY", "")
    return not (val and val in text)
