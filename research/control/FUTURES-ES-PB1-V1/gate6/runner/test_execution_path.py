#!/usr/bin/env python
"""test_execution_path.py — T1..T10 proof suite for the REAL scored
execution path of FUTURES-ES-PB1-V1 (scored_runner.py + scored_executor.py,
LAUNCH_CONTRACT_V2 §4 + §v2.1).

Every test drives the PRODUCTION PATH (the real scored_runner.py CLI and the
real scored_executor.run_scored_execution) over SYNTHETIC fixtures inside
the SANDBOX ONLY — gate6/runner/scratch/synthetic/sandbox (built by
make_sandbox_fixtures.py, committed generator; the fake GO artifact exists
ONLY inside that sandbox). The ROOT repo is never written; the real ledger,
real registry and machine-wide heavy-lock runtime are never touched.

  T1  happy path (sandbox, synthetic): execution completes; 24 ledger rows
      (observed=24 exactly); outputs published (24 identities + trades
      index + summary in BOTH passes); twin byte-identical; terminal
      handoff written with EXECUTION_COMPLETE; exit 0.
  T2  reproduction: two independent sandbox runs; cross-run pass_a
      manifests byte-match (plus each run's internal twin).
  T3  twin mismatch: injected perturbation of one output between passes
      => terminal TWIN_MISMATCH, non-zero exit, NEVER success.
  T4  publication failure: injected read-only output dir mid-run =>
      ledger rows still counted observed (published=false), run fail-closed
      non-zero.
  T5  interrupted + retry: abort after k identities => k terminals;
      retry completes the remaining 24-k with NO double-count
      (observed=24), NO recompute of terminal slots (skip receipts),
      ledger bytes prefix-preserved.
  T6  the pre-existing refusal suite (test_runner_refusals.py) still
      passes unchanged (14/14).
  T7  lock released on exception: injected executor exception =>
      lock file released (not flock'd), registry row cleared, ledger
      chain consistent, exit non-zero.
  T8  production-default safety: no sandbox + no GO => refused (existing
      behavior); code-inspection (grep + AST) that the default path has no
      fixture references and the lock-runtime redirect is sandbox-confined;
      --sandbox-root + real-root path mix => refused.
  T9  reopen-after-execution: fresh TrialLedger over the T1 ledger verifies
      ok, observed=24, and the reopen mutates nothing.
  T10 registry/head/GO invalid variants refused at the RUNNER boundary in
      sandbox mode AND at the EXECUTOR boundary (direct calls): TOCTOU
      drift => REFUSED_CONTROL_STATE_DRIFT row; pre-held lock =>
      NOT_RUN_RESOURCE_CONFLICT (75).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python \\
      research/control/FUTURES-ES-PB1-V1/gate6/runner/test_execution_path.py
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent
GATE6_DIR = RUNNER_DIR.parent
WORKTREE = str(RUNNER_DIR.parents[4])
SYN_DIR = RUNNER_DIR / "scratch" / "synthetic"
SB_ROOT = SYN_DIR / "sandbox"
LOGS = SYN_DIR / "test_logs"
RUNNER = str(RUNNER_DIR / "scored_runner.py")
EXECUTOR = str(RUNNER_DIR / "scored_executor.py")
GENERATOR = str(SYN_DIR / "make_sandbox_fixtures.py")
RESEARCH_PKG = str(Path(WORKTREE) / "research")

CYCLE_ID = "FUTURES-ES-PB1-V1"
GO_IN_SB = str(SB_ROOT / "research/control/FUTURES-ES-PB1-V1/authority/"
                       "GO_RECORDED.json")
CONTRACT_IN_SB = str(SB_ROOT / "launch_contract.json")
REGISTRY_IN_SB = str(SB_ROOT / "registry/CYCLE_REGISTRY.rowcopy.json")
CANONICAL_GO_PHRASE = "GO FUTURES-ES-PB1-V1 SCORED EXECUTION"

for p in (RESEARCH_PKG, str(GATE6_DIR), str(RUNNER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


def ensure_fixtures():
    if not (SB_ROOT / "PROVENANCE.md").is_file():
        gen = subprocess.run([sys.executable, GENERATOR, "--out",
                              str(SB_ROOT)], capture_output=True, text=True,
                             timeout=600)
        assert gen.returncode == 0, gen.stderr[-2000:]
    # a stale registry copy (pinned to an older HEAD by an earlier
    # generation) is regenerated so the row always carries the real HEAD
    gen = subprocess.run([sys.executable, GENERATOR, "--out", str(SB_ROOT),
                          "--force"], capture_output=True, text=True,
                         timeout=600)
    assert gen.returncode == 0, gen.stderr[-2000:]


def sandbox_argv(ledger: str, run_label: str, extra=None) -> list[str]:
    return ["--sandbox-root", str(SB_ROOT),
            "--contract", CONTRACT_IN_SB,
            "--registry-path", REGISTRY_IN_SB,
            "--go-artifact", GO_IN_SB,
            "--ledger-path", ledger,
            "--run-label", run_label] + (extra or [])


def run_runner(argv: list[str]):
    return subprocess.run([sys.executable, RUNNER] + argv,
                          capture_output=True, text=True, timeout=900)


def identity_ids() -> list[str]:
    con = json.loads(Path(CONTRACT_IN_SB).read_text(encoding="utf-8"))
    return con["embedded_laws"]["identity_ids"]


def read_ledger_rows(path) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        return []
    return [json.loads(line) for line in
            p.read_text(encoding="utf-8").splitlines() if line.strip()]


def log(name: str, proc) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (LOGS / f"{name}.stderr.txt").write_text(
        f"exit_code={proc.returncode}\n{proc.stderr}", encoding="utf-8")


def fresh_ledger(name: str) -> str:
    p = SB_ROOT / "ledger" / f"{name}.jsonl"
    if p.exists():
        p.unlink()
    return str(p)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_fixtures()

    def ledger_state(self, path) -> dict:
        import trial_ledger
        led = trial_ledger.TrialLedger(path, identity_ids())
        return led.summary()

    # ---------------------------------------------------------------- T1
    def test_T1_happy_path_executes_all_24(self):
        ledger = fresh_ledger("t1")
        proc = run_runner(sandbox_argv(ledger, "t1"))
        log("T1", proc)
        self.assertEqual(proc.returncode, 0,
                         f"rc={proc.returncode}\n{proc.stderr[-2500:]}")
        manifest = json.loads(proc.stdout)
        execution = manifest["execution"]
        self.assertEqual(execution["terminal_state"], "EXECUTION_COMPLETE")
        self.assertTrue(manifest["gate_verdict"]["allowed"])
        handoff = json.loads((SB_ROOT / "runs/t1/terminal_handoff.json")
                             .read_text(encoding="utf-8"))
        self.assertEqual(handoff["verdict"], "EXECUTION_COMPLETE")
        self.assertEqual(handoff["lock_released_status"], "FINISHED")
        self.assertTrue(handoff["twin_compare"]["byte_match"],
                        handoff["twin_compare"])
        self.assertTrue(handoff["reconciliation_pass"])
        self.assertEqual(handoff["sandbox_stamp"], "SYNTHETIC-SANDBOX")
        # ledger: exactly 24 identity rows, all PASS, observed == 24
        rows = [r for r in read_ledger_rows(ledger) if r.get("identity_id")]
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(r["status"] == "PASS" for r in rows))
        self.assertTrue(all(r["published"] for r in rows))
        summary = self.ledger_state(ledger)
        self.assertEqual(summary["observed_denominator"], 24)
        self.assertEqual(summary["status_counts"]["PASS"], 24)
        self.assertTrue(summary["complete"])
        # outputs published in BOTH passes, stamped SYNTHETIC-SANDBOX
        for pass_dir in ("pass_a", "pass_b"):
            files = sorted(p.name for p in
                           (SB_ROOT / "runs/t1" / pass_dir).glob("*.json"))
            self.assertEqual(len(files), 26)  # 24 identities + index + summary
        rec = json.loads((SB_ROOT / "runs/t1/pass_a/"
                          "FBES1-PB1-CONT-UP-D0-S2.json").read_text())
        self.assertEqual(rec["run_class"], "SYNTHETIC-SANDBOX")
        self.assertEqual(rec["sandbox_stamp"], "SYNTHETIC-SANDBOX")
        self.assertIn("trades", rec)

    # ---------------------------------------------------------------- T2
    def test_T2_two_independent_runs_are_byte_twins(self):
        led_a = fresh_ledger("t2a")
        led_b = fresh_ledger("t2b")
        pa = run_runner(sandbox_argv(led_a, "t2a"))
        pb = run_runner(sandbox_argv(led_b, "t2b"))
        log("T2", pa)
        log("T2-second", pb)
        self.assertEqual(pa.returncode, 0, pa.stderr[-2000:])
        self.assertEqual(pb.returncode, 0, pb.stderr[-2000:])
        import trial_ledger
        man_a = trial_ledger.twin_manifest(str(SB_ROOT / "runs/t2a/pass_a"))
        man_b = trial_ledger.twin_manifest(str(SB_ROOT / "runs/t2b/pass_a"))
        cmpres = trial_ledger.twin_compare(man_a, man_b)
        self.assertTrue(cmpres["byte_match"], cmpres)
        # each run's own internal twin also matched
        for lbl in ("t2a", "t2b"):
            h = json.loads((SB_ROOT / "runs" / lbl /
                            "terminal_handoff.json").read_text())
            self.assertTrue(h["twin_compare"]["byte_match"])

    # ---------------------------------------------------------------- T3
    def test_T3_twin_perturbation_is_TWIN_MISMATCH_never_success(self):
        ledger = fresh_ledger("t3")
        fault = json.dumps({"type": "twin_perturb",
                            "identity": "FBES1-PB1-CONT-UP-D0-S2"})
        proc = run_runner(sandbox_argv(ledger, "t3",
                                       ["--sandbox-fault", fault]))
        log("T3", proc)
        self.assertNotEqual(proc.returncode, 0)
        execution = json.loads(proc.stdout)["execution"]
        self.assertEqual(execution["terminal_state"], "TWIN_MISMATCH")
        self.assertEqual(execution["verdict"], "EXECUTION_FAILED")
        self.assertIn("TWIN_MISMATCH", execution["failure_reasons"])
        self.assertNotIn("WOULD EXECUTE", proc.stderr)
        # the computed results were still recorded to the denominator
        self.assertEqual(self.ledger_state(ledger)["observed_denominator"], 24)
        handoff = json.loads((SB_ROOT / "runs/t3/terminal_handoff.json")
                             .read_text())
        self.assertIn("TWIN_MISMATCH", handoff["failure_reasons"])
        self.assertFalse(handoff["twin_compare"]["byte_match"])
        self.assertEqual(handoff["lock_released_status"], "FAILED")

    # ---------------------------------------------------------------- T4
    def test_T4_publication_failure_counts_observed_fail_closed(self):
        ledger = fresh_ledger("t4")
        fault = json.dumps({"type": "publication",
                            "identity": "FBES1-PLA-D0-S2"})
        proc = run_runner(sandbox_argv(ledger, "t4",
                                       ["--sandbox-fault", fault]))
        log("T4", proc)
        self.assertNotEqual(proc.returncode, 0)
        execution = json.loads(proc.stdout)["execution"]
        self.assertEqual(execution["terminal_state"], "PUBLICATION_FAILURE")
        rows = [r for r in read_ledger_rows(ledger) if r.get("identity_id")]
        self.assertEqual(len(rows), 24)          # every computed result counted
        # the injected read-only dir starts at FBES1-PLA-D0-S2 (frozen index
        # 20): PLA/ALW/FLAT/DOSE compute but cannot publish (published=false)
        self.assertEqual(sum(1 for r in rows if r["published"] is False), 4)
        self.assertTrue(all(r["counts_observed"] for r in rows))
        self.assertEqual(self.ledger_state(ledger)["observed_denominator"], 24)
        self.assertEqual(execution["pass_a"]["publication_failures"][0]
                         ["identity_id"], "FBES1-PLA-D0-S2")

    # ---------------------------------------------------------------- T5
    def test_T5_interrupted_run_retry_skips_terminal_slots(self):
        ledger = fresh_ledger("t5")
        fault = json.dumps({"type": "abort", "after_k": 5})
        p1 = run_runner(sandbox_argv(ledger, "t5-fault",
                                     ["--sandbox-fault", fault]))
        log("T5-abort", p1)
        self.assertNotEqual(p1.returncode, 0)
        execution = json.loads(p1.stdout)["execution"]
        self.assertEqual(execution["terminal_state"], "ABORTED_SANDBOX_FAULT")
        rows = [r for r in read_ledger_rows(ledger) if r.get("identity_id")]
        self.assertEqual(len(rows), 5)
        self.assertEqual(self.ledger_state(ledger)["observed_denominator"], 5)
        prior_bytes = Path(ledger).read_bytes()

        p2 = run_runner(sandbox_argv(ledger, "t5-retry"))
        log("T5-retry", p2)
        self.assertEqual(p2.returncode, 0, p2.stderr[-2500:])
        execution = json.loads(p2.stdout)["execution"]
        self.assertEqual(execution["terminal_state"], "EXECUTION_COMPLETE")
        # budget law: 24 identity rows TOTAL (5 old + 19 new), observed == 24
        rows = [r for r in read_ledger_rows(ledger) if r.get("identity_id")]
        self.assertEqual(len(rows), 24)
        summary = self.ledger_state(ledger)
        self.assertEqual(summary["observed_denominator"], 24)
        self.assertTrue(summary["complete"])
        # interrupted-run law: the 5 terminal slots were SKIPPED, never
        # recomputed, and their published bytes were copied unchanged
        skipped = execution["pass_a"]["skipped_terminal"]
        computed = execution["pass_a"]["computed"]
        first5 = identity_ids()[:5]
        self.assertEqual(skipped, first5)
        self.assertEqual(len(computed), 19)
        self.assertEqual(sorted(set(computed) & set(skipped)), [])
        for iid in first5:
            a = (SB_ROOT / "runs/t5-fault/pass_a" / f"{iid}.json").read_bytes()
            b = (SB_ROOT / "runs/t5-retry/pass_a" / f"{iid}.json").read_bytes()
            self.assertEqual(a, b, iid)
        # ledger bytes prefix-preserved across the retry
        self.assertTrue(Path(ledger).read_bytes().startswith(prior_bytes))

    # ---------------------------------------------------------------- T6
    def test_T6_existing_refusal_suite_still_passes(self):
        proc = subprocess.run([sys.executable, str(RUNNER_DIR /
                                                    "test_runner_refusals.py")],
                              capture_output=True, text=True, timeout=900)
        log("T6", proc)
        self.assertEqual(proc.returncode, 0, proc.stderr[-3000:])
        self.assertIn("OK", proc.stderr.splitlines()[-1])

    # ---------------------------------------------------------------- T7
    def test_T7_exception_releases_lock_and_keeps_ledger_consistent(self):
        from governance import heavy_lock
        ledger = fresh_ledger("t7")
        fault = json.dumps({"type": "exception", "at_index": 7})
        proc = run_runner(sandbox_argv(ledger, "t7",
                                       ["--sandbox-fault", fault]))
        log("T7", proc)
        self.assertNotEqual(proc.returncode, 0)
        execution = json.loads(proc.stdout)["execution"]
        self.assertEqual(execution["terminal_state"], "COMPUTE_FAILURE")
        self.assertEqual(execution["lock_released_status"], "FAILED")
        # lock released: the flock is free and the registry row is cleared
        lock_path = SB_ROOT / "heavy_runtime" / heavy_lock.LOCK_NAME
        self.assertEqual(heavy_lock.flock_state(lock_path), "free")
        self.assertFalse((SB_ROOT / "heavy_runtime" /
                          heavy_lock.REGISTRY_NAME).exists())
        # ledger consistent (chain verifies), 7 computed terminals
        import trial_ledger
        led = trial_ledger.TrialLedger(ledger, identity_ids())
        self.assertTrue(led.verify()["ok"])
        self.assertEqual(led.verify()["observed_denominator"], 7)

    # ---------------------------------------------------------------- T8
    def test_T8_production_default_refuses_and_has_no_fixture_bypass(self):
        import tempfile
        with tempfile.TemporaryDirectory(prefix="pb1_t8_") as tmp:
            # (a) production default (no --sandbox-root), no GO => refused.
            # The refusal reason depends on the live registry state: a
            # matched head refuses REFUSED_NO_GO; the live ancestor-lagged
            # row refuses REFUSED_CONTROL_STATE_DRIFT (R0 folds in first —
            # same law as the refusal suite's real-state smoke test).
            # Either is the pre-GO law.
            ledger = str(Path(tmp) / "ledger.jsonl")
            proc = run_runner(["--worktree", WORKTREE,
                               "--ledger-path", ledger,
                               "--lock-runtime-dir",
                               str(Path(tmp) / "heavy_runtime")])
            log("T8a", proc)
            self.assertEqual(proc.returncode, 2)
            rows = read_ledger_rows(ledger)
            reasons = {r.get("reason") for r in rows
                       if r.get("status") == "REFUSED"}
            self.assertTrue(reasons & {"REFUSED_NO_GO",
                                       "REFUSED_CONTROL_STATE_DRIFT"},
                            f"rows={rows}")
            if "REFUSED_CONTROL_STATE_DRIFT" in reasons:
                self.assertTrue(any("LAG_ANCESTOR" in (r.get("note") or "")
                                    for r in rows),
                                "head-lag refusal must disclose the lag")
        # (b) code inspection: no fixture references anywhere in the
        # default (production) path sources; the lock-runtime redirect
        # exists ONLY inside sandbox-named code (AST check)
        for src in (RUNNER, EXECUTOR):
            text = Path(src).read_text(encoding="utf-8")
            self.assertNotIn("scratch/synthetic", text, src)
        exec_text = Path(EXECUTOR).read_text(encoding="utf-8")
        tree = ast.parse(exec_text)
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        def enclosing_funcs(node):
            names = []
            while node is not None:
                node = parents.get(node)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.append(node.name)
            return names

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) \
                    and node.attr == "RUNTIME_DIRNAME":
                fns = enclosing_funcs(node)
                self.assertTrue(fns, "RUNTIME_DIRNAME at module level")
                self.assertTrue(any("sandbox" in fn for fn in fns),
                                f"RUNTIME_DIRNAME touched outside sandbox "
                                f"code: {fns}")
        import scored_executor
        self.assertIsNone(scored_executor.resolve_lock_runtime(None))
        self.assertTrue(scored_executor.resolve_lock_runtime("/x/y")
                        .endswith("heavy_runtime"))
        # (c) --sandbox-root combined with a real-root path => refused
        real_freeze = os.path.join(
            WORKTREE, "research/control/FUTURES-ES-PB1-V1/final/"
                      "selection_freeze_v3.json")
        proc = run_runner(sandbox_argv(fresh_ledger("t8c"), "t8c",
                                       ["--freeze-path", real_freeze]))
        log("T8c", proc)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("SANDBOX-ISOLATION", proc.stderr)
        rr = json.loads((SB_ROOT / "refusal_record.json").read_text())
        self.assertEqual(rr["reason"], "REFUSED_CONTROL_STATE_DRIFT")
        self.assertIn("freeze-path", rr["detail"]["violations"])

    # ---------------------------------------------------------------- T9
    def test_T9_reopen_after_execution_prefix_preserved(self):
        import trial_ledger
        ledger = str(SB_ROOT / "ledger" / "t1.jsonl")
        before = Path(ledger).read_bytes()
        led = trial_ledger.TrialLedger(ledger, identity_ids())
        self.assertTrue(led.verify()["ok"])
        summary = led.summary()
        self.assertEqual(summary["observed_denominator"], 24)
        self.assertTrue(summary["complete"])
        self.assertEqual(Path(ledger).read_bytes(), before)

    # ---------------------------------------------------------------- T10
    def test_T10_invalid_variants_refused_at_runner_and_executor(self):
        # (a) runner boundary: tampered sandbox GO (paraphrase) inside the box
        bad_go_dir = SB_ROOT / "tmp_t10"
        bad_go_dir.mkdir(exist_ok=True)
        go = json.loads(Path(GO_IN_SB).read_text())
        go["key_2_owner_go"]["verbatim"] = \
            "GO FUTURES-ES-PB1-V1 SCORRED EXECUTION"
        bad_go = bad_go_dir / "GO_tampered.json"
        bad_go.write_text(json.dumps(go, indent=1), encoding="utf-8")
        proc = run_runner(sandbox_argv(fresh_ledger("t10a"), "t10a",
                                       ["--go-artifact", str(bad_go)]))
        log("T10a", proc)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("REFUSED_NO_GO", proc.stderr)

        # (b) runner boundary: registry row copy with a diverged head
        reg = json.loads(Path(REGISTRY_IN_SB).read_text())
        reg["cycles"][0]["head"] = "deadbeef" + "0" * 32
        bad_reg = bad_go_dir / "registry_bogus.json"
        bad_reg.write_text(json.dumps(reg, indent=1), encoding="utf-8")
        proc = run_runner(sandbox_argv(fresh_ledger("t10b"), "t10b",
                                       ["--registry-path", str(bad_reg)]))
        log("T10b", proc)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("REFUSED_CONTROL_STATE_DRIFT", proc.stderr)

        # (c) runner boundary: tampered sandbox freeze (drift) inside the box
        fz = Path(SB_ROOT / "research/control/FUTURES-ES-PB1-V1/final/"
                  "selection_freeze_v3.json").read_bytes()
        bad_fz = bad_go_dir / "selection_freeze_v3.json"
        bad_fz.write_bytes(fz.replace(b'"total_eval_sessions"',
                                      b'"total_eval_sessionsX"', 1))
        proc = run_runner(sandbox_argv(fresh_ledger("t10c"), "t10c",
                                       ["--freeze-path", str(bad_fz)]))
        log("T10c", proc)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("REFUSED_DRIFT", proc.stderr)

        # (d) EXECUTOR boundary: TOCTOU drift after acquire
        import scored_executor
        scratch = SB_ROOT / "tmp_t10"
        rc, terminal = scored_executor.run_scored_execution({
            "cycle_id": CYCLE_ID, "sandbox_root": str(SB_ROOT),
            "worktree": WORKTREE, "contract_path": CONTRACT_IN_SB,
            "builder_path": str(SB_ROOT / "research/control/FUTURES-ES-PB1-"
                                "V1/final/dryrun_builder_v3.py"),
            "builder_pin_sha": "0" * 64,
            "builder_overrides": None,
            "identity_ids": identity_ids(),
            "ledger_path": str(scratch / "t10d_ledger.jsonl"),
            "lock_runtime_dir": str(SB_ROOT / "heavy_runtime"),
            "run_root": str(scratch / "t10d_run"),
            "command": ["t10d"], "fault": None,
            "reverify_authority": lambda: [
                "pin operative_freeze_v3 drift post-acquire"],
        })
        self.assertEqual(rc, 2)
        self.assertEqual(terminal["terminal_state"],
                         "REFUSED_CONTROL_STATE_DRIFT")
        rows = read_ledger_rows(scratch / "t10d_ledger.jsonl")
        self.assertTrue(any(r.get("reason") ==
                            "REFUSED_CONTROL_STATE_DRIFT" for r in rows))

        # (e) EXECUTOR boundary: pre-held sandbox lock => conflict 75
        import fcntl
        from governance import heavy_lock
        rt = SB_ROOT / "heavy_runtime"
        rt.mkdir(parents=True, exist_ok=True)
        fd = os.open(rt / heavy_lock.LOCK_NAME, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            holder = {"cycle_id": "OTHER-CYCLE", "role": "HEAVY-WORKER",
                      "pid": os.getpid(),
                      "process_start_token":
                          heavy_lock.process_start_token(os.getpid()),
                      "worktree": WORKTREE, "status": "RUNNING",
                      "started_at": "1970-01-01T00:00:00Z"}
            (rt / heavy_lock.REGISTRY_NAME).write_text(
                json.dumps(holder, indent=1), encoding="utf-8")
            rc, terminal = scored_executor.run_scored_execution({
                "cycle_id": CYCLE_ID, "sandbox_root": str(SB_ROOT),
                "worktree": WORKTREE, "contract_path": CONTRACT_IN_SB,
                "builder_path": "unused",
                "builder_pin_sha": "0" * 64, "builder_overrides": None,
                "identity_ids": identity_ids(),
                "ledger_path": str(scratch / "t10e_ledger.jsonl"),
                "lock_runtime_dir": str(rt),
                "run_root": str(scratch / "t10e_run"),
                "command": ["t10e"], "fault": None,
                "reverify_authority": lambda: [],
            })
            self.assertEqual(rc, 75)
            self.assertEqual(terminal["terminal_state"],
                             "NOT_RUN_RESOURCE_CONFLICT")
            rows = read_ledger_rows(scratch / "t10e_ledger.jsonl")
            self.assertTrue(any(r.get("reason") ==
                                "NOT_RUN_RESOURCE_CONFLICT" for r in rows))
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            (rt / heavy_lock.REGISTRY_NAME).unlink(missing_ok=True)

        # (f) fault injection is impossible in production mode
        with self.assertRaises(AssertionError):
            scored_executor.run_scored_execution({
                "sandbox_root": None, "fault": {"type": "abort",
                                                "after_k": 1}})


if __name__ == "__main__":
    unittest.main(verbosity=2)
