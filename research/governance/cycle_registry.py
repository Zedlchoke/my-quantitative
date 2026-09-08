"""Canonical active-cycle registry, schema cycle_registry@1 (SHV1 sec7.2).

plans/CYCLE_REGISTRY.json is the ONLY writable cycle authority. Legacy cycle
state files and the committed projection plans/ACTIVE_CYCLES.json are read
through legacy_adapters and never rewritten (G6). Writers emit this schema
only; readers refuse malformed state (fail closed, never repair).

PAUSED_MAINTENANCE is introduced by this versioned schema per SHV1 sec4; it
never appears in legacy records.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Optional

from governance import atomic_io

SCHEMA_ID = "cycle_registry@1"
REGISTRY_REL = "plans/CYCLE_REGISTRY.json"
EVENTS_REL = "plans/CYCLE_REGISTRY.events.jsonl"

LIFECYCLE = (
    "PLANNED_NOT_STARTED",
    "ACTIVE_LIGHT",
    "ACTIVE_HEAVY",
    "PAUSED_RESOURCE_CONFLICT",
    "PAUSED_MAINTENANCE",
    "BLOCKED",
    "TERMINAL",
)

# lifecycles a router may dispatch work into
DISPATCHABLE = ("ACTIVE_LIGHT", "ACTIVE_HEAVY", "PAUSED_RESOURCE_CONFLICT", "BLOCKED")
PAUSED = ("PAUSED_RESOURCE_CONFLICT", "PAUSED_MAINTENANCE")
CLOSED = ("TERMINAL",)

REQUIRED_FIELDS = (
    "cycle_id", "asset", "plan", "lifecycle", "phase", "integration_worktree",
    "branch", "head", "budget", "denominators", "s0", "s1", "go_phrase",
    "go_phrase_state", "workers", "active_heavy", "lock", "heartbeat_utc",
    "hard_stop_reason", "pause_packet", "next_authorized_action", "updated_at_utc",
)

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class CycleNotFound(KeyError):
    pass


class IllegalTransition(ValueError):
    pass


def _fail(msg: str):
    raise atomic_io.SchemaValidationError(f"cycle_registry@1: {msg}")


def validate_registry(obj: dict) -> None:
    if obj.get("schema") != SCHEMA_ID:
        _fail(f"schema must be {SCHEMA_ID}, got {obj.get('schema')!r}")
    if not isinstance(obj.get("cycles"), list) or not obj["cycles"]:
        _fail("cycles must be a non-empty list")
    seen = set()
    for rec in obj["cycles"]:
        if not isinstance(rec, dict):
            _fail("cycle record must be an object")
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            _fail(f"{rec.get('cycle_id', '?')}: missing fields {missing}")
        cid = rec["cycle_id"]
        if cid in seen:
            _fail(f"duplicate cycle_id {cid}")
        seen.add(cid)
        if rec["lifecycle"] not in LIFECYCLE:
            _fail(f"{cid}: illegal lifecycle {rec['lifecycle']!r}")
        if rec["lifecycle"] == "PAUSED_MAINTENANCE" and not rec.get("hard_stop_reason"):
            _fail(f"{cid}: PAUSED_MAINTENANCE requires hard_stop_reason")
        if rec["lifecycle"] == "TERMINAL" and rec.get("hard_stop_reason"):
            pass  # allowed: a cycle may close while a maintenance stop is on record
        if not _HEX40.match(rec.get("head", "") or ""):
            _fail(f"{cid}: head must be a 40-hex sha, got {rec.get('head')!r}")
        budget = rec.get("budget")
        if not (isinstance(budget, dict) and isinstance(budget.get("used"), int)
                and isinstance(budget.get("max"), int) and budget["max"] >= 0
                and 0 <= budget["used"] <= budget["max"]):
            _fail(f"{cid}: budget must be {{used:int<=max:int}}")
        if not (isinstance(rec.get("denominators"), dict) and rec["denominators"]):
            _fail(f"{cid}: denominators must be a non-empty object")
        if rec.get("s1") != "SEALED_UNTOUCHED" and rec["lifecycle"] != "TERMINAL":
            _fail(f"{cid}: s1 must be SEALED_UNTOUCHED outside TERMINAL")
        if not _UTC.match(rec.get("updated_at_utc", "")):
            _fail(f"{cid}: updated_at_utc must be UTC ISO8601 Z-form")
        hb = rec.get("heartbeat_utc", "") or ""
        if hb and not _UTC.match(hb):
            _fail(f"{cid}: heartbeat_utc must be UTC ISO8601 Z-form")
        if not hb and rec["lifecycle"] not in CLOSED:
            _fail(f"{cid}: non-terminal cycle requires a heartbeat_utc")
    top = ["schema", "updated_at_utc", "writer", "write_token", "cycles"]
    for f in top:
        if f not in obj:
            _fail(f"missing top-level field {f}")


def load(path: os.PathLike | str) -> dict:
    return atomic_io.load_json_strict(path, schema_validator=validate_registry)


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save(path: os.PathLike | str, registry: dict, *, expect_prev_sha: Optional[str] = None) -> str:
    """Transactional registry write; appends the transition event journal."""
    new_sha = atomic_io.atomic_write_json(
        path, registry, schema_validator=validate_registry, expect_prev_sha=expect_prev_sha
    )
    atomic_io.append_event(Path(path).parent / Path(EVENTS_REL).name, {
        "event": "REGISTRY_SAVED",
        "writer": registry.get("writer"),
        "write_token": registry.get("write_token"),
        "content_sha256": new_sha,
        "cycles": [c["cycle_id"] + ":" + c["lifecycle"] for c in registry["cycles"]],
    })
    return new_sha


def resolve(registry: dict, cycle_id: str) -> dict:
    """Exact-record resolution. Never guesses from worktree existence."""
    for rec in registry["cycles"]:
        if rec["cycle_id"] == cycle_id:
            return rec
    raise CycleNotFound(cycle_id)


def active_cycles(registry: dict) -> list:
    return [c for c in registry["cycles"] if c["lifecycle"] in DISPATCHABLE or c["lifecycle"] in PAUSED]


def closed_cycles(registry: dict) -> list:
    return [c for c in registry["cycles"] if c["lifecycle"] in CLOSED]


ALLOWED_TRANSITIONS = {
    "PLANNED_NOT_STARTED": {"ACTIVE_LIGHT", "ACTIVE_HEAVY", "BLOCKED", "TERMINAL"},
    "ACTIVE_LIGHT": {"ACTIVE_HEAVY", "PAUSED_RESOURCE_CONFLICT", "PAUSED_MAINTENANCE", "BLOCKED", "TERMINAL"},
    "ACTIVE_HEAVY": {"ACTIVE_LIGHT", "PAUSED_RESOURCE_CONFLICT", "PAUSED_MAINTENANCE", "BLOCKED", "TERMINAL"},
    "PAUSED_RESOURCE_CONFLICT": {"ACTIVE_LIGHT", "ACTIVE_HEAVY", "PAUSED_MAINTENANCE", "TERMINAL"},
    "PAUSED_MAINTENANCE": {"ACTIVE_LIGHT", "ACTIVE_HEAVY", "TERMINAL"},
    "BLOCKED": {"ACTIVE_LIGHT", "ACTIVE_HEAVY", "PAUSED_MAINTENANCE", "TERMINAL"},
    "TERMINAL": set(),  # history is append-only: a closed cycle never re-opens
}


def transition(registry: dict, cycle_id: str, new_lifecycle: str, *, reason: str,
               hard_stop_reason: Optional[str] = None) -> dict:
    rec = resolve(registry, cycle_id)
    if new_lifecycle not in ALLOWED_TRANSITIONS[rec["lifecycle"]]:
        raise IllegalTransition(
            f"{cycle_id}: {rec['lifecycle']} -> {new_lifecycle} is not an allowed transition"
        )
    if new_lifecycle == "PAUSED_MAINTENANCE" and not hard_stop_reason:
        raise IllegalTransition("PAUSED_MAINTENANCE requires hard_stop_reason")
    rec["lifecycle"] = new_lifecycle
    rec["hard_stop_reason"] = hard_stop_reason if new_lifecycle in PAUSED else (
        rec.get("hard_stop_reason") if new_lifecycle != "ACTIVE_LIGHT" and new_lifecycle != "ACTIVE_HEAVY" else None
    )
    rec["updated_at_utc"] = now_utc()
    registry["updated_at_utc"] = rec["updated_at_utc"]
    if registry.get("write_token") is not None:
        registry["write_token"] = f"transition:{cycle_id}->{new_lifecycle}:{reason[:80]}"
    return rec
