"""SANDBOX-OVERFIT-3ASSETS — exploratory engine (NOT evidence).

Owner-ordered sandbox 2026-09-19: per-asset strategy search maximizing
in-sample net compounded return. Overfit BY DESIGN. No fold discipline,
no DSR/PBO, no trial accounting. Zero connection to STOCKS-SEARCH-V1 or
PROSPECTIVE-SHADOW-V1 ledgers/registries.
"""
from __future__ import annotations

import time
import urllib.request
import json

import numpy as np
import pandas as pd

FAPI = "https://fapi.binance.com/fapi/v1/klines"
INTERVAL = "15m"
BARS_PER_YEAR = 4 * 24 * 365
FEE_BPS = 5.0        # taker fee per side
SLIP_BPS = 1.0       # slippage per side
FUNDING_BPS_PER_BAR = 1.0 / 32  # ~1bp per 8h funding, amortized per 15m bar


# ---------------------------------------------------------------- data

def fetch_klines(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    rows: list[list] = []
    cursor = start_ms
    while cursor < end_ms:
        url = f"{FAPI}?symbol={symbol}&interval={INTERVAL}&startTime={cursor}&endTime={end_ms}&limit=1500"
        with urllib.request.urlopen(url, timeout=30) as resp:
            batch = json.loads(resp.read())
        if not batch:
            break
        rows.extend(batch)
        cursor = int(batch[-1][6]) + 1
        if len(batch) < 1500:
            break
        time.sleep(0.15)
    df = pd.DataFrame(rows, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qvol", "trades", "tbb", "tbq", "ignore"])
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    df = df[["ts", "open", "high", "low", "close", "volume"]]
    df = df.drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
    return df


# ------------------------------------------------------------ indicators

def rsi_wilder(close: np.ndarray, period: int) -> np.ndarray:
    s = pd.Series(close)
    delta = s.diff()
    up = delta.clip(lower=0.0)
    dn = (-delta).clip(lower=0.0)
    # Wilder smoothing == EMA with alpha=1/period
    au = up.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    ad = dn.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = au / ad.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.fillna(50.0).to_numpy()


def rolling_max(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).max().to_numpy()


def rolling_min(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).min().to_numpy()


def rolling_mean(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).mean().to_numpy()


def rolling_std(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).std().to_numpy()


def sma(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n).mean().to_numpy()


# ------------------------------------------------- signal state machine

def hold_until(cond_long: np.ndarray, cond_short: np.ndarray, mode: str) -> np.ndarray:
    """pos: +1/-1 latched; cond_* fire entries; mode 'long' clips to 0/+1."""
    pos = np.zeros(len(cond_long), dtype=np.float64)
    cur = 0.0
    for i in range(len(pos)):
        if cond_short[i]:
            cur = -1.0
        elif cond_long[i]:
            cur = 1.0
        pos[i] = cur
    if mode == "long":
        np.clip(pos, 0.0, 1.0, out=pos)
    return pos


# ---------------------------------------------------------- backtest

def backtest(close: np.ndarray, signal: np.ndarray, lev: float) -> dict:
    n = len(close)
    r = np.zeros(n)
    r[1:] = close[1:] / close[:-1] - 1.0
    pos = signal * lev
    pos_prev = np.empty(n)
    pos_prev[0] = 0.0
    pos_prev[1:] = pos[:-1]
    turnover = np.abs(pos - pos_prev)
    fee = turnover * (FEE_BPS + SLIP_BPS) / 1e4
    funding = np.abs(pos_prev) * FUNDING_BPS_PER_BAR / 1e4
    bar_ret = pos_prev * r - fee - funding
    equity = np.cumprod(1.0 + bar_ret)
    total = float(equity[-1] - 1.0)
    sd = float(np.std(bar_ret))
    sharpe = float(np.mean(bar_ret) / sd * np.sqrt(BARS_PER_YEAR)) if sd > 0 else 0.0
    peak = np.maximum.accumulate(equity)
    maxdd = float(np.max(1.0 - equity / peak))
    # a trade = change in position sign (incl. 0->x entry, x->0 exit)
    sgn = np.sign(pos)
    changes = np.abs(np.diff(sgn, prepend=0.0))
    n_trades = int((changes > 0).sum())
    # per-trade pnl on sign-change segments
    win_rate = np.nan
    if n_trades > 0:
        idx = np.flatnonzero(changes > 0)
        seg_start = np.concatenate(([0], idx))
        seg_end = np.concatenate((idx, [n]))
        pnls = []
        for a, b in zip(seg_start, seg_end):
            seg = bar_ret[a:b]
            if len(seg):
                pnls.append(float(np.prod(1.0 + seg) - 1.0))
        if pnls:
            win_rate = float(np.mean([p > 0 for p in pnls]))
    years = n / BARS_PER_YEAR
    cagr = float(equity[-1] ** (1.0 / years) - 1.0) if equity[-1] > 0 else -1.0
    return {
        "total_return": total, "cagr": cagr, "sharpe": sharpe,
        "max_dd": maxdd, "n_trades": n_trades, "win_rate": win_rate,
        "avg_turnover": float(turnover.mean()),
    }


# ------------------------------------------------------ signal families

def sig_sma(close, fast, slow, mode):
    f, s = sma(close, fast), sma(close, slow)
    raw = np.where(np.isnan(f) | np.isnan(s), 0.0, np.where(f > s, 1.0, -1.0))
    if mode == "long":
        np.clip(raw, 0.0, 1.0, out=raw)
    return raw


def sig_donchian(close, n, m, mode):
    hi, lo = rolling_max(close, n), rolling_min(close, m)
    # channel ending at the PREVIOUS bar; current close must break it
    hi_prev = np.roll(hi, 1)
    lo_prev = np.roll(lo, 1)
    hi_prev[0] = np.nan
    lo_prev[0] = np.nan
    cl = close > hi_prev
    cs = close < lo_prev
    cl[~np.isfinite(hi_prev)] = False
    cs[~np.isfinite(lo_prev)] = False
    return hold_until(cl, cs, mode)


def sig_rsi_mr(close, period, lo, mode):
    r = rsi_wilder(close, period)
    return hold_until(r < lo, r > (100.0 - lo), mode)


def sig_tsmom(close, lb, mode):
    mom = close / np.roll(close, lb) - 1.0
    mom[:lb] = 0.0
    raw = np.sign(mom)
    if mode == "long":
        np.clip(raw, 0.0, 1.0, out=raw)
    return raw


def sig_boll_mr(close, period, k, mode):
    m, s = rolling_mean(close, period), rolling_std(close, period)
    upper, lower = m + k * s, m - k * s
    cl = close < lower
    cs = close > upper
    cl[~np.isfinite(lower)] = False
    cs[~np.isfinite(upper)] = False
    return hold_until(cl, cs, mode)


def build_grid():
    """[(family, params, signal_fn(close)->target exposure)]"""
    g = []
    for fast in (8, 16, 24, 32, 48, 64, 96):
        for slow in (96, 128, 192, 256, 384):
            if fast < slow:
                for mode in ("both", "long"):
                    g.append(("SMA_X", {"fast": fast, "slow": slow, "mode": mode},
                              lambda c, f=fast, s=slow, m=mode: sig_sma(c, f, s, m)))
    for n in (24, 48, 96, 192, 384):
        for m in (max(2, n // 2), n):
            for mode in ("both", "long"):
                g.append(("DONCH", {"n": n, "m": m, "mode": mode},
                          lambda c, n=n, m=m, md=mode: sig_donchian(c, n, m, md)))
    for period in (6, 14, 21, 42):
        for lo in (20, 25, 30):
            for mode in ("both", "long"):
                g.append(("RSI_MR", {"period": period, "lo": lo, "mode": mode},
                          lambda c, p=period, l=lo, m=mode: sig_rsi_mr(c, p, l, m)))
    for lb in (24, 48, 96, 192, 384, 768):
        for mode in ("both", "long"):
            g.append(("TSMOM", {"lb": lb, "mode": mode},
                      lambda c, lb=lb, m=mode: sig_tsmom(c, lb, m)))
    for period in (20, 40, 80):
        for k in (1.5, 2.0, 2.5, 3.0):
            for mode in ("both", "long"):
                g.append(("BOLL_MR", {"period": period, "k": k, "mode": mode},
                          lambda c, p=period, kk=k, m=mode: sig_boll_mr(c, p, kk, m)))
    return g


LEVERAGES = (1.0, 2.0, 3.0)
OOS_FRACTION = 0.20


def search_asset(close: np.ndarray, grid) -> list[dict]:
    n = len(close)
    split = int(n * (1.0 - OOS_FRACTION))
    rows = []
    for name, params, fn in grid:
        sig = fn(close)
        for lev in LEVERAGES:
            is_m = backtest(close[:split], sig[:split], lev)
            oos_m = backtest(close[split:], sig[split:], lev)
            rows.append({
                "family": name, "params": json.dumps(params, separators=(",", ":")),
                "lev": lev, **{f"is_{k}": v for k, v in is_m.items()},
                **{f"oos_{k}": v for k, v in oos_m.items()},
            })
    rows.sort(key=lambda r: r["is_total_return"], reverse=True)
    for i, r in enumerate(rows):
        r["is_rank"] = i + 1
    return rows


def buyhold_metrics(close: np.ndarray) -> dict:
    n = len(close)
    split = int(n * (1.0 - OOS_FRACTION))
    out = {}
    for tag, seg in (("is", close[:split]), ("oos", close[split:])):
        out[f"{tag}_total_return"] = float(seg[-1] / seg[0] - 1.0)
    return out


def equity_curve(close: np.ndarray, signal: np.ndarray, lev: float) -> pd.DataFrame:
    n = len(close)
    r = np.zeros(n)
    r[1:] = close[1:] / close[:-1] - 1.0
    pos = signal * lev
    pos_prev = np.empty(n)
    pos_prev[0] = 0.0
    pos_prev[1:] = pos[:-1]
    fee = np.abs(pos - pos_prev) * (FEE_BPS + SLIP_BPS) / 1e4
    funding = np.abs(pos_prev) * FUNDING_BPS_PER_BAR / 1e4
    bar_ret = pos_prev * r - fee - funding
    return pd.DataFrame({"bar_ret": bar_ret, "equity": np.cumprod(1.0 + bar_ret)})
