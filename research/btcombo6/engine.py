"""BTC-COMBO6 event engine: per-leg backtests, baselines, metrics, verdicts.

Execution law (plan §1, frozen):
- Signals evaluated in ts order on completed bars only (no lookahead):
  a decision at decision_ts t fills at the FIRST 5m bar with open_time >=
  t + 5min; if that bar is absent the fill defers to the next present 5m bar.
- If the fill bar's open_time >= current fold end: entry dropped (signal
  expires at the fold boundary).
- Long-only, max 1 position per leg; signals arriving while LONG are
  discarded (a later entry needs a fresh state-change while FLAT).
- While LONG, from the FILL bar onward (inclusive): SL checked before TP in
  the same bar (pessimistic); SL gap-through exits at min(SL level, bar
  open); TP fills exactly at the TP level.
- Force-flat at the first 5m bar with open_time >= fold_end (exit at its
  open, fee charged), attributed to the fold being closed. The FINAL fold's
  boundary is the EVAL wall: sealed-tail bars are never evaluated, so the
  final force-flat is priced at the last in-window 5m close (disclosed
  interpretation; sealed-tail law + FOLD ERRATUM amendment).
- Funding: measured events (8h slots), cash += -(rate x 10000) for every
  event ts in (fill_ts, exit_ts]; signed, unstressed.
- Evaluation is hard-capped at eval_end: no trade, fill or exposure may
  carry a ts >= eval_end (sealed tail loaded and digested but never used).

A position still open when the panel itself ends before any fold boundary is
left OPEN (no synthetic trade record; marked equity only) — this preserves
the truncation-replay prefix law.
"""
from __future__ import annotations

from bisect import bisect_right

import numpy as np
import pandas as pd

from . import spec

_NS5 = 300_000_000_000  # 5 minutes in ns


def _ns(ts: pd.Series) -> np.ndarray:
    return ts.to_numpy(dtype="datetime64[ns]").astype("int64")


def _utc_ts(ns_value: int) -> pd.Timestamp:
    return pd.Timestamp(ns_value, unit="ns", tz="UTC")


def _dt_index(t: np.ndarray) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(t, unit="ns", utc=True), name="ts")


def _fold_index(ts_ns: int, fold_starts_ns: list[int]) -> int:
    return bisect_right(fold_starts_ns, ts_ns) - 1


def _cum_funding(f_ts: np.ndarray, f_rate: np.ndarray,
                 bar_close_ns: np.ndarray) -> np.ndarray:
    """GF[b] = cumulative signed rate of events with ts <= close of bar b."""
    cum = np.concatenate([[0.0], np.cumsum(f_rate)])
    pos = np.searchsorted(f_ts, bar_close_ns, side="right")
    return cum[pos]


def _funding_between(f_ts: np.ndarray, f_rate: np.ndarray, lo: int,
                     hi: int) -> float:
    """Sum of rates for events with lo < ts <= hi (ns epoch)."""
    a = int(np.searchsorted(f_ts, lo, side="right"))
    b = int(np.searchsorted(f_ts, hi, side="right"))
    return float(f_rate[a:b].sum()) if b > a else 0.0


# ---------------------------------------------------------------------------
# per-leg run
# ---------------------------------------------------------------------------

def run_leg(leg_id: str, leg_spec: dict, decisions: pd.DataFrame,
            m5: pd.DataFrame, folds: list[dict] | None = None,
            eval_end=None, stress: float = 1.0,
            funding: pd.DataFrame | None = None) -> dict:
    """Event backtest for one leg. Returns trades, equity, counters."""
    folds = folds if folds is not None else spec.FOLDS
    eval_end = pd.Timestamp(eval_end) if eval_end is not None else spec.EVAL_END
    start = folds[0]["start"]
    cps = spec.cost_per_side(stress)
    notional = spec.NOTIONAL_PER_ENTRY

    # Eval frame: bars with start <= open_time < eval_end (sealed wall).
    t_all = _ns(m5["ts"])
    lo = int(np.searchsorted(t_all, start.value, side="left"))
    hi = int(np.searchsorted(t_all, eval_end.value, side="left"))
    t = t_all[lo:hi]
    o = m5["o"].to_numpy(dtype=float)[lo:hi]
    h = m5["h"].to_numpy(dtype=float)[lo:hi]
    l = m5["l"].to_numpy(dtype=float)[lo:hi]
    c = m5["c"].to_numpy(dtype=float)[lo:hi]
    n = len(t)
    t_close = t + _NS5

    if funding is not None and len(funding):
        f_ts = _ns(funding["ts"])
        f_rate = funding["rate"].to_numpy(dtype=float)
    else:
        f_ts = np.empty(0, dtype="int64")
        f_rate = np.empty(0, dtype="float64")
    GF = _cum_funding(f_ts, f_rate, t_close) if n else np.empty(0)

    fold_starts_ns = [f["start"].value for f in folds]
    fold_end_ns = [f["end"].value for f in folds]

    dec = decisions
    mask = (dec["decision_ts"] >= start) & (dec["decision_ts"] < eval_end)
    dec = dec.loc[mask]
    dts = _ns(dec["decision_ts"])
    den = dec["enter"].to_numpy(dtype=bool)

    counters = {
        "decisions_seen": int(len(dts)),
        "enter_signals_seen": int(den.sum()),
        "entries_filled": 0,
        "entries_deferred": 0,
        "entries_expired_at_fold_boundary": 0,
        "entries_dropped_no_bar": 0,
        "signals_discarded_while_long": 0,
    }

    trades: list[dict] = []
    open_at_frame_end: dict | None = None
    flat_after = -1

    enter_positions = np.flatnonzero(den)
    for pos in enter_positions:
        ts_d = int(dts[pos])
        fold_i = _fold_index(ts_d, fold_starts_ns)
        target = ts_d + _NS5
        fi = int(np.searchsorted(t, target, side="left"))
        if fi >= n:
            counters["entries_dropped_no_bar"] += 1
            continue
        if t[fi] >= fold_end_ns[fold_i]:
            counters["entries_expired_at_fold_boundary"] += 1
            continue
        if fi <= flat_after:
            counters["signals_discarded_while_long"] += 1
            continue

        # Entry accepted: the fill happens here (counted now, even if the
        # position never closes before the frame ends).
        counters["entries_filled"] += 1
        if t[fi] > target:
            counters["entries_deferred"] += 1

        fill_px = float(o[fi])
        qty = notional / fill_px
        entry_fee = notional * cps
        fill_ts = int(t[fi])
        fe_end = fold_end_ns[fold_i]
        cap = int(np.searchsorted(t, fe_end, side="left"))  # first bar >= fold end
        sl_level = fill_px * (1.0 - leg_spec["sl"])
        tp_level = fill_px * (1.0 + leg_spec["tp"])

        exit_idx: int | None = None
        exit_px: float | None = None
        reason: str | None = None
        if cap > fi:
            seg = slice(fi, cap)
            hit_sl = np.flatnonzero(l[seg] <= sl_level)
            hit_tp = np.flatnonzero(h[seg] >= tp_level)
            if len(hit_sl) and (not len(hit_tp) or hit_sl[0] <= hit_tp[0]):
                j = int(hit_sl[0])              # SL first (pessimistic)
                exit_idx = fi + j
                bar_open = float(o[exit_idx])
                exit_px = min(sl_level, bar_open)   # gap-through worst fill
                reason = "SL_GAP" if bar_open < sl_level else "SL"
            elif len(hit_tp):
                j = int(hit_tp[0])
                exit_idx = fi + j
                exit_px = tp_level
                reason = "TP"
        if exit_idx is None:
            # No TP/SL before the fold boundary.
            if cap < n:
                exit_idx = cap                     # in-window boundary bar
                exit_px = float(o[cap])
                reason = "FORCE_FLAT"
            elif fe_end >= eval_end.value and hi < len(t_all):
                # Final-fold EVAL wall: boundary bars exist in the loaded
                # panel but are SEALED (never evaluated). Close at the last
                # in-window 5m close (disclosed; no sealed bytes touched).
                exit_idx = n - 1
                exit_px = float(c[n - 1])
                reason = "FORCE_FLAT"
            else:
                # Panel ends before the fold boundary: position stays OPEN
                # (no synthetic record); all later signals are discarded.
                counters["signals_discarded_while_long"] += int(den[pos + 1:].sum())
                open_at_frame_end = {
                    "leg": leg_id, "fold": folds[fold_i]["fold"],
                    "signal_ts": _utc_ts(ts_d), "fill_ts": _utc_ts(fill_ts),
                    "fill_px": fill_px, "qty": qty, "entry_fee": entry_fee,
                }
                break

        exit_ts = int(t[exit_idx])
        exit_fee = exit_px * qty * cps
        gross = qty * (exit_px - fill_px)
        funding_cost = _funding_between(f_ts, f_rate, fill_ts, exit_ts) * notional
        net = gross - entry_fee - exit_fee - funding_cost
        trades.append({
            "leg": leg_id, "fold": folds[fold_i]["fold"],
            "signal_ts": _utc_ts(ts_d), "fill_ts": _utc_ts(fill_ts),
            "fill_px": fill_px, "exit_ts": _utc_ts(exit_ts),
            "exit_px": exit_px, "exit_reason": reason, "qty": qty,
            "gross_pnl": gross, "entry_fee": entry_fee, "exit_fee": exit_fee,
            "fees": entry_fee + exit_fee, "funding": funding_cost,
            "net_pnl": net,
        })
        flat_after = exit_idx

    equity = _equity_curve(n, t, c, GF, trades, open_at_frame_end)
    return {
        "leg": leg_id, "stress": float(stress),
        "trades": trades, "equity": equity,
        "open_at_frame_end": open_at_frame_end,
        "counters": counters,
    }


def _equity_curve(n, t, c, GF, trades, open_at_frame_end) -> pd.Series:
    """Sleeve equity at every 5m bar close: 10000 + realized + open mark.

    Realized nets include fees and funding as cash events (entry fee at
    fill, funding at settlement, exit fee + gross at exit). Open marks use
    the 5m close and funding accrued through that bar's close."""
    eq = np.full(n, spec.SLEEVE_START_EQUITY, dtype=float)
    realized = 0.0
    cursor = 0
    for tr in trades:
        fi = int(np.searchsorted(t, tr["fill_ts"].value, side="left"))
        xi = int(np.searchsorted(t, tr["exit_ts"].value, side="left"))
        eq[cursor:fi] = spec.SLEEVE_START_EQUITY + realized
        gf_pre = GF[fi - 1] if fi > 0 else 0.0
        seg = slice(fi, xi)
        eq[seg] = (spec.SLEEVE_START_EQUITY + realized
                   + tr["qty"] * (c[seg] - tr["fill_px"])
                   - tr["entry_fee"] - (GF[seg] - gf_pre))
        realized += tr["net_pnl"]
        cursor = xi
    eq[cursor:] = spec.SLEEVE_START_EQUITY + realized
    if open_at_frame_end is not None:
        fi = int(np.searchsorted(t, open_at_frame_end["fill_ts"].value))
        gf_pre = GF[fi - 1] if fi > 0 else 0.0
        seg = slice(fi, n)
        eq[seg] = (spec.SLEEVE_START_EQUITY + realized
                   + open_at_frame_end["qty"] * (c[seg] - open_at_frame_end["fill_px"])
                   - open_at_frame_end["entry_fee"] - (GF[seg] - gf_pre))
    return pd.Series(eq, index=_dt_index(t))


# ---------------------------------------------------------------------------
# baselines
# ---------------------------------------------------------------------------

def always_long_baseline(m5: pd.DataFrame, folds: list[dict] | None = None,
                         eval_end=None, stress: float = 1.0,
                         funding: pd.DataFrame | None = None) -> dict:
    """B1 ALWAYS-LONG: $10k bought at the first 5m open >= F1 start, held to
    the EVAL wall. The wall exit is priced at the last in-window 5m close
    (sealed-tail bars are never evaluated — same law as the final-fold
    force-flat; disclosed). Same fee kernel + measured funding."""
    folds = folds if folds is not None else spec.FOLDS
    eval_end = pd.Timestamp(eval_end) if eval_end is not None else spec.EVAL_END
    start = folds[0]["start"]
    cps = spec.cost_per_side(stress)
    notional = spec.NOTIONAL_PER_ENTRY

    t_all = _ns(m5["ts"])
    lo = int(np.searchsorted(t_all, start.value, side="left"))
    hi = int(np.searchsorted(t_all, eval_end.value, side="left"))
    t = t_all[lo:hi]
    c = m5["c"].to_numpy(dtype=float)[lo:hi]
    o = m5["o"].to_numpy(dtype=float)
    n = len(t)
    if n == 0:
        return {"net_pnl": None, "open": False, "empty": True,
                "equity": pd.Series(dtype=float)}

    if funding is not None and len(funding):
        f_ts = _ns(funding["ts"])
        f_rate = funding["rate"].to_numpy(dtype=float)
    else:
        f_ts = np.empty(0, dtype="int64")
        f_rate = np.empty(0, dtype="float64")
    GF = _cum_funding(f_ts, f_rate, t + _NS5)

    fill_ts = int(t[0])
    fill_px = float(o[lo])
    qty = notional / fill_px
    entry_fee = notional * cps
    pre = _funding_between(f_ts, f_rate, 0, fill_ts)  # events <= fill_ts: uncharged
    eq = (spec.SLEEVE_START_EQUITY + qty * (c - fill_px) - entry_fee
          - (GF - pre))

    sealed_exists = hi < len(t_all)  # bars at/after eval_end exist but sealed
    if sealed_exists:
        exit_ts = int(t[n - 1])
        exit_px = float(c[n - 1])
        exit_fee = exit_px * qty * cps
        gross = qty * (exit_px - fill_px)
        funding_cost = _funding_between(f_ts, f_rate, fill_ts, exit_ts) * notional
        net = gross - entry_fee - exit_fee - funding_cost
        eq[n - 1] = spec.SLEEVE_START_EQUITY + net  # fully realized at wall
        open_flag = False
    else:
        gross = exit_fee = funding_cost = None
        net = None
        open_flag = True
    return {
        "net_pnl": net, "open": open_flag, "empty": False,
        "fill_ts": _utc_ts(fill_ts), "fill_px": fill_px,
        "entry_fee": entry_fee, "exit_fee": exit_fee,
        "gross_pnl": gross, "funding_cost": funding_cost,
        "qty": qty,
        "equity": pd.Series(eq, index=_dt_index(t)),
    }


def best_leg_prior_baseline(leg_fold_nets: dict[str, dict[str, float]],
                            fold_names: list[str] | None = None) -> dict:
    """B3 BEST-LEG-PRIOR: per fold hold the leg with the best cumulative net
    PnL over PRIOR folds only (ties -> lowest leg number; fold 0 -> LEG-1).
    Selection overlay, zero switching cost (disclosed)."""
    fold_names = fold_names if fold_names is not None else spec.FOLD_NAMES
    leg_ids = sorted(leg_fold_nets)  # LEG-1 < LEG-2 < ... lexicographic
    chosen: dict[str, str] = {}
    per_fold_net: dict[str, float] = {}
    for i, fname in enumerate(fold_names):
        if i == 0:
            pick = leg_ids[0]
        else:
            best_cum, pick = None, None
            for leg in leg_ids:  # ascending => ties keep lowest leg number
                cum = float(sum(leg_fold_nets[leg][fj]
                                for fj in fold_names[:i]))
                if best_cum is None or cum > best_cum:
                    best_cum, pick = cum, leg
        chosen[fname] = pick
        per_fold_net[fname] = float(leg_fold_nets[pick][fname])
    return {
        "chosen_per_fold": chosen,
        "per_fold_nets": per_fold_net,
        "total_net": float(sum(per_fold_net.values())),
        "disclosure": "selection overlay on prior-fold cumulative net PnL; "
                      "zero switching cost",
    }


# ---------------------------------------------------------------------------
# metrics + verdict bars (pure functions of plain dicts)
# ---------------------------------------------------------------------------

def metrics_from(trades: list[dict], equity: pd.Series,
                 start_capital: float, fold_names: list[str] | None = None) -> dict:
    fold_names = fold_names if fold_names is not None else spec.FOLD_NAMES
    net = float(sum(tr["net_pnl"] for tr in trades))
    wins = [tr["net_pnl"] for tr in trades if tr["net_pnl"] > 0]
    losses = [tr["net_pnl"] for tr in trades if tr["net_pnl"] < 0]
    loss_sum = float(sum(losses))
    if loss_sum != 0.0:
        pf, pf_lossless = float(sum(wins) / abs(loss_sum)), False
    elif wins:
        pf, pf_lossless = None, True
    else:
        pf, pf_lossless = None, False
    per_fold = {fn: {"trades": 0, "net_pnl": 0.0} for fn in fold_names}
    for tr in trades:
        per_fold[tr["fold"]]["trades"] += 1
        per_fold[tr["fold"]]["net_pnl"] += tr["net_pnl"]
    eq = equity.to_numpy(dtype=float)
    if len(eq):
        run_max = np.maximum.accumulate(eq)
        max_dd = float((run_max - eq).max())
        eq_end = float(eq[-1])
    else:
        max_dd, eq_end = 0.0, float(start_capital)
    return {
        "start_capital": float(start_capital),
        "net_pnl": net,
        "trade_count": int(len(trades)),
        "pf": pf,
        "pf_lossless": pf_lossless,
        "per_fold": {fn: {"trades": int(v["trades"]), "net_pnl": float(v["net_pnl"])}
                     for fn, v in per_fold.items()},
        "net_positive_folds": int(sum(1 for v in per_fold.values()
                                      if v["net_pnl"] > 0)),
        "max_dd_usd": max_dd,
        "max_dd_pct": max_dd / float(start_capital),
        "equity_end": eq_end,
    }


def leg_verdict(leg_metrics: dict) -> dict:
    n = leg_metrics["trade_count"]
    return {
        "p1_net_positive": bool(leg_metrics["net_pnl"] > 0),
        "trades": int(n),
        "trade_count_only": bool(n < spec.MIN_TRADES_NON_VACUOUS),
        "non_vacuous": bool(n >= spec.MIN_TRADES_NON_VACUOUS),
    }


def combo_verdict(combo_metrics: dict, leg_metrics: list[dict],
                  b1_net: float | None) -> dict:
    """P1-P7 per plan §6 — pure functions of the metrics dicts.

    combo_metrics must carry key 'combo_net_stress_1_5' (P5 cross-tier bar).
    P4 is combo-specific: max drawdown <= 25% of the $60,000 aggregate."""
    net = combo_metrics["net_pnl"]
    pf = combo_metrics.get("pf")
    p1 = net > 0
    p2 = bool(combo_metrics.get("pf_lossless", False)
              or (pf is not None and pf >= spec.PF_BAR))
    p3 = combo_metrics["net_positive_folds"] >= spec.NET_POSITIVE_FOLDS_BAR
    p4 = combo_metrics["max_dd_usd"] <= spec.MAX_DD_PCT_BAR * spec.COMBO_START_EQUITY
    p5 = bool(combo_metrics.get("combo_net_stress_1_5", 0.0) > 0)
    if net <= 0:
        p6 = True  # vacuous (P6 conditions on combo net > 0)
    else:
        max_fold = max((v["net_pnl"] for v in combo_metrics["per_fold"].values()),
                       default=0.0)
        p6 = bool(max_fold <= spec.SINGLE_FOLD_SHARE_BAR * net)
    legs_nets = [m["net_pnl"] for m in leg_metrics]
    mean_leg = sum(legs_nets) / len(legs_nets) if legs_nets else 0.0
    b1 = b1_net if b1_net is not None else float("-inf")
    p7 = bool(net >= b1 and net >= mean_leg)
    bars = {"p1_net_positive": p1, "p2_pf_ge_1_25": p2,
            "p3_net_positive_folds_ge_7_of_10": p3,
            "p4_max_dd_le_25pct_of_60k": p4, "p5_net_positive_stress_1_5": p5,
            "p6_no_fold_over_50pct_of_net": p6, "p7_beats_b1_and_mean_leg": p7}
    bars["all_pass"] = all(bars.values())
    bars["terminal_outcome"] = _terminal_outcome(bars, leg_metrics)
    return bars


def _terminal_outcome(bars: dict, leg_metrics: list[dict]) -> str:
    any_leg_p1 = any(m["net_pnl"] > 0 for m in leg_metrics)
    p = [bars[k] for k in ("p1_net_positive", "p2_pf_ge_1_25",
                           "p3_net_positive_folds_ge_7_of_10",
                           "p4_max_dd_le_25pct_of_60k",
                           "p5_net_positive_stress_1_5",
                           "p6_no_fold_over_50pct_of_net",
                           "p7_beats_b1_and_mean_leg")]
    if all(p):
        return "COMBO6_SURVIVOR_CANDIDATE"
    if not any_leg_p1:
        return "COMBO6_REJECT_ALL"
    if not p[6]:
        return "COMBO6_NO_INCREMENTAL_VALUE"
    if all(p[:4]) and not p[4]:
        return "COMBO6_STRESS_FAIL"
    if all(p[:3]) and (not p[3] or not p[5]):
        return "COMBO6_RISK_BAR_FAIL"
    return "COMBO6_UNCATEGORIZED_DEFER_OWNER"
