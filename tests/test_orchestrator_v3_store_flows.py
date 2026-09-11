"""ZCODE-ORCHESTRATION-V3 v3.1 remediation: store-flow guards (P7/P8 canary
defects STORE-FLOW-1/2/3).

Per defect one NEGATIVE test (the defect scenario is refused / repaired) and
one POSITIVE test (the correct flow stays green). Hermetic: every test drives
OrchestratorStore against a tmp runtime dir; git fixtures are real tiny repos
(STORE-FLOW-3 needs genuinely resolvable commits).
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
    OrchestratorStore, IllegalTransition, HandoffEvidenceRefused,
    handoff_digest,
)
from governance import atomic_io  # noqa: E402


def make_store(tmp_path, cycle_id="ZCODE-ORCHESTRATION-V3"):
    store = OrchestratorStore(runtime_dir=tmp_path / "rt", cycle_id=cycle_id)
    store.intake()
    return store


def make_git_repo(tmp_path, name="fixturerepo"):
    """A real tiny git repo (STORE-FLOW-3 needs resolvable commits)."""
    import subprocess
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True)
    git("init", "-q")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "fixture")
    (repo / "f.txt").write_text("fixture\n", encoding="utf-8")
    git("add", "f.txt")
    git("commit", "-q", "-m", "fixture commit")
    sha = git("rev-parse", "HEAD").stdout.strip()
    return repo, sha


def register_probe(store, task_id="t1", **kw):
    return store.register_task(
        task_id=task_id, role="quant-explorer", objective="probe fixture",
        base_sha="a" * 40, branch="orca/fixture",
        absolute_worktree=kw.pop("absolute_worktree", "/tmp/fixture"),
        **kw)


def handoff_for(task_id="t1", cycle="ZCODE-ORCHESTRATION-V3"):
    return {"task_id": task_id, "cycle_id": cycle, "role": "quant-explorer",
            "lane": "fixture", "dispatch_sha": "a" * 40,
            "actual_start_sha": "a" * 40, "commit_sha": "c" * 40,
            "changed_paths": [], "tests": [{"command": "true", "exit_code": 0,
                                            "verdict": "PASS"}],
            "authority_claims": [], "known_limitations": [], "incidents": [],
            "tree_status": "clean", "workers": 0, "outputs": [],
            "recommended_next_action": "integrate"}


def run_to_handoff_ready(s, task_id="t1", handoff=None):
    register_probe(s, task_id=task_id)
    s.mark_dispatched(task_id=task_id)
    s.mark_running(task_id=task_id)
    return s.publish_handoff(task_id=task_id, handoff=handoff or handoff_for(task_id))


# ------------------------------------------------- STORE-FLOW-1 (P7 defect)
def test_flow1_publish_overwrites_agent_prewritten_draft(tmp_path):
    """NEGATIVE: an agent pre-writes a draft at the inbox path; publish must
    REPLACE the draft with the submitted object (before the fix the stale
    bytes survived and validate failed closed with digest drift)."""
    s = make_store(tmp_path)
    register_probe(s)
    s.mark_dispatched(task_id="t1")
    s.mark_running(task_id="t1")
    draft_path = s.inbox / "t1-handoff.json"
    s.inbox.mkdir(parents=True, exist_ok=True)
    draft_path.write_text('{"task_id": "t1", "fabricated": true}', encoding="utf-8")
    t = s.publish_handoff(task_id="t1", handoff=handoff_for())
    assert t["status"] == "HANDOFF_READY"
    on_disk = json.loads(draft_path.read_text(encoding="utf-8"))
    assert on_disk == handoff_for()  # draft bytes gone, submitted object stored
    attempt = s.load()["tasks"][0]["attempts"][-1]
    assert handoff_digest(on_disk) == attempt["handoff_sha256"]
    s.validate_handoff(task_id="t1")  # would have been CONTROL_STATE_DRIFT pre-fix
    assert s.load()["tasks"][0]["status"] == "VALIDATING"


def test_flow1_publish_writes_inbox_artifact(tmp_path):
    """POSITIVE: the ordinary publish flow still writes the inbox artifact and
    validation re-reads it cleanly."""
    s = make_store(tmp_path)
    run_to_handoff_ready(s)
    art = Path(s.load()["tasks"][0]["handoff_path"])
    assert art.exists() and art.parent == s.inbox
    on_disk = json.loads(art.read_text(encoding="utf-8"))
    assert on_disk == handoff_for()
    s.validate_handoff(task_id="t1")
    assert s.load()["tasks"][0]["status"] == "VALIDATING"


# ------------------------------------------------- STORE-FLOW-2 (P7 defect)
def test_flow2_blocked_is_lawful_exit_from_handoff_ready(tmp_path):
    """NEGATIVE: a HANDOFF_READY task with a mismatched digest used to be a
    DEAD STATE (validate refuses, re-publish refuses, BLOCKED refused). The
    forward escape BLOCKED (with the failure recorded) must now exist - and
    ONLY BLOCKED: REJECTED/TECHABORT from HANDOFF_READY stay illegal."""
    s = make_store(tmp_path)
    run_to_handoff_ready(s)
    art = Path(s.load()["tasks"][0]["handoff_path"])
    tampered = json.loads(art.read_text(encoding="utf-8"))
    tampered["tree_status"] = "dirty"
    art.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(atomic_io.ControlStateDrift):
        s.validate_handoff(task_id="t1")
    # no backward move: re-publish stays refused
    with pytest.raises(IllegalTransition):
        s.publish_handoff(task_id="t1", handoff=handoff_for())
    # the other outcomes are NOT opened up from HANDOFF_READY
    with pytest.raises(IllegalTransition):
        s.record_outcome(task_id="t1", outcome="REJECTED", reason="x")
    with pytest.raises(IllegalTransition):
        s.record_outcome(task_id="t1", outcome="TECHABORT", reason="x")
    # the lawful forward escape: BLOCKED with the failure recorded
    t = s.record_outcome(task_id="t1", outcome="BLOCKED",
                         reason="digest mismatch after publish")
    assert t["status"] == "BLOCKED"
    row = s.load()["tasks"][0]
    assert row["blocker"] == "digest mismatch after publish"
    assert any(e["event"] == "TASK_BLOCKED" and
               e["reason"] == "digest mismatch after publish"
               for e in atomic_io.read_events(s.events_path))
    s.mark_terminal(task_id="t1", terminal_reason="closed blocked")
    assert s.terminal_check()["all_terminal"]


def test_flow2_valid_handoff_ready_validation_unchanged(tmp_path):
    """POSITIVE: the normal HANDOFF_READY -> VALIDATING path is untouched."""
    s = make_store(tmp_path)
    run_to_handoff_ready(s)
    assert s.waiting_summary()["awaiting_validation"] == ["t1"]
    s.validate_handoff(task_id="t1")
    assert s.load()["tasks"][0]["status"] == "VALIDATING"


# ------------------------------------------------- STORE-FLOW-3 (P8 defect)
def test_flow3_publish_refuses_dispatch_sha_mismatch(tmp_path):
    """NEGATIVE: a handoff whose dispatch_sha does not match the task's
    recorded dispatch context (base_sha) is refused at publish; the empty-sha
    variant is refused too. Nothing is mutated and no artifact is written."""
    s = make_store(tmp_path)
    register_probe(s)  # base_sha = a*40
    s.mark_dispatched(task_id="t1")
    s.mark_running(task_id="t1")
    fabricated = dict(handoff_for(), dispatch_sha="d" * 40)
    with pytest.raises(HandoffEvidenceRefused):
        s.publish_handoff(task_id="t1", handoff=fabricated)
    empty = dict(handoff_for(), dispatch_sha="")
    with pytest.raises(HandoffEvidenceRefused):
        s.publish_handoff(task_id="t1", handoff=empty)
    row = s.load()["tasks"][0]
    assert row["status"] == "RUNNING"  # refusal leaves the state untouched
    assert row["attempts"][-1]["handoff_sha256"] is None
    if s.inbox.exists():
        assert not list(s.inbox.glob("*-handoff.json"))


def test_flow3_integrate_refuses_unresolvable_commit(tmp_path):
    """NEGATIVE: mark_integrated with a fabricated commit_sha is refused (the
    sha does not resolve to a git commit in the task's worktree); the state
    stays VALIDATING on disk. Non-40-hex input is still a plain ValueError."""
    s = make_store(tmp_path)
    repo, _real = make_git_repo(tmp_path)
    register_probe(s, absolute_worktree=str(repo))
    s.mark_dispatched(task_id="t1")
    s.mark_running(task_id="t1")
    s.publish_handoff(task_id="t1", handoff=handoff_for())
    s.validate_handoff(task_id="t1")
    fabricated = "d" * 40
    with pytest.raises(HandoffEvidenceRefused):
        s.mark_integrated(task_id="t1", commit_sha=fabricated)
    with pytest.raises(ValueError):
        s.mark_integrated(task_id="t1", commit_sha="nothex")
    row = s.load()["tasks"][0]
    assert row["status"] == "VALIDATING"
    assert "integrated_commit_sha" not in row["attempts"][-1]


def test_flow3_consistent_evidence_integrates(tmp_path):
    """POSITIVE: a handoff whose dispatch_sha matches the recorded dispatch
    context publishes, and the REAL commit sha of the fixture repo integrates
    cleanly with the evidence recorded on the attempt."""
    s = make_store(tmp_path)
    repo, real_sha = make_git_repo(tmp_path)
    register_probe(s, absolute_worktree=str(repo))
    s.mark_dispatched(task_id="t1")
    s.mark_running(task_id="t1")
    s.publish_handoff(task_id="t1", handoff=handoff_for())
    s.validate_handoff(task_id="t1")
    t = s.mark_integrated(task_id="t1", commit_sha=real_sha)
    assert t["status"] == "INTEGRATED"
    row = s.load()["tasks"][0]
    assert row["attempts"][-1]["integrated_commit_sha"] == real_sha
