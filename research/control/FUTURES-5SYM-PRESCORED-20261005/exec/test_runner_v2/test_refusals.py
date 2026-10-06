"""Refusal-gate tests for scored_runner_v2. Every case drives the REAL CLI
via subprocess against a sandbox and asserts: exit code, FINAL_STATUS.json
(refusal_code), the REFUSED ledger row (counts_observed=false) and
refusal_record.json.

Lineage: ported from the upstream FUTURES-ES-PB1-V1 refusal suite
(exec/_upstream_test_runner_refusals.py, commit 999ece60) — cases 1/2 (no
GO / paraphrased GO), 3a-c (delegated GO markers), 4 (drift), 6 (lock held).
The registry/GO/authority contract is re-derived for the 5-symbol PREP
cycle; the real-governance-dir refusal is NEW in this build (hard law).

  T2  no GO artifact            -> REFUSED_NO_GO_ARTIFACT        (rc 2)
  T3  wrong GO phrase           -> REFUSED_GO_PHRASE_MISMATCH     (rc 2)
  T4  GO for another cycle      -> REFUSED_GO_CYCLE_MISMATCH      (rc 2)
  T5  missing authority file    -> REFUSED_NO_AUTHORITY           (rc 2)
  T6  input drift (byte mutate) -> REFUSED_INPUT_DRIFT            (rc 2)
  T7  registry cycle-id absent  -> REFUSED_REGISTRY_MISMATCH      (rc 2)
  T19 missing prior artifact    -> REFUSED_MISSING_PRIOR_ARTIFACT (rc 2)
  T20 stale IN_PROGRESS marker  -> REFUSED_STALE_IN_PROGRESS      (rc 2)
      (recovery paths are proven in test_lock.py::test_T20_recovery)
"""
from __future__ import annotations

import json

from conftest import CYCLE, Sandbox, sha256_path


def _tolerant_rows(sb):
    """Parse ledger lines that ARE complete JSON; skip torn lines."""
    out = []
    if sb.ledger.is_file():
        for line in sb.ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _assert_refusal(sb, r, code, rc=2, expect_ledger_row=True):
    assert r.returncode == rc, (r.returncode, r.stdout, r.stderr)
    fs = sb.final()
    assert fs["status"] in ("REFUSED", "NOT_RUN_RESOURCE_CONFLICT")
    assert fs["refusal_code"] == code
    assert fs["exit_code"] == rc
    assert "EXECUTION_COMPLETE" not in json.dumps(fs)
    # REFUSED ledger row, never counted into the observed denominator —
    # EXCEPT when a pre-existing torn ledger blocks appending (the runner
    # never appends to a ledger failing integrity; it says so on stderr)
    rows = sb.ledger_rows() if expect_ledger_row else _tolerant_rows(sb)
    refused = [x for x in rows if x["row_type"] == "REFUSED" and
               x["payload"]["reason"] == code]
    if expect_ledger_row:
        assert refused, f"no REFUSED row for {code}"
        assert all(x["counts_observed"] is False for x in refused)
    else:
        assert not refused
        assert "TECHNICAL: refusal ledger recording failed" in r.stderr
    rr = sb.out / "refusal_record.json"
    assert rr.is_file()
    assert json.loads(rr.read_text())["reason"] == code
    # refusals are pre-computation: no TRIAL rows may exist
    assert not [x for x in rows if x["row_type"] == "TRIAL"]
    return fs


def test_T2_no_go_artifact(sb):
    sb.go.unlink()
    _assert_refusal(sb, sb.run(), "REFUSED_NO_GO_ARTIFACT")


def test_T3_wrong_go_phrase_byte_law(sb):
    sb.build(go_verbatim=f"GO {CYCLE} scored execution")  # case fold dies
    _assert_refusal(sb, sb.run(), "REFUSED_GO_PHRASE_MISMATCH")


def test_T3b_paraphrased_go(sb):
    sb.build(go_verbatim=f"GO {CYCLE} SCORED RUN")  # paraphrase dies
    _assert_refusal(sb, sb.run(), "REFUSED_GO_PHRASE_MISMATCH")


def test_T4_go_for_other_cycle(sb):
    sb.build(go_cycle="FUTURES-OTHER-CYCLE")
    _assert_refusal(sb, sb.run(), "REFUSED_GO_CYCLE_MISMATCH")


def test_T5_missing_authority_file(sb):
    sb.auth.unlink()
    _assert_refusal(sb, sb.run(), "REFUSED_NO_AUTHORITY")


def test_T5b_invalid_authority_content(sb):
    sb.auth.write_text("{\"cycle_id\": \"OTHER\", \"typed_by_owner\": false}")
    _assert_refusal(sb, sb.run(), "REFUSED_AUTHORITY_INVALID")


def test_T6_input_drift_fixture_byte(sb):
    fx = sb.inputs / "fixtures" / "NQ.csv"
    text = fx.read_text(encoding="utf-8")
    fx.write_text(text.replace("\n", "\n").rstrip("\n") + " \n",
                  encoding="utf-8")
    assert sha256_path(fx) is not None
    _assert_refusal(sb, sb.run(), "REFUSED_INPUT_DRIFT")


def test_T6b_input_drift_spec_sha_pin(sb):
    m = json.loads(sb.manifest.read_text(encoding="utf-8"))
    m["spec_packet_sha256"] = "0" * 64
    sb.manifest.write_text(json.dumps(m, indent=1), encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_INPUT_DRIFT")


def test_T7_registry_cycle_absent(sb):
    sb.build(registry_cycles=[{"cycle_id": "SOME-OTHER-CYCLE"}])
    _assert_refusal(sb, sb.run(), "REFUSED_REGISTRY_MISMATCH")


def test_T7b_registry_unreadable(sb):
    sb.registry.write_text("{not json")
    _assert_refusal(sb, sb.run(), "REFUSED_REGISTRY_MISMATCH")


def test_delegated_go_marker_dies(sb):
    # lineage: upstream refusal cases 3a-c — a delegated GO is not an owner GO
    sb.build(go_typed_by="DELEGATE", go_typed_by_owner=False)
    _assert_refusal(sb, sb.run(), "REFUSED_GO_NOT_OWNER_TYPED")


def test_delegated_go_language_marker_dies(sb):
    sb.build(extra_spec=None)
    art = json.loads(sb.go.read_text(encoding="utf-8"))
    art["key_owner_go"]["provenance_note"] = "issued on behalf of the owner"
    sb.go.write_text(json.dumps(art, indent=1), encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_GO_NOT_OWNER_TYPED")


def test_T19_missing_prior_artifact(sb):
    m = json.loads(sb.manifest.read_text(encoding="utf-8"))
    m["prior_artifacts"] = [{"name": "prior_freeze_pin",
                             "path": "prior/evidence_pin.json",
                             "sha256": None}]
    sb.manifest.write_text(json.dumps(m, indent=1), encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_MISSING_PRIOR_ARTIFACT")


def test_T19b_prior_artifact_present_then_run_completes(sb):
    prior = sb.inputs / "prior" / "evidence_pin.json"
    prior.parent.mkdir(parents=True, exist_ok=True)
    prior.write_text('{"pin": "synthetic"}\n', encoding="utf-8")
    m = json.loads(sb.manifest.read_text(encoding="utf-8"))
    m["prior_artifacts"] = [{"name": "prior_freeze_pin",
                             "path": "prior/evidence_pin.json",
                             "sha256": sha256_path(prior)}]
    sb.manifest.write_text(json.dumps(m, indent=1), encoding="utf-8")
    r = sb.run()
    assert r.returncode == 0, r.stderr


def test_T20_stale_marker_refused_without_recovery_flag(sb):
    # simulate a crashed prior run: IN_PROGRESS marker left behind
    marker = sb.out / "runs" / "run1" / "IN_PROGRESS.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"cycle_id": CYCLE, "run_label": "run1",
                                  "pid": 1, "engine_version": "x"}),
                      encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_STALE_IN_PROGRESS")


def test_T20c_stale_marker_refused_when_recovery_integrity_fails(sb):
    marker = sb.out / "runs" / "run1" / "IN_PROGRESS.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"cycle_id": CYCLE, "run_label": "run1",
                                  "pid": 1}), encoding="utf-8")
    # torn ledger line: recovery integrity check must fail even WITH the flag
    sb.ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(sb.ledger, "a", encoding="utf-8") as fh:
        fh.write('{"seq": 1, "row_type": "TRIAL", "TORN":\n')
    r = sb.run(extra=["--resume-with-recovery-check"])
    _assert_refusal(sb, r, "REFUSED_STALE_IN_PROGRESS",
                    expect_ledger_row=False)


def test_allow_real_governance_flag_is_dead_law(sb):
    r = sb.run(extra=["--allow-real-governance"])
    _assert_refusal(sb, r, "REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED")


def test_unknown_test_fault_name_refused(sb):
    r = sb.run(extra=["--test-fault", "not_a_fault"])
    assert r.returncode == 2
    assert "unknown --test-fault" in r.stderr


def test_missing_required_args_refused(tmp_path):
    sb = Sandbox(tmp_path).build()
    r = sb.run(extra=["--ledger", "", "--run-dir", "",
                      "--final-status-out", ""])
    assert r.returncode == 2


def test_bad_symbol_in_spec_refused(sb):
    spec = json.loads(sb.spec.read_text(encoding="utf-8"))
    spec["identities"][0]["symbol"] = "ZZ"
    sb.spec.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    m = json.loads(sb.manifest.read_text(encoding="utf-8"))
    m["spec_packet_sha256"] = sha256_path(sb.spec)
    sb.manifest.write_text(json.dumps(m, indent=1), encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_SPEC_INVALID")


def test_unknown_arm_refused(sb):
    spec = json.loads(sb.spec.read_text(encoding="utf-8"))
    spec["identities"][0]["arm"] = "moon-if-bar-up"
    sb.spec.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    m = json.loads(sb.manifest.read_text(encoding="utf-8"))
    m["spec_packet_sha256"] = sha256_path(sb.spec)
    sb.manifest.write_text(json.dumps(m, indent=1), encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_SPEC_INVALID")


def test_bad_cost_tier_refused(sb):
    spec = json.loads(sb.spec.read_text(encoding="utf-8"))
    spec["identities"][0]["cost_tier"] = "t9"
    sb.spec.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    m = json.loads(sb.manifest.read_text(encoding="utf-8"))
    m["spec_packet_sha256"] = sha256_path(sb.spec)
    sb.manifest.write_text(json.dumps(m, indent=1), encoding="utf-8")
    _assert_refusal(sb, sb.run(), "REFUSED_SPEC_INVALID")
