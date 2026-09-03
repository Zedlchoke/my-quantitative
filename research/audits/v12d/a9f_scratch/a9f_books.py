"""A9-F scratch: feature values, book breadth and schedule-only cost bounds.

NO returns / PnL / Sharpe / performance ranking is computed anywhere. What
this script does:

* builds PIT features at the declared decision stamps from completed 15m bars
  (daily closes for the 90d BTC beta; per-bar quote_volume / trade-count
  aggregates for the order-size / ticket-mix statistics);
* constructs each proposal's DECLARED target-book shape at each stamp
  (extreme-quintile 4-vs-4 weekly books; 4-vs-4 monthly ticket book;
  threshold pairs book) including the declared cap clamp;
* measures breadth (eligible names, leg sizes, max |weight| after clamp);
* emits the one-way turnover schedule implied by the declared rules
  (hysteresis variant + a no-hysteresis CONSERVATIVE variant) and prices the
  transitions with the frozen adapter cost arithmetic
  (5bp taker + 1 adverse tick baseline; fee x1.5 + 3 ticks stressed).
  This is cost of CHANGING books only -- never a return.
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d2-a9f-feasibility")

from research.v12.data_contract import (  # noqa: E402
    BAR_INTERVAL_NS,
    REQUIRED_SYMBOLS,
    S0_SNAPSHOT_WINDOW_END_ISO,
    S0_SNAPSHOT_WINDOW_START_ISO,
    bar_parquet_paths,
    ceil_to_monday_00z_ns,
    ns_to_iso_utc,
    parse_iso_utc_ns,
    read_instrument_metadata,
    snap_bar_closes_to_slots,
    BARS_ROOT,
    PERP_ROOT,
)

OUT = "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d2-a9f-feasibility/research/audits/v12d/a9f_scratch/a9f_books.json"

NS_DAY = 86_400 * 10**9
W0 = parse_iso_utc_ns(S0_SNAPSHOT_WINDOW_START_ISO)
W1 = parse_iso_utc_ns(S0_SNAPSHOT_WINDOW_END_ISO)
FIRST_STAMP = ceil_to_monday_00z_ns(W0 + 1)
WEEK = 7 * NS_DAY
STAMPS_WEEKLY = list(range(FIRST_STAMP, W1, WEEK))
STAMPS_MONTHLY = STAMPS_WEEKLY[::4]
TRADEABLE = [s for s in REQUIRED_SYMBOLS if s != "BTCUSDT"]

FEE = 0.0005  # 5bp taker, tier-0 floor, from instrument metadata
TICK_FLOOR = 1
STRESS_FEE_MULT = 1.5
STRESS_EXTRA_TICKS = 2
EG_CRIT_10 = -3.05  # MacKinnon EG residual ADF ~10% (2 vars, const)

LOAD_START = parse_iso_utc_ns("2025-04-01T00:00:00Z")
LOAD_END = parse_iso_utc_ns("2026-08-22T00:00:00Z")


#: Verified empirically: the stored close raw i128 equals price * 1e16 for
#: every symbol/file (cross-checked per file against the bar's own
#: taker_buy_quote_volume / taker_buy_base_volume ratio, median rel err ~1e-3).
CLOSE_SCALE = 1e16


def decode_close(raw: bytes) -> float:
    return int.from_bytes(raw, "little") / CLOSE_SCALE


def load_symbol(sym: str) -> dict:
    frames = []
    for p in bar_parquet_paths(BARS_ROOT, sym):
        t = pq.read_table(p, columns=["ts_event", "close", "quote_volume", "count",
                                      "taker_buy_base_volume", "taker_buy_quote_volume"])
        close_raw = t.column("close").to_pylist()
        qb = np.array(t.column("taker_buy_base_volume").to_pylist(), dtype=float)
        qq = np.array([float(x) for x in t.column("taker_buy_quote_volume").to_pylist()])
        # per-file decode cross-check (sampled): decoded close vs taker-flow avg price
        raw_int = np.array([int.from_bytes(b, "little") for b in close_raw[::97]], dtype=np.float64)
        mask = slice(0, min(len(raw_int), len(qb[::97])))
        qb_s, qq_s = qb[::97], qq[::97]
        ok = (qb_s > 0) & (qq_s > 0)
        if ok.sum() >= 5:
            avg_px = qq_s[ok] / qb_s[ok]
            rel = float(np.median(np.abs(raw_int[ok] / CLOSE_SCALE - avg_px) / avg_px))
            if rel > 0.05:
                raise ValueError(f"{sym}: close decode cross-check failed (rel err {rel})")
        frames.append(
            pd.DataFrame(
                {
                    "ts": t.column("ts_event").to_numpy().astype(np.int64),
                    "close": [decode_close(b) for b in close_raw],
                    "qv": [float(x) for x in t.column("quote_volume").to_pylist()],
                    "count": t.column("count").to_numpy().astype(np.int64),
                }
            )
        )
    df = pd.concat(frames, ignore_index=True).sort_values("ts").drop_duplicates("ts")
    df = df[(df["ts"] >= LOAD_START) & (df["ts"] <= LOAD_END)].reset_index(drop=True)
    daily = (
        pd.DataFrame({"day": df["ts"].to_numpy() // NS_DAY, "close": df["close"].to_numpy()})
        .groupby("day")["close"]
        .last()
    )
    return {
        "ts": df["ts"].to_numpy(),
        "close": df["close"].to_numpy(),
        "qv": df["qv"].to_numpy(),
        "cnt": df["count"].to_numpy(),
        "daily": daily,
    }


def win_stats(d: dict, lo: int, hi: int) -> dict:
    i0 = int(np.searchsorted(d["ts"], lo, side="right"))
    i1 = int(np.searchsorted(d["ts"], hi, side="right"))
    n = i1 - i0
    expected = (hi - lo + BAR_INTERVAL_NS - 1) // BAR_INTERVAL_NS
    qv = float(d["qv"][i0:i1].sum()) if n else 0.0
    cnt = int(d["cnt"][i0:i1].sum()) if n else 0
    nz = int((d["cnt"][i0:i1] > 0).sum()) if n else 0
    return {
        "bars": n,
        "missing": max(0, expected - n),
        "qv": qv,
        "cnt": cnt,
        "nz_share": (nz / n) if n else 0.0,
    }


def daily_returns(d: dict, lo: int, hi: int):
    d0, d1 = lo // NS_DAY, hi // NS_DAY
    s = d["daily"]
    s = s[(s.index > d0) & (s.index <= d1)]
    return np.log(s).diff().dropna()


def beta_90(d: dict, btc: dict, t: int):
    j = pd.concat({"s": daily_returns(d, t - 90 * NS_DAY, t), "b": daily_returns(btc, t - 90 * NS_DAY, t)}, axis=1).dropna()
    n = len(j)
    if n < 60:
        return None, n
    s = j["s"].to_numpy()
    b = j["b"].to_numpy()
    var_b = float(np.var(b, ddof=1))
    if var_b <= 0:
        return None, n
    return float(np.cov(s, b, ddof=1)[0, 1]) / var_b, n


def fill_price(d: dict, t: int):
    i = int(np.searchsorted(d["ts"], t, side="right"))
    return float(d["close"][i]) if i < len(d["ts"]) else None


TICK_RATIO: dict[str, float] = {}


def build_features() -> dict[int, dict[str, dict]]:
    data: dict[str, dict] = {}
    for sym in REQUIRED_SYMBOLS:
        data[sym] = load_symbol(sym)
    btc = data["BTCUSDT"]
    feat: dict[int, dict[str, dict]] = {}
    for t in STAMPS_WEEKLY:
        row: dict[str, dict] = {}
        for sym in TRADEABLE:
            d = data[sym]
            beta, paired = beta_90(d, btc, t)
            w90 = win_stats(d, t - 90 * NS_DAY, t)
            w56 = win_stats(d, t - 56 * NS_DAY, t)
            w28 = win_stats(d, t - 28 * NS_DAY, t)
            w30 = win_stats(d, t - 30 * NS_DAY, t)
            w60 = win_stats(d, t - 90 * NS_DAY, t - 30 * NS_DAY)
            weeks = []
            for k in range(12):
                ws = win_stats(d, t - (k + 1) * WEEK, t - k * WEEK)
                weeks.append((ws["qv"] / ws["cnt"]) if ws["cnt"] > 0 else None)
            valid = [x for x in weeks if x is not None]
            recent = (w30["qv"] / w30["cnt"]) if w30["cnt"] > 0 else None
            base = (w60["qv"] / w60["cnt"]) if w60["cnt"] > 0 else None
            row[sym] = {
                "beta": beta,
                "paired": paired,
                "cov90_missing": w90["missing"],
                "cov56_missing": w56["missing"],
                "cov28_missing": w28["missing"],
                "osr_ratio": (recent / base) if (recent and base) else None,
                "nz30": w30["nz_share"],
                "nz60": w60["nz_share"],
                "ticket28": (w28["qv"] / w28["cnt"]) if w28["cnt"] > 0 else None,
                "ticket_norm": (weeks[0] / float(np.median(valid))) if len(valid) >= 12 and weeks[0] else None,
                "weekly_valid": len(valid),
            }
        feat[t] = row
    return feat, data


def make_book(feat_t: dict, key: str, ascending_long: bool, eligible, prev_legs, hysteresis: bool, base_w: float = 0.125):
    vals = {s: feat_t[s][key] for s in eligible if feat_t[s][key] is not None}
    names = sorted(vals, key=lambda s: (vals[s], s))
    if len(names) < 9:
        return None
    n = len(names)
    if hysteresis and prev_legs is not None:
        pl, ps = prev_legs
        band = max(1, int(round(n * 0.4)))
        rank = {s: i for i, s in enumerate(names)}
        longs = [s for s in pl if s in rank and rank[s] < band][:4]
        shorts = [s for s in ps if s in rank and rank[s] >= n - band][:4]
        rest = [s for s in names if s not in longs and s not in shorts]
        if ascending_long:
            longs += rest[: max(0, 4 - len(longs))]
            shorts += rest[::-1][: max(0, 4 - len(shorts))]
        else:
            longs += rest[::-1][: max(0, 4 - len(longs))]
            shorts += rest[: max(0, 4 - len(shorts))]
    else:
        if ascending_long:
            longs, shorts = names[:4], names[-4:][::-1]
        else:
            longs, shorts = names[-4:][::-1], names[:4]
    bl = [feat_t[s]["beta"] for s in longs if feat_t[s].get("beta") is not None]
    bs = [feat_t[s]["beta"] for s in shorts if feat_t[s].get("beta") is not None]
    w = {s: base_w for s in longs}
    for s in shorts:
        w[s] = -base_w
    if bl and bs and float(np.mean(bl)) > 0:
        m = float(np.mean(bs)) / float(np.mean(bl))
        for s in longs:
            w[s] *= m
    mx = max(abs(v) for v in w.values()) if w else 0.0
    if mx > 0.30:
        c = 0.30 / mx
        w = {s: v * c for s, v in w.items()}
    return {"longs": longs, "shorts": shorts, "weights": w}


def delta_map(pw, w):
    return {s: abs(float(w.get(s, 0.0)) - float(pw.get(s, 0.0))) for s in set(pw) | set(w) if abs(float(w.get(s, 0.0)) - float(pw.get(s, 0.0))) > 1e-12}


def drag_bounds(deltas_by_stamp, gross_mean, window_days):
    base = stressed = 0.0
    per_sym: dict = {}
    total = 0.0
    for t_iso, delta in deltas_by_stamp:
        for s, d in delta.items():
            tr = TICK_RATIO.get(s, 0.0)
            base += d * (FEE + TICK_FLOOR * tr)
            stressed += d * (FEE * STRESS_FEE_MULT + (TICK_FLOOR + STRESS_EXTRA_TICKS) * tr)
            per_sym[s] = per_sym.get(s, 0.0) + d
            total += d
    ann = 365.0 / window_days
    share = (max(per_sym.values()) / total) if total > 0 and per_sym else None
    return {
        "turnover_units": round(total, 3),
        "turnover_per_365d": round(total * ann, 2),
        "base_drag_frac_gross": round(base * ann / gross_mean, 5) if gross_mean > 0 and total > 0 else None,
        "stressed_drag_frac_gross": round(stressed * ann / gross_mean, 5) if gross_mean > 0 and total > 0 else None,
        "max_symbol_turnover_share": round(share, 4) if share is not None else None,
        "top_symbol_shares": {k: round(v / total, 4) for k, v in sorted(per_sym.items(), key=lambda kv: -kv[1])[:5]} if total > 0 else {},
    }


def holding_spans(book_rows):
    """Completed + censored intended holding spans from book occupancy.

    book_rows: list of weights dicts in stamp order (served stamps only).
    Mirrors the cost_feasibility gate's span extraction (counts/durations
    only -- no returns).
    """
    open_spans: dict = {}
    completed = []
    for w in book_rows:
        held = {s for s, v in w.items() if abs(float(v)) > 1e-12}
        idx = len(completed)
        for s in held - set(open_spans):
            open_spans[s] = w["_t"]
        for s in set(open_spans) - held:
            completed.append((s, open_spans.pop(s), w["_t"]))
    censored = dict(open_spans)
    durs = [((e - s) / NS_DAY) for _, s, e in completed]
    return completed, censored, (float(np.median(durs)) if durs else None)


def simulate(feat, stamps, elig_fn, key, ascending_long, hysteresis, base_w=0.125):
    prev_legs = None
    prev_w: dict = {}
    prev_wn: dict = {}
    rows = []
    dh, dn = [], []
    for t in stamps:
        elig = elig_fn(feat[t])
        if len(elig) < 9:
            rows.append({"t": ns_to_iso_utc(t), "eligible": len(elig), "carried": True})
            continue
        b = make_book(feat[t], key, ascending_long, elig, prev_legs, hysteresis, base_w)
        bn = make_book(feat[t], key, ascending_long, elig, None, False, base_w)
        prev_legs = (b["longs"], b["shorts"])
        delta_h = delta_map(prev_w, b["weights"])
        delta_n = delta_map(prev_wn, bn["weights"])
        dh.append((ns_to_iso_utc(t), delta_h))
        dn.append((ns_to_iso_utc(t), delta_n))
        rows.append(
            {
                "t": ns_to_iso_utc(t),
                "eligible": len(elig),
                "n_long": len(b["longs"]),
                "n_short": len(b["shorts"]),
                "max_abs_w": round(max(abs(v) for v in b["weights"].values()), 6),
                "gross": round(sum(abs(v) for v in b["weights"].values()), 4),
                "turnover_h": round(sum(delta_h.values()), 4),
                "turnover_n": round(sum(delta_n.values()), 4),
            }
        )
        prev_w = b["weights"]
        prev_wn = bn["weights"]
    served = [r for r in rows if not r.get("carried")]
    wd = (parse_iso_utc_ns(served[-1]["t"]) - parse_iso_utc_ns(served[0]["t"])) / NS_DAY if len(served) > 1 else 1.0
    gross_mean = float(np.mean([r["gross"] for r in served]))
    # holding spans from served-stamp book occupancy (rebuild weights quickly)
    prev_legs2 = None
    prev_w2: dict = {}
    book_rows = []
    for t in stamps:
        elig = elig_fn(feat[t])
        if len(elig) < 9:
            continue
        b2 = make_book(feat[t], key, ascending_long, elig, prev_legs2, hysteresis, base_w)
        prev_legs2 = (b2["longs"], b2["shorts"])
        row = dict(b2["weights"])
        row["_t"] = t
        book_rows.append(row)
    completed, censored, med_hold = holding_spans(book_rows)
    summary = {
        "served_stamps": len(served),
        "carried_stamps": len(rows) - len(served),
        "window_days": round(wd, 1),
        "decisions_per_365d": round(len(served) * 365.0 / wd, 2),
        "eligible_min": min(r["eligible"] for r in served),
        "eligible_max": max(r["eligible"] for r in served),
        "min_leg_size": min(min(r["n_long"], r["n_short"]) for r in served),
        "max_abs_weight": round(max(r["max_abs_w"] for r in served), 6),
        "gross_mean": round(gross_mean, 4),
        "completed_holding_spans": len(completed),
        "censored_spans": len(censored),
        "median_intended_holding_days": round(med_hold, 2) if med_hold is not None else None,
    }
    return {
        "rows": rows,
        "summary": summary,
        "drag_hysteresis": drag_bounds(dh, gross_mean, wd),
        "drag_nohysteresis_conservative": drag_bounds(dn, gross_mean, wd),
    }


def main() -> None:
    feat, data = build_features()

    inst = {s: read_instrument_metadata(PERP_ROOT, s) for s in REQUIRED_SYMBOLS}
    for sym in TRADEABLE:
        rs = []
        for t in (STAMPS_WEEKLY[0], STAMPS_WEEKLY[-1]):
            px = fill_price(data[sym], t)
            if px:
                rs.append(inst[sym]["price_increment_tick_size"] / px)
        TICK_RATIO[sym] = max(rs)

    result = {
        "schema": "a9f_books_v1",
        "close_decode_scale": CLOSE_SCALE,
        "tick_price_ratio": {s: TICK_RATIO[s] for s in TRADEABLE},
        "stamps_weekly": [ns_to_iso_utc(t) for t in STAMPS_WEEKLY],
        "stamps_monthly": [ns_to_iso_utc(t) for t in STAMPS_MONTHLY],
    }

    def elig_beta(f):
        return [s for s in TRADEABLE if f[s]["cov90_missing"] == 0 and f[s]["beta"] is not None and f[s]["paired"] >= 60]

    def elig_a5p2(f):
        return [s for s in TRADEABLE if f[s]["cov90_missing"] == 0 and f[s]["osr_ratio"] is not None and f[s]["nz30"] >= 0.8 and f[s]["nz60"] >= 0.8]

    def elig_a8p2(f):
        return [s for s in TRADEABLE if f[s]["cov90_missing"] == 0 and f[s]["weekly_valid"] >= 12 and f[s]["ticket_norm"] is not None]

    def elig_oscomp(f):
        return [s for s in TRADEABLE if f[s]["cov28_missing"] == 0 and f[s]["ticket28"] is not None]

    props = {}
    # BAB proposals: long LOWEST beta quintile -> ascending_long=True.
    props["V12-A5-P1-BAB-LOWBETA"] = simulate(feat, STAMPS_WEEKLY, elig_beta, "beta", True, True, 0.125)
    props["A8-P1-BAB-PERP"] = simulate(feat, STAMPS_WEEKLY, elig_beta, "beta", True, True, 0.125)
    # Ticket/order-size proposals: long TOP quintile (rising/thick ticket) -> ascending_long=False.
    props["V12-A5-P2-MIX-ORDERSIZE"] = simulate(feat, STAMPS_WEEKLY, elig_a5p2, "osr_ratio", False, True, 0.125)
    props["A8-P2-TICKET-MIX-CONTRARIAN"] = simulate(feat, STAMPS_WEEKLY, elig_a8p2, "ticket_norm", False, True, 0.125)
    # OSCOMP: long high average 28d ticket; monthly; side gross 1.0 -> base_w 0.25.
    props["H-A6-OSCOMP"] = simulate(feat, STAMPS_MONTHLY, elig_oscomp, "ticket28", False, False, 0.25)
    result["proposals"] = props

    # feature sanity rows at representative stamps
    reps = [STAMPS_WEEKLY[0], STAMPS_WEEKLY[13], STAMPS_WEEKLY[26], STAMPS_WEEKLY[-1]]
    sanity = {}
    for t in reps:
        f = feat[t]
        sanity[ns_to_iso_utc(t)] = {
            s: {
                "beta": None if f[s]["beta"] is None else round(f[s]["beta"], 4),
                "cov90_miss": f[s]["cov90_missing"],
                "osr": None if f[s]["osr_ratio"] is None else round(f[s]["osr_ratio"], 4),
                "nz30": round(f[s]["nz30"], 4),
                "ticket28": None if f[s]["ticket28"] is None else round(f[s]["ticket28"], 2),
                "tnorm": None if f[s]["ticket_norm"] is None else round(f[s]["ticket_norm"], 4),
            }
            for s in TRADEABLE
        }
    result["feature_sanity"] = sanity

    # ------------------------------------------------------------------ #
    # RVX: EG activation at weekly stamps + threshold schedule simulation
    # ------------------------------------------------------------------ #
    PAIRS = [
        ("ETHUSDT", "SOLUSDT"),
        ("SOLUSDT", "SUIUSDT"),
        ("AVAXUSDT", "NEARUSDT"),
        ("ADAUSDT", "AVAXUSDT"),
        ("AAVEUSDT", "LINKUSDT"),
        ("DOGEUSDT", "1000PEPEUSDT"),
        ("1000PEPEUSDT", "BOMEUSDT"),
        ("XRPUSDT", "BCHUSDT"),
    ]

    def eg_test(t, a, b):
        da, db = data[a], data[b]
        d0, d1 = (t - 56 * NS_DAY) // NS_DAY, t // NS_DAY
        la, lb = np.log(da["daily"]), np.log(db["daily"])
        xa, xb = la[(la.index > d0) & (la.index <= d1)], lb[(lb.index > d0) & (lb.index <= d1)]
        j = pd.concat({"a": xa, "b": xb}, axis=1).dropna()
        if len(j) < 50:
            return None
        y, x = j["a"].to_numpy(), j["b"].to_numpy()
        X = np.column_stack([np.ones_like(x), x])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        e = y - X @ coef
        gamma = float(coef[1])
        de = np.diff(e)
        if len(de) < 10 or float(np.std(e[:-1])) == 0:
            return {"gamma": gamma, "adf_t": None, "z": None, "hl": None, "n": len(j)}
        e_lag = e[:-1][1:]
        lag_de = np.roll(de, 1)[1:]
        Z = np.column_stack([e_lag, np.ones_like(e_lag), lag_de])
        yv = de[1:]
        cf, *_ = np.linalg.lstsq(Z, yv, rcond=None)
        resid = yv - Z @ cf
        dof = max(1, len(yv) - Z.shape[1])
        s2 = float(resid @ resid) / dof
        covm = s2 * np.linalg.inv(Z.T @ Z)
        se = math.sqrt(float(covm[0, 0]))
        tstat = float(cf[0] / se) if se > 0 else None
        ph = np.column_stack([np.ones_like(e[:-1]), e[:-1]])
        c2, *_ = np.linalg.lstsq(ph, e[1:], rcond=None)
        phi = float(c2[1])
        hl = (-math.log(2) / math.log(phi)) if 0 < phi < 1 else None
        z = float((e[-1] - e.mean()) / e.std()) if float(e.std()) > 0 else None
        return {"gamma": gamma, "adf_t": tstat, "z": z, "hl": hl, "n": len(j)}

    rvx_rows = []
    for t in STAMPS_WEEKLY:
        acts = []
        for a, b in PAIRS:
            covok = feat[t][a]["cov56_missing"] == 0 and feat[t][b]["cov56_missing"] == 0
            r = eg_test(t, a, b) if covok else None
            ok = bool(r and r["adf_t"] is not None and r["adf_t"] <= EG_CRIT_10 and 0.25 <= abs(r["gamma"]) <= 4.0)
            acts.append({"pair": f"{a.replace('USDT','')}/{b.replace('USDT','')}", "ok": ok, "computable": bool(covok and r),
                         "z": None if not r or r["z"] is None else round(r["z"], 3),
                         "adf": None if not r or r["adf_t"] is None else round(r["adf_t"], 3),
                         "gamma": None if not r or r["gamma"] is None else round(r["gamma"], 3),
                         "hl_d": None if not r or r["hl"] is None else round(r["hl"], 1)})
        rvx_rows.append({"t": ns_to_iso_utc(t), "pairs": acts, "activatable": sum(1 for x in acts if x["ok"]),
                         "computable": sum(1 for x in acts if x["computable"])})

    # threshold schedule simulation (replay with span + per-symbol deltas)
    def replay():
        state: dict = {}
        book_prev: dict = {}
        sched_rows = []
        per_sym_local: dict = {}
        open_spans: dict = {}
        completed_spans = []
        for i, row in enumerate(rvx_rows):
            t_ns = parse_iso_utc_ns(row["t"])
            for pi, (a, b) in enumerate(PAIRS):
                key = f"{a}+{b}"
                info = row["pairs"][pi]
                st = state.get(key)
                if st is None:
                    if info["ok"] and info["z"] is not None and abs(info["z"]) >= 2.0:
                        used = {s for k2 in state for s in k2.split("+")}
                        if len(state) < 3 and a not in used and b not in used:
                            state[key] = {"dir": (-1 if info["z"] < 0 else 1), "entry_i": i, "last_change": i, "t_open": t_ns}
                else:
                    exit_now = (info["z"] is not None and abs(info["z"]) <= 0.5) or (i - st["entry_i"] >= 8)
                    if exit_now and i - st["last_change"] >= 2:
                        for s in key.split("+"):
                            completed_spans.append((s, st["t_open"], t_ns))
                        del state[key]
            w = {}
            legw = 0.20 if len(state) == 1 else (0.25 if len(state) >= 2 else 0.0)
            for k2, st in state.items():
                a, b = k2.split("+")
                w[a] = round(w.get(a, 0.0) + legw * st["dir"], 6)
                w[b] = round(w.get(b, 0.0) - legw * st["dir"], 6)
            for s in set(w) | set(book_prev):
                d = abs(w.get(s, 0.0) - book_prev.get(s, 0.0))
                if d > 1e-12:
                    per_sym_local[s] = per_sym_local.get(s, 0.0) + d
            sched_rows.append({"t": row["t"], "npairs": len(state), "gross": round(sum(abs(v) for v in w.values()), 4),
                               "delta_total": round(sum(abs(w.get(s, 0.0) - book_prev.get(s, 0.0)) for s in set(w) | set(book_prev)), 4),
                               "max_w": round(max((abs(v) for v in w.values()), default=0.0), 4)})
            book_prev = w
        return sched_rows, per_sym_local, completed_spans

    sched, per_sym, rvx_spans = replay()
    to_total = sum(per_sym.values())
    wd_rvx = (parse_iso_utc_ns(sched[-1]["t"]) - parse_iso_utc_ns(sched[0]["t"])) / NS_DAY
    gross_rvx = float(np.mean([e["gross"] for e in sched]))
    base_cost = stressed_cost = 0.0
    for s, d in per_sym.items():
        tr = TICK_RATIO.get(s, 0.0)
        base_cost += d * (FEE + TICK_FLOOR * tr)
        stressed_cost += d * (FEE * STRESS_FEE_MULT + (TICK_FLOOR + STRESS_EXTRA_TICKS) * tr)
    ann_rvx = 365.0 / wd_rvx
    durs_rvx = [((e - s) / NS_DAY) for _, s, e in rvx_spans]
    props["H-A6-RVX"] = {
        "stamps": rvx_rows,
        "schedule": sched,
        "summary": {
            "computable_min": min(r["computable"] for r in rvx_rows),
            "computable_stamps_with_at_least_1_pair": sum(1 for r in rvx_rows if r["computable"] >= 1),
            "activatable_min": min(r["activatable"] for r in rvx_rows),
            "activatable_max": max(r["activatable"] for r in rvx_rows),
            "activatable_at_first_stamp": rvx_rows[0]["activatable"],
            "distinct_pairs_ever_activatable": len({x["pair"] for r in rvx_rows for x in r["pairs"] if x["ok"]}),
            "stamps_with_at_least_1_activatable": sum(1 for r in rvx_rows if r["activatable"] >= 1),
            "stamps_with_at_least_2_activatable": sum(1 for r in rvx_rows if r["activatable"] >= 2),
            "concurrent_pairs_max": max(e["npairs"] for e in sched),
            "max_abs_weight": max(e["max_w"] for e in sched),
            "gross_mean": round(gross_rvx, 4),
            "completed_holding_spans": len(rvx_spans),
            "median_intended_holding_days": round(float(np.median(durs_rvx)), 2) if durs_rvx else None,
            "one_way_turnover_units": round(to_total, 3),
            "turnover_per_365d": round(to_total * ann_rvx, 2),
            "base_drag_frac_gross": round(base_cost * ann_rvx / gross_rvx, 5) if to_total > 0 else None,
            "stressed_drag_frac_gross": round(stressed_cost * ann_rvx / gross_rvx, 5) if to_total > 0 else None,
            "max_symbol_turnover_share": round(max(per_sym.values()) / to_total, 4) if to_total > 0 else None,
        },
        "per_symbol_turnover": {k: round(v, 3) for k, v in sorted(per_sym.items(), key=lambda kv: -kv[1])},
    }

    with open(OUT, "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True, default=str)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
