"""test_wiring_e2e — synthetic proofs through the REAL code path.

Path under test (the integration seam):
  family adapter order_intent records (adapt_* lanes, real adapter code)
    -> intent_contract normalization
    -> SINGLE-intent groups: spec_compiler.compile_identity_group
       (positional accounting-test encoding, POSITIONAL_ACCOUNTING_TEST_ONLY)
    -> MULTI-intent groups: wiring/intent_executor (intent_packet@1, the
       REAL intent-execution seam — the positional encoding REFUSES them
       with REFUSED_POSITIONAL_SCOPE since wave-4 WIRING-FIX)
    -> exec/scored_runner_v2.py CLI (subprocess; intent-mode dispatch inside)
    -> append-only ledger rows per identity + twin + publication.

WAVE-4 ADJUSTMENTS (documented in dispatch/handoff_WIRING-FIX.json):
  - test_nq_f1_end_to_end_identity_denominator: the ALW identity (2 intents)
    now refuses on the positional path (REFUSED_POSITIONAL_SCOPE) and runs
    through the intent seam instead — same denominator laws, stronger
    per-intent timestamp assertions.
  - test_compiled_pit_truncation_identical_trades_up_to_T: positional PIT
    proof now uses a single-intent identity (multi-trade PIT law lives in
    test_intent_seam.py::test_tmd8).
  - test_6a_era_boundary_through_runner: the 2-intent era group now expects
    REFUSED_POSITIONAL_SCOPE; the positive era-boundary accounting proof
    moved to test_intent_seam.py::test_tmd5c (same expected numbers).

All authority is fake and lives in pytest tmp dirs (sandbox-only law).
No real data, no real governance writes, no scored outcome exists.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

import panel_fixtures as pf
from conftest import CYCLE_DIR, PY
from wiring import adapter_binding, intent_executor as ie, spec_compiler as sc
from wiring.intent_contract import normalize_intent

TOL = 1e-6


def compile_and_run(intents, tmp_path, label, cost_law=None, gov_kwargs=None,
                    test_fault=None, work_dir=None):
    work = Path(work_dir) if work_dir else (tmp_path / label)
    work.mkdir(parents=True, exist_ok=True)
    return sc.compile_and_run(
        intents, str(work), run_label=label,
        cost_usd_law=cost_law or dict(sc.DEFAULT_COST_USD_LAW),
        test_fault=test_fault, gov_kwargs=gov_kwargs or {},
        epoch="2026-10-05T00:00:00Z", python=PY)


def intent_seam_run(intents, panel, tmp_path, label, cost_law=None,
                    work_dir=None):
    """Route an adapter intent group through the REAL intent-execution seam
    (intent_packet@1) on the panel's own session timeline (wave-4).
    Session dates are deduped (last aggregate per date wins — the same law
    the seam builder applies; NQ panels carry a warmup row + an event-day
    override for event dates)."""
    by_date = {}
    for s in panel["sessions"]:
        by_date[s["session_date"]] = s
    sessions = [{"session_date": d, "open": by_date[d]["open"],
                 "high": by_date[d]["high"], "low": by_date[d]["low"],
                 "close": by_date[d]["close"]}
                for d in sorted(by_date)]
    work = Path(work_dir) if work_dir else (tmp_path / label)
    work.mkdir(parents=True, exist_ok=True)
    folds = [{"fold_id": "F-SESSIONS", "start_bar": 0,
              "end_bar": len(sessions)}]
    return ie.intent_and_run(
        ie.group_intents(intents), sessions, folds=folds,
        work_dir=str(work), run_label=label,
        cost_usd_law=cost_law or dict(sc.DEFAULT_COST_USD_LAW),
        epoch="2026-10-05T00:00:00Z", python=PY)


# ------------------------------------------------------------- binding tests

def test_adapter_binding_registry_and_imports():
    snap = adapter_binding.discovery_snapshot()
    wired = {w["family"]: w for w in snap["wired"]}
    assert set(wired) == {"NQ-F1", "NQ-F2", "NQ-F3", "NQ-F4",
                          "FX-F1", "FX-F2", "FX-F3", "FX-F4", "FX-F5",
                          "FX-F6", "RMM-FXEB",
                          "JF1", "JF2", "JF3", "RMM6J",
                          "AF1", "AF3", "AF4", "RMM6A"}
    for fam, w in wired.items():
        assert w["exists"], f"{fam} declared wired but module missing"
        mod = adapter_binding.load_family_module(
            adapter_binding.find_family(fam))
        assert mod is not None
        if w["kind"] == "class":
            assert hasattr(mod, w["cls"]), fam
        else:
            # FX-F5 is an OVERLAY (no standalone order_intent by construction
            # — 0 standalone IDs; it composes onto host arms), so only the
            # observables+signal interface is required at binding level
            for fn in ("build_observables", "signal"):
                assert hasattr(mod, fn), (fam, fn)
    # nothing pending at adapter-module level; authority-gated slots listed
    assert snap["pending_wiring"] == []
    gated = {g for entry in snap["authority_gated"] for g in entry["families"]}
    assert {"AF1", "AF3", "AF4", "RMM6A"} <= gated       # 6A activation chain
    assert "JF1" in gated and "FX-F1" in gated           # ceiling / PB2 gates


# ------------------------------------------------------- NQ-F1 adapter proofs

def test_nq_f1_pit_asof_truncation_byte_identical():
    """No-future-data at the ADAPTER layer: order_intent on a truncated panel
    (rows > T removed) == order_intent on the full panel with asof=T."""
    fam = adapter_binding.find_family("NQ-F1")
    panel, calendar = pf.build_nq_panel()
    full_intents = adapter_binding.collect_class_intents(fam, panel, calendar)
    up_day = "2023-06-14"
    mod = adapter_binding.load_family_module(fam)
    iid = "FBNQ1-F1-CONT-UP-D0-S2"
    from nq_common import ct_offset_str  # lane module (already on sys.path)
    # T = 13:05 CT on the UP event day: post-decision, pre-resolution.
    T = f"{up_day}T13:05:00{ct_offset_str(up_day)}"
    trunc = {**panel, "bars": [b for b in panel["bars"] if b["ts"] <= T]}
    rec_full = mod.FomcEraAdapter().order_intent(panel, calendar, iid, up_day,
                                                 asof=T)
    rec_trunc = mod.FomcEraAdapter().order_intent(trunc, calendar, iid, up_day,
                                                  asof=T)
    assert rec_full == rec_trunc                      # byte-identical PIT law
    assert rec_full["exit_resolution"] == "PENDING_UPTO_ASOF"
    # post-session asof resolves; a panel truncated AT the session end agrees
    T2 = f"{up_day}T15:59:00{ct_offset_str(up_day)}"
    rec_full2 = mod.FomcEraAdapter().order_intent(panel, calendar, iid, up_day,
                                                  asof=T2)
    trunc2 = {**panel, "bars": [b for b in panel["bars"] if b["ts"] <= T2]}
    rec_trunc2 = mod.FomcEraAdapter().order_intent(trunc2, calendar, iid,
                                                   up_day, asof=T2)
    assert rec_full2 == rec_trunc2
    assert rec_full2["exit_resolution"] == "RESOLVED"
    assert full_intents, "adapter must produce resolvable trades"


def test_nq_f1_end_to_end_identity_denominator(tmp_path):
    """Real adapter -> seam -> runner CLI -> shared append-only ledger: one
    TRIAL row per identity; observed == executed == published; declared
    zero-trade anchors stay out of the denominator. Single-intent
    identities take the positional accounting-test path; the multi-intent
    ALW identity REFUSES the positional path (REFUSED_POSITIONAL_SCOPE,
    wave-4) and executes through the intent seam — both append to the SAME
    shared ledger and the cumulative denominator law is unchanged."""
    fam = adapter_binding.find_family("NQ-F1")
    panel, calendar = pf.build_nq_panel()
    intents = adapter_binding.collect_class_intents(fam, panel, calendar)
    by_id = {}
    for it in intents:
        by_id.setdefault(it["identity_id"], []).append(it)
    compiled_ids = sorted(by_id)
    assert compiled_ids == sorted(
        [f"FBNQ1-F1-{a}-{t}-{d}-S2"
         for a in ("CONT", "REV") for t in ("UP", "DN")
         for d in ("D0", "D30")]
        + ["FBNQ1-F1-ALW-D0-S2"]), compiled_ids
    identity_table = {iid: len(by_id.get(iid, [])) for iid in
                      compiled_ids + ["FBNQ1-F1-SHDW-D0-S2", "FBNQ1-F1-FLAT"]}
    assert identity_table["FBNQ1-F1-FLAT"] == 0        # zero-trade anchor
    assert identity_table["FBNQ1-F1-SHDW-D0-S2"] == 0  # no matched Wed bars

    shared = tmp_path / "shared"
    processed = 0
    for iid in compiled_ids:
        its = by_id[iid]
        if len(its) > 1:
            # wave-4 positional scope: multi-intent groups refuse the
            # positional encoding and route through the intent seam
            with pytest.raises(sc.CompileRefusal) as ei:
                compile_and_run(its, tmp_path, f"refused_{iid}",
                                work_dir=shared)
            assert ei.value.code == "REFUSED_POSITIONAL_SCOPE"
            assert ei.value.exit_code == 46
            res = intent_seam_run(its, panel, tmp_path, f"seam_{iid}",
                                  work_dir=shared)
        else:
            res = compile_and_run(its, tmp_path, f"run{processed}",
                                  work_dir=shared)
        assert res["exit_code"] == 0, (iid, res["final_status"], res["stderr"])
        fs = res["final_status"]
        assert fs["status"] == "EXECUTION_COMPLETE"
        assert fs["sandbox_stamp"] == "SYNTHETIC-SANDBOX"
        trials = [r for r in res["ledger_rows"] if r["row_type"] == "TRIAL"]
        processed += 1
        assert len(trials) == processed                # append-only growth
        assert trials[-1]["identity_id"] == iid
        if len(its) > 1:
            # intent seam: per-intent journal — BOTH legs present with their
            # own timestamps (impossible under the positional encoding)
            rec = trials[-1]["payload"]
            assert rec["mode"] == "intent"
            assert rec["totals"]["n_trades"] == identity_table[iid]
            assert [t["entry_ts"] for t in rec["journal"]] == \
                sorted(i["entry_date"] for i in its)
            for t, declared in zip(rec["journal"],
                                   sorted(its, key=lambda i: i["entry_date"])):
                assert t["direction"] == declared["direction"]
                assert t["entry_price"] == declared["entry_price"]
                assert t["exit_price"] == declared["exit_price"]
                assert t["exit_reason"] == declared["exit_reason"]
        else:
            trades = trials[-1]["payload"]["folds"][0]["trades"]
            rec = res["compile"]
            assert len(trades) == identity_table[iid]
            for t, exp in zip(trades, rec["expected_trades"]):
                assert t["entry_price"] == exp["entry_price"]
                assert t["exit_price"] == exp["exit_price"]
                assert t["direction"] == exp["direction"]
                assert abs(t["net_pnl_usd"]
                           - exp["expected_net_pnl_usd"]) < TOL, (t, exp)
        assert fs["observed_identity_count"] == processed  # cumulative
        pub = json.loads((shared / "runs" / res["final_status"]["run_label"] /
                          "published_summary.json").read_text())
        assert pub["published_identity_count"] == processed
        recon = json.loads((shared / "runs" / res["final_status"]["run_label"]
                            / "reconciliation_report.json").read_text())
        assert recon["match"] is True                  # twin per run

    # duplicate identity re-submission: skipped, NO double count. The first
    # sorted identity is the multi-intent ALW identity, so the retry goes
    # through the SAME seam path that observed it (stronger: the 2-intent
    # mixed group cannot double-count even on retry).
    res = intent_seam_run(by_id[compiled_ids[0]], panel, tmp_path, "run_dupe",
                          work_dir=shared)
    assert res["exit_code"] == 0
    rows = res["ledger_rows"]
    dups = [r for r in rows if r["row_type"] == "DUPLICATE_RETRY"]
    assert dups and dups[0]["identity_id"] == compiled_ids[0]
    assert dups[0]["counts_observed"] is False
    trials_now = [r for r in rows if r["row_type"] == "TRIAL"]
    assert len(trials_now) == len(compiled_ids)        # no new TRIAL row
    assert res["final_status"]["observed_identity_count"] == len(compiled_ids)
    # published stays separate from observed and equal on success
    pub = json.loads((shared / "runs" / "run_dupe" /
                      "published_summary.json").read_text())
    assert pub["observed_identity_count"] == len(compiled_ids)
    assert pub["published_identity_count"] == len(compiled_ids)
    assert pub["duplicate_retry_ids"] == [compiled_ids[0]]


def test_compiled_pit_truncation_identical_trades_up_to_T(tmp_path):
    """No-future-data at the RUNNER layer (positionally-encoded PIT law,
    single-intent group — wave-4 scope): truncating the compiled fixture at
    T and running vs the full run produces IDENTICAL completed trades up to
    T; an exit-less truncation fabricates NO trade. The multi-trade PIT law
    is proven on the real seam (test_intent_seam.py::test_tmd8)."""
    fam = adapter_binding.find_family("NQ-F1")
    panel, calendar = pf.build_nq_panel()
    intents = [i for i in adapter_binding.collect_class_intents(fam, panel,
                                                                calendar)
               if i["identity_id"] == "FBNQ1-F1-CONT-UP-D0-S2"]  # 1 trade
    assert len(intents) == 1
    full = compile_and_run(intents, tmp_path, "pit_full")
    assert full["exit_code"] == 0
    full_trades = full["trials"][0]["payload"]["folds"][0]["trades"]
    assert len(full_trades) == 1

    comp = full["compile"]
    # truncation that still completes the trade: identical to the full run
    work = tmp_path / "pit_trunc"
    work.mkdir(parents=True, exist_ok=True)
    lines = Path(comp["fixture"]).read_text().splitlines()
    trunc_csv = work / "fixture_trunc.csv"
    trunc_csv.write_text("\n".join(lines[:5]) + "\n")  # header + 4 bars
    spec = json.loads(Path(comp["spec_packet"]).read_text())
    spec["folds"][0]["end_bar"] = 4
    spec_p = work / "spec_packet.json"
    spec_p.write_bytes(sc.canonical_json(spec))
    cm_p = work / "cost_manifest.json"
    shutil.copy(comp["cost_manifest"], cm_p)
    manifest = {"schema": "futures_5sym_prescored/input_manifest@1",
                "cycle_id": sc.CYCLE_ID, "epoch": "2026-10-05T00:00:00Z",
                "fixtures": [{"symbol": "NQ", "path": trunc_csv.name,
                              "sha256": hashlib.sha256(
                                  trunc_csv.read_bytes()).hexdigest(),
                              "bars_expected": 4}],
                "spec_packet_sha256": sc.sha256_file(spec_p),
                "cost_manifest_sha256": sc.sha256_file(cm_p),
                "symbol_contracts_sha256": sc.sha256_file(sc.CONTRACTS)}
    mp = work / "input_manifest.json"
    mp.write_bytes(sc.canonical_json(manifest))
    gov = sc.make_sandbox_authority(str(work / "gov"))
    res = sc.invoke_runner(
        input_manifest=str(mp), spec_packet=str(spec_p),
        cost_manifest=str(cm_p), gov=gov,
        ledger=str(work / "ledger.jsonl"), run_dir=str(work / "runs" / "t"),
        final_status_out=str(work / "FS.json"), run_label="t", python=PY)
    assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
    rows = sc.trial_rows(str(work / "ledger.jsonl"))
    trades_t = rows[0]["payload"]["folds"][0]["trades"]
    assert len(trades_t) == 1
    assert trades_t[0] == full_trades[0]   # identical trades up to T

    # truncation WITHOUT the exit bar: no trade is fabricated (the declared
    # trade cannot complete on the truncated timeline — never invented)
    work3 = tmp_path / "pit_trunc3"
    work3.mkdir(parents=True, exist_ok=True)
    trunc3 = work3 / "fixture_trunc3.csv"
    trunc3.write_text("\n".join(lines[:4]) + "\n")     # header + 3 bars
    spec3 = json.loads(Path(comp["spec_packet"]).read_text())
    spec3["folds"][0]["end_bar"] = 3
    spec3_p = work3 / "spec_packet.json"
    spec3_p.write_bytes(sc.canonical_json(spec3))
    cm3 = work3 / "cost_manifest.json"
    shutil.copy(comp["cost_manifest"], cm3)
    manifest3 = dict(manifest, fixtures=[{
        "symbol": "NQ", "path": trunc3.name,
        "sha256": hashlib.sha256(trunc3.read_bytes()).hexdigest(),
        "bars_expected": 3}],
        spec_packet_sha256=sc.sha256_file(spec3_p),
        cost_manifest_sha256=sc.sha256_file(cm3))
    m3 = work3 / "input_manifest.json"
    m3.write_bytes(sc.canonical_json(manifest3))
    gov3 = sc.make_sandbox_authority(str(work3 / "gov"))
    res3 = sc.invoke_runner(
        input_manifest=str(m3), spec_packet=str(spec3_p),
        cost_manifest=str(cm3), gov=gov3,
        ledger=str(work3 / "ledger.jsonl"), run_dir=str(work3 / "runs" / "t"),
        final_status_out=str(work3 / "FS.json"), run_label="t3", python=PY)
    assert res3["exit_code"] == 0, (res3["final_status"], res3["stderr"])
    rows3 = sc.trial_rows(str(work3 / "ledger.jsonl"))
    assert rows3[0]["payload"]["folds"][0]["trades"] == []


# ------------------------------------------------------------------ 6J proofs

def test_6j_direction_sign_through_real_adapter_and_runner(tmp_path):
    """6J quote-direction law (SPEC sign convention, T18-class): a synthetic
    yen-STRENGTHENING up-move (quoted USD-per-JPY number RISING) makes the
    DRIFT-UP long book POSITIVE net through the real runner; REV-UP negative.
    The inverted (JPY-per-USD) misread would flip every sign."""
    fam = adapter_binding.find_family("JF1")
    panel, calendar = pf.build_6j_panel()
    intents = adapter_binding.collect_class_intents(fam, panel, calendar)
    by_id = {}
    for it in intents:
        by_id.setdefault(it["identity_id"], []).append(it)
    assert set(by_id) == {"FB6J1-JF1-DRIFT-UP-D1-S2",
                          "FB6J1-JF1-DRIFT-UP-D30M-S2",
                          "FB6J1-JF1-REV-UP-D1-S2",
                          "FB6J1-JF1-REV-UP-D30M-S2",
                          "FB6J1-ALW-JF1", "FB6J1-PLA-JF1"}, sorted(by_id)
    drift = by_id["FB6J1-JF1-DRIFT-UP-D1-S2"][0]
    assert drift["direction"] == 1                     # long on UP tail
    nets = {}
    for iid, its in by_id.items():
        r = compile_and_run(its, tmp_path, f"6j_{iid.replace('-', '_')}",
                            cost_law=pf.COST_LAW_6J)
        assert r["exit_code"] == 0, (iid, r["final_status"], r["stderr"])
        trades = r["trials"][0]["payload"]["folds"][0]["trades"]
        nets[iid] = sum(t["net_pnl_usd"] for t in trades)
    assert nets["FB6J1-JF1-DRIFT-UP-D1-S2"] > 0        # yen strong -> long wins
    assert nets["FB6J1-JF1-REV-UP-D1-S2"] < 0          # mirror arm flips sign


# ------------------------------------------------------------------ 6A proofs

def _6a_intents():
    era1 = normalize_intent(
        identity_id="6A-ERA-PROOF-COMPILE-ONLY", symbol="6A", family="compiler",
        direction=1, entry_date="2020-11-19", exit_date="2020-11-20",
        entry_price=0.6550, exit_price=0.6600, cost_tier="S2", stress=1.0,
        source_adapter="freeze_wiring/spec_compiler (6A contingency packet; "
                       "no family adapter exists by design)")
    era2 = normalize_intent(
        identity_id="6A-ERA-PROOF-COMPILE-ONLY", symbol="6A", family="compiler",
        direction=1, entry_date="2020-11-24", exit_date="2020-11-25",
        entry_price=0.65500, exit_price=0.66000, cost_tier="S2", stress=1.0,
        source_adapter="freeze_wiring/spec_compiler (6A contingency packet)")
    return era1, era2


def test_6a_era_boundary_through_runner(tmp_path):
    """6A era law through the POSITIONAL encoding: the 2-era group is
    MULTI-INTENT and therefore REFUSED since wave-4 WIRING-FIX
    (REFUSED_POSITIONAL_SCOPE — the positional encoding can no longer
    silently fold both eras into one identity block). The positive
    era-boundary accounting proof (era-1 $10/tick vs era-2 $5/tick, gross
    500/500, cost 57.00/30.75 with an era-1-calibrated manifest) now runs on
    the REAL intent-execution seam:
    test_intent_seam.py::test_tmd5_calendar_roll_era_and_quote_boundaries."""
    era1, era2 = _6a_intents()
    with pytest.raises(sc.CompileRefusal) as ei:
        compile_and_run([era1, era2], tmp_path, "era6a")
    assert ei.value.code == "REFUSED_POSITIONAL_SCOPE"
    assert ei.value.exit_code == 46
    assert ei.value.detail["n_intents"] == 2
    assert ei.value.detail["directions"] == [1]   # distinct directions
    # single-intent era proofs remain legal on the positional path (one
    # compiled trade per era identity), each binding its OWN entry era:
    for intent, want_era, want_tval in ((era1, "6A-era1", 10.0),
                                        (era2, "6A-era2", 5.0)):
        res = compile_and_run([intent], tmp_path,
                              f"era6a_{want_era.replace('-', '_')}")
        assert res["exit_code"] == 0, (res["final_status"], res["stderr"])
        trades = res["trials"][0]["payload"]["folds"][0]["trades"]
        assert len(trades) == 1
        t = trades[0]
        assert t["era"] == want_era
        assert t["tick_value_usd"] == want_tval
        assert abs(t["gross_pnl_usd"] - 500.0) < TOL   # era-invariant factor
        for t_, exp in zip(trades, res["compile"]["expected_trades"]):
            assert abs(t_["net_pnl_usd"]
                       - exp["expected_net_pnl_usd"]) < TOL


def test_6a_era1_cost_model_refusal_for_era2_arm(tmp_path):
    """Era-1-calibrated cost manifest must REFUSE era-2-calibrated arms
    (never silently re-price): explicit C3 gate through the wiring stack."""
    contracts = sc.load_contracts()
    era1, era2 = _6a_intents()
    with pytest.raises(sc.CompileRefusal) as ei:
        sc.refuse_cost_era_mismatch([era2], contracts, "6A-era1")
    assert ei.value.code == "REFUSED_COMPILE_COST_ERA_MISMATCH"
    assert ei.value.exit_code == 41
    assert ei.value.detail["entry_era"] == "6A-era2"
    sc.refuse_cost_era_mismatch([era1], contracts, "6A-era1")  # no raise


# ------------------------------------------------------------ failure paths

def test_publication_failure_keeps_observed(tmp_path):
    fam = adapter_binding.find_family("NQ-F1")
    panel, calendar = pf.build_nq_panel()
    intents = [i for i in adapter_binding.collect_class_intents(fam, panel,
                                                                calendar)
               if i["identity_id"] == "FBNQ1-F1-CONT-UP-D0-S2"]
    res = compile_and_run(intents, tmp_path, "pubfail",
                          test_fault="fail_publication")
    assert res["exit_code"] == 3
    fs = res["final_status"]
    assert fs["status"] == "FAILED"
    assert fs["failure_code"] == "FAILED_PUBLICATION"
    trials = [r for r in res["ledger_rows"] if r["row_type"] == "TRIAL"]
    assert len(trials) == 1 and fs["observed_identity_count"] == 1  # kept
    q = tmp_path / "pubfail" / "runs" / "pubfail" / "PUBLICATION_QUARANTINE.json"
    assert q.is_file()
    assert not (tmp_path / "pubfail" / "runs" / "pubfail" /
                "published_summary.json").exists()


def test_refusals_fire_through_wiring_stack(tmp_path):
    fam = adapter_binding.find_family("NQ-F1")
    panel, calendar = pf.build_nq_panel()
    intents = [i for i in adapter_binding.collect_class_intents(fam, panel,
                                                                calendar)
               if i["identity_id"] == "FBNQ1-F1-CONT-UP-D0-S2"]
    r = compile_and_run(intents, tmp_path, "no_go",
                        gov_kwargs={"go_present": False})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_NO_GO_ARTIFACT"

    r = compile_and_run(intents, tmp_path, "bad_phrase",
                        gov_kwargs={"go_phrase": "GO - please run it"})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_GO_PHRASE_MISMATCH"

    r = compile_and_run(intents, tmp_path, "delegated",
                        gov_kwargs={"go_typed_by": "delegate-01"})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_GO_NOT_OWNER_TYPED"

    r = compile_and_run(intents, tmp_path, "reg_mismatch",
                        gov_kwargs={"registry_cycle_present": False})
    assert r["exit_code"] == 2
    assert r["final_status"]["refusal_code"] == "REFUSED_REGISTRY_MISMATCH"

    # input drift through the wiring stack (tamper the compiled fixture)
    r = compile_and_run(intents, tmp_path, "drift_run")
    assert r["exit_code"] == 0
    fixture = Path(r["compile"]["fixture"])
    lines = fixture.read_text().splitlines()
    parts = lines[1].split(",")
    parts[1] = "99.0"                       # entry bar open tampered
    lines[1] = ",".join(parts)
    fixture.write_text("\n".join(lines) + "\n")
    r2 = sc.invoke_runner(
        input_manifest=r["compile"]["input_manifest"],
        spec_packet=r["compile"]["spec_packet"],
        cost_manifest=r["compile"]["cost_manifest"],
        gov=sc.make_sandbox_authority(str(tmp_path / "drift_run" / "gov2")),
        ledger=str(tmp_path / "drift_run" / "l2.jsonl"),
        run_dir=str(tmp_path / "drift_run" / "runs2"),
        final_status_out=str(tmp_path / "drift_run" / "FS2.json"),
        run_label="d2", python=PY)
    assert r2["exit_code"] == 2
    assert r2["final_status"]["refusal_code"] == "REFUSED_INPUT_DRIFT"


def test_twin_mismatch_blocks_success(tmp_path):
    fam = adapter_binding.find_family("NQ-F1")
    panel, calendar = pf.build_nq_panel()
    intents = [i for i in adapter_binding.collect_class_intents(fam, panel,
                                                                calendar)
               if i["identity_id"] == "FBNQ1-F1-CONT-UP-D0-S2"]
    res = compile_and_run(intents, tmp_path, "twin_drift",
                          test_fault="force_twin_drift")
    assert res["exit_code"] == 3
    assert res["final_status"]["failure_code"] == "FAILED_TWIN_MISMATCH"
    recon = json.loads((tmp_path / "twin_drift" / "runs" / "twin_drift" /
                        "reconciliation_report.json").read_text())
    assert recon["match"] is False
