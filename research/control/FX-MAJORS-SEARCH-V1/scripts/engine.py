"""Backtest engine + families for EURUSD-OPEN-SEARCH-V1 (frozen semantics v1).

Semantics (preregistered in plans/PLAN_eurusd_open_search_v1.md §4-§6 and
selection_freeze.json — change requires a new amendment BEFORE outcomes):

- Signal on CLOSED 15m bar t uses data <= t only (PIT). Fill at t+1 open.
- Marketable fills at the OPPOSITE side: buy at bid_o + k*s_open,
  sell (entry short) at ask_o - k*s_open, close long at ask_c - k*s_close,
  close short at bid_c + k*s_close. k = cost multiplier {1.0, 1.5, 2.0};
  k=1.0 is the measured spread, k>1 is stress.
- Force-flat law: no position may exist at/after the 21:00 UTC rollover or
  over the weekend. The last fill-eligible entry is the signal on the bar
  BEFORE the 20:45 bar (fills at 20:45 open); every open position is closed
  at the close of the last valid bar strictly before 21:00 of its day.
- pips: price units × 1e4. Costs are inside the fills (charged exactly once
  per side, i.e., round trip = one spread crossing at entry + one at exit).
- Gates (frozen): G1 net>0 @k=1; G2 PF>=1.10; G3 >=2/3 folds net>0;
  G4 net>0 @k=1.5; G5 trades>=30.
"""
import hashlib
import json

import numpy as np
import pandas as pd

PIP = 1e4
SEC_DAY = 86400


def session_of(ts_epoch):
    """Return UTC hhmm*100 for bar-open timestamps (epoch seconds)."""
    h = (ts_epoch // 3600) % 24
    m = (ts_epoch // 60) % 60
    return h * 100 + m


class Plane:
    """Valid 15m bars + derived session metadata."""

    def __init__(self, df):
        # pandas >=3 may carry datetimes at us resolution; normalize through
        # numpy datetime64[s] so epoch seconds are unit-independent (the
        # fixture suite caught a real force-flat calendar break here).
        self.ts = (df["ts"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy().astype("datetime64[s]").astype("int64"))
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
        # hours-of-day helper for families
        self.hour = (self.ts // 3600 % 24).astype(np.int32)
        self.minute = (self.ts // 60 % 60).astype(np.int32)


def run_strategy(plane, target, k, warmup_end_idx=0, pip=None):
    """pip: price units per pip (default PIP=1e4 = EURUSD convention).
    PnL is reported in pips of the instrument's own pip size."""
    """target[i] in {-1,0,+1}: desired position while bar i is the signal bar.

    Fill semantics (all at effective prices with stress multiplier k):
      open long  = buy  at ask_eff(open) = b_o + k*s_o
      open short = sell at bid_eff(open) = a_o - k*s_o
      close long = sell at bid_eff(open/close)
      close short= buy  at ask_eff(open/close)
    Reversals exit and enter at the same bar open. Force-flat at the close of
    each day's last valid bar (no position survives 21:00 UTC by construction).
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
        pnl = (exit_px - entry_px) * pos * (PIP if pip is None else (1.0 / pip))
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


# ---------------- families (all signals PIT: use data up to bar i) ----------

def _sma(x, w):
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = np.full(len(x), np.nan)
    out[w - 1:] = (c[w:] - c[:-w]) / w
    return out


def _ema(x, w):
    a = 2.0 / (w + 1)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def _roll_sd(x, w):
    s1 = _sma(x, w)
    s2 = _sma(x * x, w)
    var = s2 - s1 ** 2
    return np.sqrt(np.maximum(var, 0))


def _atr(plane, w):
    tr = np.maximum.reduce([
        plane.b_h - plane.b_l,
        np.abs(plane.b_h - np.roll(plane.b_c, 1)),
        np.abs(plane.b_l - np.roll(plane.b_c, 1)),
    ])
    tr[0] = plane.b_h[0] - plane.b_l[0]
    return _sma(tr, w)


def _roll_hi_lo(p, L):
    hi = pd.Series(p.b_h).rolling(L).max().shift(1).to_numpy()
    lo = pd.Series(p.b_l).rolling(L).min().shift(1).to_numpy()
    return hi, lo


def f_donch(p, L, hold_mult):
    """Donchian breakout vs PRIOR L bars' high/low; time stop + opposite exit."""
    import pandas as pd

    hi, lo = _roll_hi_lo(p, L)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    pos = 0
    hold = 0
    for i in range(len(p.b_c)):
        if pos != 0:
            hold -= 1
            if hold <= 0 or (pos > 0 and p.b_c[i] < lo[i]) or (pos < 0 and p.b_c[i] > hi[i]):
                pos = 0
        if pos == 0 and not np.isnan(hi[i]):
            if p.b_c[i] > hi[i]:
                pos, hold = 1, int(hold_mult * L)
            elif p.b_c[i] < lo[i]:
                pos, hold = -1, int(hold_mult * L)
        tgt[i] = pos
    return tgt


def f_emacross(p, fast, slow):
    ef = _ema(p.b_c, fast); es = _ema(p.b_c, slow)
    return np.where(np.isnan(ef) | np.isnan(es), 0, np.sign(ef - es)).astype(np.int8)


def f_tsmom(p, K):
    r = np.full(len(p.b_c), 0.0)
    r[K:] = p.b_c[K:] - p.b_c[:-K]
    return np.sign(r).astype(np.int8)


def f_bollfade(p, N, z_in):
    m = _sma(p.b_c, N); sd = _roll_sd(p.b_c, N)
    z = np.where(sd > 0, (p.b_c - m) / sd, 0.0)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    pos = 0
    for i in range(len(p.b_c)):
        if pos == 0:
            if z[i] > z_in: pos = -1
            elif z[i] < -z_in: pos = 1
        else:
            if abs(z[i]) < 0.25: pos = 0
        tgt[i] = pos
    return tgt


def f_rsifade(p, N, th):
    d = np.diff(p.b_c, prepend=p.b_c[0])
    up = _sma(np.maximum(d, 0), N); dn = _sma(np.maximum(-d, 0), N)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.where(dn > 0, up / np.where(dn == 0, 1.0, dn), 100.0)
    rsi = 100 - 100 / (1 + rs)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    pos = 0
    for i in range(len(p.b_c)):
        if pos == 0:
            if rsi[i] > 100 - th: pos = -1
            elif rsi[i] < th: pos = 1
        elif (pos > 0 and rsi[i] > 50) or (pos < 0 and rsi[i] < 50):
            pos = 0
        tgt[i] = pos
    return tgt


def f_failbreak(p, L, J):
    """Failed breakout: bar pokes beyond prior-L extreme but closes back inside."""
    hi, lo = _roll_hi_lo(p, L)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    pos = 0
    hold = 0
    for i in range(len(p.b_c)):
        if pos != 0:
            hold -= 1
            if hold <= 0:
                pos = 0
        if pos == 0 and not np.isnan(hi[i]):
            if p.b_h[i] > hi[i] and p.b_c[i] < hi[i]:
                pos, hold = -1, J
            elif p.b_l[i] < lo[i] and p.b_c[i] > lo[i]:
                pos, hold = 1, J
        tgt[i] = pos
    return tgt


def f_atrbreak(p, L, N):
    atr = _atr(p, N)
    atr_lag = np.roll(atr, 96)  # one day earlier (96x15m)
    hi, lo = _roll_hi_lo(p, L)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    pos = 0
    for i in range(len(p.b_c)):
        calm = atr[i] < atr_lag[i]
        if pos == 0 and calm and not np.isnan(hi[i]):
            if p.b_c[i] > hi[i]:
                pos = 1
            elif p.b_c[i] < lo[i]:
                pos = -1
        elif pos != 0:
            if (pos > 0 and p.b_c[i] < lo[i]) or (pos < 0 and p.b_c[i] > hi[i]):
                pos = 0
        tgt[i] = pos
    return tgt


def f_squeeze(p, K, qth):
    import pandas as pd

    rng = p.b_h - p.b_l
    base = pd.Series(rng).rolling(K).quantile(qth).shift(1).to_numpy()
    hi, lo = _roll_hi_lo(p, K)
    tgt = np.zeros(len(rng), dtype=np.int8)
    pos = 0
    for i in range(len(rng)):
        if pos == 0:
            if not np.isnan(base[i]) and rng[i] < base[i]:
                if p.b_c[i] > hi[i]:
                    pos = 1
                elif p.b_c[i] < lo[i]:
                    pos = -1
        else:
            if (pos > 0 and p.b_c[i] < lo[i]) or (pos < 0 and p.b_c[i] > hi[i]):
                pos = 0
        tgt[i] = pos
    return tgt


def _session_or_mask(p, h0, h1):
    return (p.hour >= h0) & (p.hour < h1)


def f_session_momentum(p, h0, h1, hold_bars):
    """Opening-range breakout of [h0,h1) UTC traded until h1+6h (max 21:00)."""
    or_h = _session_or_mask(p, h0, h1)
    days = np.unique(p.day)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    pos = 0
    hold = 0
    day_or = {}
    m = or_h
    for d in days:
        mm = m & (p.day == d)
        if mm.any():
            day_or[d] = (p.b_h[mm].max(), p.b_l[mm].min())
    for i in range(len(p.b_c)):
        if pos != 0:
            hold -= 1
            if hold <= 0:
                pos = 0
        d = p.day[i]
        if pos == 0 and d in day_or and p.hour[i] >= h1 and p.hour[i] < min(h1 + 6, 21):
            hi, lo = day_or[d]
            if p.b_c[i] > hi: pos, hold = 1, hold_bars
            elif p.b_c[i] < lo: pos, hold = -1, hold_bars
        tgt[i] = pos
    return tgt


def f_todseason(p, win_days):
    """Time-of-day momentum from a TRAILING window of win_days only (PIT-safe).

    For each bar i (liquid hours 08-20 UTC): sign of the trailing win_days sum
    of that hour's 15m returns, evaluated only after a full window exists.
    """
    r = np.zeros(len(p.b_c))
    r[1:] = p.b_c[1:] - p.b_c[:-1]
    day_u, day_idx = np.unique(p.day, return_inverse=True)
    n_days = len(day_u)
    S = np.zeros((n_days, 24))
    np.add.at(S, (day_idx, p.hour), r)
    C = np.zeros((n_days, 24))
    np.add.at(C, (day_idx, p.hour), 1.0)
    CS = np.cumsum(S, axis=0)
    CC = np.cumsum(C, axis=0)
    tgt = np.zeros(len(p.b_c), dtype=np.int8)
    liq = (p.hour >= 8) & (p.hour < 20)
    for i in np.nonzero(liq)[0]:
        d_i = day_idx[i]
        if d_i < win_days:
            continue
        h = p.hour[i]
        s = CS[d_i - 1, h] - (CS[d_i - 1 - win_days, h] if d_i - 1 - win_days >= 0 else 0.0)
        c = CC[d_i - 1, h] - (CC[d_i - 1 - win_days, h] if d_i - 1 - win_days >= 0 else 0.0)
        if c >= win_days * 2:
            tgt[i] = 1 if s > 0 else (-1 if s < 0 else 0)
    return tgt


FAMILIES = {
    "FXOS-02": {
        "fn": lambda p, c: f_donch(p, c["L"], c["hold_mult"]),
        "configs": [
            {"L": 96, "hold_mult": 4}, {"L": 192, "hold_mult": 4},
            {"L": 384, "hold_mult": 3}, {"L": 96, "hold_mult": 8},
        ],
    },
    "FXOS-01": {
        "fn": lambda p, c: f_emacross(p, c["fast"], c["slow"]),
        "configs": [
            {"fast": 16, "slow": 64}, {"fast": 32, "slow": 128},
            {"fast": 64, "slow": 256}, {"fast": 96, "slow": 384},
        ],
    },
    "FXOS-03": {
        "fn": lambda p, c: f_tsmom(p, c["K"]),
        "configs": [
            {"K": 24}, {"K": 96}, {"K": 192}, {"K": 384},
        ],
    },
    "FXOS-04": {
        "fn": lambda p, c: f_bollfade(p, c["N"], c["z_in"]),
        "configs": [
            {"N": 96, "z_in": 2.0}, {"N": 96, "z_in": 2.5},
            {"N": 192, "z_in": 2.0}, {"N": 192, "z_in": 2.5},
        ],
    },
    "FXOS-05": {
        "fn": lambda p, c: f_rsifade(p, c["N"], c["th"]),
        "configs": [
            {"N": 28, "th": 35}, {"N": 28, "th": 30},
            {"N": 56, "th": 35}, {"N": 56, "th": 30},
        ],
    },
    "FXOS-07": {
        "fn": lambda p, c: f_failbreak(p, c["L"], c["J"]),
        "configs": [
            {"L": 48, "J": 4}, {"L": 48, "J": 8},
            {"L": 96, "J": 4}, {"L": 96, "J": 8},
        ],
    },
    "FXOS-08": {
        "fn": lambda p, c: f_atrbreak(p, c["L"], c["N"]),
        "configs": [
            {"L": 96, "N": 96}, {"L": 96, "N": 192},
            {"L": 192, "N": 96}, {"L": 192, "N": 192},
        ],
    },
    "FXOS-09": {
        "fn": lambda p, c: f_squeeze(p, c["K"], c["q"]),
        "configs": [
            {"K": 32, "q": 0.2}, {"K": 32, "q": 0.3},
            {"K": 96, "q": 0.2}, {"K": 96, "q": 0.3},
        ],
    },
    "FXOS-10": {
        "fn": lambda p, c: f_session_momentum(p, c["h0"], c["h1"], c["hold"]),
        "configs": [
            {"h0": 7, "h1": 8, "hold": 16}, {"h0": 7, "h1": 9, "hold": 16},
            {"h0": 7, "h1": 8, "hold": 32}, {"h0": 6, "h1": 8, "hold": 24},
        ],
    },
    "FXOS-11": {
        "fn": lambda p, c: f_session_momentum(p, c["h0"], c["h1"], c["hold"]),
        "configs": [
            {"h0": 12, "h1": 13, "hold": 16}, {"h0": 12, "h1": 14, "hold": 16},
            {"h0": 12, "h1": 13, "hold": 32}, {"h0": 13, "h1": 14, "hold": 24},
        ],
    },
    "FXOS-24": {
        "fn": lambda p, c: f_todseason(p, c["win_days"]),
        "configs": [
            {"win_days": 60}, {"win_days": 120},
            {"win_days": 40}, {"win_days": 90},
        ],
    },
    "FXOS-12": {
        "fn": lambda p, c: f_session_momentum(p, c["h0"], c["h1"], c["hold"]),
        "configs": [
            {"h0": 12, "h1": 16, "hold": 16}, {"h0": 13, "h1": 16, "hold": 16},
            {"h0": 12, "h1": 16, "hold": 8}, {"h0": 14, "h1": 17, "hold": 12},
        ],
    },
}


def config_digest(family_id, cfg):
    blob = json.dumps({"family": family_id, "config": cfg}, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]
