"""Metrics per evaluation_contract.json (all measured, never asserted).

V2 additions: unknown_share_effective naming and buy_hold_reference —
buy-hold is a REFERENCE METRIC per cell, never a scored arm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .data import Bars


@dataclass
class RegimeStats:
    switches: int
    occupancy: dict
    avg_dwell: float
    unknown_share: float


def regime_stats_from_timeline(labels: list[str]) -> RegimeStats:
    n = len(labels)
    if n == 0:
        return RegimeStats(0, {}, 0.0, 0.0)
    switches = sum(1 for i in range(1, n) if labels[i] != labels[i - 1])
    occ: dict[str, int] = {}
    for l in labels:
        occ[l] = occ.get(l, 0) + 1
    # avg dwell = mean length of maximal constant segments
    segs = []
    cur = 1
    for i in range(1, n):
        if labels[i] == labels[i - 1]:
            cur += 1
        else:
            segs.append(cur)
            cur = 1
    segs.append(cur)
    unknown = occ.get("TRANSITION_UNKNOWN", 0)
    return RegimeStats(
        switches=switches,
        occupancy={k: v / n for k, v in occ.items()},
        avg_dwell=sum(segs) / len(segs),
        unknown_share=unknown / n,
    )


def skipped_trade_pnl(bars: Bars, targets: list[str | None], cost_frac_per_side: float) -> float:
    """Counterfactual always-on TREND_LONG on bars where the router is FLAT.

    Buy-and-hold per flat segment: compounded bar returns over each maximal
    FLAT segment (target==FLAT, i.e. governed bars mapping to flat), minus
    per-segment entry+exit costs. Returns the compounded fraction of the
    starting equity (dimensionless).
    """
    eq = 1.0
    i = 0
    N = len(targets)
    while i < N:
        if targets[i] != "FLAT":
            i += 1
            continue
        s = i
        while i < N and targets[i] == "FLAT":
            i += 1
        e = i - 1
        seg = float(bars.close[e]) / float(bars.open[s]) - 1.0
        eq *= (1.0 + seg) * (1.0 - cost_frac_per_side) * (1.0 - cost_frac_per_side)
    return eq - 1.0


def sharpe(rets: np.ndarray, periods_per_year: float) -> float:
    r = np.asarray(rets, dtype=np.float64)
    if len(r) < 2:
        return float("nan")
    sd = float(np.std(r, ddof=1))
    if sd == 0:
        return float("nan")
    return float(np.mean(r)) / sd * math.sqrt(periods_per_year)


def sortino(rets: np.ndarray, periods_per_year: float) -> float:
    r = np.asarray(rets, dtype=np.float64)
    if len(r) < 2:
        return float("nan")
    downside = r[r < 0]
    dd = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
    if dd == 0:
        return float("nan")
    return float(np.mean(r)) / dd * math.sqrt(periods_per_year)


def max_drawdown(equity: np.ndarray) -> float:
    eq = np.asarray(equity, dtype=np.float64)
    eq = eq[np.isfinite(eq)]
    if len(eq) == 0:
        return 0.0
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1.0
    return float(np.min(dd))


def compute_arm_metrics(
    engine_result,
    exec_bars: Bars,
    periods_per_year: float,
    initial_equity: float = 100_000.0,
    timeline_labels: list[str] | None = None,
    targets: list[str | None] | None = None,
    cost_frac_per_side: float = 0.0,
) -> dict:
    tot = engine_result.totals
    eq = engine_result.equity
    eq_start = initial_equity
    finite = eq[np.isfinite(eq)]
    eq_end = float(finite[-1]) if len(finite) else initial_equity
    total_return = eq_end / eq_start - 1.0

    # time span from exec bars within folds
    ts = exec_bars.ts_close
    mask = engine_result.fold_id >= 0
    if mask.any():
        years = (float(ts[mask][-1]) - float(ts[mask][0])) / (365.25 * 86400 * 1e9)
    else:
        years = float("nan")
    cagr = (eq_end / eq_start) ** (1.0 / years) - 1.0 if years and years > 0 and eq_end > 0 else float("nan")

    # per-bar return series across fold bars
    rets = []
    prev_eq = eq_start
    for k in range(len(eq)):
        if engine_result.fold_id[k] >= 0:
            if np.isfinite(eq[k]) and prev_eq > 0:
                rets.append(float(eq[k]) / prev_eq - 1.0)
            prev_eq = float(eq[k]) if np.isfinite(eq[k]) else prev_eq
    rets_arr = np.array(rets)

    trades = engine_result.trades
    net = [t.net_pnl for t in trades]
    wins = [v for v in net if v > 0]
    losses = [v for v in net if v < 0]
    pf = (sum(wins) / abs(sum(losses))) if losses else (float("inf") if wins else float("nan"))
    win_rate = len(wins) / len(net) if net else float("nan")
    expectancy = sum(net) / len(net) if net else float("nan")

    avg_eq = float(np.mean(finite)) if len(finite) else initial_equity
    entered_notional = sum(t.qty * t.entry_px for t in trades)
    turnover = (entered_notional / avg_eq / years) if years and years > 0 else float("nan")

    if timeline_labels is not None:
        rs = regime_stats_from_timeline(timeline_labels)
        regime_block = {
            "regime_switches": rs.switches,
            "regime_occupancy": rs.occupancy,
            "avg_dwell": rs.avg_dwell,
            "unknown_share_effective": rs.unknown_share,
        }
    else:
        regime_block = {
            "regime_switches": None,
            "regime_occupancy": None,
            "avg_dwell": None,
            "unknown_share_effective": None,
        }

    fold_net = engine_result.fold_net_pnl
    pos_folds = [v for v in fold_net if v > 0]
    concentration = (max(fold_net) / sum(pos_folds)) if pos_folds and max(fold_net) > 0 else float("nan")

    skipped = (
        skipped_trade_pnl(exec_bars, targets, cost_frac_per_side)
        if targets is not None
        else None
    )

    return {
        **tot,
        "total_return": total_return,
        "cagr": cagr,
        "sharpe": sharpe(rets_arr, periods_per_year),
        "sortino": sortino(rets_arr, periods_per_year),
        "max_drawdown": max_drawdown(eq),
        "profit_factor": pf,
        "expectancy_per_trade": expectancy,
        "win_rate": win_rate,
        "turnover": turnover,
        "time_in_market": float(np.mean(engine_result.invested)),
        "fold_by_fold_net_pnl": fold_net,
        "concentration_top_fold_profit_share": concentration,
        "skipped_trade_pnl_fraction": skipped,
        "years": years,
        **regime_block,
    }


def margin_to_fail(fold_net_x: list[float], fold_net_y: list[float], total_x: float, total_y: float) -> float | None:
    """|delta net| / stdev of per-fold net deltas (P-2). None if unmeasurable."""
    if len(fold_net_x) != len(fold_net_y) or len(fold_net_x) < 2:
        return None
    d = np.array(fold_net_x) - np.array(fold_net_y)
    sd = float(np.std(d, ddof=1))
    if sd == 0 or not math.isfinite(sd):
        return None
    return abs(total_x - total_y) / sd


def q11_metrics(labels: list[str], label_codes: dict, exec_bars: Bars, exec_index_of_regime: list[int], horizon: int = 24) -> dict:
    """Q-11: lag-1 label autocorrelation + label->forward-return association.

    exec_index_of_regime[k] = index of the exec bar whose return horizon
    starts at the regime decision k (used for the association statistic).
    """
    codes = np.array([label_codes[l] for l in labels], dtype=np.float64)
    if len(codes) > 1:
        c = np.corrcoef(codes[:-1], codes[1:])
        ac = float(c[0, 1])
    else:
        ac = float("nan")
    # association: mean forward return conditional on UPTREND minus mean
    # conditional on DOWNTREND (signed structure separation)
    fwd = []
    for k, ei in enumerate(exec_index_of_regime):
        j = ei + horizon
        if j < len(exec_bars.close) and ei >= 0:
            fwd.append(float(exec_bars.close[j]) / float(exec_bars.close[ei]) - 1.0)
        else:
            fwd.append(float("nan"))
    fwd = np.array(fwd)
    up = fwd[np.array(labels) == "UPTREND"]
    dn = fwd[np.array(labels) == "DOWNTREND"]
    assoc = float(np.nanmean(up) - np.nanmean(dn)) if len(up) and len(dn) else float("nan")
    return {"lag1_autocorr": ac, "label_forward_assoc": assoc}
