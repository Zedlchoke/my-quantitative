"""test_freeze_builder_gates — GATE-0 refusal demos + bundle determinism.

Every GATE-0 refusal: its own exit code, FINAL status artifact written, and
NO bundle output dir created ("writes nothing" law). All authority artifacts
here are FORGED SANDBOX FIXTURES inside pytest tmp dirs (lawful for machinery
proofs; they are not authority and never leave the sandbox).
"""
from __future__ import annotations

import json

import pytest

from conftest import (EPOCH, run_builder, write_freeze_input_manifest,
                      write_gate_artifacts)

CYCLE = "FUTURES-5SYM-PRESCORED-20261005"


def _inputs(tmp, symbol="NQ"):
    return write_freeze_input_manifest(tmp, symbol)


def test_locks_start_recorded():
    from conftest import record_lock_line
    line = record_lock_line("suite-start")
    assert line["verdict"] in ("FREE_PROVEN", "HELD_PROVEN",
                               "CONTROL_STATE_DRIFT")
    # suite light: the canonical heavy lock must NOT be taken by this lane
    assert line["verdict"] == "FREE_PROVEN", (
        "heavy lock unexpectedly held at suite start — NOT_RUN_RESOURCE_"
        "CONFLICT posture required; never take it")


def test_nq_bundle_happy_path_and_determinism(tmp_path):
    manifest = _inputs(tmp_path)
    gates = write_gate_artifacts(tmp_path, ["d9", "ceiling"])
    rc1, st1, out1 = run_builder(tmp_path, "NQ", manifest, gates, "run1")
    rc2, st2, out2 = run_builder(tmp_path, "NQ", manifest, gates, "run2")
    assert rc1 == 0 and rc2 == 0, (rc1, rc2, st1, st2)
    assert st1["status"] == "FREEZE_BUNDLE_COMPLETE"
    assert st1["gates"] == [{"gate": "d9", "schema": "d9_ratification@1",
                             "status": "PASSED"},
                            {"gate": "ceiling", "schema": "ceiling@1",
                             "status": "PASSED"}]
    files = ["freeze_manifest_NQ.json", "frozen_identity_table_NQ.json",
             "frozen_exclusion_calendar_NQ.json"]
    for f in files:
        assert (out1 / f).read_bytes() == (out2 / f).read_bytes(), \
            f"bundle not deterministic: {f}"
    fm = json.loads((out1 / "freeze_manifest_NQ.json").read_text())
    assert fm["schema"] == "futures_5sym_prescored/freeze_manifest@1"
    assert fm["generated_at"] == EPOCH          # --epoch, never wallclock
    assert fm["sandbox_stamp"] == "SYNTHETIC-SANDBOX"
    assert len(fm["input_digests"]) == 7        # every manifest input
    import hashlib
    from pathlib import Path as _P
    builder_src = _P(__file__).parents[1] / "freeze_builder.py"
    code_sha = hashlib.sha256(builder_src.read_bytes()).hexdigest()
    assert fm["builder_code_sha256"] == code_sha
    assert len(fm["content_stamp_sha256"]) == 64
    # identity-table binding present and pinned to a 64-hex digest
    assert len(fm["identity_table_binding"]["sha256"]) == 64


def test_nq_refusals_missing_and_invalid(tmp_path):
    manifest = _inputs(tmp_path)
    gates = write_gate_artifacts(tmp_path, ["ceiling"])
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "nq_no_d9")
    assert rc == 21 and st["status"] == "REFUSED_GATE0_NQ_D9_UNSIGNED"
    assert st["inputs_consumed"] == 0 and not out.exists()
    assert "UNSIGNED" in json.dumps(st["refusal_detail"])

    # present but wrong decision (Option B routes back, never passes)
    gates = write_gate_artifacts(tmp_path, ["d9", "ceiling"], overrides={
        "d9": {"decision": "ADOPT-D9-OptionB"}})
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "nq_d9_b")
    assert rc == 29 and st["status"] == "REFUSED_GATE0_ARTIFACT_INVALID"
    assert not out.exists()

    # not owner-typed (signature law)
    gates = write_gate_artifacts(tmp_path, ["d9", "ceiling"], overrides={
        "d9": {"typed_by_owner": False}})
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "nq_d9_unsigned_sig")
    assert rc == 29 and st["status"] == "REFUSED_GATE0_ARTIFACT_INVALID"

    # wrong schema (meas_nq law: schema != d9_ratification@1 refuses)
    gates = write_gate_artifacts(tmp_path, ["d9", "ceiling"], overrides={
        "d9": {"schema": "d9_ratification@2"}})
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "nq_d9_schema")
    assert rc == 29

    # missing ceiling (identity-table binding)
    gates = write_gate_artifacts(tmp_path, ["d9"])
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "nq_no_ceiling")
    assert rc == 22 and st["status"] == "REFUSED_GATE0_CEILING_UNSIGNED"
    assert not out.exists()


def test_6e_6b_pb2_gate(tmp_path):
    manifest = _inputs(tmp_path, "6E")
    gates = write_gate_artifacts(tmp_path, ["ceiling"])
    rc, st, out = run_builder(tmp_path, "6E", manifest, gates, "6e_no_pb2")
    assert rc == 23 and st["status"] == "REFUSED_GATE0_PB2_UNSIGNED"
    assert not out.exists()
    # with the (forged sandbox) lift present the machinery completes
    gates = write_gate_artifacts(tmp_path, ["pb2", "ceiling"])
    rc, st, out = run_builder(tmp_path, "6B", write_freeze_input_manifest(
        tmp_path, "6B"), gates, "6b_ok")
    assert rc == 0 and st["status"] == "FREEZE_BUNDLE_COMPLETE"


def test_6a_full_chain_order(tmp_path):
    manifest = _inputs(tmp_path, "6A")
    rc, st, out = run_builder(tmp_path, "6A", manifest, {}, "6a_none")
    assert rc == 24 and st["status"] == "REFUSED_GATE0_PB3_UNSIGNED"
    gates = write_gate_artifacts(tmp_path, ["pb3", "d9", "ceiling"])
    rc, st, out = run_builder(tmp_path, "6A", manifest, gates, "6a_no_d8")
    assert rc == 25 and st["status"] == "REFUSED_GATE0_D8_UNSIGNED"
    gates = write_gate_artifacts(tmp_path, ["pb3", "d8", "ceiling"])
    rc, st, out = run_builder(tmp_path, "6A", manifest, gates, "6a_no_d9")
    assert rc == 21 and st["status"] == "REFUSED_GATE0_NQ_D9_UNSIGNED"
    # Option B on D8 refuses (measured boundary not ratified)
    gates = write_gate_artifacts(tmp_path, ["pb3", "d8", "d9", "ceiling"],
                                 overrides={"d8": {"decision":
                                                   "ADOPT-D8-OptionB"}})
    rc, st, out = run_builder(tmp_path, "6A", manifest, gates, "6a_d8_b")
    assert rc == 29
    gates = write_gate_artifacts(tmp_path, ["pb3", "d8", "d9", "ceiling"])
    rc, st, out = run_builder(tmp_path, "6A", manifest, gates, "6a_ok")
    assert rc == 0 and st["status"] == "FREEZE_BUNDLE_COMPLETE"
    assert not out.exists() or (out / "freeze_manifest_6A.json").is_file()


def test_6j_ceiling_gate_names_option_and_shadow(tmp_path):
    manifest = _inputs(tmp_path, "6J")
    gates = write_gate_artifacts(tmp_path, ["ceiling"])
    rc, st, out = run_builder(tmp_path, "6J", manifest, gates, "6j_none")
    assert rc == 26 and st["status"] == "REFUSED_GATE0_6J_CEILING_UNSIGNED"
    assert not out.exists()
    # option must be one of J-A/J-B/J-C (P5-D1)
    gates = write_gate_artifacts(tmp_path, ["six_je_ceiling", "ceiling"],
                                 overrides={"six_je_ceiling": {"option": "J-D"}})
    rc, st, out = run_builder(tmp_path, "6J", manifest, gates, "6j_bad_opt")
    assert rc == 29
    # clock-shadow reading must be named (a)/(b)
    gates = write_gate_artifacts(tmp_path, ["six_je_ceiling", "ceiling"],
                                 overrides={"six_je_ceiling": {
                                     "clock_shadow_reading": None}})
    rc, st, out = run_builder(tmp_path, "6J", manifest, gates, "6j_no_shadow")
    assert rc == 29
    # valid signature + identity-table ceiling -> machinery completes
    gates = write_gate_artifacts(tmp_path, ["six_je_ceiling", "ceiling"])
    rc, st, out = run_builder(tmp_path, "6J", manifest, gates, "6j_ok")
    assert rc == 0 and st["status"] == "FREEZE_BUNDLE_COMPLETE"


def test_gate1_input_drift_and_missing(tmp_path):
    manifest = _inputs(tmp_path)
    gates = write_gate_artifacts(tmp_path, ["d9", "ceiling"])
    # tamper one input AFTER pinning
    import json as _json
    m = _json.loads(open(manifest).read())
    victim = next(i for i in m["inputs"] if i["role"] == "panel")
    p = __import__("pathlib").Path(victim["path"])
    p.write_bytes(p.read_bytes() + b"TAMPER")
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "drift")
    assert rc == 27 and st["status"] == "REFUSED_INPUT_DRIFT"
    assert not out.exists()
    # missing input file
    p.unlink()
    rc, st, out = run_builder(tmp_path, "NQ", manifest, gates, "missing")
    assert rc == 30 and st["status"] == "REFUSED_INPUT_MISSING"


def test_manifest_invalid_cases(tmp_path):
    gates = write_gate_artifacts(tmp_path, ["d9", "ceiling"])
    # wrong cycle id
    manifest = _inputs(tmp_path)
    m = json.loads(open(manifest).read())
    m["cycle_id"] = "OTHER"
    p = tmp_path / "m_bad_cycle.json"
    p.write_text(json.dumps(m))
    rc, st, out = run_builder(tmp_path, "NQ", str(p), gates, "badcycle")
    assert rc == 31
    # unsupported symbol
    rc, st, out = run_builder(tmp_path, "XX", manifest, gates, "badsym")
    assert rc == 31
    # missing required role
    m = json.loads(open(manifest).read())
    m["inputs"] = [i for i in m["inputs"] if i["role"] != "chain"]
    p2 = tmp_path / "m_norole.json"
    p2.write_text(json.dumps(m))
    rc, st, out = run_builder(tmp_path, "NQ", str(p2), gates, "norole")
    assert rc == 31


def test_cease_guard_chain_diverges_exactly_at_guard_date(tmp_path):
    """6A-style violation day: the held contract has NO bars on 2020-11-20;
    the guard variant switches to the next contract EXACTLY there (naive
    crossover would have rolled later)."""
    from freeze_builder import cease_guard_chain
    chain = [
        {"date": "2020-11-18", "held": "6AZ0", "next": "6AH1"},
        {"date": "2020-11-19", "held": "6AZ0", "next": "6AH1"},
        {"date": "2020-11-20", "held": "6AZ0", "next": "6AH1"},  # violation
        {"date": "2020-11-23", "held": "6AH1", "next": None},
    ]
    sessions_with_bars = {("2020-11-18", "6AZ0"), ("2020-11-19", "6AZ0"),
                          ("2020-11-23", "6AH1")}
    res = cease_guard_chain(chain, sessions_with_bars)
    assert res["cease_floor_first_fire"] == "2020-11-20"
    assert res["first_divergence_date"] == "2020-11-20"
    naive = dict(res["naive"])
    guarded = dict(res["guarded"])
    assert naive["2020-11-19"] == guarded["2020-11-19"] == "6AZ0"
    assert guarded["2020-11-20"] == "6AH1"      # guard switched exactly there
    assert naive["2020-11-20"] == "6AZ0"        # naive kept the dead contract
    assert guarded["2020-11-23"] == naive["2020-11-23"] == "6AH1"
