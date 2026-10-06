#!/usr/bin/env python
"""test_finalization_fix.py — F1..F10 proof suite for the FINALIZE-FIX of
scored_executor.py (cycle FUTURES-ES-PB1-V1, gate6/runner/fix2).

Every test drives the PRODUCTION execution path (the real
scored_executor.run_scored_execution) over the SYNTHETIC sandbox ONLY,
with faults injected at the boundary exactly like the controller's
repro (fix2/repro_finalization_bugs.py). No real lock, ledger, GO
artifact, panel or registry is touched; D-1..D-7 remain unratified;
no real scored outcome exists.

  F1  happy path unchanged: full run => exit 0, EXECUTION_COMPLETE,
      lock_released_status FINISHED, finalization_failures == [],
      computation_complete true, handoff written (no regression).
  F2  terminal-handoff write raises OSError => exit 4 (D-7),
      FINALIZATION_FAILURE, handoff path NEVER claimed, fallback
      terminal_handoff_ERROR.json present, computation_complete true,
      ledger rows + observed intact (24).
  F3  lock release raises (pre-unlock semantics: acquire returns a handle
      whose release raises) => exit 4, UNVERIFIED_RELEASE_RAISED, canonical
      heavy_lock.inspect() evidence recorded against the sandbox runtime,
      computation_complete true, ledger intact.
  F4  release raises AFTER actual unlock (real release called, then raise)
      => exit 4, UNVERIFIED_RELEASE_RAISED, inspect evidence records the
      measured FREE state (FREE_PROVEN) — never assumed, still fail-closed.
  F5  ledger summary raises in the finalizer (boundary patch: the 3rd
      summary() call — the finalizer's) => exit 4, ledger_summary_error +
      finalization_failures[stage=ledger_summary], rows/bytes intact.
  F6  computation error + cleanup error together => BOTH recorded (original
      COMPUTE_FAILURE never masked; exit stays 3, not 4), cleanup recorded
      in finalization_failures[], lock still released (release step
      attempted after the cleanup failure).
  F7  denominators/bytes after F2-F5: fresh reopen of every ledger used by
      F2-F5 verifies ok (chain + slots), observed == 24, file sha unchanged
      since the run (bytes never rewritten).
  F8  retry after finalization failure (T5 machinery with a
      finalization-fault twist):
      (a) abort-after-5 + release-raises => rows for the 5 completed
          identities stand, retry completes the remaining 19 with NO
          recompute of terminal slots, bytes prefix-preserved;
      (b) full computation + summary fault => exit 4, 24 rows stand, retry
          skips ALL 24 terminal slots (computed == []), exit 0.
  F9  the FULL existing suites still pass unchanged:
      test_execution_path.py (T1-T10) + test_runner_refusals.py (14).
  F10 production-default safety unchanged: fault injection is
      non-constructible in production (AssertionError); no fixture
      references; no force-unlock / kill / unlink / flock primitives in the
      executor source (inspect is the only post-failure lock mechanism);
      the lock-runtime redirect stays sandbox-confined (AST).

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python \\
      research/control/FUTURES-ES-PB1-V1/gate6/runner/fix2/test_finalization_fix.py
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

FIX2_DIR = Path(__file__).resolve().parent
RUNNER_DIR = FIX2_DIR.parent
GATE6_DIR = RUNNER_DIR.parent
WORKTREE = str(RUNNER_DIR.parents[4])
SB_ROOT = RUNNER_DIR / "scratch" / "synthetic" / "sandbox"
LOGS = FIX2_DIR / "test_logs_finalization"
RESULTS_PATH = FIX2_DIR / "finalization_fix_results.json"
CONTRACT_IN_SB = str(SB_ROOT / "launch_contract.json")
BUILDER_IN_SB = str(SB_ROOT / "research/control/FUTURES-ES-PB1-V1/final/"
                            "dryrun_builder_v3.py")
BUILDER_PIN_SHA = ("5a08c9fd8a94948cc61762933f77e5fe7db660ade43e1f2d140d2"
                   "c628e164906")
EXECUTOR_SRC = RUNNER_DIR / "scored_executor.py"

for p in (str(Path(WORKTREE) / "research"), str(GATE6_DIR), str(RUNNER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_execution_path as T  # noqa: E402  (fixture + identity helpers)
import scored_executor as SE  # noqa: E402
import trial_ledger  # noqa: E402
from governance import heavy_lock  # noqa: E402

CYCLE_ID = T.CYCLE_ID

# cross-test artifact registry: F2-F5/F8 record their ledger paths + post-run
# file shas here; F7 re-verifies them (a missing key fails F7 loudly).
REGISTRY: dict[str, dict] = {}
RESULTS: dict[str, dict] = {}


def base_cfg(tag: str, ledger: str, fault=None) -> dict:
    """Sandbox cfg shaped exactly like the controller's repro (through the
    production executor; synthetic sandbox only)."""
    return {
        "cycle_id": CYCLE_ID, "sandbox_root": str(SB_ROOT),
        "worktree": T.WORKTREE, "contract_path": T.CONTRACT_IN_SB,
        "builder_path": BUILDER_IN_SB,
        "builder_pin_sha": BUILDER_PIN_SHA, "builder_overrides": None,
        "identity_ids": T.identity_ids(),
        "ledger_path": ledger,
        "lock_runtime_dir": str(SB_ROOT / "heavy_runtime"),
        "run_root": str(SB_ROOT / "runs" / tag),
        "command": [tag], "fault": fault,
        "reverify_authority": lambda: [],
    }


def run_and_record(tag: str, test_id: str, cfg: dict) -> tuple[int, dict]:
    rc, term = SE.run_scored_execution(cfg)
    RESULTS.setdefault(test_id, {})[tag] = {
        "exit_code": rc,
        "terminal_state": term.get("terminal_state"),
        "verdict": term.get("verdict"),
        "computation_complete": term.get("computation_complete"),
        "finalization_failures": term.get("finalization_failures"),
        "lock_released_status": term.get("lock_released_status"),
    }
    return rc, term


def summary_raises_from(threshold: int):
    """Boundary patch: TrialLedger.summary raises from the `threshold`-th
    call onward. Happy-path call order inside run_scored_execution:
    1=_reconcile, 2=verdict step, 3=the FINALIZER's summary."""
    calls = {"n": 0}
    real = trial_ledger.TrialLedger.summary

    def wrapper(self):
        calls["n"] += 1
        if calls["n"] >= threshold:
            raise RuntimeError(
                f"INJECTED ledger summary failure (summary call #{calls['n']})")
        return real(self)

    return wrapper, calls


class F(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        T.ensure_fixtures()
        LOGS.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- F1
    def test_F01_happy_path_unchanged(self):
        ledger = T.fresh_ledger("f1")
        rc, term = run_and_record("f1", "F1", base_cfg("f1", ledger))
        self.assertEqual(rc, 0)
        self.assertEqual(term["terminal_state"], "EXECUTION_COMPLETE")
        self.assertEqual(term["verdict"], "EXECUTION_COMPLETE")
        self.assertEqual(term["exit_code"], 0)
        self.assertEqual(term["lock_released_status"], "FINISHED")
        self.assertIsNone(term.get("lock_release_error"))
        self.assertEqual(term["finalization_failures"], [])
        self.assertTrue(term["computation_complete"])
        self.assertIn("terminal_handoff_path", term)
        handoff = json.loads(Path(term["terminal_handoff_path"]).read_text())
        self.assertEqual(handoff["lock_released_status"], "FINISHED")
        self.assertEqual(handoff["finalization_failures"], [])
        summary = trial_ledger.TrialLedger(ledger, T.identity_ids()).summary()
        self.assertEqual(summary["observed_denominator"], 24)
        self.assertTrue(summary["complete"])
        REGISTRY["f1"] = {"ledger": ledger,
                          "post_run_sha": SE.sha256_file(ledger)}

    # ---------------------------------------------------------------- F2
    def test_F02_handoff_write_failure_fails_closed(self):
        ledger = T.fresh_ledger("f2")
        real_write = SE._write_atomic

        def boom(p, data):
            if Path(p).name == "terminal_handoff.json":
                raise OSError("INJECTED handoff write failure (primary only)")
            return real_write(p, data)

        with mock.patch.object(SE, "_write_atomic", boom):
            rc, term = run_and_record("f2", "F2", base_cfg("f2", ledger))
        # NOT a success in any form
        self.assertEqual(rc, 4)
        self.assertNotEqual(term["terminal_state"], "EXECUTION_COMPLETE")
        self.assertEqual(term["terminal_state"], "FINALIZATION_FAILURE")
        self.assertEqual(term["verdict"], "EXECUTION_FAILED")
        self.assertEqual(term["failure_reasons"], ["FINALIZATION_FAILURE"])
        self.assertTrue(term["computation_complete"])
        self.assertEqual(term["exit_code"], 4)
        # the primary artifact is NEVER claimed
        self.assertNotIn("terminal_handoff_path", term)
        self.assertIn("terminal_handoff_error", term)
        self.assertIn("INJECTED handoff write failure",
                      term["terminal_handoff_error"])
        # fallback diagnostics present and consistent
        self.assertIn("terminal_handoff_fallback_path", term)
        fb = json.loads(Path(term["terminal_handoff_fallback_path"]).read_text())
        self.assertTrue(fb["terminal_handoff_primary_path_unclaimed"])
        self.assertEqual(fb["terminal_state"], "FINALIZATION_FAILURE")
        self.assertEqual(fb["exit_code"], 4)
        self.assertEqual(fb["verdict"], "EXECUTION_FAILED")
        self.assertIsNone(fb.get("terminal_handoff_path"))
        # the ledger survived intact: 24 computed rows, observed 24
        led = trial_ledger.TrialLedger(ledger, T.identity_ids())
        self.assertTrue(led.verify()["ok"])
        self.assertEqual(led.summary()["observed_denominator"], 24)
        REGISTRY["f2"] = {"ledger": ledger,
                          "post_run_sha": SE.sha256_file(ledger)}

    # ---------------------------------------------------------------- F3
    def test_F03_release_raises_preunlock_unverified_plus_inspect(self):
        ledger = T.fresh_ledger("f3")
        with mock.patch.object(heavy_lock, "acquire") as acq:
            h = mock.MagicMock()
            h.release.side_effect = RuntimeError(
                "INJECTED release failure (pre-unlock)")
            acq.return_value = h
            rc, term = run_and_record("f3", "F3", base_cfg("f3", ledger))
        self.assertEqual(rc, 4)
        self.assertEqual(term["terminal_state"], "FINALIZATION_FAILURE")
        self.assertEqual(term["verdict"], "EXECUTION_FAILED")
        # released status is NOT claimed; measured evidence is
        self.assertEqual(term["lock_released_status"],
                         "UNVERIFIED_RELEASE_RAISED")
        self.assertIn("INJECTED release failure", term["lock_release_error"])
        insp = term["lock_inspect_after_release_failure"]
        self.assertIn("verdict", insp)
        # nothing was really locked by the mocked acquire: the canonical
        # inspect of the sandbox runtime is recorded as the evidence (this
        # run observed FREE_PROVEN — the value is whatever inspect measured)
        self.assertEqual(insp["verdict"], "FREE_PROVEN", insp)
        stages = [f["stage"] for f in term["finalization_failures"]]
        self.assertEqual(stages, ["lock_release"])
        self.assertTrue(term["computation_complete"])
        # primary handoff was unaffected and carries the fixed-up verdict
        self.assertIn("terminal_handoff_path", term)
        handoff = json.loads(Path(term["terminal_handoff_path"]).read_text())
        self.assertEqual(handoff["terminal_state"], "FINALIZATION_FAILURE")
        self.assertEqual(handoff["exit_code"], 4)
        # ledger intact
        led = trial_ledger.TrialLedger(ledger, T.identity_ids())
        self.assertTrue(led.verify()["ok"])
        self.assertEqual(led.summary()["observed_denominator"], 24)
        REGISTRY["f3"] = {"ledger": ledger,
                          "post_run_sha": SE.sha256_file(ledger)}

    # ---------------------------------------------------------------- F4
    def test_F04_release_raises_after_real_unlock_inspect_shows_free(self):
        ledger = T.fresh_ledger("f4")
        real_acquire = heavy_lock.acquire

        def acquire_then_release_bomb(**kw):
            h = real_acquire(**kw)
            real_release = h.release

            def release_then_raise(status="FINISHED", note=""):
                real_release(status=status, note=note)  # ACTUAL unlock happens
                raise RuntimeError(
                    "INJECTED release failure (raised AFTER the real unlock)")

            h.release = release_then_raise
            return h

        with mock.patch.object(heavy_lock, "acquire",
                               acquire_then_release_bomb):
            rc, term = run_and_record("f4", "F4", base_cfg("f4", ledger))
        # still a finalization failure — the RAISE is the failure even
        # though the lock state is free
        self.assertEqual(rc, 4)
        self.assertEqual(term["terminal_state"], "FINALIZATION_FAILURE")
        self.assertEqual(term["lock_released_status"],
                         "UNVERIFIED_RELEASE_RAISED")
        self.assertIn("AFTER the real unlock", term["lock_release_error"])
        # the inspect evidence records the MEASURED free state (never assumed)
        insp = term["lock_inspect_after_release_failure"]
        self.assertEqual(insp["verdict"], "FREE_PROVEN", insp)
        self.assertEqual(insp["evidence"]["flock_state"], "free")
        # and the same verdict holds from a fresh canonical inspection
        self.assertEqual(
            heavy_lock.inspect()["verdict"], "FREE_PROVEN")
        self.assertTrue(term["computation_complete"])
        led = trial_ledger.TrialLedger(ledger, T.identity_ids())
        self.assertTrue(led.verify()["ok"])
        self.assertEqual(led.summary()["observed_denominator"], 24)
        REGISTRY["f4"] = {"ledger": ledger,
                          "post_run_sha": SE.sha256_file(ledger)}

    # ---------------------------------------------------------------- F5
    def test_F05_ledger_summary_failure_fails_closed_rows_stand(self):
        ledger = T.fresh_ledger("f5")
        wrapper, calls = summary_raises_from(3)  # 3rd call == the finalizer's
        with mock.patch.object(trial_ledger.TrialLedger, "summary", wrapper):
            rc, term = run_and_record("f5", "F5", base_cfg("f5", ledger))
        self.assertEqual(calls["n"], 3, calls)
        self.assertEqual(rc, 4)
        self.assertEqual(term["terminal_state"], "FINALIZATION_FAILURE")
        self.assertNotEqual(term["terminal_state"], "EXECUTION_COMPLETE")
        self.assertIn("ledger_summary_error", term)
        self.assertIn("INJECTED ledger summary failure",
                      term["ledger_summary_error"])
        self.assertTrue(term["computation_complete"])
        stages = [f["stage"] for f in term["finalization_failures"]]
        self.assertEqual(stages, ["ledger_summary"])
        # rows already written stand; bytes untouched
        led = trial_ledger.TrialLedger(ledger, T.identity_ids())
        self.assertTrue(led.verify()["ok"])
        summary = led.summary()
        self.assertEqual(summary["observed_denominator"], 24)
        self.assertEqual(summary["status_counts"]["PASS"], 24)
        REGISTRY["f5"] = {"ledger": ledger,
                          "post_run_sha": SE.sha256_file(ledger)}

    # ---------------------------------------------------------------- F6
    def test_F06_compute_and_cleanup_errors_both_present_no_masking(self):
        ledger = T.fresh_ledger("f6")
        wrapper, calls = summary_raises_from(1)  # fires in the finalizer only
        fault = {"type": "exception", "at_index": 7}
        with mock.patch.object(trial_ledger.TrialLedger, "summary", wrapper):
            rc, term = run_and_record("f6", "F6",
                                      base_cfg("f6", ledger, fault=fault))
        self.assertEqual(calls["n"], 1, calls)
        # original error PRESERVED as the terminal state; exit stays 3
        self.assertEqual(rc, 3)
        self.assertEqual(term["terminal_state"], "COMPUTE_FAILURE")
        self.assertEqual(term["verdict"], "EXECUTION_FAILED")
        self.assertIn("exception", term)  # the original error, unmasked
        self.assertFalse(term["computation_complete"])
        # the cleanup error is recorded TOO, never swallowed
        self.assertIn("ledger_summary_error", term)
        stages = [f["stage"] for f in term["finalization_failures"]]
        self.assertEqual(stages, ["ledger_summary"])
        # the release step was still attempted AFTER the cleanup failure and
        # the lock is really released (flock free + registry row cleared)
        self.assertEqual(term["lock_released_status"], "FAILED")
        lock_path = SB_ROOT / "heavy_runtime" / heavy_lock.LOCK_NAME
        self.assertEqual(heavy_lock.flock_state(lock_path), "free")
        self.assertFalse((SB_ROOT / "heavy_runtime" /
                          heavy_lock.REGISTRY_NAME).exists())
        # 7 computed terminals stand
        led = trial_ledger.TrialLedger(ledger, T.identity_ids())
        self.assertTrue(led.verify()["ok"])
        self.assertEqual(led.summary()["observed_denominator"], 7)
        REGISTRY["f6"] = {"ledger": ledger,
                          "post_run_sha": SE.sha256_file(ledger)}

    # ---------------------------------------------------------------- F7
    def test_F07_ledgers_after_failures_verify_bytes_unchanged(self):
        self.assertTrue({"f2", "f3", "f4", "f5"} <= set(REGISTRY),
                        f"F2-F5 must run before F7: {sorted(REGISTRY)}")
        for tag in ("f1", "f2", "f3", "f4", "f5", "f6"):
            info = REGISTRY[tag]
            before = Path(info["ledger"]).read_bytes()
            led = trial_ledger.TrialLedger(info["ledger"], T.identity_ids())
            v = led.verify()
            self.assertTrue(v["ok"], f"{tag}: {v}")
            expected_observed = 7 if tag == "f6" else 24
            self.assertEqual(led.summary()["observed_denominator"],
                             expected_observed, tag)
            # bytes identical to the post-run snapshot (never rewritten)
            self.assertEqual(SE.sha256_file(info["ledger"]),
                             info["post_run_sha"], tag)
            self.assertEqual(Path(info["ledger"]).read_bytes(), before, tag)

    # ---------------------------------------------------------------- F8
    def test_F08_retry_after_finalization_failure_t5_twist(self):
        ids = T.identity_ids()
        # (a) abort after 5 + release-raises: the 5 rows STAND
        ledger_a = T.fresh_ledger("f8a")
        fault = {"type": "abort", "after_k": 5}
        with mock.patch.object(heavy_lock, "acquire") as acq:
            h = mock.MagicMock()
            h.release.side_effect = RuntimeError("INJECTED release failure")
            acq.return_value = h
            rc1, term1 = run_and_record("f8a-run1", "F8",
                                        base_cfg("f8a-run1", ledger_a,
                                                 fault=fault))
        self.assertNotEqual(rc1, 0)
        self.assertEqual(term1["terminal_state"], "ABORTED_SANDBOX_FAULT")
        # original abort error NOT masked by the finalization failure;
        # both dimensions recorded
        self.assertIn("abort_reason", term1)
        stages = [f["stage"] for f in term1["finalization_failures"]]
        self.assertEqual(stages, ["lock_release"])
        self.assertEqual(term1["lock_released_status"],
                         "UNVERIFIED_RELEASE_RAISED")
        led = trial_ledger.TrialLedger(ledger_a, ids)
        self.assertTrue(led.verify()["ok"])
        self.assertEqual(led.summary()["observed_denominator"], 5)
        prefix = Path(ledger_a).read_bytes()

        rc2, term2 = run_and_record("f8a-run2", "F8",
                                    base_cfg("f8a-run2", ledger_a))
        self.assertEqual(rc2, 0)
        self.assertEqual(term2["terminal_state"], "EXECUTION_COMPLETE")
        self.assertEqual(term2["finalization_failures"], [])
        rows = trial_ledger.TrialLedger(ledger_a, ids).summary()
        self.assertEqual(rows["observed_denominator"], 24)
        self.assertTrue(rows["complete"])
        # no recompute of terminal slots: the first 5 were SKIPPED
        self.assertEqual(term2["pass_a"]["skipped_terminal"], ids[:5])
        self.assertEqual(len(term2["pass_a"]["computed"]), 19)
        self.assertEqual(sorted(set(term2["pass_a"]["computed"])
                                & set(term2["pass_a"]["skipped_terminal"])),
                         [])
        for iid in ids[:5]:
            a = (SB_ROOT / "runs/f8a-run1/pass_a" / f"{iid}.json").read_bytes()
            b = (SB_ROOT / "runs/f8a-run2/pass_a" / f"{iid}.json").read_bytes()
            self.assertEqual(a, b, iid)
        self.assertTrue(Path(ledger_a).read_bytes().startswith(prefix))

        # (b) FULL computation + finalizer summary fault => exit 4; every
        # slot is terminal; the retry recomputes NOTHING
        ledger_b = T.fresh_ledger("f8b")
        wrapper, calls = summary_raises_from(3)
        with mock.patch.object(trial_ledger.TrialLedger, "summary", wrapper):
            rc1b, term1b = run_and_record("f8b-run1", "F8",
                                          base_cfg("f8b-run1", ledger_b))
        self.assertEqual(calls["n"], 3, calls)
        self.assertEqual(rc1b, 4)
        self.assertEqual(term1b["terminal_state"], "FINALIZATION_FAILURE")
        led_b = trial_ledger.TrialLedger(ledger_b, ids)
        self.assertTrue(led_b.verify()["ok"])
        self.assertEqual(led_b.summary()["observed_denominator"], 24)
        prefix_b = Path(ledger_b).read_bytes()

        rc2b, term2b = run_and_record("f8b-run2", "F8",
                                      base_cfg("f8b-run2", ledger_b))
        self.assertEqual(rc2b, 0)
        self.assertEqual(term2b["terminal_state"], "EXECUTION_COMPLETE")
        self.assertEqual(term2b["pass_a"]["skipped_terminal"], ids)
        self.assertEqual(term2b["pass_a"]["computed"], [])
        rows_b = trial_ledger.TrialLedger(ledger_b, ids).summary()
        self.assertEqual(rows_b["observed_denominator"], 24)
        self.assertTrue(rows_b["complete"])
        self.assertTrue(Path(ledger_b).read_bytes().startswith(prefix_b))

    # ---------------------------------------------------------------- F9
    def test_F09_existing_suites_still_pass_unchanged(self):
        suites = [("test_execution_path.py", T.RUNNER_DIR /
                   "test_execution_path.py"),
                  ("test_runner_refusals.py", T.RUNNER_DIR /
                   "test_runner_refusals.py")]
        for name, path in suites:
            t0 = time.time()
            proc = subprocess.run([sys.executable, str(path)],
                                  capture_output=True, text=True, timeout=2400)
            LOGS.mkdir(parents=True, exist_ok=True)
            (LOGS / f"F9_{name}.stdout.txt").write_text(
                proc.stdout, encoding="utf-8")
            (LOGS / f"F9_{name}.stderr.txt").write_text(
                f"exit_code={proc.returncode} seconds={time.time()-t0:.1f}\n"
                f"{proc.stderr}", encoding="utf-8")
            RESULTS.setdefault("F9", {})[name] = {
                "exit_code": proc.returncode,
                "seconds": round(time.time() - t0, 1),
            }
            self.assertEqual(proc.returncode, 0,
                             f"{name} rc={proc.returncode}\n"
                             f"{proc.stderr[-3000:]}")
            self.assertIn("OK", proc.stderr.splitlines()[-1], name)

    # --------------------------------------------------------------- F10
    def test_F10_production_default_safety_unchanged(self):
        # (a) fault injection is non-constructible in production mode
        with self.assertRaises(AssertionError):
            SE.run_scored_execution({"sandbox_root": None,
                                     "fault": {"type": "abort",
                                               "after_k": 1}})
        # (b) the executor source stays free of fixture references and of
        # any force-unlock / kill / delete-lock / flock primitive; the ONLY
        # post-failure lock mechanism is the canonical read-only inspect
        text = EXECUTOR_SRC.read_text(encoding="utf-8")
        self.assertNotIn("scratch/synthetic", text)
        for banned in ("fcntl", "flock(", "unlink(", "rmtree", ".kill(",
                       "LOCK_UN"):
            self.assertNotIn(banned, text, banned)
        self.assertIn("heavy_lock.inspect()", text)
        # (c) the D-7 vocabulary is exactly as documented, and the exit
        # table is unchanged apart from the new finalization code
        self.assertEqual(SE.EXIT_OK, 0)
        self.assertEqual(SE.EXIT_REFUSED, 2)
        self.assertEqual(SE.EXIT_FAILURE, 3)
        self.assertEqual(SE.EXIT_CONFLICT, 75)
        self.assertEqual(SE.EXIT_FINALIZATION, 4)
        self.assertEqual(SE.TERMINAL_FINALIZATION, "FINALIZATION_FAILURE")
        self.assertEqual(SE.TERMINAL_COMPLETE, "EXECUTION_COMPLETE")
        # (d) the lock-runtime redirect is still sandbox-confined (AST)
        tree = ast.parse(text)
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

        hits = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) \
                    and node.attr == "RUNTIME_DIRNAME":
                hits += 1
                fns = enclosing_funcs(node)
                self.assertTrue(any("sandbox" in fn for fn in fns),
                                f"RUNTIME_DIRNAME outside sandbox code: {fns}")
        # 3 Attribute nodes, all inside _patch_sandbox_lock_runtime:
        # the read (prev =) + TWO assignment targets (set + restore).
        # Pre-fix code also had exactly 3 (verified vs c17ab2bf); the
        # earlier "==2" was this test's own wrong baseline (F10 defect
        # class: stale expectation, containment property itself PASSED).
        self.assertEqual(hits, 3)
        self.assertIsNone(SE.resolve_lock_runtime(None))
        self.assertTrue(SE.resolve_lock_runtime("/x/y").endswith(
            "heavy_runtime"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(F)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    RESULTS["_suite"] = {"tests_run": result.testsRun,
                         "failures": len(result.failures),
                         "errors": len(result.errors)}
    RESULTS_PATH.write_text(
        json.dumps(RESULTS, indent=1, sort_keys=True, ensure_ascii=False)
        + "\n", encoding="utf-8")
    print(f"results written: {RESULTS_PATH}")
    sys.exit(0 if result.wasSuccessful() else 1)
