#!/usr/bin/env python3
"""PreToolUse hook (plan sec 6.2): ownership + destructive/credential/S1 guards.

Push policy (owner standing delegation 2026-09-11, "Bạn tự do push"): the
Lead session in the ROOT checkout may push; lane worktrees NEVER push —
`git push` is denied when the command or the session cwd references a lane
worktree (.worktrees/).

Absolute denies (context-independent): hard reset/clean, main-merge
destruction, .env/credential echo, S1 path reads via cat.
Context-dependent (only when a dispatch is active, i.e.
.runtime/orchestrator_v3/current_dispatch.json exists): Edit/Write target
paths must stay inside the active task's allowed_paths and outside its
forbidden_paths; a writable subagent dispatch requires the registered
dispatch context (the ownership manifest of this design).

Exit 0 with permissionDecision JSON for allow/deny; exit 2 is the hard
blocking shortcut for malformed evaluation of a dangerous command.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(os.environ.get("QUANT_REPO_ROOT",
                           str(Path(__file__).resolve().parents[3]))).resolve()
_env_rt = os.environ.get("ZCODE_ORCH_RUNTIME_DIR")
RUNTIME = Path(_env_rt).resolve() if _env_rt else \
    REPO / ".runtime" / "orchestrator_v3"

GIT_PUSH = re.compile(r"\bgit\b[^|;&\n]*\bpush\b")
ABSOLUTE_BASH_DENY = (
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "destructive reset is forbidden"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*f"), "destructive clean is forbidden"),
    (re.compile(r"\bgit\s+filter-branch\b|\bgit\s+rebase\b.*--onto\s+main\b"),
     "history rewrite is forbidden"),
    (re.compile(r"\bcat\s+(?:[^|;\n]*\/)?\.env\b|\bless\s+[^|;\n]*\.env\b|\bhead\s+[^|;\n]*\.env\b"),
     "credential echo: .env content must not enter the conversation"),
    (re.compile(r"\b(?:printenv|env)\b[^;\n]*(?:SECRET|TOKEN|PASSWORD|API_KEY)"),
     "credential echo via environment dump"),
    (re.compile(r"\bmerge\s+.{0,40}\bmain\b|\bcheckout\s+main\b\s"),
     "main is owner/bootstrap space; merge/checkout mutations need owner authority"),
)
S1_PATTERNS = (re.compile(r"(?i)s1[_/-]?(?:data|scored|sealed)"),
               re.compile(r"(?i)sealed_oos"))
REGISTRY_WRITE_FILES = re.compile(
    r"(CYCLE_REGISTRY\.json|ACTIVE_CYCLES\.json|HYPOTHESIS_LEDGER\.md)$")
HEAVY_COMMAND = re.compile(
    r"\bpytest\b|\bfull[_-]suite\b|\bscored?\b|\bdownload_(?:funding|derivatives)\b")


def _deny(reason: str) -> int:
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"[orchestrator-v3] {reason}",
    }}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def _allow(note: str = "") -> int:
    if note:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": f"[orchestrator-v3] {note}",
        }}, sys.stdout)
        sys.stdout.write("\n")
    return 0


def _active_dispatch() -> dict | None:
    path = RUNTIME / "current_dispatch.json"
    if not path.exists():
        return None
    try:
        ctx = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return ctx if ctx.get("schema") == "zcode_orch_v3_dispatch@1" else None


def _flat(obj) -> str:
    return json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj


def main() -> int:
    try:
        raw = sys.stdin.readline()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # cannot evaluate -> do not block, the tool layer still prompts
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    blob = _flat(tool_input)

    if tool == "Bash":
        cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else blob
        cwd = str(payload.get("cwd") or "")
        if GIT_PUSH.search(cmd) and (".worktrees" in cmd or "/.worktrees/" in cwd):
            return _deny("lanes never push (plan sec 13); push from the root "
                         "checkout only (owner standing delegation 2026-09-11 "
                         "covers the Lead session, not lane agents)")
        for rx, why in ABSOLUTE_BASH_DENY:
            if rx.search(cmd):
                return _deny(why)
        for rx in S1_PATTERNS:
            if rx.search(cmd):
                return _deny("S1 is sealed until an explicitly authorized stage (plan sec 13)")
        if HEAVY_COMMAND.search(cmd):
            ctx = _active_dispatch()
            if ctx and ctx.get("workload_class") == "HEAVY":
                return _allow("heavy command under a registered heavy dispatch")
        return 0

    if tool in ("Edit", "Write", "NotebookEdit"):
        target = tool_input.get("file_path", "") if isinstance(tool_input, dict) else ""
        if REGISTRY_WRITE_FILES.search(target.replace("\\", "/")):
            ctx = _active_dispatch()
            if ctx is not None:
                return _deny("lane agents never write the canonical registry/ledger "
                             "(A1 integrates through the canonical path only)")
        for rx in S1_PATTERNS:
            if rx.search(target):
                return _deny("S1 write attempt: sealed data is untouchable")
        ctx = _active_dispatch()
        if ctx is not None:
            allowed = ctx.get("allowed_paths") or []
            forbidden = ctx.get("forbidden_paths") or []
            if forbidden and any(f and target.startswith(f) for f in forbidden):
                return _deny(f"path outside ownership: {target} is forbidden for "
                             f"task {ctx.get('task_id')}")
            if allowed and not any(a and target.startswith(a) for a in allowed):
                return _deny(f"path outside ownership: {target} is not in allowed_paths "
                             f"for task {ctx.get('task_id')} (SCOPE_ESCAPE_REQUIRED -> "
                             "report back, never improvise)")
        return 0

    if tool in ("Agent", "Task"):
        if isinstance(tool_input, dict):
            wanted = str(tool_input.get("name", "") or tool_input.get("subagent_type", ""))
            prompt = str(tool_input.get("prompt", ""))
        else:
            wanted, prompt = "", blob
        writable_role = wanted == "quant-implementer" or "implement" in prompt.lower()[:400]
        ctx = _active_dispatch()
        if writable_role and ctx is None:
            return _deny("writable dispatch requires a registered task + dispatch "
                         "context (orchestrator_register_task + mark_dispatched first)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
