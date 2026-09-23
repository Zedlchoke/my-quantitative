"""PSV1 lane_btc_h4 — signal-event counting dry-run (plan §11).

Counts ONLY: entry events, exit events by reason, hold-time distributions,
trades per era x fold, funding-boundary exposures, churn counters.
NO per-trade returns, gross/net, equity, profit factor or drawdown exists in
this lane (outcome-blind law, plan §7.3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import config
from .census import episodes


@dataclass
class BookSpec:
    name: str
    phase: str                       # gate phase
    trigger: str                     # "phase_start" or "donchian_breakout"
    donch_entry: int = config.DONCH_ENTRY
    donch_stop: int = config.DONCH_STOP
    exit_buffer: int = config.EXIT_BUFFER_BARS
    min_hold: int = config.MIN_HOLD_BARS
    max_hold: int = config.MAX_HOLD_BARS
    direction: int = 1               # long


def gate_active(labels: np.ndarray, phase: str, buffer_bars: int) -> np.ndarray:
    """Causal hysteresis: the phase episode persists while a phase label
    occurred within the last `buffer_bars` bars (current bar inclusive)."""
    hit = labels == phase
    out = hit.copy()
    for k in range(1, buffer_bars):
        out[k:] |= hit[:-k]
    return out


def run_book(labels: np.ndarray, close: np.ndarray,
             spec: BookSpec, fold_ids: np.ndarray) -> dict:
    """Event-only state machine. Decisions at close t, fills at open t+1.

    Fold law: fold ends force-flat — an exit forced by a fold boundary is
    booked AT the last bar of the fold (no fill spills into the next fold);
    entries whose fill bar would cross a fold boundary are skipped.

    No price difference is ever multiplied into any result: this function
    contains no strategy-returns path (outcome-blind law, plan §7.3).
    """
    n = len(labels)
    gate = gate_active(labels, spec.phase, spec.exit_buffer)

    # Donchian references use PRIOR bars only (t-entry .. t-1): causal.
    hh = np.full(n, np.nan)
    ll = np.full(n, np.nan)
    for t in range(n):
        if t >= spec.donch_entry:
            hh[t] = close[t - spec.donch_entry: t].max()
        if t >= spec.donch_stop:
            ll[t] = close[t - spec.donch_stop: t].min()

    position = 0  # 0 flat, +1 long
    bars_held = 0
    fill_idx = -1
    entries: list[dict] = []
    exits: list[dict] = []
    trades_per_fold: dict = {}

    def fold_of(i: int):
        return fold_ids[i]

    for t in range(n):
        if position == 0:
            trig = False
            if gate[t]:
                if spec.trigger == "phase_start":
                    at_start = (labels[t] == spec.phase) and (t == 0 or not gate[t - 1])
                    trig = bool(at_start)
                elif spec.trigger == "donchian_breakout":
                    trig = bool(np.isfinite(hh[t]) and close[t] > hh[t])
            if trig and t + 1 < n and fold_of(t + 1) == fold_of(t):
                position = 1
                fill_idx = t + 1
                bars_held = 0
                entries.append({"decision_bar": t, "fill_bar": t + 1,
                                "reason": "ENTRY", "fold": fold_of(t)})
        else:
            bars_held += 1
            exit_reason = None
            if spec.trigger == "donchian_breakout" and np.isfinite(ll[t]) and close[t] < ll[t]:
                exit_reason = "DONCHIAN_STOP"
            if exit_reason is None and not gate[t]:
                exit_reason = "GATE_INACTIVE"
            if exit_reason is None and bars_held >= spec.max_hold:
                exit_reason = "MAX_HOLD"
            if exit_reason is not None and bars_held < spec.min_hold:
                exit_reason = None  # churn law: min-dwell suppresses exit triggers
            last_bar_of_fold = (t + 1 >= n) or (fold_of(t + 1) != fold_of(t))
            if exit_reason is None and last_bar_of_fold:
                exit_reason = "FOLD_END"
            if exit_reason is not None:
                # fold law: no fill spills across a fold boundary; exits at a
                # fold's last bar are booked AT that bar (force-flat).
                exit_fill = t if last_bar_of_fold else t + 1
                exits.append({"decision_bar": t, "fill_bar": exit_fill,
                              "reason": exit_reason, "fold": fold_of(t),
                              "bars_held": bars_held})
                trades_per_fold.setdefault(fold_of(t), []).append(
                    {"entry_bar": fill_idx, "exit_bar": exit_fill,
                     "bars_held": bars_held, "exit_reason": exit_reason})
                position = 0
                fill_idx = -1
    if position == 1:  # defensive; the t >= n-1 FOLD_END path should already close it
        exits.append({"decision_bar": n - 1, "fill_bar": n - 1,
                      "reason": "SERIES_END_OPEN", "fold": fold_of(n - 1),
                      "bars_held": bars_held})

    hold_bars = [tr["bars_held"] for trs in trades_per_fold.values() for tr in trs]
    return {
        "book": spec.name,
        "phase": spec.phase,
        "trigger": spec.trigger,
        "n_entries": len(entries),
        "n_exits": len(exits),
        "exit_reason_counts": _count_reasons(exits),
        "n_trades": sum(len(v) for v in trades_per_fold.values()),
        "trades_per_fold": {k: len(v) for k, v in trades_per_fold.items()},
        "hold_bars": hold_bars,
        "hold_stats": _dwell(hold_bars),
        "open_at_series_end": position == 1,
        "_trade_records": trades_per_fold,
        "_entry_records": entries,
    }


def _count_reasons(exits: list[dict]) -> dict:
    out: dict[str, int] = {}
    for e in exits:
        out[e["reason"]] = out.get(e["reason"], 0) + 1
    return out


def _dwell(bars: list[int]) -> dict:
    if not bars:
        return {"n": 0, "min": None, "median": None, "max": None}
    a = np.asarray(bars)
    return {"n": int(a.size), "min": int(a.min()), "median": float(np.median(a)),
            "max": int(a.max())}


def funding_boundary_count(fill_ms: int, exit_ms: int) -> int:
    """8h funding boundaries b (00/08/16 UTC) with fill_ms <= b < exit_ms.

    Frozen convention: a position held AT a boundary instant pays that
    boundary's funding (entering exactly at the boundary instant counts).
    """
    step = config.FUNDING_INTERVAL_H * 3600 * 1000
    if exit_ms <= fill_ms:
        return 0
    first = ((fill_ms + step - 1) // step) * step  # first boundary >= fill
    if exit_ms <= first:
        return 0
    return int(-(-(exit_ms - first) // step))


def churn_sanity(labels: np.ndarray, book: dict, spec: BookSpec) -> dict:
    """Churn-law counters (plan §11).

    - flicker_fills: fills attributable to same-direction label noise while the
      gate never went inactive — STRUCTURALLY ZERO: an exit (other than
      DONCHIAN_STOP/MAX_HOLD) requires gate_active to turn False, which by
      construction requires `exit_buffer` consecutive bars without a phase
      label; a within-buffer label flicker keeps the gate ON and cannot fill.
    - reentries_within_buffer_of_exit: exits followed by a re-entry decision
      within `exit_buffer` bars. These are NOT noise fills: the gate was fully
      inactive (a genuine episode end per the frozen rule) before relapsing.
      Reported as a disclosed cadence statistic.
    """
    trans = len(episodes(np.asarray(labels) == spec.phase))
    switches = book["n_trades"]
    reentries = 0
    recs = [(f, tr) for f, trs in book["_trade_records"].items() for tr in trs]
    recs.sort(key=lambda x: x[1]["entry_bar"])
    for i in range(len(recs) - 1):
        xb = recs[i][1]["exit_bar"]
        eb_next = recs[i + 1][1]["entry_bar"]
        if 0 < eb_next - xb <= spec.exit_buffer:
            reentries += 1
    return {
        "phase_transitions": int(trans),
        "position_switches": int(switches),
        "switches_per_phase_transition": float(switches) / max(1, trans),
        "flicker_fills_structural_zero": 0,
        "reentries_within_buffer_of_exit": int(reentries),
        "noop_law": ("same-direction label noise inside the gate buffer cannot fill: "
                     "exit requires exit_buffer consecutive non-phase bars; re-entry "
                     "requires a fresh entry event"),
    }
