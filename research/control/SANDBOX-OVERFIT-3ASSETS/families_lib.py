"""SANDBOX family overfit — 3 family chọn từ corpus đã research của owner.

- CRYPTO : H-VOLCOMP-BRKOUT-v1   (strategy_vol_compression_breakout.py)
- STOCKS : EVENT-UNWIND          (PLAN_stocks_search_v1.md family #1, NG6 anchor)
- FOREX  : SWING-EXTREME ABSORPTION / DIVERGENT CLV (PLAN_forex_ng7.md
           anchor FNG7-A2-P1-ABSORB)

Overfit BY DESIGN (owner chỉ đạo 2026-09-20): grid rộng, chọn theo IS net
return, KHÔNG fold discipline. OOS 20% cuối chỉ để chẩn đoán.
Đọc-only; không đụng registry/ledger/worktree nào.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DATA.mkdir(exist_ok=True)

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval=1d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


# ---------------------------------------------------------------- data

def fetch_yahoo_daily(sym: str, rng: str = "15y") -> pd.DataFrame:
    cache = DATA / f"yh_{sym.replace('=','_').replace('^','_')}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    req = urllib.request.Request(YAHOO.format(sym=sym, rng=rng), headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())
    res = payload["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    ts = pd.to_datetime(res["timestamp"], unit="s", utc=True).normalize()
    df = pd.DataFrame({
        "ts": ts, "open": q["open"], "high": q["high"], "low": q["low"],
        "close": q["close"], "volume": q["volume"],
    }).dropna().drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
    df.to_parquet(cache, index=False)
    time.sleep(0.4)
    return df


# ------------------------------------------------------------- helpers

def roll_min(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).min().to_numpy()


def roll_max(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).max().to_numpy()


def roll_mean(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).mean().to_numpy()


def roll_std(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).std().to_numpy()


def atr(h, l, c, n: int) -> np.ndarray:
    prev_c = np.roll(c, 1); prev_c[0] = np.nan
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return roll_mean(tr, n)


# ===================================================== CRYPTO: VOLCOMP
# Anchor: strategy_vol_compression_breakout.py — squeeze bb bandwidth
# percentile <= squeeze_pct_max sustained qua lookback; entry close phá
# Donchian-upper (window trước) + volume >= ratio x SMA; long-only;
# stop = ATR*mult; TP = entry + tp_mult * stop_dist.

def volcomp_trades(o, h, l, c, v, *, bb_period, bb_k, squeeze_lb, squeeze_pct,
                   vol_ratio, donch, atr_mult, tp_mult, max_hold,
                   fee_side=6e-4, funding_per_bar=1e-4 / 32) -> list[tuple]:
    mid = roll_mean(c, bb_period)
    sd = roll_std(c, bb_period)
    up, lo = mid + bb_k * sd, mid - bb_k * sd
    bw = (up - lo) / mid
    pct = pd.Series(bw).rolling(squeeze_lb, min_periods=squeeze_lb).rank(pct=True).to_numpy()
    don_hi_prev = np.roll(roll_max(h, donch), 1); don_hi_prev[0] = np.nan
    vsma = roll_mean(v, 20)
    a = atr(h, l, c, 14)
    squeeze = pct <= squeeze_pct / 100.0
    n = len(c)
    trades = []
    i = bb_period + 1
    warm = max(squeeze_lb, donch) + 5
    while i < n - 1:
        # sustained squeeze trong cửa sổ kết thúc ở bar t-1
        if not squeeze[max(0, i - 1 - (squeeze_lb // 2)):i].any():
            i += 1
            continue
        if not (np.isfinite(don_hi_prev[i]) and c[i] > don_hi_prev[i]):
            i += 1
            continue
        if not (np.isfinite(vsma[i]) and v[i] >= vol_ratio * vsma[i]):
            i += 1
            continue
        entry = o[i + 1]
        stop_d = atr_mult * (a[i] if np.isfinite(a[i]) and a[i] > 0 else 0.01 * entry)
        stop, tp = entry - stop_d, (entry + tp_mult * stop_d) if tp_mult else None
        # path scan
        exit_px, j = None, i + 1
        bars_held = 0
        while j < n:
            bars_held += 1
            if l[j] <= stop:
                exit_px = stop  # pessimistic: stop trước TP nếu cùng bar
                break
            if tp is not None and h[j] >= tp:
                exit_px = tp
                break
            if bars_held >= max_hold:
                exit_px = c[j]
                break
            j += 1
        if exit_px is None:
            exit_px = c[n - 1]; j = n - 1
        gross = exit_px / entry - 1.0
        net = gross - 2 * fee_side - funding_per_bar * bars_held
        trades.append((i + 1, j, net))
        i = j + 1
    return trades


# ===================================================== STOCKS: EVENT-UNWIND
# Anchor NG6: BREAK low_t < min(low_{t-K..t-1}) -> RECLAIM close > mức low
# bị phá, RANGE (c-l)/(h-l) >= r, PARTICIPATION dollar_vol >= p x median60.

def event_unwind_trades(o, h, l, c, v, *, K, H, range_thr, part_mult,
                        reclaim_gap, fee_side=3e-4) -> list[tuple]:
    n = len(c)
    prior_k_low = roll_min(l, K)
    prev_of = np.roll(prior_k_low, 1); prev_of[0] = np.nan
    dv = v * c
    dv_med60 = roll_mean(dv, 60)
    hl = h - l
    rng_ok = hl > 0
    trades = []
    broken_level = np.nan
    broken_at = -10 ** 9
    i = K + 1
    while i < n - 1:
        if np.isfinite(prev_of[i]) and l[i] < prev_of[i]:
            broken_level = prev_of[i]
            broken_at = i
            i += 1
            continue
        if np.isfinite(broken_level) and 0 < i - broken_at <= reclaim_gap \
                and c[i] > broken_level:
            ok = rng_ok[i] and (c[i] - l[i]) / hl[i] >= range_thr
            ok = ok and np.isfinite(dv_med60[i]) and dv[i] >= part_mult * dv_med60[i]
            if ok:
                entry = o[i + 1]
                j = min(i + 1 + H, n - 1)
                exit_px = c[j]
                net = exit_px / entry - 1.0 - 2 * fee_side
                trades.append((i + 1, j, net))
                broken_level = np.nan
                i = j + 1
                continue
        i += 1
    return trades


# ===================================================== FOREX: DIVERGENT CLV
# Anchor FNG7-A2-P1-ABSORB: CLV=((C-L)-(H-C))/(H-L); P = sum CLV 20 bars;
# slope = P_t - P_{t-k}; fresh close extreme 20 bars + slope KHÔNG xác nhận
# -> LONG (low) / SHORT (high); warmup 60; hold H bars.

def clv_absorb_trades(o, h, l, c, *, ext_win=20, p_win=20, slope_win=5,
                      hold=3, div_thr=0.0, pip=1e-4, fee_pips=1.0) -> list[tuple]:
    n = len(c)
    rng = h - l
    clv = np.where(rng > 0, ((c - l) - (h - c)) / np.where(rng > 0, rng, 1.0), 0.0)
    P = pd.Series(clv).rolling(p_win).sum().to_numpy()
    slope = P - np.roll(P, slope_win)
    slope[:slope_win] = np.nan
    lo_ext = roll_min(c, ext_win)
    hi_ext = roll_max(c, ext_win)
    trades = []
    i = 60
    while i < n - 1:
        entry_i = i + 1
        px = o[entry_i]
        if np.isfinite(lo_ext[i]) and c[i] <= lo_ext[i] and slope[i] > div_thr:
            j = min(entry_i + hold, n - 1)
            net = c[j] / px - 1.0 - 2 * fee_pips * pip / px
            trades.append((entry_i, j, net))
            i = j + 1
            continue
        if np.isfinite(hi_ext[i]) and c[i] >= hi_ext[i] and slope[i] < -div_thr:
            j = min(entry_i + hold, n - 1)
            net = -(c[j] / px - 1.0) - 2 * fee_pips * pip / px
            trades.append((entry_i, j, net))
            i = j + 1
            continue
        i += 1
    return trades


# ============================================================ evaluator

def trades_to_daily(ts_index: pd.DatetimeIndex, trades: list[tuple],
                    n_slots: int = 1) -> pd.Series:
    """daily portfolio return: mỗi slot vốn chia đều cho các trade đang chạy
    trong ngày (per-symbol book đã skip overlap)."""
    daily = pd.Series(0.0, index=ts_index)
    counts = pd.Series(0.0, index=ts_index)
    for (a, b, net) in trades:
        seg = ts_index[a:b + 1]
        if len(seg) == 0:
            continue
        per_bar = (1.0 + net) ** (1.0 / len(seg)) - 1.0
        daily.loc[seg] += per_bar
        counts.loc[seg] += 1
    # vốn cố định chia n_slots slot; slot idle = 0%
    return daily / n_slots


def metrics_from_daily(ret: pd.Series) -> dict:
    r = ret.to_numpy()
    eq = np.cumprod(1.0 + r)
    total = float(eq[-1] - 1.0)
    sd = float(np.std(r))
    sharpe = float(np.mean(r) / sd * np.sqrt(252)) if sd > 0 else 0.0
    peak = np.maximum.accumulate(eq)
    maxdd = float(np.max(1.0 - eq / peak)) if len(eq) else 0.0
    years = len(r) / 252.0
    cagr = float(eq[-1] ** (1 / years) - 1.0) if eq[-1] > 0 and years > 0 else -1.0
    return {"total_return": total, "cagr": cagr, "sharpe": sharpe, "max_dd": maxdd}
