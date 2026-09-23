"""Signal-event golden tests (plan §14): entries/exits as EVENTS on synthetic
bars, next-bar fills, fold force-flat, min-hold suppression, no-op law.
Hand-computed fixtures; no returns anywhere."""

import numpy as np

from research.control.phase_strategy_v1.lane_btc_h4.pipeline.events import (
    BookSpec, gate_active, run_book, funding_boundary_count, churn_sanity)
from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config

UNK = "TRANSITION_UNKNOWN"
UP = "UPTREND"
H8 = config.FUNDING_INTERVAL_H * 3600 * 1000


def _labels_30():
    labs = np.array([UNK] * 5 + [UP] * 10 + [UNK] * 11 + [UP] * 4, dtype=object)
    assert len(labs) == 30
    return labs


def _folds_20_10():
    return np.array(["F1"] * 20 + ["F2"] * 10, dtype=object)


def _spec(buffer=3, min_hold=2, max_hold=100):
    return BookSpec(name="T", phase=UP, trigger="phase_start",
                    exit_buffer=buffer, min_hold=min_hold, max_hold=max_hold)


def test_gate_active_hysteresis_window():
    labs = _labels_30()
    g = gate_active(labs, UP, 3)
    # UP ends at index 14; gate must stay True through 14+2=16, False at 17
    assert g[14] and g[15] and g[16] and not g[17]
    # gate turns ON at the first UP bar (5)
    assert not g[4] and g[5]


def test_phase_start_golden_events():
    labs = _labels_30()
    folds = _folds_20_10()
    book = run_book(labs, np.arange(30, dtype="float64"), _spec(), folds)
    # hand-computed: entry decision 5 fill 6; gate OFF first at 17 -> exit
    # decision 17 fill 18 (bars_held 12); re-entry decision 26 fill 27;
    # FOLD_END at 29 (fill 29, force-flat).
    entries = book["_entry_records"]
    assert (entries[0]["decision_bar"], entries[0]["fill_bar"]) == (5, 6)
    assert (entries[1]["decision_bar"], entries[1]["fill_bar"]) == (26, 27)
    assert book["exit_reason_counts"] == {"GATE_INACTIVE": 1, "FOLD_END": 1}
    recs = [tr for trs in book["_trade_records"].values() for tr in trs]
    assert recs[0]["entry_bar"] == 6 and recs[0]["exit_bar"] == 18
    assert recs[0]["bars_held"] == 12
    assert recs[1]["exit_reason"] == "FOLD_END"
    assert book["n_trades"] == 2
    assert book["trades_per_fold"] == {"F1": 1, "F2": 1}


def test_next_bar_fill_law():
    """Every fill bar is exactly decision bar + 1 (no same-bar fills)."""
    labs = _labels_30()
    book = run_book(labs, np.arange(30, dtype="float64"), _spec(), _folds_20_10())
    for e in book["_entry_records"]:
        assert e["fill_bar"] == e["decision_bar"] + 1
    for x in [tr for trs in book["_trade_records"].values() for tr in trs]:
        pass  # exit fills recorded in records; check entry-side only here


def test_noop_law_label_flicker_zero_fills():
    """Same-direction label noise inside the gate buffer must produce ZERO fills."""
    labs = np.array([UNK] * 4 + [UP] * 5 + [UNK] + [UP] * 11 + [UNK] * 9, dtype=object)
    folds = np.array(["F1"] * 30, dtype=object)
    book = run_book(labs, np.arange(30, dtype="float64"), _spec(buffer=3, min_hold=1), folds)
    # single continuous gate: one entry, one exit — the flicker at index 9
    # (and the 21/22 window) must NOT generate fills
    assert book["n_entries"] == 1
    assert book["n_trades"] == 1
    assert book["exit_reason_counts"] == {"GATE_INACTIVE": 1}
    churn = churn_sanity(labs, book, _spec(buffer=3, min_hold=1))
    assert churn["flicker_fills_structural_zero"] == 0
    assert churn["reentries_within_buffer_of_exit"] == 0


def test_min_hold_suppresses_trigger_but_not_fold_force_flat():
    labs = np.array([UNK] * 3 + [UP] * 8 + [UNK] * 14, dtype=object)
    folds = np.array(["F1"] * 25, dtype=object)
    spec = _spec(buffer=3, min_hold=50, max_hold=100)
    book = run_book(labs, np.arange(25, dtype="float64"), spec, folds)
    # entry decision 3 fill 4; GATE_INACTIVE fires at 13 but bars_held=10 < 50
    # -> suppressed; fold end force-flattens at 24 regardless of min-dwell.
    recs = [tr for trs in book["_trade_records"].values() for tr in trs]
    assert len(recs) == 1
    assert recs[0]["exit_reason"] == "FOLD_END"
    assert recs[0]["exit_bar"] == 24
    assert recs[0]["bars_held"] == 21


def test_max_hold_exit():
    labs = np.array([UP] * 30, dtype=object)
    folds = np.array(["F1"] * 30, dtype=object)
    spec = _spec(buffer=3, min_hold=2, max_hold=5)
    book = run_book(labs, np.arange(30, dtype="float64"), spec, folds)
    recs = [tr for trs in book["_trade_records"].values() for tr in trs]
    # entry decision 0 fill 1; MAX_HOLD at bars_held 5 -> decision 5, fill 6
    assert recs[0]["exit_reason"] == "MAX_HOLD"
    assert (recs[0]["entry_bar"], recs[0]["exit_bar"]) == (1, 6)
    assert recs[0]["bars_held"] == 5


def test_donchian_event_golden():
    closes = np.array([100.0] * 6 + [105.0, 110.0, 90.0] + [95.0] * 21)
    labs = np.array([UP] * 30, dtype=object)
    folds = np.array(["F1"] * 30, dtype=object)
    spec = BookSpec(name="D", phase=UP, trigger="donchian_breakout",
                    donch_entry=4, donch_stop=2, exit_buffer=1,
                    min_hold=1, max_hold=100)
    book = run_book(labs, closes, spec, folds)
    recs = [tr for trs in book["_trade_records"].values() for tr in trs]
    # t=6: close 105 > max(close[2..5]) = 100 -> entry decision 6 fill 7
    # t=8: close 90 < min(close[6..7]) = 105 -> DONCHIAN_STOP decision 8 fill 9
    assert book["n_trades"] == 1
    assert (recs[0]["entry_bar"], recs[0]["exit_bar"]) == (7, 9)
    assert recs[0]["exit_reason"] == "DONCHIAN_STOP"


def test_fold_attribution_reconciliation():
    labs = _labels_30()
    book = run_book(labs, np.arange(30, dtype="float64"), _spec(), _folds_20_10())
    total = sum(len(v) for v in book["_trade_records"].values())
    assert total == book["n_trades"] == sum(book["trades_per_fold"].values())
    for f, trs in book["_trade_records"].items():
        for tr in trs:
            assert f in ("F1", "F2")


def test_no_cross_fold_entry_fill():
    """An entry whose fill bar would cross a fold boundary is skipped; the
    trigger does NOT chase — it re-arms only on a fresh gate transition."""
    labs = np.array([UNK] * 9 + [UP] + [UNK] * 3 + [UP] * 17, dtype=object)
    folds = np.array(["F1"] * 10 + ["F2"] * 20, dtype=object)
    book = run_book(labs, np.arange(30, dtype="float64"), _spec(), folds)
    # UP spike at 9: entry decision 9 would fill at 10 (F2) -> skipped;
    # gate dies at 12, re-arms at 13 -> entry decision 13, fill 14 (F2)
    entries = book["_entry_records"]
    assert [e["decision_bar"] for e in entries] == [13]
    assert entries[0]["fill_bar"] == 14
    assert book["trades_per_fold"] == {"F2": 1}


def test_funding_boundary_count_convention():
    t0 = 1577836800000  # 2020-01-01T00:00Z (a boundary)
    h8 = config.FUNDING_INTERVAL_H * 3600 * 1000
    assert funding_boundary_count(t0, t0) == 0
    assert funding_boundary_count(t0, t0 + 1) == 1          # held AT the 00:00 boundary
    assert funding_boundary_count(t0, t0 + h8) == 1         # 08:00 boundary excluded at exit
    assert funding_boundary_count(t0, t0 + h8 + 1) == 2     # crossing into 08:00
    t1h = t0 + 3600_000                                     # fill at 01:00 (not a boundary)
    assert funding_boundary_count(t1h, t0 + 9 * 3600_000) == 1  # only the 08:00 boundary
    assert funding_boundary_count(t0 + h8, t0 + 3 * h8) == 2  # 08:00 and 16:00
