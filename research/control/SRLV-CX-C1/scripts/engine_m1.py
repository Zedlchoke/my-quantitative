"""SRLV-CX-C1 M1 SETTLE-RESOLVE engine — GO-2 scored execution.

Frozen by TRIAL_FREEZE_GO1.md sha 64aba7c3... + impl-pins (incl. pin 10:
TRUE flat-by-settlement subset for the anchor — any entry whose span would
contain a settlement instant [t_entry, t_exit] is SKIPPED so base-book
funding == 0 exactly, provable by fixture F-P1A-FLAT; the proposal-literal
span (crossing S_k) with MEASURED funding is a reported diagnostic only).
Deterministic: seed 20260926. Bar label = UTC open time (pin P0).
"""
import zipfile, csv, io, json, glob, random
from datetime import datetime, timezone
import numpy as np

BASE = "research/control/SRLV-CX-C1"
PAIRS = ["BTCUSDT", "ETHUSDT"]
TICKS = {"BTCUSDT": 0.1, "ETHUSDT": 0.01, "SOLUSDT": 0.01, "BNBUSDT": 0.01}
FEE_BPS = 5.0
SEED = 20260926
N_ANCHOR, N_NB1, N_NB2 = 6, 3, 10
BUF_ATR = 0.25
STOP_ATR = 1.0
RECLAIM_MAX = 3
FOLDS = [("F1", "2020-01-01", "2021-05-01"), ("F2", "2021-05-01", "2023-01-01"),
         ("F3", "2023-01-01", "2025-01-01"), ("F4", "2025-01-01", "2026-09-01")]
DEV_END = "2026-09-01"

def iso(t): return datetime.fromtimestamp(t/1000, tz=timezone.utc)
def ms(s):
    s = s if len(s) > 10 else s + "-01"
    return int(datetime.fromisoformat(s + "+00:00").timestamp()*1000)

def load_klines(pair):
    rows = []
    for z in sorted(glob.glob(f"{BASE}/data_local/vision/klines_um_{pair}_1h/*.zip")):
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                for r in csv.reader(io.TextIOWrapper(zf.open(name), "utf-8")):
                    if not r or not r[0].strip().isdigit(): continue
                    rows.append((int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    rows.sort(); seen = {}
    for r in rows: seen.setdefault(r[0], r)
    rows = [seen[k] for k in sorted(seen)]
    return dict(t=np.array([r[0] for r in rows], dtype=np.int64), o=np.array([r[1] for r in rows]),
                h=np.array([r[2] for r in rows]), l=np.array([r[3] for r in rows]),
                c=np.array([r[4] for r in rows]))

def load_settlements(pair):
    ts = set()
    if pair == "ETHUSDT":
        for z in sorted(glob.glob(f"{BASE}/data_local/vision/fundingRate_um_ETHUSDT/*.zip")):
            with zipfile.ZipFile(z) as zf:
                for name in zf.namelist():
                    for r in csv.reader(io.TextIOWrapper(zf.open(name), "utf-8")):
                        if r and r[0].strip().isdigit(): ts.add(int(r[0]))
    else:
        import pandas as pd
        df = pd.read_parquet(f"{BASE}/data_local/funding_events.parquet")
        ts = set(int(x) for x in df["ts"].astype(np.int64))
    arr = np.unique((np.array(sorted(ts), dtype=np.int64) // 3600000) * 3600000)
    gaps = np.unique(np.diff(arr) // 3600000)
    return arr, gaps

def load_rates(pair):
    rates = {}
    if pair == "ETHUSDT":
        for z in sorted(glob.glob(f"{BASE}/data_local/vision/fundingRate_um_ETHUSDT/*.zip")):
            with zipfile.ZipFile(z) as zf:
                for name in zf.namelist():
                    for r in csv.reader(io.TextIOWrapper(zf.open(name), "utf-8")):
                        if r and r[0].strip().isdigit():
                            rates[int((int(r[0])//3600000)*3600000)] = float(r[2])  # col2=rate; col1=interval_hours
    else:
        import pandas as pd
        df = pd.read_parquet(f"{BASE}/data_local/funding_events.parquet")
        # dtype is datetime64[ms, UTC]: astype(int64) already yields MILLISECONDS
        ts_ms = df["ts"].astype(np.int64)
        if ts_ms.iloc[0] < 10**12:  # ns-scale fallback safety
            ts_ms = ts_ms // 10**6
        for t_ms, rate in zip(ts_ms.tolist(), df["last_funding_rate"].tolist()):
            rates[int((int(t_ms)//3600000)*3600000)] = float(rate)
    return rates

def atr24(D):
    h, l, c = D["h"], D["l"], D["c"]
    n = len(c)
    tr = np.empty(n); tr[0] = h[0]-l[0]
    tr[1:] = np.maximum(h[1:]-l[1:], np.maximum(abs(h[1:]-c[:-1]), abs(l[1:]-c[:-1])))
    a = np.full(n, np.nan)
    cs = np.cumsum(tr)
    a[23:] = (cs[23:] - np.concatenate(([0.0], cs[:-24]))) / 24.0
    return a

def pivots(D, N):
    l, h = D["l"], D["h"]
    levels = []

    def strict_extreme(arr, N, is_low):
        out = []
        n = len(arr)
        for j in range(N, n-N):
            w = arr[j-N:j+N+1]
            v = arr[j]
            if is_low:
                if np.sum(w <= v) == 1: out.append(j)
            else:
                if np.sum(w >= v) == 1: out.append(j)
        return out
    for j in strict_extreme(l, N, True): levels.append((j, float(l[j]), "low"))
    for j in strict_extreme(h, N, False): levels.append((j, float(h[j]), "high"))
    levels.sort()
    return levels

def window_settlement(close_ms, sett, shift_hours):
    """S whose shifted window [S-1h,S+3h]+shift contains close_ms."""
    lo = close_ms - (3 + shift_hours)*3600000
    hi = close_ms + (1 - shift_hours)*3600000
    i0 = np.searchsorted(sett, lo, side="left")
    for idx in range(i0, min(i0+4, len(sett))):
        S = sett[idx]
        wlo = S - 3600000 + shift_hours*3600000
        whi = S + 3*3600000 + shift_hours*3600000
        if wlo <= close_ms <= whi: return int(S)
    return None

def fold_of(ts):
    d = iso(ts).strftime("%Y-%m-%d")
    for (name, a, b) in FOLDS:
        if a <= d < b: return name
    return None

def candidate_events(D, sett, N=6, shift_hours=0, ungated=False, delay=0,
                     placebo_offsets=None, literal_span=False, pair=""):
    """Generate all candidate sweep->reclaim events (before one-position greedy)."""
    t, o, h, l, c = D["t"], D["o"], D["h"], D["l"], D["c"]
    n = len(t); A = atr24(D); close_ms = t + 3600000
    levels = pivots(D, N)
    if placebo_offsets:
        levels = sorted((j + placebo_offsets.get(j, 0), p, s) for (j, p, s) in levels)
    cands = []
    dev_end = ms(DEV_END)
    for (j, price, side) in levels:
        start = j + N + 1
        if start >= n: continue
        seg = c[j+N:n]
        beyond = (seg < price) if side == "low" else (seg > price)
        nz = np.nonzero(beyond)[0]
        intact_until = (j+N + int(nz[0])) if len(nz) else n
        if intact_until <= start: continue
        sw = np.nonzero((l[start:intact_until] < price) if side == "low"
                        else (h[start:intact_until] > price))[0]
        for k in sw:
            s = start + int(k)
            if not ungated:
                if window_settlement(int(close_ms[s]), sett, shift_hours) is None: continue
            ev = None
            for cc in range(s+1, min(s+RECLAIM_MAX, intact_until-1)+1):
                if cc >= n: break
                if np.isnan(A[cc]): break
                if side == "low" and c[cc] < price - BUF_ATR*A[cc]: ev = ("bd", cc); break
                if side == "high" and c[cc] > price + BUF_ATR*A[cc]: ev = ("bd", cc); break
                if side == "low" and c[cc] > price: ev = ("rc", cc); break
                if side == "high" and c[cc] < price: ev = ("rc", cc); break
            if not ev or ev[0] != "rc": continue
            cc = ev[1]
            e0 = cc + 1 + delay
            if e0 >= n or t[e0] >= dev_end: continue
            S_ev = window_settlement(int(close_ms[s]), sett, 0)
            if S_ev is None: S_ev = int(close_ms[s])
            i1 = np.searchsorted(sett, S_ev, side="right")
            S_next = int(sett[i1]) if i1 < len(sett) else None
            if S_next is None: continue
            pre = np.searchsorted(close_ms, S_next - 2*3600000, side="right") - 1
            settle_exit = int(pre) + 1 if pre >= 0 else None
            if settle_exit is None or settle_exit <= e0: continue
            exit_i, why = settle_exit, "settle"
            for e in range(e0+1, min(settle_exit+1, n)):
                if side == "low":
                    if c[e] < price: exit_i, why = e+1, "reclaim"; break
                    if c[e] < l[s] - STOP_ATR*A[e]: exit_i, why = e+1, "stop"; break
                else:
                    if c[e] > price: exit_i, why = e+1, "reclaim"; break
                    if c[e] > h[s] + STOP_ATR*A[e]: exit_i, why = e+1, "stop"; break
            if exit_i >= n or exit_i <= e0: continue
            if fold_of(int(t[e0])) is None or fold_of(int(t[e0])) != fold_of(int(t[exit_i])): continue
            span_ok = True
            if not literal_span:
                # pin-10: no settlement instant in [t_entry, t_exit]
                a_, b_ = int(t[e0]), int(t[exit_i])
                i0 = np.searchsorted(sett, a_, side="left")
                if i0 < len(sett) and sett[i0] <= b_: span_ok = False
            if not span_ok: continue
            cands.append(dict(j=j, price=price, side=side, s=s, c_bar=cc,
                              entry_i=e0, exit_i=exit_i, why=why,
                              dir=1 if side == "low" else -1,
                              entry=float(o[e0]), exit=float(o[exit_i]),
                              t_entry=int(t[e0]), t_exit=int(t[exit_i])))
    cands.sort(key=lambda x: x["t_entry"])
    return cands

def greedy_one_pos(cands):
    kept, busy = [], -1
    for ev in cands:
        if ev["entry_i"] > busy:
            kept.append(ev); busy = ev["exit_i"]
    return kept

def run_book(D, sett, **kw):
    cands = candidate_events(D, sett, **kw)
    return greedy_one_pos(cands)

def pnl_of(trades, pair, fee_mult=1.0, flip=False, rates=None, sett=None):
    tick = TICKS[pair]; out = []
    for tr in trades:
        d = -tr["dir"] if flip else tr["dir"]
        gross = d*(tr["exit"]-tr["entry"])/tr["entry"]*1e4
        tb = tick/tr["entry"]*1e4
        cost = 2.0*fee_mult*(FEE_BPS+tb)
        out.append(gross-cost)
    return out

def funding_between(rates, sett_arr, a_ms, b_ms, direction):
    i0 = np.searchsorted(sett_arr, a_ms, side="left")
    tot = 0.0
    while i0 < len(sett_arr) and sett_arr[i0] <= b_ms:
        tot += rates.get(int(sett_arr[i0]), 0.0); i0 += 1
    return tot*1e4*(1 if direction == 1 else -1)  # long pays positive rates

def stats(pnls):
    if not pnls: return dict(n=0, net=0.0, pf=None, mean=0.0, win_rate=0.0)
    a = np.array(pnls); g = a[a > 0].sum(); ls = -a[a < 0].sum()
    return dict(n=len(a), net=float(a.sum()), mean=float(a.mean()),
                pf=float(g/ls) if ls > 0 else (None if g == 0 else 99.0),
                win_rate=float((a > 0).mean()))

def fold_split(trades, pnls):
    out = {}
    for tr, p in zip(trades, pnls):
        out.setdefault(fold_of(tr["t_entry"]) or "SEAM", []).append(p)
    return {k: float(np.sum(v)) for k, v in out.items()}

def direction_split(trades, pnls):
    out = {}
    for tr, p in zip(trades, pnls):
        out.setdefault("long" if tr["dir"] == 1 else "short", []).append(p)
    return {k: dict(n=len(v), net=float(np.sum(v))) for k, v in out.items()}

def concentration(trades, pnls):
    f = fold_split(trades, pnls)
    pos = {k: v for k, v in f.items() if v > 0}; tot = sum(pos.values())
    if tot <= 0: return None
    return max(pos.values())/tot

def daily_series(trades, pnls):
    agg = {}
    for tr, p in zip(trades, pnls):
        agg[iso(tr["t_entry"]).strftime("%Y-%m-%d")] = agg.get(iso(tr["t_entry"]).strftime("%Y-%m-%d"), 0.0)+p
    return agg

def baselines(D, sett, rates, pair):
    t, o, c = D["t"], D["o"], D["c"]; n = len(t); tick = TICKS[pair]
    i0 = 720; i1 = int(np.searchsorted(t, ms(DEV_END))-1)
    lh_gross = (o[i1]-o[i0])/o[i0]*1e4
    lh_cost = 2*(FEE_BPS + tick/o[i0]*1e4)
    lh_fund = funding_between(rates, sett, int(t[i0]), int(t[i1]), 1)
    sma = np.full(n, np.nan); cs = np.cumsum(c)
    sma[719:] = (cs[719:]-np.concatenate((np.zeros(1), cs[:-720])))/720.0
    net = 0.0; prev_i = None; fund = 0.0
    for i in range(719, i1):
        want = 1 if c[i] > sma[i] else 0
        have = 0 if prev_i is None else (1 if c[prev_i] > sma[prev_i] else 0)
        if want != have:
            if have == 1:
                g = (o[i]-o[prev_i])/o[prev_i]*1e4
                f = funding_between(rates, sett, int(t[prev_i]), int(t[i]), 1)
                net += g - 2*(FEE_BPS+tick/o[prev_i]*1e4) - f; fund -= f
            if want == 1: prev_i = i
            else: prev_i = i
        if want == 1: prev_i = prev_i  # hold
        else: prev_i = i if have == 1 else prev_i
    # simpler recompute for correctness
    net = 0.0; fund = 0.0; pos = 0; e_i = None
    for i in range(719, i1+1):
        want = 1 if c[i] > sma[i] else 0
        if want != pos:
            if pos == 1:
                g = (o[i]-o[e_i])/o[e_i]*1e4
                f = funding_between(rates, sett, int(t[e_i]), int(t[i]), 1)
                net += g - 2*(FEE_BPS+tick/o[e_i]*1e4) - f; fund += f
            pos = want; e_i = i
    return dict(long_hold=dict(net=float(lh_gross-lh_cost-lh_fund), funding_bps=float(lh_fund)),
                trend_sma720=dict(net=float(net), funding_bps=float(fund)))

# ------------- shadows (frozen representations, impl-pin 3) -------------
def _shadow_trades_pnl(trades, pair):
    tick = TICKS[pair]; out = []
    for tr in trades:
        out.append(tr["dir"]*(tr["exit"]-tr["entry"])/tr["entry"]*1e4 - 2*(FEE_BPS+tick/tr["entry"]*1e4))
    return out

def shadow_bandfade(D):
    t, o, h, l, c = D["t"], D["o"], D["h"], D["l"], D["c"]; n = len(t)
    days = np.array([iso(x).strftime("%Y-%m-%d") for x in t]); uniq = sorted(set(days.tolist()))
    idx_by_day = {d: np.nonzero(days == d)[0] for d in uniq}
    trades = []
    for di in range(1, len(uniq)):
        pd_ = uniq[di-1]; d = uniq[di]
        pi = idx_by_day[pd_]
        H = float(h[pi].max()); L = float(l[pi].min())
        for s in idx_by_day[d]:
            if s+4 >= n or t[s+1] >= ms(DEV_END): break
            if l[s] < L and c[s] > L:
                trades.append(dict(dir=1, entry=float(o[s+1]), exit=float(o[s+4]), t_entry=int(t[s+1]))); break
            if h[s] > H and c[s] < H:
                trades.append(dict(dir=-1, entry=float(o[s+1]), exit=float(o[s+4]), t_entry=int(t[s+1]))); break
    return trades

def shadow_donchian168(D):
    t, o, h, l, c = D["t"], D["o"], D["h"], D["l"], D["c"]; n = len(t)
    trades = []; pos = 0; ep = 0.0; et = 0
    for i in range(168, n):
        hh = h[i-168:i].max(); ll = l[i-168:i].min()
        sig = 1 if c[i] > hh else (-1 if c[i] < ll else pos)
        if sig != pos:
            if pos != 0 and t[i] < ms(DEV_END):
                trades.append(dict(dir=pos, entry=ep, exit=float(c[i]), t_entry=et))
            pos = sig; ep = float(c[i]); et = int(t[i])
    if pos != 0: trades.append(dict(dir=pos, entry=ep, exit=float(c[-1]), t_entry=et))
    return trades

def shadow_cng2(D, sett):
    t, o, c = D["t"], D["o"], D["c"]; n = len(t); trades = []
    for S in sett:
        lo, hi = S-2*3600000, S+2*3600000
        idx = np.nonzero((t >= lo) & (t <= hi))[0]
        if len(idx) < 5: continue
        first, last = int(idx[0]), int(idx[-1])
        pre = int(np.searchsorted(t, S-24*3600000, side="right"))-1
        if pre < 24 or last+1 >= n or t[last+1] >= ms(DEV_END): continue
        d = 1 if c[pre] > c[pre-24] else -1
        trades.append(dict(dir=d, entry=float(o[first]), exit=float(o[last+1]), t_entry=int(t[first])))
    return trades

def shadow_rev24(D):
    t, o, c = D["t"], D["o"], D["c"]; n = len(t); trades = []; busy = -1
    for i in range(24, n-6):
        if i <= busy: continue
        r = (c[i]-c[i-24])/c[i-24]
        if abs(r) > 0.02 and t[i+1] < ms(DEV_END):
            d = -1 if r > 0 else 1
            trades.append(dict(dir=d, entry=float(o[i+1]), exit=float(o[i+5]), t_entry=int(t[i+1])))
            busy = i+5
    return trades

def rho_daily(a, b):
    keys = sorted(set(a) | set(b))
    xa = np.array([a.get(k, 0.0) for k in keys]); xb = np.array([b.get(k, 0.0) for k in keys])
    if xa.std() == 0 or xb.std() == 0: return 0.0
    return float(np.corrcoef(xa, xb)[0, 1])
