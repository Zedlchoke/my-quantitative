"""PROPOSAL (T1) — closeout field sync via the sanctioned governance library.

Adds update_closeout_fields(): atomic CAS + append-only journal update of
budget.used and/or s0 ONLY, with validation, mirroring update_cycle's
discipline. NOT wired into researchctl yet — see BLOCKER.md Option 1/2.
Tested against a COPY of the live registry by tests/test_closeout_fields_proposal.py.
"""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

REPO = "/Users/hoangminhlong/my-quantitative"
sys.path.insert(0, os.path.join(REPO, "research"))

from governance import cycle_registry  # noqa: E402


def update_closeout_fields(path, cycle_id, *, budget_used=None, s0=None,
                           reason="closeout-sync", expect_prev_sha=None):
    """CAS update of budget.used and/or s0 for one cycle. Returns changes.

    Validation: budget_used int in [0, budget.max]; s0 in {OPEN, CLOSED}.
    Fails closed (no write) on any violation or CAS mismatch.
    """
    registry = cycle_registry.load(path)
    rec = cycle_registry.resolve(registry, cycle_id)
    changes = []
    if budget_used is not None:
        if not isinstance(budget_used, int) or isinstance(budget_used, bool):
            raise ValueError("budget_used must be an int")
        if not (0 <= budget_used <= int(rec["budget"]["max"])):
            raise ValueError(f"budget_used {budget_used} outside [0, {rec['budget']['max']}]")
        if budget_used != rec["budget"]["used"]:
            changes.append({"cycle_id": cycle_id, "field": "budget.used",
                            "from": rec["budget"]["used"], "to": budget_used})
            rec["budget"]["used"] = budget_used
    if s0 is not None:
        if s0 not in ("OPEN", "CLOSED"):
            raise ValueError("s0 must be OPEN or CLOSED")
        if s0 != rec.get("s0"):
            changes.append({"cycle_id": cycle_id, "field": "s0",
                            "from": rec.get("s0"), "to": s0})
            rec["s0"] = s0
    if not changes:
        return []
    from governance import atomic_io
    prev = expect_prev_sha or atomic_io.sha256_file(path)
    if prev != atomic_io.sha256_file(path):
        raise RuntimeError("CAS mismatch: registry changed since read")
    registry["write_token"] = f"closeout-sync:{cycle_id}:{reason[:80]}"
    new_sha = cycle_registry.save(path, registry, expect_prev_sha=prev)
    for ch in changes:
        cycle_registry.journal_event(path, {"event": "CYCLE_CLOSEOUT_FIELD_SYNC",
                                            "utc": cycle_registry.now_utc(), **ch,
                                            "reason": reason})
    _ = new_sha
    return changes
