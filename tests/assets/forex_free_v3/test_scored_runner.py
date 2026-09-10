#!/usr/bin/env python
"""FOREX-FREE-V3: central scored-runner tests. All expected numbers are
hand-computed literals. No real-data PnL anywhere in this file: every
fixture below is synthetic, per Phase I rules."""
import copy
import json
import os
import tempfile
import threading
import time

import pytest

from research.assets.forex_free_v3 import scored_runner as R
from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3.macro_reader import MacroDataBlocked, PolicyRateReader

W3 = "FOREX_FREE_V3_W3"


# ---------- fixtures: a dummy family satisfying the documented contract ----------
def _dec(did, pair, side, dec_ts, entry_ts, entry_px, exit_ts, exit_px,
         force_flat=False, notional=10000):
    return {"decision_id": did, "pair": pair, "side": side,
            "decision_ts": dec_ts, "notional_usd": notional,
            "entry_bar_ts": entry_ts, "entry_price": entry_px,
            "exit_bar_ts": exit_ts, "exit_price": exit_px,
            "force_flat": force_flat}


FIXTURE_DECISIONS = [
    # fold 0: EUR/USD long, entry Thu 2021-06-10, exit Mon 2021-06-14
    _dec("d1", "EUR/USD", 1, "2021-06-09T20:00:00+00:00",
         "2021-06-10T20:00:00+00:00", 1.10, "2021-06-14T20:00:00+00:00", 1.11),
    # fold 2: USD/JPY short, entry Wed 2024-08-07, exit Thu 2024-08-08
    _dec("d2", "USD/JPY", -1, "2024-08-06T20:00:00+00:00",
         "2024-08-07T20:00:00+00:00", 150.0, "2024-08-08T20:00:00+00:00", 149.0),
    # fold 0: force-flattened at the 2022-05-01 boundary (last NY bar: Fri 04-29)
    _dec("d3", "EUR/USD", 1, "2022-04-27T20:00:00+00:00",
         "2022-04-28T20:00:00+00:00", 1.08, "2022-04-29T20:00:00+00:00", 1.085,
         force_flat=True),
]
FIXTURE_FINANCING = [
    {"decision_id": "d1", "financing_adjustment_usd": 2.0, "formula": "V3_FROZEN_POLICY_RATE_CARRY"},
    {"decision_id": "d2", "financing_adjustment_usd": 1.0, "formula": "V3_FROZEN_POLICY_RATE_CARRY"},
    {"decision_id": "d3", "financing_adjustment_usd": -0.5, "formula": "V3_FROZEN_POLICY_RATE_CARRY"},
]
# The family's frozen benchmark treatment book (required in scored mode):
# one EUR/USD round trip, financing-adjusted expectancy 451.5454545455+2.0.
BENCH_DECISIONS = [
    _dec("b1", "EUR/USD", 1, "2021-06-09T20:00:00+00:00",
         "2021-06-10T20:00:00+00:00", 1.10, "2021-06-11T20:00:00+00:00", 1.15),
]
BENCH_FINANCING = [
    {"decision_id": "b1", "financing_adjustment_usd": 2.0,
     "formula": "V3_FROZEN_POLICY_RATE_CARRY"},
]


class DummyFamily:
    ARMS = ("anchor", "neighbour", "control", "benchmark_treatment")

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        if arm == "benchmark_treatment":
            return {"decisions": copy.deepcopy(BENCH_DECISIONS),
                    "financing_events": copy.deepcopy(BENCH_FINANCING),
                    "meta": {"decision_clock": "daily",
                             "proposal_id": "DUMMY-BENCH"}}
        return {"decisions": copy.deepcopy(FIXTURE_DECISIONS),
                "financing_events": copy.deepcopy(FIXTURE_FINANCING),
                "meta": {"proposal_id": "DUMMY", "decision_clock": "daily",
                         "pair_universe": list(R.PAIRS),
                         "alpha_definition": R.ALPHA_EXPECTANCY_DIFFERENCE,
                         "usd_index_daily_returns": {},
                         "fill_delay_events": {}}}


class NoBenchmarkFamily(DummyFamily):
    """A family that has NOT implemented the required benchmark arm."""

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        if arm == "benchmark_treatment":
            raise ValueError("unknown arm 'benchmark_treatment'")
        return super().run_arm(arm, data_paths, macro_reader, freeze_token)


def _h1_file(tmp, pair, rows):
    """Canonical td_loader-schema H1 window file; rows are
    (utc 'YYYY-MM-DD HH:MM:SS', open, high, low, close)."""
    tag = pair.replace("/", "")
    payload = {"meta": {"symbol": pair, "interval": "1h"},
               "values": [{"datetime": ts, "open": o, "high": h,
                           "low": lo, "close": c} for ts, o, h, lo, c in rows]}
    with open(os.path.join(tmp, f"{tag}_1h_fix.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return os.path.join(tmp, f"{tag}_1h_fix.json")


def _scored_price_dir():
    """Minimal 2-pair H1 snapshot covering the fixture trades' instants
    (EDT weeks: 16:00 New York == 20:00Z).  Index days stay far below the
    60-day floor, so the USD diagnostic is recorded but cannot fail."""
    tmp = tempfile.mkdtemp(prefix="runner_prices_")
    _h1_file(tmp, "EUR/USD", [
        ("2021-06-09 20:00:00", 1.100, 1.101, 1.099, 1.1005),
        ("2021-06-10 20:00:00", 1.100, 1.101, 1.099, 1.1010),
        ("2022-04-27 20:00:00", 1.080, 1.081, 1.079, 1.0805),
        ("2022-04-28 20:00:00", 1.080, 1.081, 1.079, 1.0810)])
    _h1_file(tmp, "USD/JPY", [
        ("2024-08-06 20:00:00", 150.0, 150.1, 149.9, 150.05),
        ("2024-08-07 20:00:00", 150.0, 150.1, 149.9, 150.10)])
    return tmp


class SlowFamily:
    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        time.sleep(0.5)
        return {"decisions": [], "financing_events": [], "meta": {}}


@pytest.fixture(autouse=True)
def _registry():
    saved = dict(R.FAMILIES)
    R.register_family("family1", DummyFamily())
    yield
    R.FAMILIES.clear()
    R.FAMILIES.update(saved)


# ---------- the runner must dispatch to the registered family API ----------
def test_runner_registry_contract():
    fam = R.FAMILIES["family1"]
    assert fam is not None and hasattr(fam, "run_arm")
    out = fam.run_arm("anchor", {}, None, None)
    assert set(out) == {"decisions", "financing_events", "meta"}
    with pytest.raises(ValueError):
        R.register_family("bad", object())  # no run_arm -> refused
    with pytest.raises(KeyError):
        R.compute_cell("unknown_family", "anchor", {})


# ---------- session gate (inherited) ----------
def test_session_gate_drops_weekend_fill_bars():
    trades = [
        _dec("a", "EUR/USD", 1, "2025-06-10T20:00:00+00:00",
             "2025-06-11T20:00:00+00:00", 1.10, "2025-06-12T20:00:00+00:00", 1.11),
        _dec("b", "EUR/USD", 1, "2025-06-13T20:00:00+00:00",
             "2025-06-14T10:00:00+00:00", 1.10, "2025-06-14T15:00:00+00:00", 1.11),
    ]
    trades[1]["entry_bar_ts"] = "2025-06-14T10:00:00+00:00"  # Saturday fill
    kept, dropped = R.apply_session_gate(trades)
    assert [t["decision_id"] for t in kept] == ["a"]
    assert len(dropped) == 1


def test_session_gate_boundary_hours():
    # Sunday 21:00 NY (EDT, 01:00Z Mon) opens the week: 01:30Z Mon OK.
    assert R.is_market_open_entry("2025-06-09T01:30:00+00:00") is True
    # Sunday 20:00 NY (00:00Z Sun) is still closed.
    assert R.is_market_open_entry("2025-06-08T00:00:00+00:00") is False
    # Friday 15:59 NY (19:59Z EDT) open; 16:00 NY (20:00Z) closed.
    assert R.is_market_open_entry("2025-06-13T19:59:00+00:00") is True
    assert R.is_market_open_entry("2025-06-13T20:00:00+00:00") is False


# ---------- fold assignment (inherited) ----------
def test_fold_and_purge():
    assert R.fold_of("2020-02-01T10:00:00+00:00") is None          # warmup < B0
    assert R.fold_of("2020-03-05T10:00:00+00:00") is None          # purged (<=B0+14d)
    assert R.fold_of("2020-03-16T00:00:00+00:00") == 0             # +15d
    assert R.fold_of("2022-05-10T00:00:00+00:00") is None          # purged after B1
    assert R.fold_of("2022-06-01T00:00:00+00:00") == 1
    assert R.fold_of("2024-08-01T00:00:00+00:00") == 2


# ---------- decision clock: one-event-lag + 16:00-NY daily bar ----------
def test_one_event_lag_and_clock_rejections():
    ok = [_dec("x", "EUR/USD", 1, "2025-06-10T20:00:00+00:00",
               "2025-06-11T20:00:00+00:00", 1.10, "2025-06-12T20:00:00+00:00", 1.11)]
    fin = [{"decision_id": "x", "financing_adjustment_usd": 0.0, "formula": "F"}]
    trades, adj, formula = R.validate_decisions(ok, fin)
    assert formula == "F" and adj == {"x": 0.0}
    # Friday decision fills Monday 16:00-NY (3-day weekend lag): OK.
    friday = [_dec("f", "EUR/USD", 1, "2025-06-13T20:00:00+00:00",
                   "2025-06-16T20:00:00+00:00", 1.10, "2025-06-17T20:00:00+00:00", 1.11)]
    R.validate_decisions(friday, [{"decision_id": "f", "financing_adjustment_usd": 0.0,
                                   "formula": "F"}])
    # Same-bar fill: rejected.
    same_bar = [_dec("y", "EUR/USD", 1, "2025-06-10T20:00:00+00:00",
                     "2025-06-10T20:00:00+00:00", 1.10, "2025-06-11T20:00:00+00:00", 1.11)]
    with pytest.raises(R.DecisionRuleError, match="ONE_EVENT_LAG_VIOLATION"):
        R.validate_decisions(same_bar, [])
    # Six-day lag is not the next session bar: rejected.
    late = [_dec("z", "EUR/USD", 1, "2025-06-10T20:00:00+00:00",
                 "2025-06-16T20:00:00+00:00", 1.10, "2025-06-17T20:00:00+00:00", 1.11)]
    with pytest.raises(R.DecisionRuleError, match="ONE_EVENT_LAG_VIOLATION"):
        R.validate_decisions(late, [])
    # Decision not at a completed 16:00-NY bar: rejected.
    off_clock = [_dec("w", "EUR/USD", 1, "2025-06-10T19:00:00+00:00",
                      "2025-06-11T20:00:00+00:00", 1.10, "2025-06-12T20:00:00+00:00", 1.11)]
    with pytest.raises(R.DecisionRuleError, match="DECISION_CLOCK_VIOLATION"):
        R.validate_decisions(off_clock, [])
    # Fill bar not a 16:00-NY bar: rejected.
    bad_fill = [_dec("v", "EUR/USD", 1, "2025-06-10T20:00:00+00:00",
                     "2025-06-11T21:00:00+00:00", 1.10, "2025-06-12T20:00:00+00:00", 1.11)]
    with pytest.raises(R.DecisionRuleError, match="DECISION_CLOCK_VIOLATION"):
        R.validate_decisions(bad_fill, [])
    # Financing must be carried by the family, never invented by the runner.
    with pytest.raises(R.DecisionRuleError, match="MISSING_FINANCING_EVENT"):
        R.validate_decisions(ok, [])
    with pytest.raises(R.DecisionRuleError, match="FINANCING_EVENT_UNMATCHED"):
        R.validate_decisions(ok, [{"decision_id": "ghost", "financing_adjustment_usd": 0.0,
                                   "formula": "F"}])
    with pytest.raises(R.DecisionRuleError, match="MISSING_FINANCING_FORMULA"):
        R.validate_decisions(ok, [{"decision_id": "x", "financing_adjustment_usd": 0.0}])


# ---------- fold boundaries force-flat ----------
def test_fold_force_flat_attribution():
    # A trade spanning the internal 2022-05-01 boundary is refused.
    spanning = [_dec("s", "EUR/USD", 1, "2022-04-26T20:00:00+00:00",
                     "2022-04-28T20:00:00+00:00", 1.08, "2022-05-03T20:00:00+00:00", 1.09)]
    with pytest.raises(R.DecisionRuleError, match="FOLD_FORCE_FLAT_VIOLATION"):
        R.validate_decisions(spanning, [])
    # A force-flat trade closed at the boundary's last NY bar is attributed cleanly.
    fin = [{"decision_id": "d3", "financing_adjustment_usd": -0.5, "formula": "F"}]
    trades, _, _ = R.validate_decisions([FIXTURE_DECISIONS[2]], fin)
    assert trades[0]["force_flat"] is True
    assert R.fold_of(trades[0]["entry_bar_ts"]) == 0


# ---------- booking: dual book columns, hand-computed ----------
def test_book_trades_dual_columns_hand_computed():
    trades = [_dec("t1", "EUR/USD", 1, "2021-06-09T20:00:00+00:00",
                   "2021-06-10T20:00:00+00:00", 1.10, "2021-06-11T20:00:00+00:00", 1.15)]
    adjustments = {"t1": 2.0}
    booked, specs, dual = R.book_trades(trades, adjustments)
    # gross move = +1 * 10000 * (1.15/1.10 - 1) = 454.5454545455
    assert booked[0]["_gross_move_pnl"] == pytest.approx(454.5454545455, abs=1e-9)
    # price-only = gross - 2 x (10000 x 1.5bps) = 454.5454545455 - 3.0 = 451.5454545455
    assert booked[0]["_price_only"] == pytest.approx(451.5454545455, abs=1e-9)
    # financing-adjusted = price-only + carried adjustment = 453.5454545455
    assert booked[0]["_pnl"] == pytest.approx(453.5454545455, abs=1e-9)
    assert booked[0]["_financing"] == pytest.approx(2.0)
    assert dual[0].price_only_pnl_usd == pytest.approx(451.5454545455, abs=1e-9)
    assert dual[0].financing_adjusted_pnl_usd == pytest.approx(453.5454545455, abs=1e-9)


def test_book_trades_dry_run_zeroes_book_columns_only():
    trades = [_dec("t1", "USD/JPY", -1, "2021-06-09T20:00:00+00:00",
                   "2021-06-10T20:00:00+00:00", 150.0, "2021-06-11T20:00:00+00:00", 149.0)]
    booked, _specs, _dual = R.book_trades(trades, {"t1": 5.0}, dry_run=True)
    # gross move would be +66.666... but dry_run books 0 in BOTH book columns
    assert booked[0]["_gross_move_pnl"] == pytest.approx(66.6666666667, abs=1e-9)
    assert booked[0]["_price_only"] == 0.0 and booked[0]["_pnl"] == 0.0
    assert booked[0]["_financing"] == 0.0 and booked[0]["_dry_run"] is True


# ---------- stress: F1-fixed booked tiers, hand-computed ----------
def test_stress_booking_f1_fixed_hand_computed():
    trades = [_dec("t1", "EUR/USD", 1, "2021-06-09T20:00:00+00:00",
                   "2021-06-10T20:00:00+00:00", 1.10, "2021-06-11T20:00:00+00:00", 1.15)]
    specs = [R._spec_of(t) for t in trades]
    stress = R.stress_book(specs, {"t1"})
    # gross 454.5454545455 minus round-trip cost 3.00 / 4.50 / 6.00 USD:
    assert stress["tier1.0"]["total_pnl"] == pytest.approx(451.5454545455, abs=1e-9)
    assert stress["tier1.5"]["total_pnl"] == pytest.approx(450.0454545455, abs=1e-9)
    assert stress["tier2.0"]["total_pnl"] == pytest.approx(448.5454545455, abs=1e-9)
    # pure cost deltas, applied to BOOKED PnL (the F1 fix):
    assert stress["tier1.5"]["cost_component_delta_vs_base_usd"] == pytest.approx(-1.5)
    assert stress["tier2.0"]["cost_component_delta_vs_base_usd"] == pytest.approx(-3.0)
    rows = [stress[f"tier{t}"] for t in ("1.0", "1.5", "2.0")]
    assert len({(r["total_pnl"], r["expectancy"]) for r in rows}) == 3  # rows distinct


# ---------- gates on hand-built records ----------
def _rec(base_exp, base_pf, folds, mdd=100.0, fold_share=0.3, conc=None,
         stress=None, drop=None, usd=None, price_exp=None, alpha=None,
         n_decisions=1000):
    price_exp = base_exp if price_exp is None else price_exp
    return {
        "base": {"expectancy": base_exp, "pf": base_pf, "total_pnl": base_exp * 100},
        "base_price_only": {"expectancy": price_exp, "pf": base_pf,
                            "total_pnl": price_exp * 100},
        "folds": folds, "mdd_usd": mdd, "fold_positive_share": fold_share,
        "pair_concentration": conc if conc is not None else {"EUR/USD": 0.2},
        "stress": stress if stress is not None else {
            "tier1.5": {"total_pnl": 10.0, "pf": 1.2},
            "tier2.0": {"total_pnl": 5.0, "pf": 1.05}},
        "drop_one_expectancy": drop if drop is not None else {p: 1.0 for p in R.PAIRS},
        "usd_drift_diag": usd if usd is not None else {"corr": 0.05, "n_days": 300, "evaluated": True},
        "incremental_alpha": alpha,
        "n_decisions": n_decisions,
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
    assert not ok and "DROPOUT_SURVIVAL_BELOW_6_OF_8" in reasons
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), usd={"corr": 0.31, "n_days": 300, "evaluated": True}))
    assert not ok and "USD_DRIFT_EXPLAINS_ANCHOR" in reasons
    ok, _ = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), usd={"corr": None, "n_days": 10, "evaluated": False}))
    assert ok  # not evaluated -> cannot fail


def test_financing_gate_fires_on_manufactured_edge():
    # Financing-adjusted positive while the price-only book is non-positive:
    # financing manufactured the edge -> the anchor fails (PLAN section 12).
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.30, _good_folds(), price_exp=-0.05))
    assert not ok and "FINANCING_MANUFACTURES_EDGE" in reasons
    # Exactly zero price-only expectancy also fires the gate.
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.30, _good_folds(), price_exp=0.0))
    assert not ok and "FINANCING_MANUFACTURES_EDGE" in reasons
    # A genuinely price-positive book passes the financing gate.
    ok, _ = R.stage_a_gates(_rec(0.5, 1.30, _good_folds(), price_exp=0.2))
    assert ok
    # Non-positive adjusted expectancy is caught by the expectancy gate; the
    # financing gate does not double-fire on it.
    ok, reasons = R.stage_a_gates(_rec(-0.5, 0.85, _good_folds(), price_exp=-0.4))
    assert not ok and "FINANCING_MANUFACTURES_EDGE" not in reasons


def test_decision_floor_and_incremental_alpha_gates():
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), n_decisions=39))
    assert not ok and "DECISION_FLOOR_NOT_MET" in reasons
    ok, reasons = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), alpha=0.0))
    assert not ok and "INCREMENTAL_ALPHA_NOT_POSITIVE" in reasons
    ok, _ = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), alpha=0.01))
    assert ok
    ok, _ = R.stage_a_gates(_rec(0.5, 1.2, _good_folds(), alpha=None))
    assert ok  # absent -> evaluated family-side per the frozen treatment


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


# ---------- metrics hand-math (inherited conventions) ----------
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
    # equity curve 100 -> 150 -> 50 -> 120 has max drawdown 100
    assert R.mdd_of([100.0, 50.0, -100.0, 70.0]) == 100.0
    assert R.mdd_of([100.0, -10.0, 20.0]) == 10.0
    # break-even from the kernel: G=454.5454545455 over 1 trade at 10000
    be = accounting.break_even_bps([454.5454545455])
    assert be == pytest.approx(227.272727, abs=1e-6)


# ---------- USD-drift diagnostic (runner-owned statistic) ----------
def test_usd_drift_diag_hand_computed():
    trades, returns = [], {}
    for i in range(60):
        day = f"2021-{1 + i // 28:02d}-{(i % 28) + 1:02d}"
        trades.append({"pair": "EUR/USD", "entry_bar_ts": f"{day}T20:00:00+00:00",
                       "_pnl": float(i)})
        returns[day] = 0.001 * i
    diag = R.usd_drift_corr(trades, returns)
    assert diag["evaluated"] is True and diag["n_days"] == 60
    assert diag["corr"] == pytest.approx(1.0)   # pnl perfectly tracks USD index
    flipped = [dict(t, _pnl=-t["_pnl"]) for t in trades]
    diag = R.usd_drift_corr(flipped, returns)
    assert diag["corr"] == pytest.approx(-1.0)
    # below the 60-day floor the diagnostic is not evaluated and cannot fail
    diag = R.usd_drift_corr(trades[:59], returns)
    assert diag["evaluated"] is False and diag["n_days"] == 59


# ---------- per-arm wall clock: fail-closed TECHABORT ----------
def test_arm_timeout_techabort():
    with pytest.raises(R.TechAbort, match="TECHABORT"):
        R.call_family_arm(SlowFamily(), "anchor", {}, None, None,
                          timeout_minutes=0.0005)  # 0.03 s wall
    # a fast family passes through untouched
    out = R.call_family_arm(DummyFamily(), "anchor", {}, None, None,
                            timeout_minutes=5.0)
    assert out["decisions"]


# ---------- macro reader: availability gating + fail-closed BLOCKED_DATA ----------
def _vintage(area, value, effective_day, avail_iso):
    return {"source_id": "BIS_CBPOL", "dataset_id": "WS_CBPOL",
            "entity_id": area, "field": "policy_rate", "value": value,
            "unit": "percent_per_annum",
            "event_time_utc": f"{effective_day}T00:00:00Z",
            "available_time_utc": avail_iso,
            "effective_time_utc": f"{effective_day}T00:00:00Z",
            "vintage_time_utc": avail_iso,
            "retrieved_time_utc": "2026-09-01T00:00:00Z",
            "raw_path": "bis/cbol/x.json", "raw_sha256": "a" * 64,
            "license_id": "bis-terms-public-v1",
            "entitlement_id": "anonymous-no-key",
            "normalizer_version": "bis-adapter-1.0.0"}


def test_macro_reader_asof_gating_and_blocked_data():
    with tempfile.TemporaryDirectory() as tmp:
        us = os.path.join(tmp, "US.json")
        emu = os.path.join(tmp, "EMU.json")
        json.dump([_vintage("US", 0.25, "2021-01-01", "2021-01-01T23:59:59Z"),
                   _vintage("US", 0.50, "2021-06-16", "2021-06-16T23:59:59Z")], open(us, "w"))
        json.dump([_vintage("EMU", -0.5, "2021-01-01", "2021-01-01T23:59:59Z")], open(emu, "w"))
        reader = PolicyRateReader.from_data_paths({"macro_vintages": {"US": us, "EMU": emu}})
        # A 2021-06-16 decision (20:00Z) cannot read the rate available that UTC day's end.
        assert reader.policy_rate("US", "2021-06-16T20:00:00Z") == 0.25
        # The next decision day reads it.
        assert reader.policy_rate("US", "2021-06-17T20:00:00Z") == 0.50
        assert reader.differential("EMU", "US", "2021-06-17T20:00:00Z") == pytest.approx(-1.0)
        # Missing eligible vintage at T -> None (NO_EVAL, never backfilled).
        assert reader.policy_rate("US", "2020-06-17T20:00:00Z") is None
        # Missing area -> fail closed.
        with pytest.raises(MacroDataBlocked, match="BLOCKED_DATA"):
            reader.policy_rate("GB", "2021-06-17T20:00:00Z")
        # Missing file / missing key -> fail closed.
        with pytest.raises(MacroDataBlocked, match="BLOCKED_DATA"):
            PolicyRateReader.from_data_paths(
                {"macro_vintages": {"US": us, "GB": os.path.join(tmp, "GB.json")}})
        with pytest.raises(MacroDataBlocked, match="BLOCKED_DATA"):
            PolicyRateReader.from_data_paths({})
        with pytest.raises(MacroDataBlocked, match="BLOCKED_DATA"):
            R.compute_cell("family1", "anchor", {}, freeze_token=None)


# ---------- cell assembly: dual-book presence + immutability ----------
def _scores_token():
    return "scored-token-for-tests"


def test_dummy_family_end_to_end_dry_run():
    rec = R.compute_cell("family1", "anchor", {}, freeze_token=None,
                         macro_reader=PolicyRateReader({}))
    # dummy dry-run: scored=false, real_pnl=false, placeholders only
    assert rec["dry_run"] is True and rec["real_pnl"] is False and rec["scored"] is False
    assert rec["price_only_pnl_usd"] == 0.0 and rec["financing_adjusted_pnl_usd"] == 0.0
    assert rec["financing_adjustment_usd"] == 0.0
    assert rec["base"]["total_pnl"] == 0.0 and rec["base"]["trades"] == 3
    assert rec["n_decisions"] == 3 and rec["purged_trades"] == 0
    assert rec["weekend_gate_dropped"] == 0
    assert rec["folds"][0]["trades"] == 2 and rec["folds"][2]["trades"] == 1
    # dry-run records are refused at publication even with a valid token file
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        auth = os.path.join(tmp, "auth.json")
        json.dump({"freeze_token": W3}, open(auth, "w"))
        with pytest.raises(ValueError, match="REAL_PNL_REQUIRED"):
            R.publish_cell(led, rec, auth, W3)
        assert not os.path.exists(led)


def test_dummy_family_end_to_end_scored_mode_flags():
    rec = R.compute_cell("family1", "anchor", {"price_h1_dir": _scored_price_dir()},
                         freeze_token=_scores_token(),
                         macro_reader=PolicyRateReader({}))
    assert rec["dry_run"] is False and rec["real_pnl"] is True and rec["scored"] is True
    # hand-computed dual-book sums over the three fixture trades (IEEE reprs):
    # d1: gross 90.9090909091, price-only 87.9090909091, +2.0
    # d2: gross 66.6666666667, price-only 63.6666666667, +1.0
    # d3: gross 46.2962962963, price-only 43.2962962963, -0.5
    assert rec["gross_price_pnl_usd"] == pytest.approx(203.8720538721, abs=1e-9)
    assert rec["price_only_pnl_usd"] == pytest.approx(194.8720538721, abs=1e-9)
    assert rec["financing_adjustment_usd"] == pytest.approx(2.5, abs=1e-9)
    assert rec["financing_adjusted_pnl_usd"] == pytest.approx(197.3720538721, abs=1e-9)
    # V3-I H1: the scored anchor ALWAYS carries the runner-computed
    # incremental alpha = anchor expectancy 197.3720538721/3 - benchmark
    # expectancy 453.5454545455 (the b1 book) = -387.7547699215 -> the gate
    # fires and the record is still returned.
    assert rec["incremental_alpha"] == pytest.approx(-387.7547699215, abs=1e-9)
    assert rec["benchmark_treatment"]["n_decisions"] == 1
    assert rec["benchmark_treatment"]["expectancy"] == pytest.approx(453.5454545455, abs=1e-9)
    # the small fixture fails the floor gate but every gate evaluated
    ok, reasons = R.stage_a_gates(rec)
    assert not ok
    assert "DECISION_FLOOR_NOT_MET" in reasons
    assert "INCREMENTAL_ALPHA_NOT_POSITIVE" in reasons
    # V3-I H2: the USD index was built runner-side from the snapshot dir
    assert rec["usd_index_source"] == "price_h1_dir" and rec["usd_index_pairs"] == 2
    assert rec["usd_drift_diag"]["evaluated"] is False  # < 60 common days
    # V3-I M1: the dropout scenarios are recorded; pair part matches the
    # drop-one dict, all eight (7 pairs + best fold) survive this book
    assert len(rec["dropout_scenarios"]) == 8
    assert {s["scenario"].split(":", 1)[1] for s in rec["dropout_scenarios"]
            if s["scenario"].startswith("drop_pair:")} == set(R.PAIRS)
    for s in rec["dropout_scenarios"]:
        if s["scenario"].startswith("drop_pair:"):
            assert s["expectancy"] == rec["drop_one_expectancy"][s["scenario"].split(":", 1)[1]]
        assert s["survived"] is True
    # F1-fixed stress rows present and distinct, delay stress carried unblended
    assert {"tier1.0", "tier1.5", "tier2.0"} <= set(rec["stress"])
    assert (rec["stress"]["tier1.0"]["total_pnl"]
            != rec["stress"]["tier1.5"]["total_pnl"]
            != rec["stress"]["tier2.0"]["total_pnl"])
    assert rec["delay_stress"] == {"carried_unblended": True, "n_delayed_trades": 0}
    assert rec["break_even_cost_bps"] == pytest.approx(
        accounting.break_even_bps([90.9090909091, 66.6666666667, 46.2962962963]), abs=1e-6)


def test_dual_book_presence_and_immutability_in_cell_record():
    rec = R.compute_cell("family1", "anchor", {"price_h1_dir": _scored_price_dir()},
                         freeze_token=_scores_token(),
                         macro_reader=PolicyRateReader({}))
    # both immutable columns present as SEPARATE keys
    assert "price_only_pnl_usd" in rec and "financing_adjusted_pnl_usd" in rec
    digest = accounting.digest_of(rec)
    accounting.validate_scored_record(rec, digest)  # intact
    mutated = dict(rec)
    mutated["price_only_pnl_usd"] = mutated["price_only_pnl_usd"] + 1.0
    with pytest.raises(accounting.PositionBookError, match="DUAL_BOOK_VIOLATION"):
        accounting.validate_scored_record(mutated, digest)


# ---------- once-only publication behind the freeze token ----------
def _auth(tmp, token=W3):
    p = os.path.join(tmp, "auth.json")
    json.dump({"freeze_token": token}, open(p, "w"))
    return p


def _real_record():
    """Full gate-carrying record (publish computes gates before hashing)."""
    return {"cell_id": "family1:anchor:tier1.0", "dry_run": False, "real_pnl": True,
            "base": {"expectancy": 0.5, "pf": 1.3, "total_pnl": 500.0},
            "base_price_only": {"expectancy": 0.3, "pf": 1.2, "total_pnl": 300.0},
            "folds": _good_folds(), "mdd_usd": 100.0, "fold_positive_share": 0.3,
            "pair_concentration": {"EUR/USD": 0.2},
            "stress": {"tier1.5": {"total_pnl": 10.0, "pf": 1.2},
                       "tier2.0": {"total_pnl": 5.0, "pf": 1.05}},
            "drop_one_expectancy": {p: 1.0 for p in R.PAIRS},
            "usd_drift_diag": {"corr": 0.05, "n_days": 300, "evaluated": True},
            "incremental_alpha": 0.1, "n_decisions": 1000}


def test_publish_requires_authorization_and_matching_freeze_token():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        with pytest.raises(ValueError, match="LAUNCH_AUTHORIZATION_MISSING"):
            R.publish_cell(led, _real_record(), os.path.join(tmp, "nope.json"), W3)
        bad = _auth(tmp, token="OTHER")
        with pytest.raises(ValueError, match="FREEZE_TOKEN_MISMATCH"):
            R.publish_cell(led, _real_record(), bad, W3)
        assert not os.path.exists(led)


def test_publish_refuses_dry_run_records():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        rec = dict(_real_record()); rec["dry_run"] = True; rec["real_pnl"] = False
        with pytest.raises(ValueError, match="REAL_PNL_REQUIRED"):
            R.publish_cell(led, rec, _auth(tmp), W3)
        assert not os.path.exists(led)


def test_publish_once_only_and_replay_zero_delta():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        auth = _auth(tmp)
        assert R.publish_cell(led, _real_record(), auth, W3) == (1, 1)
        assert R.publish_cell(led, _real_record(), auth, W3) == (0, 0)  # replay
        lines = open(led, "rb").read().strip().split(b"\n")
        assert len(lines) == 1
        row = json.loads(lines[0])
        # digest-addressed: the line's digest is sha256 of its EXACT bytes
        exp = accounting.sha256_hex(accounting.canonical_json_bytes(
            {**_real_record(), "gates": True, "gate_reasons": [], "published": True}))
        assert accounting.sha256_hex(lines[0]) == exp
        assert row["published"] is True  # flipped pre-digest (V3-L4 by construction)


def test_publish_serializes_parallel_writers():
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        auth = _auth(tmp)

        def pub(i):
            rec = _real_record(); rec["cell_id"] = f"cell{i}"
            R.publish_cell(led, rec, auth, W3)
        ts = [threading.Thread(target=pub, args=(i,)) for i in range(8)]
        [t.start() for t in ts]; [t.join() for t in ts]
        lines = open(led, "rb").read().strip().split(b"\n")
        digests = {accounting.sha256_hex(line) for line in lines}
        assert len(lines) == 8 and len(digests) == 8


# ===================== V3-I remediation (findings H1/H2/H3/M1) =====================

# ---------- H2: the USD index is built INSIDE the runner (hand golden) ----------
def test_usd_index_hand_computed_two_pair_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        _h1_file(tmp, "EUR/USD", [
            ("2021-06-09 20:00:00", 1.100, 1.1001, 1.0999, 1.10),
            ("2021-06-10 20:00:00", 1.200, 1.2001, 1.1999, 1.21)])
        _h1_file(tmp, "USD/JPY", [
            ("2021-06-09 20:00:00", 100.0, 100.1, 99.9, 100.0),
            ("2021-06-10 20:00:00", 101.0, 101.1, 100.9, 101.0),
            ("2021-06-11 20:00:00", 102.0, 102.1, 101.9, 102.0),   # Friday
            ("2021-06-12 20:00:00", 103.0, 103.1, 102.9, 103.0),   # Saturday: ignored
            ("2021-06-11 19:00:00", 55.0, 55.1, 54.9, 55.0),       # 15:00-NY: ignored
            ("2021-06-14 20:00:00", 103.0, 103.1, 102.9, 103.02)])  # Monday
        # Hand-computed (XXX/USD contributes -r, USD/XXX +r, equal-weight mean):
        #   2021-06-10: EUR/USD -(1.21/1.10-1) = -0.10; JPY +(101/100-1) = +0.01
        #   2021-06-11: JPY only, 102/101-1 = 0.00990099009901 (weekend-partial day)
        #   2021-06-14: Fri->Mon is ONE daily step: JPY 103.02/102-1 = 0.01
        index = R.usd_index_daily_returns(tmp)
        assert set(index) == {"2021-06-10", "2021-06-11", "2021-06-14"}
        assert index["2021-06-10"] == pytest.approx((-0.10 + 0.01) / 2, abs=1e-12)
        assert index["2021-06-11"] == pytest.approx(102.0 / 101.0 - 1.0, abs=1e-12)
        assert index["2021-06-14"] == pytest.approx(103.02 / 102.0 - 1.0, abs=1e-12)
        # an explicit pair subset pins the equal-weight-over-present-pairs rule
        only_eur = R.usd_index_daily_returns(tmp, pairs=("EUR/USD",))
        assert only_eur == {"2021-06-10": pytest.approx(-(1.21 / 1.10 - 1.0), abs=1e-12)}
        # source resolution: explicit override > price_h1_dir > h1_dir
        idx, key, n_pairs = R.usd_index_from_data_paths({"h1_dir": tmp})
        assert key == "h1_dir" and n_pairs == 2 and idx == index
        _idx2, key2, _n2 = R.usd_index_from_data_paths(
            {"price_h1_dir": tmp, "h1_dir": os.path.join(tmp, "elsewhere")})
        assert key2 == "price_h1_dir"
        _idx3, key3, _n3 = R.usd_index_from_data_paths(
            {"usd_index_h1_dir": tmp, "price_h1_dir": os.path.join(tmp, "nope")})
        assert key3 == "usd_index_h1_dir"
        assert R.usd_index_from_data_paths({}) == (None, None, 0)
        # a present but empty/broken source fails closed
        empty = tempfile.mkdtemp(prefix="runner_empty_prices_")
        with pytest.raises(RuntimeError, match="BLOCKED_DATA"):
            R.usd_index_daily_returns(empty)
        with pytest.raises(RuntimeError, match="BLOCKED_DATA"):
            R.usd_index_daily_returns(os.path.join(tmp, "missing-dir"))


def test_scored_run_without_price_source_fails_closed():
    # A scored run with booked trades but no H1 source cannot evaluate the
    # frozen USD-drift gate: USD_INDEX_SOURCE_MISSING (fail closed, V3-I H2).
    with pytest.raises(R.DecisionRuleError, match="USD_INDEX_SOURCE_MISSING"):
        R.compute_cell("family1", "anchor", {}, freeze_token=_scores_token(),
                       macro_reader=PolicyRateReader({}))
    # ...while the dry-run of the same cell stays a placeholder record.
    rec = R.compute_cell("family1", "anchor", {}, freeze_token=None,
                         macro_reader=PolicyRateReader({}))
    assert rec["dry_run"] is True and rec["usd_index_source"] is None


# ---------- H3: dry-run records leak NO booked monetary metric ----------
def test_dry_run_record_hygiene_zeroes_every_monetary_field():
    rec = R.compute_cell("family1", "anchor", {}, freeze_token=None,
                         macro_reader=PolicyRateReader({}))
    # top-level booked columns
    for key in ("gross_price_pnl_usd", "price_only_pnl_usd",
                "financing_adjustment_usd", "financing_adjusted_pnl_usd"):
        assert rec[key] == 0.0, key
    # book metrics: money zeroed / pf None, trade COUNTS kept
    zeroed = {"trades": 3, "total_pnl": 0.0, "expectancy": 0.0,
              "pf": None, "gross_positive": 0.0}
    assert rec["base"] == zeroed and rec["base_price_only"] == zeroed
    for fold in rec["folds"]:
        assert fold["total_pnl"] == 0.0 and fold["expectancy"] == 0.0
        assert fold["gross_positive"] == 0.0 and fold["pf"] is None
    assert [f["trades"] for f in rec["folds"]] == [2, 0, 1]
    assert [f["populated"] for f in rec["folds"]] == [False, False, False]
    # the stress sub-record (booked from REAL specs internally) is zeroed at
    # every tier -- the exact H3 leak the auditor measured on W3
    assert set(rec["stress"]) == {"tier1.0", "tier1.5", "tier2.0"}
    for tier, st in rec["stress"].items():
        assert st["total_pnl"] == 0.0 and st["expectancy"] == 0.0
        assert st["gross_positive"] == 0.0 and st["pf"] is None
        assert st["cost_component_delta_vs_base_usd"] == 0.0
        assert st["trades"] == 3
        assert st["stress_rows_distinct_certified"] is True
    # remaining monetary/diagnostic fields
    assert rec["break_even_cost_bps"] is None
    assert rec["mdd_usd"] == 0.0
    assert rec["fold_positive_share"] == 0.0
    assert rec["pair_concentration"] == {}
    assert rec["drop_one_expectancy"] == {p: 0.0 for p in R.PAIRS}
    assert all(s["expectancy"] is None and s["survived"] is None
               for s in rec["dropout_scenarios"])
    assert len(rec["dropout_scenarios"]) == 8
    assert rec["incremental_alpha"] is None and rec["benchmark_treatment"] is None
    assert rec["usd_drift_diag"] == {"corr": None, "n_days": 3, "evaluated": False}
    # counts and mode flags survive untouched
    assert rec["n_decisions"] == 3 and rec["n_trades_kept"] == 3
    assert rec["weekend_gate_dropped"] == 0 and rec["purged_trades"] == 0
    assert rec["delay_stress"] == {"carried_unblended": True, "n_delayed_trades": 0}
    assert rec["folds_declared"] == list(R.FOLD_BOUNDARIES)
    assert rec["scored"] is False and rec["real_pnl"] is False
    assert rec["dry_run"] is True and rec["published"] is False


# ---------- H1: the incremental alpha is always computed when scored ----------
class PositiveAlphaFamily(DummyFamily):
    """Benchmark book = one LOSING round trip: gross 10000*(1.05/1.10-1)
    = -454.5454545455, price-only -457.5454545455, financing 0.0."""

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        out = super().run_arm(arm, data_paths, macro_reader, freeze_token)
        if arm == "benchmark_treatment":
            out = copy.deepcopy(out)
            out["decisions"][0]["exit_price"] = 1.05
            out["financing_events"][0]["financing_adjustment_usd"] = 0.0
        return out


def test_scored_anchor_incremental_alpha_gate_fires_and_passes():
    # negative alpha: the gate FAILS but the record is still returned
    rec = R.compute_cell("family1", "anchor", {"price_h1_dir": _scored_price_dir()},
                         freeze_token=_scores_token(),
                         macro_reader=PolicyRateReader({}))
    assert rec["incremental_alpha"] == pytest.approx(-387.7547699215, abs=1e-9)
    ok, reasons = R.stage_a_gates(rec)
    assert not ok and "INCREMENTAL_ALPHA_NOT_POSITIVE" in reasons
    # positive alpha: anchor expectancy 65.790684624 - (-457.5454545455)
    # = 523.3361391695 > 0 -> the incremental gate does not fire
    R.FAMILIES["family1"] = PositiveAlphaFamily()
    try:
        rec2 = R.compute_cell("family1", "anchor",
                              {"price_h1_dir": _scored_price_dir()},
                              freeze_token=_scores_token(),
                              macro_reader=PolicyRateReader({}))
    finally:
        R.FAMILIES["family1"] = DummyFamily()
    assert rec2["incremental_alpha"] == pytest.approx(523.3361391695, abs=1e-9)
    assert rec2["benchmark_treatment"]["expectancy"] == pytest.approx(-457.5454545455, abs=1e-9)
    ok2, reasons2 = R.stage_a_gates(rec2)
    assert "INCREMENTAL_ALPHA_NOT_POSITIVE" not in reasons2


def test_scored_anchor_requires_benchmark_treatment_arm():
    # enforcement: a family WITHOUT the benchmark arm cannot produce a
    # scored anchor cell (its unknown-arm refusal propagates, fail closed)
    R.FAMILIES["family1"] = NoBenchmarkFamily()
    try:
        with pytest.raises(ValueError, match="benchmark_treatment"):
            R.compute_cell("family1", "anchor", {"price_h1_dir": _scored_price_dir()},
                           freeze_token=_scores_token(),
                           macro_reader=PolicyRateReader({}))
        # the dry-run of the same family never calls the benchmark arm
        rec = R.compute_cell("family1", "anchor", {}, freeze_token=None,
                             macro_reader=PolicyRateReader({}))
        assert rec["dry_run"] is True and rec["incremental_alpha"] is None
    finally:
        R.FAMILIES["family1"] = DummyFamily()
    # ...and the benchmark treatment is never a scored cell of its own
    with pytest.raises(ValueError, match="BENCHMARK_TREATMENT_IS_NOT_A_SCORED_CELL"):
        R.compute_cell("family1", R.BENCHMARK_ARM, {}, freeze_token=None,
                       macro_reader=PolicyRateReader({}))


# ---------- M1: dropout survival incl. the drop-one-BEST-fold scenario ----------
def test_dropout_scenarios_hand_built():
    # hand-built book spanning every fold boundary (folds 0, 1, 2):
    # pnls 100, 50 (fold 0); 200 (fold 1); -80, 30 (fold 2); full exp 60
    trades = [
        {"pair": "EUR/USD", "_fold": 0}, {"pair": "GBP/USD", "_fold": 0},
        {"pair": "USD/JPY", "_fold": 1}, {"pair": "EUR/USD", "_fold": 2},
        {"pair": "AUD/USD", "_fold": 2}]
    pnls = [100.0, 50.0, 200.0, -80.0, 30.0]
    folds = [{"fold": 0, "trades": 2, "expectancy": 75.0},
             {"fold": 1, "trades": 1, "expectancy": 200.0},
             {"fold": 2, "trades": 2, "expectancy": -25.0}]
    s = R.dropout_scenarios(trades, pnls, folds)
    assert [x["scenario"] for x in s] == \
        [f"drop_pair:{p}" for p in R.PAIRS] + ["drop_best_fold:1"]
    # hand-computed reduced-book expectancies:
    expected = {
        "drop_pair:EUR/USD": (50.0 + 200.0 + 30.0) / 3,          # 93.3333333333
        "drop_pair:GBP/USD": (100.0 + 200.0 - 80.0 + 30.0) / 4,  # 62.5
        "drop_pair:AUD/USD": (100.0 + 50.0 + 200.0 - 80.0) / 4,  # 67.5
        "drop_pair:NZD/USD": 60.0,
        "drop_pair:USD/JPY": (100.0 + 50.0 - 80.0 + 30.0) / 4,   # 25.0
        "drop_pair:USD/CHF": 60.0, "drop_pair:USD/CAD": 60.0,
        "drop_best_fold:1": (100.0 + 50.0 - 80.0 + 30.0) / 4,    # 25.0
    }
    assert len(s) == 8
    for x in s:
        assert x["expectancy"] == pytest.approx(expected[x["scenario"]], abs=1e-9)
        assert x["survived"] is True
    # a fold-concentrated book: dropping the BEST fold flips the sign
    trades2 = [{"pair": "EUR/USD", "_fold": 0}, {"pair": "GBP/USD", "_fold": 0},
               {"pair": "USD/JPY", "_fold": 1}, {"pair": "EUR/USD", "_fold": 2}]
    pnls2 = [-200.0, -100.0, 10.0, 5.0]
    folds2 = [{"fold": 0, "trades": 2, "expectancy": -150.0},
              {"fold": 1, "trades": 1, "expectancy": 10.0},
              {"fold": 2, "trades": 1, "expectancy": 5.0}]
    s2 = R.dropout_scenarios(trades2, pnls2, folds2)
    assert s2[-1]["scenario"] == "drop_best_fold:1"
    assert s2[-1]["expectancy"] == pytest.approx((-200.0 - 100.0 + 5.0) / 3, abs=1e-9)
    assert s2[-1]["survived"] is False
    assert all(not x["survived"] for x in s2)   # 0/7
    # an unevaluable fold scenario (no fold holds trades) fails closed
    s3 = R.dropout_scenarios([], [], [{"fold": 0, "trades": 0, "expectancy": 0.0}] * 3)
    assert s3[-1] == {"scenario": "drop_best_fold:none",
                      "expectancy": None, "survived": False}


def test_stage_a_dropout_survival_gate_over_scenarios():
    # M1-DEV binding floor (a7_prelaunch_v3_delta.json): 6 of the
    # DROPOUT_SCENARIOS = 8 suite must survive.
    assert R.DROPOUT_SCENARIOS == 8 and R.DROPOUT_MIN_SURVIVAL == 6
    rec = _rec(0.5, 1.2, _good_folds())
    rec["dropout_scenarios"] = (
        [{"scenario": f"drop_pair:{p}", "expectancy": 1.0, "survived": True}
         for p in R.PAIRS]
        + [{"scenario": "drop_best_fold:0", "expectancy": 0.5, "survived": True}])
    ok, _ = R.stage_a_gates(rec)
    assert ok                                   # 8/8
    rec["dropout_scenarios"][7]["survived"] = False   # 7/8 still passes
    ok, _ = R.stage_a_gates(rec)
    assert ok
    rec["dropout_scenarios"][6]["survived"] = False   # exactly 6/8 passes
    ok, reasons = R.stage_a_gates(rec)
    assert ok
    rec["dropout_scenarios"][5]["survived"] = False   # 5/8 FAILS (binding floor)
    ok, reasons = R.stage_a_gates(rec)
    assert not ok and "DROPOUT_SURVIVAL_BELOW_6_OF_8" in reasons


# ---------- D1: the incremental alpha follows the family-DECLARED definition ----------
def _pairday_price_dir():
    """Synthetic 2-pair x 5-daily-bar snapshot, 2021-06-07..11 (EDT:
    20:00Z == 16:00 New York).  With the fixture warmup of 2 bars the
    identical post-warmup schedule window holds (5-2) + (5-2) = 6 pair-days."""
    tmp = tempfile.mkdtemp(prefix="runner_pairday_prices_")
    days = ("07", "08", "09", "10", "11")
    eur = [(f"2021-06-{d} 20:00:00", 1.10, 1.101, 1.099, 1.1005) for d in days]
    jpy = [(f"2021-06-{d} 20:00:00", 150.0, 150.1, 149.9, 150.05) for d in days]
    _h1_file(tmp, "EUR/USD", eur)
    _h1_file(tmp, "USD/JPY", jpy)
    return tmp


_PAIRDAY_FIN = [{"decision_id": did, "financing_adjustment_usd": 0.0,
                 "formula": "V3_FROZEN_POLICY_RATE_CARRY"}
                for did in ("pa1", "pb1", "pb2", "pb3")]
# Anchor: ONE round trip (entry Thu, exit Fri).  Benchmark: THREE small
# winners.  Hand-computed booked financing-adjusted PnL at tier 1.0
# (gross = 10000*(exit/entry-1); round-trip cost 3.0 USD; financing 0.0):
#   pa1 EUR/USD L 1.10 -> 1.101  : 6.0909090909
#   pb1 EUR/USD L 1.10 -> 1.1005 : 1.5454545455
#   pb2 USD/JPY S 150.0 -> 149.9 : 3.6666666667
#   pb3 EUR/USD L 1.20 -> 1.2008 : 3.6666666667
PAIRDAY_ANCHOR = [_dec("pa1", "EUR/USD", 1, "2021-06-09T20:00:00+00:00",
                       "2021-06-10T20:00:00+00:00", 1.10,
                       "2021-06-11T20:00:00+00:00", 1.101)]
PAIRDAY_BENCH = [
    _dec("pb1", "EUR/USD", 1, "2021-06-08T20:00:00+00:00",
         "2021-06-09T20:00:00+00:00", 1.10, "2021-06-10T20:00:00+00:00", 1.1005),
    _dec("pb2", "USD/JPY", -1, "2021-06-09T20:00:00+00:00",
         "2021-06-10T20:00:00+00:00", 150.0, "2021-06-11T20:00:00+00:00", 149.9),
    _dec("pb3", "EUR/USD", 1, "2021-06-08T20:00:00+00:00",
         "2021-06-09T20:00:00+00:00", 1.20, "2021-06-11T20:00:00+00:00", 1.2008),
]


class PairDayAlphaFamily:
    """Declares the A5 per-pair-day normalized definition (V3-I D1) with
    warmup_daily_bars = 2.  The anchor's single trade BEATS the benchmark
    per trade (+3.1313131313 expectancy difference) yet LOSES per pair-day
    over the identical window (-0.4646464647): the exact sign divergence the
    A5 per-pair-day normalization froze the gate on (exposure fairness)."""

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        meta = {"decision_clock": "daily", "proposal_id": "PAIRDAY",
                "alpha_definition": R.ALPHA_PER_PAIR_DAY_NORMALIZED,
                "warmup_daily_bars": 2}
        if arm == "benchmark_treatment":
            return {"decisions": copy.deepcopy(PAIRDAY_BENCH),
                    "financing_events": copy.deepcopy(_PAIRDAY_FIN[1:]),
                    "meta": dict(meta, proposal_id="PAIRDAY-BENCH")}
        return {"decisions": copy.deepcopy(PAIRDAY_ANCHOR),
                "financing_events": copy.deepcopy(_PAIRDAY_FIN[:1]),
                "meta": meta}


class LosingBenchPairDayFamily(PairDayAlphaFamily):
    """Same anchor; the benchmark books three LOSERS so the frozen
    per-pair-day alpha is positive and the gate does not fire."""

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        out = super().run_arm(arm, data_paths, macro_reader, freeze_token)
        if arm == "benchmark_treatment":
            out = copy.deepcopy(out)
            out["decisions"][0]["exit_price"] = 1.099    # pb1: -12.0909090909
            out["decisions"][1]["exit_price"] = 150.1    # pb2: -9.6666666667
            out["decisions"][2]["exit_price"] = 1.199    # pb3: -11.3333333333
        return out


def test_post_warmup_pair_days_counts_window():
    d = _pairday_price_dir()
    assert R.post_warmup_pair_days(d, 2) == 6            # (5-2) + (5-2)
    assert R.post_warmup_pair_days(d, 4) == 2            # (5-4) + (5-4)
    assert R.post_warmup_pair_days(d, 2, pairs=("EUR/USD",)) == 3
    with pytest.raises(R.DecisionRuleError, match="ALPHA_WARMUP_NOT_DECLARED"):
        R.post_warmup_pair_days(d, "2")
    with pytest.raises(R.DecisionRuleError, match="ALPHA_PRICE_SOURCE_MISSING"):
        R.post_warmup_pair_days(None, 2)
    with pytest.raises(R.DecisionRuleError, match="ALPHA_WINDOW_EMPTY"):
        R.post_warmup_pair_days(d, 5)                    # (5-5)+(5-5) = 0


def test_pair_day_normalized_alpha_golden_gate_fires():
    R.FAMILIES["family1"] = PairDayAlphaFamily()
    try:
        rec = R.compute_cell("family1", "anchor",
                             {"price_h1_dir": _pairday_price_dir()},
                             freeze_token=_scores_token(),
                             macro_reader=PolicyRateReader({}))
    finally:
        R.FAMILIES["family1"] = DummyFamily()
    # Hand-computed golden (A5 incremental_test.operationalization):
    #   anchor sum 6.0909090909 - benchmark sum 8.8787878789
    #   = -2.787878788 over N = 6 identical-window pair-days
    #   -> alpha = -0.4646464647  (NEGATIVE)
    assert rec["incremental_alpha_definition"] == R.ALPHA_PER_PAIR_DAY_NORMALIZED
    assert rec["incremental_alpha"] == pytest.approx(-0.4646464647, abs=1e-9)
    # The per-trade expectancy difference is reported alongside as the
    # proposal's DIAGNOSTIC -- and it disagrees IN SIGN with the frozen gate:
    # 6.0909090909 - 2.9595959596 = +3.1313131313.
    assert rec["benchmark_treatment"]["expectancy"] == pytest.approx(2.9595959596, abs=1e-9)
    assert (rec["benchmark_treatment"]["per_trade_expectancy_difference_diagnostic"]
            == pytest.approx(3.1313131313, abs=1e-9))
    # The gate follows the FROZEN per-pair-day value, not the diagnostic.
    ok, reasons = R.stage_a_gates(rec)
    assert not ok and "INCREMENTAL_ALPHA_NOT_POSITIVE" in reasons


def test_pair_day_normalized_alpha_positive_gate_passes():
    R.FAMILIES["family1"] = LosingBenchPairDayFamily()
    try:
        rec = R.compute_cell("family1", "anchor",
                             {"price_h1_dir": _pairday_price_dir()},
                             freeze_token=_scores_token(),
                             macro_reader=PolicyRateReader({}))
    finally:
        R.FAMILIES["family1"] = DummyFamily()
    # (6.0909090909 - (-33.0909090909)) / 6 = +6.5303030303 -> frozen gate
    # does not fire; diagnostic 6.0909090909 - (-11.0303030303) = +17.1212121212.
    assert rec["incremental_alpha"] == pytest.approx(6.5303030303, abs=1e-9)
    assert (rec["benchmark_treatment"]["per_trade_expectancy_difference_diagnostic"]
            == pytest.approx(17.1212121212, abs=1e-9))
    ok, reasons = R.stage_a_gates(rec)
    assert "INCREMENTAL_ALPHA_NOT_POSITIVE" not in reasons


class UnknownAlphaDefinitionFamily(DummyFamily):
    """Declares an alpha_definition the runner does not know."""

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        out = super().run_arm(arm, data_paths, macro_reader, freeze_token)
        out["meta"] = dict(out["meta"], alpha_definition="momentum_is_alpha_v9")
        return out


class UndeclaredAlphaFamily(DummyFamily):
    """Declares NO alpha_definition at all."""

    def run_arm(self, arm, data_paths, macro_reader, freeze_token):
        out = super().run_arm(arm, data_paths, macro_reader, freeze_token)
        meta = dict(out["meta"])
        meta.pop("alpha_definition", None)
        out["meta"] = meta
        return out


def test_unknown_or_undeclared_alpha_definition_fails_closed():
    for fam in (UnknownAlphaDefinitionFamily(), UndeclaredAlphaFamily()):
        R.FAMILIES["family1"] = fam
        try:
            with pytest.raises(R.DecisionRuleError, match="ALPHA_DEFINITION_UNKNOWN"):
                R.compute_cell("family1", "anchor",
                               {"price_h1_dir": _scored_price_dir()},
                               freeze_token=_scores_token(),
                               macro_reader=PolicyRateReader({}))
        finally:
            R.FAMILIES["family1"] = DummyFamily()
    # Dry-run never dispatches on the definition (no benchmark arm call).
    rec = R.compute_cell("family1", "anchor", {}, freeze_token=None,
                         macro_reader=PolicyRateReader({}))
    assert rec["dry_run"] is True and rec["incremental_alpha"] is None


def test_pair_day_window_fail_closed_paths():
    class NoWarmup(PairDayAlphaFamily):
        def run_arm(self, arm, data_paths, macro_reader, freeze_token):
            out = super().run_arm(arm, data_paths, macro_reader, freeze_token)
            meta = dict(out["meta"])
            meta.pop("warmup_daily_bars", None)
            out["meta"] = meta
            return out

    class EmptyWindow(PairDayAlphaFamily):
        def run_arm(self, arm, data_paths, macro_reader, freeze_token):
            out = super().run_arm(arm, data_paths, macro_reader, freeze_token)
            out["meta"] = dict(out["meta"], warmup_daily_bars=100)  # > 5 bars/pair
            return out

    R.FAMILIES["family1"] = NoWarmup()
    try:
        with pytest.raises(R.DecisionRuleError, match="ALPHA_WARMUP_NOT_DECLARED"):
            R.compute_cell("family1", "anchor",
                           {"price_h1_dir": _pairday_price_dir()},
                           freeze_token=_scores_token(),
                           macro_reader=PolicyRateReader({}))
    finally:
        R.FAMILIES["family1"] = DummyFamily()
    R.FAMILIES["family1"] = EmptyWindow()
    try:
        with pytest.raises(R.DecisionRuleError, match="ALPHA_WINDOW_EMPTY"):
            R.compute_cell("family1", "anchor",
                           {"price_h1_dir": _pairday_price_dir()},
                           freeze_token=_scores_token(),
                           macro_reader=PolicyRateReader({}))
    finally:
        R.FAMILIES["family1"] = DummyFamily()


def test_family_declarations_match_runner_constants():
    # The declared strings must equal the runner's dispatch constants
    # (guards silent drift between family meta and runner).
    import research.assets.forex_free_v3.family1 as f1
    import research.assets.forex_free_v3.family2 as f2
    assert f1.PROPOSAL_ID == "FXFV3-A5-P1"
    assert R.ALPHA_PER_PAIR_DAY_NORMALIZED == "a5_per_pair_day_normalized_v1"
    assert R.ALPHA_EXPECTANCY_DIFFERENCE == "per_trade_expectancy_difference_v1"
    # family1 declares the A5 definition with its 63-bar warmup; family2 the
    # A6 expectancy difference.
    import inspect
    src1 = inspect.getsource(f1.run_arm)
    src2 = inspect.getsource(f2.run_arm)
    assert '"alpha_definition": "a5_per_pair_day_normalized_v1"' in src1
    assert '"alpha_definition": "per_trade_expectancy_difference_v1"' in src2
