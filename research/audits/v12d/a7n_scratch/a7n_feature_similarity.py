"""A7-N scratch: cross-proposal FEATURE rank-similarity on the frozen S0 window.

Read-only on raw data (catalog_live_crypto/data). Computes PIT feature
cross-sectional ranks at Monday 00:00Z stamps exactly as each proposal's
formation rule defines them. NO PnL, NO strategy/book returns, NO backtest.

Features (per proposal anchor):
  beta90      : A5-P1 / A8-P1  OLS beta of daily log returns vs BTC over
                               trailing 90d daily block (identical estimator)
  ticket_a5p2 : A5-P2         mean(qv/count) over (T-30d,T] divided by mean
                              over (T-60d,T-30d], bars with count>0
  ticket_a8p2 : A8-P2         weekly ticket sum(qv)/sum(count) over (T-7d,T]
                              divided by the median of the trailing 12 weekly
                              tickets inside the same 90d window
  ticket_a6p1 : A6-P1 (OSCOMP) sum(qv)/sum(count) level over (T-28d,T]
  mom90, mom28: diagnostics only - trailing-return ranks (V4-XSECT-MOM
                              ancestor feature), used to test whether any
                              proposal's feature collapses into a momentum rank
  amihud28    : diagnostic only - 28d mean |r|/dollar-volume (reserved ILLIQ
                              ancestor feature) used ONLY to measure how far
                              the ticket features sit from the reserved identity

H-A6-RVX is a state-dependent pairs book (no per-stamp single-name rank
vector) -> NOT_COMPUTED, reason recorded.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import numpy as np
import pyarrow.parquet as pq

BARS_ROOT = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/binance_bar"
SYMBOLS = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT", "BCHUSDT",
    "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT", "ENAUSDT", "ETHUSDT",
    "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT", "SUIUSDT", "WLDUSDT",
    "XRPUSDT", "ZECUSDT",
]
TRADED = [s for s in SYMBOLS if s != "BTCUSDT"]
DAY = 86_400 * 10**9
WEEK = 7 * DAY
NS_PER_15M = 900 * 10**9

OUT = {}


def snap_to_slot(ts: np.ndarray) -> np.ndarray:
    r = ts % NS_PER_15M
    d = (NS_PER_15M - r) % NS_PER_15M
    return np.where(d < NS_PER_15M // 2, ts + d, ts)


def load_symbol(sym: str):
    d = os.path.join(BARS_ROOT, f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
    files = sorted(os.listdir(d))
    closes, qvs, counts, tss = [], [], [], []
    prec = None
    for fn in files:
        t = pq.read_table(os.path.join(d, fn))
        md = t.schema.metadata or {}
        if prec is None:
            for k, v in md.items():
                if k == b"price_precision":
                    prec = int(v.decode())
        df = t.select(["close", "quote_volume", "count", "ts_event"]).to_pandas()
        raw = np.array([int.from_bytes(b, "big") for b in df["close"].values], dtype=np.float64)
        closes.append(raw / (10**prec))
        qvs.append(df["quote_volume"].astype(float).values)
        counts.append(df["count"].astype(np.int64).values)
        tss.append(df["ts_event"].values.astype(np.int64))
    ts = np.unique(np.concatenate(tss))
    idx = {v: i for i, v in enumerate(ts)}
    close = np.empty(len(ts)); qv = np.empty(len(ts)); cnt = np.empty(len(ts), dtype=np.int64)
    # merge in ts order
    all_rows = sorted(
        zip(np.concatenate(tss).tolist(),
            np.concatenate(closes).tolist(),
            np.concatenate(qvs).tolist(),
            np.concatenate(counts).tolist())
    )
    for i, (t, c, q, n) in enumerate(all_rows):
        close[i] = c; qv[i] = q; cnt[i] = n
    ts = np.array([r[0] for r in all_rows], dtype=np.int64)
    ts = snap_to_slot(ts)
    return ts, close, qv, cnt, prec


def daily_closes(ts, close):
    """Last completed bar close per UTC day (strictly at-or-before day end)."""
    day_idx = ts // DAY
    days, last_close = [], []
    for d in np.unique(day_idx):
        m = day_idx == d
        days.append(int(d))
        last_close.append(close[m][-1] if close[m].size else np.nan)
    return np.array(days, dtype=np.int64), np.array(last_close)


def monday_stamps(start_ns, end_ns):
    """Mondays 00:00Z, strictly after start, at or before end."""
    t = start_ns
    # ceil to Monday 00:00Z
    off = 4 * DAY
    r = t % WEEK
    delta = off - r
    if delta < 0:
        delta += WEEK
    t += delta
    out = []
    while t <= end_ns:
        out.append(t)
        t += WEEK
    return out


def spearman(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) < 3:
        return np.nan
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return np.nan
    return float(np.corrcoef(ra, rb)[0, 1])


# ---------------------------------------------------------------- load data
data = {}
for sym in SYMBOLS:
    ts, close, qv, cnt, prec = load_symbol(sym)
    days, dc = daily_closes(ts, close)
    data[sym] = {"ts": ts, "close": close, "qv": qv, "cnt": cnt,
                 "days": days, "dc": dc, "prec": prec}
    print(sym, "prec", prec, "bars", len(ts), "first", datetime.fromtimestamp(ts[0] / 1e9, tz=timezone.utc).isoformat(), "days", len(days))

btc_days = data["BTCUSDT"]["days"]
btc_dc = data["BTCUSDT"]["dc"]
btc_ret_by_day = {}
for i in range(1, len(btc_days)):
    btc_ret_by_day[int(btc_days[i])] = np.log(btc_dc[i] / btc_dc[i - 1])

WINDOW_START = datetime(2025, 8, 22, tzinfo=timezone.utc).timestamp() * 1e9
WINDOW_END = datetime(2026, 8, 21, tzinfo=timezone.utc).timestamp() * 1e9
PRE_END = WINDOW_START  # prewindow stamps: strictly before 2025-08-22

stamps_window = monday_stamps(int(WINDOW_START), int(WINDOW_END))
stamps_pre = monday_stamps(int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1e9), int(PRE_END) - 1)


def features_at(T: int) -> dict:
    """PIT features at Monday 00:00Z stamp T (all inputs at-or-before T)."""
    out = {}
    day_of_T = int(T // DAY)
    for sym in TRADED:
        d = data[sym]
        days, dc, ts, qv, cnt = d["days"], d["dc"], d["ts"], d["qv"], d["cnt"]
        # --- 90d daily block: days (T-90d, T]
        lo_d = day_of_T - 90
        mask = (days > lo_d) & (days <= day_of_T)
        blk_days = days[mask]
        blk_dc = dc[mask]
        f = {}
        # daily returns with BTC pairing
        rets_sym, rets_btc = [], []
        dc_map = dict(zip(days.tolist(), dc.tolist()))
        for dd in blk_days[1:]:
            prev = int(dd) - 1
            if prev in dc_map and np.isfinite(dc_map[prev]) and np.isfinite(dc_map[int(dd)]) \
                    and int(dd) in btc_ret_by_day:
                rets_sym.append(np.log(dc_map[int(dd)] / dc_map[prev]))
                rets_btc.append(btc_ret_by_day[int(dd)])
        n_pairs = len(rets_sym)
        if n_pairs >= 30:
            rs = np.array(rets_sym); rb = np.array(rets_btc)
            var_b = rb.var()
            f["beta90"] = float(np.cov(rs, rb)[0, 1] / var_b) if var_b > 0 else np.nan
            f["beta_npairs"] = n_pairs
            f["mom90"] = float(rs.sum())
        # 28d momentum
        mask28 = (days > day_of_T - 28) & (days <= day_of_T)
        bd = days[mask28]
        r28 = []
        for dd in bd[1:]:
            prev = int(dd) - 1
            if prev in dc_map and np.isfinite(dc_map[prev]) and np.isfinite(dc_map[int(dd)]):
                r28.append(np.log(dc_map[int(dd)] / dc_map[prev]))
        if len(r28) >= 20:
            f["mom28"] = float(np.sum(r28))
        # --- 15m-based ticket features
        slot_lo_28 = T - 28 * DAY
        m28 = (ts > slot_lo_28) & (ts <= T)
        v28 = cnt[m28] > 0
        if m28.sum() > 0:
            f["ticket_a6p1"] = float(qv[m28][v28].sum() / max(cnt[m28][v28].sum(), 1))
            f["cov28"] = float(v28.mean())
        # A5P2: 30d vs prior 60d
        m30 = (ts > T - 30 * DAY) & (ts <= T)
        m60 = (ts > T - 90 * DAY) & (ts <= T - 30 * DAY)
        v30 = cnt[m30] > 0
        v60 = cnt[m60] > 0
        if m30.sum() and m60.sum() and v30.mean() >= 0.8 and v60.mean() >= 0.8:
            rec = qv[m30][v30].sum() / cnt[m30][v30].sum()
            base = qv[m60][v60].sum() / cnt[m60][v60].sum()
            if base > 0:
                f["ticket_a5p2"] = float(rec / base)
        # A8P2: weekly tickets over trailing 12 weeks (84d) within the 90d window
        wk = []
        for k in range(12, 0, -1):
            m = (ts > T - k * WEEK) & (ts <= T - (k - 1) * WEEK)
            csum = cnt[m].sum()
            if csum > 0 and m.sum() > 0:
                wk.append(qv[m].sum() / csum)
            else:
                wk = None
                break
        if wk is not None and len(wk) == 12:
            med = float(np.median(wk[:-1] + [wk[-1]]))
            if med > 0:
                f["ticket_a8p2"] = float(wk[-1] / med)
        # --- diagnostic: 28d Amihud (reserved ancestor feature, diagnostics only)
        m28b = (ts > T - 28 * DAY) & (ts <= T)
        if m28b.sum() > 0:
            # daily amihud from daily close changes and daily qv
            dq = []
            for dd in bd[1:]:
                prev = int(dd) - 1
                if prev in dc_map and np.isfinite(dc_map[prev]) and np.isfinite(dc_map[int(dd)]):
                    md_ = (ts > (prev) * DAY) & (ts <= dd * DAY)
                    qsum = qv[md_].sum()
                    if qsum > 0:
                        dq.append(abs(np.log(dc_map[int(dd)] / dc_map[prev])) / qsum)
            if len(dq) >= 20:
                f["amihud28"] = float(np.mean(dq))
        out[sym] = f
    return out


def rank_series(feat: dict, key: str, elig):
    syms = [s for s in TRADED if elig(feat, s)]
    if len(syms) < 9:
        return None
    return syms, np.array([feat[s][key] for s in syms])


def rho_pairs(fa, fb, key_a, elig_a, key_b, elig_b, min_common=10):
    """rho over the common eligible set at one stamp; None if insufficient."""
    A = rank_series(fa, key_a, elig_a)
    B = rank_series(fb, key_b, elig_b)
    if A is None or B is None:
        return None, None
    common = sorted(set(A[0]) & set(B[0]))
    if len(common) < min_common:
        return None, len(common)
    va = [A[1][A[0].index(s)] for s in common]
    vb = [B[1][B[0].index(s)] for s in common]
    return spearman(va, vb), len(common)


# eligibility masks per proposal rule
def elig_a5p1(feat, sym):
    f = feat.get(sym, {})
    return f.get("beta_npairs", 0) >= 60 and "beta90" in f

def elig_a8p1(feat, sym):
    f = feat.get(sym, {})
    return f.get("beta_npairs", 0) >= 85 and "beta90" in f  # full 90d block

def elig_std(feat, sym, key):
    return key in feat.get(sym, {})


PAIRS = [
    # (pair_id, key_a, elig_a, key_b, elig_b, label)
    ("A5P1_vs_A8P1", "beta90", elig_a5p1, "beta90", elig_a8p1, "BAB vs BAB (identical estimator)"),
    ("A5P2_vs_A8P2", "ticket_a5p2", lambda f, s: elig_std(f, s, "ticket_a5p2"),
     "ticket_a8p2", lambda f, s: elig_std(f, s, "ticket_a8p2"), "ticket-ratio vs weekly ticket-norm"),
    ("A5P2_vs_A6P1", "ticket_a5p2", lambda f, s: elig_std(f, s, "ticket_a5p2"),
     "ticket_a6p1", lambda f, s: elig_std(f, s, "ticket_a6p1"), "ticket-ratio vs 28d ticket level"),
    ("A8P2_vs_A6P1", "ticket_a8p2", lambda f, s: elig_std(f, s, "ticket_a8p2"),
     "ticket_a6p1", lambda f, s: elig_std(f, s, "ticket_a6p1"), "weekly ticket-norm vs 28d ticket level"),
    # vs rejected/reserved ancestor features (diagnostics)
    ("A5P1_vs_MOM90", "beta90", elig_a5p1, "mom90", lambda f, s: elig_std(f, s, "mom90"), "BAB vs 90d momentum (V4 diagnostic)"),
    ("A8P1_vs_MOM90", "beta90", elig_a8p1, "mom90", lambda f, s: elig_std(f, s, "mom90"), "BAB vs 90d momentum (V4 diagnostic)"),
    ("A5P2_vs_MOM28", "ticket_a5p2", lambda f, s: elig_std(f, s, "ticket_a5p2"),
     "mom28", lambda f, s: elig_std(f, s, "mom28"), "ticket-ratio vs 28d momentum"),
    ("A8P2_vs_MOM28", "ticket_a8p2", lambda f, s: elig_std(f, s, "ticket_a8p2"),
     "mom28", lambda f, s: elig_std(f, s, "mom28"), "ticket-norm vs 28d momentum"),
    ("A6P1_vs_MOM28", "ticket_a6p1", lambda f, s: elig_std(f, s, "ticket_a6p1"),
     "mom28", lambda f, s: elig_std(f, s, "mom28"), "ticket level vs 28d momentum"),
    ("A6P1_vs_AMIHUD28", "ticket_a6p1", lambda f, s: elig_std(f, s, "ticket_a6p1"),
     "amihud28", lambda f, s: elig_std(f, s, "amihud28"), "ticket level vs reserved ILLIQ feature"),
    ("A8P2_vs_AMIHUD28", "ticket_a8p2", lambda f, s: elig_std(f, s, "ticket_a8p2"),
     "amihud28", lambda f, s: elig_std(f, s, "amihud28"), "ticket-norm vs reserved ILLIQ feature"),
    ("A5P2_vs_AMIHUD28", "ticket_a5p2", lambda f, s: elig_std(f, s, "ticket_a5p2"),
     "amihud28", lambda f, s: elig_std(f, s, "amihud28"), "ticket-ratio vs reserved ILLIQ feature"),
]


def run(stamps, label):
    results = {p[0]: {"rhos": [], "n_common": []} for p in PAIRS}
    per_stamp = {}
    for T in stamps:
        feat = features_at(T)
        stamp_rec = {}
        for pid, ka, ea, kb, eb, lab in PAIRS:
            r, n = rho_pairs(feat, feat, ka, ea, kb, eb)
            if r is not None and np.isfinite(r):
                results[pid]["rhos"].append(r)
                results[pid]["n_common"].append(n)
                stamp_rec[pid] = {"rho": round(r, 4), "n_common": n}
        per_stamp[datetime.fromtimestamp(T / 1e9, tz=timezone.utc).strftime("%Y-%m-%d")] = stamp_rec
    summary = {}
    for pid, *_ in PAIRS:
        rhos = np.array(results[pid]["rhos"])
        if len(rhos) == 0:
            summary[pid] = {"n_stamps": 0}
            continue
        ar = np.abs(rhos)
        summary[pid] = {
            "n_stamps": int(len(rhos)),
            "mean_abs_rho": round(float(ar.mean()), 4),
            "median_abs_rho": round(float(np.median(ar)), 4),
            "min_abs_rho": round(float(ar.min()), 4),
            "max_abs_rho": round(float(ar.max()), 4),
            "share_abs_rho_ge_0.70": round(float((ar >= 0.70).mean()), 4),
            "share_abs_rho_ge_0.50": round(float((ar >= 0.50).mean()), 4),
            "mean_signed_rho": round(float(rhos.mean()), 4),
            "median_n_common": float(np.median(results[pid]["n_common"])),
        }
    return {"scope": label, "n_stamps_total": len(stamps), "summary": summary,
            "per_stamp": per_stamp}


out = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "window": run(stamps_window, "S0 scored window 2025-08-22..2026-08-21, Monday PIT stamps"),
       "prewindow": run(stamps_pre, "prewindow Mondays 2025-01-06..2025-08-18 (strictly before window start)")}

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "a7n_rank_similarity_raw.json"), "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print(json.dumps({k: v["summary"] for k, v in out.items()}, indent=1)[:200])
print("WROTE", os.path.join(here, "a7n_rank_similarity_raw.json"))
