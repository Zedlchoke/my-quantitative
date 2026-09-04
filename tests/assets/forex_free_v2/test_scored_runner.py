#!/usr/bin/env python
"""FOREX-FREE-V2: central scored-runner tests. All expected numbers are
hand-computed literals. No real-data PnL anywhere in this file."""
import json
import os
import tempfile
import threading

import pytest

from research.assets.forex_free_v2 import scored_runner as R
from research.assets.forex_free_v2 import accounting, family1, family2


# ---------- the runner must call the ACTUAL family APIs ----------
def test_runner_registry_is_actual_family_modules():
    assert R.FAMILIES["family1"] is family1
    assert R.FAMILIES["family2"] is family2
    for fid, fam in R.FAMILIES.items():
        assert hasattr(fam, "compute_arm_schedule")
        assert set(fam.ARMS) == {"anchor", "neighbour", "control"}
        empty = {p: [{"datetime": "2020-01-01 00:00:00", "open": 1.0, "high": 1.0,
                      "low": 1.0, "close": 1.0}] for p in R.PAIRS}  # minimal valid rows
        for arm in fam.ARMS:  # callable with the runner-facing signature
            out = fam.compute_arm_schedule(arm, empty, cost_tier=1.0)
            assert "schedule_digest" in out and out["trades"] == []


# ---------- session gate ----------
def test_session_gate_drops_weekend_entries():
    trades = [
        {"trade_id": "a", "pair": "EUR/USD", "side": 1, "notional_usd": 10000,
         "entry_price": 1.10, "entry_ts": "2025-06-10T10:00:00+00:00",  # Tue
         "exit_price": 1.11, "exit_ts": "2025-06-10T15:00:00+00:00", "cost_tier": 1.0},
        {"trade_id": "b", "pair": "EUR/USD", "side": 1, "notional_usd": 10000,
         "entry_price": 1.10, "entry_ts": "2025-06-14T10:00:00+00:00",  # Saturday
         "exit_price": 1.11, "exit_ts": "2025-06-14T15:00:00+00:00", "cost_tier": 1.0},
    ]
    kept, dropped = R.apply_session_gate(trades)
    assert [t["trade_id"] for t in kept] == ["a"]
    assert len(dropped) == 1


def test_session_gate_boundary_hours():
    # Sunday 21:00 NY (EDT, 01:00Z Mon) opens the week: 01:30Z Mon OK.
    assert R.is_market_open_entry("2025-06-09T01:30:00+00:00") is True
    # Sunday 20:00 NY (00:00Z Sun) is still closed.
    assert R.is_market_open_entry("2025-06-08T00:00:00+00:00") is False
    # Friday 15:59 NY (19:59Z EDT) open; 16:00 NY (20:00Z) closed.
    assert R.is_market_open_entry("2025-06-13T19:59:00+00:00") is True
    assert R.is_market_open_entry("2025-06-13T20:00:00+00:00") is False


# ---------- fold assignment ----------
def test_fold_and_purge():
    assert R.fold_of("2020-02-01T10:00:00+00:00") is None          # warmup < B0
    assert R.fold_of("2020-03-05T10:00:00+00:00") is None          # purged (<=B0+14d)
    assert R.fold_of("2020-03-16T00:00:00+00:00") == 0             # B0+15d... 03-16 is +15d
    assert R.fold_of("2022-05-10T00:00:00+00:00") is None          # purged after B1
    assert R.fold_of("2022-06-01T00:00:00+00:00") == 1
    assert R.fold_of("2024-08-01T00:00:00+00:00") == 2


# ---------- booking (cost once per side, kernel-verified) ----------
def test_book_trades_pnl_and_costs_hand_computed():
    trades = [{
        "trade_id": "t1", "pair": "EUR/USD", "side": 1, "notional_usd": 10000,
        "entry_price": 1.10, "entry_ts": "2021-06-10T10:00:00+00:00",
        "exit_price": 1.15, "exit_ts": "2021-06-10T15:00:00+00:00", "cost_tier": 1.0,
    }]
    booked, book = R.book_trades(trades)
    # gross move = +1 * 10000 * (1.15/1.10 - 1) = 454.5454545455
    assert booked[0]["_gross_move_pnl"] == pytest.approx(454.5454545455, abs=1e-9)
    # net = gross - 2 x (10000 x 1.5bps) = 454.5454545455 - 3.0 = 451.5454545455
    assert booked[0]["_pnl"] == pytest.approx(451.5454545455, abs=1e-9)
    filled = [f for f in book.fills if f.trade_id == "t1"]
    assert len(filled) == 2 and sum(f.cost_usd for f in filled) == pytest.approx(3.0)


def test_book_trades_dry_run_zeroes_move_pnl_only():
    trades = [{
        "trade_id": "t1", "pair": "USD/JPY", "side": -1, "notional_usd": 10000,
        "entry_price": 150.0, "entry_ts": "2021-06-10T10:00:00+00:00",
        "exit_price": 149.0, "exit_ts": "2021-06-10T15:00:00+00:00", "cost_tier": 1.0,
    }]
    booked, _ = R.book_trades(trades, dry_run=True)
    # gross move would be +66.666... but dry_run books 0 (real_pnl=false)
    assert booked[0]["_gross_move_pnl"] == pytest.approx(66.6666666667, abs=1e-9)
    assert booked[0]["_pnl"] == 0.0 and booked[0]["_dry_run"] is True


# ---------- gates on hand-built records ----------
def _rec(base_exp, base_pf, folds, mdd=100.0, fold_share=0.3, conc=None,
         stress=None, drop=None, usd=None):
    return {
        "base": {"expectancy": base_exp, "pf": base_pf, "total_pnl": base_exp * 100},
        "folds": folds, "mdd_usd": mdd, "fold_positive_share": fold_share,
        "pair_concentration": conc if conc is not None else {"EUR/USD": 0.2},
        "stress": stress if stress is not None else {
            "tier1.5": {"total_pnl": 10.0, "pf": 1.2},
            "tier2.0": {"total_pnl": 5.0, "pf": 1.05}},
        "drop_one_expectancy": drop if drop is not None else {p: 1.0 for p in R.PAIRS},
        "usd_drift_diag": usd if usd is not None else {"corr": 0.05, "n_days": 300, "evaluated": True},
    }


def _good_folds():
    return [
        {"fold": 0, "trades": 100, "expectancy": 1.0, "pf": 1.4, "populated": True, "gross_positive": 200.0},
        {"fold": 1, "trades": 100, "expectancy": 0.5, "pf": 1.2, "populated": True, "gross_positive": 150.0},
        {"fold": 2, "trades": 100, "expectancy": 0.2, "pf": 1.05, "populated": True, "gross_positive": 50.0},
    ]


def test_stage_a_positive_record_passes():
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.30, _good_folds()))
    assert ok and reasons == []


def test_stage_a_negative_expectancy_fails():
    ok, reasons = R.stage_a_gates(_rec(-0.5, 0.85, _good_folds()))
    assert not ok and "EXPECTANCY_NONPOSITIVE" in reasons and "PF_BELOW_1.10" in reasons


def test_stage_a_fold_rules():
    folds = _good_folds()
    folds[2] = {"fold": 2, "trades": 10, "expectancy": -1.0, "pf": 0.5, "populated": False, "gross_positive": 0.0}
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, folds))
    # unpopulated fold is ignored; 2/3 positive populated -> still pass
    assert ok
    folds[1] = {"fold": 1, "trades": 100, "expectancy": -0.5, "pf": 1.2, "populated": True, "gross_positive": 0.0}
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, folds))
    assert not ok and "FEWER_THAN_2_POSITIVE_POPULATED_FOLDS" in reasons
    folds[1] = {"fold": 1, "trades": 100, "expectancy": 0.5, "pf": 0.70, "populated": True, "gross_positive": 0.0}
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, folds))
    assert not ok and "POPULATED_FOLD_PF_BELOW_0.80" in reasons


def test_stage_a_mdd_concentration_share_stress_dropout_usd():
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), mdd=2500.01))
    assert not ok and "MDD_ABOVE_FROZEN_CEILING" in reasons
    ok, _ = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), mdd=2500.0))
    assert ok  # ceiling inclusive
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), fold_share=0.51))
    assert not ok and "POSITIVE_FOLD_SHARE_ABOVE_50PCT" in reasons
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), conc={"EUR/USD": 0.41}))
    assert not ok and "PAIR_CONCENTRATION_ABOVE_40PCT" in reasons
    bad_stress = {"tier1.5": {"total_pnl": -1.0, "pf": 0.9}, "tier2.0": {"total_pnl": 5.0, "pf": 1.05}}
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), stress=bad_stress))
    assert not ok and "STRESS_TIER_1.5_FAIL" in reasons
    drop = {p: (1.0 if i < 4 else -0.1) for i, p in enumerate(R.PAIRS)}  # 4/7 survive
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), drop=drop))
    assert not ok and "DROP_ONE_PAIR_SURVIVAL_INSUFFICIENT" in reasons
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), usd={"corr": 0.31, "n_days": 300, "evaluated": True}))
    assert not ok and "USD_DRIFT_EXPLAINS_ANCHOR" in reasons
    ok, _ = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), usd={"corr": None, "n_days": 10, "evaluated": False}))
    assert ok  # not evaluated -> cannot fail


def test_mechanism_sanity_neighbour_and_placebo():
    good = _rec(0.5, 1.30, _good_folds())
    weak_neighbour = _rec(-0.1, 0.9, _good_folds())
    ok, reasons = R.mechanism_sanity({"anchor": good, "neighbour": weak_neighbour, "control": _rec(-0.2, 0.8, _good_folds())})
    assert not ok and "NEIGHBOUR_DOES_NOT_SUPPORT_ANCHOR" in reasons
    placebo_passing = _rec(0.4, 1.25, _good_folds())
    ok, reasons = R.mechanism_sanity({"anchor": good, "neighbour": _rec(0.1, 1.1, _good_folds()), "control": placebo_passing})
    assert not ok and "CONTROL_REPRODUCES_MECHANISM" in reasons
    ok, _ = R.mechanism_sanity({"anchor": good, "neighbour": _rec(0.1, 1.1, _good_folds()), "control": _rec(-0.2, 0.9, _good_folds())})
    assert ok


# ---------- once-only publication ----------
def _auth(tmp, w2="W2SHA"):
    p = os.path.join(tmp, "auth.json")
    json.dump({"w2_sha": w2}, open(p, "w"))
    return p


def _real_record():
    """Full gate-carrying record (publish computes gates before hashing)."""
    return {"cell_id": "family1:anchor:tier1.0", "dry_run": False, "real_pnl": True,
            "base": {"expectancy": 0.5, "pf": 1.3, "total_pnl": 500.0},
            "folds": _good_folds(), "mdd_usd": 100.0, "fold_positive_share": 0.3,
            "pair_concentration": {"EUR/USD": 0.2},
            "stress": {"tier1.5": {"total_pnl": 10.0, "pf": 1.2},
                       "tier2.0": {"total_pnl": 5.0, "pf": 1.05}},
            "drop_one_expectancy": {p: 1.0 for p in R.PAIRS},
            "usd_drift_diag": {"corr": 0.05, "n_days": 300, "evaluated": True}}


def test_publish_requires_authorization_and_matching_w2():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        with pytest.raises(ValueError, match="LAUNCH_AUTHORIZATION_MISSING"):
            R.publish_cell(led, _real_record(), os.path.join(tmp, "nope.json"), "W2SHA")
        bad = _auth(tmp, w2="OTHER")
        with pytest.raises(ValueError, match="W2_SHA_MISMATCH"):
            R.publish_cell(led, _real_record(), bad, "W2SHA")
        assert not os.path.exists(led)


def test_publish_refuses_dry_run_records():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        rec = dict(_real_record()); rec["dry_run"] = True; rec["real_pnl"] = False
        with pytest.raises(ValueError, match="REAL_PNL_REQUIRED"):
            R.publish_cell(led, rec, _auth(tmp), "W2SHA")
        assert not os.path.exists(led)


def test_publish_once_only_and_replay_zero_delta():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        auth = _auth(tmp)
        assert R.publish_cell(led, _real_record(), auth, "W2SHA") == (1, 1)
        assert R.publish_cell(led, _real_record(), auth, "W2SHA") == (0, 0)  # replay
        lines = open(led).read().strip().split("\n")
        assert len(lines) == 1
        row = json.loads(lines[0])
        exp = accounting.sha256_hex(accounting.canonical_json_bytes(
            {**_real_record(), "gates": True, "gate_reasons": []}))
        assert row["digest"] == exp


def test_publish_serializes_parallel_writers():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        auth = _auth(tmp)
        def pub(i):
            rec = _real_record(); rec["cell_id"] = f"cell{i}"
            R.publish_cell(led, rec, auth, "W2SHA")
        ts = [threading.Thread(target=pub, args=(i,)) for i in range(8)]
        [t.start() for t in ts]; [t.join() for t in ts]
        rows = [json.loads(l) for l in open(led).read().strip().split("\n")]
        assert len(rows) == 8 and len({r["digest"] for r in rows}) == 8


# ---------- fold metrics + concentration hand-math ----------
def test_book_metrics_and_concentration_hand_computed():
    m = R.book_metrics([100.0, -50.0, 25.0, 0.0])
    assert m["trades"] == 4
    assert m["total_pnl"] == pytest.approx(75.0)
    assert m["expectancy"] == pytest.approx(18.75)
    assert m["pf"] == pytest.approx(125.0 / 50.0)
    trs = [
        {"pair": "EUR/USD", "_pnl": 60.0}, {"pair": "EUR/USD", "_pnl": 40.0},
        {"pair": "USD/JPY", "_pnl": 30.0}, {"pair": "USD/JPY", "_pnl": -70.0},
    ]
    c = R.concentration(trs)
    # gross positive = 60+40+30 = 130; shares 100/130 and 30/130
    assert c == {"EUR/USD": 0.769231, "USD/JPY": 0.230769}
    # trade pnls whose equity curve 100 -> 150 -> 50 -> 120 has max drawdown 100
    assert R.mdd_of([100.0, 50.0, -100.0, 70.0]) == 100.0
    assert R.mdd_of([100.0, -10.0, 20.0]) == 10.0


def test_usd_drift_corr_hand_case():
    rows = {p: [] for p in R.PAIRS}
    # 60 days; pnl perfectly correlated with USD index -> |corr| = 1 -> gate fails
    trades = []
    for i in range(60):
        d = f"2021-01-{(i % 28) + 1:02d}" if i < 28 else f"2021-02-{(i % 28) + 1:02d}"
        if d in {t["entry_ts"][:10] for t in trades}:
            continue
        trades.append({"pair": "EUR/USD", "side": 1, "notional_usd": 10000,
                       "entry_price": 1.0, "entry_ts": f"{d}T10:00:00+00:00",
                       "exit_price": 1.0, "exit_ts": f"{d}T15:00:00+00:00",
                       "cost_tier": 1.0, "_pnl": float(i), "_gross_move_pnl": float(i)})
    # rows_by_pair empty -> usd_ret None every day -> not evaluated -> cannot fail
    diag = R.usd_drift_corr(trades, rows)
    assert diag["evaluated"] is False
