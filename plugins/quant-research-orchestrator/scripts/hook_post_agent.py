#!/usr/bin/env python3
"""PostToolUse hook (plan sec 6.3): after an Agent/Task tool returns, verify the
handoff artifact exists for the active dispatch. A missing handoff is injected
as HANDOFF_INVALID - success is NEVER inferred from prose. Other tools pass.
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


def main() -> int:
    try:
        raw = sys.stdin.readline()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    if payload.get("tool_name") not in ("Agent", "Task"):
        return 0
    dispatch = RUNTIME / "current_dispatch.json"
    if not dispatch.exists():
        return 0
    try:
        ctx = json.loads(dispatch.read_text(encoding="utf-8"))
    except Exception:
        ctx = None
    if not ctx or ctx.get("schema") != "zcode_orch_v3_dispatch@1":
        return 0
    handoff = None
    try:
        tasks = json.loads((RUNTIME / "tasks.json").read_text(encoding="utf-8"))
        for t in tasks.get("tasks", []):
            if t.get("task_id") == ctx.get("task_id"):
                handoff = t.get("handoff_path")
                break
    except Exception:
        handoff = None
    note = (f"[orchestrator-v3] Agent returned for task {ctx.get('task_id')}. ")
    if handoff and Path(handoff).exists():
        note += (f"Handoff artifact present: {handoff}. Validate it with "
                 "orchestrator_validate_handoff + independent git checks; prose is advisory.")
    else:
        note += ("HANDOFF_INVALID: no handoff artifact on disk for this task - "
                 "do NOT infer success from the chat summary. Re-dispatch a new "
                 "attempt (within max_attempts) or record TECHABORT/BLOCKED.")
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": note,
    }}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
