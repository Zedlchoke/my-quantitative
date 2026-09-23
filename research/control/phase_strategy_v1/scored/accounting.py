"""PSV1 scored-run engine (post-GO only; plan §15/§16.3; evaluation_freeze).

A1-owned accounting layer. Consumes the LANES' frozen label/signal machines
verbatim (identity law) and adds the ONLY thing lanes were forbidden to have:
prices-to-dollars accounting.

Frozen execution/accounting conventions (binding, disclosed in every tier
artifact):
- Initial equity 100,000; sizing fraction 1.0 compounding on equity.
- Fill events carry a fill bar and a class: open-class fills execute at that
  bar's OPEN; close-class fills (fold-end force-flat / series end) execute at
  that bar's CLOSE — the position holds through the bar either way.
- Costs charged exactly once per NET exposure change at the fill:
  equity * |target - pos| * tier * bps_per_side / 1e4. Same-bar exit+entry
  pairs net to the last target (frozen churn/no-op law); raw event pairs are
  still counted and reported.
- Funding (BTC perp cells only): 1.377e-5 per 8h, signed (a long position
  pays a positive rate), charged at bars whose open stamp is an 8h boundary
  (00/08/16 UTC), on equity*position after that bar's open fills. Scaled by
  the same cost tier as fees+slippage (full-stack tier law).
- Bar accounting order: (1) close[t-1]->open[t] gap accrues to the incoming
  position; (2) open-class fill + cost (gap already priced in; the position
  then earns open[t]->close[t]); (3) open[t]->close[t] move accrues to the
  position held; (4) funding; (5) close-class fill + cost at close[t].
- Fold nets decompose exactly (every fold boundary is flat by construction).
"""
from __future__ import annotations

import numpy as np

INITIAL_EQUITY = 100_000.0
BTC_BPS_PER_SIDE = 6.0         # taker 5 + slippage 1 (V2 frozen identity)
SPY_BPS_PER_FILL = 10.0        # long-only, per fill (V2 frozen identity)
BTC_FUNDING_PER_8H = 1.377e-5  # V2 frozen identity


def btc_8h_boundary_mask(open_stamps_ms: np.ndarray) -> np.ndarray:
    hrs = (open_stamps_ms // 3_600_000) % 24
    return (hrs % 8) == 0


def _group_fills(fills: list[tuple[int, float, bool]]):
    """Per bar: [at_close, final_target] from the ordered fill events
    (side 0 = flatten). Same-bar exit+entry pairs net to the last target."""
    ev: dict[int, list] = {}
    raw = 0
    for bar, side, at_close in sorted(fills, key=lambda x: (x[0], x[2])):
        raw += 1
        tgt = 0.0 if side == 0.0 else float(side)
        ev[bar] = [at_close, tgt]
    return ev, raw


def run_accounting(open_: np.ndarray, close_: np.ndarray,
                   fills: list[tuple[int, float, bool]],
                   fold_ids: np.ndarray,
                   bps_per_side: float, tier: float = 1.0,
                   funding_mask: np.ndarray | None = None,
                   funding_rate: float = 0.0) -> dict:
    n = len(close_)
    rate = bps_per_side * tier / 1e4
    frate = funding_rate * tier
    ev_by_bar, raw = _group_fills(fills)

    eq = INITIAL_EQUITY
    pos = 0.0
    gross = fees = funding = 0.0
    curve = np.empty(n)
    open_trade = None
    trades: list[dict] = []

    fold_last: dict[int, int] = {}
    fold_first: dict[int, int] = {}
    for i, f in enumerate(fold_ids):
        f = int(f)
        fold_first.setdefault(f, i)
        if i == n - 1 or int(fold_ids[i + 1]) != f:
            fold_last[f] = i
    fold_eq: dict[int, float] = {}
    fold_net: dict[int, float] = {}

    def charge(cost: float) -> None:
        nonlocal eq, fees
        eq -= cost
        fees += cost
        if open_trade is not None:
            open_trade["fees"] += cost

    def close_trade(t: int) -> None:
        nonlocal open_trade
        open_trade["exit_bar"] = t
        open_trade["net"] = eq - open_trade["eq_at_entry"]
        open_trade["hold_bars"] = t - open_trade["entry_bar"]
        trades.append(open_trade)
        open_trade = None

    for t in range(n):
        f = int(fold_ids[t])
        if fold_first[f] == t:
            fold_eq[f] = eq
        prev_close = close_[t - 1] if t > 0 else None
        event = ev_by_bar.get(t)
        open_class = (event is not None and not event[0])
        close_class = (event is not None and event[0])

        # (1) gap accrual on the incoming position
        if pos != 0.0 and prev_close is not None and prev_close > 0:
            g = eq * pos * (open_[t] / prev_close - 1.0)
            eq += g
            gross += g
            if open_trade is not None:
                open_trade["gross"] += g

        # (2) open-class fill: cost at open, then the position earns the bar
        if open_class:
            target = event[1]
            delta = target - pos
            if delta != 0.0:
                if open_trade is None and target != 0.0:
                    open_trade = {"entry_bar": t, "side": target,
                                  "eq_at_entry": eq, "gross": 0.0,
                                  "fees": 0.0, "funding": 0.0}
                charge(eq * abs(delta) * rate)
                pos = target
                if open_trade is not None and pos == 0.0:
                    close_trade(t)

        # (3) bar move on the position held through the bar
        if pos != 0.0 and open_[t] > 0:
            m = eq * pos * (close_[t] / open_[t] - 1.0)
            eq += m
            gross += m
            if open_trade is not None:
                open_trade["gross"] += m

        # (4) funding on the position held during this bar
        if funding_mask is not None and funding_mask[t] and pos != 0.0:
            ffee = eq * pos * frate
            eq -= ffee
            funding -= ffee
            if open_trade is not None:
                open_trade["funding"] -= ffee

        # (5) close-class fill: cost at close, position flat at fold end
        if close_class:
            target = event[1]
            delta = target - pos
            if delta != 0.0:
                charge(eq * abs(delta) * rate)
                pos = target
                if open_trade is not None and pos == 0.0:
                    close_trade(t)

        if fold_last[f] == t:
            fold_net[f] = eq - fold_eq[f]
        curve[t] = eq

    if ev_by_bar and max(ev_by_bar) >= n:
        raise ValueError("fill scheduled past the series end")
    if open_trade is not None or pos != 0.0:
        raise ValueError("book not flat at series end")
    mdd = _max_drawdown(curve)
    pos_folds = [v for v in fold_net.values() if v > 0]
    concentration = (max(pos_folds) / sum(pos_folds)) if pos_folds else None
    holds = sorted(tr["hold_bars"] for tr in trades)
    med_hold = float(np.median(holds)) if holds else None
    return {
        "net": eq - INITIAL_EQUITY,
        "gross": gross,
        "fees": fees,
        "funding": funding,
        "trades": len(trades),
        "raw_fill_events": raw,
        "netted_fill_bars": len(ev_by_bar),
        "per_fold_net": {k: fold_net.get(k, 0.0) for k in sorted(fold_last)},
        "fold_concentration": concentration,
        "max_drawdown": mdd,
        "median_hold_bars": med_hold,
        "final_equity": eq,
        "trade_records": trades,
    }


def _max_drawdown(curve: np.ndarray) -> float:
    peak = np.maximum.accumulate(curve)
    dd = curve / peak - 1.0
    return float(dd.min())
