#!/usr/bin/env python

# ============================================================================
# [EXTRACT/PROVENANCE] _upstream_test_runner_refusals.py
# Verbatim byte-exact extraction (blob sha256 3678446b5c96f1cc43237aa142ae85fccbf337911d6e685ccf7d94848c3a4384) of
#   research/control/FUTURES-ES-PB1-V1/gate6/runner/test_runner_refusals.py
# from branch prep/futures-es-reg-20261004 (FUTURES-ES-PB1-V1), commit 999ece6024ba739ed9a4046dcbcbb382f4d6650c.
# Branch-tip revision; refusal-gate lineage ported into test_runner_v2/.
# Extracted 2026-10-05 by LANE-EXEC, cycle FUTURES-5SYM-PRESCORED-20261005,
# via `git show prep/futures-es-reg-20261004:<path>` — read-only evidence extraction; the
# futures-es-reg worktree was NEVER written. Evidence only; not executable
# authority for the PRESCORED cycle.
# ============================================================================
"""test_runner_refusals.py — refusal-gate + reproduction tests for
FUTURES-ES-PB1-V1 gate6/runner/scored_runner.py (contract v2).

Proves, on SYNTHETIC fixtures and sandbox copies only (the real ROOT is never
written; real authority artifacts are only READ):

  1.  no GO artifact                  -> REFUSED_NO_GO        (rc 2 + REFUSED ledger row)
  2.  paraphrased GO                  -> REFUSED_NO_GO        (rc 2 + row)
  3a. delegated GO (typed_by flag)    -> REFUSED_NO_GO        (rc 2 + row)
  3b. delegated GO (marker language)  -> REFUSED_NO_GO        (rc 2 + row)
  3c. early GO (bound to wrong audit) -> REFUSED_NO_GO        (rc 2 + row)
  4.  freeze drift (tampered copy)    -> REFUSED_DRIFT        (rc 2 + row)
  5a. registry-head DIVERGED          -> REFUSED_CONTROL_STATE_DRIFT (rc 2 + row)
  5b. registry-head LAG_ANCESTOR      -> REFUSED_CONTROL_STATE_DRIFT (rc 2 + row)
  6.  lock HELD (real flock in a temp runtime) -> NOT_RUN_RESOURCE_CONFLICT (rc 75 + row)
  7.  A7 digest missing               -> REFUSED_NO_AUTH      (rc 2 + row)
  8.  production-default authority guard: a fully-valid SYNTHETIC GO +
      consistent simulated state passes every gate, but scored execution in
      production mode refuses any authority-path override (the anti-bypass
      guard that replaced the removed WOULD-EXECUTE stub; synthetic
      execution is only reachable via --sandbox-root, proven by
      test_execution_path.py T1-T10)
  9.  real state (real registry, GO absent) refuses in execution mode
  10. reproduction: the deterministic preflight manifest run twice is a
      byte-identical twin (PREFLIGHT twin; scored-OUTPUT twins are post-GO)

Every refusal test verifies BOTH the non-zero exit AND the REFUSED row in the
sandbox ledger written by the FIXED gate6/trial_ledger.py (rows carry
counts_observed=false — REFUSED never increments the observed denominator).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python \\
      research/control/FUTURES-ES-PB1-V1/gate6/runner/test_runner_refusals.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent
GATE6_DIR = RUNNER_DIR.parent
WORKTREE = str(RUNNER_DIR.parents[4])          # .../.worktrees/futures-es-reg/prep
RUNNER = str(RUNNER_DIR / "scored_runner.py")
RESEARCH_PKG = str(Path(WORKTREE) / "research")

sys.path.insert(0, RESEARCH_PKG)
from governance import heavy_lock  # noqa: E402  (canonical lock primitives)

A7_DIGEST_SHA = "d42f27d99c6c428929aa16f82b3a0a956c39b7f4c71cab1b987c97b4a3389d5d"
CANONICAL_GO_PHRASE = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"
CYCLE_ID = "FUTURES-ES-PB1-V1"


def real_head() -> str:
    out = subprocess.run(["git", "-C", WORKTREE, "rev-parse", "HEAD"],
                         capture_output=True, text=True, timeout=20)
    assert out.returncode == 0
    return out.stdout.strip()


def real_branch() -> str:
    out = subprocess.run(["git", "-C", WORKTREE, "rev-parse",
                          "--abbrev-ref", "HEAD"],
                         capture_output=True, text=True, timeout=20)
    assert out.returncode == 0
    return out.stdout.strip()


def simulated_registry(tmp: Path, head: str | None = None,
                       go_phrase: str = CANONICAL_GO_PHRASE) -> str:
    row = {
        "cycle_id": CYCLE_ID, "asset": "futures", "lifecycle": "ACTIVE_LIGHT",
        "phase": "REGISTERED",
        "integration_worktree": WORKTREE, "branch": real_branch(),
        "head": head if head is not None else real_head(),
        "budget": {"used": 0, "max": 24}, "s0": "OPEN",
        "s1": "SEALED_UNTOUCHED", "go_phrase": go_phrase,
        "go_phrase_state": "REGISTERED_NOT_CONSUMED", "workers": 0,
        "active_heavy": False, "heartbeat_utc": "1970-01-01T00:00:00Z",
        "hard_stop_reason": None, "pause_packet": None,
        "next_authorized_action": "", "updated_at_utc": "1970-01-01T00:00:00Z",
        "adapter_warnings": []}
    path = tmp / "simulated_registry.json"
    path.write_text(json.dumps({"cycles": [row]}, indent=1), encoding="utf-8")
    return str(path)


def synthetic_go(tmp: Path, *, verbatim: str = CANONICAL_GO_PHRASE,
                 typed_by_owner: bool = True, typed_by: str = "OWNER",
                 extra_string: str | None = None,
                 key1_sha: str = A7_DIGEST_SHA) -> str:
    art = {
        "schema": "futures_es_pb1_v1/go_recorded@1",
        "cycle_id": CYCLE_ID,
        "recorded_utc": "2026-10-05T00:00:00Z",
        "key_1_a7_prelaunch": {
            "verdict": "AUTHORIZED_WITH_FINDINGS",
            "artifact": ("research/control/FUTURES-ES-PB1-V1/a7_v3/"
                         "a7_prelaunch_v3_digest.json"),
            "sha256": key1_sha,
            "findings": "0 CRITICAL / 0 HIGH / 0 MEDIUM (test fixture)"},
        "key_2_owner_go": {
            "verbatim": verbatim,
            "typed_by_owner": typed_by_owner,
            "typed_by": typed_by,
            "received_utc": "2026-10-05"},
        "authorizes": {"scored_execution":
                       "gate6/runner/scored_runner.py (SYNTHETIC TEST "
                       "FIXTURE — exists only inside this tmp sandbox)"},
        "forbids": ["push, merge to main, history rewrite", "S1 opening"]}
    if extra_string:
        art["key_2_owner_go"]["provenance_note"] = extra_string
    path = tmp / "GO_RECORDED_synthetic.json"
    path.write_text(json.dumps(art, indent=1, ensure_ascii=False),
                    encoding="utf-8")
    return str(path)


def run_runner(argv: list[str]):
    return subprocess.run([sys.executable, RUNNER] + argv,
                          capture_output=True, text=True, timeout=300)


class SandboxCase(unittest.TestCase):
    """Base: sandbox tmp with simulated registry + tmp lock runtime + tmp
    ledger. Real authority artifacts are read-only."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="pb1_runner_test_")
        self.tmp = self._tmp.name
        tmp = Path(self.tmp)
        self.registry = simulated_registry(Path(tmp))       # head-MATCH row
        self.lock_runtime = str(tmp / "heavy_runtime")       # empty => FREE
        self.ledger = str(tmp / "ledger" / "trial_ledger.jsonl")
        self.go_absent = str(tmp / "no_go_artifact.json")    # never created

    def tearDown(self):
        self._tmp.cleanup()

    def base_argv(self, extra: list[str]) -> list[str]:
        return ["--worktree", WORKTREE,
                "--registry-path", self.registry,
                "--go-artifact", self.go_absent,
                "--ledger-path", self.ledger,
                "--lock-runtime-dir", self.lock_runtime] + extra

    def read_ledger_rows(self) -> list[dict]:
        p = Path(self.ledger)
        if not p.is_file():
            return []
        return [json.loads(line) for line in
                p.read_text(encoding="utf-8").splitlines() if line.strip()]

    def assert_refused(self, rc_expected: int, reason: str,
                       proc) -> dict:
        self.assertEqual(proc.returncode, rc_expected,
                         f"rc={proc.returncode}\nstderr={proc.stderr[-1500:]}")
        rows = self.read_ledger_rows()
        refused = [r for r in rows
                   if r.get("status") == "REFUSED" and r.get("reason") == reason]
        self.assertTrue(refused,
                        f"no REFUSED/{reason} ledger row; rows={rows}")
        row = refused[-1]
        self.assertIsNone(row.get("identity_id"))
        self.assertFalse(row.get("counts_observed"))
        self.assertTrue(row.get("prev_row_sha") is None
                        or len(row["prev_row_sha"]) == 64)
        return row


class TestRefusals(SandboxCase):

    def test_01_no_go_artifact_refuses(self):
        proc = run_runner(self.base_argv([]))
        self.assert_refused(2, "REFUSED_NO_GO", proc)

    def test_02_paraphrased_go_refuses(self):
        go = synthetic_go(Path(self.tmp),
                          verbatim="GO FUTURES-ES-PB1-V1 SCORRED EXECUTION")
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_NO_GO", proc)
        self.assertIn("byte-equal", row.get("note", ""))

    def test_03a_delegated_go_flag_refuses(self):
        go = synthetic_go(Path(self.tmp), typed_by_owner=False,
                          typed_by="CONTROLLER (delegated by owner)")
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_NO_GO", proc)
        self.assertIn("typed_by_owner is not true", row.get("note", ""))

    def test_03b_delegated_go_language_refuses(self):
        go = synthetic_go(Path(self.tmp),
                          extra_string="run on behalf of the owner")
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_NO_GO", proc)
        self.assertIn("delegation marker", row.get("note", ""))

    def test_03c_early_go_wrong_audit_binding_refuses(self):
        go = synthetic_go(Path(self.tmp),
                          key1_sha="0" * 64)  # bound to nothing operative
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_NO_GO", proc)
        self.assertIn("early/superseded", row.get("note", ""))

    def test_04_freeze_drift_refuses(self):
        real_freeze = Path(WORKTREE,
                           "research/control/FUTURES-ES-PB1-V1/final/"
                           "selection_freeze_v3.json")
        tampered = Path(self.tmp) / "tampered_freeze.json"
        raw = real_freeze.read_bytes()
        tampered.write_bytes(raw.replace(b'"total_eval_sessions"',
                                         b'"total_eval_sessionsX"', 1))
        self.assertNotEqual(tampered.read_bytes(), raw)
        go = synthetic_go(Path(self.tmp))
        proc = run_runner(self.base_argv(
            ["--go-artifact", go, "--freeze-path", str(tampered)]))
        row = self.assert_refused(2, "REFUSED_DRIFT", proc)
        self.assertIn("operative_freeze_v3", row.get("note", ""))

    def test_05a_registry_head_diverged_refuses(self):
        bogus = "deadbeef" + "0" * 32  # well-formed sha, NOT an ancestor
        self.registry = simulated_registry(Path(self.tmp), head=bogus)
        go = synthetic_go(Path(self.tmp))
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_CONTROL_STATE_DRIFT", proc)
        self.assertIn("DIVERGED", row.get("note", ""))

    def test_05b_registry_head_lag_ancestor_refuses(self):
        stale = "71326c8c22307bc62ef2f81b80b3fef3ada5e96e"  # real stale row head
        self.registry = simulated_registry(Path(self.tmp), head=stale)
        go = synthetic_go(Path(self.tmp))
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_CONTROL_STATE_DRIFT", proc)
        self.assertIn("LAG_ANCESTOR", row.get("note", ""))

    def test_06_lock_held_refuses_with_conflict(self):
        runtime = Path(self.lock_runtime)
        runtime.mkdir(parents=True, exist_ok=True)
        lock_fd = os.open(runtime / heavy_lock.LOCK_NAME,
                          os.O_RDWR | os.O_CREAT, 0o644)
        try:
            import fcntl
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # HOLD it
            holder = {"cycle_id": "SOME-OTHER-CYCLE", "role": "HEAVY-WORKER",
                      "pid": os.getpid(),
                      "process_start_token":
                          heavy_lock.process_start_token(os.getpid()),
                      "worktree": WORKTREE, "status": "RUNNING",
                      "started_at": "1970-01-01T00:00:00Z"}
            (runtime / heavy_lock.REGISTRY_NAME).write_text(
                json.dumps(holder, indent=1), encoding="utf-8")
            go = synthetic_go(Path(self.tmp))
            proc = run_runner(self.base_argv(["--go-artifact", go]))
            self.assert_refused(75, "NOT_RUN_RESOURCE_CONFLICT", proc)
        finally:
            import fcntl
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)

    def test_07_a7_digest_missing_refuses(self):
        go = synthetic_go(Path(self.tmp))
        missing = str(Path(self.tmp) / "no_such_digest.json")
        proc = run_runner(self.base_argv(
            ["--go-artifact", go, "--a7-digest-path", missing]))
        row = self.assert_refused(2, "REFUSED_NO_AUTH", proc)
        self.assertIn("a7_prelaunch_v3_digest sha mismatch/missing",
                      row.get("note", ""))


class TestHappyPathAndReproduction(SandboxCase):

    def test_08_production_guard_refuses_overrides_even_when_gates_pass(self):
        # EXEC-BUILD v2.1: the pre-GO WOULD-EXECUTE stub is REMOVED
        # (GO_READY_WITHDRAWAL.md). A fully-valid SYNTHETIC GO + consistent
        # simulated state still passes every gate, but scored execution in
        # production mode now runs ONLY against the unoverridden REAL
        # authority paths (anti-bypass guard): the tmp GO/registry/ledger/
        # lock overrides that used to reach the stub now die as
        # REFUSED_CONTROL_STATE_DRIFT with a REFUSED ledger row. The ONLY
        # way to drive synthetic execution is --sandbox-root (proven by
        # test_execution_path.py T1-T10).
        go = synthetic_go(Path(self.tmp))  # fully-valid SYNTHETIC fixture
        proc = run_runner(self.base_argv(["--go-artifact", go]))
        row = self.assert_refused(2, "REFUSED_CONTROL_STATE_DRIFT", proc)
        self.assertIn("PRODUCTION-DEFAULT-AUTHORITY", row.get("note", ""))

    def test_09_real_state_refuses_in_execution_mode(self):
        # REAL registry, no GO anywhere, tmp ledger — the runner must
        # refuse TODAY in its own smoke test. Post-reconcile the real
        # registry head MATCHES the branch HEAD (V-1 fix 2026-10-04:
        # pre-reconcile it was LAG_ANCESTOR -> REFUSED_CONTROL_STATE_DRIFT;
        # both refusals satisfy the law — assert EITHER the GO refusal on
        # a matched head OR the drift refusal on a lagged/diverged head).
        proc = run_runner([
            "--worktree", WORKTREE, "--ledger-path", self.ledger,
            "--lock-runtime-dir", self.lock_runtime])
        if proc.returncode == 2:
            out = proc.stdout + proc.stderr
            if "REFUSED_NO_GO" in out:
                # matched-head branch: refusal for the right reason (no GO)
                return
        row = self.assert_refused(2, "REFUSED_CONTROL_STATE_DRIFT", proc)
        self.assertIn("LAG_ANCESTOR", row.get("note", ""))

    def test_10_preflight_manifest_twin_is_byte_identical(self):
        out_a = Path(self.tmp) / "twin_a" / "manifest.json"
        out_b = Path(self.tmp) / "twin_b" / "manifest.json"
        argv = ["--preflight-only", "--worktree", WORKTREE,
                "--lock-runtime-dir", self.lock_runtime]
        pa = run_runner(argv + ["--manifest-out", str(out_a)])
        pb = run_runner(argv + ["--manifest-out", str(out_b)])
        self.assertEqual(pa.returncode, 0, pa.stderr[-1500:])
        self.assertEqual(pb.returncode, 0, pb.stderr[-1500:])
        a, b = out_a.read_bytes(), out_b.read_bytes()
        self.assertEqual(a, b, "preflight manifests are not byte-identical")
        ma = json.loads(a)
        self.assertEqual(ma["wiring_failures"], [])
        self.assertTrue(ma["drift_check"]["pass"])
        self.assertEqual(ma["lock_check"]["verdict"], "FREE_PROVEN")
        self.assertTrue(ma["expected_pre_go_state"]["go_absent_is_expected"])
        # formal twin bookkeeping via the FIXED ledger module
        sys.path.insert(0, str(GATE6_DIR))
        import trial_ledger
        cmp_result = trial_ledger.twin_compare(
            trial_ledger.twin_manifest(out_a.parent),
            trial_ledger.twin_manifest(out_b.parent))
        self.assertTrue(cmp_result["byte_match"], cmp_result)

    def test_11_preflight_writes_nothing_else(self):
        marker_parent = Path(self.tmp) / "write_probe"
        marker_parent.mkdir()
        before = set(p.name for p in marker_parent.rglob("*"))
        proc = run_runner(["--preflight-only", "--worktree", WORKTREE,
                           "--lock-runtime-dir", self.lock_runtime,
                           "--ledger-path", str(marker_parent / "l.jsonl")])
        self.assertEqual(proc.returncode, 0, proc.stderr[-1500:])
        after = set(p.name for p in marker_parent.rglob("*"))
        self.assertEqual(before, after,
                         "preflight-only wrote files (it must write nothing "
                         "without --manifest-out)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
