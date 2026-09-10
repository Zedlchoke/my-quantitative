"""SHV1 G6 - legacy read adapters never rewrite legacy bytes.

The byte-preservation and composition cases run HERMETICALLY against COMMITTED
synthetic fixture replicas of the measured legacy shapes under
tests/fixtures/legacy_adapters/ (injected via build_registry_from_legacy's
source_paths / source_root) — no real worktree path, no skip, no network.
Unit cases below replicate the three measured legacy shapes (v17
state_v17.json, forex state.json open + closed, stocks cycle_state.json)
including the two H0-recorded head drifts.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import legacy_adapters  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "legacy_adapters"

# committed synthetic replicas of LEGACY_SOURCES (class SYNTHETIC_HAND_COMPUTED,
# digests pinned in tests/fixtures/governance_fixture_manifest.json)
FIXTURE_SOURCES = {
    "CRYPTO-V17": FIXTURE_DIR / "v17_state.json",
    "FOREX-FREE-V8": FIXTURE_DIR / "forex_v8_state.json",
    "STOCKS-FREE-V12": FIXTURE_DIR / "stocks_v12_cycle_state.json",
}
# measured 2026-09-09: the V8 legacy state closed (REJECT_ALL at its terminal
# gate); this replica carries NO status field — closure is recorded in the phase.
FIXTURE_SOURCES_V8_CLOSED = dict(
    FIXTURE_SOURCES, **{"FOREX-FREE-V8": FIXTURE_DIR / "forex_v8_state_closed.json"}
)
ALL_FIXTURE_FILES = tuple(sorted(FIXTURE_DIR.glob("*.json")))

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

# measured 2026-09-09: the V8 legacy state closed (REJECT_ALL at its terminal
# gate). The file carries NO status field; closure is recorded in the phase.
V8_CLOSED_SHAPE = {
    "schema": "forex_free_v8_cycle_state_v1", "cycle_id": "FOREX-FREE-V8",
    "updated_at_utc": "2026-09-09T05:10:00Z",
    "head": "d" * 40,
    "phase": "CLOSED \u2014 FOREX_FREE_V8_REJECT_ALL (A7 terminal CONFIRM; "
             "GO consumed at its gate, dead with the cycle per P-8)",
    "budget": {"planned": 6, "used": 3},
    "s1": "SEALED_UNTOUCHED", "hard_stop_reason": None,
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


def test_v8_closed_shape_derives_terminal_with_recorded_drift():
    """A legacy state that closed without a status field (closure recorded in
    the phase) normalizes to TERMINAL, with the derivation warning recorded —
    never silently normalized, and never a KeyError (legitimate progress must
    not break the read path)."""
    rec = legacy_adapters.normalize_legacy_state(
        "FOREX-FREE-V8", dict(V8_CLOSED_SHAPE), measured_branch_head="d" * 40)
    assert rec["lifecycle"] == "TERMINAL"
    assert rec["budget"] == {"used": 3, "max": 6}
    assert rec["go_phrase_state"].startswith("DEAD"), "P-8: no GO survives its cycle's close"
    assert rec["next_authorized_action"].startswith("NONE (closed")
    assert any("recorded-not-normalized" in w for w in rec["adapter_warnings"])


def test_unknown_cycle_id_rejected():
    with pytest.raises(KeyError):
        legacy_adapters.normalize_legacy_state("CRYPTO-V99", {})


def test_adapter_without_hard_stop_maps_status():
    s = {k: v for k, v in V17_SHAPE.items() if k != "hard_stop_reason"}
    rec = legacy_adapters.normalize_legacy_state("CRYPTO-V17", s, measured_branch_head="a" * 40)
    assert rec["lifecycle"] == "ACTIVE_LIGHT"  # retained, no invented status


def test_undeterminable_legacy_state_fails_closed():
    s = {"schema": "x", "cycle_id": "FOREX-FREE-V8", "phase": "MID_FLIGHT",
         "s1": "SEALED_UNTOUCHED"}
    with pytest.raises(KeyError):
        legacy_adapters.normalize_legacy_state("FOREX-FREE-V8", s,
                                               measured_branch_head="b" * 40)


def _fixture_heads():
    measured = "f" * 40  # distinct from any recorded fixture head
    return {cid: measured for cid in legacy_adapters.LEGACY_SOURCES}


def _fixture_hashes():
    return {p.name: legacy_adapters.file_sha256(p) for p in ALL_FIXTURE_FILES}


def test_real_legacy_files_are_read_without_byte_mutation():
    """The read path never mutates legacy state files. Runs hermetically
    against the COMMITTED fixture replicas of the legacy shapes (stand-ins
    for LEGACY_SOURCES, injected via source_paths/source_root): every fixture
    file is hashed before and after full build_registry_from_legacy reads
    (the open and the closed v8 shape) and the bytes must be identical.
    Driven from the injected mapping — no cycle name or lifecycle is
    hard-coded beyond the fixture mapping itself."""
    before = _fixture_hashes()
    reg = legacy_adapters.build_registry_from_legacy(
        _fixture_heads(), source_paths=dict(FIXTURE_SOURCES), source_root=FIXTURE_DIR)
    assert len(reg["cycles"]) == len(legacy_adapters.LEGACY_SOURCES) + len(legacy_adapters.HISTORICAL_CLOSED)
    reg_closed = legacy_adapters.build_registry_from_legacy(
        _fixture_heads(), source_paths=dict(FIXTURE_SOURCES_V8_CLOSED),
        source_root=FIXTURE_DIR)
    assert len(reg_closed["cycles"]) == len(reg["cycles"])
    after = _fixture_hashes()
    assert before == after, "legacy state files were mutated by a read path"


def test_registry_composition_validates_and_carries_warnings():
    """Composition (from the committed fixture replicas, injected via
    source_paths) validates as cycle_registry@1 and every head mismatch vs
    the supplied measured authority surfaces as a recorded warning (drift is
    recorded, not normalized) — for whatever the fixture replicas say."""
    reg = legacy_adapters.build_registry_from_legacy(
        _fixture_heads(), source_paths=dict(FIXTURE_SOURCES), source_root=FIXTURE_DIR)
    from governance import cycle_registry
    cycle_registry.validate_registry(reg)
    warnings = [w for c in reg["cycles"] for w in c.get("adapter_warnings", [])]
    assert warnings, "head drift between legacy files and the measured authority must surface as warnings"
    assert all(("drift recorded-not-normalized" in w or "stale" in w or "prose" in w)
               for w in warnings)
    # the closed v8 replica composes to TERMINAL with the same wording classes
    reg_closed = legacy_adapters.build_registry_from_legacy(
        _fixture_heads(), source_paths=dict(FIXTURE_SOURCES_V8_CLOSED),
        source_root=FIXTURE_DIR)
    cycle_registry.validate_registry(reg_closed)
    closed_warnings = [w for c in reg_closed["cycles"]
                       for w in c.get("adapter_warnings", [])]
    assert any("recorded-not-normalized" in w for w in closed_warnings), \
        "derived TERMINAL from a closure phase must be recorded, not normalized"


# ------------------------------------------------------- negative (typed errors)

def _tmp_sources_with(tmp_path, cid, value):
    """source_paths mapping with one entry replaced and the other two backed
    by valid byte-identical copies of the committed fixtures under tmp_path."""
    sources = {k: tmp_path / (k + ".json") for k in legacy_adapters.LEGACY_SOURCES}
    for other, fixture in FIXTURE_SOURCES.items():
        if other != cid:
            shutil.copyfile(fixture, sources[other])
    sources[cid] = value
    return sources


def test_missing_source_raises_typed_error_with_cycle_and_path(tmp_path):
    err = _missing_source_error(tmp_path)
    assert err.cycle_id == "CRYPTO-V17"
    assert Path(err.path).is_absolute()
    assert err.path == str((tmp_path / "CRYPTO-V17.json").resolve())
    assert err.reason.startswith("missing")


def _missing_source_error(tmp_path):
    sources = _tmp_sources_with(tmp_path, "CRYPTO-V17", tmp_path / "CRYPTO-V17.json")
    with pytest.raises(legacy_adapters.LegacySourceUnavailable) as excinfo:
        legacy_adapters.build_registry_from_legacy(
            _fixture_heads(), source_paths=sources, source_root=tmp_path)
    return excinfo.value


def test_malformed_source_raises_typed_error(tmp_path):
    bad = tmp_path / "broken.json"
    bad.write_bytes(b'{"schema": "v17_run_artifact_v1", "cycle_id": "CRYPT')  # truncated
    sources = _tmp_sources_with(tmp_path, "CRYPTO-V17", bad)
    with pytest.raises(legacy_adapters.LegacySourceUnavailable) as excinfo:
        legacy_adapters.build_registry_from_legacy(
            _fixture_heads(), source_paths=sources, source_root=tmp_path)
    err = excinfo.value
    assert err.cycle_id == "CRYPTO-V17"
    assert err.path == str(bad.resolve())
    assert err.reason.startswith("malformed json")


def test_source_path_escape_raises_typed_error(tmp_path):
    outside = tmp_path.parent / "outside_of_root.json"  # declared escape target
    outside.write_bytes(b'{"schema": "x"}\n')  # even a readable target is rejected
    sources = _tmp_sources_with(tmp_path, "CRYPTO-V17", "../outside_of_root.json")
    with pytest.raises(legacy_adapters.LegacySourceUnavailable) as excinfo:
        legacy_adapters.build_registry_from_legacy(
            _fixture_heads(), source_paths=sources, source_root=tmp_path)
    err = excinfo.value
    assert err.cycle_id == "CRYPTO-V17"
    assert err.path == "../outside_of_root.json"  # the declared source
    assert err.reason.startswith("path escape")
    assert "outside declared source root" in err.reason
    # absolute paths are confined too: a real fixture file outside the
    # declared root is rejected, never silently read
    sources_abs = _tmp_sources_with(tmp_path, "CRYPTO-V17", FIXTURE_SOURCES["CRYPTO-V17"])
    with pytest.raises(legacy_adapters.LegacySourceUnavailable) as excinfo_abs:
        legacy_adapters.build_registry_from_legacy(
            _fixture_heads(), source_paths=sources_abs, source_root=tmp_path)
    assert excinfo_abs.value.reason.startswith("path escape")


def test_repeated_builds_are_identical_excluding_timestamps():
    """Two full builds from the same committed fixtures produce identical
    normalized records field-by-field, excluding only the updated_at_utc
    timestamp fields (which must themselves be UTC ISO8601 Z stamps)."""
    utc = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    first = legacy_adapters.build_registry_from_legacy(
        _fixture_heads(), source_paths=dict(FIXTURE_SOURCES), source_root=FIXTURE_DIR)
    second = legacy_adapters.build_registry_from_legacy(
        _fixture_heads(), source_paths=dict(FIXTURE_SOURCES), source_root=FIXTURE_DIR)
    assert set(first) == set(second)
    for field in first:
        if field == "updated_at_utc":
            assert utc.match(first[field]) and utc.match(second[field])
            continue
        if field == "cycles":
            continue  # never compared wholesale: records carry wall-clock stamps
        assert first[field] == second[field], f"top-level field {field} differs across runs"
    assert len(first["cycles"]) == len(second["cycles"])
    for rec1, rec2 in zip(first["cycles"], second["cycles"]):
        assert rec1["cycle_id"] == rec2["cycle_id"]
        assert set(rec1) == set(rec2)
        for field in rec1:
            if field == "updated_at_utc":
                assert utc.match(rec1[field]) and utc.match(rec2[field])
                continue
            assert rec1[field] == rec2[field], \
                f"cycle {rec1['cycle_id']} field {field} differs across runs"
