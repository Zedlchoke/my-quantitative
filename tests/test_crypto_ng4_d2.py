"""CRYPTO-NG4 D2 goldens (plan plans/PLAN_crypto_ng4.md sections 6/7).

Covers, per the D2 lane dispatch:
  1. hand-computed rho fixtures (Pearson AND Spearman, ties, bar 0.20 immovable);
  2. BETDIS construction vs closed forms (beta / residual / z, PIT windows,
     stale shift, entry/exit/fold discipline);
  3. fold-population kill fixture (any fold < 4 decisions => pre-score dead);
  4. inventory-hash fail-closed fixture (tampered/absent shadow inventory
     refuses before the heavy lock);
  5. venue-control fail-closed status (frozen 60-day floor unmet).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_WORKTREE))

from research.control.crypto_ng4_run.d2 import d2_run as D  # noqa: E402


# --------------------------------------------------------------------------- #
# 1. hand-computed rho fixtures
# --------------------------------------------------------------------------- #

def test_rho_perfect_positive_is_veto():
    x = [1.0, 0.0, -1.0] * 5
    row = D.rho_row(x, list(x), min_pairs=8)
    assert row["status"] == "VETO"
    assert row["pearson"] == 1.0 and row["spearman"] == 1.0
    assert row["max_abs_rho"] == 1.0
    assert row["margin_to_bar"] == pytest.approx(0.20 - 1.0)


def test_rho_perfect_negative_is_veto_on_abs():
    x = [1.0, 0.0, -1.0] * 5
    row = D.rho_row(x, [-v for v in x], min_pairs=8)
    assert row["status"] == "VETO"
    assert row["pearson"] == -1.0
    assert row["max_abs_rho"] == 1.0  # |rho| bar is sign-invariant


def test_rho_hand_computed_mixed_pair():
    # x = 1..10; y swaps adjacent pairs. By hand:
    # sum dx*dy = 77.5, sum dx^2 = sum dy^2 = 82.5 -> both coefficients 77.5/82.5
    x = [1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    y = [2.0, 1, 4, 3, 6, 5, 8, 7, 10, 9]
    expected = 77.5 / 82.5
    row = D.rho_row(x, y, min_pairs=8)
    assert row["pearson"] == pytest.approx(expected, abs=1e-6)
    assert row["spearman"] == pytest.approx(expected, abs=1e-6)
    assert row["status"] == "VETO"  # 0.9394 > 0.20 immovable bar


def test_rho_ties_average_rank_spearman():
    # Hand-checked case with ties in x (binary) and y.
    x = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
    y = [1.0, 2.0, 2.0, 3.0, 1.0, 2.0, 4.0, 3.0]
    # pearson: sum dx*dy = -2, sxx = 8, syy = 7.5 -> -2/sqrt(60)
    assert D.rho_row(x, y, min_pairs=8)["pearson"] == pytest.approx(
        -2.0 / (60.0 ** 0.5), abs=1e-6)
    # spearman: x avg-ranks 6.5/2.5, y avg-ranks 1.5/4/6.5/8:
    # sum dxdy = -12, sxx = 32, syy = 39 -> -12/sqrt(1248)
    assert D.rho_row(x, y, min_pairs=8)["spearman"] == pytest.approx(
        -12.0 / (1248.0 ** 0.5), abs=1e-6)


def test_rho_low_n_and_zero_variance_are_not_vetoes():
    assert D.rho_row([1.0, 0.0, 1.0], [1.0, 0.0, 1.0], min_pairs=8)[
        "status"] == "UNMEASURED_LOW_N"
    assert D.rho_row([1.0] * 10, [0.0, 1.0] * 5, min_pairs=8)[
        "status"] == "UNMEASURED_ZERO_VARIANCE"


def test_rho_bar_is_immovable_constant():
    assert D.RHO_BAR == 0.20
    assert D.MIN_PAIRS == 8
    assert D.FOLD_POP_FLOOR == 4
    assert D.NEIGH_SUBSUMPTION_BAR == 0.98


# --------------------------------------------------------------------------- #
# 2. BETDIS construction vs closed forms (synthetic panels)
# --------------------------------------------------------------------------- #

def _synthetic_pair(seed: int = 11, T: int = 4000):
    rng = np.random.default_rng(seed)
    rb = rng.normal(scale=0.01, size=T)
    ra = 0.8 * rb + rng.normal(scale=0.004, size=T)
    pa = {"last": 100.0 * np.exp(np.cumsum(np.concatenate(([0.0], ra))))}
    pb = {"last": 100.0 * np.exp(np.cumsum(np.concatenate(([0.0], rb))))}
    return pa, pb


def test_betdis_beta_residual_z_match_closed_form():
    pa, pb = _synthetic_pair()
    book = D.build_pair_state(pa, pb, 2.0)
    rra, rrb = D.log_returns(pa["last"]), D.log_returns(pb["last"])
    assert book["decisions"], "synthetic pair should trigger decisions"
    dec = book["decisions"][0]
    t = dec["decision_bar"]
    beta_ref = np.polyfit(rrb[t - 720:t], rra[t - 720:t], 1)[0]
    e_ref = rra[t] - beta_ref * rrb[t]
    ew = np.array([rra[u] - np.polyfit(rrb[u - 720:u], rra[u - 720:u], 1)[0] * rrb[u]
                   for u in range(t - 720, t)])
    sig_ref = 1.4826 * np.median(np.abs(ew - np.median(ew)))
    assert abs(book["z"][t] - e_ref / sig_ref) < 1e-8
    # decision at bar t close -> entry next bar; exit within H bars; one fold
    assert dec["entry_bar"] == t + 1
    assert dec["exit_bar"] <= dec["entry_bar"] + D.HORIZON - 1
    assert dec["fold"] == D.fold_of_bar(dec["entry_bar"])
    assert D.fold_of_bar(dec["exit_bar"]) == dec["fold"]
    # state series is exactly the holding window, sign = sign(entry z)
    j, x = dec["entry_bar"], dec["exit_bar"]
    assert np.all(book["state"][j:x + 1] == dec["sign"])
    assert book["state"][j - 1] == 0 and (x + 1 >= book["state"].size
                                          or book["state"][x + 1] == 0)


def test_stale_beta_window_shift_matches_closed_form():
    pa, pb = _synthetic_pair()
    rra, rrb = D.log_returns(pa["last"]), D.log_returns(pb["last"])
    stale = D.build_pair_state(pa, pb, 1.0, stale_shift=D.STALE_SHIFT)
    assert stale["decisions"], "synthetic pair should trigger stale decisions"
    dec = stale["decisions"][0]
    t = dec["decision_bar"]
    # beta window is exactly the trailing 720 bars ending 720 bars earlier
    beta_ref = np.polyfit(rrb[t - 1440:t - 720], rra[t - 1440:t - 720], 1)[0]
    be = D.rolling_ols_slope(rrb, rra, 720, shift=720)
    assert abs(be[t - 1] - beta_ref) < 1e-10
    ew = np.array([rra[u] - be[u - 1] * rrb[u] for u in range(t - 720, t)])
    sig_ref = 1.4826 * np.median(np.abs(ew - np.median(ew)))
    assert abs(stale["z"][t] - (rra[t] - be[t - 1] * rrb[t]) / sig_ref) < 1e-8


def test_first_decidable_bar_is_day61_and_fold_discipline_holds():
    assert D.FIRST_DECIDABLE_BAR == 61 * 24
    pa, pb = _synthetic_pair()
    book = D.build_pair_state(pa, pb, 1.0)
    for dec in book["decisions"]:
        assert dec["decision_bar"] >= D.FIRST_DECIDABLE_BAR
        # full H-bar window must fit inside a single frozen fold
        assert dec["exit_bar"] <= dec["entry_bar"] + D.HORIZON - 1
        assert D.fold_of_bar(dec["entry_bar"]) == dec["fold"]


# --------------------------------------------------------------------------- #
# 3. fold-population kill fixture (NG3-A5 class)
# --------------------------------------------------------------------------- #

def _dec(bar: int, fold: str) -> dict:
    return {"decision_bar": bar - 1, "entry_bar": bar, "exit_bar": bar + 23,
            "sign": 1.0, "fold": fold, "z_entry": 3.0}


def test_fold_population_below_floor_kills_pre_score():
    decisions = (
        [_dec(1500, "FOLD-1")] * 9
        + [_dec(3400, "FOLD-2")] * 12
        + [_dec(5300, "FOLD-3")] * 2          # < 4 -> kill
        + [_dec(7200, "FOLD-4")] * 30
    )
    report = D.pair_fold_report(decisions)
    assert report["decisions_per_fold"] == {
        "FOLD-1": 9, "FOLD-2": 12, "FOLD-3": 2, "FOLD-4": 30}
    assert report["folds_below_floor"] == ["FOLD-3"]
    assert report["pre_score_dead"] is True
    assert report["total_decisions"] == 53


def test_fold_population_at_floor_survives():
    decisions = [_dec(1500 + k, "FOLD-1") for k in range(4)] \
        + [_dec(3400, "FOLD-2")] * 4 + [_dec(5300, "FOLD-3")] * 4 \
        + [_dec(7200, "FOLD-4")] * 4
    report = D.pair_fold_report(decisions)
    assert report["folds_below_floor"] == []
    assert report["pre_score_dead"] is False


def test_fold_population_weekend_weekday_split():
    # entry bar 1464 = 2025-10-22 (a Wednesday); +72 bars = Saturday
    assert D.bar_ts(1464).weekday() == 2
    assert D.bar_ts(1464 + 72).weekday() >= 5
    report = D.pair_fold_report([_dec(1464, "FOLD-1"), _dec(1536, "FOLD-1"),
                                 _dec(1465, "FOLD-1"), _dec(1466, "FOLD-1")])
    assert report["weekend_entry_decisions_per_fold"]["FOLD-1"] == 1
    assert report["weekday_entry_decisions_per_fold"]["FOLD-1"] == 3


# --------------------------------------------------------------------------- #
# 4. inventory-hash fail-closed
# --------------------------------------------------------------------------- #

def test_committed_inventory_hash_matches_pin():
    assert D.INVENTORY_PATH.is_file()
    assert D.sha256_file(D.INVENTORY_PATH) == D.SHADOW_INVENTORY_SHA256


def test_committed_inventory_carries_plan_s6_and_x1_envelope():
    inv = json.loads(D.INVENTORY_PATH.read_text())
    names = [e["name"] for g in inv["groups"] for e in g.get("shapes", [])]
    ledger = [g for g in inv["groups"]
              if g["group"] == "X1_FAMILY_FAILURES_DEAD_FORM_ENVELOPE"]
    assert len(ledger) == 1 and ledger[0]["n_entries"] == 32
    for required in ("generic_dvol_shock", "generic_tsmom28", "v17_wkndliq_flag",
                     "generic_session_asia", "cng4_rev24_leg_BTCUSDT",
                     "cng4_mom168_leg_BTCUSDT", "cng4_tsmom28_leg_BTCUSDT",
                     "cng4_rv24_stress_leg_BTCUSDT", "cng4_pair_spread_trend_lag1",
                     "cng4_sham_randomized_event_time", "cng4_stale_beta_control",
                     "cng4_x3_tape_proxy_leg_BTCUSDT",
                     "cng4_taker_imbalance_leg_BTCUSDT", "cng4_corr_decay_24",
                     "cng4_corr_decay_72", "cng4_lead_lag_m1", "cng4_lead_lag_p2",
                     "cng4_dvol_shock_pair_residual", "cng4_neighbour_z2_freq"):
        assert required in names, required
    assert inv["rho_bar"] == 0.20 and inv["min_pairs"] == 8


def test_run_main_refuses_tampered_inventory_before_lock(monkeypatch, tmp_path):
    tampered = tmp_path / "shadow_inventory.json"
    payload = json.loads(D.INVENTORY_PATH.read_text())
    payload["rho_bar"] = 0.99  # any mutation must be caught
    tampered.write_text(json.dumps(payload))
    monkeypatch.setattr(D, "INVENTORY_PATH", tampered)
    import io, contextlib
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = D.run_main()
    assert rc == 2
    assert "hash mismatch" in err.getvalue()


def test_run_main_refuses_absent_inventory(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "INVENTORY_PATH", tmp_path / "absent.json")
    import io, contextlib
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = D.run_main()
    assert rc == 2
    assert "absent" in err.getvalue()


# --------------------------------------------------------------------------- #
# 5. venue controls fail-closed
# --------------------------------------------------------------------------- #

def test_venue_controls_fail_closed():
    venue = D.venue_status()
    assert venue["complete_coverage_utc_days"] < D.VENUE_FLOOR_DAYS
    assert venue["floor_met"] is False
    assert venue["collectors_first_process_utc"] is not None
    for pname, entry in venue["per_pair"].items():
        assert entry["status"] == "NOT_RUN_COVERAGE_INSUFFICIENT"
        assert entry["fail_closed"] is True
        assert len(entry["controls"]) == 6


# --------------------------------------------------------------------------- #
# 6. committed verdict consistency (artifact of the heavy-lock run)
# --------------------------------------------------------------------------- #

def test_committed_verdict_consistent(tmp_path):
    verdict_path = D.D2_DIR / "d2_verdict.json"
    if not verdict_path.is_file():
        pytest.skip("d2_verdict.json not yet generated")
    v = json.loads(verdict_path.read_text())
    assert v["cycle_id"] == "CRYPTO-NG4" and v["role"] == "A8-D2"
    assert v["base_head"] == "950f3bfdc9a5b45993d09107b99c744d2c6ac726"
    assert v["method"]["rho_bar"] == 0.20
    assert v["inventory"]["sha256"] == D.SHADOW_INVENTORY_SHA256
    # cycle-state declaration rule
    if v["r0_ancestry_vetoes_fired"]:
        assert v["cycle_state"] == "ANCESTRY_VETO_CLOSE"
        assert v["verdict"] == "ANCESTRY_VETO"
        for veto in v["r0_ancestry_vetoes_fired"]:
            assert veto["max_abs_rho"] > 0.20
            assert veto["margin_to_bar"] < 0
    else:
        assert v["cycle_state"] == "WAITING_PROSPECTIVE_COVERAGE"
        assert v["verdict"] == "WAITING_PROSPECTIVE_COVERAGE"
    # venue fail-closed regardless of path
    assert v["venue_controls"]["floor_met"] is False
    for entry in v["venue_controls"]["per_pair"].values():
        assert entry["status"] == "NOT_RUN_COVERAGE_INSUFFICIENT"
    # PnL ban
    blob = verdict_path.read_text()
    for banned in ("\"expectancy\"", "\"sharpe\"", "\"profit_factor\"",
                   "\"pnl\"", "\"net_pnl\""):
        assert banned not in blob, banned
