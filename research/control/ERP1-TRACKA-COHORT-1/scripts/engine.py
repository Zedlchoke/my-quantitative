"""Backtest-engine core, PARAMETRIZED per pair — ERP1-TRACKA-COHORT-1.

PORT LINEAGE: ported from EURUSD-RANGEEXP-SCORED-V1/scripts/engine.py
(fx-rangefade-2m-shadow-v1 worktree). The ancestor hard-codes PIP=1e4 —
the plan §5.2 BLOCKING PORT DEFECT. Here the pips multiplier is carried
per Plane from PairConfig.pip (pip_mult = 1/pip): EURUSD-style 1e-4 pip
-> 1e4, USDJPY-style 0.01 pip -> 1e2 (template fixture in tests/), and
the cohort pairs from their probe-derived configs. All fill/force-flat
SEMANTICS are byte-compatible with the ancestor (documented below).

DATA-GATE SCOPE: the strategy FAMILIES table is deliberately NOT ported —
family configs are scored-cell machinery (plan §8/§10); a later lane with
its own GO ports them from the same lineage. No PnL of any arm is
produced in this lane; run_strategy exists so engine parity fixtures can
run later, and is exercised here only with all-zero targets (0 trades).

Semantics (preregistered in the ancestor plan §4–§6 — inherited text):
- Signal on CLOSED 15m bar t uses data <= t only (PIT). Fill at t+1 open.
- Marketable fills at the OPPOSITE side: buy at bid_o + k*s_open, sell
  (entry short) at ask_o - k*s_open, close long at ask_c - k*s_close,
  close short at bid_c + k*s_close. k = cost multiplier {1.0, 1.5, 2.0}.
  taker PAYS the spread (never "earns" it — plan §6 wording bans).
- Force-flat law (engine-v1): no position at/after the 21:00 UTC rollover;
  last fill-eligible entry signals on the bar before the 20:45 bar; every
  position closes at the close of the last valid bar strictly before 21:00
  of its day. (The cohort H1 trading law — no fills on/after the 19:00
  bar, flat before 20:00 UTC — is a LATER lane's Plane subclass, as the
  ancestor's v2_lib.H1Plane subclasses this Plane.)
- Costs are inside the fills: one spread crossing per side.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEC_DAY = 86400


def session_of(ts_epoch):
    """Return UTC hhmm*100 for bar-open timestamps (epoch seconds)."""
    h = (ts_epoch // 3600) % 24
    m = (ts_epoch // 60) % 60
    return h * 100 + m


class Plane:
    """Valid 15m bars + derived session metadata, with per-pair pip mult.

    pip_mult converts price deltas to pips (ancestor constant PIP=1e4 is
    the EURUSD-style special case pip_mult = 1/1e-4).
    """

    def __init__(self, df, pip_mult=1e4):
        # pandas >=3 may carry datetimes at us resolution; normalize through
        # numpy datetime64[s] so epoch seconds are unit-independent (the
        # ancestor fixture suite caught a real force-flat calendar break here).
        self.ts = (
            df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
            .to_numpy().astype("datetime64[s]").astype("int64")
        )
        self.pip_mult = float(pip_mult)
        self.b_o = df["b_o"].to_numpy(); self.b_h = df["b_h"].to_numpy()
        self.b_l = df["b_l"].to_numpy(); self.b_c = df["b_c"].to_numpy()
        self.a_o = df["a_o"].to_numpy(); self.a_c = df["a_c"].to_numpy()
        self.s_o = df["s_open"].to_numpy(); self.s_c = df["s_close"].to_numpy()
        self.hhmm = np.array([session_of(t) for t in self.ts], dtype=np.int32)
        self.day = (self.ts // SEC_DAY).astype(np.int64)
        # last valid bar of each UTC day (force-flat close bar)
        last_of_day = {}
        for i in range(len(self.ts)):
            last_of_day[self.day[i]] = i
        self.last_bar_of_day = np.array([last_of_day[d] for d in self.day])
        self.is_day_close = np.zeros(len(self.ts), dtype=bool)
        self.is_day_close[self.last_bar_of_day] = True
        # entry fill allowed at bar i if a previous bar exists to signal on
        # and the fill bar is NOT the day-close bar (no fill into rollover)
        self.fill_ok = np.ones(len(self.ts), dtype=bool)
        self.fill_ok[0] = False
        self.fill_ok[self.is_day_close] = False
        # hours-of-day helper
        self.hour = (self.ts // 3600 % 24).astype(np.int32)
        self.minute = (self.ts // 60 % 60).astype(np.int32)

    def pips(self, price_delta):
        """Price delta -> pips via the per-pair multiplier."""
        return np.asarray(price_delta, dtype=float) * self.pip_mult


def run_strategy(plane, target, k, warmup_end_idx=0):
    """target[i] in {-1,0,+1}: desired position while bar i is the signal bar.

    Fill semantics (all at effective prices with stress multiplier k):
      open long  = buy  at ask_eff(open) = b_o + k*s_o
      open short = sell at bid_eff(open) = a_o - k*s_o
      close long = sell at bid_eff(open/close)
      close short= buy  at ask_eff(open/close)
    Reversals exit and enter at the same bar open. Force-flat at the close
    of each day's last valid bar. PnL in PIPS via plane.pip_mult.
    """
    n = len(plane.ts)
    pos = 0
    entry_i = -1
    entry_px = 0.0
    trades = []
    equity = np.zeros(n)
    cum = 0.0

    def close_trade(i, exit_px):
        nonlocal cum, pos
        pnl = (exit_px - entry_px) * pos * plane.pip_mult
        cum += pnl
        trades.append(
            {
                "entry_ts": int(plane.ts[entry_i]), "exit_ts": int(plane.ts[i]),
                "dir": int(pos), "entry_px": round(entry_px, 6),
                "exit_px": round(exit_px, 6), "pips": round(pnl, 2),
                "hold_bars": int(i - entry_i),
            }
        )
        pos = 0

    for i in range(warmup_end_idx, n):
        if plane.is_day_close[i]:
            if pos != 0:
                px = (plane.a_c[i] - k * plane.s_c[i]) if pos > 0 else (plane.b_c[i] + k * plane.s_c[i])
                close_trade(i, px)
            equity[i] = cum
            continue
        want = int(target[i - 1]) if i > warmup_end_idx else 0
        if not plane.fill_ok[i]:
            want = 0
        if want != pos:
            if pos != 0:
                px = (plane.a_o[i] - k * plane.s_o[i]) if pos > 0 else (plane.b_o[i] + k * plane.s_o[i])
                close_trade(i, px)
            if want != 0:
                pos = want
                entry_i = i
                entry_px = (plane.b_o[i] + k * plane.s_o[i]) if want > 0 else (plane.a_o[i] - k * plane.s_o[i])
        equity[i] = cum
    if pos != 0:  # fail-safe; the day-close law should prevent this
        i = n - 1
        px = (plane.a_c[i] - k * plane.s_c[i]) if pos > 0 else (plane.b_c[i] + k * plane.s_c[i])
        close_trade(i, px)
        equity[-1] = cum
    return trades, equity


def metrics(trades, equity):
    if not trades:
        return {"net_pips": 0.0, "trades": 0, "pf": None, "hit": None, "maxdd_pips": 0.0}
    pnls = np.array([t["pips"] for t in trades])
    gross_win = pnls[pnls > 0].sum()
    gross_loss = -pnls[pnls < 0].sum()
    peak = np.maximum.accumulate(equity)
    maxdd = float((peak - equity).max())
    return {
        "net_pips": round(float(pnls.sum()), 2),
        "trades": int(len(pnls)),
        "pf": round(float(gross_win / gross_loss), 4) if gross_loss > 0 else None,
        "hit": round(float((pnls > 0).mean()), 4),
        "maxdd_pips": round(maxdd, 2),
    }
