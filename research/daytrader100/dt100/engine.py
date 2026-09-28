"""DT100 execution engine.

Semantics (frozen at G3):
- `pos` series = position DESIRED as of each bar's CLOSE (built by signals.py).
- A position change decided at bar t is FILLED at bar t+1's OPEN.
- Day force-flat (crypto): pos forced 0 at the 23:59 UTC bar each day.
- Fold force-flat: pos forced 0 at each fold's last bar (no cross-fold holding).
- Costs per side: crypto = (taker_bps + half_spread_bps) * stress;
  fx = per-bar measured half-spread_bps(fill bar) * stress (floor applies).
- Funding (crypto, measured bytes): a position held INTO a settlement bar pays
  dir * rate; charged in bps of entry notional.
- Controls (re-evaluations, zero scored cells): clock_shadow (direction permuted
  within weekday x hour strata, frozen seed), sign_flip, stale_lag.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def _force_flat(pos: pd.Series, ts: pd.Series, folds: list, crypto: bool) -> pd.Series:
    pos = pos.copy()
    day = ts.dt.floor("D")
    if crypto:
        last_of_day = day != day.shift(-1)
        pos[last_of_day] = 0.0
    edges = []
    for _, _a, _b in folds:
        b = pd.Timestamp(_b, tz="UTC") + pd.Timedelta(days=1)
        inwin = (ts >= pd.Timestamp(_a, tz="UTC")) & (ts < b)
        if inwin.any():
            edges.append(inwin.index[inwin][-1])
    for i in edges:
        pos.loc[i] = 0.0
    return pos


def clock_shadow(pos: pd.Series, ts: pd.Series) -> pd.Series:
    """Same schedule (when entries fire), direction permuted within
    weekday x hour strata — the Q-7 clock shadow."""
    rng = np.random.default_rng(config.CONTROL_SEED)
    df = pd.DataFrame({"pos": pos.to_numpy(), "wd": ts.dt.dayofweek.to_numpy(),
                       "hh": ts.dt.hour.to_numpy()})
    out = pos.copy()
    for (_, _), g in df.groupby(["wd", "hh"]):
        idx = g.index.to_numpy()
        vals = pos.to_numpy()[idx]
        fired = vals != 0
        if fired.sum() > 1:
            dirs = vals[fired].copy()
            rng.shuffle(dirs)
            out.iloc[idx[fired]] = dirs
    return out


def stale_lag(pos: pd.Series, lag_bars: int) -> pd.Series:
    return pos.shift(lag_bars).fillna(0.0)


def run_arm(df: pd.DataFrame, pos: pd.Series, folds: list, asset: str,
            symbol: str, stress: float = 1.0, warmup_end: str | None = None,
            funding: pd.DataFrame | None = None,
            cost_multiplier: float = 1.0, funding_sign: float = 1.0,
            spread_marking: bool = False) -> dict:
    """Returns trade-level frame + aggregate stats. No display of PnL in dry mode
    is enforced by the runner, not here (scored path only)."""
    ts = df["ts"]
    o = df["o"].to_numpy()
    c = df["c"].to_numpy()
    pos = _force_flat(pos.astype(float), ts, folds, crypto=(asset == "crypto"))
    if warmup_end:
        pos[ts < pd.Timestamp(warmup_end, tz="UTC")] = 0.0
    p = pos.to_numpy()

    change = np.zeros(len(p), dtype=bool)
    change[1:] = p[1:] != p[:-1]
    seg = np.cumsum(change)
    change_idx = np.flatnonzero(change)

    # pos[t] is DESIRED as of CLOSE of bar t -> a change detected at bar t
    # can only fill at the OPEN of bar t+1. Filling at open[t] would use a
    # price that predates the signal (lookahead) — the golden fixture pins this.
    # fills = change bars + 1 (signal at close t -> open t+1). A change at the
    # literal last bar cannot fill (fail-closed). Zero-dir fills close segments.
    cand = change_idx[change_idx + 1 < len(p)]
    fills = cand + 1
    dirs_at = p[cand]
    if len(fills) == 0:
        return {"trades": 0, "empty": True}
    entry_i = fills[:-1]
    exit_i = fills[1:]
    dirs = dirs_at[:-1]
    final_open = bool(dirs_at[-1] != 0)   # still held at frame end
    if final_open:
        entry_i = np.append(entry_i, fills[-1])
        exit_i = np.append(exit_i, len(p) - 1)
        dirs = np.append(dirs, dirs_at[-1])
    keep = dirs != 0
    entry_i, exit_i, dirs = entry_i[keep], exit_i[keep], dirs[keep]

    entry_px = o[entry_i].astype(float)
    exit_px = o[exit_i].astype(float)
    if final_open and keep.size and keep[-1]:
        exit_px[-1] = c[-1]          # frame-end mark at the last CLOSE
    # INC-DT100-1 remediation (owner order 2026-09-28 "sửa và chạy lại 12 cell
    # spread"): synthetic-spread frames mark PnL as the DIFFERENCE of the spread
    # (long spread profits when spread rises), never the ratio — log-spreads
    # cross zero and ratios explode.
    if spread_marking:
        gross_bps = dirs * (exit_px - entry_px) * 1e4
    else:
        gross_bps = dirs * (exit_px / entry_px - 1.0) * 1e4

    if asset == "crypto":
        cc = config.CRYPTO_COSTS[symbol]
        side = (cc["taker_bps"] + cc["half_spread_bps"]) * stress * cost_multiplier
        cost_bps = np.full(len(entry_i), 2 * side)
        fund_bps = np.zeros(len(entry_i))
        if funding is not None and len(funding):
            for k in range(len(entry_i)):
                lo, hi = ts.iloc[entry_i[k]], ts.iloc[exit_i[k]]
                m = (funding["ts"] >= lo) & (funding["ts"] < hi)
                if m.any():
                    fund_bps[k] = dirs[k] * funding.loc[m, "rate"].to_numpy().sum() * 1e4 * funding_sign
    else:
        sp = df["spread_bps"].to_numpy()
        half_entry = np.maximum(sp[entry_i] / 2, config.FX_MIN_HALF_SPREAD_BPS)
        half_exit = np.maximum(sp[np.minimum(exit_i, len(sp) - 1)] / 2,
                               config.FX_MIN_HALF_SPREAD_BPS)
        cost_bps = (half_entry + half_exit) * stress * cost_multiplier
        fund_bps = np.zeros(len(entry_i))

    net_bps = gross_bps - cost_bps - fund_bps
    tr = pd.DataFrame({
        "ts_entry": ts.iloc[entry_i].to_numpy(),
        "ts_exit": ts.iloc[exit_i].to_numpy(),
        "dir": dirs, "gross_bps": gross_bps, "cost_bps": cost_bps,
        "fund_bps": fund_bps, "net_bps": net_bps,
    })
    tr["fold"] = ""
    for name, a, b in folds:
        bb = pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1)
        m = (tr["ts_entry"] >= pd.Timestamp(a, tz="UTC")) & (tr["ts_entry"] < bb)
        tr.loc[m, "fold"] = name
    tr = tr[tr["fold"] != ""].reset_index(drop=True)
    return trades_frame(tr)


def trades_frame(tr: pd.DataFrame) -> dict:
    """Aggregate a trade frame into the frozen stat block."""
    out = {"trades": int(len(tr))}
    if not len(tr):
        return {**out, "empty": True}
    folds = [f for f in tr["fold"].unique()]
    per = {}
    for f in folds:
        g = tr[tr["fold"] == f]["net_bps"]
        per[f] = {"n": int(len(g)), "net_sum": float(g.sum()),
                  "expectancy": float(g.mean()) if len(g) else None}
    out["per_fold"] = per
    net = tr["net_bps"]
    wins, losses = net[net > 0], net[net < 0]
    out.update({
        "expectancy_bps": float(net.mean()),
        "net_sum_bps": float(net.sum()),
        "pf": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else None,
        "win_rate": float(len(wins) / len(net)),
        "folds_positive": int(sum(1 for v in per.values() if v["net_sum"] > 0)),
        "max_cost_bps": float(tr["cost_bps"].max()),
        "fund_sum_bps": float(tr["fund_bps"].sum()),
    })
    d = pd.to_datetime(tr["ts_entry"])
    wd = d.dt.dayofweek
    out["weekday_share_max"] = float(wd.value_counts(normalize=True).max())
    out["entry_hour_mode_share"] = float(d.dt.hour.value_counts(normalize=True).max())
    return out
