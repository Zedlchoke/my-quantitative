#!/usr/bin/env python
"""FOREX-FREE-V4 exec_driver_v4 tests (lane A8).

Light tests on SYNTHETIC fixtures only (no scored PnL anywhere): the scored
mode's launch-gate refusal, the dummy mode's sanitization/pairwise-ID
discipline, replay determinism and the recursive PnL-leak scan.  The real
six-arm dry-run over the staged snapshot is executed separately by the lane
(not in this suite); its sanitized evidence lives in
research/control/forex_free_v4_run/dry_run_v4.json.
"""
import json
import os
import shutil
import uuid
from datetime import date

import pytest

from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v4 import exec_driver_v4 as D

from tests.assets.forex_free_v4.test_family1 import (
    _build_fixture,
    _weekday_dates,
)
from tests.assets.forex_free_v4.test_family2 import (
    baseline_rows,
    rc_row,
    write_ledger,
)

FIXTURE_START = date(2024, 1, 1)  # Monday


def _make_fixture(tmp):
    """One synthetic snapshot dir serving BOTH families: 7 pairs of H1
    windows (family1 reads price_h1_dir, family2 reads h1_dir -- w3_freeze
    family_api_note), 8 macro vintage files (family1 financing) and a small
    evidenced announcement ledger (family2 events).  The trigger pairs carry
    the golden risk-off event at valid-day index 61."""
    days = _weekday_dates(FIXTURE_START, 100)
    data_paths, _reader = _build_fixture(
        tmp, days,
        spec_overrides={p: {"drops": {61: 3.0}}
                        for p in ("AUD/USD", "NZD/USD", "USD/CAD")})
    data_paths["h1_dir"] = data_paths["price_h1_dir"]
    rates = {a: 0.5 for a in ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ")}
    rows = baseline_rows(rates)
    # one evidenced hike per area inside the fixture window (delta != 0)
    for area in ("US", "EMU", "GB", "JP", "CH", "CA", "AU", "NZ"):
        rows.append(rc_row(area, "2024-02-15", rates[area],
                           rates[area] + 0.25, "2024-02-14T23:59:59Z"))
    ledger = os.path.join(tmp, "announcement_ledger.jsonl")
    write_ledger(ledger, rows)
    data_paths["announcement_ledger"] = ledger
    return data_paths


def _tmp_ledger(name):
    """A ledger path under the gitignored dryrun_tmp/ (the driver refuses
    dummy ledgers anywhere else); the caller cleans up."""
    d = os.path.join(D.ROOT, D.V4_CTL, D.DRYRUN_TMP_DIRNAME, name)
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------- scored mode
def test_scored_mode_refuses_without_launch_gates(tmp_path):
    """No W4 freeze / S0 / fresh GO artifacts => refusal BEFORE any compute;
    a refusal report is written and no scored ledger is created."""
    report = tmp_path / "refusal.json"
    ledger = tmp_path / "scored_ledger.jsonl"
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"freeze_token": D.W4_FREEZE_TOKEN}))
    with pytest.raises(SystemExit) as exc:
        D.run_scored({}, str(ledger), str(auth), str(report), root=str(tmp_path))
    assert exc.value.code == 2
    assert not ledger.exists()          # nothing booked, nothing published
    refusal = json.loads(report.read_text())
    assert refusal["refused"] is True
    failed = {k for k, v in refusal["gates"].items() if not v["ok"]}
    assert {"w4_freeze", "s0_launch_authorized", "owner_fresh_go"} <= failed
    assert refusal["gates"]["w4_freeze"]["ok"] is False


def test_scored_mode_refusal_lists_every_missing_gate(tmp_path):
    ok, gates = D.evaluate_launch_gates(root=str(tmp_path))
    assert ok is False
    for gate in ("w4_freeze", "s0_launch_authorized", "owner_fresh_go",
                 "budget", "s1_seal"):
        assert gate in gates and gates[gate]["ok"] is False


def test_dummy_ledger_outside_dryrun_tmp_refused(tmp_path):
    with pytest.raises(SystemExit, match="DUMMY_LEDGER_MUST_BE_TEMPORARY"):
        D.run_dummy({}, str(tmp_path / "elsewhere.jsonl"),
                    str(tmp_path / "report.json"), root=D.ROOT)


# ---------------------------------------------------------------- dummy mode
def test_dummy_six_arm_sanitized_pairwise_and_replay():
    """The full discipline on a synthetic snapshot: sanitize-clean records,
    pairwise-distinct trial identity, zero-position visibility, replay
    determinism with zero denominator delta."""
    import tempfile
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
            assert len(report1["arms"]) == 6
            assert report1["pairwise_distinct_ids"] is True
            assert report1["recursive_leak_scan"]["leaks_found"] == []

            record_ids = [a["record_id"] for a in report1["arms"]]
            trial_ids = [a["trial_id"] for a in report1["arms"]]
            assert len(set(record_ids)) == 6
            assert len(set(trial_ids)) == 6
            assert all(t.startswith(f"{D.CYCLE_ID}/") for t in trial_ids)
            assert len({a["arm_config_digest"] for a in report1["arms"]}) == 6

            lines = [l for l in open(ledger1, encoding="utf-8") if l.strip()]
            assert len(lines) == 6
            records = [json.loads(l) for l in lines]
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

            zero_arms = [a for a in report1["arms"]
                         if a["zero_positions"]["would_refuse_publication"]]
            for a in zero_arms:
                assert a["zero_positions"]["refusal_code"] == \
                    "STRESS_EMPTY_TRADE_SET"

            # replay: zero denominator delta, byte-identical records
            report2 = D.run_dummy(data_paths, ledger1,
                                  os.path.join(work, "report2.json"))
            assert all(a["observed_delta"] == 0 and a["published_now"] == 0
                       for a in report2["arms"])
            assert [a["record_sha256"] for a in report1["arms"]] == \
                [a["record_sha256"] for a in report2["arms"]]
            assert len([l for l in open(ledger1, encoding="utf-8")
                        if l.strip()]) == 6  # replay appended nothing
        finally:
            shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------- leak scan
def test_leak_scan_clean_on_kernel_sanitized_shape():
    from research.assets.forex_free_v3 import scored_runner as R
    rec = {
        "schema": "forex_free_v3_scored_record_v1", "record_id": "f:a:tier1.0",
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
        "usd_drift_diag": {"corr": 0.12, "n_days": 61, "evaluated": True},
        "stress": {"tier1.5": {"trades": 3, "total_pnl": 3.0}},
    }
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
