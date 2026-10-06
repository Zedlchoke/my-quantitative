"""Read-only REAL-state checks (safe to run for real — no write anywhere).

LANE-CANONICAL-CODE wave-4: permitted read-only real-state verification.
Every function here only READS the real governance surfaces:

(i)  the real cycle registry parses, counts cycles, and can check a named
     cycle row — via the canonical strict loader (cycle_registry.load), never
     by hand-rolled parsing;
(ii) the machine-wide heavy-lock verdict, parsed from an actual
     ``researchctl.py locks inspect`` run (the documented operator entrypoint,
     which is inspect-only by design);
(iii) a digest of the real governance heavy_runtime listing.

Nothing here acquires the lock, writes the registry, or mutates any real
file — the isolation is proven by sha-snapshots (test T14 and the suite-level
proof recorded in the lane handoff).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_RESEARCH_DIR = _REPO / "research"
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from governance import atomic_io, cycle_registry  # noqa: E402

REAL_REPO_ROOT = Path(_REPO)
REAL_ROOT_REGISTRY = REAL_REPO_ROOT / "plans" / "CYCLE_REGISTRY.json"
REAL_RESEARCHCTL = REAL_REPO_ROOT / "research" / "researchctl.py"
REAL_GOVERNANCE_DIR = Path.home() / ".my-quantitative-governance"
REAL_HEAVY_RUNTIME = REAL_GOVERNANCE_DIR / "heavy_runtime"

CYCLE_ID_THIS_ROUND = "FUTURES-5SYM-PRESCORED-20261005"


# -------------------------------------------------- (i) real registry check

def check_real_registry(
    *,
    registry_path: os.PathLike | str = REAL_ROOT_REGISTRY,
    assert_absent_cycles: tuple[str, ...] = (CYCLE_ID_THIS_ROUND,),
) -> dict:
    """Parse the REAL registry through the canonical strict loader.

    Returns a machine-readable report: schema, cycle count, id-index facts,
    presence flags for the requested assert-absent cycle ids, and the file
    sha256. Read-only: raises (ControlStateDrift) on malformed state — a
    malformed real registry is never repaired from here.
    """
    registry_path = Path(registry_path)
    sha = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    reg = cycle_registry.load(registry_path)          # strict validation
    ids = [c["cycle_id"] for c in reg["cycles"]]
    presence = {cid: (cid in ids) for cid in assert_absent_cycles}
    return {
        "check": "real_registry_parse",
        "registry": str(registry_path),
        "schema": reg["schema"],
        "n_cycles": len(ids),
        "unique_cycle_ids": len(set(ids)),
        "assert_absent": presence,
        "all_absent_as_required": not any(presence.values()),
        "registry_sha256": sha,
        "read_only": True,
    }


# --------------------------------------------- (ii) locks-inspect verdict

def parse_locks_inspect(report: dict) -> dict:
    """Parse a locks-inspect JSON report (dict form) into a verdict summary.

    Tri-state law: HELD_PROVEN | FREE_PROVEN | CONTROL_STATE_DRIFT. Ambiguous
    NEVER becomes FREE — the parser preserves the verdict verbatim plus the
    key evidence fields; it never re-classifies."""
    verdict = report.get("verdict")
    ev = report.get("evidence", {}) or {}
    known = ("HELD_PROVEN", "FREE_PROVEN", "CONTROL_STATE_DRIFT")
    return {
        "verdict": verdict,
        "reason": report.get("reason"),
        "flock_state": ev.get("flock_state"),
        "registry_path": ev.get("registry_path"),
        "lock_path": ev.get("lock_path"),
        "registry_row_present": "registry_row" in ev,
        "runtime_dir": report.get("runtime_dir"),
        "known_verdict": verdict in known,
    }


def real_locks_inspect(
    *,
    python: str = sys.executable,
    researchctl: os.PathLike | str = REAL_RESEARCHCTL,
    timeout: float = 30.0,
) -> dict:
    """Run the REAL ``researchctl.py locks inspect`` (read-only by design)
    and return the parsed verdict. Never acquires the lock."""
    proc = subprocess.run(
        [str(python), str(researchctl), "locks", "inspect"],
        capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        return {"verdict": "INSPECT_FAILED", "returncode": proc.returncode,
                "stderr": proc.stderr[-2000:]}
    report = json.loads(proc.stdout)
    parsed = parse_locks_inspect(report)
    parsed["last_history_rows_n"] = len(report.get("last_history_rows", []))
    parsed["read_only_cli"] = True
    return parsed


# -------------------------------------------- (iii) governance dir digest

def governance_listing_digest(
    *,
    runtime_dir: os.PathLike | str = REAL_HEAVY_RUNTIME,
) -> dict:
    """sha256 + size digest of every file in the real heavy_runtime listing
    (sorted by relative path). A registry row file is absent while the lock
    is free — recorded as ABSENT, never fabricated."""
    runtime = Path(runtime_dir)
    files: dict[str, dict] = {}
    for p in sorted(runtime.iterdir()) if runtime.is_dir() else []:
        if p.is_file():
            data = p.read_bytes()
            files[p.name] = {"sha256": hashlib.sha256(data).hexdigest(),
                             "bytes": len(data)}
    # expected canonical members, recorded even when absent
    for expected in ("heavy_worker.lock", "heavy_worker.registry.json",
                     "heavy_worker.history.jsonl", "scheduler_jobs.json"):
        files.setdefault(expected, {"sha256": "ABSENT", "bytes": 0})
    return {
        "check": "real_governance_listing_digest",
        "runtime_dir": str(runtime),
        "files": dict(sorted(files.items())),
        "read_only": True,
    }


def sha_snapshot(paths: list[os.PathLike | str]) -> dict:
    """Generic path -> sha256 snapshot for byte-identical isolation proofs.
    Missing paths are recorded as ABSENT (presence changes are detectable)."""
    snap: dict[str, str] = {}
    for p in paths:
        try:
            snap[str(p)] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
        except OSError:
            snap[str(p)] = "ABSENT"
    return dict(sorted(snap.items()))
