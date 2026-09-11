#!/usr/bin/env python3
"""SessionStart hook (plan sec 6.1): inject a compact generated snapshot.

Read-only. Strict failure semantics: a failure is VISIBLE in the injected
context (SNAPSHOT_UNAVAILABLE) and never silently becomes a clean state.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(os.environ.get("QUANT_REPO_ROOT",
                           str(Path(__file__).resolve().parents[3]))).resolve()
sys.path.insert(0, str(REPO / "research"))


def _git(*args: str, cwd: Path) -> str:
    try:
        return subprocess.run(("git", "-C", str(cwd)) + args,
                              capture_output=True, text=True, timeout=4,
                              check=True).stdout.strip()
    except Exception as exc:  # noqa: BLE001 - visible failure, never a guess
        return f"UNMEASURABLE({type(exc).__name__})"


def main() -> int:
    try:
        raw = sys.stdin.readline()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    cwd = Path(payload.get("cwd") or str(REPO))
    lines = ["[orchestrator-v3 snapshot]"]
    try:
        branch = _git("branch", "--show-current", cwd=cwd)
        head = _git("rev-parse", "HEAD", cwd=cwd)
        dirty = _git("status", "--porcelain=v1", cwd=cwd)
        lines.append(f"cwd={cwd} branch={branch} HEAD={head}")
        lines.append(f"dirty={'CLEAN' if not dirty else dirty[:400]}")
        from governance import cycle_registry, atomic_io
        reg = cycle_registry.load(REPO / "plans" / "CYCLE_REGISTRY.json")
        act = [(c["cycle_id"], c["lifecycle"], c["phase"]) for c in reg["cycles"]
               if c["lifecycle"] != "TERMINAL"]
        lines.append(f"canonical_non_terminal_cycles={act}")
        lines.append("s1_boundary=SEALED_UNTOUCHED everywhere; no scoring/GO/push/"
                     "main-merge without explicit owner authority (plan sec 13)")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"SNAPSHOT_UNAVAILABLE: registry/lock state not measured "
                     f"({type(exc).__name__}: {exc}) - treat state as UNMEASURED, "
                     "run researchctl cycle doctor + locks inspect before dispatch")
    try:
        from governance import heavy_lock
        rep = heavy_lock.inspect()
        lines.append(f"heavy_lock={rep['verdict']} ({rep.get('reason', '')[:120]})")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"heavy_lock=UNMEASURABLE({type(exc).__name__})")
    try:
        from orchestrator_store import OrchestratorStore
        store = OrchestratorStore()
        if store.exists():
            ws = store.waiting_summary()
            lines.append(f"orchestrator: ready={ws['ready']} "
                         f"inflight={[(t['task_id'], t['status']) for t in ws['inflight']]} "
                         f"awaiting_validation={ws['awaiting_validation']}")
        else:
            lines.append("orchestrator: no runtime store (run orchestrator_intake "
                         "or /lead-resume; missing state is not an empty queue)")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"orchestrator=SNAPSHOT_UNAVAILABLE({type(exc).__name__})")
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
