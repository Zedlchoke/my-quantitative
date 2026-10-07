"""Canonical active-cycle registry, schema cycle_registry@1 (SHV1 sec7.2).

plans/CYCLE_REGISTRY.json is the ONLY writable cycle authority. Legacy cycle
state files and the committed projection plans/ACTIVE_CYCLES.json are read
through legacy_adapters and never rewritten (G6). Writers emit this schema
only; readers refuse malformed state (fail closed, never repair).

PAUSED_MAINTENANCE is introduced by this versioned schema per SHV1 sec4; it
never appears in legacy records.

MDP-V1 M0 additions (PLAN_market_data_plane_v1 sec3.2):
- plans/ACTIVE_CYCLES.json is a GENERATED PROJECTION of the canonical
  NON-TERMINAL records, produced only by :func:`write_projection` (called by
  every registry-mutating write via :func:`save`). It is never hand-edited;
  a hand edit is projection drift, detected by :func:`projection_matches`
  and by doctor — recorded, never silently accepted.
- :func:`register_cycle` / :func:`update_cycle` / :func:`reconcile_registry`
  give register / measured-HEAD-update / reconciliation workflows the SAME
  atomic CAS + append-only journal path as pause/resume. History is never
  normalized: every change is recorded as a journal event.
- A transition to TERMINAL kills the cycle's GO phrase state (P-8: no GO
  survives its cycle's close) — the terminal-GO-death invariant is enforced
  by the writer, not by convention.

MDP-V2R1 A4 addition (PLAN_market_data_plane_v2r1 §12):
- :func:`declare_terminal_identity` writes the additive TERMINAL_ANCHOR
  semantics onto a TERMINAL row through the SAME atomic CAS + journal path
  (event TERMINAL_IDENTITY_DECLARED). The fields are additive: rows without
  them stay valid legacy rows and validate_registry accepts both shapes.
  Once declared the identity is immutable; an identical re-declaration is an
  idempotent no-op (no write, no journal event).
- :func:`redeclare_terminal_identity` is the ONE sanctioned way to move an
  already-declared row to a new anchor (A4-r2): FORWARD-ONLY migration — the
  old anchor must be a git ancestor of the new one — updating head and
  terminal_anchor_sha together (event TERMINAL_IDENTITY_REDECLARED). An
  identical re-declaration is a no-op; backward or unrelated moves are
  refused. Validation never causes a migration, so a repin loop is
  structurally impossible.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from governance import atomic_io, terminal_identity

SCHEMA_ID = "cycle_registry@1"
REGISTRY_REL = "plans/CYCLE_REGISTRY.json"
EVENTS_REL = "plans/CYCLE_REGISTRY.events.jsonl"
PROJECTION_SCHEMA = "active_cycles_projection@1"
PROJECTION_REL = "plans/ACTIVE_CYCLES.json"

UNMEASURED_HEAD = "0" * 40  # placeholder for a planned cycle with no measured branch yet

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


def save(path: os.PathLike | str, registry: dict, *, expect_prev_sha: Optional[str] = None,
         with_projection: bool = True) -> str:
    """Transactional registry write; appends the transition event journal.

    M0: every registry write regenerates plans/ACTIVE_CYCLES.json as the
    deterministic projection of the canonical NON-TERMINAL records, so the
    projection can only ever be produced by this writer.
    """
    new_sha = atomic_io.atomic_write_json(
        path, registry, schema_validator=validate_registry, expect_prev_sha=expect_prev_sha
    )
    projection_sha = None
    if with_projection:
        projection_sha = write_projection(path, registry)
    atomic_io.append_event(Path(path).parent / Path(EVENTS_REL).name, {
        "event": "REGISTRY_SAVED",
        "writer": registry.get("writer"),
        "write_token": registry.get("write_token"),
        "content_sha256": new_sha,
        "projection_sha256": projection_sha,
        "cycles": [c["cycle_id"] + ":" + c["lifecycle"] for c in registry["cycles"]],
    })
    return new_sha


def resolve(registry: dict, cycle_id: str) -> dict:
    """Exact-record resolution. Never guesses from worktree existence."""
    for rec in registry["cycles"]:
        if rec["cycle_id"] == cycle_id:
            return rec
    raise CycleNotFound(cycle_id)


# ------------------------------------------------------------- projection (M0)
PROJECTION_ROW_FIELDS = (
    "cycle_id", "asset", "plan", "lifecycle", "phase", "worktree", "branch",
    "head", "budget", "s1", "go_phrase_state", "next_authorized_action",
    "updated_at_utc",
)

PROJECTION_HEADER = (
    "GENERATED PROJECTION — deterministic function of the canonical NON-TERMINAL "
    "records in plans/CYCLE_REGISTRY.json (schema cycle_registry@1). Produced "
    "ONLY by governance.cycle_registry.write_projection on every registry-mutating "
    "command. DO NOT hand-edit: a hand edit is projection drift, detected by "
    "projection_matches()/cycle reconcile and reported by cycle doctor. Terminal "
    "cycles are historical evidence and never appear here."
)


def build_projection(registry: dict) -> dict:
    """The ONE deterministic projection of canonical non-terminal records.

    Deterministic: rows sorted by cycle_id, no wall-clock timestamps — the
    only time field is the source registry's own updated_at_utc, so two
    regenerations from the same registry content are byte-identical.
    """
    rows = []
    for rec in registry["cycles"]:
        if rec["lifecycle"] in CLOSED:
            continue
        rows.append({
            "cycle_id": rec["cycle_id"],
            "asset": rec["asset"],
            "plan": rec["plan"],
            "lifecycle": rec["lifecycle"],
            "phase": rec["phase"],
            "worktree": rec.get("integration_worktree") or "",
            "branch": rec["branch"],
            "head": rec["head"],
            "budget": {"used": rec["budget"]["used"], "max": rec["budget"]["max"]},
            "s1": rec["s1"],
            "go_phrase_state": rec["go_phrase_state"],
            "next_authorized_action": rec.get("next_authorized_action", ""),
            "updated_at_utc": rec["updated_at_utc"],
        })
    rows.sort(key=lambda r: r["cycle_id"])
    return {
        "schema": PROJECTION_SCHEMA,
        "header": PROJECTION_HEADER,
        "source_registry": REGISTRY_REL,
        "generated_from_registry_updated_at_utc": registry.get("updated_at_utc", ""),
        "cycles": rows,
    }


def projection_bytes(registry: dict) -> bytes:
    return atomic_io.canonical_bytes(build_projection(registry))


def validate_projection(obj: dict) -> None:
    if obj.get("schema") != PROJECTION_SCHEMA:
        _fail(f"projection schema must be {PROJECTION_SCHEMA}, got {obj.get('schema')!r}")
    if not isinstance(obj.get("cycles"), list):
        _fail("projection cycles must be a list")
    for row in obj["cycles"]:
        if not isinstance(row, dict):
            _fail("projection row must be an object")
        missing = [f for f in PROJECTION_ROW_FIELDS if f not in row]
        if missing:
            _fail(f"projection row {row.get('cycle_id', '?')}: missing fields {missing}")
        if row.get("lifecycle") not in LIFECYCLE:
            _fail(f"projection row {row.get('cycle_id', '?')}: illegal lifecycle")
        if row.get("lifecycle") in CLOSED:
            _fail(f"projection must never carry a terminal cycle ({row.get('cycle_id')})")


def projection_matches(registry: dict, actual_bytes: bytes) -> bool:
    """True iff actual_bytes is exactly what this writer would regenerate."""
    return actual_bytes == projection_bytes(registry)


def write_projection(registry_path: os.PathLike | str, registry: dict) -> str:
    """Regenerate ACTIVE_CYCLES.json next to the registry; returns its sha256."""
    proj_path = Path(registry_path).parent / Path(PROJECTION_REL).name
    return atomic_io.atomic_write_json(
        proj_path, build_projection(registry), schema_validator=validate_projection
    )


def projection_drift(registry_path: os.PathLike | str, registry: dict) -> Optional[str]:
    """Describe projection drift for the report, or None when bytes match."""
    proj_path = Path(registry_path).parent / Path(PROJECTION_REL).name
    if not proj_path.exists():
        return "projection file missing (regenerable by the registry writer)"
    actual = proj_path.read_bytes()
    if projection_matches(registry, actual):
        return None
    try:
        parsed = json.loads(actual.decode("utf-8"))
        shape = parsed.get("schema", "unknown")
    except (UnicodeDecodeError, json.JSONDecodeError):
        shape = "unparseable"
    return (f"projection bytes differ from regeneration (file schema/shape: {shape}; "
            "hand edits and stale hand-shaped files are drift, never silently accepted)")


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
    if new_lifecycle == "TERMINAL" and not str(rec.get("go_phrase_state", "")).startswith("DEAD"):
        # terminal-GO-death invariant (P-8 / RULES §7): no GO phrase survives
        # its cycle's close — enforced by the writer, not by convention.
        rec["go_phrase_state"] = "DEAD (consumed or extinguished at its cycle's close per P-8 / RULES §7)"
    rec["updated_at_utc"] = now_utc()
    registry["updated_at_utc"] = rec["updated_at_utc"]
    if registry.get("write_token") is not None:
        registry["write_token"] = f"transition:{cycle_id}->{new_lifecycle}:{reason[:80]}"
    return rec


# ------------------------------------------- register / update / reconcile (M0)
REGISTERABLE_LIFECYCLES = ("PLANNED_NOT_STARTED", "ACTIVE_LIGHT", "BLOCKED")


def journal_event(path: os.PathLike | str, event: dict) -> None:
    """Typed append-only event next to the registry (same journal as save)."""
    atomic_io.append_event(Path(path).parent / Path(EVENTS_REL).name, event)


def register_cycle(path: os.PathLike | str, registry: dict, *, prev_sha: Optional[str],
                   cycle_id: str, plan: str, branch: str, head: Optional[str] = None,
                   lifecycle: str = "PLANNED_NOT_STARTED", asset: str = "",
                   worktree: str = "", budget_max: int = 6, go_phrase: str = "",
                   reason: str = "register") -> tuple:
    """Register a NEW planned cycle through the atomic CAS + journal path.

    Fails closed (no write) on: duplicate cycle_id, illegal lifecycle
    (TERMINAL is a history state, never a registration state), malformed
    head sha, or a CAS loss against a concurrent writer. The projection is
    regenerated by save(). Returns (record, new_registry_sha256).
    """
    try:
        resolve(registry, cycle_id)
    except CycleNotFound:
        pass
    else:
        raise ValueError(
            f"cycle_registry@1: {cycle_id} is already registered — register is for NEW "
            "cycles only (use cycle update for measured HEAD/lifecycle changes)"
        )
    if lifecycle not in REGISTERABLE_LIFECYCLES:
        raise IllegalTransition(
            f"register: lifecycle must be one of {REGISTERABLE_LIFECYCLES}, got {lifecycle!r} "
            "(TERMINAL is a history state, never a registration state)"
        )
    if not asset:
        raise ValueError("register: asset is required (or derivable by the caller)")
    if head is not None and not _HEX40.match(head):
        raise ValueError(f"register: head must be a 40-hex sha or omitted, got {head!r}")
    now = now_utc()
    rec = {
        "cycle_id": cycle_id,
        "asset": asset,
        "plan": plan,
        "lifecycle": lifecycle,
        "phase": "REGISTERED (planned)" if lifecycle == "PLANNED_NOT_STARTED" else "REGISTERED",
        "integration_worktree": worktree,
        "branch": branch,
        "head": head or UNMEASURED_HEAD,
        "budget": {"used": 0, "max": int(budget_max)},
        "denominators": {"note": "see HYPOTHESIS_LEDGER.md (P-9)"},
        "s0": "OPEN",
        "s1": "SEALED_UNTOUCHED",
        "go_phrase": go_phrase,
        "go_phrase_state": ("REGISTERED_NOT_CONSUMED" if go_phrase
                            else "NOT_REGISTERED (P-8: a GO is typed only at the cycle's own gate)"),
        "workers": 0,
        "active_heavy": False,
        "lock": "machine-wide heavy lock (see researchctl locks inspect)",
        "heartbeat_utc": now,
        "hard_stop_reason": None,
        "pause_packet": None,
        "next_authorized_action": "",
        "updated_at_utc": now,
        "adapter_warnings": [],
    }
    registry["cycles"].append(rec)
    registry["updated_at_utc"] = now
    registry["write_token"] = f"register:{cycle_id}:{reason[:60]}"
    new_sha = save(path, registry, expect_prev_sha=prev_sha)
    journal_event(path, {
        "event": "CYCLE_REGISTERED",
        "cycle_id": cycle_id,
        "lifecycle": lifecycle,
        "branch": branch,
        "head": rec["head"],
        "plan": plan,
        "reason": reason,
    })
    return rec, new_sha


def update_cycle(path: os.PathLike | str, registry: dict, *, prev_sha: Optional[str],
                 cycle_id: str, head: Optional[str] = None, lifecycle: Optional[str] = None,
                 phase: Optional[str] = None, workers: Optional[int] = None,
                 active_heavy: Optional[bool] = None, worktree: Optional[str] = None,
                 budget_used: Optional[int] = None,
                 reason: str = "update") -> tuple:
    """Update a cycle's measured HEAD and/or lifecycle atomically.

    Touches ONLY the requested fields (+ updated_at_utc bookkeeping); never
    rewrites any other field. A no-op (same head, no lifecycle change)
    writes nothing. Every applied change is recorded as a CYCLE_UPDATED
    journal event — drift is recorded, never normalized silently.
    Returns (changes, new_registry_sha256).
    """
    rec = resolve(registry, cycle_id)
    if head is None and lifecycle is None and phase is None \
            and workers is None and active_heavy is None and worktree is None \
            and budget_used is None:
        raise ValueError("update: nothing to do (pass --head and/or --lifecycle)")
    if head is not None and not _HEX40.match(head):
        raise ValueError(f"update: head must be a 40-hex sha, got {head!r}")
    if workers is not None and (not isinstance(workers, int) or workers < 0):
        raise ValueError(f"update: workers must be a non-negative int, got {workers!r}")
    if budget_used is not None and (not isinstance(budget_used, int) or budget_used < 0):
        raise ValueError(f"update: budget_used must be a non-negative int, got {budget_used!r}")
    if worktree:  # non-empty bind must be a real absolute directory; "" stays legal (planned placeholder)
        if not os.path.isabs(worktree) or not os.path.isdir(worktree):
            raise ValueError(
                f"update: worktree must be an absolute path to an existing directory, got {worktree!r}")
    changes = []
    if head is not None and head != rec["head"]:
        changes.append({"cycle_id": cycle_id, "field": "head",
                        "from": rec["head"], "to": head})
        rec["head"] = head
    if phase is not None and phase != rec.get("phase"):
        changes.append({"cycle_id": cycle_id, "field": "phase",
                        "from": rec.get("phase"), "to": phase})
        rec["phase"] = phase
    if workers is not None and workers != rec.get("workers", 0):
        changes.append({"cycle_id": cycle_id, "field": "workers",
                        "from": rec.get("workers", 0), "to": workers})
        rec["workers"] = workers
    if active_heavy is not None and active_heavy != rec.get("active_heavy", False):
        changes.append({"cycle_id": cycle_id, "field": "active_heavy",
                        "from": rec.get("active_heavy", False), "to": active_heavy})
        rec["active_heavy"] = active_heavy
    if worktree is not None and worktree != rec.get("integration_worktree", ""):
        changes.append({"cycle_id": cycle_id, "field": "integration_worktree",
                        "from": rec.get("integration_worktree", ""), "to": worktree})
        rec["integration_worktree"] = worktree
    if budget_used is not None and budget_used != rec["budget"]["used"]:
        if budget_used > rec["budget"]["max"]:
            raise ValueError(
                f"update: budget_used {budget_used} exceeds budget max {rec['budget']['max']}")
        changes.append({"cycle_id": cycle_id, "field": "budget.used",
                        "from": rec["budget"]["used"], "to": budget_used})
        rec["budget"]["used"] = budget_used
    if lifecycle is not None and lifecycle != rec["lifecycle"]:
        prev_lifecycle = rec["lifecycle"]
        transition(registry, cycle_id, lifecycle, reason=reason)
        changes.append({"cycle_id": cycle_id, "field": "lifecycle",
                        "from": prev_lifecycle, "to": lifecycle})
    if not changes:
        return [], atomic_io.sha256_file(path)
    rec["updated_at_utc"] = now_utc()
    registry["updated_at_utc"] = rec["updated_at_utc"]
    registry["write_token"] = f"update:{cycle_id}:{reason[:60]}"
    new_sha = save(path, registry, expect_prev_sha=prev_sha)
    for change in changes:
        journal_event(path, dict(change, event="CYCLE_UPDATED", reason=reason))
    return changes, new_sha


def plan_reconciliation(registry: dict, measured_heads: dict) -> dict:
    """Pure diff: canonical registry vs measured branch heads + projection.

    Returns the planned head changes WITHOUT touching anything. Cycles with
    no measured head (no worktree / unmeasurable branch) are never guessed.
    """
    changes = []
    unmeasured = []
    for rec in registry["cycles"]:
        measured = measured_heads.get(rec["cycle_id"])
        if measured is None:
            unmeasured.append(rec["cycle_id"])
            continue
        if measured != rec["head"] and rec.get("branch"):
            changes.append({"cycle_id": rec["cycle_id"], "field": "head",
                            "from": rec["head"], "to": measured})
    return {"head_changes": changes, "unmeasured": unmeasured}


def reconcile_registry(path: os.PathLike | str, registry: dict, *, prev_sha: Optional[str],
                       measured_heads: dict, reason: str = "reconcile") -> tuple:
    """Apply the reconciliation as ONE CAS save + append-only journal events.

    - head drift -> updated to the measured value, one CYCLE_HEAD_RECONCILED
      event per change (recorded, never silent, history never normalized);
    - projection drift -> the projection is regenerated by save() (or, when
      there are no head changes, directly with a PROJECTION_REGENERATED
      event) — never rewritten by hand;
    - nothing to do -> no write at all.
    Returns (report, new_registry_sha256_or_None).
    """
    plan = plan_reconciliation(registry, measured_heads)
    drift = projection_drift(path, registry)
    report = dict(plan, projection_drift=drift)
    if not plan["head_changes"]:
        if drift:
            proj_sha = write_projection(path, registry)
            journal_event(path, {"event": "PROJECTION_REGENERATED", "reason": reason,
                                 "projection_sha256": proj_sha,
                                 "detail": drift})
            report["projection_sha256"] = proj_sha
            return report, atomic_io.sha256_file(path)
        report["mode"] = "NO_CHANGE"
        return report, None
    for change in plan["head_changes"]:
        resolve(registry, change["cycle_id"])["head"] = change["to"]
    registry["updated_at_utc"] = now_utc()
    registry["write_token"] = f"reconcile:{reason[:60]}"
    new_sha = save(path, registry, expect_prev_sha=prev_sha)
    for change in plan["head_changes"]:
        journal_event(path, dict(change, event="CYCLE_HEAD_RECONCILED", reason=reason))
    report["mode"] = "EXECUTED"
    report["registry_sha256"] = new_sha
    return report, new_sha


# --------------------------------------- declare_terminal_identity (MDP-V2R1)

def declare_terminal_identity(path: os.PathLike | str, registry: dict, *,
                              prev_sha: Optional[str], cycle_id: str,
                              terminal_anchor_sha: str,
                              post_terminal_policy: str = terminal_identity.POST_TERMINAL_POLICY,
                              reason: str = "declare terminal identity") -> tuple:
    """Declare the additive TERMINAL_ANCHOR semantics on a TERMINAL row.

    MDP-V2R1 §12.1: a commit cannot contain its own SHA, so a TERMINAL row
    binds ``head`` to the terminal ANCHOR (the last commit the auditor
    audited) instead of the live branch tip; post-terminal descendants are
    judged by governance.terminal_identity against the frozen allowlist.

    Writes ONLY the three additive fields (+ updated_at_utc bookkeeping)
    through the atomic CAS + journal path; the row's head and every other
    field are never modified here. Fails closed (no write) unless:

    - the row lifecycle is TERMINAL;
    - terminal_anchor_sha is 40-hex AND row head is 40-hex AND they are equal;
    - post_terminal_policy equals the frozen
      ALLOWLISTED_APPEND_ONLY_DESCENDANTS value;
    - the identity is not already declared (an identical re-declaration is
      an idempotent no-op returning (record, current file sha256) with NO
      write and NO journal event; a different re-declaration raises — the
      declared identity is immutable).

    Every applied declaration is recorded as a TERMINAL_IDENTITY_DECLARED
    journal event. Returns (record, new_registry_sha256) — new_registry_sha256
    is the current file sha on the idempotent no-op path.
    """
    rec = resolve(registry, cycle_id)
    if rec["lifecycle"] != "TERMINAL":
        raise ValueError(
            f"declare_terminal_identity: {cycle_id} lifecycle is "
            f"{rec['lifecycle']!r}, TERMINAL required — identity semantics "
            "apply only to closed cycles")
    if not _HEX40.match(terminal_anchor_sha or ""):
        raise ValueError(
            f"declare_terminal_identity: terminal_anchor_sha must be a 40-hex "
            f"sha, got {terminal_anchor_sha!r}")
    if not _HEX40.match(rec.get("head", "") or ""):
        raise ValueError(
            f"declare_terminal_identity: {cycle_id} head "
            f"{rec.get('head')!r} is not a 40-hex sha")
    if rec["head"] != terminal_anchor_sha:
        raise ValueError(
            f"declare_terminal_identity: {cycle_id} head {rec['head']!r} != "
            f"terminal_anchor_sha {terminal_anchor_sha!r} — under "
            f"{terminal_identity.HEAD_SEMANTICS!r} the row head IS the "
            "terminal anchor (re-anchor first via CAS update, never by "
            "hand-editing)")
    if post_terminal_policy != terminal_identity.POST_TERMINAL_POLICY:
        raise ValueError(
            f"declare_terminal_identity: post_terminal_policy must be "
            f"{terminal_identity.POST_TERMINAL_POLICY!r}, got "
            f"{post_terminal_policy!r}")

    wanted = {
        "head_semantics": terminal_identity.HEAD_SEMANTICS,
        "terminal_anchor_sha": terminal_anchor_sha,
        "post_terminal_policy": post_terminal_policy,
    }
    already = {k: rec[k] for k in terminal_identity.IDENTITY_FIELDS if k in rec}
    if already:
        if already == wanted:
            # idempotent re-declaration: no write, no journal event
            return rec, atomic_io.sha256_file(path)
        raise ValueError(
            f"declare_terminal_identity: {cycle_id} already declares terminal "
            f"identity {already} — the declared identity is immutable; "
            "re-declaration with different values is refused")
    rec.update(wanted)
    now = now_utc()
    rec["updated_at_utc"] = now
    registry["updated_at_utc"] = now
    registry["write_token"] = f"declare_terminal_identity:{cycle_id}:{reason[:60]}"
    new_sha = save(path, registry, expect_prev_sha=prev_sha)
    journal_event(path, {
        "event": "TERMINAL_IDENTITY_DECLARED",
        "cycle_id": cycle_id,
        "head": rec["head"],
        "terminal_anchor_sha": terminal_anchor_sha,
        "post_terminal_policy": post_terminal_policy,
        "reason": reason,
    })
    return rec, new_sha


def redeclare_terminal_identity(path: os.PathLike | str, registry: dict, *,
                                prev_sha: Optional[str], cycle_id: str,
                                terminal_anchor_sha: str, repo_root,
                                reason: str = "redeclare terminal anchor") -> tuple:
    """Move an ALREADY-DECLARED terminal row to a new anchor — FORWARD-ONLY.

    MDP-V2R1 A4-r2 (plan §12.2): the cure for a substantive post-anchor
    change inside a cycle's own evidence scope is a NEW anchor after A7
    re-audit, written ONCE through this writer — never by hand-editing the
    registry and never because a validation run demands it. Repin loops are
    structurally impossible: validation is read-only/idempotent and this
    migration can only move FORWARD.

    Allowed ONLY when:

    - the row lifecycle is TERMINAL;
    - the row ALREADY carries a declaration (head_semantics
      TERMINAL_ANCHOR with terminal_anchor_sha present) and its invariant
      head == terminal_anchor_sha still holds;
    - the new terminal_anchor_sha is a 40-hex sha and a DIFFERENT one
      (an identical re-declaration is an idempotent no-op: no write, no
      journal event; returns (record, current file sha256));
    - ``git -C repo_root merge-base --is-ancestor <old_anchor>
      <new_anchor>`` succeeds: the OLD anchor is an ANCESTOR of the new one.
      Backward or unrelated moves raise without writing (this also refuses
      anchors that do not exist under repo_root).

    head and terminal_anchor_sha are updated TOGETHER (they stay bound under
    TERMINAL_ANCHOR semantics); every other field is untouched. The applied
    migration is recorded as a TERMINAL_IDENTITY_REDECLARED journal event
    with from_anchor/to_anchor. Returns (record, new_registry_sha256).
    """
    rec = resolve(registry, cycle_id)
    if rec["lifecycle"] != "TERMINAL":
        raise ValueError(
            f"redeclare_terminal_identity: {cycle_id} lifecycle is "
            f"{rec['lifecycle']!r}, TERMINAL required — identity semantics "
            "apply only to closed cycles")
    old_anchor = rec.get("terminal_anchor_sha")
    if rec.get("head_semantics") != terminal_identity.HEAD_SEMANTICS \
            or not old_anchor:
        raise ValueError(
            f"redeclare_terminal_identity: {cycle_id} carries no "
            f"{terminal_identity.HEAD_SEMANTICS!r} declaration — use "
            "declare_terminal_identity first; only a declared row can "
            "migrate its anchor")
    if not (_HEX40.match(old_anchor) and _HEX40.match(rec.get("head", "") or "")):
        raise ValueError(
            f"redeclare_terminal_identity: {cycle_id} declared identity is "
            f"malformed (head={rec.get('head')!r}, "
            f"terminal_anchor_sha={old_anchor!r})")
    if rec["head"] != old_anchor:
        raise ValueError(
            f"redeclare_terminal_identity: {cycle_id} head {rec['head']!r} != "
            f"terminal_anchor_sha {old_anchor!r} — the declared row is "
            "malformed; fix the row before migrating (never by hand-editing)")
    if not _HEX40.match(terminal_anchor_sha or ""):
        raise ValueError(
            f"redeclare_terminal_identity: terminal_anchor_sha must be a "
            f"40-hex sha, got {terminal_anchor_sha!r}")
    if terminal_anchor_sha == old_anchor:
        # identical redeclare: structurally a no-op (no write, no event)
        return rec, atomic_io.sha256_file(path)
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor",
         old_anchor, terminal_anchor_sha], capture_output=True)
    if proc.returncode != 0:
        raise ValueError(
            f"redeclare_terminal_identity: {cycle_id} forward-only migration "
            f"refused — old anchor {old_anchor} is NOT a git ancestor of the "
            f"proposed anchor {terminal_anchor_sha} under repo_root "
            f"{repo_root} (backward or unrelated moves are never written; "
            "migrations only move forward, plan §12.2)")

    rec["head"] = terminal_anchor_sha
    rec["terminal_anchor_sha"] = terminal_anchor_sha
    now = now_utc()
    rec["updated_at_utc"] = now
    registry["updated_at_utc"] = now
    registry["write_token"] = f"redeclare_terminal_identity:{cycle_id}:{reason[:60]}"
    new_sha = save(path, registry, expect_prev_sha=prev_sha)
    journal_event(path, {
        "event": "TERMINAL_IDENTITY_REDECLARED",
        "cycle_id": cycle_id,
        "from_anchor": old_anchor,
        "to_anchor": terminal_anchor_sha,
        "reason": reason,
    })
    return rec, new_sha
