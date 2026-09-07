#!/usr/bin/env python
"""FOREX-FREE-V5 exec_driver_v5 tests (I1 lane).

Light tests on SYNTHETIC fixtures only (no scored PnL anywhere, no
real-data arm execution): the scored mode's launch-gate refusal, the dummy
mode's sanitization / pairwise-ID / margin-scaffold discipline on a
synthetic snapshot, replay determinism with zero denominator delta, and
the recursive PnL-leak scan.  The real-data dry-run over the staged
snapshot is NOT executed by the I1 lane (the lane report discloses this);
its harness shape is proven here on synthetic data exactly as the V4 lane
proved its own (tests/assets/forex_free_v4/test_exec_driver_v4.py).
"""
import json
import os
import shutil
import sys
import tempfile
import uuid
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v3 import accounting              # noqa: E402
from research.assets.forex_free_v5 import exec_driver_v5 as D     # noqa: E402

from tests.assets.forex_free_v5.test_family_a6p1 import (          # noqa: E402
    _three_gb_clocks,
    _story_closes,
    make_fixture,
)

FIXTURE_START = date(2024, 1, 1)  # Monday (documentation anchor)


def _make_fixture(tmp):
    """One synthetic snapshot serving all three arms: 70 NY weekdays of
    16:00-NY bars for the four evidenced pairs, the three GB story clocks
    (inside the snapshot) plus the deterministic 246-row filler structure,
    and the tiny evidenced ledger (financing kernel input)."""
    return make_fixture(tmp, story=_three_gb_clocks(),
                        closes=_story_closes(n=70))


def _tmp_ledger(name):
    """A ledger path under the gitignored-by-convention dryrun_tmp/ (the
    driver refuses dummy ledgers anywhere else); the caller cleans up."""
    d = os.path.join(D.ROOT, D.V5_CTL, D.DRYRUN_TMP_DIRNAME, name)
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------- scored
def test_scored_mode_refuses_without_launch_gates(tmp_path):
    """No W5 freeze / S0 / fresh GO artifacts => refusal BEFORE any
    compute; a refusal report is written and no scored ledger is
    created."""
    report = tmp_path / "refusal.json"
    ledger = tmp_path / "scored_ledger.jsonl"
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"freeze_token": D.W4_FREEZE_TOKEN}))
    with pytest.raises(SystemExit) as exc:
        D.run_scored({}, str(ledger), str(auth), str(report))
    assert exc.value.code == 2
    assert not ledger.exists()          # nothing booked, nothing published
    refusal = json.loads(report.read_text())
    assert refusal["refused"] is True
    failed = {k for k, v in refusal["gates"].items() if not v["ok"]}
    assert {"w4_freeze", "s0_launch_authorized", "owner_fresh_go",
            "budget", "s1_seal"} <= failed


def test_scored_mode_refusal_lists_every_missing_gate(tmp_path):
    ok, gates = D.evaluate_launch_gates()
    assert ok is False
    for gate in ("w4_freeze", "s0_launch_authorized", "owner_fresh_go",
                 "budget", "s1_seal"):
        assert gate in gates and gates[gate]["ok"] is False


def test_dummy_ledger_outside_dryrun_tmp_refused(tmp_path):
    with pytest.raises(SystemExit, match="DUMMY_LEDGER_MUST_BE_TEMPORARY"):
        D.run_dummy({}, str(tmp_path / "elsewhere.jsonl"),
                    str(tmp_path / "report.json"))


# ----------------------------------------------------------------- dummy
def test_dummy_three_arm_sanitized_pairwise_and_replay():
    """The full discipline on a synthetic snapshot: sanitize-clean records,
    pairwise-distinct trial identity, margin-to-fail scaffold, zero-
    position visibility, replay determinism with zero denominator delta."""
    with tempfile.TemporaryDirectory() as tmp:
        data_paths = _make_fixture(tmp)
        run_id = uuid.uuid4().hex[:8]
        work = _tmp_ledger(f"pytest_{run_id}")
        try:
            ledger1 = os.path.join(work, "ledger.jsonl")
            report1 = D.run_dummy(data_paths, ledger1,
                                  os.path.join(work, "report1.json"))
            assert report1["scored"] is False
            assert report1["real_pnl"] is False
            assert report1["published"] is False
            assert report1["code_freeze_sha"] == D.CODE_FREEZE_SHA_PLACEHOLDER
            assert len(report1["arms"]) == 3
            assert report1["pairwise_distinct_ids"] is True
            assert report1["recursive_leak_scan"]["leaks_found"] == []
            assert report1["data_verification"]["conditioning_clocks"][
                "total"] == 246

            record_ids = [a["record_id"] for a in report1["arms"]]
            trial_ids = [a["trial_id"] for a in report1["arms"]]
            digests = [a["arm_config_digest"] for a in report1["arms"]]
            assert len(set(record_ids)) == 3
            assert len(set(trial_ids)) == 3
            assert len(set(digests)) == 3
            assert all(t.startswith(f"{D.CYCLE_ID}/{D.FAMILY_ID}/")
                       for t in trial_ids)
            assert record_ids == [f"{D.FAMILY_ID}:{arm}:tier1.0"
                                  for arm in ("anchor", "neighbour", "control")]

            lines = [ln for ln in open(ledger1, encoding="utf-8") if ln.strip()]
            assert len(lines) == 3
            records = [json.loads(ln) for ln in lines]
            for rec in records:
                assert rec["dry_run"] is True
                assert rec["scored"] is False
                assert rec["real_pnl"] is False
                assert rec["published"] is False
                # every booked monetary column is the kernel placeholder
                for key in ("gross_price_pnl_usd", "price_only_pnl_usd",
                            "financing_adjustment_usd",
                            "financing_adjusted_pnl_usd"):
                    assert rec[key] == 0.0
                assert rec["base"]["expectancy"] == 0.0
                assert rec["base"]["pf"] is None
                assert rec["mdd_usd"] == 0.0
                assert rec["incremental_alpha"] is None
                assert rec["break_even_cost_bps"] is None
                # force-flat / zero-position visibility
                assert "n_force_flat_decisions" in rec["dryrun_structure"]
                assert "zero_positions" in rec["dryrun_structure"]
                # P-2 margin-to-fail scaffold: every gate carries threshold
                # + comparator + observed + signed margin (placeholders)
                scaffold = rec["dryrun_gate_scaffold"]
                assert scaffold["evaluated_on"] == \
                    "sanitized_placeholders_not_evidence"
                gate_names = {g["gate"] for g in scaffold["gates"]}
                assert {"financing_adjusted_expectancy_gt_0", "pf_ge_1.10",
                        "decisions_floor_40", "mdd_within_2500_usd",
                        "stress_tier2.0_primary_pf_ge_1.00",
                        "incremental_alpha_gt_0"} <= gate_names
                for g in scaffold["gates"]:
                    assert set(g) == {"gate", "threshold", "comparator",
                                      "observed", "margin"}

            # replay: zero denominator delta, byte-identical records
            report2 = D.run_dummy(data_paths, ledger1,
                                  os.path.join(work, "report2.json"))
            assert all(a["observed_delta"] == 0 and a["published_now"] == 0
                       for a in report2["arms"])
            assert [a["record_sha256"] for a in report1["arms"]] == \
                [a["record_sha256"] for a in report2["arms"]]
            assert len([ln for ln in open(ledger1, encoding="utf-8")
                        if ln.strip()]) == 3  # replay appended nothing

            # mechanism sanity evaluated on placeholders (not evidence)
            sanity = report1["mechanism_sanity"][D.FAMILY_ID]
            assert sanity["evaluated_on"] == \
                "sanitized_placeholders_not_evidence"
            # schedule invariant held on every arm
            assert report1["structural_invariant_violations"] == []
        finally:
            shutil.rmtree(work, ignore_errors=True)


def test_gate_scaffold_margin_signs_on_a_hand_record():
    """The scaffold's signed margin: positive in the pass direction, <= 0
    at the fail boundary, None when not evaluable."""
    rec = {
        "base": {"expectancy": 2.0, "pf": 1.25},
        "n_decisions": 50,
        "folds": [{"populated": True, "expectancy": 1.0},
                  {"populated": True, "expectancy": 0.5},
                  {"populated": False, "expectancy": 0.0}],
        "mdd_usd": 1200.0,
        "fold_positive_share": 0.4,
        "pair_concentration": {"USD/CAD": 0.35},
        "stress": {"tier2.0": {"total_pnl": 15.0, "pf": 1.05}},
        "dropout_scenarios": [{"survived": True}] * 7 + [{"survived": False}],
        "incremental_alpha": 0.4,
        "usd_drift_diag": {"evaluated": True, "corr": -0.12},
    }
    rows = {g["gate"]: g for g in D.gate_scaffold(rec)}
    assert rows["financing_adjusted_expectancy_gt_0"]["margin"] == \
        pytest.approx(2.0)
    assert rows["pf_ge_1.10"]["margin"] == pytest.approx(0.15)
    assert rows["decisions_floor_40"]["margin"] == pytest.approx(10.0)
    assert rows["mdd_within_2500_usd"]["margin"] == pytest.approx(1300.0)
    assert rows["pair_concentration_le_0.40"]["margin"] == pytest.approx(0.05)
    assert rows["stress_tier2.0_primary_pf_ge_1.00"]["margin"] == \
        pytest.approx(0.05)
    assert rows["dropout_survival_ge_6_of_8"]["margin"] == pytest.approx(1.0)
    assert rows["incremental_alpha_gt_0"]["margin"] == pytest.approx(0.4)
    assert rows["usd_drift_corr_abs_le_0.30"]["margin"] == \
        pytest.approx(0.18)
    # at the boundary the margin is exactly zero; unobservable -> None
    rec["base"]["pf"] = 1.10
    rows = {g["gate"]: g for g in D.gate_scaffold(rec)}
    assert rows["pf_ge_1.10"]["margin"] == 0.0
    rec["incremental_alpha"] = None
    rows = {g["gate"]: g for g in D.gate_scaffold(rec)}
    assert rows["incremental_alpha_gt_0"]["margin"] is None


# ------------------------------------------------------------- leak scan
def test_leak_scan_clean_on_kernel_sanitized_shape():
    rec = {
        "schema": "forex_free_v3_scored_record_v1",
        "record_id": "FXFV5-A6-P1:anchor:tier1.0",
        "cost_tier": 1.0, "n_trades": 3, "gross_price_pnl_usd": 12.5,
        "price_only_pnl_usd": 4.0, "financing_adjustment_usd": -0.5,
        "financing_adjusted_pnl_usd": 3.5, "dry_run": False,
        "real_pnl": True, "published": False, "scored": False,
        "base": {"trades": 3, "total_pnl": 3.5, "expectancy": 1.166,
                 "pf": 2.0, "gross_positive": 4.0},
        "base_price_only": {"trades": 3, "total_pnl": 4.0,
                            "expectancy": 1.333, "pf": 2.5,
                            "gross_positive": 4.5},
        "folds": [{"fold": 0, "trades": 3, "total_pnl": 3.5,
                   "expectancy": 1.166, "pf": 2.0, "gross_positive": 4.0,
                   "populated": False}],
        "mdd_usd": 1.25, "fold_positive_share": 1.0,
        "pair_concentration": {"AUD/USD": 1.0},
        "drop_one_expectancy": {"AUD/USD": 1.2},
        "dropout_scenarios": [{"scenario": "drop_pair:AUD/USD",
                               "expectancy": 1.2, "survived": True}],
        "break_even_cost_bps": 0.9, "incremental_alpha": 0.1,
        "incremental_alpha_definition": "per_trade_expectancy_difference_v1",
        "benchmark_treatment": None,
        "usd_drift_diag": {"corr": 0.12, "n_days": 61, "evaluated": True},
        "stress": {"tier1.5": {"trades": 3, "total_pnl": 3.0}},
        "dry_run": True, "real_pnl": False,
        "trial_id": "FOREX-FREE-V5/FXFV5-A6-P1/anchor",
        "arm_config_digest": "0" * 64,
        "dryrun_structure": {
            "cycle_id_in_record": D.CYCLE_ID,
            "structure_family": D.FAMILY_ID, "structure_arm": "anchor",
            "n_decisions_returned": 3, "n_financing_events": 3,
            "n_force_flat_decisions": 0,
            "clock_counters": {"published_clocks": 246,
                               "arm_candidates": 246, "sham_dropped": 0,
                               "s0_cap_excluded": 0, "warmup_void": 0,
                               "exact_zero_direction": 0,
                               "fold_window_voided": 0,
                               "missing_decision_bar": 0, "missing_f": 0,
                               "missing_x": 0, "fill_lag_refused": 0,
                               "governor_blocked_open": 0,
                               "governor_blocked_same_day": 0,
                               "skipped_no_predecessor": 0,
                               "fold_boundary_no_entry": 0},
            "economy_clock_counts": {"GB": 88, "CA": 105, "AU": 23,
                                     "NZ": 30},
            "skipped_reason_counts": {"f_missing_void": 243},
            "schedule_totals": {"GBP/USD": {
                "candidates": 88, "round_trips": 3, "decision_bars": 70,
                "no_refresh_ignored": 0, "no_decision_bar_available": 0,
                "f_missing_void": 85, "x_missing_void": 0,
                "s0_cap_excluded": 0, "warmup_void": 0,
                "exact_zero_direction": 0, "fill_lag_exceeds_4_days": 0,
                "fold_window_voided": 0, "fold_boundary_no_entry": 0,
                "sham_dropped": 0}},
            "frozen_constants": {
                "trailing_return_sum_ny_days": 10,
                "sham_shift_calendar_days": 7,
                "staleness_mode": None,
                "s0_cap_entry_utc": "2025-07-25T00:00:00+00:00",
                "notional_usd_unit": 10000.0,
                "clocks_pair_map": {"GB": "GBP/USD", "CA": "USD/CAD",
                                    "AU": "AUD/USD", "NZ": "NZD/USD"}},
            "zero_positions": {"n_trades_kept": 3,
                               "would_refuse_publication": False,
                               "refusal_code": None},
        },
        "dryrun_gate_check": {"evaluated_on":
                              "sanitized_placeholders_not_evidence",
                              "gate_pass": False, "gate_reasons": []},
        "dryrun_gate_scaffold": {
            "evaluated_on": "sanitized_placeholders_not_evidence",
            "gates": [{"gate": "pf_ge_1.10", "threshold": 1.1,
                       "comparator": ">=", "observed": None,
                       "margin": None}]},
    }
    from research.assets.forex_free_v3 import scored_runner as R
    sanitized = R.dry_run_sanitized(dict(rec))
    findings, scanned = D.recursive_leak_scan(sanitized)
    assert findings == []
    assert scanned > 0


def test_leak_scan_catches_seeded_outcomes():
    rec = {"schema": "x", "record_id": "r", "scored": False,
           "real_pnl": False, "published": False, "dry_run": True,
           "base": {"trades": 1, "total_pnl": 0.0, "expectancy": 0.0,
                    "pf": None, "gross_positive": 0.0},
           "mdd_usd": 0.0}
    findings, _ = D.recursive_leak_scan(rec)
    assert findings == []
    seeded = json.loads(json.dumps(rec))
    seeded["base"]["total_pnl"] = 123.45          # a PnL that survived
    findings, _ = D.recursive_leak_scan(seeded)
    assert any("total_pnl" in f for f in findings)
    seeded2 = json.loads(json.dumps(rec))
    seeded2["mystery_outcome_field"] = 99.0       # key outside allowlist
    findings, _ = D.recursive_leak_scan(seeded2)
    assert any("mystery_outcome_field" in f for f in findings)
    seeded3 = json.loads(json.dumps(rec))
    seeded3["scored"] = True                      # broken flag
    findings, _ = D.recursive_leak_scan(seeded3)
    assert any("$.scored" in f for f in findings)


def test_verify_staged_data_pins_the_authorities():
    """The real staged authorities verify fail-closed (read-only): 153-file
    snapshot digests, the 246-clock conditioning authority, and the pinned
    V5-extension ledger sha."""
    evidence = D.verify_staged_data()
    assert evidence["price_snapshot"]["mismatches"] == 0
    assert evidence["conditioning_clocks"]["total"] == 246
    assert evidence["conditioning_clocks"]["per_economy"] == {
        "GB": 88, "CA": 105, "AU": 23, "NZ": 30}
    assert evidence["announcement_ledger"]["match"] is True
    assert evidence["announcement_ledger"]["rows"] == 250
    assert evidence["announcement_ledger"]["sha256"] == \
        D.EXTENSION_LEDGER_SHA256


def test_proposal_packet_registration_is_pinned():
    """The materialized proposal packet must match its pinned sha256 (the
    driver fails closed on any drift)."""
    spec = D.FAMILY_MODULES[D.FAMILY_ID]
    path = os.path.join(D.ROOT, spec["proposal"])
    assert os.path.exists(path)
    assert D.sha256_file(path) == spec["proposal_sha256"]
