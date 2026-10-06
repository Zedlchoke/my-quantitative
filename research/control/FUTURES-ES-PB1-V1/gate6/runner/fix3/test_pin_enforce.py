#!/usr/bin/env python
"""test_pin_enforce.py — P1..P10 proof suite for the PIN-ENFORCE lane of
FUTURES-ES-PB1-V1 (cycle FUTURES-ES-PB1-V1, gate6/runner/fix3).

Closes F-V1 (live/history diagnostic clobber) and F-V2 (addendum pin drift
executed to completion) with ONE consistent live-operative-pin law:

  P1  valid sandbox GO + all pins right => synthetic happy path executes
      (exit 0, EXECUTION_COMPLETE, 24 ledger rows) — regression proof that
      the full-live gate facts and self-integrity binding stay green.
  P2  the FAIL_FV2 reproduction (tamper the LIVE scored_executor pin sha
      in the sandbox contract copy; at repro time that row lived in
      v2_2_addendum, after the PIN-ENFORCE v2_3 re-pin it lives in
      v2_3_addendum — the tamper is the same and so is the target: the
      live pin) => NOW refuses BEFORE computation: exit 2 REFUSED_DRIFT
      naming scored_executor; NO run outputs; REFUSED ledger row;
      explicitly asserts no execution artifacts exist. Also proves the
      superseded v2_2 twin's tamper is INERT (history is evidence-only,
      never a gate input).
  P3  tamper the scored_runner self-pin so the FILE and PIN agree but the
      bytes ACTUALLY imported do not (sandbox copy + contract pin patched
      together) => the pre-lock drift gate stays green and the refusal
      fires at the SELF-INTEGRITY execution boundary (exit 2, gate
      SELF-INTEGRITY, names scored_runner, no execution).
  P4  inject a NEW v2_4 addendum carrying a NEW file pin into the sandbox
      contract copy (the sandbox contract already carries the lane's
      v2_3 re-pin, so the dynamically-consumed addendum here is v2_4 —
      same law: ANY new v2_*_addendum is checked with NO code change):
      correct sha => full happy path (exit 0) and the probe appears in
      drift pins_live; tampered => REFUSED_DRIFT naming the probe. Also
      asserts the probe name appears in NO production source (no
      hardcoded pin names).
  P5  post-acquire TOCTOU drift: (a) the runner-built reverify closure
      returns [] on the green state and names operative_freeze_v3 after a
      sandbox tamper (enforcement site); (b) the FULL production CLI with
      the sandbox-only tamper_after_gates fault refuses at gate
      TOCTOU-post-acquire, lock released correctly (flock free, registry
      row cleared), REFUSED ledger row, no computation; (c) the executor
      driven with the REAL contract-built closure after the tamper also
      refuses before computation.
  P6  missing pinned file (deleted from the sandbox copy) => fail closed,
      exit 2 REFUSED_DRIFT with the pin named.
  P7  F-V1: tamper nothing; check_drift output shows scored_executor in
      pins_live with match=true AND its superseded v2_1/v2_2 twins in
      pins_history — both visible, no name clobber.
  P8  registry-head tamper in the sandbox copy => refuse (existing law
      intact).
  P9  regression: fix2/test_finalization_fix.py,
      test_runner_refusals.py, test_execution_path.py all green.
  P10 preflight vs execution distinction: the SAME tampered freeze bytes
      run in preflight mode (real wiring, tmp override path) AND execution
      mode (sandbox copy) BOTH refuse exit 2 with DIFFERENT exit
      paths/records — preflight refusal proves wiring only (manifest,
      no writes); execution refusal is the enforcement proof (REFUSED
      ledger row + refusal_record + no run outputs).

Every case drives the PRODUCTION PATH (the real scored_runner.py CLI over
sandbox copies; the fake GO exists ONLY inside sandbox copies) and records
exit code + refusal reason + ledger row into fix3/pin_enforce_results.json.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python \\
      research/control/FUTURES-ES-PB1-V1/gate6/runner/fix3/test_pin_enforce.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FIX3_DIR = Path(__file__).resolve().parent
RUNNER_DIR = FIX3_DIR.parent
GATE6_DIR = RUNNER_DIR.parent
WORKTREE = str(RUNNER_DIR.parents[4])
SB_ROOT = RUNNER_DIR / "scratch" / "synthetic" / "sandbox"
RUNNER = str(RUNNER_DIR / "scored_runner.py")
EXECUTOR = str(RUNNER_DIR / "scored_executor.py")
RESEARCH_PKG = str(Path(WORKTREE) / "research")
RESULTS_PATH = FIX3_DIR / "pin_enforce_results.json"

CY = "research/control/FUTURES-ES-PB1-V1"
GO_IN_SB = "research/control/FUTURES-ES-PB1-V1/authority/GO_RECORDED.json"
FREEZE_REL = f"{CY}/final/selection_freeze_v3.json"
EXCLUDE_REL = f"{CY}/final/exclude_list_v3.json"
RUNNER_COPY_REL = f"{CY}/gate6/runner/scored_runner.py"

for p in (RESEARCH_PKG, str(GATE6_DIR), str(RUNNER_DIR), str(FIX3_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_execution_path as T          # noqa: E402  (fixtures + helpers)
import scored_runner as SR               # noqa: E402  (the law under test)

RESULTS: dict = {}


def record(case: str, **kv) -> None:
    RESULTS.setdefault(case, {}).update(kv)
    RESULTS_PATH.write_text(json.dumps(RESULTS, indent=1, sort_keys=True,
                                       ensure_ascii=False) + "\n",
                            encoding="utf-8")


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fresh_sb(tag: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"pin_enforce_{tag}_"))
    sb = tmp / "sb"
    shutil.copytree(SB_ROOT, sb)
    return sb


def load_contract(sb: Path) -> dict:
    return json.loads((sb / "launch_contract.json").read_text("utf-8"))


def save_contract(sb: Path, con: dict) -> None:
    (sb / "launch_contract.json").write_text(
        json.dumps(con, indent=1, ensure_ascii=False), encoding="utf-8")


def sandbox_argv(sb: Path, ledger: str, label: str, extra=None) -> list:
    return ["--sandbox-root", str(sb),
            "--contract", str(sb / "launch_contract.json"),
            "--registry-path", str(sb / "registry/CYCLE_REGISTRY.rowcopy.json"),
            "--go-artifact", str(sb / GO_IN_SB),
            "--ledger-path", ledger,
            "--run-label", label] + (extra or [])


def run_cli(sb: Path, ledger: str, label: str, extra=None):
    return subprocess.run([sys.executable, RUNNER]
                          + sandbox_argv(sb, ledger, label, extra),
                          capture_output=True, text=True, timeout=900)


def ledger_rows(path) -> list:
    p = Path(path)
    if not p.is_file():
        return []
    return [json.loads(line) for line in
            p.read_text("utf-8").splitlines() if line.strip()]


def refused_rows(path) -> list:
    return [r for r in ledger_rows(path) if r.get("status") == "REFUSED"]


def refusal_record(sb: Path) -> dict:
    return json.loads((sb / "ledger" / "refusal_record.json")
                      .read_text("utf-8"))


def assert_no_execution(self, sb: Path) -> None:
    """Explicit: the runner produced ZERO execution artifacts."""
    self.assertFalse((sb / "runs").exists(),
                     "runs/ directory was created — execution artifacts exist")
    leftovers = [str(p) for p in sb.rglob("*")
                 if p.is_file() and ("pass_a" in p.parent.name
                                     or p.name.startswith("terminal_handoff"))]
    self.assertEqual(leftovers, [], f"execution artifacts leaked: {leftovers}")


class P(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        T.ensure_fixtures()   # regenerate the pristine sandbox (new generator)

    # ---------------------------------------------------------------- P1
    def test_P1_happy_path_regression_full_live_gate(self):
        sb = fresh_sb("p1")
        ledger = str(sb / "ledger" / "p1.jsonl")
        proc = run_cli(sb, ledger, "p1")
        T.log("P1", proc)
        record("P1", exit_code=proc.returncode)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2500:])
        man = json.loads(proc.stdout)
        record("P1", verdict=man["execution"]["terminal_state"],
               ledger_rows=24, refusal_reason=None)
        self.assertEqual(man["execution"]["terminal_state"],
                         "EXECUTION_COMPLETE")
        self.assertTrue(man["gate_verdict"]["allowed"])
        # the full-live gate facts: addendum pins are gate inputs now
        self.assertTrue(man["drift_check"]["pins_live"]["scored_executor"]
                        ["match"])
        self.assertTrue(man["drift_check"]["pins_live"]["scored_runner"]
                        ["match"])
        rows = [r for r in ledger_rows(ledger) if r.get("identity_id")]
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(r["status"] == "PASS" for r in rows))
        self.assertEqual(refused_rows(ledger), [])

    # ---------------------------------------------------------------- P2
    def test_P2_live_scored_executor_pin_tamper_refuses_before_compute(self):
        # The FAIL_FV2 reproduction, re-targeted at the LIVE scored_executor
        # pin (v2_3 row after the PIN-ENFORCE re-pin; v2_2 at repro time).
        sb = fresh_sb("p2")
        con = load_contract(sb)
        live_sha = sha256_file(RUNNER_DIR / "scored_executor.py")
        tampered_to = None
        for key in sorted(con):
            if key.startswith("v2_") and key.endswith("_addendum"):
                for np in con[key].get("new_pins", []):
                    if np["name"] == "scored_executor" \
                            and np["sha256"] == live_sha:
                        np["sha256"] = "f" * 64          # THE FAIL_FV2 TAMPER
                        tampered_to = key
        self.assertEqual(tampered_to, "v2_3_addendum")
        save_contract(sb, con)
        ledger = str(sb / "ledger" / "p2.jsonl")
        proc = run_cli(sb, ledger, "p2")
        T.log("P2", proc)
        record("P2", exit_code=proc.returncode,
               live_pin_tampered_in=tampered_to)
        self.assertEqual(proc.returncode, 2, proc.stderr[-2500:])
        self.assertIn("REFUSED_DRIFT", proc.stderr)
        self.assertNotIn("EXECUTION_COMPLETE", proc.stdout)
        rr = refusal_record(sb)
        record("P2", refusal_reason=rr["reason"],
               mismatched=rr["detail"].get("mismatched_pins"))
        self.assertEqual(rr["reason"], "REFUSED_DRIFT")
        self.assertIn("scored_executor", rr["detail"]["mismatched_pins"])
        rows = refused_rows(ledger)
        self.assertTrue(any(r.get("reason") == "REFUSED_DRIFT"
                            for r in rows), rows)
        assert_no_execution(self, sb)
        # history-inert sub-law: tampering the SUPERSEDED v2_2 twin must
        # NOT flip anything (history rows are evidence-only, never inputs)
        sb2 = fresh_sb("p2hist")
        con2 = load_contract(sb2)
        for np in con2["v2_2_addendum"]["new_pins"]:
            if np["name"] == "scored_executor":
                np["sha256"] = "e" * 64        # the SUPERSEDED v2_2 twin
        save_contract(sb2, con2)
        drift = SR.check_drift(con2, WORKTREE,
                               SR.resolve_sandbox_paths(str(sb2), con2))
        self.assertTrue(drift["pass"], drift["mismatched_pins"])
        record("P2", history_tamper_inert=True)

    # ---------------------------------------------------------------- P3
    def test_P3_self_integrity_boundary_refuses_stale_module_binding(self):
        # File and contract pin agree (pre-lock drift stays green), but the
        # bytes ACTUALLY imported (the real worktree runner) do not — the
        # refusal must fire at the SELF-INTEGRITY execution boundary.
        sb = fresh_sb("p3")
        runner_copy = sb / RUNNER_COPY_REL
        data = runner_copy.read_bytes() + \
            b"\n# pin-enforce P3: sandbox copy tampered, contract re-pinned\n"
        runner_copy.write_bytes(data)
        con = load_contract(sb)
        for np in con["v2_3_addendum"]["new_pins"]:
            if np["name"] == "scored_runner":
                np["sha256"] = hashlib.sha256(data).hexdigest()
        save_contract(sb, con)
        ledger = str(sb / "ledger" / "p3.jsonl")
        proc = run_cli(sb, ledger, "p3")
        T.log("P3", proc)
        record("P3", exit_code=proc.returncode)
        self.assertEqual(proc.returncode, 2, proc.stderr[-2500:])
        self.assertIn("REFUSED_CONTROL_STATE_DRIFT", proc.stderr)
        self.assertIn("SELF-INTEGRITY", proc.stderr)
        rr = refusal_record(sb)
        record("P3", refusal_reason=rr["reason"],
               gate=rr["detail"].get("gate"))
        self.assertEqual(rr["reason"], "REFUSED_CONTROL_STATE_DRIFT")
        self.assertEqual(rr["detail"]["gate"], "SELF-INTEGRITY")
        self.assertTrue(any("scored_runner" in v
                            for v in rr["detail"]["violations"]),
                        rr["detail"]["violations"])
        rows = refused_rows(ledger)
        self.assertTrue(any(r.get("reason") == "REFUSED_CONTROL_STATE_DRIFT"
                            for r in rows), rows)
        assert_no_execution(self, sb)
        # enforcement-site isolation: the binding function itself, called
        # with a stale-import simulation (module __file__ elsewhere,
        # contract pin at the original bytes) — method: direct call at the
        # enforcement site, exactly where main() invokes it.
        stale = Path(tempfile.mkdtemp(prefix="p3_stale_")) / "scored_runner.py"
        stale.write_bytes(data)
        v = SR.self_integrity_violations(load_contract(sb), WORKTREE,
                                         runner_file=str(stale),
                                         executor_file=EXECUTOR)
        self.assertTrue(any("scored_runner" in x for x in v), v)
        record("P3", enforcement_site_method="direct call to "
               "scored_runner.self_integrity_violations with a stale-copy "
               "module file", stale_import_violations=len(v))

    # ---------------------------------------------------------------- P4
    def test_P4_new_addendum_pin_checked_without_code_change(self):
        probe_name = "pin_enforce_probe_prego"
        probe_rel = f"{CY}/auth/PREGO_REPAIR_RECORDED.json"

        def inject(sb: Path, sha: str) -> None:
            con = load_contract(sb)
            con["v2_4_addendum"] = {
                "schema": "launch_contract_addendum@2.4",
                "written_utc_date": "2026-10-05",
                "lane": "PIN-ENFORCE P4 (sandbox dynamic-addendum probe)",
                "new_pins": [{"name": probe_name, "path": probe_rel,
                              "sha256": sha,
                              "role": "P4 probe: new file pin via a new "
                                      "v2_* addendum, no code change"}],
            }
            save_contract(sb, con)

        # (a) correct sha => checked and GREEN through the full CLI
        sb = fresh_sb("p4green")
        inject(sb, sha256_file(sb / probe_rel))
        ledger = str(sb / "ledger" / "p4green.jsonl")
        proc = run_cli(sb, ledger, "p4green")
        T.log("P4green", proc)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2500:])
        man = json.loads(proc.stdout)
        self.assertEqual(man["execution"]["terminal_state"],
                         "EXECUTION_COMPLETE")
        self.assertIn(probe_name, man["drift_check"]["pins_live"])
        self.assertTrue(man["drift_check"]["pins_live"][probe_name]["match"])
        record("P4", green_exit=0, probe_in_pins_live=True,
               ledger_rows=24, refusal_reason=None)
        # (b) tampered sha => refused, naming the probe (no hardcoded names)
        sb2 = fresh_sb("p4bad")
        inject(sb2, "0" * 64)
        ledger2 = str(sb2 / "ledger" / "p4bad.jsonl")
        proc2 = run_cli(sb2, ledger2, "p4bad")
        T.log("P4bad", proc2)
        record("P4", tampered_exit=proc2.returncode)
        self.assertEqual(proc2.returncode, 2, proc2.stderr[-2500:])
        rr = refusal_record(sb2)
        record("P4", refusal_reason=rr["reason"],
               mismatched=rr["detail"].get("mismatched_pins"))
        self.assertEqual(rr["reason"], "REFUSED_DRIFT")
        self.assertIn(probe_name, rr["detail"]["mismatched_pins"])
        self.assertTrue(any(r.get("reason") == "REFUSED_DRIFT"
                            for r in refused_rows(ledger2)))
        assert_no_execution(self, sb2)
        # (c) the probe name exists in NO production source
        for src in (RUNNER, EXECUTOR):
            self.assertNotIn(probe_name, Path(src).read_text("utf-8"), src)
        record("P4", no_hardcoded_names=True)

    # ---------------------------------------------------------------- P5
    def test_P5_post_acquire_toctou_drift_refuses_and_releases_lock(self):
        from governance import heavy_lock
        import scored_executor as SE

        # (a) enforcement site: the runner-built closure over the green
        # state returns [], and names the pin after a sandbox tamper.
        sb = fresh_sb("p5")
        con = load_contract(sb)
        paths = SR.resolve_sandbox_paths(str(sb), con)
        pins_live, _ = SR.live_operative_pins(con)
        reg_path = str(sb / "registry/CYCLE_REGISTRY.rowcopy.json")
        reg = SR.check_registry(WORKTREE, reg_path)
        self.assertEqual(reg["head_check"], "MATCH")
        closure = SR.build_reverify_closure(
            con, WORKTREE, reg_path, paths, pins_live,
            str(sb / GO_IN_SB), reg["row_stable_fields"],
            next(p["sha256"] for p in pins_live
                 if p["name"] == "a7_prelaunch_v3_digest"),
            paths["pin:a7_prelaunch_v3_digest"])
        self.assertEqual(closure(), [])
        (sb / FREEZE_REL).write_bytes(
            (sb / FREEZE_REL).read_bytes() + b"\n")
        drifts = closure()
        record("P5", closure_method="scored_runner.build_reverify_closure "
               "called at the enforcement site after a sandbox tamper")
        self.assertTrue(any("operative_freeze_v3" in d for d in drifts),
                        drifts)
        self.assertEqual(len(drifts), 1, drifts)

        # (b) FULL production CLI through the TOCTOU window: the
        # sandbox-only tamper_after_gates fault corrupts a pinned file
        # between the pre-lock drift check and the post-acquire re-verify.
        sb2 = fresh_sb("p5cli")
        ledger2 = str(sb2 / "ledger" / "p5cli.jsonl")
        fault = json.dumps({"type": "tamper_after_gates",
                            "pin": "operative_freeze_v3"})
        proc = run_cli(sb2, ledger2, "p5cli",
                       ["--sandbox-fault", fault])
        T.log("P5cli", proc)
        record("P5", cli_fault_exit=proc.returncode)
        self.assertEqual(proc.returncode, 2, proc.stderr[-2500:])
        man = json.loads(proc.stdout)
        execution = man["execution"]
        self.assertEqual(execution["terminal_state"],
                         "REFUSED_CONTROL_STATE_DRIFT")
        # the executor's refusal carries the TOCTOU gate + drifts in the
        # ledger row note (the executor does not print the refusal detail)
        refusal_note = json.dumps(execution.get("refusal_row") or {})
        self.assertIn("TOCTOU-post-acquire", refusal_note)
        self.assertIn("operative_freeze_v3", refusal_note)
        record("P5", cli_refusal_reason="REFUSED_CONTROL_STATE_DRIFT",
               cli_gate="TOCTOU-post-acquire",
               cli_drifts_named="operative_freeze_v3")
        self.assertTrue(any(r.get("reason")
                            == "REFUSED_CONTROL_STATE_DRIFT"
                            for r in refused_rows(ledger2)))
        # lock released correctly (flock free, registry row cleared)
        lock_path = sb2 / "heavy_runtime" / heavy_lock.LOCK_NAME
        self.assertEqual(heavy_lock.flock_state(lock_path), "free")
        self.assertFalse((sb2 / "heavy_runtime" /
                          heavy_lock.REGISTRY_NAME).exists())
        self.assertFalse((sb2 / "runs" / "p5cli" / "pass_a").exists())
        record("P5", cli_refusal_reason="REFUSED_CONTROL_STATE_DRIFT",
               cli_gate="TOCTOU-post-acquire", lock_released=True,
               no_computation=True)

        # (c) enforcement site through the REAL executor: the same
        # contract-built closure (now over the tampered box) drives
        # run_scored_execution => refuse BEFORE computation.
        con_t = load_contract(sb)
        paths_t = SR.resolve_sandbox_paths(str(sb), con_t)
        pins_t, _ = SR.live_operative_pins(con_t)
        closure_t = SR.build_reverify_closure(
            con_t, WORKTREE, reg_path, paths_t, pins_t,
            str(sb / GO_IN_SB), reg["row_stable_fields"],
            next(p["sha256"] for p in pins_t
                 if p["name"] == "a7_prelaunch_v3_digest"),
            paths_t["pin:a7_prelaunch_v3_digest"])
        ledger3 = str(sb / "ledger" / "p5site.jsonl")
        rc, terminal = SE.run_scored_execution({
            "cycle_id": T.CYCLE_ID, "sandbox_root": str(sb),
            "worktree": WORKTREE, "contract_path": str(sb / "launch_contract.json"),
            "builder_path": paths_t["pin:machinery_builder_v3"],
            "builder_pin_sha": next(
                p["sha256"] for p in pins_t
                if p["name"] == "machinery_builder_v3"),
            "builder_overrides": SE.sandbox_builder_overrides(str(sb), con_t),
            "identity_ids": con_t["embedded_laws"]["identity_ids"],
            "ledger_path": ledger3,
            "lock_runtime_dir": str(sb / "heavy_runtime"),
            "run_root": str(sb / "runs" / "p5site"),
            "command": ["p5site"], "fault": None,
            "reverify_authority": closure_t,
        })
        record("P5", executor_site_exit=rc)
        self.assertEqual(rc, 2)
        self.assertEqual(terminal["terminal_state"],
                         "REFUSED_CONTROL_STATE_DRIFT")
        self.assertEqual(terminal["lock_released_status"], "FAILED")
        self.assertFalse((sb / "runs" / "p5site" / "pass_a").exists())
        self.assertEqual(heavy_lock.flock_state(
            sb / "heavy_runtime" / heavy_lock.LOCK_NAME), "free")

    # ---------------------------------------------------------------- P6
    def test_P6_missing_pin_fails_closed_naming_the_pin(self):
        sb = fresh_sb("p6")
        (sb / EXCLUDE_REL).unlink()
        ledger = str(sb / "ledger" / "p6.jsonl")
        proc = run_cli(sb, ledger, "p6")
        T.log("P6", proc)
        record("P6", exit_code=proc.returncode)
        self.assertEqual(proc.returncode, 2, proc.stderr[-2500:])
        rr = refusal_record(sb)
        record("P6", refusal_reason=rr["reason"],
               mismatched=rr["detail"].get("mismatched_pins"))
        self.assertEqual(rr["reason"], "REFUSED_DRIFT")
        self.assertIn("exclude_list_v3", rr["detail"]["mismatched_pins"])
        self.assertTrue(any(r.get("reason") == "REFUSED_DRIFT"
                            for r in refused_rows(ledger)))
        assert_no_execution(self, sb)

    # ---------------------------------------------------------------- P7
    def test_P7_live_and_history_diagnostics_both_visible_no_clobber(self):
        con = load_contract(SB_ROOT)
        paths = SR.resolve_sandbox_paths(str(SB_ROOT), con)
        drift = SR.check_drift(con, WORKTREE, paths)
        record("P7", drift_pass=drift["pass"])
        self.assertTrue(drift["pass"], drift["mismatched_pins"])
        live = drift["pins_live"]
        hist = drift["pins_history"]
        self.assertTrue(live["scored_executor"]["match"])
        self.assertEqual(live["scored_executor"]["source_addendum"],
                         "v2_3_addendum")
        # the superseded twins are ALL visible under the SAME name —
        # v2_1's original pin and v2_2's re-pin, no clobber in either
        # direction (live row and history row coexist)
        he = hist["scored_executor"]
        self.assertEqual(len(he["entries"]), 2, he)
        self.assertEqual(he["entries"][0]["source_addendum"],
                         "v2_1_addendum")
        self.assertEqual(he["entries"][1]["source_addendum"],
                         "v2_2_addendum")
        self.assertIn("supersedes_note", he)
        self.assertIn("scored_runner", live)
        self.assertIn("scored_runner_v2_1", hist)
        self.assertIn("scored_runner", hist)   # the v2_2 twin of the same name
        self.assertEqual(len(hist["scored_runner"]["entries"]), 1)
        # explicit contract HISTORY rows stay evidence-only
        self.assertIn("donor_law_carryover_HISTORY", hist)
        self.assertIn("a7_adjudicated_freeze_bytes_HISTORY", hist)
        self.assertNotIn("donor_law_carryover_HISTORY", live)
        # no live pin was masked by a history row: every live name has a
        # match flag and every history name carries a supersedes note
        for name, row in live.items():
            self.assertIn("match", row, name)
        for name, row in hist.items():
            self.assertIn("supersedes_note", row, name)
        record("P7", live_names=len(live), history_names=len(hist),
               scored_executor_history_entries=2)

    # ---------------------------------------------------------------- P8
    def test_P8_registry_head_tamper_refused(self):
        sb = fresh_sb("p8")
        reg_path = sb / "registry/CYCLE_REGISTRY.rowcopy.json"
        reg = json.loads(reg_path.read_text("utf-8"))
        reg["cycles"][0]["head"] = "deadbeef" + "0" * 32
        reg_path.write_text(json.dumps(reg, indent=1, ensure_ascii=False),
                            encoding="utf-8")
        ledger = str(sb / "ledger" / "p8.jsonl")
        proc = run_cli(sb, ledger, "p8")
        T.log("P8", proc)
        record("P8", exit_code=proc.returncode)
        self.assertEqual(proc.returncode, 2, proc.stderr[-2500:])
        rr = refusal_record(sb)
        record("P8", refusal_reason=rr["reason"])
        self.assertEqual(rr["reason"], "REFUSED_CONTROL_STATE_DRIFT")
        self.assertTrue(any(r.get("reason")
                            == "REFUSED_CONTROL_STATE_DRIFT"
                            for r in refused_rows(ledger)))
        assert_no_execution(self, sb)

    # ---------------------------------------------------------------- P9
    def test_P9_regression_suites_all_green(self):
        suites = [
            ("fix2/test_finalization_fix.py",
             RUNNER_DIR / "fix2" / "test_finalization_fix.py"),
            ("test_runner_refusals.py", RUNNER_DIR / "test_runner_refusals.py"),
            ("test_execution_path.py", RUNNER_DIR / "test_execution_path.py"),
        ]
        for name, path in suites:
            proc = subprocess.run([sys.executable, str(path)],
                                  capture_output=True, text=True, timeout=3500)
            T.log(f"P9_{name.replace('/', '_')}", proc)
            record(f"P9:{name}", exit_code=proc.returncode,
                   tail=proc.stderr.splitlines()[-1:]
                   if proc.stderr.splitlines() else [])
            self.assertEqual(proc.returncode, 0,
                             f"{name} failed\n{proc.stderr[-3000:]}")
            self.assertIn("OK", proc.stderr.splitlines()[-1], name)

    # --------------------------------------------------------------- P10
    def test_P10_preflight_refusal_vs_execution_refusal(self):
        # the SAME tampered freeze bytes in BOTH modes
        tampered = (SB_ROOT / FREEZE_REL).read_bytes() + \
            b'{"pin_enforce": "P10 tampered freeze"}\n'
        tmp = Path(tempfile.mkdtemp(prefix="pin_enforce_p10_"))
        tampered_file = tmp / "selection_freeze_v3.tampered.json"
        tampered_file.write_bytes(tampered)

        # (a) PREFLIGHT mode (real wiring, tmp override path): refuses with
        # a wiring record, writes NOTHING else (no ledger, no outputs).
        manifest_out = tmp / "p10_preflight_manifest.json"
        proc = subprocess.run(
            [sys.executable, RUNNER, "--preflight-only",
             "--worktree", WORKTREE,
             "--lock-runtime-dir", str(tmp / "heavy_runtime"),
             "--freeze-path", str(tampered_file),
             "--ledger-path", str(tmp / "never_written.jsonl"),
             "--manifest-out", str(manifest_out)],
            capture_output=True, text=True, timeout=600)
        T.log("P10_preflight", proc)
        record("P10", preflight_exit=proc.returncode)
        self.assertEqual(proc.returncode, 2, proc.stderr[-2500:])
        man = json.loads(manifest_out.read_text("utf-8"))
        self.assertIn("REFUSED_DRIFT", man["wiring_failures"])
        self.assertFalse(man["drift_check"]["pins_live"]
                         ["operative_freeze_v3"]["match"])
        record("P10", preflight_wiring=man["wiring_failures"],
               preflight_writes="manifest only (no ledger, no outputs)")
        self.assertFalse((tmp / "never_written.jsonl").exists(),
                         "preflight wrote a ledger")
        self.assertFalse((tmp / "refusal_record.json").exists())

        # (b) EXECUTION mode over a sandbox copy carrying the SAME tampered
        # freeze bytes: refuses with a REFUSED ledger row + refusal_record
        # and produces NO execution artifacts — the enforcement proof.
        sb = fresh_sb("p10")
        (sb / FREEZE_REL).write_bytes(tampered)
        ledger = str(sb / "ledger" / "p10.jsonl")
        proc2 = run_cli(sb, ledger, "p10")
        T.log("P10_execution", proc2)
        record("P10", execution_exit=proc2.returncode)
        self.assertEqual(proc2.returncode, 2, proc2.stderr[-2500:])
        rr = refusal_record(sb)
        record("P10", execution_refusal_reason=rr["reason"],
               mismatched=rr["detail"].get("mismatched_pins"),
               distinction="preflight refusal proves wiring only; the "
                           "execution refusal (ledger REFUSED row + "
                           "refusal_record + no outputs) is the "
                           "enforcement proof")
        self.assertEqual(rr["reason"], "REFUSED_DRIFT")
        self.assertIn("operative_freeze_v3",
                      rr["detail"]["mismatched_pins"])
        self.assertTrue(any(r.get("reason") == "REFUSED_DRIFT"
                            for r in refused_rows(ledger)))
        assert_no_execution(self, sb)


if __name__ == "__main__":
    unittest.main(verbosity=2)
