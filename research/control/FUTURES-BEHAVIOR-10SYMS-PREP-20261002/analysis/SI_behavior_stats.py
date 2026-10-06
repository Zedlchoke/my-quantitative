#!/usr/bin/env python
"""SI (COMEX silver 5000oz, tradingClass SI) descriptive statistics.

Task: FUTURES-BEHAVIOR-10SYMS-PREP-20261002, lane SYMBOL-DOSSIER-SI.
PREP ONLY: descriptive statistics computed from legal raw per-contract daily
data. No PnL, no event studies, no parameter selection, no performance
metrics. Thresholds/normalizations use strict past / trailing windows and are
descriptive labels only, never entry features.

Input (read-only): ~/.my-quantitative-data/futures-10syms-v1/raw/SI_*.json
(GC_* additionally for the GC/SI ratio cross-asset descriptive).
Output: analysis/SI_behavior_stats.json (same directory as this script).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python analysis/SI_behavior_stats.py

Chain construction (declared data-lane roll rule, applied to the MEASURED
liquid cycle H/K/N/U/Z):
  - hold contract until the last session before day-1 of its delivery month,
    roll to the next liquid-cycle contract at that close;
  - raw files of expired contracts end exactly at that roll date (verified
    per contract below), active contracts end at the 2026-10-01/02 fetch;
  - serial months (F,G,J,M,Q,V,X outside the cycle) are listed but measured
    dead (max ~1k lots/day vs 26k-178k on cycle months) -> excluded from the
    chain; S1's "front" (nearest expiry, e.g. SIV6 Oct serial) is NOT the
    liquidity front.
  - chain start 2025-07-01: the previous liquid fronts (SIN5 and earlier /
    GCQ5 and earlier) are NOT in the raw set (expired-secdef wall ~1 year),
    so the chain is only honest from the roll off SIN5 (2025-06-30). The
    pre-2025-07 deep history exists only as deferred-contract settlement
    marks (e.g. SIZ5 file from 2020-12-31), unusable as a front chain.
"""
import json
import os
import statistics as st
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "SI_behavior_stats.json")

FETCH_DATE = date(2026, 10, 2)     # bulk fetch session (FUTURES-DATA-10SYMS-V1)
CHAIN_START = "2025-07-01"         # see docstring basis
MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
SI_CYCLE = ("H", "K", "N", "U", "Z")       # measured liquid cycle (SI)
GC_CYCLE = ("G", "J", "M", "Q", "V", "Z")  # measured liquid cycle (GC)
SI_MULT = 5000       # oz/contract, S1_IDENTITY machine-verified
SI_MINTICK = 0.005   # $/oz (= $25/contract)
FRONT_SCALE = 10_000  # declared descriptive threshold for a "front-scale" day
SCALE_ROBUST = [5_000, 20_000]


def load_bars(sym, local, conid, kind="TRADES", bar="1day", dur="6Y"):
    p = os.path.join(RAW, f"{sym}_{local}_{conid}_{kind}_{bar}_{dur}.json")
    if not os.path.exists(p):
        return None, None
    with open(p) as fh:
        d = json.load(fh)
    return d, d["bars"]


def q(sv, frac):
    if not sv:
        return None
    return sv[min(len(sv) - 1, max(0, int(round(frac * (len(sv) - 1)))))]


def stats(xs):
    if not xs:
        return {"n": 0}
    sv = sorted(xs)
    m = st.fmean(xs)
    sd = st.pstdev(xs) if len(xs) > 1 else 0.0
    skew = sum(((x - m) / sd) ** 3 for x in xs) / len(xs) if sd > 0 else 0.0
    kurt = sum(((x - m) / sd) ** 4 for x in xs) / len(xs) - 3.0 if sd > 0 else 0.0
    return {"n": len(xs), "mean": round(m, 6), "std": round(sd, 6),
            "min": round(sv[0], 6), "q05": round(q(sv, 0.05), 6),
            "median": round(q(sv, 0.5), 6), "q95": round(q(sv, 0.95), 6),
            "max": round(sv[-1], 6), "skew": round(skew, 4),
            "ex_kurt": round(kurt, 4)}


def last_session_before(y, m):
    d = date(y, m, 1) - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def dm_from_meta(meta, local):
    """Delivery month from machine-verified lastTradeDate metadata (yyyymmdd).
    For SI and GC the last-trade month == delivery month (S9 identity check);
    cross-checked against the localSymbol month code."""
    ltd = meta.get("expiry_month") or ""
    y, m = int(ltd[:4]), int(ltd[4:6])
    assert MONTH_CODE[local[-2]] == m, f"month code mismatch {local} {ltd}"
    return f"{y}{m:02d}"


def scan(sym, cycle):
    """Liquid-cycle contracts: local, conId, delivery_month, bars."""
    out = []
    for fn in os.listdir(RAW):
        if not fn.startswith(sym + "_"):
            continue
        parts = fn[len(sym) + 1:].rsplit(".", 1)[0].split("_")
        if len(parts) < 5 or parts[2] != "TRADES" or parts[3] != "1day" or parts[4] != "6Y":
            continue
        local, conid = parts[0], int(parts[1])
        mc = local[-2]
        if mc not in cycle:
            continue
        d, bars = load_bars(sym, local, conid)
        out.append({"local": local, "conId": conid, "mc": mc,
                    "dm": dm_from_meta(d, local),
                    "meta": d, "bars": bars})
    out.sort(key=lambda r: r["dm"])
    return out


def scan_all(sym):
    """All contracts incl. serial (for the panel)."""
    seen = {}
    for fn in os.listdir(RAW):
        if not fn.startswith(sym + "_"):
            continue
        parts = fn[len(sym) + 1:].rsplit(".", 1)[0].split("_")
        if len(parts) < 5 or parts[2] != "TRADES" or parts[3] != "1day" or parts[4] != "6Y":
            continue
        local, conid = parts[0], int(parts[1])
        if (local, conid) in seen:
            continue
        d, bars = load_bars(sym, local, conid)
        seen[(local, conid)] = (d, bars)
    return seen


def roll_date_of(c):
    """Declared roll date: last session before day-1 of delivery month.
    For expired contracts this equals the raw file's last bar date
    (verified in verify_rolls); for active contracts it is in the future."""
    y, m = int(c["dm"][:4]), int(c["dm"][4:])
    return last_session_before(y, m)


def build_chain(sym, cycle):
    contracts = scan(sym, cycle)
    for c in contracts:
        c["file_last"] = c["bars"][-1]["t"] if c["bars"] else None
        c["roll_date"] = roll_date_of(c).isoformat()
        c["expired"] = c["file_last"] is not None and c["file_last"] < c["roll_date"] \
            if c["bars"] else True
        # active contracts' files are cut at the fetch date, not the roll
    by_date = defaultdict(list)
    for c in contracts:
        for b in c["bars"]:
            if b["t"] >= CHAIN_START:
                by_date[b["t"]].append((c, b))
    chain = {}
    for t, cands in by_date.items():
        # owner = first cycle contract (in delivery order) whose roll >= t
        for c in contracts:
            if c["roll_date"] >= t and any(cc["local"] == c["local"] for cc, _ in cands):
                b = next(b for cc, b in cands if cc["local"] == c["local"])
                chain[t] = {"contract": c["local"], "delivery_month": c["dm"],
                            "o": b["o"], "h": b["h"], "l": b["l"],
                            "c": b["c"], "v": b["v"]}
                break
    return contracts, chain


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    res = {"generated_utc": now, "script": os.path.abspath(__file__),
           "raw_root": RAW, "fetch_date_of_snapshot": FETCH_DATE.isoformat(),
           "notes": [
               "All raw bars useRTH=true (US/Eastern RTH day bars); the Globex "
               "overnight session is NOT in the snapshot.",
               "Deep per-contract history is settlement-derived close-only "
               "volume-0 (FUTURES-DATA-10SYMS-V1 FINAL_REPORT): reference "
               "price only, never fill price.",
               "SI chain = measured liquid cycle H/K/N/U/Z under the declared "
               "data-lane roll rule; serial months measured dead (panel).",
               "Chain starts 2025-07-01 (previous fronts SIN5-/GCQ5- not in "
               "raw set; earlier bars are deferred-contract marks).",
               "Descriptive only: no PnL, no event studies, no parameter "
               "selection; ex-post labels are descriptions, never features.",
           ]}

    # ---------------- SI panel (all 22 contracts incl. serial)
    panel = []
    for (local, conid), (d, bars) in sorted(scan_all("SI").items(),
                                            key=lambda kv: kv[0][0]):
        mc = local[-2]
        dm = dm_from_meta(d, local)
        volbars = [b for b in bars if b["v"] > 0]
        flat = sum(1 for b in bars if b["o"] == b["h"] == b["l"] == b["c"] and b["v"] == 0)
        panel.append({"local": local, "conId": conid,
                      "lastTradeDate": d.get("expiry_month"),
                      "delivery_month": dm, "month_code": mc,
                      "in_liquid_cycle": mc in SI_CYCLE,
                      "n_bars": len(bars),
                      "first": bars[0]["t"] if bars else None,
                      "last": bars[-1]["t"] if bars else None,
                      "n_flat_zero_vol": flat, "n_vol_bars": len(volbars),
                      "max_vol": max((b["v"] for b in bars), default=0)})
    panel.sort(key=lambda r: r["lastTradeDate"] or "99999999")
    res["contract_panel"] = panel
    serial = [r for r in panel if not r["in_liquid_cycle"]]
    liq = [r for r in panel if r["in_liquid_cycle"]]
    res["panel_summary"] = {
        "n_contracts": len(panel), "n_cycle_HKNUZ": len(liq),
        "n_serial": len(serial),
        "serial_max_vol": max((r["max_vol"] for r in serial), default=0),
        "serial_max_vol_contract": max(serial, key=lambda r: r["max_vol"])["local"] if serial else None,
        "cycle_min_max_vol": min(r["max_vol"] for r in liq),
        "cycle_median_max_vol": st.median([r["max_vol"] for r in liq]),
        "all_flat_contracts": [r["local"] for r in panel if r["n_vol_bars"] == 0],
    }

    # ---------------- SI liquid chain + roll verification
    contracts, chain = build_chain("SI", SI_CYCLE)
    dates = sorted(chain)
    res["chain_window"] = {"first": dates[0], "last": dates[-1], "n_days": len(dates)}
    verify = []
    for c in contracts:
        expired = c["meta"].get("expiry_month", "99999999")[:8] <= FETCH_DATE.isoformat().replace("-", "")
        if expired:
            verify.append({"local": c["local"], "expired": True,
                           "roll_date_declared": c["roll_date"],
                           "file_last": c["file_last"],
                           "file_ends_at_roll": c["file_last"] == c["roll_date"]})
        else:
            verify.append({"local": c["local"], "expired": False,
                           "roll_date_declared": c["roll_date"],
                           "file_last": c["file_last"],
                           "note": "active at fetch; file cut at fetch date"})
    res["verify_files_end_at_declared_roll"] = verify

    # roll gaps (adjacent-contract close gap at roll date, both legs observed)
    roll_rows = []
    for a, b in zip(contracts, contracts[1:]):
        rd = a["roll_date"]
        if rd not in chain or rd > dates[-1]:
            continue  # future roll or missing leg
        # old leg: its own file's last close at rd; new leg: close at rd
        old_c = next((bb["c"] for bb in a["bars"] if bb["t"] == rd), None)
        new_c = next((bb["c"] for bb in b["bars"] if bb["t"] == rd), None)
        if old_c is None or new_c is None:
            continue
        gap = new_c - old_c
        roll_rows.append({
            "roll_date": rd, "from": a["local"], "to": b["local"],
            "old_close": old_c, "new_close": new_c,
            "gap_usd_oz": round(gap, 4), "gap_pct": round(100 * gap / old_c, 4),
            "gap_usd_contract": round(gap * SI_MULT, 2),
            "gap_ticks": round(gap / SI_MINTICK, 1),
            "old_vol_rd": next((bb["v"] for bb in a["bars"] if bb["t"] == rd), None),
            "new_vol_rd": next((bb["v"] for bb in b["bars"] if bb["t"] == rd), None)})
    res["roll_gaps"] = roll_rows
    res["roll_gap_summary"] = {
        "n_completed_rolls": len(roll_rows),
        "n_positive": sum(1 for r in roll_rows if r["gap_usd_oz"] > 0),
        "n_negative": sum(1 for r in roll_rows if r["gap_usd_oz"] < 0),
        "median_gap_usd_oz": round(st.median([r["gap_usd_oz"] for r in roll_rows]), 4),
        "mean_gap_pct": round(st.fmean([r["gap_pct"] for r in roll_rows]), 4),
        "next_scheduled_roll": "SIZ6->SIH7 at last session before 2026-12-01",
    }

    # ---------------- front-scale era (threshold + robustness)
    vol = {d: chain[d]["v"] for d in dates}
    era = {}
    for thr in [FRONT_SCALE] + SCALE_ROBUST:
        first_sustained = None
        for i, d in enumerate(dates):
            win = [vol[x] for x in dates[i:i + 20]]
            if len(win) == 20 and sum(1 for v in win if v >= thr) >= 16:
                first_sustained = d
                break
        era[thr] = {"n_days_ge_thr": sum(1 for v in vol.values() if v >= thr),
                    "first_sustained_80pct_of_20d": first_sustained}
    res["front_scale_era"] = era
    front_start = era[FRONT_SCALE]["first_sustained_80pct_of_20d"]
    res["front_scale_era"]["era_used"] = front_start

    # ---------------- volume migration per cycle
    mig = []
    for prev, nxt in zip(contracts, contracts[1:]):
        d10 = next((b["t"] for b in nxt["bars"] if b["v"] >= 10_000), None)
        d5 = next((b["t"] for b in nxt["bars"] if b["v"] >= 5_000), None)
        roll = next((r["roll_date"] for r in roll_rows if r["to"] == nxt["local"]), None)
        days_before = None
        if roll and d10:
            days_before = (datetime.strptime(roll, "%Y-%m-%d")
                           - datetime.strptime(d10, "%Y-%m-%d")).days
        mig.append({"to": nxt["local"], "first_vol_ge_5k": d5,
                    "first_vol_ge_10k": d10, "declared_roll_date": roll,
                    "days_10k_before_roll": days_before})
    res["volume_migration"] = mig

    # ---------------- returns (roll-morning returns excluded)
    closes = {d: chain[d]["c"] for d in dates}
    owner = {d: chain[d]["contract"] for d in dates}
    rets, ret_dates, excl = [], [], 0
    for a, b in zip(dates, dates[1:]):
        if owner[a] != owner[b]:  # return dated b mixes contracts -> exclude
            excl += 1
            continue
        if closes[a] and closes[b]:
            rets.append(closes[b] / closes[a] - 1)
            ret_dates.append(b)
    era_idx = [i for i, d in enumerate(ret_dates) if d >= front_start]
    era_rets = [rets[i] for i in era_idx]
    res["returns"] = {
        "chain_since_2025_07": stats(rets),
        "front_scale_era": stats(era_rets),
        "annualized_vol_pct_front_scale": round(st.pstdev(era_rets) * 252 ** 0.5 * 100, 2),
        "roll_morning_returns_excluded": excl,
    }
    res["top_abs_daily_moves"] = [
        {"date": d, "ret_pct": round(100 * r, 2), "contract": chain[d]["contract"]}
        for d, r in sorted(zip(ret_dates, rets), key=lambda x: -abs(x[1]))[:10]]
    res["top_volume_days"] = [
        {"date": d, "vol": chain[d]["v"], "contract": chain[d]["contract"]}
        for d in sorted(dates, key=lambda d: -chain[d]["v"])[:10]]

    # rolling 63d vol
    rv = [{"date": ret_dates[i], "vol_d": round(st.pstdev(rets[i - 63:i]), 6)}
          for i in range(63, len(rets))]
    res["rolling63_vol"] = {
        "n": len(rv), "min": min(x["vol_d"] for x in rv),
        "median": round(st.median([x["vol_d"] for x in rv]), 6),
        "max": max(x["vol_d"] for x in rv),
        "first": rv[0]["date"], "last": rv[-1]["date"],
        "last_value": rv[-1]["vol_d"]}

    def lag1(xs):
        a = [abs(x) for x in xs]
        if len(a) < 3:
            return None
        ma, mb = st.fmean(a[:-1]), st.fmean(a[1:])
        num = sum((a[i] - ma) * (a[i + 1] - mb) for i in range(len(a) - 1))
        den = (sum((x - ma) ** 2 for x in a[:-1])
               * sum((x - mb) ** 2 for x in a[1:])) ** 0.5
        return round(num / den, 4) if den else None
    res["absret_lag1_autocorr"] = {"chain": lag1(rets), "front_scale_era": lag1(era_rets)}

    # ---------------- overnight->RTH-open gap (strict-past normalization)
    gaps, grows = [], []
    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        if owner[d0] != owner[d1] or not chain[d1]["o"] or not closes[d0]:
            continue
        g = chain[d1]["o"] / closes[d0] - 1
        past = [rets[j] for j in range(len(ret_dates)) if ret_dates[j] < d1][-20:]
        if len(past) < 20:
            continue
        base = st.fmean([abs(x) for x in past])
        gaps.append(g)
        grows.append({"date": d1, "gap_pct": round(100 * g, 3),
                      "gap_over_trailing20d_meanabs":
                          round(abs(g) / base, 2) if base else None})
    era_mask = [r["date"] >= front_start for r in grows]
    res["overnight_gap"] = {
        "chain": stats(gaps),
        "front_scale_era": stats([g for g, m in zip(gaps, era_mask) if m]),
        "share_days_ge_2x_trailing": round(
            sum(1 for r in grows if r["gap_over_trailing20d_meanabs"] is not None
                and r["gap_over_trailing20d_meanabs"] >= 2) / len(grows), 4),
        "share_ge_2x_front_scale": round(
            sum(1 for r, m in zip(grows, era_mask) if m
                and r["gap_over_trailing20d_meanabs"] is not None
                and r["gap_over_trailing20d_meanabs"] >= 2)
            / max(1, sum(era_mask)), 4),
        "top3_abs": sorted(grows, key=lambda r: -abs(r["gap_pct"]))[:3],
    }

    # ---------------- seasonality (descriptive)
    def season(pairs):
        agg = defaultdict(list)
        for d, x in pairs:
            agg[d].append(x)
        return {k: stats(v) for k, v in sorted(agg.items())}
    res["seasonality"] = {
        "by_month_front_scale_era": season(
            [(ret_dates[i][5:7], rets[i]) for i in era_idx]),
        "by_weekday_front_scale_era": season(
            [(datetime.strptime(ret_dates[i], "%Y-%m-%d").strftime("%a"),
              rets[i]) for i in era_idx]),
        "caveat": "single-bull-regime 15-month window; not a seasonal-alpha claim",
    }

    # ---------------- level context
    res["level_context"] = {
        "chain_first_close": closes[dates[0]], "chain_last_close": closes[dates[-1]],
        "chain_min_close": min(closes.values()), "chain_max_close": max(closes.values()),
        "min_date": min(closes, key=closes.get), "max_date": max(closes, key=closes.get),
        "chain_pct_change": round(100 * (closes[dates[-1]] / closes[dates[0]] - 1), 1),
        "deferred_mark_context": "SIZ5 (Dec-25 delivery, then-deferred) "
        "settlement marks from 2020-12-31 exist in raw but are NOT a front "
        "chain; not used for return statistics.",
    }

    # ---------------- hourly RTH volume profile
    hourly = {}
    for local, conid, label in [("SIZ6", "535526329", "SIZ6_liquid_front"),
                                ("SIU6", "738529133", "SIU6_liquid_front_prior")]:
        d, bars = load_bars("SI", local, conid, "TRADES", "1hour", "30D")
        if not bars:
            continue
        hb, days = defaultdict(int), set()
        for b in bars:
            hb[b["t"][11:13]] += b["v"]
            days.add(b["t"][:10])
        tot = sum(hb.values())
        hourly[label] = {
            "contract": local, "window": f"{bars[0]['t'][:10]}..{bars[-1]['t'][:10]}",
            "n_days": len(days), "n_bars": len(bars), "total_vol": tot,
            "share_by_hour_et": {h: round(v / tot, 4) for h, v in sorted(hb.items())},
            "tz_offsets_seen": sorted({b["t"][19:] for b in bars}),
            "note": "RTH-only bars (useRTH=true); hour 09 = 09:30-10:00 half "
                    "hour, hour 16 = 16:00 close bar only",
        }
    res["hourly_volume_profile_rth_only"] = hourly
    _, m1 = load_bars("SI", "SIZ6", "535526329", "TRADES", "1min", "2D")
    res["one_min_files"] = {
        "SIZ6_2D_n_bars": len(m1) if m1 else 0,
        "note": "2-day window per contract; deeper intraday NOT_RUN in snapshot",
    }

    # ---------------- BID/ASK close-proxy spreads
    def spread_stats(local, conid, lo=None):
        _, bb = load_bars("SI", local, conid, "BID", "1day", "1Y")
        _, ba = load_bars("SI", local, conid, "ASK", "1day", "1Y")
        if not bb or not ba:
            return None
        bm = {b["t"]: b["c"] for b in bb}
        am = {b["t"]: b["c"] for b in ba}
        rows, crossed = [], []
        for t in sorted(set(bm) & set(am)):
            if lo and t < lo:
                continue
            rows.append(am[t] - bm[t])
            if bm[t] > am[t]:
                crossed.append(t)
        sv = sorted(rows)
        return {"local": local, "n": len(rows),
                "window": (min(set(bm) & set(am)), max(set(bm) & set(am))),
                "median_usd_oz": round(q(sv, 0.5), 4),
                "median_ticks": round(q(sv, 0.5) / SI_MINTICK, 1),
                "median_usd_contract": round(q(sv, 0.5) * SI_MULT, 2),
                "p90_usd_oz": round(q(sv, 0.9), 4),
                "n_crossed_close_days": len(crossed), "crossed_dates": crossed}
    liq_windows = {
        "SIV6_S1front_full1y_NOTliquidfront": ("SIV6", "760200581", None),
        "SIZ6_full1y_incl_deferred_era": ("SIZ6", "535526329", None),
        "SIZ6_liquid_era_2026_09plus": ("SIZ6", "535526329", "2026-09-01"),
        "SIU5_liquid_era_2025_07plus": ("SIU5", "662922826", "2025-07-01"),
        "SIZ5_liquid_era_2025_09plus": ("SIZ5", "462941489", "2025-09-01"),
        "SIH6_liquid_era_2025_12plus": ("SIH6", "700079997", "2025-12-01"),
        "SIK6_liquid_era_2026_03plus": ("SIK6", "712566019", "2026-03-01"),
        "SIN6_liquid_era_2026_05plus": ("SIN6", "505405746", "2026-05-01"),
        "SIU6_liquid_era_2026_07plus": ("SIU6", "738529133", "2026-07-01"),
    }
    res["spread_close_proxy"] = {
        k: spread_stats(lc, cid, lo) for k, (lc, cid, lo) in liq_windows.items()}
    liq_sp = [v for k, v in res["spread_close_proxy"].items()
              if v and "liquid_era" in k]
    res["spread_close_proxy"]["pooled_liquid_era_summary"] = {
        "n_windows": len(liq_sp),
        "median_of_medians_usd_oz": round(st.median([v["median_usd_oz"] for v in liq_sp]), 4),
        "median_of_medians_ticks": round(st.median([v["median_usd_oz"] for v in liq_sp]) / SI_MINTICK, 1),
        "median_of_medians_usd_contract": round(st.median([v["median_usd_oz"] for v in liq_sp]) * SI_MULT, 2),
        "caveat": "close-to-close proxy from non-synchronous daily BID/ASK "
                  "closes; NOT an executable spread",
    }

    # ---------------- GC/SI ratio (both liquid chains, declared rule)
    gc_contracts, gc_chain = build_chain("GC", GC_CYCLE)
    gcdates = sorted(gc_chain)
    both = [t for t in dates if t in gc_chain]
    ratio = {t: gc_chain[t]["c"] / chain[t]["c"] for t in both
             if gc_chain[t]["c"] and chain[t]["c"]}
    rd = sorted(ratio)
    rv_ = [ratio[t] for t in rd]
    si_rolls = {r["roll_date"] for r in roll_rows}
    gc_rolls = {c["roll_date"] for c in gc_contracts
                if c["file_last"] and c["file_last"] <= c["roll_date"]}
    adj_rolls = si_rolls | gc_rolls
    clean = [t for t in rd if not any(
        (datetime.strptime(t, "%Y-%m-%d") + timedelta(days=k)).date().isoformat() in adj_rolls
        or (datetime.strptime(t, "%Y-%m-%d") - timedelta(days=k)).date().isoformat() in adj_rolls
        for k in (0, 1))]
    pct_now = None
    if len(rv_) >= 64:
        past = rv_[-64:-1]
        pct_now = round(100 * sum(1 for x in past if x <= rv_[-1]) / len(past), 1)
    res["gc_chain_window"] = {"first": gcdates[0], "last": gcdates[-1],
                              "n_days": len(gcdates),
                              "contracts": sorted({v["delivery_month"] for v in gc_chain.values()})}
    res["gc_si_ratio"] = {
        "window": [rd[0], rd[-1]], "n_days": len(rd),
        "ratio_stats": stats(rv_),
        "min_date": rd[rv_.index(min(rv_))], "max_date": rd[rv_.index(max(rv_))],
        "current_ratio": round(rv_[-1], 4),
        "current_pctile_vs_trailing63d_strict_past": pct_now,
        "n_days_adjacent_to_either_roll": len(rd) - len(clean),
        "caveats": ["both legs unadjusted declared-rule chains; ratio embeds "
                    "roll-gap jumps of either leg at roll dates",
                    "descriptive only - no mean-reversion test run"],
    }

    # rolling 63d SI-vs-GC beta/correlation (daily simple returns, descriptive)
    gc_closes = {t: gc_chain[t]["c"] for t in sorted(gc_chain)}
    gc_owner = {t: gc_chain[t]["contract"] for t in gc_chain}
    pairs = []
    ts = sorted(set(dates) & set(gc_chain))
    for a, b in zip(ts, ts[1:]):
        if owner[a] == owner[b] and gc_owner[a] == gc_owner[b] \
                and closes[a] and closes[b] and gc_closes[a] and gc_closes[b]:
            pairs.append((b, closes[b] / closes[a] - 1,
                          gc_closes[b] / gc_closes[a] - 1))
    xs = [g for _, _, g in pairs]
    ys = [s for _, s, _ in pairs]
    mx, my = st.fmean(xs), st.fmean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
    beta_full = cov / st.pstdev(xs)
    corr_full = cov / (st.pstdev(xs) * st.pstdev(ys))
    rb = []
    for i in range(63, len(pairs)):
        wx = xs[i - 63:i]
        wy = ys[i - 63:i]
        mxw, myw = st.fmean(wx), st.fmean(wy)
        covw = sum((x - mxw) * (y - myw) for x, y in zip(wx, wy)) / 63
        den = st.pstdev(wx) * st.pstdev(wy)
        rb.append({"date": pairs[i][0],
                   "beta": round(covw / st.pstdev(wx), 3),
                   "corr": round(covw / den, 3) if den else None,
                   "si_vol_d": round(st.pstdev(wy), 4),
                   "gc_vol_d": round(st.pstdev(wx), 4)})
    res["gc_si_beta"] = {
        "window": [pairs[0][0], pairs[-1][0]], "n": len(pairs),
        "beta_full_sample": round(beta_full, 3),
        "corr_full_sample": round(corr_full, 3),
        "beta_min": min(r["beta"] for r in rb), "beta_max": max(r["beta"] for r in rb),
        "beta_median": round(st.median([r["beta"] for r in rb]), 3),
        "corr_min": min(r["corr"] for r in rb if r["corr"] is not None),
        "corr_max": max(r["corr"] for r in rb if r["corr"] is not None),
        "beta_last": rb[-1],
        "note": "rolling windows use strict past 63 returns ending the prior "
                "day; beta is in $/oz-per-$/oz units (multiply by GC/SI price "
                "ratio for %-elasticity); descriptive only",
    }

    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
