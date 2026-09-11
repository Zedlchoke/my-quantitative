#!/usr/bin/env python3
"""Stop hook (plan sec 6.4): a safety gate, not a scheduler.

If owned work remains (active tasks, unvalidated handoffs, unrun terminal
check), request ONE continuation with a compact next action (decision:block).
ZCode bounds consecutive Stop continuations at 3; this hook additionally
self-caps at 3 via a local counter file, then stands down - durable recovery
remains /lead-resume + the task state, never an infinite loop.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("QUANT_REPO_ROOT",
                           str(Path(__file__).resolve().parents[3]))).resolve()
_env_rt = os.environ.get("ZCODE_ORCH_RUNTIME_DIR")
RUNTIME = Path(_env_rt).resolve() if _env_rt else \
    REPO / ".runtime" / "orchestrator_v3"
MAX_BLOCKS = 3
ACTIVE_STATES = ("REGISTERED", "READY", "DISPATCHED", "RUNNING",
                 "HANDOFF_READY", "VALIDATING")


def main() -> int:
    try:
        raw = sys.stdin.readline()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    tasks_path = RUNTIME / "tasks.json"
    if not tasks_path.exists():
        return 0  # no owned state; ordinary session end is fine
    try:
        store = json.loads(tasks_path.read_text(encoding="utf-8"))
    except Exception:
        json.dump({"decision": "block", "reason":
                   "[orchestrator-v3] CONTROL_STATE_DRIFT: tasks.json is "
                   "malformed - run /lead-status and reconcile before ending."},
                  sys.stdout)
        sys.stdout.write("\n")
        return 0
    active = [t for t in store.get("tasks", [])
              if t.get("status") in ACTIVE_STATES]
    unvalidated = [t["task_id"] for t in store.get("tasks", [])
                   if t.get("status") == "HANDOFF_READY"]
    if not active:
        return 0
    count_path = RUNTIME / "stop_block_count.json"
    count = 0
    if payload.get("stop_hook_active"):
        try:
            count = json.loads(count_path.read_text(encoding="utf-8")).get("count", 0)
        except Exception:
            count = 0
    count += 1
    if count > MAX_BLOCKS:
        return 0  # stand down; /lead-resume owns recovery from durable state
    try:
        count_path.parent.mkdir(parents=True, exist_ok=True)
        count_path.write_text(json.dumps({"count": count}) + "\n", encoding="utf-8")
    except Exception:
        pass
    next_action = (f"validate + integrate handoff for {unvalidated[0]}"
                   if unvalidated else
                   f"reconcile in-flight tasks {[t['task_id'] for t in active]}")
    json.dump({"decision": "block", "reason":
               f"[orchestrator-v3] owned work remains ({len(active)} non-terminal "
               f"tasks; unvalidated handoffs: {unvalidated}). Next single action: "
               f"{next_action}. After {MAX_BLOCKS} continuations this hook stands "
               "down - use /lead-resume for durable recovery."},
              sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
