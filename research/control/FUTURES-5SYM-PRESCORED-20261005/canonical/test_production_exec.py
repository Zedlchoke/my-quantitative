"""T1-T14 — the canonical-integration wrapper, tested sandbox-isolated
THROUGH THE SAME PRODUCTION CODE (production_exec.py + realstate.py).

Isolation law: every sandbox test aims the canonical heavy_lock module at a
per-test tmp governance dir via the sanctioned RUNTIME_DIRNAME redirection
(production_exec._sandbox_runtime / target_root=). Real surfaces
(plans/CYCLE_REGISTRY.json, ~/.my-quantitative-governance) are only ever
READ — T12 proves the write refusal, T14 proves read-only real-state checks,
and the suite-level byte-identical snapshot is recorded in the lane handoff.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import production_exec as pe  # noqa: E402
import realstate as rs  # noqa: E402
from governance import atomic_io, cycle_registry, heavy_lock  # noqa: E402

CID = "FUTURES-5SYM-PRESCORED-20261005"
BRANCH = "prep/futures-5sym-prescored-20261005"
HEAD_A = "a" * 40
HEAD_B = "b" * 40
SEED_HEAD = "c" * 40
NOW = "2026-10-06T00:00:00Z"


# ------------------------------------------------------------ fixtures ----

@pytest.fixture(autouse=True)
def _no_env_override(monkeypatch):
    """No test may inherit a real F5SYM_GOVERNANCE_DIR."""
    monkeypatch.delenv(pe.SANDBOX_ENV_VAR, raising=False)


def make_row(cycle_id: str = CID, lifecycle: str = "ACTIVE_HEAVY",
             head: str = HEAD_A, branch: str = BRANCH,
             go_phrase: str | None = None) -> dict:
    return {
        "cycle_id": cycle_id, "asset": "futures",
        "plan": "plans/PLAN_futures_5sym_prescored.md",
        "lifecycle": lifecycle, "phase": "REGISTERED",
        "integration_worktree": "/tmp/sandbox-worktree",
        "branch": branch, "head": head,
        "budget": {"used": 0, "max": 6},
        "denominators": {"note": "sandbox-only denominators"},
        "s0": "OPEN", "s1": "SEALED_UNTOUCHED",
        "go_phrase": go_phrase if go_phrase is not None
        else pe.canonical_go_phrase(cycle_id),
        "go_phrase_state": "REGISTERED_NOT_CONSUMED",
        "workers": 0, "active_heavy": False,
        "lock": "machine-wide heavy lock (see researchctl locks inspect)",
        "heartbeat_utc": NOW, "hard_stop_reason": None, "pause_packet": None,
        "next_authorized_action": "", "updated_at_utc": NOW,
        "adapter_warnings": [],
    }


def write_registry(plans: Path, cycles: list[dict]) -> Path:
    reg = {"schema": "cycle_registry@1", "updated_at_utc": NOW,
           "writer": "sandbox fixture", "write_token": None,
           "cycles": cycles}
    cycle_registry.validate_registry(reg)  # fixture validity through the canonical validator
    path = plans / "CYCLE_REGISTRY.json"
    path.write_text(json.dumps(reg, indent=1) + "\n", encoding="utf-8")
    return path


def write_go(root: Path, *, cycle: str = CID, typed: str | None = None,
             registered: str | None = None, two_key: dict | None = None,
             omit_two_key: bool = False, schema: str = "dev1_go_auth@1",
             filename: str = "GO_RECORDED.json") -> Path:
    phrase = typed if typed is not None else pe.canonical_go_phrase(cycle)
    go = {
        "schema": schema, "cycle": cycle,
        "gate": "SCORED EXECUTION",
        "go_phrase_typed": phrase,
        "go_phrase_registered": registered if registered is not None else phrase,
        "match": "EXACT", "received_utc": NOW,
        "two_key": two_key if two_key is not None else {
            "key_1_a7": {"verdict": "AUTHORIZED_WITH_FINDINGS (0 CRITICAL / 0 HIGH)"},
            "key_2_owner_go": "consumed verbatim at this gate"},
        "recorded_by": "OWNER", "recorded_utc": NOW,
    }
    if omit_two_key:
        go.pop("two_key")
    p = root / "auth" / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(go, indent=1) + "\n", encoding="utf-8")
    return p


def seed_registry(plans: Path, row: dict | None = None) -> Path:
    """Sandbox registry seeded with a valid TERMINAL row (registries are
    never empty per cycle_registry@1)."""
    seed = make_row("SEED-V1", lifecycle="TERMINAL", head=SEED_HEAD,
                    branch="orca/seed", go_phrase="GO SEED V1 SCORED EXECUTION")
    return write_registry(plans, [row] if row else [seed])


@pytest.fixture()
def sandbox(tmp_path: Path) -> dict:
    plans = tmp_path / "plans"
    plans.mkdir(parents=True)
    gov = tmp_path / "gov"
    return {
        "root": tmp_path,
        "plans": plans,
        "registry": seed_registry(plans),
        "gov": gov,
        "final_status": tmp_path / "FINAL_STATUS.json",
        "handoff": tmp_path / "handoff" / "handoff.json",
        "ledger": tmp_path / "ledger" / "TRIAL_LEDGER.jsonl",
    }


def sha_of(p: os.PathLike | str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sandbox_inspect(gov: Path) -> dict:
    with pe._sandbox_runtime(gov):
        return heavy_lock.inspect()


def step_ok() -> dict:
    return {"rows": 2, "twin": "MATCH"}


# --------------------------------------------------------------- T1 -------

def test_t1_happy_path_full_production_sequence(sandbox):
    """register-row (canonical CAS) + valid GO + acquire + step + handoff +
    release => exit 0, lock released, sandbox registry updated via CAS."""
    reg_path, gov = sandbox["registry"], sandbox["gov"]
    prev = sha_of(reg_path)
    reg = cycle_registry.load(reg_path)
    rec, new_sha = cycle_registry.register_cycle(
        reg_path, reg, prev_sha=prev, cycle_id=CID,
        plan="plans/PLAN_futures_5sym_prescored.md", branch=BRANCH, head=HEAD_A,
        lifecycle="PLANNED_NOT_STARTED", asset="futures",
        worktree="/tmp/sandbox-worktree", reason="t1 register")
    assert rec["head"] == HEAD_A and Path(reg_path).exists()
    # lifecycle to executable through the PRODUCTION CAS wrapper
    cas = pe.registry_cas_update(registry_path=reg_path, cycle_id=CID,
                                 prev_sha=new_sha, lifecycle="ACTIVE_HEAVY",
                                 reason="t1 activate")
    assert cas["changes"][0]["field"] == "lifecycle"

    sandbox["ledger"].parent.mkdir(parents=True, exist_ok=True)
    sandbox["ledger"].write_text("")  # empty ledger, must stay untouched

    go = write_go(sandbox["root"])
    outcome = pe.run_protected_step(
        registry_path=reg_path, cycle_id=CID, role="EXEC",
        worktree="/tmp/sandbox-worktree", command=["python", "runner.py"],
        expected_artifacts=["/tmp/artifacts/SUMMARY.json", "/tmp/artifacts/LEDGER.jsonl"],
        step_callable=step_ok, final_status_path=sandbox["final_status"],
        handoff_path=sandbox["handoff"],
        handoff_payload={"verdict": "PASS", "lane": "T1"},
        ledger_paths=[str(sandbox["ledger"])],
        measured_head=HEAD_A, measured_branch=BRANCH, go_artifact=go,
        target_root=gov)

    assert outcome["exit_code"] == 0 and outcome["status"] == "FINISHED"
    assert outcome["success"] is True
    assert outcome["released"] is True
    assert outcome["registry_cas"]["changes"][0]["field"] == "phase"
    # lock released: sandbox heavy registry unlinked, history FINISHED row
    assert not (gov / "heavy_runtime" / "heavy_worker.registry.json").exists()
    hist = (gov / "heavy_runtime" / "heavy_worker.history.jsonl").read_text().splitlines()
    last = json.loads(hist[-1])
    assert last["cycle_id"] == CID and last["status"] == "FINISHED"
    # machine-readable FINAL_STATUS + terminal handoff written inside the lock
    final = json.loads(sandbox["final_status"].read_text())
    assert final["schema"] == pe.FINAL_STATUS_SCHEMA and final["success"] is True
    handoff = json.loads(sandbox["handoff"].read_text())
    assert handoff["schema"] == pe.HANDOFF_SCHEMA
    assert outcome["handoff"]["sha256"] == handoff_sha(sandbox["handoff"])
    assert outcome["ledger_untouched"] is True
    # sandbox registry CAS-updated via the canonical writer (projection too)
    reg2 = cycle_registry.load(reg_path)
    row = cycle_registry.resolve(reg2, CID)
    assert row["phase"] == "step executed under canonical lock"
    assert (sandbox["plans"] / "ACTIVE_CYCLES.json").exists()


def handoff_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ----------------------------------------------------------- T2 - T5 -------

def test_t2_registry_row_missing(sandbox):
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], "NOT-A-REGISTERED-CYCLE",
                          measured_head=HEAD_A, measured_branch=BRANCH)
    assert ei.value.code == "REGISTRY_ROW_MISSING"


def test_t3_head_mismatch(sandbox):
    row = make_row(head=HEAD_A)
    write_registry(sandbox["plans"], [row])
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, measured_head=HEAD_B,
                          measured_branch=BRANCH)
    assert ei.value.code == "HEAD_MISMATCH"
    assert ei.value.detail["kind"] == "stale"
    # unmeasured placeholder is the same refusal class, fail closed
    row2 = make_row(head=cycle_registry.UNMEASURED_HEAD)
    write_registry(sandbox["plans"], [row2])
    with pytest.raises(pe.AuthorityError) as ei2:
        pe.read_authority(sandbox["registry"], CID, measured_head=HEAD_A,
                          measured_branch=BRANCH)
    assert ei2.value.code == "HEAD_MISMATCH"
    assert ei2.value.detail["kind"] == "unmeasured_placeholder"


def test_t4_branch_mismatch(sandbox):
    write_registry(sandbox["plans"], [make_row(branch="other/branch")])
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, measured_head=HEAD_A,
                          measured_branch=BRANCH)
    assert ei.value.code == "BRANCH_MISMATCH"
    assert ei.value.detail["row_branch"] == "other/branch"


def test_t5_lifecycle_not_executable(sandbox):
    go = write_go(sandbox["root"])
    for lifecycle in ("TERMINAL", "PAUSED_MAINTENANCE", "PLANNED_NOT_STARTED"):
        row = make_row(lifecycle=lifecycle)
        if lifecycle == "PAUSED_MAINTENANCE":
            row["hard_stop_reason"] = "OPERATOR_REQUESTED"
        write_registry(sandbox["plans"], [row])
        with pytest.raises(pe.AuthorityError) as ei:
            pe.read_authority(sandbox["registry"], CID, measured_head=HEAD_A,
                              measured_branch=BRANCH, go_artifact=go)
        assert ei.value.code == "LIFECYCLE_NOT_EXECUTABLE"
        assert ei.value.detail["lifecycle"] == lifecycle


# --------------------------------------------------------------- T6 -------

def test_t6_go_refusals(sandbox):
    row = make_row()
    write_registry(sandbox["plans"], [row])
    kw = dict(measured_head=HEAD_A, measured_branch=BRANCH)

    # GO missing entirely
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID,
                          go_artifact=sandbox["root"] / "auth" / "absent.json", **kw)
    assert ei.value.code == "GO_MISSING"

    # wrong cycle-id (checked BEFORE the phrase — even with a wrong phrase too)
    go = write_go(sandbox["root"], cycle="OTHER-CYCLE",
                  typed="GO OTHER-CYCLE SCORED EXECUTION")
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, go_artifact=go, **kw)
    assert ei.value.code == "GO_CYCLE_MISMATCH"

    # wrong phrase (paraphrase dies; byte-exact law, no trim/case-fold)
    go = write_go(sandbox["root"], typed=f"  go {CID} scored execution  ")
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, go_artifact=go, **kw)
    assert ei.value.code == "GO_PHRASE_MISMATCH"

    # registered != typed inside the GO artifact
    go = write_go(sandbox["root"], registered="GO SOMETHING ELSE")
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, go_artifact=go, **kw)
    assert ei.value.code == "GO_PHRASE_MISMATCH"

    # two-key incomplete: key_2_owner_go missing
    go = write_go(sandbox["root"], two_key={"key_1_a7": {"verdict": "OK"}})
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, go_artifact=go, **kw)
    assert ei.value.code == "TWO_KEY_INCOMPLETE"

    # two_key object absent entirely
    go = write_go(sandbox["root"], omit_two_key=True)
    with pytest.raises(pe.AuthorityError) as ei:
        pe.read_authority(sandbox["registry"], CID, go_artifact=go, **kw)
    assert ei.value.code == "TWO_KEY_INCOMPLETE"

    # a complete GO passes and returns the row
    go = write_go(sandbox["root"])
    row_back = pe.read_authority(sandbox["registry"], CID, go_artifact=go, **kw)
    assert row_back["cycle_id"] == CID


# --------------------------------------------------------------- T7 -------

def test_t7_lock_held_by_foreign_row(sandbox):
    gov = sandbox["gov"]
    foreign = pe.acquire_canonical_lock(
        "FOREIGN-CYCLE", "EXEC", "/tmp/wt", ["true"], [],
        target_root=gov)
    ran = {"called": False}

    def step():
        ran["called"] = True
        return {}

    with pytest.raises(pe.CanonicalLockBusy) as ei:
        pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [],
                                  target_root=gov)
    assert ei.value.verdict == "NOT_RUN_RESOURCE_CONFLICT"
    # no computation under a foreign lock: the registry never gained our row,
    # the history holds exactly one foreign row
    with pe._sandbox_runtime(gov):
        row = heavy_lock._read_json(gov / "heavy_runtime" / "heavy_worker.registry.json")
    assert row["cycle_id"] == "FOREIGN-CYCLE"
    assert ran["called"] is False
    foreign.release(status="FINISHED", note="t7 cleanup")


# --------------------------------------------------------------- T8 -------

def test_t8_post_acquire_drift_foreign_row(sandbox):
    gov = sandbox["gov"]
    with pytest.raises(pe.CanonicalRefusal) as ei:
        pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [],
                                  target_root=gov,
                                  faults={"post_acquire_foreign_row"})
    assert ei.value.code == "LOCK_POSTACQUIRE_DRIFT"
    assert any("cycle_id" in p for p in ei.value.detail["problems"])
    # evidence preserved: the injected foreign row bytes stay untouched,
    # only the OS flock was given back (never reclaimed by the worker)
    with pe._sandbox_runtime(gov):
        row = heavy_lock._read_json(gov / "heavy_runtime" / "heavy_worker.registry.json")
    assert row["cycle_id"] == "FOREIGN-CYCLE-INJECTED"
    # the flock is actually free again (probe takes + releases it)
    with pe._sandbox_runtime(gov):
        assert heavy_lock.flock_state(gov / "heavy_runtime" / "heavy_worker.lock") == "free"
    # and the canonical inspector now fails closed (row under a free flock)
    assert sandbox_inspect(gov)["verdict"] == "CONTROL_STATE_DRIFT"


# --------------------------------------------------------------- T9 -------

def test_t9_step_exception_releases_lock_ledger_untouched(sandbox):
    gov = sandbox["gov"]
    sandbox["ledger"].parent.mkdir(parents=True, exist_ok=True)
    sandbox["ledger"].write_text('{"row": 1}\n')
    ledger_sha = sha_of(sandbox["ledger"])
    write_registry(sandbox["plans"], [make_row()])

    def boom():
        raise RuntimeError("mid-step computation fault")

    guard = pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [],
                                      target_root=gov)
    outcome = pe.execute_cycle_step(
        cycle_id=CID, step_name="compute", step_callable=boom, lock=guard,
        expected_artifacts=["/tmp/artifacts/SUMMARY.json"],
        final_status_path=sandbox["final_status"],
        ledger_paths=[str(sandbox["ledger"])])
    assert outcome["status"] == "FAILED" and outcome["exit_code"] == pe.EXIT_FAILED
    assert outcome["success"] is False
    assert outcome["step_error"]["type"] == "RuntimeError"
    assert outcome["released"] is True           # release ALWAYS attempted
    assert outcome["ledger_untouched"] is True
    assert sha_of(sandbox["ledger"]) == ledger_sha
    assert not (gov / "heavy_runtime" / "heavy_worker.registry.json").exists()
    assert sandbox_inspect(gov)["verdict"] == "FREE_PROVEN"
    final = json.loads(sandbox["final_status"].read_text())
    assert final["status"] == "FAILED" and final["success"] is False


# -------------------------------------------------------------- T10 -------

def test_t10_release_raises_failed_nonzero_bug1(sandbox):
    gov = sandbox["gov"]
    write_registry(sandbox["plans"], [make_row()])
    guard = pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [],
                                      target_root=gov)
    outcome = pe.execute_cycle_step(
        cycle_id=CID, step_name="compute", step_callable=step_ok, lock=guard,
        expected_artifacts=[], final_status_path=sandbox["final_status"],
        handoff_path=sandbox["handoff"], faults={"fail_release"})
    # BUG1 class: the step completed and the handoff was written, but a
    # raised release is a FINALIZATION FAILURE — FAILED, non-zero, no success
    assert outcome["status"] == "FAILED" and outcome["exit_code"] != 0
    assert outcome["success"] is False
    assert outcome["release_error"]["type"] == "HeavyLockError"
    assert outcome["released"] is False
    final = json.loads(sandbox["final_status"].read_text())
    assert final["success"] is False and final["release_error"]
    # cleanup: give back only the flock (test-scoped sandbox dir is discarded)
    guard.abandon_preserving_row()


# -------------------------------------------------------------- T11 -------

def test_t11_handoff_write_raises_failed_bug2(sandbox):
    gov = sandbox["gov"]
    write_registry(sandbox["plans"], [make_row()])
    guard = pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [],
                                      target_root=gov)
    outcome = pe.execute_cycle_step(
        cycle_id=CID, step_name="compute", step_callable=step_ok, lock=guard,
        expected_artifacts=[], final_status_path=sandbox["final_status"],
        handoff_path=sandbox["handoff"], faults={"fail_handoff_write"})
    # BUG2 class: terminal handoff write failed inside the guarded path =>
    # non-zero, lock still released, and NO success token anywhere
    assert outcome["status"] == "FAILED" and outcome["exit_code"] != 0
    assert outcome["success"] is False
    assert outcome["handoff_error"]["message"] == "fail_handoff_write"
    assert outcome["handoff"] is None
    assert not sandbox["handoff"].exists()
    assert outcome["released"] is True
    final = json.loads(sandbox["final_status"].read_text())
    assert final["success"] is False
    assert sandbox_inspect(gov)["verdict"] == "FREE_PROVEN"


# -------------------------------------------------------------- T12 -------

def test_t12_real_mode_refused_before_any_write(sandbox):
    real_sha_before = sha_of(pe.REAL_ROOT_REGISTRY)
    prev = sha_of(pe.REAL_ROOT_REGISTRY)

    # real registry CAS write refused (hard-compiled PREP law)
    with pytest.raises(pe.CanonicalRefusal) as ei:
        pe.registry_cas_update(registry_path=pe.REAL_ROOT_REGISTRY, cycle_id=CID,
                               prev_sha=prev, head=HEAD_A)
    assert ei.value.code == "REGISTRY_WRITE_REAL_REFUSED"
    assert "owner authorization" in ei.value.detail["todo"]
    # anything inside the real plans dir is a real target too
    with pytest.raises(pe.CanonicalRefusal) as ei:
        pe.registry_cas_update(registry_path=str(Path(pe.REAL_PLANS_DIR) / "x.json"),
                               cycle_id=CID, prev_sha=prev)
    assert ei.value.code == "REGISTRY_WRITE_REAL_REFUSED"

    # canonical lock acquire refused against the real governance dir
    with pytest.raises(pe.CanonicalRefusal) as ei:
        pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [],
                                  target_root=pe.REAL_GOVERNANCE_DIR)
    assert ei.value.code == "REAL_LOCK_ACQUIRE_REFUSED_PREP"
    # no target at all => real mode => refused
    with pytest.raises(pe.CanonicalRefusal) as ei:
        pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [])
    assert ei.value.code == "REAL_LOCK_ACQUIRE_REFUSED_PREP"
    # env override pointing at the real dir => refused
    os.environ[pe.SANDBOX_ENV_VAR] = str(pe.REAL_GOVERNANCE_DIR)
    try:
        with pytest.raises(pe.CanonicalRefusal) as ei:
            pe.acquire_canonical_lock(CID, "EXEC", "/tmp/wt", ["true"], [])
        assert ei.value.code == "REAL_LOCK_ACQUIRE_REFUSED_PREP"
    finally:
        del os.environ[pe.SANDBOX_ENV_VAR]

    # full sequence with a write intent against real paths => refused, no write
    outcome = pe.run_protected_step(
        registry_path=pe.REAL_ROOT_REGISTRY, cycle_id=CID, role="EXEC",
        worktree="/tmp/wt", command=["true"], expected_artifacts=[],
        step_callable=step_ok, final_status_path=sandbox["final_status"],
        target_root=pe.REAL_GOVERNANCE_DIR)
    assert outcome["status"] == "REFUSED" and outcome["exit_code"] == pe.EXIT_REFUSED
    assert sha_of(pe.REAL_ROOT_REGISTRY) == real_sha_before


# -------------------------------------------------------------- T13 -------

def test_t13_cas_conflict_stale_base_no_partial_write(sandbox):
    reg_path = sandbox["registry"]
    write_registry(sandbox["plans"], [make_row()])
    sha_before = sha_of(reg_path)
    stale = "0" * 64
    with pytest.raises(pe.CanonicalRefusal) as ei:
        pe.registry_cas_update(registry_path=reg_path, cycle_id=CID,
                               prev_sha=stale, head=HEAD_B)
    assert ei.value.code == "CAS_MISMATCH"
    assert sha_of(reg_path) == sha_before          # byte-identical: no partial write
    # and the canonical CAS succeeds with the true prev sha
    cas = pe.registry_cas_update(registry_path=reg_path, cycle_id=CID,
                                 prev_sha=sha_before, head=HEAD_B)
    assert cas["changes"][0]["field"] == "head"
    assert cas["changes"][0]["from"] == HEAD_A and cas["changes"][0]["to"] == HEAD_B


# -------------------------------------------------------------- T14 -------

def test_t14_readonly_real_state_checks_green(sandbox):
    """Real registry parses through the canonical loader; this round's cycle
    is ABSENT; locks inspect verdict parses; listing digest stable; and all
    of it leaves the real state byte-identical."""
    real_paths = [
        rs.REAL_ROOT_REGISTRY,
        rs.REAL_REPO_ROOT / "plans" / "ACTIVE_CYCLES.json",
        rs.REAL_HEAVY_RUNTIME / "heavy_worker.lock",
        rs.REAL_HEAVY_RUNTIME / "heavy_worker.registry.json",
        rs.REAL_HEAVY_RUNTIME / "heavy_worker.history.jsonl",
        rs.REAL_HEAVY_RUNTIME / "scheduler_jobs.json",
    ]
    before = rs.sha_snapshot(real_paths)

    report = rs.check_real_registry()
    assert report["schema"] == "cycle_registry@1"
    assert report["n_cycles"] >= 1
    assert report["unique_cycle_ids"] == report["n_cycles"]
    assert report["assert_absent"][rs.CYCLE_ID_THIS_ROUND] is False
    assert report["all_absent_as_required"] is True

    locks = rs.real_locks_inspect()
    assert locks["verdict"] in ("FREE_PROVEN", "HELD_PROVEN", "CONTROL_STATE_DRIFT")
    assert locks["known_verdict"] is True
    assert locks["verdict"] == "FREE_PROVEN", (
        f"machine-wide heavy lock not free during the suite: {locks['reason']}")

    listing = rs.governance_listing_digest()
    assert listing["files"]["heavy_worker.lock"]["bytes"] == 0
    assert "heavy_worker.registry.json" in listing["files"]

    after = rs.sha_snapshot(real_paths)
    assert before == after, "real state changed during read-only checks"
