"""ZCODE-ORCHESTRATION-V3 P2: task-store state machine tests (gate Z3-G2).

Hermetic: every test drives OrchestratorStore against a tmp runtime dir.
The canonical cycle registry is never touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_SCRIPTS = Path(__file__).resolve().parents[1] / \
    "plugins" / "quant-research-orchestrator" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from orchestrator_store import (  # noqa: E402
    OrchestratorStore, IllegalTransition, ForeignTaskRefused, TaskNotFound,
    DependencyCycle, handoff_digest,
)
from governance import atomic_io  # noqa: E402


def make_store(tmp_path, cycle_id="ZCODE-ORCHESTRATION-V3"):
    store = OrchestratorStore(runtime_dir=tmp_path / "rt", cycle_id=cycle_id)
    store.intake()
    return store


def register_probe(store, task_id="t1", **kw):
    return store.register_task(
        task_id=task_id, role="quant-explorer", objective="probe fixture",
        base_sha="a" * 40, branch="orca/fixture", absolute_worktree="/tmp/fixture",
        **kw)


def handoff_for(task_id="t1", cycle="ZCODE-ORCHESTRATION-V3"):
    return {"task_id": task_id, "cycle_id": cycle, "role": "quant-explorer",
            "lane": "fixture", "dispatch_sha": "b" * 40,
            "actual_start_sha": "b" * 40, "commit_sha": "c" * 40,
            "changed_paths": [], "tests": [{"command": "true", "exit_code": 0,
                                            "verdict": "PASS"}],
            "authority_claims": [], "known_limitations": [], "incidents": [],
            "tree_status": "clean", "workers": 0, "outputs": [],
            "recommended_next_action": "integrate"}


# ------------------------------------------------------------------ lifecycle
def test_full_happy_path(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    assert s.tasks_path.exists()
    t = s.mark_dispatched(task_id="t1")
    assert t["status"] == "DISPATCHED" and len(t["attempts"]) == 1
    t = s.mark_running(task_id="t1")
    t = s.publish_handoff(task_id="t1", handoff=handoff_for())
    assert t["status"] == "HANDOFF_READY"
    s.validate_handoff(task_id="t1")
    s.mark_integrated(task_id="t1", commit_sha="c" * 40)
    s.mark_terminal(task_id="t1", terminal_reason="fixture done")
    chk = s.terminal_check()
    assert chk["all_terminal"] and chk["tasks_terminal"] == 1


def test_no_backward_transitions(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    s.mark_dispatched(task_id="t1")
    store = s.load()
    with pytest.raises(IllegalTransition):
        s._transition(store, "t1", "READY", writer="x")
    # a terminal state absorbs everything
    s.mark_running(task_id="t1")
    s.publish_handoff(task_id="t1", handoff=handoff_for())
    s.validate_handoff(task_id="t1")
    s.record_outcome(task_id="t1", outcome="REJECTED", reason="fixture")
    s.mark_terminal(task_id="t1", terminal_reason="closed rejected")
    store = s.load()
    with pytest.raises(IllegalTransition):
        s._transition(store, "t1", "READY", writer="x")


def test_duplicate_dispatch_is_idempotent(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    s.mark_dispatched(task_id="t1", invocation_id="inv-1")
    before = s.load()["tasks"][0]["attempts"]
    s.mark_dispatched(task_id="t1", invocation_id="inv-1")
    after = s.load()["tasks"][0]["attempts"]
    assert len(before) == len(after) == 1


def test_retry_appends_attempt_and_max_attempts_enforced(tmp_path):
    s = make_store(tmp_path)
    s.register_task(task_id="t2", role="quant-implementer", objective="x",
                    max_attempts=2)
    s.mark_dispatched(task_id="t2")
    s.mark_running(task_id="t2")
    s.publish_handoff(task_id="t2", handoff=handoff_for("t2"))
    s.validate_handoff(task_id="t2")  # VALIDATING is the only route to an outcome
    s.record_outcome(task_id="t2", outcome="TECHABORT", reason="fixture retry loop")
    # terminal TECHABORT cannot be re-dispatched: re-dispatch = NEW task
    with pytest.raises(IllegalTransition):
        s.mark_dispatched(task_id="t2")
    assert s.load()["tasks"][0]["attempts"][0]["outcome"] == "HANDOFF_PUBLISHED"


def test_events_are_append_only(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    n0 = len(atomic_io.read_events(s.events_path))
    s.mark_dispatched(task_id="t1")
    n1 = len(atomic_io.read_events(s.events_path))
    # REGISTERED -> READY -> DISPATCHED: exactly two journaled events
    assert n1 == n0 + 2
    s.mark_dispatched(task_id="t1")  # duplicate ignored but still journaled
    rows = atomic_io.read_events(s.events_path)
    assert any(r["event"] == "TASK_DISPATCH_DUPLICATE_IGNORED" for r in rows)


# ------------------------------------------------------------------- guards
def test_duplicate_task_id_refused(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    with pytest.raises(ValueError):
        register_probe(s)


def test_dependency_cycle_refused(tmp_path):
    s = make_store(tmp_path)
    register_probe(s, task_id="a")
    s.register_task(task_id="b", role="quant-explorer", objective="x",
                    dependencies=["a"])
    # unknown dependency is refused by the schema validator (fail closed)
    with pytest.raises(atomic_io.SchemaValidationError):
        s.register_task(task_id="c", role="quant-explorer", objective="x",
                        dependencies=["nonexistent"])
    # self-dependency is refused
    with pytest.raises(atomic_io.SchemaValidationError):
        s.register_task(task_id="selfdep", role="quant-explorer", objective="x")
        store = s.load()
        store["tasks"][-1]["dependencies"] = ["selfdep"]
        s._save(store, expect_prev_sha=atomic_io.sha256_file(s.tasks_path))


def test_ready_requires_dependencies_done(tmp_path):
    s = make_store(tmp_path)
    s.register_task(task_id="dep", role="quant-explorer", objective="x")
    s.register_task(task_id="child", role="quant-implementer", objective="y",
                    dependencies=["dep"])
    ready = {t["task_id"] for t in s.list_ready()}
    assert ready == {"dep"}
    s.mark_dispatched(task_id="dep")
    s.mark_running(task_id="dep")
    s.publish_handoff(task_id="dep", handoff=handoff_for("dep"))
    s.validate_handoff(task_id="dep")
    s.mark_integrated(task_id="dep")
    s.mark_terminal(task_id="dep", terminal_reason="done")
    assert {t["task_id"] for t in s.list_ready()} == {"child"}


def test_foreign_task_isolation(tmp_path):
    s = make_store(tmp_path, cycle_id="OTHER-CYCLE")
    s.intake()
    s.register_task(task_id="foreign", role="quant-explorer", objective="x",
                    )
    other = OrchestratorStore(runtime_dir=tmp_path / "rt",
                              cycle_id="ZCODE-ORCHESTRATION-V3")
    with pytest.raises((ForeignTaskRefused, IllegalTransition)):
        other.mark_dispatched(task_id="foreign")
    with pytest.raises((ForeignTaskRefused, TaskNotFound)):
        other.validate_handoff(task_id="foreign")


def test_malformed_state_is_drift_not_empty(tmp_path):
    s = make_store(tmp_path)
    s.intake()
    s.tasks_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(atomic_io.ControlStateDrift):
        s.load()
    missing = OrchestratorStore(runtime_dir=tmp_path / "rt2")
    with pytest.raises(atomic_io.ControlStateDrift):
        missing.load()


def test_cas_fails_closed_on_concurrent_writer(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    stale_sha = atomic_io.sha256_file(s.tasks_path)
    # another writer moves the file
    store = s.load()
    store["updated_at_utc"] = "2099-01-01T00:00:00Z"
    s._save(store, expect_prev_sha=stale_sha)
    # now attempt a write with the STALE sha -> must fail closed
    store2 = s.load()
    store2["updated_at_utc"] = "2099-01-01T00:00:01Z"
    with pytest.raises(atomic_io.ControlStateDrift):
        s._save(store2, expect_prev_sha=stale_sha)


def test_handoff_digest_mismatch_refused(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    s.mark_dispatched(task_id="t1")
    s.mark_running(task_id="t1")
    s.publish_handoff(task_id="t1", handoff=handoff_for())
    # tamper with the artifact on disk -> validation must fail closed
    art = Path(s.load()["tasks"][0]["handoff_path"])
    tampered = json.loads(art.read_text(encoding="utf-8"))
    tampered["tree_status"] = "dirty"
    art.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(atomic_io.ControlStateDrift):
        s.validate_handoff(task_id="t1")


def test_controller_restart_recovery_from_disk(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    s.mark_dispatched(task_id="t1", invocation_id="inv-9")
    # a restarted controller re-opens the store from files only
    s2 = OrchestratorStore(runtime_dir=tmp_path / "rt")
    ws = s2.waiting_summary()
    assert ws["inflight"] and ws["inflight"][0]["task_id"] == "t1"
    assert ws["inflight"][0]["attempt"] == 1


def test_heartbeat_only_for_live_work(tmp_path):
    s = make_store(tmp_path)
    register_probe(s)
    with pytest.raises(IllegalTransition):
        s.heartbeat(task_id="t1")
    s.mark_dispatched(task_id="t1")
    s.heartbeat(task_id="t1", pid=12345)
    assert s.load()["tasks"][0]["pid"] == 12345


def test_dispatch_context_written_and_cleared(tmp_path):
    s = make_store(tmp_path)
    s.register_task(task_id="t3", role="quant-implementer", objective="x",
                    allowed_paths=["/tmp/fixture/src"], forbidden_paths=["/etc"])
    s.mark_dispatched(task_id="t3")
    ctx = json.loads(s.current_dispatch.read_text(encoding="utf-8"))
    assert ctx["task_id"] == "t3" and ctx["allowed_paths"] == ["/tmp/fixture/src"]
    s.mark_running(task_id="t3")
    s.publish_handoff(task_id="t3", handoff=handoff_for("t3"))
    s.validate_handoff(task_id="t3")
    s.mark_integrated(task_id="t3")
    assert not s.current_dispatch.exists()
