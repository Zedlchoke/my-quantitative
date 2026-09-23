"""A2 unit tests — mechanism attribution (hermetic: no V2 reads, no I/O).

Covers (dispatch minimum):
- synthetic-ledger reconciliation (recompute vs stored totals; PASS + FAIL
  detection);
- frozen cause-classification rule (fold_flat -> fold_force_flat;
  stop/strategy_exit -> strategy_native; regime_off with same-direction
  resume -> unnecessary_close_reopen; regime_off with opposite direction ->
  regime_switch);
- counterfactual target transforms on tiny synthetic series (no-op hold,
  transition-buffer delay, minimum hold).

Full-cell runs over the V2 corpus live in tools/run_diagnostics.py
attribution (their runtime is minutes and they need the read-only V2
worktree; they are deliberately NOT part of the unit suite).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1.attribution import (  # noqa: E402
    CAUSE_FOLD,
    CAUSE_NOOP,
    CAUSE_REGIME,
    CAUSE_STRATEGY,
    DISCLOSURE,
    RECON_TOL,
    classify_exit_reason,
    classify_regime_off,
    classify_trade,
    delay_labels,
    direction_of,
    min_hold_targets,
    noop_hold_same_direction,
    recompute_totals,
    reconcile_ledger,
    stored_engine_identity_ok,
)
from rsmv1.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT  # noqa: E402

P_H1 = 3_600_000_000_000  # 1 hour in ns


# ---------------------------------------------------------------------------
# synthetic ledger reconciliation
# ---------------------------------------------------------------------------


def _mk_trade(i: int, gross: float, fee: float, slip: float, funding: float) -> dict:
    return {
        "direction": 1,
        "entry_bar": i,
        "exit_bar": i + 3,
        "exit_reason": "strategy_exit",
        "gross_pnl": gross,
        "fees": fee,
        "slip": slip,
        "funding": funding,
        "net_pnl": gross - fee - slip - funding,
        "fold_id": 0,
    }


def _synthetic_ledger() -> dict:
    trades = [
        _mk_trade(0, 100.0, 1.0, 0.5, 0.0),
        _mk_trade(5, -40.0, 1.0, 0.5, 0.25),
        _mk_trade(9, 12.5, 1.0, 0.5, 0.0),
    ]
    totals = {
        "trades": len(trades),
        "gross_pnl": sum(t["gross_pnl"] for t in trades),
        "costs_fee": sum(t["fees"] for t in trades),
        "costs_slip": sum(t["slip"] for t in trades),
        "costs_funding": sum(t["funding"] for t in trades),
        "net_pnl": sum(t["net_pnl"] for t in trades),
    }
    net = totals["net_pnl"]
    return {
        "trades": trades,
        "totals": totals,
        "equity": [100_000.0, 100_000.0, 100_000.0 + net],
        "fold_net_pnl": [net],
    }


def test_recompute_totals_synthetic():
    led = _synthetic_ledger()
    rec = recompute_totals(led["trades"])
    assert rec["trades"] == 3
    assert abs(rec["gross"] - 72.5) < RECON_TOL
    assert abs(rec["fee"] - 3.0) < RECON_TOL
    assert abs(rec["slip"] - 1.5) < RECON_TOL
    assert abs(rec["funding"] - 0.25) < RECON_TOL
    assert abs(rec["net"] - 67.75) < RECON_TOL


def test_reconcile_ledger_pass_and_fail_detection():
    led = _synthetic_ledger()
    ok, rec, stored = reconcile_ledger(led)
    assert ok
    assert stored["net"] == rec["net"]
    # any perturbation of a stored component must be detected (never adjusted)
    for key, field in (
        ("gross_pnl", "gross"),
        ("costs_fee", "fee"),
        ("costs_slip", "slip"),
        ("costs_funding", "funding"),
        ("net_pnl", "net"),
    ):
        bad = _synthetic_ledger()
        bad["totals"][key] += 1e-3  # above RECON_TOL = 1e-6
        ok_bad, _, _ = reconcile_ledger(bad)
        assert not ok_bad, f"perturbed {field} not detected"
    bad_count = _synthetic_ledger()
    bad_count["totals"]["trades"] = 2
    ok_count, _, _ = reconcile_ledger(bad_count)
    assert not ok_count


def test_stored_engine_identity_synthetic():
    led = _synthetic_ledger()
    ok, gaps = stored_engine_identity_ok(led)
    assert ok
    assert abs(gaps["identity_gap"]) < RECON_TOL
    assert abs(gaps["fold_sum_gap"]) < 1e-9
    bad = _synthetic_ledger()
    bad["equity"][-1] += 0.01
    ok_bad, _ = stored_engine_identity_ok(bad)
    assert not ok_bad


# ---------------------------------------------------------------------------
# frozen cause-classification rule
# ---------------------------------------------------------------------------


def test_classify_exit_reason_branches():
    assert classify_exit_reason("fold_flat") == CAUSE_FOLD
    assert classify_exit_reason("stop") == CAUSE_STRATEGY
    assert classify_exit_reason("strategy_exit") == CAUSE_STRATEGY
    assert classify_exit_reason("regime_off") == "regime_off"
    assert classify_exit_reason("mystery") == "unknown_reason"


def _regime_off_trade(direction: int, exit_bar: int, fold_id: int = 0) -> dict:
    return {
        "direction": direction,
        "entry_bar": exit_bar - 4,
        "exit_bar": exit_bar,
        "exit_reason": "regime_off",
        "fold_id": fold_id,
    }


def _entry_trade(direction: int, entry_bar: int, fold_id: int = 0) -> dict:
    return {
        "direction": direction,
        "entry_bar": entry_bar,
        "exit_bar": entry_bar + 4,
        "exit_reason": "strategy_exit",
        "fold_id": fold_id,
    }


def test_regime_off_same_direction_resume_is_unnecessary_close_reopen():
    # long closed by regime_off at bar 10; target stays long/flat (never
    # short) and the next entry (same fold) is long again -> the close/reopen
    # was avoidable churn.
    t = _regime_off_trade(1, 10)
    nxt = _entry_trade(1, 14)
    dirs = [1] * 10 + [0, 0, 0, 1] + [1] * 4  # bars 10..13 flat, 14 long
    assert classify_regime_off(t, nxt, dirs) == CAUSE_NOOP
    # same via the full per-trade path
    assert classify_trade(t, 0, [t, nxt], dirs) == CAUSE_NOOP


def test_regime_off_opposite_direction_is_regime_switch():
    # next entry is the OPPOSITE direction -> genuine regime switch
    t = _regime_off_trade(1, 10)
    nxt = _entry_trade(-1, 14)
    dirs = [1] * 10 + [0, -1, -1, -1] + [-1] * 4
    assert classify_regime_off(t, nxt, dirs) == CAUSE_REGIME
    # same direction resumes, but the target mapped OPPOSITE in between ->
    # regime_switch (the frozen rule's intervening-opposite clause)
    nxt_same = _entry_trade(1, 14)
    dirs_whipsaw = [1] * 10 + [0, -1, 0, 1] + [1] * 4
    assert classify_regime_off(t, nxt_same, dirs_whipsaw) == CAUSE_REGIME


def test_regime_off_without_same_fold_entry_is_regime_switch():
    t = _regime_off_trade(1, 10)
    # no next entry at all
    assert classify_regime_off(t, None, [1] * 20) == CAUSE_REGIME
    # next entry lives in a DIFFERENT fold (position never re-opened here)
    nxt_other_fold = _entry_trade(1, 14, fold_id=1)
    assert classify_regime_off(t, nxt_other_fold, [1] * 20) == CAUSE_REGIME
    # next entry flipped direction
    nxt_rev = _entry_trade(-1, 14)
    assert classify_regime_off(t, nxt_rev, [1] * 20) == CAUSE_REGIME


def test_stop_and_strategy_exit_are_always_strategy_native():
    # the frozen rule: stop/strategy_exit -> strategy_native with NO
    # predecessor-based reclassification (even right after a regime_switch)
    stop_t = {
        "direction": 1,
        "entry_bar": 20,
        "exit_bar": 24,
        "exit_reason": "stop",
        "fold_id": 0,
    }
    exit_t = dict(stop_t, exit_reason="strategy_exit")
    regime_t = _regime_off_trade(1, 10)
    nxt = _entry_trade(1, 14)
    # governing target maps OPPOSITE inside the intervening window -> the
    # regime_off close is a genuine regime_switch (not unnecessary churn)
    dirs = [1] * 11 + [-1] * 17
    tr = [regime_t, nxt, stop_t, exit_t]
    assert classify_trade(regime_t, 0, tr, dirs) == CAUSE_REGIME
    assert classify_trade(stop_t, 2, tr, dirs) == CAUSE_STRATEGY
    assert classify_trade(exit_t, 3, tr, dirs) == CAUSE_STRATEGY
    assert classify_exit_reason("fold_flat") == CAUSE_FOLD


def test_direction_of():
    assert direction_of(TREND_LONG) == 1
    assert direction_of(MR_LONG) == 1
    assert direction_of(TREND_SHORT) == -1
    assert direction_of(FLAT) == 0
    assert direction_of(None) == 0


# ---------------------------------------------------------------------------
# counterfactual target transforms (tiny synthetic series)
# ---------------------------------------------------------------------------


def test_noop_hold_same_direction_transform():
    base = [
        TREND_LONG,
        MR_LONG,
        MR_LONG,
        FLAT,
        TREND_LONG,
        TREND_LONG,
        TREND_SHORT,
        None,
    ]
    fixed = noop_hold_same_direction(base)
    # same-direction strategy-string churn (TL -> MR) suppressed; direction
    # changes (to flat, to short) honored; leading/trailing Nones untouched
    assert fixed == [
        TREND_LONG,
        TREND_LONG,
        TREND_LONG,
        FLAT,
        TREND_LONG,
        TREND_LONG,
        TREND_SHORT,
        None,
    ]
    # flat -> flat is not a direction change
    assert noop_hold_same_direction([FLAT, FLAT, TREND_LONG]) == [
        FLAT,
        FLAT,
        TREND_LONG,
    ]
    # identity when no same-direction change exists
    assert noop_hold_same_direction([TREND_LONG, FLAT, TREND_SHORT]) == [
        TREND_LONG,
        FLAT,
        TREND_SHORT,
    ]


def test_delay_labels_buffer_shift():
    persisted = ["A", "A", "B", "B", "A"]
    assert delay_labels(persisted, 0) == persisted
    assert delay_labels(persisted, 1) == ["A", "A", "A", "B", "B"]
    assert delay_labels(persisted, 2) == ["A", "A", "A", "A", "B"]
    # switch at index 2 acts only at index 2+k (old label honored k bars late)
    one = delay_labels(persisted, 1)
    assert one[2] == "A" and one[3] == "B"
    # over-long delay degrades to the initial label everywhere
    assert delay_labels(persisted, 99) == ["A"] * 5
    assert len(delay_labels(persisted, 3)) == 5


def test_min_hold_transform_vetoes_flat_inside_window():
    ts = [i * P_H1 for i in range(6)]
    base = [TREND_LONG, FLAT, TREND_LONG, FLAT, FLAT, TREND_SHORT]
    # hold=2 regime bars: the flat at bar 1 (1 bar after entry) is vetoed;
    # flats at bars 3-4 (>= 2 bars after entry) are honored; the later short
    # is a direction change and always honored.
    out = min_hold_targets(base, ts, 2 * P_H1)
    assert out == [
        TREND_LONG,
        TREND_LONG,
        TREND_LONG,
        FLAT,
        FLAT,
        TREND_SHORT,
    ]


def test_min_hold_transform_honors_reversal_immediately():
    ts = [0, P_H1, 2 * P_H1, 3 * P_H1]
    base = [TREND_LONG, TREND_SHORT, TREND_SHORT, FLAT]
    # opposite direction inside the window is honored immediately (and
    # re-anchors the hold clock at the short entry) — so the flat at bar 3,
    # only 2 bars after the short, is vetoed by the 8-bar hold
    out = min_hold_targets(base, ts, 8 * P_H1)
    assert out == [TREND_LONG, TREND_SHORT, TREND_SHORT, TREND_SHORT]
    # with the flat beyond the re-anchored window it is honored again
    ts2 = [0, P_H1, 2 * P_H1, 10 * P_H1]
    out2 = min_hold_targets(base, ts2, 8 * P_H1)
    assert out2 == [TREND_LONG, TREND_SHORT, TREND_SHORT, FLAT]


def test_min_hold_transform_same_direction_string_change():
    ts = [0, P_H1, 2 * P_H1, 3 * P_H1, 4 * P_H1]
    base = [TREND_LONG, MR_LONG, MR_LONG, MR_LONG, TREND_LONG]
    # hold=3: the TL -> MR string change at bar 1 (inside window) is ignored;
    # after the window the target string is followed again
    out = min_hold_targets(base, ts, 3 * P_H1)
    assert out == [
        TREND_LONG,
        TREND_LONG,
        TREND_LONG,
        MR_LONG,
        TREND_LONG,
    ]
    # flat right after entry re-arms once accepted; a later long re-anchors
    ts2 = [0, P_H1, 2 * P_H1, 3 * P_H1]
    base2 = [TREND_LONG, FLAT, TREND_LONG, FLAT]
    out2 = min_hold_targets(base2, ts2, 2 * P_H1)
    assert out2 == [TREND_LONG, TREND_LONG, TREND_LONG, FLAT]


def test_min_hold_handles_leading_none_and_initial_flat():
    ts = [0, P_H1, 2 * P_H1, 3 * P_H1]
    base = [None, FLAT, TREND_LONG, FLAT]
    out = min_hold_targets(base, ts, 4 * P_H1)
    assert out == [None, FLAT, TREND_LONG, TREND_LONG]


def test_disclosure_string_present():
    assert "Nothing here is a validated configuration" in DISCLOSURE
    assert "failure mechanism only" in DISCLOSURE
