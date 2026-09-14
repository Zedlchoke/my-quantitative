#!/usr/bin/env python3
"""Orchestrator V3 controller MCP - local stdio JSON-RPC server (plan sec 5).

Wraps the OrchestratorStore + repository governance state as MCP tools. It is
NOT a second scheduler authority: it never calls a model, never spawns ZCode
agents, never mutates the canonical cycle registry directly (registry writes
stay behind researchctl / governance.cycle_registry). Missing or malformed
runtime state surfaces as CONTROL_STATE_DRIFT, never as an empty queue.

Protocol: MCP stdio (JSON-RPC 2.0, one JSON object per line). Declared to
ZCode under mcpServers in .zcode-plugin/plugin.json (design delta D1 - ZCode
v3.10.2 has no .mcp.json mechanism).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator_store import (  # noqa: E402
    OrchestratorStore, CONTROL_STATE_DRIFT, DependencyCycle,
    ForeignTaskRefused, IllegalTransition, TaskNotFound,
)

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "quant-research-orchestrator", "version": "0.1.2"}

TOOLS = [
    ("orchestrator_intake", "Create this cycle's runtime task store (idempotent; refuses to overwrite an existing valid store).",
     {"type": "object", "properties": {"writer": {"type": "string"}}, "required": []}),
    ("orchestrator_register_task", "Register a NEW task (REGISTERED). Duplicate ids, unknown dependencies and dependency cycles are refused.",
     {"type": "object", "properties": {
         "task_id": {"type": "string"}, "role": {"type": "string"},
         "objective": {"type": "string"}, "base_sha": {"type": "string"},
         "branch": {"type": "string"}, "absolute_worktree": {"type": "string"},
         "allowed_paths": {"type": "array", "items": {"type": "string"}},
         "forbidden_paths": {"type": "array", "items": {"type": "string"}},
         "dependencies": {"type": "array", "items": {"type": "string"}},
         "priority": {"type": "integer"}, "workload_class": {"type": "string"},
         "background_allowed": {"type": "boolean"},
         "test_commands": {"type": "array", "items": {"type": "string"}},
         "max_attempts": {"type": "integer"}},
      "required": ["task_id", "role", "objective"]}),
    ("orchestrator_list_ready", "List REGISTERED tasks whose dependencies are done, priority-ordered.",
     {"type": "object", "properties": {}, "required": []}),
    ("orchestrator_mark_dispatched", "READY->DISPATCHED and open a new attempt (idempotent for a repeated identical dispatch).",
     {"type": "object", "properties": {"task_id": {"type": "string"},
                                        "invocation_id": {"type": "string"}},
      "required": ["task_id"]}),
    ("orchestrator_heartbeat", "Record a live heartbeat (DISPATCHED/RUNNING only).",
     {"type": "object", "properties": {"task_id": {"type": "string"},
                                        "pid": {"type": "integer"}},
      "required": ["task_id"]}),
    ("orchestrator_publish_handoff", "RUNNING->HANDOFF_READY; refuses a dispatch_sha that does not match the task's recorded dispatch context, then atomically writes the submitted object over the inbox artifact and records its digest.",
     {"type": "object", "properties": {"task_id": {"type": "string"},
                                        "handoff": {"type": "object"}},
      "required": ["task_id", "handoff"]}),
    ("orchestrator_validate_handoff", "HANDOFF_READY->VALIDATING; re-reads the artifact from disk and fails closed on digest drift. A failed validation escapes forward via record_blocker(BLOCKED) from HANDOFF_READY.",
     {"type": "object", "properties": {"task_id": {"type": "string"}},
      "required": ["task_id"]}),
    ("orchestrator_mark_integrated", "VALIDATING->INTEGRATED with the integrated commit sha; the sha must resolve to a git commit in the task's recorded worktree or the transition is refused.",
     {"type": "object", "properties": {"task_id": {"type": "string"},
                                        "commit_sha": {"type": "string"}},
      "required": ["task_id"]}),
    ("orchestrator_record_blocker", "VALIDATING->REJECTED|BLOCKED|TECHABORT (or HANDOFF_READY->BLOCKED when validation failed) with a reason.",
     {"type": "object", "properties": {"task_id": {"type": "string"},
                                        "outcome": {"type": "string"},
                                        "reason": {"type": "string"}},
      "required": ["task_id", "outcome"]}),
    ("orchestrator_waiting_summary", "Ready / in-flight / awaiting-validation readout for the Lead.",
     {"type": "object", "properties": {}, "required": []}),
    ("orchestrator_terminal_check", "All-terminal reconciliation check for this cycle's tasks.",
     {"type": "object", "properties": {}, "required": []}),
]


def _store() -> OrchestratorStore:
    return OrchestratorStore()


def _ok(store: OrchestratorStore, result) -> dict:
    return {"content": [{"type": "text",
                         "text": json.dumps(result, indent=1, ensure_ascii=False)}],
            "isError": False}


def _err(exc: Exception) -> dict:
    return {"content": [{"type": "text",
                         "text": json.dumps({"error": str(exc),
                                             "kind": type(exc).__name__},
                                            ensure_ascii=False)}],
            "isError": True}


def call_tool(name: str, args: dict) -> dict:
    store = _store()
    if name == "orchestrator_intake":
        return _ok(store, store.intake(writer=(args or {}).get("writer", "primary-lead")))
    if name == "orchestrator_register_task":
        a = args or {}
        task = store.register_task(
            task_id=a["task_id"], role=a["role"], objective=a["objective"],
            base_sha=a.get("base_sha", ""), branch=a.get("branch", ""),
            absolute_worktree=a.get("absolute_worktree", ""),
            allowed_paths=a.get("allowed_paths"), forbidden_paths=a.get("forbidden_paths"),
            dependencies=a.get("dependencies"), priority=a.get("priority", 5),
            workload_class=a.get("workload_class", "LIGHT"),
            background_allowed=a.get("background_allowed", True),
            test_commands=a.get("test_commands"),
            max_attempts=a.get("max_attempts", 3))
        return _ok(store, task)
    if name == "orchestrator_list_ready":
        return _ok(store, {"ready": [
            {"task_id": t["task_id"], "role": t["role"], "priority": t["priority"],
             "workload_class": t["workload_class"], "branch": t["branch"],
             "absolute_worktree": t["absolute_worktree"]}
            for t in store.list_ready()]})
    if name == "orchestrator_mark_dispatched":
        a = args or {}
        return _ok(store, store.mark_dispatched(
            task_id=a["task_id"], invocation_id=a.get("invocation_id")))
    if name == "orchestrator_heartbeat":
        a = args or {}
        return _ok(store, store.heartbeat(task_id=a["task_id"], pid=a.get("pid")))
    if name == "orchestrator_publish_handoff":
        a = args or {}
        return _ok(store, store.publish_handoff(task_id=a["task_id"],
                                                handoff=a["handoff"]))
    if name == "orchestrator_validate_handoff":
        return _ok(store, store.validate_handoff(task_id=(args or {})["task_id"]))
    if name == "orchestrator_mark_integrated":
        a = args or {}
        return _ok(store, store.mark_integrated(task_id=a["task_id"],
                                                commit_sha=a.get("commit_sha", "")))
    if name == "orchestrator_record_blocker":
        a = args or {}
        return _ok(store, store.record_outcome(task_id=a["task_id"],
                                               outcome=a["outcome"],
                                               reason=a.get("reason", "")))
    if name == "orchestrator_waiting_summary":
        return _ok(store, store.waiting_summary())
    if name == "orchestrator_terminal_check":
        return _ok(store, store.terminal_check())
    raise KeyError(f"unknown tool {name}")


def handle(msg: dict) -> Optional[dict]:
    method = msg.get("method", "")
    mid = msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO}}
    if method.startswith("notifications/"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [
            {"name": n, "description": d, "inputSchema": s}
            for n, d, s in TOOLS]}}
    if method == "tools/call":
        params = msg.get("params", {})
        try:
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
        except (TaskNotFound, IllegalTransition, ForeignTaskRefused,
                DependencyCycle, KeyError, ValueError) as exc:
            return {"jsonrpc": "2.0", "id": mid, "result": _err(exc)}
        except Exception as exc:  # drift and the unexpected: fail closed, never guess
            kind = CONTROL_STATE_DRIFT if "ControlState" in type(exc).__name__ \
                or "DRIFT" in str(exc).upper() else type(exc).__name__
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": json.dumps(
                    {"error": str(exc), "kind": kind}, ensure_ascii=False)}],
                "isError": True}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {
            "code": -32601, "message": f"method not found: {method}"}}
    return None


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            resp = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32700, "message": f"parse error: {exc}"}}
        else:
            resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
