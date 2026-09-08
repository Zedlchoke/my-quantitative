"""SHV1 G1 - canonical registry truth (tests/test_cycle_registry.py).

The committed plans/CYCLE_REGISTRY.json must resolve the exact measured cycle
authorities; closed cycles must never appear dispatchable. All mutation-path
tests run on sandbox fixtures.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import atomic_io, cycle_registry  # noqa: E402

REGISTRY = Path(__file__).resolve().parents[1] / "plans" / "CYCLE_REGISTRY.json"


def test_canonical_registry_resolves_exact_cycles():
    reg = cycle_registry.load(REGISTRY)
    v17 = cycle_registry.resolve(reg, "CRYPTO-V17")
    assert v17["lifecycle"] == "PAUSED_MAINTENANCE"
    assert v17["branch"] == "orca/v17-integration"
    assert v17["head"] == "41de5c9e9aedb80610f55fc2fca6b7b61c5bf90f"
    assert v17["integration_worktree"].endswith(".worktrees/crypto/v17/integration")
    assert v17["budget"] == {"used": 0, "max": 6}
    assert v17["hard_stop_reason"] == "SYSTEM_HARDENING_V1"
    v8 = cycle_registry.resolve(reg, "FOREX-FREE-V8")
    assert v8["lifecycle"] == "PAUSED_MAINTENANCE"
    assert v8["head"] == "94e78f6df55af52735bb6ebfb53fd4e3b412568d"
    v12 = cycle_registry.resolve(reg, "STOCKS-FREE-V12")
    assert v12["lifecycle"] == "TERMINAL"
    assert v12["head"] == "5a9b42d148a483766ef4e6bd4827b2c6102524f0"
    assert v12["next_authorized_action"].startswith("NONE (closed")
    # resolution is exact: a name that is not in the registry raises - never a guess
    with pytest.raises(cycle_registry.CycleNotFound):
        cycle_registry.resolve(reg, "CRYPTO-V18")
    with pytest.raises(cycle_registry.CycleNotFound):
        cycle_registry.resolve(reg, "stocks-free-v12")  # case-sensitive exact ids


def test_closed_cycles_cannot_appear_active():
    reg = cycle_registry.load(REGISTRY)
    closed_ids = {c["cycle_id"] for c in cycle_registry.closed_cycles(reg)}
    assert {"STOCKS-FREE-V12", "CRYPTO-V16", "STOCKS-V11", "FOREX-FREE-V7"} <= closed_ids
    active_ids = {c["cycle_id"] for c in cycle_registry.active_cycles(reg)}
    assert active_ids == {"CRYPTO-V17", "FOREX-FREE-V8"}
    for rec in reg["cycles"]:
        if rec["lifecycle"] in cycle_registry.CLOSED:
            assert rec["go_phrase_state"].startswith("DEAD"), \
                f"closed {rec['cycle_id']} GO phrase must be DEAD (P-8: no GO survives its close)"
            assert rec["next_authorized_action"].startswith("NONE")


def test_paused_maintenance_requires_hard_stop_reason():
    reg = cycle_registry.load(REGISTRY)
    for rec in reg["cycles"]:
        if rec["lifecycle"] == "PAUSED_MAINTENANCE":
            assert rec["hard_stop_reason"] == "SYSTEM_HARDENING_V1"
            assert rec["pause_packet"], "paused cycle must name its pause packet"


def _minimal_registry():
    return {
        "schema": cycle_registry.SCHEMA_ID,
        "updated_at_utc": "2026-09-08T00:00:00Z",
        "writer": "test",
        "write_token": None,
        "cycles": [{
            "cycle_id": "TEST-C1", "asset": "crypto", "plan": "plans/PLAN_test.md",
            "lifecycle": "ACTIVE_LIGHT", "phase": "P0",
            "integration_worktree": "/tmp/x", "branch": "orca/x",
            "head": "a" * 40, "budget": {"used": 0, "max": 1},
            "denominators": {"asset_published": 0, "asset_observed": 0},
            "s0": "OPEN", "s1": "SEALED_UNTOUCHED", "go_phrase": "",
            "go_phrase_state": "", "workers": 0, "active_heavy": False,
            "lock": "free", "heartbeat_utc": "2026-09-08T00:00:00Z",
            "hard_stop_reason": None, "pause_packet": None,
            "next_authorized_action": "", "updated_at_utc": "2026-09-08T00:00:00Z",
        }],
    }


def test_terminal_is_absorbing_closed_never_reopens():
    reg = _minimal_registry()
    reg["cycles"][0]["lifecycle"] = "TERMINAL"
    with pytest.raises(cycle_registry.IllegalTransition):
        cycle_registry.transition(reg, "TEST-C1", "ACTIVE_LIGHT", reason="rescue")


def test_pause_transition_requires_hard_stop_reason_and_journals(tmp_path):
    p = tmp_path / "CYCLE_REGISTRY.json"
    reg = _minimal_registry()
    cycle_registry.save(p, reg)
    stored = cycle_registry.load(p)
    with pytest.raises(cycle_registry.IllegalTransition):
        cycle_registry.transition(stored, "TEST-C1", "PAUSED_MAINTENANCE", reason="x")
    cycle_registry.transition(stored, "TEST-C1", "PAUSED_MAINTENANCE",
                              reason="maintenance", hard_stop_reason="SYSTEM_HARDENING_V1")
    cycle_registry.save(p, stored, expect_prev_sha=atomic_io.sha256_file(p))
    events = atomic_io.read_events(tmp_path / "CYCLE_REGISTRY.events.jsonl")
    assert events and events[-1]["event"] == "REGISTRY_SAVED"
    assert "TEST-C1:PAUSED_MAINTENANCE" in events[-1]["cycles"]


def test_validator_rejects_drifted_shapes():
    bad = _minimal_registry()
    bad["schema"] = "cycle_registry@0"
    with pytest.raises(atomic_io.SchemaValidationError):
        cycle_registry.validate_registry(bad)
    bad = _minimal_registry()
    bad["cycles"][0]["head"] = "not-a-sha"
    with pytest.raises(atomic_io.SchemaValidationError):
        cycle_registry.validate_registry(bad)
    bad = _minimal_registry()
    bad["cycles"][0]["budget"] = {"used": 5, "max": 1}
    with pytest.raises(atomic_io.SchemaValidationError):
        cycle_registry.validate_registry(bad)
    bad = _minimal_registry()
    bad["cycles"][0]["s1"] = "OPENED"
    with pytest.raises(atomic_io.SchemaValidationError):
        cycle_registry.validate_registry(bad)


def test_load_fails_closed_on_truncated_registry(tmp_path):
    p = tmp_path / "CYCLE_REGISTRY.json"
    p.write_text('{"schema": "cycle_registry@1", "cycl')
    with pytest.raises(atomic_io.ControlStateDrift):
        cycle_registry.load(p)
