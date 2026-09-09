"""MDP-V1 M0 - atomic registry register / update / reconcile machinery.

Hermetic only: every case runs on tmp_path fixture registries through the
SAME atomic CAS + append-only journal path used by pause/resume. Proven here:

- register adds a NEW planned cycle (duplicate/illegal lifecycle refused,
  nothing written on refusal);
- update touches only the requested fields and records drift as journal
  events (history is never normalized);
- reconcile applies all head updates as ONE CAS save + journal events and
  regenerates the projection; a concurrent writer loses cleanly on the CAS
  (a crash or interrupt between load and save can never half-apply);
- a sidecar-flock-holding concurrent writer is refused with the file
  untouched.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

from governance import atomic_io, cycle_registry  # noqa: E402

HEAD1 = "a" * 40
HEAD2 = "b" * 40
HEAD3 = "c" * 40


def _rec(cycle_id="TEST-A", lifecycle="ACTIVE_LIGHT", head=HEAD1, **over):
    rec = {
        "cycle_id": cycle_id, "asset": "crypto", "plan": "plans/PLAN_test.md",
        "lifecycle": lifecycle, "phase": "P0",
        "integration_worktree": "", "branch": "orca/x", "head": head,
        "budget": {"used": 0, "max": 6},
        "denominators": {"asset_published": 0, "asset_observed": 0},
        "s0": "OPEN", "s1": "SEALED_UNTOUCHED", "go_phrase": "",
        "go_phrase_state": "", "workers": 0, "active_heavy": False,
        "lock": "free", "heartbeat_utc": "2026-09-08T00:00:00Z",
        "hard_stop_reason": None, "pause_packet": None,
        "next_authorized_action": "", "updated_at_utc": "2026-09-08T00:00:00Z",
    }
    rec.update(over)
    return rec


@pytest.fixture()
def reg_path(tmp_path):
    p = tmp_path / "CYCLE_REGISTRY.json"
    cycle_registry.save(p, {"schema": cycle_registry.SCHEMA_ID,
                            "updated_at_utc": "2026-09-08T00:00:00Z",
                            "writer": "test", "write_token": None,
                            "cycles": [_rec()]})
    return p


def _events(reg_path):
    return atomic_io.read_events(reg_path.parent / "CYCLE_REGISTRY.events.jsonl")


# ---------------------------------------------------------------- register

def test_register_adds_planned_cycle_with_cas_event_and_projection(reg_path):
    reg = cycle_registry.load(reg_path)
    prev = atomic_io.sha256_file(reg_path)
    rec, sha = cycle_registry.register_cycle(
        reg_path, reg, prev_sha=prev, cycle_id="TEST-NEW", plan="plans/PLAN_new.md",
        branch="orca/new", head=None, lifecycle="PLANNED_NOT_STARTED", asset="stocks",
        reason="planned wave")
    assert rec["lifecycle"] == "PLANNED_NOT_STARTED"
    assert rec["head"] == cycle_registry.UNMEASURED_HEAD  # unmeasured placeholder
    stored = cycle_registry.load(reg_path)  # validates schema on read
    assert stored["cycles"][-1]["cycle_id"] == "TEST-NEW"
    events = _events(reg_path)
    assert events[-1]["event"] == "CYCLE_REGISTERED"
    assert events[-1]["cycle_id"] == "TEST-NEW"
    saved = [e for e in events if e["event"] == "REGISTRY_SAVED"]
    assert saved and saved[-1]["content_sha256"] == sha
    # the projection was regenerated as a function of the non-terminal records
    proj = reg_path.parent / "ACTIVE_CYCLES.json"
    assert cycle_registry.projection_matches(stored, proj.read_bytes())
    assert "TEST-NEW" in [r["cycle_id"] for r in
                          json.loads(proj.read_bytes().decode("utf-8"))["cycles"]]


def test_register_refuses_duplicate_without_writing(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    with pytest.raises(ValueError, match="already registered"):
        cycle_registry.register_cycle(
            reg_path, reg, prev_sha=None, cycle_id="TEST-A", plan="p", branch="b",
            asset="crypto")
    assert reg_path.read_bytes() == before, "refused register must not write"


def test_register_refuses_illegal_lifecycle_and_bad_head(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    with pytest.raises(cycle_registry.IllegalTransition):
        cycle_registry.register_cycle(
            reg_path, reg, prev_sha=None, cycle_id="TEST-T", plan="p", branch="b",
            lifecycle="TERMINAL", asset="crypto")
    with pytest.raises(ValueError, match="40-hex"):
        cycle_registry.register_cycle(
            reg_path, reg, prev_sha=None, cycle_id="TEST-H", plan="p", branch="b",
            head="nope", asset="crypto")
    with pytest.raises(ValueError, match="asset"):
        cycle_registry.register_cycle(
            reg_path, reg, prev_sha=None, cycle_id="TEST-ZZ", plan="p", branch="b",
            asset="")
    assert reg_path.read_bytes() == before


# ------------------------------------------------------------------ update

def test_update_head_touches_only_the_requested_field(reg_path):
    reg = cycle_registry.load(reg_path)
    before = json.loads(json.dumps(reg["cycles"][0]))
    prev = atomic_io.sha256_file(reg_path)
    changes, _ = cycle_registry.update_cycle(
        reg_path, reg, prev_sha=prev, cycle_id="TEST-A", head=HEAD2,
        reason="measured advance")
    assert changes == [{"cycle_id": "TEST-A", "field": "head", "from": HEAD1, "to": HEAD2}]
    after = cycle_registry.load(reg_path)["cycles"][0]
    touched = {k for k in before if before[k] != after[k]}
    assert touched == {"head", "updated_at_utc"}, \
        f"update must never rewrite fields it does not touch (touched: {touched})"
    assert _events(reg_path)[-1]["event"] == "CYCLE_UPDATED"
    assert _events(reg_path)[-1]["field"] == "head"


def test_update_lifecycle_enforces_transitions_and_terminal_go_death(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    with pytest.raises(cycle_registry.IllegalTransition):
        cycle_registry.update_cycle(
            reg_path, reg, prev_sha=None, cycle_id="TEST-A",
            lifecycle="PLANNED_NOT_STARTED", reason="backwards")
    assert reg_path.read_bytes() == before
    prev = atomic_io.sha256_file(reg_path)
    reg = cycle_registry.load(reg_path)
    cycle_registry.update_cycle(
        reg_path, reg, prev_sha=prev, cycle_id="TEST-A", lifecycle="TERMINAL",
        reason="closed")
    rec = cycle_registry.load(reg_path)["cycles"][0]
    assert rec["lifecycle"] == "TERMINAL"
    assert rec["go_phrase_state"].startswith("DEAD"), "P-8 terminal GO death"
    # and a terminal cycle left the projection (regenerated on that save)
    proj = json.loads((reg_path.parent / "ACTIVE_CYCLES.json").read_bytes().decode("utf-8"))
    assert "TEST-A" not in [r["cycle_id"] for r in proj["cycles"]]


def test_update_noop_writes_nothing(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    events_before = len(_events(reg_path))
    changes, sha = cycle_registry.update_cycle(
        reg_path, reg, prev_sha=None, cycle_id="TEST-A", head=HEAD1, reason="noop")
    assert changes == []
    assert reg_path.read_bytes() == before
    assert len(_events(reg_path)) == events_before
    assert sha == atomic_io.sha256_file(reg_path)


def test_update_unknown_cycle_fails_closed(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    with pytest.raises(cycle_registry.CycleNotFound):
        cycle_registry.update_cycle(
            reg_path, reg, prev_sha=None, cycle_id="GHOST", head=HEAD2)
    assert reg_path.read_bytes() == before


# ---------------------------------------------------------------- reconcile

def test_plan_reconciliation_is_pure_diff(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    before_events = len(_events(reg_path))
    plan = cycle_registry.plan_reconciliation(reg, {"TEST-A": HEAD2, "GHOST": HEAD3})
    assert plan["head_changes"] == [{"cycle_id": "TEST-A", "field": "head",
                                     "from": HEAD1, "to": HEAD2}]
    assert plan["unmeasured"] == [], "measured cycles are never listed as unmeasurable"
    # pure: nothing written, nothing journaled
    assert reg_path.read_bytes() == before
    assert len(_events(reg_path)) == before_events
    plan2 = cycle_registry.plan_reconciliation(reg, {"TEST-A": HEAD2})
    assert plan2["head_changes"] == plan["head_changes"]


def test_reconcile_execute_is_one_save_with_events_and_projection(reg_path):
    reg = cycle_registry.load(reg_path)
    reg["cycles"].append(_rec("TEST-B", head=HEAD1))
    cycle_registry.save(reg_path, reg, expect_prev_sha=atomic_io.sha256_file(reg_path))
    # hand-edit the projection to simulate a stale/hand-shaped file
    proj = reg_path.parent / "ACTIVE_CYCLES.json"
    proj.write_bytes(b'{"stale": true}\n')
    events_before = len(_events(reg_path))
    reg = cycle_registry.load(reg_path)
    prev = atomic_io.sha256_file(reg_path)
    report, sha = cycle_registry.reconcile_registry(
        reg_path, reg, prev_sha=prev, measured_heads={"TEST-A": HEAD2, "TEST-B": HEAD3},
        reason="M0 closure")
    assert report["mode"] == "EXECUTED"
    assert len(report["head_changes"]) == 2
    new_events = _events(reg_path)[events_before:]
    saved = [e for e in new_events if e["event"] == "REGISTRY_SAVED"]
    assert len(saved) == 1, "all updates must land as ONE CAS save"
    assert [e["event"] for e in new_events if e["event"].startswith("CYCLE_HEAD_RECONCILED")] \
        == ["CYCLE_HEAD_RECONCILED", "CYCLE_HEAD_RECONCILED"]
    stored = cycle_registry.load(reg_path)
    assert stored["cycles"][0]["head"] == HEAD2 and stored["cycles"][1]["head"] == HEAD3
    assert cycle_registry.projection_matches(stored, proj.read_bytes()), \
        "reconcile must regenerate the projection"
    assert sha == atomic_io.sha256_file(reg_path)


def test_reconcile_no_change_writes_nothing(reg_path):
    reg = cycle_registry.load(reg_path)
    before = reg_path.read_bytes()
    events_before = len(_events(reg_path))
    report, sha = cycle_registry.reconcile_registry(
        reg_path, reg, prev_sha=None, measured_heads={"TEST-A": HEAD1})
    assert report["head_changes"] == []
    assert report["mode"] == "NO_CHANGE"
    assert reg_path.read_bytes() == before
    assert len(_events(reg_path)) == events_before
    assert sha is None


def test_reconcile_regenerates_projection_even_without_head_changes(reg_path):
    reg = cycle_registry.load(reg_path)
    proj = reg_path.parent / "ACTIVE_CYCLES.json"
    proj.write_bytes(b'{"stale": true}\n')
    before = reg_path.read_bytes()
    report, _ = cycle_registry.reconcile_registry(
        reg_path, reg, prev_sha=None, measured_heads={"TEST-A": HEAD1}, reason="proj fix")
    assert report["head_changes"] == []
    assert report["projection_drift"], "stale projection must be reported as drift"
    assert cycle_registry.projection_matches(cycle_registry.load(reg_path),
                                             proj.read_bytes())
    assert _events(reg_path)[-1]["event"] == "PROJECTION_REGENERATED"
    assert reg_path.read_bytes() == before, "registry itself untouched"


# --------------------------------------------- crash / concurrency hermetics

def test_cas_lost_update_fails_closed_and_retry_converges(reg_path):
    """Crash/interrupt during reconcile: a writer that loaded stale state
    (another writer committed in between, or the process was frozen) loses
    CLEANLY on the compare-and-swap — the file is never half-applied."""
    reg_a = cycle_registry.load(reg_path)
    sha_seen_by_a = atomic_io.sha256_file(reg_path)  # A's view of the world
    # a concurrent writer commits first
    reg_b = cycle_registry.load(reg_path)
    cycle_registry.update_cycle(reg_path, reg_b, prev_sha=sha_seen_by_a,
                                cycle_id="TEST-A", head=HEAD2, reason="other writer")
    content_after_b = reg_path.read_bytes()
    with pytest.raises(atomic_io.ControlStateDrift, match="CAS mismatch"):
        cycle_registry.reconcile_registry(
            reg_path, reg_a, prev_sha=sha_seen_by_a,  # A's view is now stale
            measured_heads={"TEST-A": HEAD3}, reason="stale writer")
    assert reg_path.read_bytes() == content_after_b, "CAS loser must not touch the file"
    # the loser re-loads and converges
    reg_a = cycle_registry.load(reg_path)
    report, _ = cycle_registry.reconcile_registry(
        reg_path, reg_a, prev_sha=atomic_io.sha256_file(reg_path),
        measured_heads={"TEST-A": HEAD3}, reason="stale writer retried")
    assert report["mode"] == "EXECUTED"
    assert cycle_registry.load(reg_path)["cycles"][0]["head"] == HEAD3


def test_sidecar_flock_holding_writer_is_refused_file_untouched(tmp_path, reg_path):
    """Two concurrent CAS writers serialized by the sidecar flock: the one
    that cannot take the lock loses cleanly with the file untouched."""
    holder = tmp_path / "holder.py"
    holder.write_text(
        "import fcntl, os, time\n"
        f"fd = os.open({str(reg_path.name + '.lock')!r}, os.O_CREAT | os.O_RDWR)\n"
        "fcntl.flock(fd, fcntl.LOCK_EX)\n"
        "print('HELD', flush=True)\n"
        "time.sleep(5)\n",
    )
    proc = subprocess.Popen([sys.executable, str(holder)], cwd=str(tmp_path),
                            stdout=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().strip() == "HELD"
        reg = cycle_registry.load(reg_path)
        with pytest.raises(atomic_io.WriteLockBusy):
            cycle_registry.update_cycle(
                reg_path, reg, prev_sha=None, cycle_id="TEST-A", head=HEAD2)
        assert cycle_registry.load(reg_path)["cycles"][0]["head"] == HEAD1
    finally:
        proc.kill()
        proc.wait()


def test_malformed_registry_row_fails_closed_before_any_write(reg_path):
    """A registry row that drifted into a malformed shape (illegal lifecycle)
    can never reach the disk: validation runs before the write and the file
    is preserved byte-for-byte."""
    reg = cycle_registry.load(reg_path)
    reg["cycles"][0]["lifecycle"] = "GARBAGE"
    before = reg_path.read_bytes()
    with pytest.raises(atomic_io.SchemaValidationError):
        cycle_registry.reconcile_registry(
            reg_path, reg, prev_sha=atomic_io.sha256_file(reg_path),
            measured_heads={"TEST-A": HEAD2})
    assert reg_path.read_bytes() == before, "malformed state never written, never repaired"
    reg2 = cycle_registry.load(reg_path)  # fresh load: the failed writer mutated its copy
    reg2["cycles"][0]["lifecycle"] = "GARBAGE"
    with pytest.raises(atomic_io.SchemaValidationError):
        cycle_registry.update_cycle(
            reg_path, reg2, prev_sha=atomic_io.sha256_file(reg_path),
            cycle_id="TEST-A", head=HEAD2)
    assert reg_path.read_bytes() == before
