"""SHV1 G6 - legacy read adapters never rewrite legacy bytes.

Fixtures replicate the three measured legacy shapes (v17 state_v17.json,
forex state.json, stocks cycle_state.json) including the two H0-recorded head
drifts. A byte-preservation case reads the REAL legacy files through
main_repo_root() and asserts no mutation; it skips (NOT_RUN semantics) when
the main checkout is not present.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import legacy_adapters  # noqa: E402

V17_SHAPE = {
    "schema": "v17_run_artifact_v1", "artifact": "state", "cycle_id": "CRYPTO-V17",
    "status": "ACTIVE_LIGHT", "phase": "P0_ACTIVE",
    "updated_utc": "2026-09-08T04:22:06Z", "head": "0" * 40,  # stale (drift)
    "budget_used": 0, "budget_max": 6,
    "go_phrase": "GO CRYPTO V17 SCORED EXECUTION", "go_state": "NOT_PRESENT",
    "s1": "SEALED_UNTOUCHED", "workers": 0, "active_heavy": False,
    "hard_stop_reason": "SYSTEM_HARDENING_V1",  # applied additively at H0 pause
    "next_safe_action": "full build attempt 3",
}

V8_SHAPE = {
    "schema": "forex_free_v8_cycle_state_v1", "cycle_id": "FOREX-FREE-V8",
    "updated_at_utc": "2026-09-08T08:00:00Z", "head": "kernel inheritance merge 210fa01",
    "phase": "D2_COMPLETE + SELECTION FROZEN",
    "budget": {"planned": 6, "used": 0, "bound_by_selection": 3},
    "s1": "SEALED_UNTOUCHED", "hard_stop_reason": "SYSTEM_HARDENING_V1",
}

V12_SHAPE = {
    "schema": "stocks_free_v12_run/cycle_state@1", "cycle": "STOCKS-FREE-V12",
    "status": "TERMINAL", "phase": "CLOSED_A7_CONFIRMED",
    "updated_at_utc": "2026-09-08T01:03:29Z", "head": "5" * 40,
    "budget_used": 0, "budget_max": 6, "s1": "SEALED_UNTOUCHED", "survivors": 0,
}


def test_v17_adapter_paused_with_stale_head_warning():
    rec = legacy_adapters.normalize_legacy_state(
        "CRYPTO-V17", dict(V17_SHAPE), measured_branch_head="a" * 40)
    assert rec["lifecycle"] == "PAUSED_MAINTENANCE"
    assert rec["head"] == "a" * 40  # measured authority, not the stale field
    assert rec["budget"] == {"used": 0, "max": 6}
    assert any("stale" in w for w in rec["adapter_warnings"])


def test_v8_adapter_no_status_field_prose_head():
    rec = legacy_adapters.normalize_legacy_state(
        "FOREX-FREE-V8", dict(V8_SHAPE), measured_branch_head="b" * 40)
    assert rec["lifecycle"] == "PAUSED_MAINTENANCE"  # derived from hard_stop_reason
    assert rec["budget"]["used"] == 0 and rec["budget"]["max"] == 6
    assert rec["budget"]["bound_by_selection"] == 3
    assert any("prose" in w for w in rec["adapter_warnings"])


def test_v12_adapter_terminal():
    rec = legacy_adapters.normalize_legacy_state(
        "STOCKS-FREE-V12", dict(V12_SHAPE), measured_branch_head="c" * 40)
    assert rec["lifecycle"] == "TERMINAL"
    assert rec["next_authorized_action"].startswith("NONE (closed")
    assert rec["s1"] == "SEALED_UNTOUCHED"


def test_unknown_cycle_id_rejected():
    with pytest.raises(KeyError):
        legacy_adapters.normalize_legacy_state("CRYPTO-V99", {})


def test_adapter_without_hard_stop_maps_status():
    s = dict(V17_SHAPE)
    s.pop("hard_stop_reason", None)
    s["hard_stop_reason"] = None
    # v17 fixture has no hard_stop_reason key by default; rebuild explicitly
    s = {k: v for k, v in V17_SHAPE.items() if k != "hard_stop_reason"}
    rec = legacy_adapters.normalize_legacy_state("CRYPTO-V17", s, measured_branch_head="a" * 40)
    assert rec["lifecycle"] == "ACTIVE_LIGHT"  # retained, no invented status


def test_real_legacy_files_are_read_without_byte_mutation():
    root = legacy_adapters.main_repo_root()
    before = {rel: legacy_adapters.file_sha256(root / rel)
              for rel in legacy_adapters.LEGACY_SOURCES.values()}
    heads = {"CRYPTO-V17": "a" * 40, "FOREX-FREE-V8": "b" * 40, "STOCKS-FREE-V12": "c" * 40}
    reg = legacy_adapters.build_registry_from_legacy(heads)
    assert len(reg["cycles"]) == 6
    after = {rel: legacy_adapters.file_sha256(root / rel)
             for rel in legacy_adapters.LEGACY_SOURCES.values()}
    assert before == after, "legacy state files were mutated by a read path"


def test_registry_composition_validates_and_carries_warnings():
    reg = legacy_adapters.build_registry_from_legacy(
        {"CRYPTO-V17": "a" * 40, "FOREX-FREE-V8": "b" * 40, "STOCKS-FREE-V12": "c" * 40})
    from governance import cycle_registry
    cycle_registry.validate_registry(reg)
    warnings = [w for c in reg["cycles"] for w in c.get("adapter_warnings", [])]
    assert len(warnings) >= 2, "the two H0-recorded head drifts must surface as warnings"
